"""Shared test fixtures.

Every test in this suite runs against an in-memory S3 fake -- there is no
network access, no botocore credential resolution, and no real bucket
anywhere in the suite.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Ensure `app` is importable regardless of the directory pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import Settings  # noqa: E402
from app.models import AnalyzedCallRecord, CallAnalysis  # noqa: E402
from app.repository import CallRepository  # noqa: E402


class FakeS3Error(Exception):
    """Mimics botocore's ClientError shape closely enough for the
    repository's `_is_not_found` check, without importing botocore."""

    def __init__(self, code: str):
        super().__init__(code)
        self.response = {"Error": {"Code": code}}


class FakeS3Client:
    """In-memory stand-in for the boto3 S3 client.

    Implements real ListObjectsV2 pagination (1000-key pages by default, but
    `page_size` is adjustable so tests can exercise the continuation-token
    loop without creating a thousand objects).
    """

    def __init__(self, page_size: int = 1000):
        self.objects: dict[str, bytes] = {}
        self.page_size = page_size
        self.put_calls: list[str] = []
        self.fail_with: Exception | None = None

    def put_object(self, **kwargs):
        if self.fail_with:
            raise self.fail_with
        key = kwargs["Key"]
        body = kwargs["Body"]
        self.objects[key] = body if isinstance(body, bytes) else str(body).encode("utf-8")
        self.put_calls.append(key)
        return {}

    def get_object(self, **kwargs):
        if self.fail_with:
            raise self.fail_with
        key = kwargs["Key"]
        if key not in self.objects:
            raise FakeS3Error("NoSuchKey")
        return {"Body": _Body(self.objects[key])}

    def head_object(self, **kwargs):
        if kwargs["Key"] not in self.objects:
            raise FakeS3Error("404")
        return {}

    def list_objects_v2(self, **kwargs):
        if self.fail_with:
            raise self.fail_with
        prefix = kwargs.get("Prefix", "")
        token = kwargs.get("ContinuationToken")
        matching = sorted(k for k in self.objects if k.startswith(prefix))
        start = matching.index(token) + 1 if token and token in matching else 0
        page = matching[start : start + self.page_size]
        truncated = (start + self.page_size) < len(matching)
        response = {"Contents": [{"Key": k} for k in page], "IsTruncated": truncated}
        if truncated and page:
            response["NextContinuationToken"] = page[-1]
        return response


class _Body:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):
        return self._data


@pytest.fixture
def settings() -> Settings:
    return Settings(
        aws_region="us-east-2",
        s3_bucket="xsight-test-bucket",
        application_prefix="xsight/application/analyzed-calls/v1/",
        bedrock_forbidden_prefix="xsight/bedrock/",
        log_level="INFO",
        default_list_limit=100,
        max_list_limit=500,
        s3_endpoint_url=None,
    )


@pytest.fixture
def fake_s3() -> FakeS3Client:
    return FakeS3Client()


@pytest.fixture
def repository(fake_s3: FakeS3Client, settings: Settings) -> CallRepository:
    return CallRepository(s3_client=fake_s3, settings=settings)


@pytest.fixture
def now() -> datetime:
    """A pinned 'now' so window arithmetic in tests is never clock-dependent."""
    return datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)


def make_record(
    call_id: str = "CALL_001",
    *,
    days_ago: float = 1,
    now: datetime | None = None,
    agent_name: str = "Sarah Levi",
    status: str = "completed",
    source: str = "historical_seed",
    call_outcome: str | None = "Sale",
    agent_performance_score: int | None = 4,
    lead_quality_score: int | None = 4,
    customer_sentiment: str | None = "positive",
    guardrail_status: str = "pass",
    attention_required: bool = False,
    attention_priority: str = "low",
    attention_priority_score: int = 0,
    attention_category: str = "low_priority",
    confidence: float | None = None,
    risk_level: str | None = None,
) -> AnalyzedCallRecord:
    """Build a valid record with sensible defaults; override only what a
    given test actually cares about."""
    base = now or datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    created_at = base - timedelta(days=days_ago)
    return AnalyzedCallRecord(
        call_id=call_id,
        source=source,
        created_at=created_at,
        call_date=created_at.date(),
        agent_name=agent_name,
        status=status,
        router_reasons=[],
        analysis=CallAnalysis(
            transcript="Agent: hello.\nCustomer: hi.",
            call_summary="A summary.",
            call_outcome=call_outcome,
            customer_sentiment=customer_sentiment,
            agent_performance_score=agent_performance_score,
            lead_quality_score=lead_quality_score,
            confidence=confidence,
            risk_level=risk_level,
            guardrail_status=guardrail_status,
            attention={
                "required": attention_required,
                "priority": attention_priority,
                "priority_score": attention_priority_score,
                "category": attention_category,
            },
        ),
    )
