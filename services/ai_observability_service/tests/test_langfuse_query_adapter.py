"""Unit tests for app/langfuse_query_adapter.py -- both the
LangfuseQueryClient wrapper (error isolation, disabled-mode no-ops) and the
normalize_*() functions (Langfuse-API-shaped fixture data -> XSight's
stable product response shapes). No real Langfuse SDK or network call."""
from app.langfuse_query_adapter import (
    LangfuseQueryClient,
    normalize_call_list,
    normalize_daily_buckets,
    normalize_grouped_breakdown,
    normalize_summary,
)


class _FakeObservabilityClient:
    def __init__(self, enabled, api=None):
        self.enabled = enabled
        self._client = type("C", (), {"api": api})() if api is not None else None


class _BoomApi:
    class metrics:
        @staticmethod
        def metrics(**kwargs):
            raise RuntimeError("network error")

    class observations:
        @staticmethod
        def get_many(**kwargs):
            raise RuntimeError("network error")

    class scores_v3:
        @staticmethod
        def get(**kwargs):
            raise RuntimeError("network error")


class _WorkingApi:
    def __init__(self):
        self.metrics_calls = []
        self.observations_calls = []

        class _Metrics:
            def metrics(inner_self, **kwargs):
                self.metrics_calls.append(kwargs)
                return {"data": [{"usage_input": 10, "usage_output": 5, "count": 1, "call_id": "call-1"}]}

        class _Observations:
            def get_many(inner_self, **kwargs):
                self.observations_calls.append(kwargs)
                return [{"trace_id": "call-1"}]

        self.metrics = _Metrics()
        self.observations = _Observations()


# --- LangfuseQueryClient: disabled mode is a pure no-op -----------------------


def test_fetch_metrics_disabled_returns_none():
    client = LangfuseQueryClient(_FakeObservabilityClient(enabled=False))
    assert client.fetch_metrics(period_start="a", period_end="b") is None


def test_fetch_observations_disabled_returns_none():
    client = LangfuseQueryClient(_FakeObservabilityClient(enabled=False))
    assert client.fetch_observations(period_start="a", period_end="b") is None


def test_fetch_scores_disabled_returns_none():
    client = LangfuseQueryClient(_FakeObservabilityClient(enabled=False))
    assert client.fetch_scores() is None


# --- LangfuseQueryClient: error isolation --------------------------------------


def test_fetch_metrics_swallows_sdk_exception():
    client = LangfuseQueryClient(_FakeObservabilityClient(enabled=True, api=_BoomApi()))
    assert client.fetch_metrics(period_start="a", period_end="b") is None


def test_fetch_observations_swallows_sdk_exception():
    client = LangfuseQueryClient(_FakeObservabilityClient(enabled=True, api=_BoomApi()))
    assert client.fetch_observations(period_start="a", period_end="b") is None


def test_fetch_scores_swallows_sdk_exception():
    client = LangfuseQueryClient(_FakeObservabilityClient(enabled=True, api=_BoomApi()))
    assert client.fetch_scores() is None


# --- LangfuseQueryClient: enabled + working API --------------------------------


def test_fetch_metrics_calls_api_with_period_and_dimensions():
    api = _WorkingApi()
    client = LangfuseQueryClient(_FakeObservabilityClient(enabled=True, api=api))
    result = client.fetch_metrics(period_start="2026-07-01", period_end="2026-08-01", dimensions=["provider"])
    assert result["data"][0]["call_id"] == "call-1"
    assert api.metrics_calls[0]["from_timestamp"] == "2026-07-01"
    assert api.metrics_calls[0]["dimensions"] == ["provider"]


def test_fetch_observations_calls_api_with_trace_id():
    api = _WorkingApi()
    client = LangfuseQueryClient(_FakeObservabilityClient(enabled=True, api=api))
    result = client.fetch_observations(period_start="a", period_end="b", trace_id="call-1")
    assert result == [{"trace_id": "call-1"}]
    assert api.observations_calls[0]["trace_id"] == "call-1"


# --- normalize_summary ---------------------------------------------------------


def test_normalize_summary_none_response_returns_all_none_not_zero():
    summary = normalize_summary(None)
    assert summary["total_input_tokens"] is None
    assert summary["total_output_tokens"] is None
    assert summary["calls_analyzed"] == 0
    assert summary["events_count"] == 0


def test_normalize_summary_empty_data_returns_all_none():
    summary = normalize_summary({"data": []})
    assert summary["total_tokens"] is None


def test_normalize_summary_sums_across_rows_and_dedupes_call_ids():
    metrics = {
        "data": [
            {"usage_input": 500, "usage_output": 200, "count": 2, "call_id": "call-1"},
            {"usage_input": 100, "usage_output": 50, "count": 1, "call_id": "call-1"},
            {"usage_input": 10, "usage_output": 5, "count": 1, "call_id": "call-2"},
        ]
    }
    summary = normalize_summary(metrics)
    assert summary["total_input_tokens"] == 610
    assert summary["total_output_tokens"] == 255
    assert summary["total_tokens"] == 865
    assert summary["calls_analyzed"] == 2
    assert summary["events_count"] == 4


# --- normalize_daily_buckets -----------------------------------------------


def test_normalize_daily_buckets_empty_returns_empty_list():
    assert normalize_daily_buckets(None) == []
    assert normalize_daily_buckets({"data": []}) == []


def test_normalize_daily_buckets_groups_by_date_sorted():
    metrics = {
        "data": [
            {"date": "2026-07-16", "usage_input": 10, "usage_output": 5, "call_id": "c2"},
            {"date": "2026-07-15", "usage_input": 100, "usage_output": 40, "call_id": "c1"},
            {"date": "2026-07-15", "usage_input": 50, "usage_output": 20, "call_id": "c1"},
        ]
    }
    days = normalize_daily_buckets(metrics)
    assert [d["date"] for d in days] == ["2026-07-15", "2026-07-16"]
    assert days[0]["input_tokens"] == 150
    assert days[0]["calls_analyzed"] == 1
    assert days[1]["input_tokens"] == 10


def test_normalize_daily_buckets_skips_rows_missing_date():
    metrics = {"data": [{"usage_input": 10, "usage_output": 5}]}
    assert normalize_daily_buckets(metrics) == []


# --- normalize_grouped_breakdown (shared by-stage / by-provider) --------------


def test_normalize_grouped_breakdown_groups_by_key_sorted():
    metrics = {
        "data": [
            {"pipeline_stage": "final_analysis", "usage_input": 300, "usage_output": 100, "count": 1},
            {"pipeline_stage": "information_extraction", "usage_input": 100, "usage_output": 40, "count": 2},
        ]
    }
    stages = normalize_grouped_breakdown(metrics, "pipeline_stage")
    assert [s["pipeline_stage"] for s in stages] == ["final_analysis", "information_extraction"]
    assert stages[1]["events_count"] == 2


def test_normalize_grouped_breakdown_skips_rows_missing_key():
    metrics = {"data": [{"usage_input": 10, "usage_output": 5, "count": 1}]}
    assert normalize_grouped_breakdown(metrics, "provider") == []


def test_normalize_grouped_breakdown_empty_returns_empty_list():
    assert normalize_grouped_breakdown(None, "provider") == []


# --- normalize_call_list -----------------------------------------------------


def test_normalize_call_list_empty_returns_empty_list():
    assert normalize_call_list(None) == []
    assert normalize_call_list([]) == []


def test_normalize_call_list_groups_by_trace_and_flags_error_as_failed():
    observations = [
        {"trace_id": "call-1", "usage_details": {"input": 100, "output": 40}, "level": "DEFAULT", "start_time": "t1"},
        {"trace_id": "call-1", "usage_details": {"input": 50, "output": 10}, "level": "DEFAULT", "start_time": "t1"},
        {"trace_id": "call-2", "usage_details": {"input": 5, "output": 2}, "level": "ERROR", "start_time": "t2"},
    ]
    calls = {c["call_id"]: c for c in normalize_call_list(observations)}
    assert calls["call-1"]["input_tokens"] == 150
    assert calls["call-1"]["status"] == "success"
    assert calls["call-2"]["status"] == "failed"


def test_normalize_call_list_skips_observations_missing_trace_id():
    observations = [{"usage_details": {"input": 10, "output": 5}, "level": "DEFAULT"}]
    assert normalize_call_list(observations) == []
