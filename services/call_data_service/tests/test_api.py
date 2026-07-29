"""HTTP contract tests. Every case runs against the in-memory S3 fake."""
import json

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_repository
from app.main import app
from app.repository import CallRepository
from conftest import FakeS3Client, make_record


@pytest.fixture
def client(fake_s3, settings, monkeypatch):
    """A TestClient whose repository is the in-memory fake.

    `load_settings()` is also stubbed for the list endpoint's paging limits,
    so no test needs real environment variables.
    """
    repo = CallRepository(s3_client=fake_s3, settings=settings)
    app.dependency_overrides[get_repository] = lambda: repo
    monkeypatch.setattr("app.main.load_settings", lambda: settings)
    with TestClient(app) as test_client:
        test_client.fake_s3 = fake_s3
        test_client.repo = repo
        yield test_client
    app.dependency_overrides.clear()


def _payload(call_id="CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c", **overrides):
    body = {
        "call_id": call_id,
        "source": "live_analysis",
        "created_at": "2026-07-27T10:00:00Z",
        "call_date": "2026-07-27",
        "agent_name": "Sarah Levi",
        "customer_name": "Northwind Solutions",
        "router_reasons": [],
        "analysis": {
            "transcript": "Agent: hello.\nCustomer: hi.",
            "call_summary": "A short call.",
            "call_outcome": "No Sale",
            "customer_sentiment": "neutral",
            "agent_performance_score": 4,
            "lead_quality_score": 5,
            "confidence": 0.82,
            "risk_level": "Medium",
            "guardrail_status": "pass",
        },
    }
    body.update(overrides)
    return body


# ---- health ----------------------------------------------------------------


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "call_data_service", "version": "1.0.0"}


# ---- POST /calls -----------------------------------------------------------


def test_post_call_persists_and_returns_the_key(client):
    response = client.post("/calls", json=_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["created"] is True
    assert body["overwritten"] is False
    assert body["key"].startswith("xsight/application/analyzed-calls/v1/year=2026/month=07/day=27/")
    assert body["key"].endswith(".json")


def test_post_call_derives_attention_server_side(client):
    """lead_quality 5 + No Sale -> recoverable_opportunity, computed here
    rather than trusted from the caller."""
    client.post("/calls", json=_payload())
    stored = client.get("/calls/CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c").json()
    attention = stored["analysis"]["attention"]
    assert attention["required"] is True
    assert attention["category"] == "recoverable_opportunity"
    assert attention["priority_score"] > 0
    assert stored["analysis"]["recovery_opportunity"]["detected"] is True


def test_post_call_ignores_caller_supplied_attention(client):
    """A caller cannot inflate its own priority; the server recomputes."""
    payload = _payload()
    payload["analysis"]["attention"] = {
        "required": True,
        "priority": "critical",
        "priority_score": 100,
        "category": "evidence_conflict",
    }
    client.post("/calls", json=payload)
    stored = client.get("/calls/CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c").json()
    assert stored["analysis"]["attention"]["category"] == "recoverable_opportunity"
    assert stored["analysis"]["attention"]["priority_score"] < 100


def test_post_call_derives_status_from_guardrail_status(client):
    payload = _payload()
    payload["analysis"]["guardrail_status"] = "human_review_required"
    client.post("/calls", json=payload)
    stored = client.get("/calls/CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c").json()
    assert stored["status"] == "human_review_required"


def test_post_same_call_id_twice_overwrites_one_object(client):
    first = client.post("/calls", json=_payload())
    second = client.post("/calls", json=_payload())
    assert first.json()["key"] == second.json()["key"]
    assert second.json()["overwritten"] is True
    assert len(client.fake_s3.objects) == 1


def test_post_rejects_a_frontend_generated_call_id(client):
    response = client.post("/calls", json=_payload(call_id="XS-1004"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_post_rejects_a_missing_agent_name(client):
    payload = _payload()
    del payload["agent_name"]
    response = client.post("/calls", json=payload)
    assert response.status_code == 422


def test_post_rejects_an_out_of_range_score(client):
    payload = _payload()
    payload["analysis"]["agent_performance_score"] = 9
    assert client.post("/calls", json=payload).status_code == 422


def test_post_defaults_created_at_when_absent(client):
    payload = _payload()
    del payload["created_at"]
    del payload["call_date"]
    assert client.post("/calls", json=payload).status_code == 201


# ---- GET /calls ------------------------------------------------------------


def _seed(client, count=5):
    for i in range(1, count + 1):
        client.repo.put_record(make_record(f"CALL_0{i:02d}", days_ago=i))


def test_list_returns_summaries_without_transcripts(client):
    _seed(client, 3)
    body = client.get("/calls").json()
    assert body["count"] == 3
    assert "transcript" not in body["calls"][0]


def test_list_is_ordered_newest_first(client):
    _seed(client, 4)
    body = client.get("/calls").json()
    assert [c["call_id"] for c in body["calls"]] == ["CALL_001", "CALL_002", "CALL_003", "CALL_004"]


def test_list_respects_the_limit_and_returns_a_cursor(client):
    _seed(client, 5)
    body = client.get("/calls?limit=2").json()
    assert body["count"] == 2
    assert body["next_cursor"] == body["calls"][-1]["call_id"]


def test_list_cursor_resumes_after_the_previous_page(client):
    _seed(client, 5)
    first = client.get("/calls?limit=2").json()
    second = client.get(f"/calls?limit=2&cursor={first['next_cursor']}").json()
    assert not ({c["call_id"] for c in first["calls"]} & {c["call_id"] for c in second["calls"]})


def test_list_filters_by_agent_name_case_insensitively(client):
    client.repo.put_record(make_record("CALL_001", agent_name="Sarah Levi"))
    client.repo.put_record(make_record("CALL_002", agent_name="Daniel Cohen"))
    body = client.get("/calls?agent_name=sarah   LEVI").json()
    assert body["count"] == 1
    assert body["calls"][0]["agent_name"] == "Sarah Levi"


def test_list_filters_by_status(client):
    client.repo.put_record(make_record("CALL_001", status="completed"))
    client.repo.put_record(make_record("CALL_002", status="human_review_required"))
    body = client.get("/calls?status=human_review_required").json()
    assert [c["call_id"] for c in body["calls"]] == ["CALL_002"]


def test_list_filters_by_source(client):
    client.repo.put_record(make_record("CALL_001", source="historical_seed"))
    client.repo.put_record(
        make_record("CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c", source="live_analysis")
    )
    body = client.get("/calls?source=live_analysis").json()
    assert body["count"] == 1
    assert body["calls"][0]["source"] == "live_analysis"


def test_list_filters_by_date_range(client):
    client.repo.put_record(make_record("CALL_001", days_ago=1))
    client.repo.put_record(make_record("CALL_002", days_ago=40))
    body = client.get("/calls?from_date=2026-07-01").json()
    assert [c["call_id"] for c in body["calls"]] == ["CALL_001"]


def test_list_reports_malformed_records_without_failing(client):
    client.repo.put_record(make_record("CALL_001"))
    client.fake_s3.objects[
        "xsight/application/analyzed-calls/v1/year=2026/month=07/day=10/CALL_002.json"
    ] = b"broken"
    body = client.get("/calls").json()
    assert body["count"] == 1
    assert body["skipped_malformed_records"] == 1


# ---- GET /calls/{call_id} --------------------------------------------------


def test_get_call_returns_the_full_record_with_transcript(client):
    client.repo.put_record(make_record("CALL_007"))
    body = client.get("/calls/CALL_007").json()
    assert body["call_id"] == "CALL_007"
    assert body["analysis"]["transcript"]


def test_get_missing_call_returns_404(client):
    response = client.get("/calls/CALL_999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CALL_NOT_FOUND"


def test_error_bodies_never_leak_bucket_or_key_details(client):
    body = client.get("/calls/CALL_999").json()
    serialized = json.dumps(body)
    assert "xsight-test-bucket" not in serialized
    assert "xsight/application" not in serialized


# ---- GET /overview ---------------------------------------------------------


def test_overview_returns_the_full_contract(client):
    _seed(client, 3)
    body = client.get("/overview?period=7d").json()
    for key in (
        "period",
        "generated_at",
        "executive_summary",
        "kpis",
        "outcome_distribution",
        "close_rate_trend",
        "improved_agents",
        "attention_calls",
        "recent_calls",
        "data_quality",
    ):
        assert key in body, f"missing top-level field: {key}"

    for kpi in (
        "calls_analyzed",
        "close_rate",
        "average_agent_performance",
        "average_lead_quality",
        "calls_requiring_attention",
        "improved_agents_count",
    ):
        assert kpi in body["kpis"], f"missing KPI: {kpi}"
        for field in ("current_value", "previous_value", "absolute_change", "percentage_change", "trend_direction"):
            assert field in body["kpis"][kpi]

    for bucket in ("sale", "no_sale", "follow_up", "uncertain", "unknown"):
        assert bucket in body["outcome_distribution"], f"missing outcome_distribution bucket: {bucket}"


def test_overview_outcome_distribution_reconciles_with_calls_analyzed(client):
    _seed(client, 5)
    body = client.get("/overview?period=30d").json()
    dist = body["outcome_distribution"]
    total = dist["sale"] + dist["no_sale"] + dist["follow_up"] + dist["uncertain"] + dist["unknown"]
    assert total == body["kpis"]["calls_analyzed"]["current_value"]


def test_overview_defaults_to_seven_days(client):
    assert client.get("/overview").json()["period"]["period"] == "7d"


def test_overview_accepts_thirty_days(client):
    assert client.get("/overview?period=30d").json()["period"]["period"] == "30d"


def test_overview_rejects_an_unsupported_period(client):
    assert client.get("/overview?period=90d").status_code == 422


def test_overview_returns_four_trend_buckets(client):
    _seed(client, 3)
    assert len(client.get("/overview?period=30d").json()["close_rate_trend"]) == 4


def test_overview_on_empty_storage_is_a_valid_empty_response(client):
    body = client.get("/overview?period=7d").json()
    assert body["kpis"]["calls_analyzed"]["current_value"] == 0
    assert body["recent_calls"] == []
    assert body["data_quality"]["loaded_records"] == 0


def test_overview_survives_entirely_malformed_storage(client):
    """One bad object must never take down the Overview screen."""
    for i in range(3):
        client.fake_s3.objects[
            f"xsight/application/analyzed-calls/v1/year=2026/month=07/day=2{i}/CALL_00{i}.json"
        ] = b"not json"
    response = client.get("/overview?period=7d")
    assert response.status_code == 200
    assert response.json()["data_quality"]["skipped_malformed_records"] == 3


def test_overview_storage_failure_returns_503(client):
    client.fake_s3.fail_with = RuntimeError("s3 down")
    response = client.get("/overview?period=7d")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "STORAGE_UNAVAILABLE"


def test_overview_reflects_a_posted_live_call(client):
    """End-to-end through the real write path, not a fixture shortcut."""
    client.post("/calls", json=_payload())
    body = client.get("/overview?period=30d").json()
    assert body["kpis"]["calls_analyzed"]["current_value"] == 1
    assert body["recent_calls"][0]["source"] == "live_analysis"
    assert body["attention_calls"][0]["category"] == "recoverable_opportunity"
