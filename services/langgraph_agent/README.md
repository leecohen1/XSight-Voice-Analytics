# langgraph_agent

LangGraph Sales Agent.

**Status:** Not yet implemented. Planned for Phase 14.

**Stack:** FastAPI, LangGraph.

**Role:** the system's single AI orchestrator and final synthesis layer — called once per request by n8n. Not just a reasoning helper: this service decides which tools are needed, invokes the RAG Service and Call Signal Analyser itself (n8n never calls them directly), reconciles their evidence, and returns the complete final output JSON.

**Endpoint:** `POST /agent/run` — runs a Planner → Tool Execution → Synthesizer graph over the call transcript, metadata, and Gemini's structured extraction, using the RAG tool, Call Signal Analyser tool, and Follow-up recommendation tool, to detect conflicting/missing evidence and produce the complete analysis result: coaching feedback, recommended next action, follow-up email, and the rest of the final output schema, plus `reasoning_steps` and `tools_used` for transparency.

See [CLAUDE.md](../../CLAUDE.md#6-langgraph-sales-agent) for the full input/output contract.
