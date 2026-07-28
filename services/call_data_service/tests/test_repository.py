"""S3 repository: key generation, prefix safety, pagination, malformed objects."""
import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.errors import PrefixSafetyError, RecordNotFoundError, StorageUnavailableError
from app.repository import CallRepository, month_prefixes_for_range, window_bounds
from conftest import FakeS3Client, make_record


# ---- key generation --------------------------------------------------------


def test_build_key_uses_date_partitions(repository):
    key = repository.build_key("CALL_001", datetime(2026, 7, 4, 9, 0, tzinfo=timezone.utc))
    assert key == "xsight/application/analyzed-calls/v1/year=2026/month=07/day=04/CALL_001.json"


def test_build_key_zero_pads_month_and_day(repository):
    key = repository.build_key("CALL_002", datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc))
    assert "year=2026/month=01/day=05/" in key


def test_build_key_converts_to_utc_before_partitioning(repository):
    """A non-UTC timestamp must partition by its UTC date, not its local one."""
    from datetime import timedelta

    tz = timezone(timedelta(hours=+13))
    # 2026-07-05 01:00 +13:00 is 2026-07-04 12:00 UTC.
    key = repository.build_key("CALL_003", datetime(2026, 7, 5, 1, 0, tzinfo=tz))
    assert "day=04" in key


def test_build_key_is_stable_for_the_same_inputs(repository):
    when = datetime(2026, 7, 4, 9, 0, tzinfo=timezone.utc)
    assert repository.build_key("CALL_001", when) == repository.build_key("CALL_001", when)


# ---- prefix safety ---------------------------------------------------------


def test_writing_into_the_bedrock_prefix_is_refused(fake_s3, settings):
    """The single most important guard in this service: an application write
    must never land where the Knowledge Base would ingest it."""
    bad_settings = replace(settings, application_prefix="xsight/bedrock/historical-calls/v1/")
    repo = CallRepository(s3_client=fake_s3, settings=bad_settings)
    with pytest.raises(PrefixSafetyError):
        repo.build_key("CALL_001", datetime(2026, 7, 4, tzinfo=timezone.utc))
    assert fake_s3.put_calls == []


def test_reading_a_key_outside_the_application_prefix_is_refused(repository):
    with pytest.raises(PrefixSafetyError):
        repository._get_record_at_key("xsight/bedrock/historical-calls/v1/CALL_001.json")


def test_path_traversal_in_a_key_is_refused(repository):
    with pytest.raises(PrefixSafetyError):
        repository._get_record_at_key(
            "xsight/application/analyzed-calls/v1/../../bedrock/historical-calls/v1/CALL_001.json"
        )


def test_config_rejects_an_application_prefix_inside_the_bedrock_prefix(monkeypatch):
    from app.config import load_settings
    from app.errors import ConfigurationError

    monkeypatch.setenv("AWS_REGION", "us-east-2")
    monkeypatch.setenv("XSIGHT_S3_BUCKET", "bucket")
    monkeypatch.setenv("XSIGHT_APPLICATION_PREFIX", "xsight/bedrock/live/")
    with pytest.raises(ConfigurationError):
        load_settings()


def test_config_requires_bucket_and_region(monkeypatch):
    from app.config import load_settings
    from app.errors import ConfigurationError

    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("XSIGHT_S3_BUCKET", raising=False)
    with pytest.raises(ConfigurationError) as exc:
        load_settings()
    # Both missing variables are reported together, not one at a time.
    assert "AWS_REGION" in str(exc.value)
    assert "XSIGHT_S3_BUCKET" in str(exc.value)


def test_config_normalizes_prefix_slashes(monkeypatch):
    from app.config import load_settings

    monkeypatch.setenv("AWS_REGION", "us-east-2")
    monkeypatch.setenv("XSIGHT_S3_BUCKET", "bucket")
    monkeypatch.setenv("XSIGHT_APPLICATION_PREFIX", "/xsight/application/analyzed-calls/v1")
    assert load_settings().application_prefix == "xsight/application/analyzed-calls/v1/"


# ---- writes ----------------------------------------------------------------


def test_put_record_writes_valid_json_at_the_expected_key(repository, fake_s3):
    record = make_record("CALL_001")
    key, overwritten = repository.put_record(record)

    assert overwritten is False
    assert key in fake_s3.objects
    payload = json.loads(fake_s3.objects[key].decode("utf-8"))
    assert payload["call_id"] == "CALL_001"
    assert payload["schema_version"] == "1.0"
    assert payload["analysis"]["call_outcome"] == "Sale"


def test_put_is_idempotent_by_call_id(repository, fake_s3):
    """Re-posting the same call (an n8n retry) overwrites one object rather
    than creating a duplicate."""
    record = make_record("CALL_001")
    key1, first_overwritten = repository.put_record(record)
    key2, second_overwritten = repository.put_record(record)

    assert key1 == key2
    assert first_overwritten is False
    assert second_overwritten is True
    assert len(fake_s3.objects) == 1


def test_put_failure_surfaces_as_storage_unavailable(repository, fake_s3):
    fake_s3.fail_with = RuntimeError("network down")
    with pytest.raises(StorageUnavailableError):
        repository.put_record(make_record("CALL_001"))


# ---- reads -----------------------------------------------------------------


def test_get_by_call_id_returns_the_record(repository):
    repository.put_record(make_record("CALL_007", agent_name="Daniel Cohen"))
    found = repository.get_by_call_id("CALL_007")
    assert found.call_id == "CALL_007"
    assert found.agent_name == "Daniel Cohen"


def test_get_by_call_id_raises_for_a_missing_call(repository):
    with pytest.raises(RecordNotFoundError):
        repository.get_by_call_id("CALL_999")


def test_load_all_returns_every_record(repository):
    for i in range(1, 6):
        repository.put_record(make_record(f"CALL_00{i}", days_ago=i))
    result = repository.load_all()
    assert len(result.records) == 5
    assert result.skipped_count == 0


def test_list_follows_pagination(settings):
    """The continuation-token loop is exercised for real: 7 objects with a
    page size of 2 requires four round trips."""
    fake = FakeS3Client(page_size=2)
    repo = CallRepository(s3_client=fake, settings=settings)
    for i in range(1, 8):
        repo.put_record(make_record(f"CALL_00{i}", days_ago=i))

    result = repo.load_all()
    assert len(result.records) == 7
    assert {r.call_id for r in result.records} == {f"CALL_00{i}" for i in range(1, 8)}


def test_malformed_json_is_skipped_not_raised(repository, fake_s3):
    repository.put_record(make_record("CALL_001"))
    fake_s3.objects[
        "xsight/application/analyzed-calls/v1/year=2026/month=07/day=20/CALL_002.json"
    ] = b"{not json at all"

    result = repository.load_all()
    assert len(result.records) == 1
    assert result.skipped_count == 1
    assert "CALL_002" in result.skipped[0].key


def test_schema_violating_object_is_skipped_not_raised(repository, fake_s3):
    repository.put_record(make_record("CALL_001"))
    fake_s3.objects[
        "xsight/application/analyzed-calls/v1/year=2026/month=07/day=20/CALL_003.json"
    ] = json.dumps({"call_id": "XS-9999", "status": "banana"}).encode("utf-8")

    result = repository.load_all()
    assert len(result.records) == 1
    assert result.skipped_count == 1


def test_every_object_malformed_yields_no_records_and_no_crash(repository, fake_s3):
    for i in range(3):
        fake_s3.objects[
            f"xsight/application/analyzed-calls/v1/year=2026/month=07/day=2{i}/CALL_00{i}.json"
        ] = b"garbage"
    result = repository.load_all()
    assert result.records == []
    assert result.skipped_count == 3


def test_non_json_keys_are_ignored(repository, fake_s3):
    repository.put_record(make_record("CALL_001"))
    fake_s3.objects["xsight/application/analyzed-calls/v1/README.txt"] = b"not a record"
    result = repository.load_all()
    assert len(result.records) == 1
    assert result.skipped_count == 0


def test_list_failure_surfaces_as_storage_unavailable(repository, fake_s3):
    fake_s3.fail_with = RuntimeError("s3 unreachable")
    with pytest.raises(StorageUnavailableError):
        repository.load_all()


# ---- date-range loading ----------------------------------------------------


def test_month_prefixes_span_the_range():
    prefixes = month_prefixes_for_range(
        datetime(2026, 5, 20, tzinfo=timezone.utc), datetime(2026, 7, 4, tzinfo=timezone.utc)
    )
    assert prefixes == ["year=2026/month=05/", "year=2026/month=06/", "year=2026/month=07/"]


def test_month_prefixes_cross_a_year_boundary():
    prefixes = month_prefixes_for_range(
        datetime(2025, 12, 15, tzinfo=timezone.utc), datetime(2026, 1, 10, tzinfo=timezone.utc)
    )
    assert prefixes == ["year=2025/month=12/", "year=2026/month=01/"]


def test_load_range_only_returns_records_in_touched_partitions(repository, now):
    repository.put_record(make_record("CALL_001", days_ago=2, now=now))     # July
    repository.put_record(make_record("CALL_002", days_ago=200, now=now))   # January

    result = repository.load_range(now.replace(month=7, day=1), now)
    assert [r.call_id for r in result.records] == ["CALL_001"]


# ---- window arithmetic -----------------------------------------------------


def test_seven_day_window_bounds(now):
    start, end, prev_start, prev_end = window_bounds("7d", now)
    assert end == now
    assert (end - start).days == 7
    assert prev_end == start                      # contiguous, no gap
    assert (prev_end - prev_start).days == 7


def test_thirty_day_window_bounds(now):
    start, end, prev_start, prev_end = window_bounds("30d", now)
    assert (end - start).days == 30
    assert prev_end == start
    assert (prev_end - prev_start).days == 30


def test_windows_never_overlap(now):
    start, end, prev_start, prev_end = window_bounds("30d", now)
    assert prev_start < prev_end <= start < end
