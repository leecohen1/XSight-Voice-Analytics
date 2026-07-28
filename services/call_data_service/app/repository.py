"""S3-backed repository for analyzed call records.

Storage layout (the approved application prefix -- never the Bedrock one):

    <application_prefix>/year=YYYY/month=MM/day=DD/<call_id>.json

The date partition comes from the record's own `created_at` (UTC), which
makes every window query a prefix scan over a bounded set of month prefixes
instead of a full-bucket list.

Design notes
------------
* The boto3 client is injected, never constructed inside a method, so the
  whole test suite runs against an in-memory fake with zero network access.
* Every key this module produces is validated by `_assert_safe_key` before
  any Get/Put/List. The check is not "did the caller behave" -- it is a hard
  guard that a bug in key construction can never write into the Bedrock
  Knowledge Base ingestion prefix and get silently indexed as curated corpus
  evidence.
* One malformed object never breaks a list or the Overview. Parse/validation
  failures are collected as `SkippedObject` and reported in the response's
  data_quality block instead of raising.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Optional, Protocol

from app.config import Settings
from app.errors import (
    MalformedRecordError,
    PrefixSafetyError,
    RecordNotFoundError,
    StorageUnavailableError,
)
from app.models import AnalyzedCallRecord

logger = logging.getLogger("call_data_service.repository")


class S3ClientProtocol(Protocol):
    """The exact, minimal slice of the boto3 S3 client this service uses."""

    def put_object(self, **kwargs: Any) -> dict: ...
    def get_object(self, **kwargs: Any) -> dict: ...
    def head_object(self, **kwargs: Any) -> dict: ...
    def list_objects_v2(self, **kwargs: Any) -> dict: ...


@dataclass
class SkippedObject:
    key: str
    reason: str


@dataclass
class LoadResult:
    records: list[AnalyzedCallRecord] = field(default_factory=list)
    skipped: list[SkippedObject] = field(default_factory=list)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)


def _is_not_found(exc: Exception) -> bool:
    """True for S3's 'object does not exist' errors.

    Matches on the response code rather than the exception class so this
    works identically against botocore's ClientError and the test fake.
    """
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        code = str(response.get("Error", {}).get("Code", ""))
        if code in {"NoSuchKey", "404", "NotFound"}:
            return True
    return exc.__class__.__name__ in {"NoSuchKey", "NoSuchKeyError"}


def month_prefixes_for_range(start: datetime, end: datetime) -> list[str]:
    """Every 'year=YYYY/month=MM/' partition touching [start, end], inclusive.

    Listing three month prefixes for a 60-day window is dramatically cheaper
    than 60 day-prefix calls, and still far cheaper than scanning the bucket.
    """
    if end < start:
        start, end = end, start
    cursor = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    out: list[str] = []
    while cursor <= last:
        out.append(f"year={cursor.year:04d}/month={cursor.month:02d}/")
        cursor = date(cursor.year + 1, 1, 1) if cursor.month == 12 else date(cursor.year, cursor.month + 1, 1)
    return out


class CallRepository:
    def __init__(self, s3_client: S3ClientProtocol, settings: Settings) -> None:
        self._s3 = s3_client
        self._settings = settings

    # ---- key construction & safety ----------------------------------------

    @property
    def prefix(self) -> str:
        return self._settings.application_prefix

    def build_key(self, call_id: str, created_at: datetime) -> str:
        when = created_at.astimezone(timezone.utc)
        key = (
            f"{self.prefix}"
            f"year={when.year:04d}/month={when.month:02d}/day={when.day:02d}/"
            f"{call_id}.json"
        )
        self._assert_safe_key(key)
        return key

    def _assert_safe_key(self, key: str) -> None:
        forbidden = self._settings.bedrock_forbidden_prefix
        if forbidden and key.startswith(forbidden):
            raise PrefixSafetyError(
                "Refusing to operate on a key inside the Bedrock Knowledge Base prefix."
            )
        if not key.startswith(self.prefix):
            raise PrefixSafetyError(
                "Refusing to operate on a key outside the configured application prefix."
            )
        if ".." in key:
            raise PrefixSafetyError("Refusing to operate on a key containing a path traversal segment.")

    # ---- writes ------------------------------------------------------------

    def put_record(self, record: AnalyzedCallRecord) -> tuple[str, bool]:
        """Write one record. Returns (key, overwritten).

        Idempotent by call_id: the key is a pure function of call_id and the
        record's created_at date, so re-posting the same analysis (an n8n
        retry, for example) replaces the same object rather than creating a
        duplicate.
        """
        key = self.build_key(record.call_id, record.created_at)
        existed = self._object_exists(key)
        body = record.model_dump_json(indent=2).encode("utf-8")
        try:
            self._s3.put_object(
                Bucket=self._settings.s3_bucket,
                Key=key,
                Body=body,
                ContentType="application/json",
            )
        except PrefixSafetyError:
            raise
        except Exception as exc:  # noqa: BLE001 - mapped to a safe 503 upstream
            logger.exception("S3 put_object failed for key %s", key)
            raise StorageUnavailableError("Could not write the record to object storage.") from exc
        return key, existed

    def _object_exists(self, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._settings.s3_bucket, Key=key)
            return True
        except Exception as exc:  # noqa: BLE001
            if _is_not_found(exc):
                return False
            # An ambiguous head failure must not be reported as "new" -- but
            # it also must not fail the write, which is the operation that
            # actually matters. Log and treat as unknown/not-existing.
            logger.warning("head_object was inconclusive for key %s: %s", key, exc.__class__.__name__)
            return False

    # ---- reads -------------------------------------------------------------

    def _list_keys(self, prefix: str) -> Iterable[str]:
        """List every key under `prefix`, following ListObjectsV2 pagination.

        boto3 truncates at 1000 keys per response; not following
        ContinuationToken is the classic silent-data-loss bug, so this is
        an explicit loop rather than a single call.
        """
        token: Optional[str] = None
        while True:
            kwargs: dict[str, Any] = {"Bucket": self._settings.s3_bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            try:
                response = self._s3.list_objects_v2(**kwargs)
            except Exception as exc:  # noqa: BLE001
                logger.exception("S3 list_objects_v2 failed for prefix %s", prefix)
                raise StorageUnavailableError("Could not list records from object storage.") from exc
            for item in response.get("Contents", []) or []:
                key = item.get("Key")
                if key and key.endswith(".json"):
                    yield key
            if response.get("IsTruncated") and response.get("NextContinuationToken"):
                token = response["NextContinuationToken"]
            else:
                return

    def _get_record_at_key(self, key: str) -> AnalyzedCallRecord:
        self._assert_safe_key(key)
        try:
            response = self._s3.get_object(Bucket=self._settings.s3_bucket, Key=key)
        except Exception as exc:  # noqa: BLE001
            if _is_not_found(exc):
                raise RecordNotFoundError(key) from exc
            logger.exception("S3 get_object failed for key %s", key)
            raise StorageUnavailableError("Could not read the record from object storage.") from exc

        body = response.get("Body")
        raw = body.read() if hasattr(body, "read") else body
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise MalformedRecordError(f"{key}: not valid JSON") from exc
        try:
            return AnalyzedCallRecord.model_validate(payload)
        except Exception as exc:  # noqa: BLE001 - pydantic ValidationError
            raise MalformedRecordError(f"{key}: does not match the record schema") from exc

    def get_by_call_id(self, call_id: str) -> AnalyzedCallRecord:
        """Fetch one record without knowing its date partition.

        The key embeds the created_at date, which the caller does not have,
        so this scans the application prefix for the matching `<call_id>.json`
        suffix. Acceptable at this project's scale, and it keeps the stored
        layout partitioned for the window queries that actually dominate.
        """
        suffix = f"/{call_id}.json"
        for key in self._list_keys(self.prefix):
            if key.endswith(suffix):
                return self._get_record_at_key(key)
        raise RecordNotFoundError(call_id)

    def load_all(self) -> LoadResult:
        return self._load_from_prefixes([self.prefix])

    def load_range(self, start: datetime, end: datetime) -> LoadResult:
        """Load every record whose partition could fall in [start, end].

        Partition granularity is a day, so this deliberately over-fetches at
        the edges; callers filter precisely on `created_at`.
        """
        prefixes = [f"{self.prefix}{p}" for p in month_prefixes_for_range(start, end)]
        return self._load_from_prefixes(prefixes)

    def _load_from_prefixes(self, prefixes: list[str]) -> LoadResult:
        result = LoadResult()
        seen: set[str] = set()
        for prefix in prefixes:
            self._assert_safe_key(prefix)
            for key in self._list_keys(prefix):
                if key in seen:
                    continue
                seen.add(key)
                try:
                    result.records.append(self._get_record_at_key(key))
                except MalformedRecordError as exc:
                    logger.warning("Skipping malformed object: %s", exc)
                    result.skipped.append(SkippedObject(key=key, reason=str(exc)))
                except RecordNotFoundError:
                    # Deleted between list and get -- a benign race, not an error.
                    logger.info("Object disappeared between list and get: %s", key)
        return result


def build_s3_client(settings: Settings) -> S3ClientProtocol:
    """Construct the real boto3 client.

    Imported lazily so the test suite (which always injects a fake) never
    needs botocore's credential chain to resolve.
    """
    import boto3

    kwargs: dict[str, Any] = {"region_name": settings.aws_region}
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    return boto3.client("s3", **kwargs)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def window_bounds(period: str, now: Optional[datetime] = None) -> tuple[datetime, datetime, datetime, datetime]:
    """Return (current_start, current_end, previous_start, previous_end).

    Windows are UTC and defined so that:
      * current  = [now - N days, now]      -- INCLUSIVE of now, and so of today
      * previous = [now - 2N days, now - N days)  -- half-open at its end

    They therefore never overlap and never leave a gap between them.
    """
    days = 7 if period == "7d" else 30
    end = now or utc_now()
    start = end - timedelta(days=days)
    prev_end = start
    prev_start = start - timedelta(days=days)
    return start, end, prev_start, prev_end
