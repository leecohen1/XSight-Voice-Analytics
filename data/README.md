# data

Historical sales calls datasets for XSight — two separate files, not one.

**Status:** Not yet implemented. Planned for Phase 5.

**Planned files:**
- `historical_sales_calls.csv` — the RAG corpus: 20–30 detailed records with full transcripts, for RAG retrieval quality (ChromaDB ingestion).
- `call_signal_training.csv` — the classifier training dataset: ~150–300 synthetic/adapted rows with features and labels only (no full transcript), for PyTorch classifier training.

All content in English. The two files share a compatible column schema (the training file omits `transcript`) so feature-engineering logic can be reused, but they serve different purposes and are not interchangeable.

See [CLAUDE.md](../CLAUDE.md) for the full column schema and content requirements.

**Note:** Real audio files, ChromaDB data, and any dataset containing real customer information must never be committed to this repository (see [.gitignore](../.gitignore)).
