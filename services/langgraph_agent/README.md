# langgraph_agent

LangGraph Sales Agent.

**Status:** Not yet implemented. Planned for Phase 14.

**Stack:** FastAPI, LangGraph.

**Endpoint:** `POST /agent/run` — runs a Planner → Tool Execution → Synthesizer graph over the call transcript, metadata, and prior analysis, using the RAG tool, Call Signal Analyser tool, and Follow-up recommendation tool, to produce a synthesized answer, reasoning steps, coaching feedback, and a recommended next action.

See [CLAUDE.md](../../CLAUDE.md) for the full input/output contract.
