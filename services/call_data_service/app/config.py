"""Runtime configuration for the Call Data Service.

Same convention as every other XSight service's config module: plain
`os.environ` reads, no configuration framework, every required variable
reported together in one ConfigurationError rather than failing on the
first one.

AWS credentials are never read here. boto3 resolves them through the
standard credential chain (environment, ~/.aws/credentials, or an instance
role) -- there is no code path in this service that accepts a key.
"""
import os
from dataclasses import dataclass

from app.errors import ConfigurationError

REQUIRED_ENV_VARS = ("AWS_REGION", "XSIGHT_S3_BUCKET")

# The application data prefix. Deliberately a sibling of -- never inside --
# the Bedrock ingestion prefix below, so a live analyzed call can never be
# picked up by a Knowledge Base sync and treated as curated corpus evidence.
DEFAULT_APPLICATION_PREFIX = "xsight/application/analyzed-calls/v1/"

# The Bedrock Knowledge Base data source's inclusionPrefix. This service
# must never write here. Held as configuration (not a bare literal in
# repository.py) so the guard and the real deployed value stay in sync from
# one place, but it is re-validated on every single key we build.
DEFAULT_BEDROCK_FORBIDDEN_PREFIX = "xsight/bedrock/"

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_MAX_LIST_LIMIT = 500
DEFAULT_LIST_LIMIT = 100


@dataclass(frozen=True)
class Settings:
    aws_region: str
    s3_bucket: str
    application_prefix: str
    bedrock_forbidden_prefix: str
    log_level: str
    default_list_limit: int
    max_list_limit: int
    s3_endpoint_url: str | None


def normalize_prefix(raw: str) -> str:
    """Collapse a prefix to the canonical 'a/b/c/' form.

    Leading slashes are stripped (S3 keys are not filesystem paths) and
    exactly one trailing slash is guaranteed, so key construction can always
    be plain concatenation with no double-slash bugs.
    """
    cleaned = (raw or "").strip().strip("/")
    if not cleaned:
        return ""
    return cleaned + "/"


def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def load_settings() -> Settings:
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise ConfigurationError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            f"See services/call_data_service/.env.example."
        )

    application_prefix = normalize_prefix(
        os.environ.get("XSIGHT_APPLICATION_PREFIX", DEFAULT_APPLICATION_PREFIX)
    )
    forbidden_prefix = normalize_prefix(
        os.environ.get("XSIGHT_BEDROCK_FORBIDDEN_PREFIX", DEFAULT_BEDROCK_FORBIDDEN_PREFIX)
    )

    if not application_prefix:
        raise ConfigurationError(
            "XSIGHT_APPLICATION_PREFIX resolved to an empty prefix. Refusing to treat the "
            "whole bucket as the application prefix."
        )

    # A configuration that would let application writes land inside the
    # Bedrock ingestion prefix is rejected at startup, not at write time.
    if forbidden_prefix and application_prefix.startswith(forbidden_prefix):
        raise ConfigurationError(
            "XSIGHT_APPLICATION_PREFIX resolves inside the Bedrock Knowledge Base prefix. "
            "Live analyzed calls must never be written where the Knowledge Base can ingest them."
        )

    max_list_limit = _positive_int("MAX_LIST_LIMIT", DEFAULT_MAX_LIST_LIMIT)
    default_list_limit = min(_positive_int("DEFAULT_LIST_LIMIT", DEFAULT_LIST_LIMIT), max_list_limit)

    return Settings(
        aws_region=os.environ["AWS_REGION"],
        s3_bucket=os.environ["XSIGHT_S3_BUCKET"],
        application_prefix=application_prefix,
        bedrock_forbidden_prefix=forbidden_prefix,
        log_level=os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL),
        default_list_limit=default_list_limit,
        max_list_limit=max_list_limit,
        # Present for local testing against an S3-compatible endpoint. Unset
        # in every real deployment, where boto3's default endpoint is used.
        s3_endpoint_url=os.environ.get("S3_ENDPOINT_URL") or None,
    )
