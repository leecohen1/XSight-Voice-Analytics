"""Shared loader for metadata_schema.json.

convert_csv_to_documents.py and validate_documents.py both import from here
instead of hardcoding field lists, so the two scripts cannot silently drift
apart. metadata_schema.json is the single policy source; this module just
provides small typed accessors over it.
"""

import json
from pathlib import Path

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent / "metadata_schema.json"


def load_schema(schema_path: Path = DEFAULT_SCHEMA_PATH) -> dict:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def csv_field_names(schema: dict) -> list[str]:
    """All field names backed by a CSV column (excludes generated metadata fields)."""
    return list(schema["fields"].keys())


def fields_with_destination(schema: dict, destination: str) -> list[str]:
    """destination: 'txt' | 'metadata'. Returns field names whose destination
    is that value or 'both'."""
    return [
        name for name, spec in schema["fields"].items()
        if spec["destination"] == destination or spec["destination"] == "both"
    ]


def retrieval_context_fields(schema: dict) -> list[str]:
    for section in schema["txt_structure"]["sections"]:
        if section["name"] == "retrieval_context":
            return section["fields"]
    raise KeyError("retrieval_context section not found in txt_structure")


def retrieval_context_field_labels(schema: dict) -> dict:
    for section in schema["txt_structure"]["sections"]:
        if section["name"] == "retrieval_context":
            return section["field_labels"]
    raise KeyError("retrieval_context section not found in txt_structure")


def section_label(schema: dict, section_name: str) -> str:
    for section in schema["txt_structure"]["sections"]:
        if section["name"] == section_name:
            return section["label"]
    raise KeyError(f"section {section_name!r} not found in txt_structure")


def generated_metadata_values(schema: dict) -> dict:
    """Resolve generated_metadata_fields into {name: value}, following any
    'value_from' pointer back to a top-level schema key (keeps e.g.
    schema_version defined in exactly one place)."""
    resolved = {}
    for name, spec in schema["generated_metadata_fields"].items():
        if "value" in spec:
            resolved[name] = spec["value"]
        elif "value_from" in spec:
            resolved[name] = schema[spec["value_from"]]
        else:
            raise KeyError(f"generated metadata field {name!r} has neither 'value' nor 'value_from'")
    return resolved


def metadata_field_names(schema: dict) -> list[str]:
    """All metadata sidecar keys: CSV-backed fields destined for metadata,
    plus the generated fields. Excludes txt-only fields (transcript, manager_notes)."""
    return fields_with_destination(schema, "metadata") + list(schema["generated_metadata_fields"].keys())


def filter_allowlist(schema: dict) -> list[str]:
    """Field names eligible for the future deterministic filter builder
    (allowed_for_filtering: true in metadata_schema.json). Filter *construction*
    is out of scope here — this only reports which fields are eligible."""
    return [name for name, spec in schema["fields"].items() if spec.get("allowed_for_filtering")]


def cast_value(field: str, spec: dict, raw: str) -> bool | int | float | str:
    """Cast a raw CSV string into the JSON type declared for this field."""
    field_type = spec["type"]
    if field_type == "boolean":
        lowered = raw.strip().lower()
        if lowered not in {"true", "false"}:
            raise ValueError(f"{field}={raw!r} is not a valid boolean")
        return lowered == "true"
    if field_type == "integer":
        return int(raw)
    if field_type == "number":
        return float(raw)
    if field_type == "string":
        return raw
    raise ValueError(f"{field}: unknown schema type {field_type!r}")


def validate_value(field: str, spec: dict, value: object, errors: list[str], call_id: str) -> None:
    """Check a cast value against spec['validation']. Appends human-readable
    messages to errors (does not raise) so callers can collect many at once."""
    rules = spec.get("validation", {})
    if rules.get("non_empty") and (value is None or (isinstance(value, str) and not value.strip())):
        errors.append(f"{call_id}: {field} must not be empty")
    if "enum" in rules and value not in rules["enum"]:
        errors.append(f"{call_id}: {field}={value!r} is not one of {rules['enum']}")
    if "min" in rules and isinstance(value, (int, float)) and value < rules["min"]:
        errors.append(f"{call_id}: {field}={value!r} is below the allowed minimum {rules['min']}")
    if "max" in rules and isinstance(value, (int, float)) and value > rules["max"]:
        errors.append(f"{call_id}: {field}={value!r} is above the allowed maximum {rules['max']}")
