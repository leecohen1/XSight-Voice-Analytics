# Bedrock Knowledge Base Ingestion Pipeline

Converts `data/historical_sales_calls.csv` (the project's immutable RAG
corpus — see `CLAUDE.md`) into per-call documents ready to upload to S3 and
ingest into an Amazon Bedrock Knowledge Base. This is data-preparation
tooling only — it does not provision AWS resources and does not implement
the FastAPI `/query` service itself (that's the rest of Phase 12; see
`CLAUDE.md` Component 3).

## Canonical source vs. generated artifacts

```text
data/historical_sales_calls.csv        ← canonical source of truth, edited by hand
        ↓
convert_csv_to_documents.py             (reads metadata_schema.json for field rules)
        ↓
documents/<call_id>.txt                ← generated artifact
documents/<call_id>.txt.metadata.json  ← generated artifact
```

- **`data/historical_sales_calls.csv` is the only canonical source of
  truth.** It is never modified by anything in this pipeline.
- **The generated `.txt` and `.txt.metadata.json` files are deployment
  artifacts, not a second source of truth.** Never edit them by hand — any
  manual edit is silently overwritten the next time the converter runs, and
  `validate_documents.py`'s deterministic-regeneration check would flag a
  hand-edited file as inconsistent with what the CSV actually produces.
- **To add or update a historical call:** edit `data/historical_sales_calls.csv`
  directly (add a row, or change an existing row's values — never the
  generated files), then re-run both scripts (below). Never do direct CSV
  ingestion into Bedrock — always go through the converter, so every
  document and its metadata sidecar are generated the same way.

## Folder layout

```text
services/rag_service/ingestion/
├── metadata_schema.json          # shared policy source: field types, TXT/metadata
│                                  # placement, categories, filter eligibility, rules
├── schema_loader.py               # loads metadata_schema.json for both scripts below
├── convert_csv_to_documents.py    # CSV -> documents/*.txt + *.txt.metadata.json
├── validate_documents.py          # independent post-conversion validation
├── document_schema.md             # human-readable document/metadata format + rationale
├── README.md                      # this file
└── output/                        # generated, gitignored — not committed
    ├── manifest.json
    └── documents/
        ├── CALL_001.txt
        ├── CALL_001.txt.metadata.json
        ├── ...
        ├── CALL_024.txt
        └── CALL_024.txt.metadata.json
```

`output/` is regenerated from the CSV on demand and gitignored — it's
derived data, not a second source of truth.

## Running the pipeline

```bash
# 1. Convert the CSV into per-call documents
python services/rag_service/ingestion/convert_csv_to_documents.py

# 2. Validate the output before uploading anything
python services/rag_service/ingestion/validate_documents.py
```

Both scripts are pure-stdlib (csv, json, argparse, pathlib, tempfile) — no
`requirements.txt` needed, no network access, nothing installed. Both accept
`--csv-path` / `--output-dir` / `--schema-path` overrides.

Expected result today: **24 documents converted, 0 errors, 0 warnings.**

`validate_documents.py` also re-runs the converter into a temporary
directory and diffs it byte-for-byte against `output/documents/` — if the
committed output isn't exactly what the current CSV + schema would produce
right now (e.g. someone hand-edited a generated file, or forgot to
regenerate after a CSV change), this fails with an explicit error rather
than silently ingesting stale documents.

## Uploading to S3

```bash
aws s3 sync services/rag_service/ingestion/output/documents/ \
  s3://<your-bedrock-kb-bucket>/historical-sales-calls/ \
  --exclude "*" --include "*.txt" --include "*.txt.metadata.json"
```

Each `.txt` object and its `.txt.metadata.json` sidecar must land in the
same S3 prefix with matching keys — that's how Bedrock associates metadata
with its source document.

## Ingesting into the Knowledge Base

Assumes a Bedrock Knowledge Base already exists (provisioning it is out of
scope for this data-prep task) pointed at that S3 prefix as its data source.
After uploading:

1. Trigger a data-source sync (console, or `bedrock-agent` `StartIngestionJob`)
   so Bedrock re-scans S3 and re-embeds new/changed/removed documents.
2. Confirm the document count in the console matches `manifest.json`'s
   `document_count` (24).

## What's above the transcript, and why

The `.txt` document's `Retrieval Context` section — shown before the
transcript — contains exactly 5 fields: `customer_segment`, `industry`,
`main_objection`, `customer_intent`, `customer_sentiment`. These are the
fields judged most useful as *semantic* context for retrieval (the kind of
thing a query like "enterprise customer with a trust objection" should
match against). Scores, voice/audio metrics, booleans, and outcome values
are deliberately excluded from this section — see `document_schema.md` for
the full reasoning and the exact document layout.

## Metadata: what's for filtering, what's evidence-only

See `document_schema.md`'s "Metadata classification" table for the full
per-category breakdown. Summary:

- **Filterable today** (`allowed_for_filtering: true` in `metadata_schema.json`):
  the 5 semantic-context fields (also above) plus the 6 outcome/strategy
  fields — `sale_result`, `call_category`, `closing_attempt`,
  `follow_up_needed`, `next_meeting_scheduled`, `decision_maker_present`.
- **Evidence-only, not a default filter**: the 11 analytical-evidence fields
  (`call_duration_seconds`, `agent_performance_score`,
  `objection_handling_quality`, `lead_quality_score`, `silence_ratio`,
  `speaking_rate_wpm`, `speech_to_non_speech_ratio`, `agent_talk_ratio`,
  `average_energy_level`, `price_mentions_count`,
  `competitor_mentions_count`). These are returned in every retrieval hit's
  metadata so LangGraph's evidence reconciliation can use them, but the
  filter builder should not apply them as default filters against the
  current 24-call corpus.
- **Identity fields** (`call_id`, `agent_name`) and the **generated system
  fields** (`source_type`, `dataset_version`, `schema_version`) are not in
  the default filter allowlist either — identity fields serve citation and
  dedup, not filtering; the system fields exist for provenance and schema
  bookkeeping, not semantic filtering.

The full allowlist is the field-level `allowed_for_filtering: true` flags in
`metadata_schema.json` — that file is authoritative if this summary and it
ever disagree.

## Small-corpus filter policy

The current corpus has 24 calls. A future deterministic filter builder
(**not implemented in this task** — filter construction is separate,
later work) should follow:

- **No hard filter by default.** Start with an unfiltered semantic query.
- **At most one high-confidence filter** at a time (e.g. `main_objection`
  matching the current call) — never combine multiple restrictive filters,
  which can easily return zero results from a 24-document corpus.
- **Retry without filters** if a filtered query returns too few results.
- **Allow both successful and unsuccessful contrast cases** through —
  don't filter out calls with a different outcome than the current one;
  contrast (a similar situation that went differently) has real coaching
  value, not just confirming matches.
- **Merge and deduplicate results by `call_id`** if multiple retrieval
  passes (e.g. filtered + unfiltered) are combined.
- **Filters must be built deterministically from the `allowed_for_filtering`
  allowlist above — never let an LLM generate arbitrary Bedrock filter
  JSON.** This keeps every filter traceable to a known, validated field
  rather than free-form model output that could reference a nonexistent
  field or an unsupported filter operator.

## Retrieval strategy

- **Chunking:** `NONE` — one chunk per document. See `document_schema.md`.
- **Overlap:** not applicable — no chunking means no chunk boundaries.
- **Number of retrieved documents:** top-`k` = 5 by default (`Retrieve`'s
  `numberOfResults`), configurable per-request if needed later.
- **Ranking:** prefer Bedrock's `HYBRID` search (semantic + keyword) over
  `SEMANTIC`-only, if the deployed vector store configuration supports it —
  sales-call transcripts are keyword-sensitive (exact terms like "price,"
  "competitor," product/company names) in a way pure semantic search can
  under-weight. Fall back to `SEMANTIC` if hybrid isn't available.
- **Post-retrieval:** the FastAPI wrapper (Phase 12) should apply a
  similarity-score floor before building `similar_calls[]`, and return
  `"insight": "Not enough evidence"` with empty `citations` when nothing
  clears it — the RAG Service's Ground Truth Rule obligation (`CLAUDE.md`),
  not something Bedrock enforces on its own.

## Integration with the rest of the pipeline

This pipeline only prepares data — it does not change where the RAG Service
sits in the overall flow (`CLAUDE.md`'s "Architecture flow" applies
unchanged):

```text
AssemblyAI (transcription)
  → Gemini Information Extractor (structured extraction)
    → n8n AI Agent Node (payload prep)
      → Sales Call RAG Service  ──┐
        POST /query                │  same request/response
        internally: boto3          │  contract as before —
        bedrock-agent-runtime      │  only the internals
        .retrieve(...)             │  changed
      → Voice / Call Signal Analyser ──┘  (parallel, unrelated)
        → Merge Results
          → LangGraph Agent (reasoning over merged RAG + signal results)
            → Gemini Final Analysis LLM Chain (assembles final output JSON)
```

## Validation summary (last run)

```
Checked 24 CSV rows against 24 documents / 24 metadata files
Errors: 0, Warnings: 0

Metadata key count per document: [27] (consistent across all documents)
Maximum serialized metadata.json size: 985 bytes (largest: CALL_017.txt.metadata.json)

READY for S3 upload / Bedrock ingestion.
```

No Bedrock vector-store size/count limit has been verified against a live
deployment — see `validate_documents.py`'s printed compatibility note. The
numbers above are real measurements, not assumptions; nothing is trimmed
preemptively.
