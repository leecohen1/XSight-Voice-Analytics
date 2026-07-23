#!/usr/bin/env python3
"""Convert data/historical_sales_calls.csv into per-call documents ready for
Amazon Bedrock Knowledge Base ingestion via S3.

data/historical_sales_calls.csv is the only canonical source of truth. This
script never rewrites it, and every transcript / manager_notes value is
copied into its document byte-for-byte (see validate_documents.py's
verbatim-content checks). The generated documents/*.txt and
*.txt.metadata.json files are deployment artifacts, not a second source of
truth — never edit them by hand; change the CSV and re-run this script.

Field lists, types, TXT placement, metadata categories, and validation rules
all come from metadata_schema.json (via schema_loader.py) — nothing about a
specific CSV column is hardcoded here, so this script and validate_documents.py
cannot define a field two different ways.

For each CSV row this produces two files under <output-dir>/documents/:
    <call_id>.txt               - the retrievable content (see document_schema.md)
    <call_id>.txt.metadata.json - the Bedrock KB S3 metadata sidecar (filterable fields)

and one manifest.json summarizing the run.

Usage:
    python services/rag_service/ingestion/convert_csv_to_documents.py
    python services/rag_service/ingestion/convert_csv_to_documents.py --output-dir /tmp/bedrock_docs

Exit code 0 on success, 1 if the CSV is missing or a row fails to convert.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import schema_loader

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV_PATH = ROOT / "data" / "historical_sales_calls.csv"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def build_content(row: dict[str, str], schema: dict) -> str:
    """Build the TXT document body strictly from metadata_schema.json's
    txt_structure: Call ID line, Retrieval Context (5 semantic fields only —
    no scores, voice metrics, booleans, or outcome values), the verbatim
    transcript, then the verbatim manager notes under 'Manager Review —
    Secondary Evidence'."""
    call_id_label = schema_loader.section_label(schema, "call_id_line")
    context_label = schema_loader.section_label(schema, "retrieval_context")
    transcript_label = schema_loader.section_label(schema, "transcript")
    manager_label = schema_loader.section_label(schema, "manager_review")

    context_fields = schema_loader.retrieval_context_fields(schema)
    context_field_labels = schema_loader.retrieval_context_field_labels(schema)
    context_lines = "\n".join(f"- {context_field_labels[f]}: {row[f]}" for f in context_fields)

    transcript = row["transcript"].strip()
    notes = row["manager_notes"].strip()

    return (
        f"{call_id_label}: {row['call_id']}\n\n"
        f"{context_label}:\n{context_lines}\n\n"
        f"{transcript_label}:\n{transcript}\n\n"
        f"{manager_label}:\n{notes}\n"
    )


def build_metadata(row: dict[str, str], schema: dict) -> dict:
    attributes = {}
    metadata_fields = schema_loader.fields_with_destination(schema, "metadata")
    for field in metadata_fields:
        spec = schema["fields"][field]
        attributes[field] = schema_loader.cast_value(field, spec, row[field])
    attributes.update(schema_loader.generated_metadata_values(schema))
    return {"metadataAttributes": attributes}


def convert(csv_path: Path, output_dir: Path, schema_path: Path) -> int:
    schema = schema_loader.load_schema(schema_path)
    required_columns = schema_loader.csv_field_names(schema)

    if not csv_path.exists():
        print(f"ERROR: CSV not found at {csv_path}", file=sys.stderr)
        return 1

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in required_columns if c not in (reader.fieldnames or [])]
        if missing:
            print(f"ERROR: CSV is missing required columns: {missing}", file=sys.stderr)
            return 1
        rows = list(reader)

    documents_dir = output_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries: list[dict] = []
    seen_ids: set[str] = set()
    errors: list[str] = []

    for i, row in enumerate(rows, start=2):  # header is line 1
        call_id = row["call_id"].strip()
        if not call_id:
            errors.append(f"row {i}: empty call_id")
            continue
        if call_id in seen_ids:
            errors.append(f"row {i}: duplicate call_id {call_id}")
            continue
        seen_ids.add(call_id)

        for field in required_columns:
            spec = schema["fields"][field]
            try:
                value = schema_loader.cast_value(field, spec, row[field])
            except ValueError as e:
                errors.append(f"{call_id}: {e}")
                continue
            schema_loader.validate_value(field, spec, value, errors, call_id)

    if errors:
        print(f"ERROR: {len(errors)} validation issue(s) found — aborting before writing any documents:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    for row in rows:
        call_id = row["call_id"].strip()
        content = build_content(row, schema)
        metadata = build_metadata(row, schema)

        doc_path = documents_dir / f"{call_id}.txt"
        meta_path = documents_dir / f"{call_id}.txt.metadata.json"
        doc_path.write_text(content, encoding="utf-8")
        meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        manifest_entries.append({
            "call_id": call_id,
            "document_file": doc_path.name,
            "metadata_file": meta_path.name,
            "content_chars": len(content),
            "metadata_key_count": len(metadata["metadataAttributes"]),
            "metadata_bytes": meta_path.stat().st_size,
            "sale_result": row["sale_result"],
            "main_objection": row["main_objection"],
        })

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_csv": str(csv_path.relative_to(ROOT)) if csv_path.is_relative_to(ROOT) else str(csv_path),
        "schema_version": schema["schema_version"],
        "dataset_version": schema["dataset_version"],
        "document_count": len(manifest_entries),
        "documents": manifest_entries,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"Converted {len(manifest_entries)} calls from {csv_path} into {documents_dir}")
    print(f"Manifest written to {output_dir / 'manifest.json'}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV_PATH,
                         help=f"Path to historical_sales_calls.csv (default: {DEFAULT_CSV_PATH})")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                         help=f"Directory to write documents/ and manifest.json into (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--schema-path", type=Path, default=schema_loader.DEFAULT_SCHEMA_PATH,
                         help=f"Path to metadata_schema.json (default: {schema_loader.DEFAULT_SCHEMA_PATH})")
    args = parser.parse_args()
    sys.exit(convert(args.csv_path, args.output_dir, args.schema_path))


if __name__ == "__main__":
    main()
