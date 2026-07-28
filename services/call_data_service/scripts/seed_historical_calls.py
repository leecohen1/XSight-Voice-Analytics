"""Deterministic historical seed: data/historical_sales_calls.csv -> S3.

Converts the 24-call curated corpus into application records under the same
prefix the live pipeline writes to, so the Overview aggregates one dataset
instead of stitching two together at read time.

WHAT THIS SCRIPT DOES NOT DO
----------------------------
* No Gemini, AssemblyAI, Bedrock, or pipeline call of any kind.
* No write anywhere near the Bedrock ingestion prefix (the repository's key
  guard enforces this independently of anything here).
* No modification of data/historical_sales_calls.csv -- it is read-only.
* No fabricated AI content. The corpus has no call summary, coaching array,
  confidence, risk level, or follow-up email, so:
    - `call_summary` is composed deterministically from structured columns;
    - `coaching_feedback` carries `manager_notes` verbatim when present, else [];
    - `similar_calls` is [] (RAG retrieval is never run during seeding);
    - `confidence`, `risk_level` are None;
    - `suggested_follow_up_email` is "" (the frontend contract types it as a
      string; there is no source content to put in it).

DETERMINISTIC DATES
-------------------
The CSV has no date column, so dates are assigned -- never invented at
random. Every call's timestamp is `anchor_date - <fixed offset> days`, where
the offset comes from a hardcoded table indexed by the call's position
within its agent's group (calls sorted by call_id). Given the same anchor,
this script always produces byte-identical output.

The anchor defaults to today (UTC) so seeded data stays inside the Overview's
rolling windows; pass --anchor-date for a fully pinned, reproducible run
(every test does exactly this).

Offsets per agent (with a per-agent stagger of 0-3 days so all four agents
do not share identical dates):

    base = [1, 10, 22, 36, 52, 68]  +  agent_index (0..3)

This guarantees, for every one of the four agents:
    * >= 1 call in the current 7-day window   (offset ~1-4)
    * >= 1 call in the previous 7-day window  (offset ~10-13)
    * 3 calls in the current 30-day window    (offsets ~1, ~10, ~22)
    * 2 calls in the previous 30-day window   (offsets ~36, ~52)
and a total corpus span of ~68 days (>= the required 60).

The two-calls-per-window floor is what makes the improved-agent calculation
(minimum 2 calls in each period) evaluable for every agent. The improvement
values themselves come from the CSV's real scores -- this script never
arranges data to manufacture an improvement.
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Make `app` importable when this file is run directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.attention import derive_attention, derive_recovery_opportunity  # noqa: E402
from app.config import load_settings  # noqa: E402
from app.models import (  # noqa: E402
    SCHEMA_VERSION,
    AnalyzedCallRecord,
    CallAnalysis,
)
from app.repository import CallRepository, build_s3_client  # noqa: E402

AGENT_BASE_DAY_OFFSETS = [1, 10, 22, 36, 52, 68]

# Time-of-day spread so records within one day still order deterministically.
HOUR_CYCLE = [9, 11, 13, 15, 10, 14]

OUTCOME_CANONICAL = {
    "sale": "Sale",
    "no sale": "No Sale",
    "follow-up needed": "Follow-up Needed",
    "follow up needed": "Follow-up Needed",
    "uncertain": "Uncertain",
}

SENTIMENT_CANONICAL = {"positive": "positive", "neutral": "neutral", "negative": "negative"}


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _as_bool(value: str | None) -> bool | None:
    text = _clean(value).lower()
    if text in {"true", "yes", "1"}:
        return True
    if text in {"false", "no", "0"}:
        return False
    return None


def _as_int(value: str | None) -> int | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def canonical_outcome(raw: str | None) -> str | None:
    return OUTCOME_CANONICAL.get(_clean(raw).lower())


def canonical_sentiment(raw: str | None) -> str | None:
    """`mixed` exists in the corpus taxonomy but not in the frontend
    contract's three-value sentiment; it maps to `neutral` rather than being
    dropped or guessed as positive/negative."""
    text = _clean(raw).lower()
    if text == "mixed":
        return "neutral"
    return SENTIMENT_CANONICAL.get(text)


def build_call_summary(row: dict[str, str]) -> str:
    """A deterministic sentence assembled only from structured CSV columns.

    Deliberately not an interpretation of the transcript -- every clause
    below restates a column the corpus already asserts.
    """
    outcome = canonical_outcome(row.get("sale_result")) or "an unrecorded outcome"
    objection = _clean(row.get("main_objection")) or "none"
    intent = _clean(row.get("customer_intent")) or "unrecorded"
    sentiment = canonical_sentiment(row.get("customer_sentiment")) or "unrecorded"
    segment = _clean(row.get("customer_segment"))
    industry = _clean(row.get("industry"))

    who = " ".join(part for part in [segment, industry] if part) or "Unspecified segment"
    objection_clause = (
        "no objection was recorded" if objection in {"", "none"} else f"the main objection was {objection}"
    )
    return (
        f"{who} call handled by {_clean(row.get('agent_name'))}. "
        f"Customer intent was {intent} and {objection_clause}. "
        f"Recorded sentiment was {sentiment} and the call ended as {outcome}. "
        f"Seeded from the curated historical corpus; field values are the corpus's own."
    )


def build_recommended_next_action(row: dict[str, str]) -> str | None:
    """Derived only from the corpus's own follow-up columns."""
    follow_up = _as_bool(row.get("follow_up_needed"))
    scheduled = _as_bool(row.get("next_meeting_scheduled"))
    if follow_up and scheduled:
        return "Prepare for the scheduled next meeting recorded against this call."
    if follow_up and scheduled is False:
        return "Schedule the follow-up this call recorded as needed; no next meeting is on the calendar."
    if follow_up is False:
        return "No follow-up was recorded as needed for this call."
    return None


def build_detected_signals(row: dict[str, str]) -> list[str]:
    """Restates explicit CSV columns as signal strings. Nothing inferred."""
    signals: list[str] = []
    objection = _clean(row.get("main_objection")).lower()
    if objection and objection != "none":
        signals.append(f"{objection} objection")
    closing = _clean(row.get("closing_attempt")).lower()
    if closing:
        signals.append(f"{closing} closing attempt")
    if _as_bool(row.get("decision_maker_present")) is True:
        signals.append("decision maker present")
    if _as_bool(row.get("follow_up_needed")) is True:
        signals.append("follow-up needed")
    return signals


def build_record(row: dict[str, str], created_at: datetime) -> AnalyzedCallRecord:
    outcome = canonical_outcome(row.get("sale_result"))
    sentiment = canonical_sentiment(row.get("customer_sentiment"))
    agent_performance = _as_int(row.get("agent_performance_score"))
    lead_quality = _as_int(row.get("lead_quality_score"))
    objection = _clean(row.get("main_objection")) or None
    manager_notes = _clean(row.get("manager_notes"))

    attention = derive_attention(
        call_outcome=outcome,
        customer_sentiment=sentiment,
        agent_performance_score=agent_performance,
        lead_quality_score=lead_quality,
        # The corpus never measured a risk level or a confidence, so both
        # stay None and contribute nothing to the priority score.
        risk_level=None,
        confidence=None,
        guardrail_status="pass",
        router_reasons=[],
        follow_up_needed=_as_bool(row.get("follow_up_needed")),
        next_meeting_scheduled=_as_bool(row.get("next_meeting_scheduled")),
    )
    recovery = derive_recovery_opportunity(
        call_outcome=outcome,
        lead_quality_score=lead_quality,
        main_objection=objection,
        confidence=None,
        attention=attention,
    )

    analysis = CallAnalysis(
        transcript=row.get("transcript") or "",
        call_summary=build_call_summary(row),
        customer_intent=_clean(row.get("customer_intent")) or None,
        main_objection=objection,
        customer_sentiment=sentiment,
        call_outcome=outcome,
        agent_performance_score=agent_performance,
        lead_quality_score=lead_quality,
        similar_calls=[],
        coaching_feedback=[manager_notes] if manager_notes else [],
        recommended_next_action=build_recommended_next_action(row),
        suggested_follow_up_email="",
        routing_category=_clean(row.get("call_category")) or None,
        confidence=None,
        risk_level=None,
        detected_signals=build_detected_signals(row),
        limitations=(
            "Seeded from data/historical_sales_calls.csv. This record was never processed by the live "
            "pipeline, so it has no measured confidence, risk level, RAG citations, or generated "
            "follow-up email; those fields are empty rather than estimated."
        ),
        guardrail_status="pass",
        attention=attention,
        recovery_opportunity=recovery,
    )

    return AnalyzedCallRecord(
        schema_version=SCHEMA_VERSION,
        call_id=_clean(row.get("call_id")),
        source="historical_seed",
        created_at=created_at,
        call_date=created_at.date(),
        agent_name=_clean(row.get("agent_name")),
        # The corpus records customer_segment/industry but no customer name.
        # Left null rather than synthesising a company.
        customer_name=None,
        status="completed",
        router_reasons=[],
        analysis=analysis,
    )


def assign_timestamps(rows: list[dict[str, str]], anchor: date) -> list[tuple[dict[str, str], datetime]]:
    """Deterministically date every row. Same rows + same anchor => same output."""
    ordered = sorted(rows, key=lambda r: _clean(r.get("call_id")))

    agent_order: list[str] = []
    for row in ordered:
        agent = _clean(row.get("agent_name"))
        if agent not in agent_order:
            agent_order.append(agent)

    per_agent_index: dict[str, int] = {}
    out: list[tuple[dict[str, str], datetime]] = []
    for row in ordered:
        agent = _clean(row.get("agent_name"))
        index = per_agent_index.get(agent, 0)
        per_agent_index[agent] = index + 1

        stagger = agent_order.index(agent) % 4
        base = AGENT_BASE_DAY_OFFSETS[index % len(AGENT_BASE_DAY_OFFSETS)]
        # Calls beyond the fixed table (never hit by the 24-call corpus)
        # keep marching backwards deterministically rather than colliding.
        extra_cycles = index // len(AGENT_BASE_DAY_OFFSETS)
        offset_days = base + stagger + extra_cycles * 90

        hour = HOUR_CYCLE[index % len(HOUR_CYCLE)]
        created_at = datetime.combine(anchor - timedelta(days=offset_days), datetime.min.time()).replace(
            hour=hour, tzinfo=timezone.utc
        )
        out.append((row, created_at))
    return out


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if _clean(row.get("call_id"))]


def default_csv_path() -> Path:
    """Best-effort local-repo default: scripts/ -> call_data_service/ -> services/ -> repo root.

    Guarded because only `app/` and `scripts/` are copied into the Docker
    image (this file then runs from /service/scripts/, which has no 4th
    parent to index) -- `--csv-path` must be passed explicitly in that
    environment. Never raises IndexError; the caller checks `.exists()`.
    """
    parents = Path(__file__).resolve().parents
    if len(parents) > 3:
        return parents[3] / "data" / "historical_sales_calls.csv"
    return Path("/data/historical_sales_calls.csv")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the historical call corpus into S3.")
    # No default path is computed here -- argument parsing (including --help)
    # must never depend on resolving a filesystem location first. `None`
    # means "use default_csv_path(), resolved after parsing, once we know
    # the flag wasn't supplied."
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=None,
        help=(
            "Path to historical_sales_calls.csv. Defaults to the local repo layout "
            "(services/call_data_service/../../data/historical_sales_calls.csv); "
            "required when running from a shallow layout such as the Docker image."
        ),
    )
    parser.add_argument(
        "--anchor-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        default=None,
        help="UTC date that day-offset 0 maps to. Defaults to today (UTC).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Build and validate records, write nothing.")
    args = parser.parse_args(argv)

    csv_path: Path = args.csv_path if args.csv_path is not None else default_csv_path()
    if not csv_path.exists():
        print(f"ERROR: CSV not found at {csv_path}")
        return 2

    anchor = args.anchor_date or datetime.now(timezone.utc).date()
    rows = read_rows(csv_path)
    print(f"Read {len(rows)} rows from {csv_path}")
    print(f"Anchor date (UTC): {anchor.isoformat()}")

    dated = assign_timestamps(rows, anchor)
    records: list[AnalyzedCallRecord] = []
    failures = 0
    for row, created_at in dated:
        try:
            records.append(build_record(row, created_at))
        except Exception as exc:  # noqa: BLE001 - report, do not abort the batch
            failures += 1
            print(f"  SKIP {row.get('call_id')}: {exc}")

    print(f"Built {len(records)} records ({failures} failed)")

    if args.dry_run:
        print("\nDRY RUN -- nothing was written to S3.\n")
        for record in records:
            flag = "ATTN" if record.analysis.attention.required else "    "
            print(
                f"  {record.call_id}  {record.created_at.date()}  {flag} "
                f"{record.analysis.attention.category:<24} score={record.analysis.attention.priority_score:>3} "
                f"{record.agent_name}"
            )
        return 0 if failures == 0 else 1

    settings = load_settings()
    repo = CallRepository(s3_client=build_s3_client(settings), settings=settings)
    written = 0
    overwritten = 0
    for record in records:
        key, was_overwritten = repo.put_record(record)
        written += 1
        overwritten += 1 if was_overwritten else 0
        print(f"  wrote s3://{settings.s3_bucket}/{key}")

    print(f"\nWrote {written} records ({overwritten} overwritten, idempotent by call_id).")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
