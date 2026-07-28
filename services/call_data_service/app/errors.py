"""Typed errors for the Call Data Service.

Kept framework-agnostic (plain exceptions, no FastAPI imports) exactly like
services/rag_service/app/config.py and app/bedrock_client.py do -- app/main.py
owns the exception handlers that translate these into stable HTTP responses.
No handler ever puts an AWS error code, bucket name, key, or credential
detail into a response body; those are logged server-side only.
"""


class ConfigurationError(RuntimeError):
    """Required runtime configuration is missing or invalid.

    Mapped to 503 -- a misconfigured service is an availability problem, not
    a client request problem (same convention as rag_service).
    """


class PrefixSafetyError(RuntimeError):
    """A computed S3 key fell outside the configured application prefix, or
    landed inside the Bedrock Knowledge Base ingestion prefix.

    This is a programming error, never a client-triggerable one: the
    repository refuses the operation rather than risking a write that the
    Knowledge Base would later ingest as if it were curated corpus data.
    """


class RecordNotFoundError(LookupError):
    """No stored record exists for the requested call_id. Mapped to 404."""


class MalformedRecordError(ValueError):
    """A stored S3 object could not be parsed or did not validate against
    the current record schema.

    List and aggregate paths never raise this outward -- they count the
    object as skipped and carry on, so one bad object can never take down
    the Overview screen.
    """


class StorageUnavailableError(RuntimeError):
    """S3 could not be reached, or refused the request for a reason that is
    not the caller's fault (credentials, throttling, network). Mapped to 503.
    """
