"""Thin wrapper around boto3's bedrock-agent-runtime Retrieve API.

Retrieve only — RetrieveAndGenerate is never called, per the approved
architecture. This module owns exactly two responsibilities: calling
Retrieve (with the documented retry-without-filter behavior) and mapping
boto3/botocore exceptions into the small set of typed errors app/main.py
knows how to turn into stable HTTP responses. It does not shape the final
API response — that stays in app/main.py.
"""
import logging
from dataclasses import dataclass

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError

from app.config import Settings

logger = logging.getLogger("rag_service")

DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_RETRIES = 2  # botocore-level retries for transient network errors only


class BedrockAccessDeniedError(RuntimeError):
    """Maps to HTTP 502 — the service's own AWS credentials/role are
    misconfigured. Not the client's fault, but not a 500 either: it's a
    known, named upstream-dependency failure mode."""


class BedrockValidationError(RuntimeError):
    """Maps to HTTP 400 — Bedrock rejected the request shape itself (e.g. a
    malformed filter). Should be rare, since app/filters.py only ever
    builds schema-valid filters, but Bedrock is the authority, not us."""


class BedrockThrottlingError(RuntimeError):
    """Maps to HTTP 429."""


class BedrockUnavailableError(RuntimeError):
    """Maps to HTTP 503 — network/timeout/generic AWS service errors."""


@dataclass
class RetrievalOutcome:
    results: list[dict]
    filter_applied: bool
    search_type: str


def _client(settings: Settings):
    config = Config(
        region_name=settings.aws_region,
        connect_timeout=DEFAULT_TIMEOUT_SECONDS,
        read_timeout=DEFAULT_TIMEOUT_SECONDS,
        retries={"max_attempts": DEFAULT_MAX_RETRIES, "mode": "standard"},
    )
    return boto3.client("bedrock-agent-runtime", config=config)


def _raise_for_client_error(exc: ClientError) -> None:
    code = exc.response.get("Error", {}).get("Code", "")
    message = exc.response.get("Error", {}).get("Message", str(exc))
    if code in ("AccessDeniedException",):
        raise BedrockAccessDeniedError(message) from exc
    if code in ("ValidationException",):
        raise BedrockValidationError(message) from exc
    if code in ("ThrottlingException", "TooManyRequestsException"):
        raise BedrockThrottlingError(message) from exc
    # ResourceNotFoundException, InternalServerException, ServiceUnavailable,
    # and anything else unrecognized: treat as an upstream availability
    # problem rather than guessing further.
    raise BedrockUnavailableError(f"{code}: {message}") from exc


def retrieve(
    settings: Settings,
    query_text: str,
    number_of_results: int,
    bedrock_filter: dict | None,
    client=None,
) -> RetrievalOutcome:
    """Calls Retrieve once with the given filter; if a filter was supplied
    and it returns zero results, retries once without it (Small-Corpus
    Filter Policy: "retry without filters if a filtered query returns too
    few results"). Never calls RetrieveAndGenerate."""
    bedrock = client or _client(settings)

    def _call(with_filter: dict | None) -> list[dict]:
        vector_search_config = {
            "numberOfResults": number_of_results,
            "overrideSearchType": "SEMANTIC",  # S3 Vectors does not support HYBRID
        }
        if with_filter:
            vector_search_config["filter"] = with_filter
        try:
            response = bedrock.retrieve(
                knowledgeBaseId=settings.knowledge_base_id,
                retrievalQuery={"text": query_text},
                retrievalConfiguration={"vectorSearchConfiguration": vector_search_config},
            )
        except ClientError as exc:
            _raise_for_client_error(exc)
        except (EndpointConnectionError, ReadTimeoutError) as exc:
            raise BedrockUnavailableError(f"Network error calling Bedrock Retrieve: {exc}") from exc
        return response.get("retrievalResults", [])

    results = _call(bedrock_filter)
    if bedrock_filter and not results:
        logger.info("Filtered retrieve returned 0 results — retrying unfiltered per Small-Corpus Filter Policy.")
        results = _call(None)
        return RetrievalOutcome(results=results, filter_applied=False, search_type="SEMANTIC")

    return RetrievalOutcome(results=results, filter_applied=bool(bedrock_filter), search_type="SEMANTIC")
