# Bedrock Knowledge Base Document Schema

Human-readable explanation of the format `convert_csv_to_documents.py`
produces from `data/historical_sales_calls.csv`, and why it's structured
this way. **`metadata_schema.json` is the machine-readable source of truth**
this document describes — both `convert_csv_to_documents.py` and
`validate_documents.py` load it directly (via `schema_loader.py`) instead of
hardcoding field lists, so this prose and the actual behavior cannot drift
apart from each other by definition; they can still drift from this
document, so treat `metadata_schema.json` as authoritative if the two ever
disagree.

## Canonical source of truth

```
data/historical_sales_calls.csv  (canonical, immutable, edited by hand)
        ↓  convert_csv_to_documents.py
documents/<call_id>.txt + <call_id>.txt.metadata.json  (generated artifacts)
```

The CSV is the only file a human ever edits. The generated `.txt` /
`.txt.metadata.json` pair is regenerated from it — never edited directly.
To change a historical call, edit the CSV row, then re-run the converter and
validator (see `README.md`).

## One document per historical call

Each of the 24 rows becomes exactly one document pair in `documents/`:

```
documents/
├── CALL_001.txt
├── CALL_001.txt.metadata.json
├── ...
├── CALL_024.txt
└── CALL_024.txt.metadata.json
```

This is Amazon Bedrock Knowledge Base's standard S3 ingestion pattern: for
every source object `<key>`, an optional sidecar object named
`<key>.metadata.json` in the same location supplies filterable metadata for
that object. One call → one text object → one metadata sidecar keeps a 1:1
mapping between a Bedrock retrieval hit and a `call_id` (see "Chunking
strategy" below).

## `<call_id>.txt` — document content

```
Call ID: CALL_003

Retrieval Context:
- Customer Segment: SMB
- Industry: Retail
- Main Objection: authority
- Customer Intent: medium
- Customer Sentiment: neutral

Transcript:
Agent: Hi Yossi, thanks for hopping on. ...
Customer: Pretty ad hoc, honestly. ...
...

Manager Review — Secondary Evidence:
Strong discovery and a tailored one-page proposal built specifically for the
actual decision-maker, but the contact on the call — Dana, the owner — was
not present...
```

Four parts, in order (see `metadata_schema.json`'s `txt_structure`):

1. **`Call ID: <call_id>`**
2. **`Retrieval Context:`** — exactly 5 semantic fields, no more:
   `customer_segment`, `industry`, `main_objection`, `customer_intent`,
   `customer_sentiment`. Values are copied **verbatim** from the CSV (e.g.
   `authority`, not `Authority`) — only the field labels are formatted for
   readability. Scores, voice metrics, booleans, and outcome values (e.g.
   `sale_result`, `agent_performance_score`, `follow_up_needed`) are
   deliberately excluded from this section; they live in the metadata
   sidecar instead (see below). This section exists purely to strengthen
   semantic retrieval — a query like "SMB retail customer with an authority
   objection" matches this block even if those exact words don't appear
   organically in the dialogue.
3. **`Transcript:`** followed by the `transcript` column, copied verbatim —
   never edited, reformatted, or summarized. `validate_documents.py` checks
   this by confirming the CSV's transcript text is a substring of the
   generated document.
4. **`Manager Review — Secondary Evidence:`** followed by `manager_notes`,
   verbatim. Per the Ground Truth Rules, `manager_notes` only
   restates/interprets the call and never introduces new business facts, so
   including it as retrievable content doesn't create a grounding risk.

## `<call_id>.txt.metadata.json` — Bedrock S3 metadata sidecar

```json
{
  "metadataAttributes": {
    "call_id": "CALL_003",
    "agent_name": "Sarah Levi",
    "customer_segment": "SMB",
    "industry": "Retail",
    "main_objection": "authority",
    "customer_intent": "medium",
    "customer_sentiment": "neutral",
    "sale_result": "No Sale",
    "call_category": "Follow-up Needed",
    "closing_attempt": "strong",
    "follow_up_needed": true,
    "next_meeting_scheduled": true,
    "decision_maker_present": false,
    "call_duration_seconds": 240,
    "agent_performance_score": 5,
    "objection_handling_quality": 4,
    "lead_quality_score": 3,
    "silence_ratio": 0.13,
    "speaking_rate_wpm": 119.0,
    "speech_to_non_speech_ratio": 0.87,
    "agent_talk_ratio": 0.68,
    "average_energy_level": "medium",
    "price_mentions_count": 2,
    "competitor_mentions_count": 0,
    "source_type": "historical_sales_call",
    "dataset_version": 1,
    "schema_version": 1
  }
}
```

A flat `metadataAttributes` map — 27 keys per document, always the same set
and order (`validate_documents.py` checks both). Native JSON types
throughout: strings as strings, scores/ratios/counts as numbers, flags as
booleans — never everything coerced to a string. **`transcript` and
`manager_notes` are never included here** — they're free text, not filter
values, and live in the `.txt` body only; `validate_documents.py` asserts
their absence explicitly.

This uses the flat `metadataAttributes: {field: value}` form rather than the
more verbose typed form some Bedrock documentation also shows
(`{"value": {"type": "STRING", "stringValue": "..."}}` with an optional
`includeForEmbedding` flag). **No `includeForEmbedding` or other
typed-form-only property is set anywhere in this pipeline** — that property
doesn't apply to the flat form being used here, and inventing a property
without confirming it's supported by the exact sidecar format in use would
risk silently-ignored or rejected metadata at ingestion time. Verify the
flat form is still Bedrock's current documented default before provisioning
a real Knowledge Base — AWS APIs evolve and this hasn't been checked against
live Bedrock docs.

### Metadata classification

Every metadata field belongs to exactly one category (see
`metadata_schema.json`'s `"category"` per field):

| Category | Fields | Purpose |
|---|---|---|
| **Identity** | `call_id`, `agent_name` | Citation, traceability, result display, debugging, deduplication. Not part of the default filter allowlist. |
| **Semantic context** | `customer_segment`, `industry`, `main_objection`, `customer_intent`, `customer_sentiment` | Also shown once in the TXT `Retrieval Context` section (for embedding). In metadata, the *same* fields additionally support exact-match filtering — this is a separate mechanism from embedding, not a duplication of semantic influence. |
| **Outcome & strategy** | `sale_result`, `call_category`, `closing_attempt`, `follow_up_needed`, `next_meeting_scheduled`, `decision_maker_present` | Structured metadata only (never in the TXT body). Candidates for the future deterministic filter builder. |
| **Analytical evidence** | `call_duration_seconds`, `agent_performance_score`, `objection_handling_quality`, `lead_quality_score`, `silence_ratio`, `speaking_rate_wpm`, `speech_to_non_speech_ratio`, `agent_talk_ratio`, `average_energy_level`, `price_mentions_count`, `competitor_mentions_count` | Returned as evidence for LangGraph's reasoning. **Not** used as default retrieval filters against the current 24-call corpus. |
| **System (generated)** | `source_type`, `dataset_version`, `schema_version` | Not derived from any CSV column — constants stamped by the converter from `metadata_schema.json` itself, so they can never drift from the schema that generated them. Not added to the canonical CSV. |

The full per-field detail — source column, required/optional, type,
destination (`txt` / `metadata` / `both`), category, `allowed_for_filtering`,
and validation rule — lives in `metadata_schema.json`, not duplicated here.

## Small-corpus filter policy

See `README.md`'s "Small-Corpus Filter Policy" section for the retrieval-time
policy (not implemented yet — filter *building* is out of scope for this
ingestion phase). The `allowed_for_filtering` flag on each field in
`metadata_schema.json` is the input allowlist that policy will draw from.

## Chunking strategy

**Recommendation: `NONE` (whole document = one chunk), not fixed-size
chunking.** Reasoning:

- Current transcripts run 363–670 words (~2,000–4,000 characters, roughly
  500–900 tokens) — comfortably within a single embedding call for any
  Bedrock-supported embedding model (Titan Embeddings supports up to 8,192
  tokens), even with the added header/footer sections.
- The project's `similar_calls[]` output contract (see `CLAUDE.md` Component
  3) treats each retrieval result as **one call** with **one**
  `similarity_score`. Whole-document chunking keeps that 1:1 mapping exact —
  no chunk-to-call score aggregation logic is needed.
- If future transcripts grow substantially longer, revisit this with
  fixed-size chunking (~300–512 tokens, 10–20% overlap) and add
  chunk-to-call aggregation (e.g. max score per `call_id`) in the FastAPI
  wrapper — not needed for the current 24-call corpus.
