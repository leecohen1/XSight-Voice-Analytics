"""Unit tests for app/langfuse_client.py -- the only module in this
service that touches the Langfuse SDK directly. Every test here mocks the
underlying SDK client (or omits credentials entirely); none makes a real
network call or imports the real `langfuse` package's network layer."""
from dataclasses import replace

import pytest

from app.config import Settings
from app.langfuse_client import (
    ObservabilityClient,
    build_observability_client,
    is_observability_enabled,
)

BASE_SETTINGS = Settings(
    db_path=":memory:",
    max_events_per_batch=100,
    log_level="INFO",
    langfuse_public_key=None,
    langfuse_secret_key=None,
    langfuse_base_url="https://cloud.langfuse.com",
    langfuse_environment="development",
    langfuse_release=None,
    langfuse_timeout_seconds=3.0,
)


def _enabled_settings():
    return replace(BASE_SETTINGS, langfuse_public_key="pk-test", langfuse_secret_key="sk-test")


# --- is_observability_enabled / disabled-mode defaults ------------------------


def test_disabled_when_both_keys_missing():
    assert is_observability_enabled(BASE_SETTINGS) is False


def test_disabled_when_only_public_key_present():
    settings = replace(BASE_SETTINGS, langfuse_public_key="pk-test")
    assert is_observability_enabled(settings) is False


def test_enabled_when_both_keys_present():
    assert is_observability_enabled(_enabled_settings()) is True


def test_build_client_disabled_mode_never_imports_langfuse_sdk(monkeypatch):
    """With no credentials, build_observability_client must not even
    attempt to import/construct the real SDK -- verified by making the
    import raise if it's ever reached."""
    import builtins

    real_import = builtins.__import__

    def _fail_on_langfuse_import(name, *args, **kwargs):
        if name == "langfuse":
            raise AssertionError("must not import langfuse SDK in disabled mode")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fail_on_langfuse_import)
    client = build_observability_client(BASE_SETTINGS)
    assert client.enabled is False


def test_build_client_falls_back_to_disabled_on_construction_error(monkeypatch):
    """Even with credentials present, a broken SDK construction must
    degrade to disabled mode, never raise."""
    import builtins

    real_import = builtins.__import__

    class _BoomLangfuse:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("simulated SDK construction failure")

    def _fake_import(name, *args, **kwargs):
        if name == "langfuse":
            return type("FakeModule", (), {"Langfuse": _BoomLangfuse})
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    client = build_observability_client(_enabled_settings())
    assert client.enabled is False
    assert client._client is None


# --- ObservabilityClient: disabled mode is a pure no-op -----------------------


def test_disabled_client_record_span_is_noop():
    client = ObservabilityClient(client=None, enabled=False)
    assert client.record_span(trace_id="t1", name="rag_retrieval") is None


def test_disabled_client_record_generation_is_noop():
    client = ObservabilityClient(client=None, enabled=False)
    assert client.record_generation(trace_id="t1", name="final_analysis", model="gemini-2.5-flash") is None


def test_disabled_client_update_trace_attributes_returns_false():
    client = ObservabilityClient(client=None, enabled=False)
    assert client.update_trace_attributes(trace_id="t1", name="xsight-call-analysis") is False


def test_disabled_client_create_score_returns_false():
    client = ObservabilityClient(client=None, enabled=False)
    assert client.create_score(name="quality", value=1, data_type="NUMERIC", trace_id="t1") is False


def test_disabled_client_flush_does_not_raise():
    client = ObservabilityClient(client=None, enabled=False)
    client.flush(timeout_seconds=1.0)  # must not raise


def test_disabled_client_create_trace_id_uses_local_deterministic_fallback():
    client = ObservabilityClient(client=None, enabled=False)
    a = client.create_trace_id(seed="call-123")
    b = client.create_trace_id(seed="call-123")
    other = client.create_trace_id(seed="call-456")
    assert a == b
    assert a != other
    assert len(a) == 32
    assert all(c in "0123456789abcdef" for c in a)


# --- ObservabilityClient: enabled mode, mocked SDK client ---------------------


class _FakeObservation:
    def __init__(self):
        self.id = "obs-123"
        self.updates = []

    def update(self, **kwargs):
        self.updates.append(kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeSdkClient:
    def __init__(self):
        self.trace_calls = []
        self.observation_calls = []
        self.trace_updates = []
        self.scores = []
        self.flushed = False
        self._next_observation = None

    def create_trace_id(self, seed):
        self.trace_calls.append(seed)
        return f"trace-for-{seed}"

    def start_as_current_observation(self, **kwargs):
        self.observation_calls.append(kwargs)
        self._next_observation = _FakeObservation()
        return self._next_observation

    def update_current_trace(self, **kwargs):
        self.trace_updates.append(kwargs)

    def create_score(self, **kwargs):
        self.scores.append(kwargs)

    def flush(self):
        self.flushed = True


def test_enabled_client_record_span_calls_sdk_and_sanitizes_metadata():
    sdk = _FakeSdkClient()
    client = ObservabilityClient(client=sdk, enabled=True)
    obs_id = client.record_span(
        trace_id="t1",
        name="rag_retrieval",
        metadata={"results_returned": 3, "customer_notes": "leaked transcript detail"},
    )
    assert obs_id == "obs-123"
    assert sdk.observation_calls[0]["as_type"] == "span"
    assert sdk.observation_calls[0]["trace_context"] == {"trace_id": "t1"}
    recorded_metadata = sdk._next_observation.updates[0]["metadata"]
    assert recorded_metadata == {"results_returned": 3}
    assert "customer_notes" not in recorded_metadata


def test_enabled_client_record_generation_passes_usage_and_cost_through_unchanged():
    sdk = _FakeSdkClient()
    client = ObservabilityClient(client=sdk, enabled=True)
    client.record_generation(
        trace_id="t1",
        name="final_analysis",
        model="gemini-2.5-flash",
        usage_details={"input": 500, "output": 200},
        cost_details={"total": "0.0034"},
    )
    assert sdk.observation_calls[0]["as_type"] == "generation"
    assert sdk.observation_calls[0]["model"] == "gemini-2.5-flash"
    update_kwargs = sdk._next_observation.updates[0]
    assert update_kwargs["usage_details"] == {"input": 500, "output": 200}
    assert update_kwargs["cost_details"] == {"total": "0.0034"}


def test_enabled_client_record_generation_never_fabricates_missing_usage():
    sdk = _FakeSdkClient()
    client = ObservabilityClient(client=sdk, enabled=True)
    client.record_generation(trace_id="t1", name="final_analysis", model="gemini-2.5-flash")
    update_kwargs = sdk._next_observation.updates[0]
    assert update_kwargs["usage_details"] is None
    assert update_kwargs["cost_details"] is None


def test_enabled_client_failed_status_sets_error_level():
    sdk = _FakeSdkClient()
    client = ObservabilityClient(client=sdk, enabled=True)
    client.record_span(trace_id="t1", name="guardrails_check", status="failed")
    assert sdk._next_observation.updates[0]["level"] == "ERROR"


def test_enabled_client_update_trace_attributes_sanitizes_trace_metadata():
    """The installed SDK (v4.14.1) has no update_current_trace-style call --
    trace-level name/metadata are set via a small root span instead (see
    ObservabilityClient.update_trace_attributes' docstring)."""
    sdk = _FakeSdkClient()
    client = ObservabilityClient(client=sdk, enabled=True)
    ok = client.update_trace_attributes(
        trace_id="t1",
        name="xsight-call-analysis",
        tags=["env:development"],
        metadata={"call_id": "call-1", "customer_name": "should be stripped"},
    )
    assert ok is True
    assert sdk.observation_calls[0]["as_type"] == "span"
    assert sdk.observation_calls[0]["name"] == "xsight-call-analysis"
    assert sdk.observation_calls[0]["trace_context"] == {"trace_id": "t1"}
    recorded = sdk._next_observation.updates[0]["metadata"]
    assert recorded == {"call_id": "call-1", "tags": ["env:development"]}


def test_enabled_client_create_score_is_idempotent_by_score_id():
    sdk = _FakeSdkClient()
    client = ObservabilityClient(client=sdk, enabled=True)
    ok = client.create_score(name="quality", value=1, data_type="NUMERIC", trace_id="t1", score_id="score-1")
    assert ok is True
    assert sdk.scores[0]["score_id"] == "score-1"


def test_enabled_client_flush_calls_sdk_flush():
    sdk = _FakeSdkClient()
    client = ObservabilityClient(client=sdk, enabled=True)
    client.flush(timeout_seconds=2.0)
    assert sdk.flushed is True


# --- Error isolation: observability failure must never raise -----------------


class _BoomSdkClient:
    def create_trace_id(self, seed):
        raise RuntimeError("network error")

    def start_as_current_observation(self, **kwargs):
        raise RuntimeError("network error")

    def update_current_trace(self, **kwargs):
        raise RuntimeError("network error")

    def create_score(self, **kwargs):
        raise RuntimeError("network error")

    def flush(self):
        raise RuntimeError("network error")


@pytest.fixture()
def boom_client():
    return ObservabilityClient(client=_BoomSdkClient(), enabled=True)


def test_record_span_swallows_sdk_exception(boom_client):
    assert boom_client.record_span(trace_id="t1", name="x") is None


def test_record_generation_swallows_sdk_exception(boom_client):
    assert boom_client.record_generation(trace_id="t1", name="x", model="m") is None


def test_update_trace_attributes_swallows_sdk_exception(boom_client):
    assert boom_client.update_trace_attributes(trace_id="t1", name="x") is False


def test_create_score_swallows_sdk_exception(boom_client):
    assert boom_client.create_score(name="x", value=1, data_type="NUMERIC", trace_id="t1") is False


def test_flush_swallows_sdk_exception(boom_client):
    boom_client.flush(timeout_seconds=1.0)  # must not raise


def test_create_trace_id_falls_back_to_local_on_sdk_exception(boom_client):
    trace_id = boom_client.create_trace_id(seed="call-1")
    assert len(trace_id) == 32
