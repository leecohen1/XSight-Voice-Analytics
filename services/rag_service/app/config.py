"""Runtime configuration for the RAG service's real Amazon Bedrock Knowledge
Base integration (Phase 12).

All values come from environment variables — see .env.example. Nothing here
is hardcoded: the Knowledge Base ID, data source ID, region, embedding model
ID, vector index name, and S3 location are all injected at runtime, per the
project's "do not hardcode the Knowledge Base ID in application logic" rule.

Settings are read once at import time (module-level singleton), matching
how the rest of this service already reads configuration (see
HISTORICAL_CSV_PATH in app/main.py) — no new configuration framework is
introduced.
"""
import os
from dataclasses import dataclass

REQUIRED_ENV_VARS = (
    "AWS_REGION",
    "BEDROCK_KNOWLEDGE_BASE_ID",
)

# Present for completeness / future use (data-source ID is not needed for a
# Retrieve-only call, but is part of the documented runtime configuration
# and is validated the same way so a misconfigured deployment fails the
# same, consistent way regardless of which variable is missing).
OPTIONAL_ENV_VARS = (
    "BEDROCK_DATA_SOURCE_ID",
    "BEDROCK_EMBEDDING_MODEL_ID",
    "BEDROCK_VECTOR_INDEX_NAME",
    "XSIGHT_S3_BUCKET",
    "XSIGHT_S3_PREFIX",
)


class ConfigurationError(RuntimeError):
    """Raised when required runtime configuration is missing. Mapped to a
    503 by the /query endpoint — a configuration problem is a service
    availability problem, not a client request problem."""


@dataclass(frozen=True)
class Settings:
    aws_region: str
    knowledge_base_id: str
    data_source_id: str | None
    embedding_model_id: str | None
    vector_index_name: str | None
    s3_bucket: str | None
    s3_prefix: str | None


def load_settings() -> Settings:
    """Read and validate settings from the environment. Raises
    ConfigurationError listing every missing required variable at once,
    rather than failing on the first one — easier to fix in one pass."""
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise ConfigurationError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            f"See services/rag_service/.env.example."
        )
    return Settings(
        aws_region=os.environ["AWS_REGION"],
        knowledge_base_id=os.environ["BEDROCK_KNOWLEDGE_BASE_ID"],
        data_source_id=os.environ.get("BEDROCK_DATA_SOURCE_ID"),
        embedding_model_id=os.environ.get("BEDROCK_EMBEDDING_MODEL_ID"),
        vector_index_name=os.environ.get("BEDROCK_VECTOR_INDEX_NAME"),
        s3_bucket=os.environ.get("XSIGHT_S3_BUCKET"),
        s3_prefix=os.environ.get("XSIGHT_S3_PREFIX"),
    )
