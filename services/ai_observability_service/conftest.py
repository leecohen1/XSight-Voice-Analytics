import sys
import tempfile
from pathlib import Path

import pytest

# Ensure `app` is importable regardless of the directory pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db import get_connection  # noqa: E402
from app.main import app, get_db, get_query_client  # noqa: E402


@pytest.fixture()
def temp_db_path(tmp_path):
    """A fresh, isolated SQLite file per test — tests never touch the
    configured production database path."""
    return str(tmp_path / "test_ai_observability.db")


@pytest.fixture()
def db_conn(temp_db_path):
    conn = get_connection(temp_db_path)
    yield conn
    conn.close()


@pytest.fixture()
def client(temp_db_path):
    """A TestClient wired to an isolated temp database via FastAPI's
    dependency-override mechanism — the real get_db (which reads
    settings.db_path) is never used in tests. Observability stays disabled
    (no LANGFUSE_* env vars are set in this test environment), so every
    Langfuse-backed dependency (get_observability_client / get_query_client)
    runs through its own real "disabled mode" no-op path -- exactly what a
    credential-free deployment would do."""
    from fastapi.testclient import TestClient

    def _override_get_db():
        conn = get_connection(temp_db_path)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class FakeObservabilityClient:
    """Stands in for app.langfuse_client.ObservabilityClient in tests that
    need `enabled=True` without ever constructing a real Langfuse SDK
    client. Only `.enabled` is read by app/main.py directly (see
    `query_client._observability_client.enabled`)."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled


class FakeQueryClient:
    """Stands in for app.langfuse_query_adapter.LangfuseQueryClient. Tests
    set `.metrics_response` / `.observations_response` to whatever
    Langfuse-Metrics-API-shaped / Observations-API-shaped fixture data they
    want normalize_*() to be exercised against -- this fake never talks to
    a real SDK or network."""

    def __init__(self):
        self._observability_client = FakeObservabilityClient(enabled=True)
        self.metrics_response = None
        self.observations_response = None

    def fetch_metrics(self, *, period_start, period_end, dimensions=None):
        return self.metrics_response

    def fetch_observations(self, *, period_start, period_end, trace_id=None, limit=100):
        if trace_id is None:
            return self.observations_response
        return [o for o in (self.observations_response or []) if o.get("trace_id") == trace_id]


@pytest.fixture()
def client_with_mocked_langfuse(temp_db_path):
    """Like `client`, but with observability forced "enabled" and backed by
    a FakeQueryClient the test controls directly -- for exercising the read
    endpoints' Langfuse-enabled code path without any real SDK/network use."""
    from fastapi.testclient import TestClient

    def _override_get_db():
        conn = get_connection(temp_db_path)
        try:
            yield conn
        finally:
            conn.close()

    fake_query_client = FakeQueryClient()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_query_client] = lambda: fake_query_client
    with TestClient(app) as test_client:
        yield test_client, fake_query_client
    app.dependency_overrides.clear()


def insert_pricing_row(
    conn,
    provider="gemini",
    service="generative_ai",
    model="gemini-test-model",
    billing_unit="per_1k_tokens",
    input_price="0.10",
    output_price="0.40",
    unit_price=None,
    currency="USD",
    effective_from="2020-01-01T00:00:00+00:00",
    effective_to=None,
    source_reference="test fixture",
    is_active=1,
):
    cursor = conn.execute(
        """
        INSERT INTO pricing_config (
            provider, service, model, billing_unit, input_price, output_price,
            unit_price, currency, effective_from, effective_to, source_reference, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            provider, service, model, billing_unit, input_price, output_price,
            unit_price, currency, effective_from, effective_to, source_reference, is_active,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def insert_infra_row(
    conn,
    provider="aws",
    service="ec2",
    resource_name="test-instance",
    monthly_cost_usd="30.00",
    allocation_method="flat_monthly",
    effective_from="2020-01-01T00:00:00+00:00",
    effective_to=None,
    is_active=1,
):
    cursor = conn.execute(
        """
        INSERT INTO infrastructure_cost_config (
            provider, service, resource_name, monthly_cost_usd, allocation_method,
            effective_from, effective_to, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (provider, service, resource_name, monthly_cost_usd, allocation_method, effective_from, effective_to, is_active),
    )
    conn.commit()
    return cursor.lastrowid
