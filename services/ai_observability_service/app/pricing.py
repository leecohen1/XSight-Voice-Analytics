"""Pricing selection and cost-calculation formulas.

All monetary arithmetic uses `decimal.Decimal` exclusively — never `float`
— per the explicit requirement to preserve exact currency precision for
low-cost API calls (a single Gemini extraction call can cost a small
fraction of a cent; float would round that away over many calls).

No provider price is hardcoded here. Every formula takes its price(s) from
a `pricing_config` row already selected from the database — this module
has no knowledge of what Gemini, AssemblyAI, or Bedrock actually charge.

"A missing value is not equivalent to zero usage": every function below
returns `None` (not `Decimal("0")`) whenever a required input is missing,
rather than guessing.
"""
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

BILLING_UNIT_PER_1K_TOKENS = "per_1k_tokens"
BILLING_UNIT_PER_1M_TOKENS = "per_1m_tokens"
BILLING_UNIT_PER_MINUTE = "per_minute"
BILLING_UNIT_PER_REQUEST = "per_request"

SUPPORTED_BILLING_UNITS = frozenset(
    {
        BILLING_UNIT_PER_1K_TOKENS,
        BILLING_UNIT_PER_1M_TOKENS,
        BILLING_UNIT_PER_MINUTE,
        BILLING_UNIT_PER_REQUEST,
    }
)


def to_decimal(value) -> Optional[Decimal]:
    """Parses a stored price/cost string into a Decimal. Returns None for
    missing/unparseable values rather than raising, since a malformed
    pricing row should degrade to "no price available", not a 500."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _parse_ts(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(frozen=True)
class PricingRow:
    id: int
    provider: str
    service: str
    model: Optional[str]
    billing_unit: str
    input_price: Optional[Decimal]
    output_price: Optional[Decimal]
    unit_price: Optional[Decimal]
    currency: str


def find_active_pricing(
    conn: sqlite3.Connection,
    provider: str,
    service: str,
    model: Optional[str],
    occurred_at: datetime,
) -> Optional[PricingRow]:
    """Selects the pricing_config row active at `occurred_at` for the given
    (provider, service, model). Matches model-specific pricing first; falls
    back to a model-agnostic row (pricing_config.model IS NULL) if no
    model-specific row applies — useful for services with no per-model
    pricing concept (e.g. AssemblyAI, which prices per audio-minute
    regardless of any "model").

    Uses a half-open interval: effective_from <= occurred_at < effective_to
    (or effective_to IS NULL, meaning still open-ended). If more than one
    row matches, the one with the latest effective_from wins.

    Candidate rows are fetched with a broad SQL filter and then matched
    precisely in Python (parsing timestamps), rather than comparing
    timestamp strings in SQL — this avoids subtle bugs from
    inconsistently-formatted ISO strings and keeps the date-boundary logic
    in one place, testable independent of SQLite's string collation.
    """
    rows = conn.execute(
        """
        SELECT * FROM pricing_config
        WHERE provider = ? AND service = ? AND is_active = 1
          AND (model = ? OR model IS NULL)
        """,
        (provider, service, model),
    ).fetchall()

    best: Optional[sqlite3.Row] = None
    best_from: Optional[datetime] = None
    best_is_model_specific = False

    for row in rows:
        eff_from = _parse_ts(row["effective_from"])
        if eff_from is None or occurred_at < eff_from:
            continue
        eff_to = _parse_ts(row["effective_to"]) if row["effective_to"] else None
        if eff_to is not None and occurred_at >= eff_to:
            continue

        is_model_specific = row["model"] is not None
        # Prefer a model-specific match over a model-agnostic one outright;
        # among equally-specific matches, prefer the most recent effective_from.
        if best is None:
            better = True
        elif is_model_specific and not best_is_model_specific:
            better = True
        elif (not is_model_specific) and best_is_model_specific:
            better = False
        else:
            better = eff_from > best_from

        if better:
            best = row
            best_from = eff_from
            best_is_model_specific = is_model_specific

    if best is None:
        return None

    return PricingRow(
        id=best["id"],
        provider=best["provider"],
        service=best["service"],
        model=best["model"],
        billing_unit=best["billing_unit"],
        input_price=to_decimal(best["input_price"]),
        output_price=to_decimal(best["output_price"]),
        unit_price=to_decimal(best["unit_price"]),
        currency=best["currency"],
    )


def calculate_cost(
    pricing: Optional[PricingRow],
    *,
    input_tokens: Optional[int],
    output_tokens: Optional[int],
    audio_duration_seconds: Optional[float],
    request_count: Optional[int],
) -> Optional[Decimal]:
    """Computes the estimated variable cost for one usage event, given the
    already-selected pricing row and the event's measured usage. Returns
    None whenever the billing unit's required input(s) are missing or the
    pricing row lacks the corresponding price(s) — never substitutes zero."""
    if pricing is None:
        return None

    if pricing.billing_unit == BILLING_UNIT_PER_1K_TOKENS:
        return _token_cost(input_tokens, output_tokens, pricing.input_price, pricing.output_price, Decimal(1000))

    if pricing.billing_unit == BILLING_UNIT_PER_1M_TOKENS:
        return _token_cost(input_tokens, output_tokens, pricing.input_price, pricing.output_price, Decimal(1_000_000))

    if pricing.billing_unit == BILLING_UNIT_PER_MINUTE:
        if audio_duration_seconds is None or pricing.unit_price is None:
            return None
        try:
            duration = Decimal(str(audio_duration_seconds))
        except InvalidOperation:
            return None
        return (duration / Decimal(60)) * pricing.unit_price

    if pricing.billing_unit == BILLING_UNIT_PER_REQUEST:
        if request_count is None or pricing.unit_price is None:
            return None
        return Decimal(request_count) * pricing.unit_price

    # Unrecognized/unsupported billing unit — degrade to "no cost available"
    # rather than guessing at a formula.
    return None


def _token_cost(
    input_tokens: Optional[int],
    output_tokens: Optional[int],
    input_price: Optional[Decimal],
    output_price: Optional[Decimal],
    divisor: Decimal,
) -> Optional[Decimal]:
    """Shared per_1k_tokens / per_1m_tokens formula. Both input and output
    token counts AND both prices must be present — a missing token count is
    not the same as zero tokens, so a partial (input-only) total would
    misrepresent the real cost. Either side missing => the whole event's
    token cost is None, not a partial sum."""
    if input_tokens is None or output_tokens is None:
        return None
    if input_price is None or output_price is None:
        return None
    input_cost = (Decimal(input_tokens) / divisor) * input_price
    output_cost = (Decimal(output_tokens) / divisor) * output_price
    return input_cost + output_cost
