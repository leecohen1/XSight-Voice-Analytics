# services

FastAPI microservices that make up the XSight AI backend. Each service is independently deployable, has its own `requirements.txt` and `.env.example`, and is designed to run in Docker locally first, then on AWS EC2.

## Services

- **rag_service** — Sales Call RAG Service. LangChain + ChromaDB + HuggingFace embeddings + Llama.cpp. Retrieves similar historical sales calls with grounded, cited insights.
- **call_signal_analyser** — Voice / Call Signal Analyser. PyTorch feature-based classifier operating on transcript-derived features only (no audio processing).
- **guardrails_service** — NeMo Guardrails input/output validation service.
- **langgraph_agent** — LangGraph Sales Agent (Planner → Tool Execution → Synthesizer) exposed via FastAPI, producing reasoning, coaching feedback, and recommended next actions.

**Status:** Skeletons introduced starting Phase 6; full logic implemented in Phases 11–14. See [CLAUDE.md](../CLAUDE.md) for endpoint contracts and [docs/PROGRESS.md](../docs/PROGRESS.md) for current status.
