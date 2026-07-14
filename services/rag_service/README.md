# rag_service

Sales Call RAG Service.

**Status:** Not yet implemented. Planned for Phase 12.

**Stack:** FastAPI, LangChain, ChromaDB, HuggingFace embeddings (`sentence-transformers/all-MiniLM-L6-v2`), Llama.cpp.

**Called by:** the LangGraph agent only, as a tool. Not called directly by n8n.

**Endpoint:** `POST /query` — given a transcript and metadata, retrieves similar historical sales calls from ChromaDB and returns a grounded, cited insight.

**Rules:** Use only retrieved historical calls. Never invent CRM facts, budgets, prices, customer names, or outcomes. Every claim about a historical call must cite its `call_id`. If evidence is missing, return "Not enough evidence".

See [CLAUDE.md](../../CLAUDE.md) for the full input/output contract.
