"""Deterministic Bedrock Retrieve filter builder.

Builds at most one `equals` metadata filter from client-supplied filter
criteria, using only fields the shared ingestion schema
(services/rag_service/ingestion/metadata_schema.json) marks
`allowed_for_filtering: true`. This is the single source of truth for which
fields may be used as filters — nothing here hardcodes a second copy of
that list, per the ingestion pipeline's own "single shared policy source"
design (see services/rag_service/ingestion/schema_loader.py).

Policy (see services/rag_service/ingestion/README.md, "Small-corpus filter
policy"):
    - No hard filter by default.
    - At most one filter at a time — combining multiple restrictive filters
      can easily return zero results from a 24-document corpus.
    - Filters are built deterministically from the allowlist — an LLM never
      generates filter JSON, and an unrecognized key is dropped, not
      silently coerced into something it wasn't.
"""
import json
import os
from collections.abc import Mapping
from pathlib import Path

# services/rag_service/app/filters.py -> parents[1] is services/rag_service/,
# which contains ingestion/metadata_schema.json in local dev. In Docker,
# app/filters.py sits at /service/app/filters.py, so parents[1] is /service/
# — and the Dockerfile copies the schema to /service/ingestion/metadata_schema.json
# to match. Same index works in both layouts; no length-guard needed (unlike
# HISTORICAL_CALLS_CSV_PATH in app/main.py, which reaches further up to the
# repo root and does need one).
_DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "ingestion" / "metadata_schema.json"
# `or` (not .get's default arg) so an empty-but-set METADATA_SCHEMA_PATH= in
# .env.example/.env still falls back to the default instead of resolving to
# the current working directory.
METADATA_SCHEMA_PATH = Path(os.environ.get("METADATA_SCHEMA_PATH") or _DEFAULT_SCHEMA_PATH)


class FilterBuildError(RuntimeError):
    """Raised only for genuine misconfiguration (e.g. the schema file is
    missing) — an unrecognized filter *key* from a client is not an error,
    it's silently dropped (see build_filter)."""


def load_filter_allowlist(schema_path: Path = METADATA_SCHEMA_PATH) -> dict[str, dict]:
    """Returns {field_name: field_spec} for every field with
    allowed_for_filtering: true in the shared schema."""
    if not schema_path.exists():
        raise FilterBuildError(f"metadata_schema.json not found at {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return {
        name: spec for name, spec in schema["fields"].items()
        if spec.get("allowed_for_filtering")
    }


def _cast_and_validate(field: str, spec: dict, value) -> bool | int | float | str | None:
    """Casts a client-supplied filter value to the field's declared type and
    checks it against the schema's validation rule (enum, etc.). Returns
    None (meaning: drop this filter) if the value doesn't fit — never
    raises for bad client input, since an invalid filter value is handled
    the same way as an unrecognized key: omitted, not rejected."""
    field_type = spec["type"]
    cast: bool | int | float | str
    try:
        if field_type == "boolean":
            if not isinstance(value, bool):
                return None
            cast = value
        elif field_type == "integer":
            cast = int(value)  # type: ignore[arg-type]
        elif field_type == "number":
            cast = float(value)  # type: ignore[arg-type]
        elif field_type == "string":
            cast = str(value)
        else:
            return None
    except (TypeError, ValueError):
        return None

    rules = spec.get("validation", {})
    if "enum" in rules and cast not in rules["enum"]:
        return None
    if "min" in rules and isinstance(cast, (int, float)) and cast < rules["min"]:
        return None
    if "max" in rules and isinstance(cast, (int, float)) and cast > rules["max"]:
        return None
    return cast


def build_filter(
    requested_filters: Mapping[str, object] | None,
    allowlist: dict[str, dict],
) -> tuple[dict | None, str | None, list[str]]:
    """Builds a Bedrock `equals` filter from at most one valid, allowlisted
    field.

    Returns (bedrock_filter, applied_field_name, dropped_keys):
        - bedrock_filter: {"equals": {"key": ..., "value": ...}} or None if
          no valid filter was found (semantic-only retrieval follows).
        - applied_field_name: the field actually used, or None.
        - dropped_keys: every requested key that was ignored, either
          because it isn't in the allowlist or its value didn't validate —
          reported back in retrieval_metadata, never silently swallowed.
    """
    if not requested_filters:
        return None, None, []

    dropped: list[str] = []
    # Deterministic order: iterate the caller's own dict order (Python
    # dicts preserve insertion order) so "at most one filter" picks the
    # first one the caller listed, not an arbitrary one.
    for field, raw_value in requested_filters.items():
        if field not in allowlist:
            dropped.append(field)
            continue
        cast_value = _cast_and_validate(field, allowlist[field], raw_value)
        if cast_value is None:
            dropped.append(field)
            continue
        # First valid filter wins — policy is "at most one filter at a time".
        remaining_unexamined = [k for k in requested_filters if k not in dropped and k != field]
        dropped.extend(remaining_unexamined)
        return {"equals": {"key": field, "value": cast_value}}, field, dropped

    return None, None, dropped
