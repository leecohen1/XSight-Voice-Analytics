# data

Historical sales calls dataset for XSight.

**Status:** Not yet implemented. Planned for Phase 5.

**Planned file:** `historical_sales_calls.csv`

All content in English. The dataset supports both RAG retrieval (ChromaDB) and PyTorch classifier training.

**Structure:**
- 20–30 detailed records with full transcripts, for RAG retrieval quality
- An additional 150–300 synthetic rows with features and labels only (no full transcript), for PyTorch classifier training

See [CLAUDE.md](../CLAUDE.md) for the full column schema and content requirements.

**Note:** Real audio files, ChromaDB data, and any dataset containing real customer information must never be committed to this repository (see [.gitignore](../.gitignore)).
