# data

Historical sales calls datasets for XSight — two separate files, not one.

**Status:**
- `historical_sales_calls.csv` — **Implemented (Phase 5B.1 / 5C, validated and frozen).** 24 rows, 26 columns, matching the schema in [docs/dataset_design.md](../docs/dataset_design.md) §14 exactly.
- `call_signal_training.csv` — Not yet implemented. Planned for a later Phase 5B sub-step (PyTorch classifier training data).

**Files:**
- `historical_sales_calls.csv` — the RAG corpus: 24 detailed, hand-authored records with full transcripts, for RAG retrieval quality (ChromaDB ingestion in a later phase). Sourced from `docs/generated_calls_batch_01.md` through `_05.md` (Phase 5B.1) and validated by `scripts/validate_historical_dataset.py` (Phase 5C) — see [docs/dataset_validation_report.md](../docs/dataset_validation_report.md) for the full validation results (status: READY WITH WARNINGS).
- `call_signal_training.csv` — the classifier training dataset: ~150–300 synthetic/adapted rows with features and labels only (no full transcript), for PyTorch classifier training. Not yet generated.

All content in English. The two files share a compatible column schema (the training file omits `transcript`) so feature-engineering logic can be reused, but they serve different purposes and are not interchangeable — see `docs/dataset_design.md` §2.

## Validating `historical_sales_calls.csv`

Re-run the validator any time the CSV changes:

```
python scripts/validate_historical_dataset.py
```

This checks schema, enums, numeric ranges, corpus-wide distributions (outcome/agent/objection balance, all 8 required contrast cases), Ground Truth consistency heuristics, audio-feature internal consistency, mention-count recomputation, and transcript-style patterns, then regenerates `docs/dataset_validation_report.md`. Exit code 0 for `READY`/`READY WITH WARNINGS`, non-zero for `NOT READY`. The script only auto-corrects objective formatting issues (stray whitespace, boolean casing) — it never rewrites transcripts, mention counts, or subjective labels; those are reported for human review instead.

See [CLAUDE.md](../CLAUDE.md) for the full column schema and content requirements, and [docs/dataset_design.md](../docs/dataset_design.md) for the complete data design.

**Note:** Real audio files, ChromaDB data, and any dataset containing real customer information must never be committed to this repository (see [.gitignore](../.gitignore)). Every row in `historical_sales_calls.csv` is fictional, per the project's fictional B2B SaaS product context.
