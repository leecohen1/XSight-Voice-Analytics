#!/usr/bin/env python3
"""Validate the output of convert_csv_to_documents.py before it gets uploaded
to S3 / ingested into the Bedrock Knowledge Base.

This is an independent check, not a re-run of the converter's own belief
about itself: it re-reads data/historical_sales_calls.csv directly and
cross-checks it against the generated documents/*.txt and
documents/*.txt.metadata.json files. Field lists, types, and validation
rules come from metadata_schema.json (via schema_loader.py) — the same
shared source convert_csv_to_documents.py uses — so this script can never
define "what a valid document looks like" differently than the converter
does.

Checks performed:
    1. Every CSV call_id has exactly one <call_id>.txt and one
       <call_id>.txt.metadata.json file, no missing or extra calls, no
       duplicate call_ids in the CSV itself.
    2. Correct sidecar naming (<call_id>.txt.metadata.json next to <call_id>.txt).
    3. The transcript and the manager_notes are each preserved verbatim
       inside the .txt document (data/historical_sales_calls.csv is
       immutable — this is the check that would catch an accidental edit).
    4. The TXT document's "Retrieval Context" values match the CSV's
       customer_segment / industry / main_objection / customer_intent /
       customer_sentiment columns exactly.
    5. Each metadata.json is valid JSON, has a top-level "metadataAttributes"
       object, contains exactly the expected metadata keys (schema fields
       destined for "metadata" plus the generated fields) — no missing, no
       unexpected extra keys.
    6. Every metadata value has the correct JSON type and passes its
       schema-declared validation rule (enum / min / max / non_empty).
    7. transcript and manager_notes are absent from every metadata.json.
    8. The generated fields (source_type, dataset_version, schema_version)
       have their expected constant values.
    9. Regeneration is deterministic: re-running the converter into a scratch
       directory produces byte-identical files to what's already on disk.

Also reports (not treated as failures): metadata key count per document,
maximum serialized metadata.json size, which sidecar is largest, and any
open Bedrock vector-store compatibility question — this script never trims
fields based on an assumed backend limit; it only measures and reports.

Usage:
    python services/rag_service/ingestion/validate_documents.py
    python services/rag_service/ingestion/validate_documents.py --output-dir /tmp/bedrock_docs

Exit code 0 if there are no errors (warnings are still printed), 1 otherwise.
"""

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path

import schema_loader
import convert_csv_to_documents as converter

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV_PATH = ROOT / "data" / "historical_sales_calls.csv"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def load_csv_rows(csv_path: Path, errors: list[str]) -> dict[str, dict]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows_by_id = {}
        for i, row in enumerate(reader, start=2):
            call_id = row["call_id"].strip()
            if call_id in rows_by_id:
                errors.append(f"CSV row {i}: duplicate call_id {call_id}")
                continue
            rows_by_id[call_id] = row
        return rows_by_id


def check_retrieval_context(call_id: str, content: str, row: dict, schema: dict, errors: list[str]) -> None:
    context_label = schema_loader.section_label(schema, "retrieval_context")
    context_fields = schema_loader.retrieval_context_fields(schema)
    context_field_labels = schema_loader.retrieval_context_field_labels(schema)

    marker = f"{context_label}:\n"
    if marker not in content:
        errors.append(f"{call_id}: '{context_label}:' section not found in document")
        return
    block = content.split(marker, 1)[1].split("\n\n", 1)[0]
    lines = {}
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- ") and ": " in line:
            label, value = line[2:].split(": ", 1)
            lines[label] = value

    for field in context_fields:
        expected_label = context_field_labels[field]
        expected_value = row[field]
        if expected_label not in lines:
            errors.append(f"{call_id}: Retrieval Context is missing '{expected_label}'")
        elif lines[expected_label] != expected_value:
            errors.append(
                f"{call_id}: Retrieval Context '{expected_label}' = {lines[expected_label]!r}, "
                f"expected {expected_value!r} (from CSV column {field!r})"
            )


def check_metadata(call_id: str, meta_path: Path, row: dict, schema: dict, errors: list[str], warnings: list[str]) -> dict | None:
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"{call_id}: metadata.json is not valid JSON ({e})")
        return None
    if "metadataAttributes" not in payload:
        errors.append(f"{call_id}: metadata.json is missing the top-level \"metadataAttributes\" key")
        return None
    attributes = payload["metadataAttributes"]

    expected_keys = set(schema_loader.metadata_field_names(schema))
    present_keys = set(attributes.keys())
    missing = expected_keys - present_keys
    extra = present_keys - expected_keys
    if missing:
        errors.append(f"{call_id}: metadata.json is missing keys: {sorted(missing)}")
    if extra:
        errors.append(f"{call_id}: metadata.json has unexpected extra keys: {sorted(extra)}")

    for field in {"transcript", "manager_notes"} & present_keys:
        errors.append(f"{call_id}: metadata.json must not contain '{field}' — it belongs in the TXT document only")

    for field in schema_loader.fields_with_destination(schema, "metadata"):
        if field not in attributes:
            continue
        spec = schema["fields"][field]
        value = attributes[field]
        field_type = spec["type"]
        type_ok = (
            (field_type == "boolean" and isinstance(value, bool)) or
            (field_type == "integer" and isinstance(value, int) and not isinstance(value, bool)) or
            (field_type == "number" and isinstance(value, (int, float)) and not isinstance(value, bool)) or
            (field_type == "string" and isinstance(value, str))
        )
        if not type_ok:
            errors.append(f"{call_id}: {field} should be a JSON {field_type}, got {type(value).__name__} ({value!r})")
            continue
        schema_loader.validate_value(field, spec, value, errors, call_id)

    generated = schema_loader.generated_metadata_values(schema)
    for field, expected_value in generated.items():
        actual = attributes.get(field)
        if actual != expected_value:
            errors.append(f"{call_id}: generated field {field}={actual!r}, expected constant {expected_value!r}")

    return attributes


def check_deterministic_regeneration(csv_path: Path, output_dir: Path, schema_path: Path, errors: list[str]) -> None:
    documents_dir = output_dir / "documents"
    with tempfile.TemporaryDirectory(prefix="xsight_bedrock_regen_") as tmp:
        tmp_dir = Path(tmp)
        rc = converter.convert(csv_path, tmp_dir, schema_path)
        if rc != 0:
            errors.append("deterministic regeneration check: converter failed on a fresh run")
            return
        tmp_documents_dir = tmp_dir / "documents"
        for existing_file in sorted(documents_dir.glob("*")):
            if existing_file.name == "manifest.json":
                continue
            regenerated_file = tmp_documents_dir / existing_file.name
            if not regenerated_file.exists():
                errors.append(f"deterministic regeneration check: {existing_file.name} missing from a fresh run")
                continue
            if existing_file.read_bytes() != regenerated_file.read_bytes():
                errors.append(f"deterministic regeneration check: {existing_file.name} differs between the "
                               f"committed output and a fresh regeneration from the same CSV")


def validate(csv_path: Path, output_dir: Path, schema_path: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    schema = schema_loader.load_schema(schema_path)

    if not csv_path.exists():
        print(f"ERROR: CSV not found at {csv_path}", file=sys.stderr)
        return 1
    documents_dir = output_dir / "documents"
    if not documents_dir.exists():
        print(f"ERROR: {documents_dir} does not exist — run convert_csv_to_documents.py first", file=sys.stderr)
        return 1

    csv_rows = load_csv_rows(csv_path, errors)
    csv_ids = set(csv_rows.keys())

    # glob("*.txt") only matches names literally ending in ".txt" — a name like
    # "CALL_001.txt.metadata.json" ends in ".json" and is never matched here,
    # so no extra filter is needed to exclude the metadata sidecars.
    txt_files = {p.name[:-4]: p for p in documents_dir.glob("*.txt")}
    meta_files = {}
    for p in documents_dir.glob("*.txt.metadata.json"):
        call_id = p.name[: -len(".txt.metadata.json")]
        meta_files[call_id] = p

    txt_ids = set(txt_files.keys())
    meta_ids = set(meta_files.keys())

    missing_txt = csv_ids - txt_ids
    missing_meta = csv_ids - meta_ids
    orphan_txt = txt_ids - csv_ids
    orphan_meta = meta_ids - csv_ids

    if missing_txt:
        errors.append(f"Missing .txt document for call_ids: {sorted(missing_txt)}")
    if missing_meta:
        errors.append(f"Missing .txt.metadata.json for call_ids: {sorted(missing_meta)}")
    if orphan_txt:
        errors.append(f"Orphan .txt files with no matching CSV row: {sorted(orphan_txt)}")
    if orphan_meta:
        errors.append(f"Orphan .txt.metadata.json files with no matching CSV row: {sorted(orphan_meta)}")

    metadata_key_counts = {}
    metadata_sizes = {}

    for call_id in sorted(csv_ids & txt_ids):
        content = txt_files[call_id].read_text(encoding="utf-8")
        if not content.strip():
            errors.append(f"{call_id}: document file is empty")
            continue
        row = csv_rows[call_id]
        transcript = row["transcript"].strip()
        notes = row["manager_notes"].strip()
        if transcript not in content:
            errors.append(f"{call_id}: document content does not contain the transcript verbatim "
                           f"(data/historical_sales_calls.csv must be treated as immutable)")
        if notes not in content:
            errors.append(f"{call_id}: document content does not contain manager_notes verbatim")
        check_retrieval_context(call_id, content, row, schema, errors)

    for call_id in sorted(csv_ids & meta_ids):
        row = csv_rows[call_id]
        attributes = check_metadata(call_id, meta_files[call_id], row, schema, errors, warnings)
        if attributes is not None:
            metadata_key_counts[call_id] = len(attributes)
            metadata_sizes[call_id] = meta_files[call_id].stat().st_size

    manifest_path = output_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("document_count") != len(csv_ids):
            errors.append(f"manifest.json document_count ({manifest.get('document_count')}) "
                           f"does not match the CSV row count ({len(csv_ids)})")
    else:
        warnings.append(f"{manifest_path} not found — run convert_csv_to_documents.py to regenerate it")

    check_deterministic_regeneration(csv_path, output_dir, schema_path, errors)

    print(f"Checked {len(csv_ids)} CSV rows against {len(txt_ids)} documents / {len(meta_ids)} metadata files")
    print(f"Errors: {len(errors)}, Warnings: {len(warnings)}\n")

    if metadata_key_counts:
        counts = set(metadata_key_counts.values())
        print(f"Metadata key count per document: {sorted(counts)} "
              f"({'consistent across all documents' if len(counts) == 1 else 'INCONSISTENT — see warnings'})")
        if len(counts) != 1:
            warnings.append(f"Metadata key counts are not consistent across documents: {metadata_key_counts}")
        largest_call_id = max(metadata_sizes, key=metadata_sizes.get)
        print(f"Maximum serialized metadata.json size: {metadata_sizes[largest_call_id]} bytes "
              f"(largest: {largest_call_id}.txt.metadata.json)")
        print("Bedrock compatibility note: no per-field or per-document metadata size/count limit has been "
              "verified against a live Bedrock Knowledge Base or a specific vector store backend (OpenSearch "
              "Serverless / Pinecone / Aurora / etc. all have different documented limits). The numbers above "
              "are the actual measured values for this corpus — fields are never trimmed based on an assumed "
              "limit; verify against the chosen backend's current documentation before provisioning.")
        allowlist = schema_loader.filter_allowlist(schema)
        print(f"Filter allowlist ({len(allowlist)} fields): {allowlist}")
    print()

    for w in warnings:
        print(f"  WARNING: {w}")
    for e in errors:
        print(f"  ERROR: {e}")

    if errors:
        print("\nNOT READY for S3 upload / Bedrock ingestion.")
        return 1
    print("\nREADY for S3 upload / Bedrock ingestion." if not warnings else
          "\nREADY WITH WARNINGS for S3 upload / Bedrock ingestion.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--schema-path", type=Path, default=schema_loader.DEFAULT_SCHEMA_PATH)
    args = parser.parse_args()
    sys.exit(validate(args.csv_path, args.output_dir, args.schema_path))


if __name__ == "__main__":
    main()
