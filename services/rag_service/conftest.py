import sys
from pathlib import Path

import pytest

# Ensure `app` is importable regardless of the directory pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture(autouse=True)
def bedrock_env(monkeypatch):
    """Default Bedrock configuration for every test, so tests don't depend
    on the developer's real .env. test_config.py's own tests override/unset
    these explicitly to exercise the missing-configuration path."""
    monkeypatch.setenv("AWS_REGION", "us-east-2")
    monkeypatch.setenv("BEDROCK_KNOWLEDGE_BASE_ID", "TESTKBID123")
    monkeypatch.setenv("BEDROCK_DATA_SOURCE_ID", "TESTDSID456")
    monkeypatch.setenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
    monkeypatch.setenv("BEDROCK_VECTOR_INDEX_NAME", "xsight-historical-calls-index")
    monkeypatch.setenv("XSIGHT_S3_BUCKET", "xsight-test-bucket")
    monkeypatch.setenv("XSIGHT_S3_PREFIX", "xsight/bedrock/historical-calls/v1/")
