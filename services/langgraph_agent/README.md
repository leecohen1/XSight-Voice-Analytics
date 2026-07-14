# langgraph_agent

LangGraph Sales Agent.

**Status:** Not yet implemented. Planned for Phase 14.

**Stack:** FastAPI, LangGraph.

**Role:** a multi-step reasoning layer — called by n8n after the RAG Service and Call Signal Analyser have both already returned. This service does not call those services itself; n8n fetches their results first and passes them in. It reasons over the transcript, Gemini's extraction, the RAG results, and the Call Signal Analyser's results, but does **not** produce the complete final report — that's the Gemini Final Analysis LLM Chain's job (a separate n8n node), using this service's reasoning output as one of its inputs.

**Endpoint:** `POST /agent/run` — runs a Planner Node → Evidence Reconciliation Node → Synthesizer Node graph over the call transcript, metadata, Gemini's structured extraction, the RAG Service's results, and the Call Signal Analyser's results (received as input, not fetched live), to detect conflicting/missing evidence and produce a reasoning output: `answer`, `evidence_used`, `reasoning_steps`, `evidence_conflicts`, `recommended_next_action`, and `coaching_points`.

- **Planner Node:** determines which evidence and questions must be evaluated.
- **Evidence Reconciliation Node:** compares the transcript, Gemini's extraction, the AI Agent Node's enrichment, the RAG results, and the Call Signal Analyser results; detects conflicts, missing evidence, and inconsistencies.
- **Synthesizer Node:** produces `reasoning_steps`, `evidence_conflicts`, `coaching_points`, and `recommended_next_action`.

**Architecture note:** in this implementation, the generic Tool Execution step is adapted into an Evidence Reconciliation step because n8n performs the external HTTP tool calls before LangGraph is invoked.

See [CLAUDE.md](../../CLAUDE.md#6-langgraph-sales-agent) for the full input/output contract.
