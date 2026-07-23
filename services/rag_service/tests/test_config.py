"""Unit tests for app/config.py's settings loader, isolated from the HTTP
layer (see test_main.py for the end-to-end 503 behavior)."""
import pytest

from app.config import ConfigurationError, load_settings


def test_load_settings_succeeds_with_required_vars_present():
    settings = load_settings()  # conftest.py's autouse fixture sets these
    assert settings.aws_region == "us-east-2"
    assert settings.knowledge_base_id == "TESTKBID123"
    assert settings.data_source_id == "TESTDSID456"


def test_missing_knowledge_base_id_raises(monkeypatch):
    monkeypatch.delenv("BEDROCK_KNOWLEDGE_BASE_ID", raising=False)
    with pytest.raises(ConfigurationError, match="BEDROCK_KNOWLEDGE_BASE_ID"):
        load_settings()


def test_missing_region_raises(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    with pytest.raises(ConfigurationError, match="AWS_REGION"):
        load_settings()


def test_all_missing_required_vars_are_listed_together(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("BEDROCK_KNOWLEDGE_BASE_ID", raising=False)
    with pytest.raises(ConfigurationError) as exc_info:
        load_settings()
    assert "AWS_REGION" in str(exc_info.value)
    assert "BEDROCK_KNOWLEDGE_BASE_ID" in str(exc_info.value)


def test_optional_vars_default_to_none_when_unset(monkeypatch):
    monkeypatch.delenv("BEDROCK_DATA_SOURCE_ID", raising=False)
    settings = load_settings()
    assert settings.data_source_id is None
