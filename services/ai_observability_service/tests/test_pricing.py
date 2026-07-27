"""Tests for app/pricing.py — pricing selection and Decimal cost formulas.
Uses the isolated temp-db fixtures from conftest.py, never the real DB."""
from decimal import Decimal

from app.pricing import (
    BILLING_UNIT_PER_1K_TOKENS,
    BILLING_UNIT_PER_1M_TOKENS,
    BILLING_UNIT_PER_MINUTE,
    BILLING_UNIT_PER_REQUEST,
    PricingRow,
    calculate_cost,
    find_active_pricing,
)
from app.time_utils import parse_utc
from conftest import insert_pricing_row


# --- Formulas (pure, no DB) --------------------------------------------------


def test_per_1k_tokens_formula():
    pricing = PricingRow(
        id=1, provider="gemini", service="generative_ai", model="m", billing_unit=BILLING_UNIT_PER_1K_TOKENS,
        input_price=Decimal("0.10"), output_price=Decimal("0.40"), unit_price=None, currency="USD",
    )
    cost = calculate_cost(pricing, input_tokens=1000, output_tokens=1000, audio_duration_seconds=None, request_count=None)
    assert cost == Decimal("0.10") + Decimal("0.40")


def test_per_1m_tokens_formula():
    pricing = PricingRow(
        id=1, provider="gemini", service="generative_ai", model="m", billing_unit=BILLING_UNIT_PER_1M_TOKENS,
        input_price=Decimal("100"), output_price=Decimal("400"), unit_price=None, currency="USD",
    )
    cost = calculate_cost(pricing, input_tokens=1_000_000, output_tokens=1_000_000, audio_duration_seconds=None, request_count=None)
    assert cost == Decimal("100") + Decimal("400")


def test_per_minute_formula():
    pricing = PricingRow(
        id=1, provider="assemblyai", service="transcription", model=None, billing_unit=BILLING_UNIT_PER_MINUTE,
        input_price=None, output_price=None, unit_price=Decimal("0.006"), currency="USD",
    )
    cost = calculate_cost(pricing, input_tokens=None, output_tokens=None, audio_duration_seconds=120.0, request_count=None)
    assert cost == Decimal("2") * Decimal("0.006")  # 120s = 2 minutes


def test_per_request_formula():
    pricing = PricingRow(
        id=1, provider="bedrock", service="rag_retrieval", model=None, billing_unit=BILLING_UNIT_PER_REQUEST,
        input_price=None, output_price=None, unit_price=Decimal("0.001"), currency="USD",
    )
    cost = calculate_cost(pricing, input_tokens=None, output_tokens=None, audio_duration_seconds=None, request_count=3)
    assert cost == Decimal("0.003")


def test_decimal_precision_preserved_for_tiny_cost():
    """A very small Gemini call must not round to zero or lose precision."""
    pricing = PricingRow(
        id=1, provider="gemini", service="generative_ai", model="m", billing_unit=BILLING_UNIT_PER_1K_TOKENS,
        input_price=Decimal("0.075"), output_price=Decimal("0.30"), unit_price=None, currency="USD",
    )
    cost = calculate_cost(pricing, input_tokens=1, output_tokens=1, audio_duration_seconds=None, request_count=None)
    expected = (Decimal(1) / Decimal(1000)) * Decimal("0.075") + (Decimal(1) / Decimal(1000)) * Decimal("0.30")
    assert cost == expected
    assert str(cost) == str(expected)  # exact string round-trip, no float artifact


def test_missing_input_tokens_returns_none_not_zero():
    pricing = PricingRow(
        id=1, provider="gemini", service="generative_ai", model="m", billing_unit=BILLING_UNIT_PER_1K_TOKENS,
        input_price=Decimal("0.10"), output_price=Decimal("0.40"), unit_price=None, currency="USD",
    )
    cost = calculate_cost(pricing, input_tokens=None, output_tokens=30, audio_duration_seconds=None, request_count=None)
    assert cost is None


def test_missing_pricing_returns_none():
    cost = calculate_cost(None, input_tokens=100, output_tokens=30, audio_duration_seconds=None, request_count=None)
    assert cost is None


def test_missing_audio_duration_returns_none_for_per_minute():
    pricing = PricingRow(
        id=1, provider="assemblyai", service="transcription", model=None, billing_unit=BILLING_UNIT_PER_MINUTE,
        input_price=None, output_price=None, unit_price=Decimal("0.006"), currency="USD",
    )
    cost = calculate_cost(pricing, input_tokens=None, output_tokens=None, audio_duration_seconds=None, request_count=None)
    assert cost is None


# --- Pricing selection (DB-backed) -------------------------------------------


def test_pricing_effective_date_selection(db_conn):
    insert_pricing_row(
        db_conn, model="gemini-old", effective_from="2020-01-01T00:00:00+00:00", effective_to="2026-01-01T00:00:00+00:00",
        input_price="0.05", output_price="0.20",
    )
    insert_pricing_row(
        db_conn, model="gemini-old", effective_from="2026-01-01T00:00:00+00:00", effective_to=None,
        input_price="0.10", output_price="0.40",
    )

    before = find_active_pricing(db_conn, "gemini", "generative_ai", "gemini-old", parse_utc("2025-06-01T00:00:00+00:00"))
    after = find_active_pricing(db_conn, "gemini", "generative_ai", "gemini-old", parse_utc("2026-06-01T00:00:00+00:00"))

    assert before is not None and before.input_price == Decimal("0.05")
    assert after is not None and after.input_price == Decimal("0.10")


def test_old_and_new_pricing_versions_both_recomputable(db_conn):
    """Historic events must preserve the exact pricing row used — this test
    confirms both versions remain independently selectable by timestamp,
    not that a later insert overwrites the earlier one's applicability."""
    old_id = insert_pricing_row(
        db_conn, model="m", effective_from="2020-01-01T00:00:00+00:00", effective_to="2025-01-01T00:00:00+00:00",
        input_price="0.05", output_price="0.20",
    )
    new_id = insert_pricing_row(
        db_conn, model="m", effective_from="2025-01-01T00:00:00+00:00", effective_to=None,
        input_price="0.10", output_price="0.40",
    )
    assert old_id != new_id

    at_2022 = find_active_pricing(db_conn, "gemini", "generative_ai", "m", parse_utc("2022-01-01T00:00:00+00:00"))
    at_2026 = find_active_pricing(db_conn, "gemini", "generative_ai", "m", parse_utc("2026-01-01T00:00:00+00:00"))
    assert at_2022.id == old_id
    assert at_2026.id == new_id


def test_no_matching_pricing_returns_none(db_conn):
    result = find_active_pricing(db_conn, "unknown_provider", "unknown_service", "unknown_model", parse_utc("2026-01-01T00:00:00+00:00"))
    assert result is None


def test_boundary_at_effective_to_excluded(db_conn):
    """Half-open interval: effective_to is exclusive."""
    insert_pricing_row(
        db_conn, model="m", effective_from="2020-01-01T00:00:00+00:00", effective_to="2026-01-01T00:00:00+00:00",
        input_price="0.05", output_price="0.20",
    )
    exactly_at_boundary = find_active_pricing(db_conn, "gemini", "generative_ai", "m", parse_utc("2026-01-01T00:00:00+00:00"))
    assert exactly_at_boundary is None


def test_model_agnostic_pricing_used_as_fallback(db_conn):
    """A service with no per-model pricing concept (model=None in
    pricing_config) should still resolve, e.g. AssemblyAI."""
    insert_pricing_row(
        db_conn, provider="assemblyai", service="transcription", model=None, billing_unit="per_minute",
        input_price=None, output_price=None, unit_price="0.006",
    )
    result = find_active_pricing(db_conn, "assemblyai", "transcription", None, parse_utc("2026-01-01T00:00:00+00:00"))
    assert result is not None
    assert result.unit_price == Decimal("0.006")
