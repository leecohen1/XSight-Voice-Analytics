"""Historical seed converter: determinism, field fidelity, window coverage."""
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from seed_historical_calls import (  # noqa: E402
    AGENT_BASE_DAY_OFFSETS,
    assign_timestamps,
    build_call_summary,
    build_detected_signals,
    build_record,
    canonical_outcome,
    canonical_sentiment,
    default_csv_path,
    main,
    read_rows,
)

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "seed_historical_calls.py"
APP_DIR = Path(__file__).resolve().parents[1] / "app"

ANCHOR = date(2026, 7, 28)
CSV_PATH = Path(__file__).resolve().parents[3] / "data" / "historical_sales_calls.csv"


def _row(**overrides):
    row = {
        "call_id": "CALL_001",
        "agent_name": "Sarah Levi",
        "customer_segment": "Mid-Market",
        "industry": "Finance",
        "transcript": "Agent: Hello.\nCustomer: Hi there.",
        "sale_result": "Sale",
        "customer_intent": "high",
        "main_objection": "price",
        "customer_sentiment": "positive",
        "agent_performance_score": "4",
        "objection_handling_quality": "4",
        "closing_attempt": "strong",
        "follow_up_needed": "false",
        "lead_quality_score": "5",
        "call_category": "new_business",
        "next_meeting_scheduled": "true",
        "decision_maker_present": "true",
        "manager_notes": "Handled the price objection well.",
    }
    row.update(overrides)
    return row


# ---- row conversion --------------------------------------------------------


def test_row_converts_to_a_valid_record():
    record = build_record(_row(), datetime(2026, 7, 27, 9, 0, tzinfo=timezone.utc))
    assert record.call_id == "CALL_001"
    assert record.source == "historical_seed"
    assert record.status == "completed"
    assert record.analysis.guardrail_status == "pass"


def test_seed_preserves_the_corpus_call_id():
    assert build_record(_row(call_id="CALL_024"), datetime.now(timezone.utc)).call_id == "CALL_024"


def test_seed_preserves_agent_name_outcome_objection_and_scores():
    record = build_record(
        _row(
            agent_name="Michael Ben-David",
            sale_result="No Sale",
            main_objection="competitor",
            agent_performance_score="3",
            lead_quality_score="2",
        ),
        datetime.now(timezone.utc),
    )
    assert record.agent_name == "Michael Ben-David"
    assert record.analysis.call_outcome == "No Sale"
    assert record.analysis.main_objection == "competitor"
    assert record.analysis.agent_performance_score == 3
    assert record.analysis.lead_quality_score == 2


def test_seed_preserves_the_transcript_verbatim():
    transcript = "Agent: Verbatim line.\nCustomer: Second line."
    record = build_record(_row(transcript=transcript), datetime.now(timezone.utc))
    assert record.analysis.transcript == transcript


@pytest.mark.parametrize(
    "raw,expected",
    [("Sale", "Sale"), ("No Sale", "No Sale"), ("Follow-up Needed", "Follow-up Needed"), ("sale", "Sale")],
)
def test_outcome_is_canonicalized(raw, expected):
    assert canonical_outcome(raw) == expected


def test_mixed_sentiment_maps_to_neutral_not_a_guess():
    assert canonical_sentiment("mixed") == "neutral"


def test_unknown_sentiment_is_none_not_defaulted():
    assert canonical_sentiment("ecstatic") is None


# ---- no fabricated AI content ---------------------------------------------


def test_seed_never_fabricates_confidence_or_risk_level():
    record = build_record(_row(), datetime.now(timezone.utc))
    assert record.analysis.confidence is None
    assert record.analysis.risk_level is None


def test_seed_never_fabricates_similar_calls():
    """No RAG retrieval runs during seeding, so there are no citations."""
    assert build_record(_row(), datetime.now(timezone.utc)).analysis.similar_calls == []


def test_seed_never_fabricates_a_follow_up_email():
    assert build_record(_row(), datetime.now(timezone.utc)).analysis.suggested_follow_up_email == ""


def test_coaching_feedback_uses_manager_notes_verbatim():
    record = build_record(_row(manager_notes="Specific note."), datetime.now(timezone.utc))
    assert record.analysis.coaching_feedback == ["Specific note."]


def test_coaching_feedback_is_empty_when_no_manager_notes_exist():
    assert build_record(_row(manager_notes=""), datetime.now(timezone.utc)).analysis.coaching_feedback == []


def test_customer_name_is_null_because_the_corpus_has_none():
    assert build_record(_row(), datetime.now(timezone.utc)).customer_name is None


def test_call_summary_only_restates_structured_columns():
    summary = build_call_summary(_row(main_objection="price", sale_result="Sale"))
    assert "price" in summary
    assert "Sale" in summary
    assert "Sarah Levi" in summary


def test_detected_signals_only_restate_explicit_columns():
    signals = build_detected_signals(_row(main_objection="timing", closing_attempt="weak"))
    assert "timing objection" in signals
    assert "weak closing attempt" in signals


def test_no_objection_produces_no_objection_signal():
    assert not any("objection" in s for s in build_detected_signals(_row(main_objection="none")))


# ---- deterministic attention ----------------------------------------------


def test_seed_derives_recoverable_opportunity_deterministically():
    record = build_record(_row(lead_quality_score="5", sale_result="No Sale"), datetime.now(timezone.utc))
    assert record.analysis.attention.required is True
    assert record.analysis.attention.category == "recoverable_opportunity"
    assert record.analysis.recovery_opportunity.detected is True


def test_seed_derives_human_review_for_an_unresolved_follow_up():
    record = build_record(
        _row(follow_up_needed="true", next_meeting_scheduled="false", lead_quality_score="2"),
        datetime.now(timezone.utc),
    )
    assert record.analysis.attention.category == "human_review"


def test_seed_derives_critical_coaching():
    record = build_record(_row(agent_performance_score="2", lead_quality_score="2"), datetime.now(timezone.utc))
    assert record.analysis.attention.category == "critical_coaching"


def test_seed_derives_customer_dissatisfaction():
    record = build_record(
        _row(customer_sentiment="negative", agent_performance_score="4", lead_quality_score="2"),
        datetime.now(timezone.utc),
    )
    assert record.analysis.attention.category == "customer_dissatisfaction"


def test_a_clean_sale_needs_no_attention():
    record = build_record(
        _row(sale_result="Sale", lead_quality_score="5", agent_performance_score="5", customer_sentiment="positive"),
        datetime.now(timezone.utc),
    )
    assert record.analysis.attention.required is False


def test_seed_attention_is_reproducible():
    row = _row(lead_quality_score="4", sale_result="No Sale")
    first = build_record(row, datetime.now(timezone.utc)).analysis.attention
    second = build_record(row, datetime.now(timezone.utc)).analysis.attention
    assert first.priority_score == second.priority_score
    assert first.category == second.category


# ---- deterministic dates ---------------------------------------------------


def _rows_for_agents(agents, per_agent=6):
    rows = []
    n = 1
    for agent in agents:
        for _ in range(per_agent):
            rows.append(_row(call_id=f"CALL_{n:03d}", agent_name=agent))
            n += 1
    return rows


AGENTS = ["Sarah Levi", "Daniel Cohen", "Michael Ben-David", "Noa Friedman"]


def test_dates_are_identical_across_runs_for_the_same_anchor():
    rows = _rows_for_agents(AGENTS)
    first = {r["call_id"]: dt for r, dt in assign_timestamps(rows, ANCHOR)}
    second = {r["call_id"]: dt for r, dt in assign_timestamps(list(reversed(rows)), ANCHOR)}
    assert first == second, "output must not depend on input row order"


def test_dates_are_never_in_the_future_relative_to_the_anchor():
    for _, created_at in assign_timestamps(_rows_for_agents(AGENTS), ANCHOR):
        assert created_at.date() < ANCHOR


def test_corpus_spans_at_least_sixty_days():
    dates = [dt.date() for _, dt in assign_timestamps(_rows_for_agents(AGENTS), ANCHOR)]
    assert (max(dates) - min(dates)).days >= 60


def test_every_agent_appears_in_both_thirty_day_windows():
    assigned = assign_timestamps(_rows_for_agents(AGENTS), ANCHOR)
    for agent in AGENTS:
        offsets = [(ANCHOR - dt.date()).days for row, dt in assigned if row["agent_name"] == agent]
        current = [o for o in offsets if 0 <= o <= 30]
        previous = [o for o in offsets if 30 < o <= 60]
        assert len(current) >= 2, f"{agent} needs >= 2 calls in the current 30d window, got {current}"
        assert len(previous) >= 2, f"{agent} needs >= 2 calls in the previous 30d window, got {previous}"


def test_every_agent_appears_in_both_seven_day_windows():
    assigned = assign_timestamps(_rows_for_agents(AGENTS), ANCHOR)
    for agent in AGENTS:
        offsets = [(ANCHOR - dt.date()).days for row, dt in assigned if row["agent_name"] == agent]
        assert any(o <= 7 for o in offsets), f"{agent} has no call in the current 7d window"
        assert any(7 < o <= 14 for o in offsets), f"{agent} has no call in the previous 7d window"


def test_offsets_come_from_the_fixed_table():
    assigned = assign_timestamps(_rows_for_agents(["Solo Agent"], per_agent=6), ANCHOR)
    offsets = sorted((ANCHOR - dt.date()).days for _, dt in assigned)
    assert offsets == sorted(AGENT_BASE_DAY_OFFSETS)


def test_all_timestamps_are_utc():
    for _, created_at in assign_timestamps(_rows_for_agents(AGENTS), ANCHOR):
        assert created_at.tzinfo is not None
        assert created_at.utcoffset().total_seconds() == 0


# ---- against the real corpus ----------------------------------------------


@pytest.mark.skipif(not CSV_PATH.exists(), reason="historical CSV not present")
def test_real_corpus_converts_completely():
    rows = read_rows(CSV_PATH)
    assert len(rows) == 24, "the curated corpus is 24 calls"
    records = [build_record(row, dt) for row, dt in assign_timestamps(rows, ANCHOR)]
    assert len(records) == 24
    assert {r.call_id for r in records} == {f"CALL_{i:03d}" for i in range(1, 25)}
    assert all(r.source == "historical_seed" for r in records)
    assert all(r.status == "completed" for r in records)
    assert all(r.analysis.guardrail_status == "pass" for r in records)


@pytest.mark.skipif(not CSV_PATH.exists(), reason="historical CSV not present")
def test_real_corpus_covers_every_window_for_every_agent():
    rows = read_rows(CSV_PATH)
    assigned = assign_timestamps(rows, ANCHOR)
    agents = {row["agent_name"] for row in rows}
    assert len(agents) == 4
    for agent in agents:
        offsets = [(ANCHOR - dt.date()).days for row, dt in assigned if row["agent_name"] == agent]
        assert len([o for o in offsets if 0 <= o <= 30]) >= 2
        assert len([o for o in offsets if 30 < o <= 60]) >= 2


@pytest.mark.skipif(not CSV_PATH.exists(), reason="historical CSV not present")
def test_real_corpus_keeps_outcomes_and_never_invents_confidence():
    rows = read_rows(CSV_PATH)
    records = [build_record(row, dt) for row, dt in assign_timestamps(rows, ANCHOR)]
    assert all(r.analysis.confidence is None for r in records)
    assert all(r.analysis.similar_calls == [] for r in records)
    assert {r.analysis.call_outcome for r in records} <= {"Sale", "No Sale", "Follow-up Needed"}


# ---- CLI path handling (container-shallow-path regression) ----------------
#
# services/call_data_service/scripts/seed_historical_calls.py used to compute
# `Path(__file__).resolve().parents[3]` as an eagerly-evaluated argparse
# default -- before `parse_args()` ever ran. Inside the Docker image, this
# file executes from /service/scripts/seed_historical_calls.py, which has no
# 4th parent, so even `--help` raised IndexError. The fixes:
#   1. the default is now `None` at the argparse level (no path is computed
#      merely to build the parser or print --help);
#   2. `default_csv_path()` resolves the local-repo path only when needed,
#      guarded by `len(parents) > 3`, and falls back to a plain literal
#      instead of indexing a parent that may not exist.
#
# The tests below actually reproduce the shallow /service/... layout on disk
# (copying the real `app/` package alongside a copy of the script, exactly
# like the Dockerfile's `COPY app ./app` + `COPY scripts ./scripts` into
# `/service`) and invoke it as a real subprocess -- the only way to prove
# `Path(__file__).resolve().parents` genuinely has few entries, rather than
# asserting against this test file's own (deep) location.


@pytest.fixture
def shallow_service_layout(tmp_path) -> Path:
    """Builds tmp_path/service/{app,scripts}/, mirroring the Docker image's
    directory depth exactly, and returns the copied script's path."""
    service_root = tmp_path / "service"
    shutil.copytree(APP_DIR, service_root / "app")
    scripts_dir = service_root / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy2(SCRIPT_PATH, scripts_dir / "seed_historical_calls.py")
    return scripts_dir / "seed_historical_calls.py"


def test_default_csv_path_resolves_to_the_real_repo_csv_locally():
    """Existing local-repo default behavior is preserved: no --csv-path,
    running from the real (deep) checkout location, resolves the same
    data/historical_sales_calls.csv every other local tool uses."""
    assert default_csv_path() == CSV_PATH


def test_help_works_from_a_shallow_docker_style_layout(shallow_service_layout):
    """The exact bug: --help must not crash with IndexError when this file
    runs from a shallow /service/scripts/ path, matching the Docker image."""
    result = subprocess.run(
        [sys.executable, str(shallow_service_layout), "--help"],
        cwd=str(shallow_service_layout.parent),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "IndexError" not in result.stderr
    assert "--csv-path" in result.stdout


def test_explicit_csv_path_works_from_a_shallow_docker_style_layout(shallow_service_layout, tmp_path):
    """An explicit --csv-path must be used verbatim from the shallow layout
    too -- this is the real Docker usage pattern (no local repo checkout,
    only an operator-supplied CSV path)."""
    csv_file = tmp_path / "supplied.csv"
    csv_file.write_text(
        "call_id,agent_name,sale_result,customer_intent,main_objection,customer_sentiment,"
        "agent_performance_score,lead_quality_score,follow_up_needed,next_meeting_scheduled,"
        "call_category,manager_notes,transcript\n"
        'CALL_900,Sarah Levi,Sale,high,none,positive,5,5,false,true,new_business,,'
        '"Agent: hi.\nCustomer: hi."\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(shallow_service_layout), "--csv-path", str(csv_file), "--anchor-date", "2026-07-28", "--dry-run"],
        cwd=str(shallow_service_layout.parent),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "CALL_900" in result.stdout
    assert "Read 1 rows" in result.stdout


def test_missing_csv_path_from_a_shallow_layout_reports_a_clean_error_not_a_crash(shallow_service_layout):
    """No --csv-path, shallow layout, no /data volume mounted -- must fail
    with the documented clean error (exit 2), never an IndexError traceback."""
    result = subprocess.run(
        [sys.executable, str(shallow_service_layout), "--dry-run"],
        cwd=str(shallow_service_layout.parent),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "IndexError" not in result.stderr
    assert "ERROR: CSV not found" in result.stdout


# ---- dry run ---------------------------------------------------------------


@pytest.mark.skipif(not CSV_PATH.exists(), reason="historical CSV not present")
def test_dry_run_writes_nothing_and_needs_no_aws(capsys, monkeypatch):
    """A dry run must not construct a boto3 client or read AWS settings."""
    def explode(*_args, **_kwargs):
        raise AssertionError("dry run must not touch AWS")

    monkeypatch.setattr("seed_historical_calls.build_s3_client", explode)
    monkeypatch.setattr("seed_historical_calls.load_settings", explode)

    exit_code = main(["--csv-path", str(CSV_PATH), "--anchor-date", "2026-07-28", "--dry-run"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "DRY RUN" in output
    assert "CALL_001" in output


def test_missing_csv_returns_an_error_code(tmp_path):
    assert main(["--csv-path", str(tmp_path / "nope.csv"), "--dry-run"]) == 2


def test_missing_csv_path_reports_the_exact_path_in_a_clear_message(tmp_path, capsys):
    missing = tmp_path / "nope.csv"
    exit_code = main(["--csv-path", str(missing), "--dry-run"])
    assert exit_code == 2
    assert f"ERROR: CSV not found at {missing}" in capsys.readouterr().out


def test_explicit_csv_path_is_used_verbatim_over_any_default(tmp_path, capsys):
    """--csv-path always wins, even when a real default would also resolve."""
    csv_file = tmp_path / "custom_name.csv"
    csv_file.write_text(
        "call_id,agent_name,sale_result,customer_intent,main_objection,customer_sentiment,"
        "agent_performance_score,lead_quality_score,follow_up_needed,next_meeting_scheduled,"
        "call_category,manager_notes,transcript\n"
        'CALL_901,Daniel Cohen,No Sale,low,price,neutral,3,2,false,false,renewal,,'
        '"Agent: hi.\nCustomer: hi."\n',
        encoding="utf-8",
    )
    exit_code = main(["--csv-path", str(csv_file), "--anchor-date", "2026-07-28", "--dry-run"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert str(csv_file) in output
    assert "CALL_901" in output


# ---- seeding through the repository abstraction ---------------------------


@pytest.mark.skipif(not CSV_PATH.exists(), reason="historical CSV not present")
def test_seeded_records_write_through_the_repository_and_never_hit_bedrock(repository, fake_s3):
    """The seed uses the same repository the API does, so the Bedrock-prefix
    guard protects seeding exactly as it protects live writes."""
    rows = read_rows(CSV_PATH)
    for row, created_at in assign_timestamps(rows, ANCHOR):
        repository.put_record(build_record(row, created_at))

    assert len(fake_s3.objects) == 24
    assert all(k.startswith("xsight/application/analyzed-calls/v1/") for k in fake_s3.objects)
    assert not any(k.startswith("xsight/bedrock/") for k in fake_s3.objects)


@pytest.mark.skipif(not CSV_PATH.exists(), reason="historical CSV not present")
def test_reseeding_is_idempotent(repository, fake_s3):
    rows = read_rows(CSV_PATH)
    dated = assign_timestamps(rows, ANCHOR)
    for row, created_at in dated:
        repository.put_record(build_record(row, created_at))
    for row, created_at in dated:
        repository.put_record(build_record(row, created_at))
    assert len(fake_s3.objects) == 24, "re-running the seed must not duplicate objects"


@pytest.mark.skipif(not CSV_PATH.exists(), reason="historical CSV not present")
def test_seeded_corpus_produces_a_working_overview(repository):
    """The real end state: 24 seeded calls aggregate into a valid Overview."""
    from app.aggregation import build_overview
    from app.repository import window_bounds

    rows = read_rows(CSV_PATH)
    for row, created_at in assign_timestamps(rows, ANCHOR):
        repository.put_record(build_record(row, created_at))

    now = datetime(2026, 7, 28, 23, 0, tzinfo=timezone.utc)
    start, end, prev_start, prev_end = window_bounds("30d", now)
    loaded = repository.load_range(prev_start, end)
    overview = build_overview(
        all_records=loaded.records,
        skipped_count=loaded.skipped_count,
        period="30d",
        current_start=start,
        current_end=end,
        previous_start=prev_start,
        previous_end=prev_end,
        generated_at=now,
    )

    assert overview.data_quality.skipped_malformed_records == 0
    assert overview.kpis.calls_analyzed.current_value == 12   # 3 per agent x 4
    assert overview.kpis.calls_analyzed.previous_value == 8   # 2 per agent x 4
    assert overview.kpis.close_rate.current_value is not None
    assert overview.kpis.average_agent_performance.current_value is not None
    assert len(overview.close_rate_trend) == 4
    assert len(overview.recent_calls) > 0
