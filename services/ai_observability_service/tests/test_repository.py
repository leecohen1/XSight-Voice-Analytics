"""Unit tests for app/repository.py -- the fixed infrastructure cost
allocation logic this service still owns directly (Langfuse has no
equivalent concept; see repository.py's module docstring)."""
from decimal import Decimal

from conftest import insert_infra_row

from app.repository import get_flat_monthly_infrastructure_cost, get_per_call_share_infrastructure_cost

PERIOD_START = "2026-07-01T00:00:00+00:00"
PERIOD_END = "2026-08-01T00:00:00+00:00"


def test_flat_monthly_sums_all_active_rows_in_window(db_conn):
    insert_infra_row(db_conn, resource_name="ec2", monthly_cost_usd="20.00", allocation_method="flat_monthly")
    insert_infra_row(db_conn, resource_name="n8n", monthly_cost_usd="10.50", allocation_method="flat_monthly")
    total = get_flat_monthly_infrastructure_cost(db_conn, PERIOD_START, PERIOD_END)
    assert total == Decimal("30.50")


def test_flat_monthly_excludes_inactive_rows(db_conn):
    insert_infra_row(db_conn, resource_name="ec2", monthly_cost_usd="20.00", is_active=1)
    insert_infra_row(db_conn, resource_name="retired", monthly_cost_usd="999.00", is_active=0)
    total = get_flat_monthly_infrastructure_cost(db_conn, PERIOD_START, PERIOD_END)
    assert total == Decimal("20.00")


def test_flat_monthly_excludes_rows_outside_effective_window(db_conn):
    insert_infra_row(
        db_conn,
        resource_name="decommissioned",
        monthly_cost_usd="15.00",
        effective_from="2020-01-01T00:00:00+00:00",
        effective_to="2026-01-01T00:00:00+00:00",
    )
    total = get_flat_monthly_infrastructure_cost(db_conn, PERIOD_START, PERIOD_END)
    assert total == Decimal("0")


def test_flat_monthly_no_rows_returns_zero_not_none(db_conn):
    total = get_flat_monthly_infrastructure_cost(db_conn, PERIOD_START, PERIOD_END)
    assert total == Decimal("0")


def test_flat_monthly_includes_per_call_share_rows_too(db_conn):
    """flat_monthly view shows the whole configured monthly cost regardless
    of allocation_method -- only the per_call_share *view* filters by method."""
    insert_infra_row(db_conn, resource_name="ec2", monthly_cost_usd="20.00", allocation_method="per_call_share")
    total = get_flat_monthly_infrastructure_cost(db_conn, PERIOD_START, PERIOD_END)
    assert total == Decimal("20.00")


def test_per_call_share_only_sums_rows_flagged_per_call_share(db_conn):
    insert_infra_row(db_conn, resource_name="ec2", monthly_cost_usd="20.00", allocation_method="flat_monthly")
    insert_infra_row(db_conn, resource_name="rag_index", monthly_cost_usd="5.00", allocation_method="per_call_share")
    total = get_per_call_share_infrastructure_cost(db_conn, PERIOD_START, PERIOD_END)
    assert total == Decimal("5.00")


def test_per_call_share_no_matching_rows_returns_zero(db_conn):
    insert_infra_row(db_conn, resource_name="ec2", monthly_cost_usd="20.00", allocation_method="flat_monthly")
    total = get_per_call_share_infrastructure_cost(db_conn, PERIOD_START, PERIOD_END)
    assert total == Decimal("0")
