# langgraph_agent

LangGraph Sales Agent.

**Status:** demo-day cross-phase build (approved override — see project root for context). A real `langgraph.graph.StateGraph` is installed, built, compiled, and invoked per-request in `app/graph.py` — API contract, validation, error handling, and graph execution are all real. Per-node reasoning is still deterministic/rule-based (no LLM call anywhere yet); see **Limitations** below for exactly what that does and doesn't mean.

**Stack:** FastAPI, Pydantic, LangGraph (`langgraph==1.2.9`). No model downloads, no API keys — nothing in this service calls out to an LLM or any other network service.

**Role:** a multi-step reasoning layer — called by n8n after the RAG Service and Call Signal Analyser have both already returned. This service does not call those services itself; n8n fetches their results first and passes them in. It reasons over the transcript, structured extraction, RAG results, and Call Signal Analyser results, but does **not** produce the complete final report — that's the Gemini Final Analysis LLM Chain's job (a separate n8n node), using this service's reasoning output as one of its inputs.

## Endpoints

- `GET /health` → `{"status": "ok", "service": "langgraph_agent", "version": "0.1.0"}`
- `POST /agent/run` → invokes the compiled StateGraph and returns its reasoning output (see below).

### `POST /agent/run` request

```json
{
  "question": "Why did this call fail and what should the agent improve?",
  "transcript": "Agent: ... Customer: ...",
  "metadata": {},
  "structured_extraction": {"closing_attempt": "weak", "main_objection": "price"},
  "rag_results": {"similar_calls": [{"call_id": "CALL_007"}], "insight": "...", "citations": ["CALL_007"]},
  "signal_analysis": {"predicted_outcome": "Follow-up Needed", "confidence": 0.72, "risk_level": "Medium"}
}
```

`question` (min 5 chars) and `transcript` (min 20 chars) are required; `metadata`, `structured_extraction`, `rag_results`, and `signal_analysis` are all optional and default to empty.

### `POST /agent/run` response

```json
{
  "answer": "Reasoning answer based on the supplied evidence citing CALL_007. Reasoning is deterministic/rule-based — no LLM call is made yet (Phase 14 LLM backend decision pending).",
  "reasoning_steps": [
    "Reviewed structured extraction",
    "Reviewed historical evidence",
    "Reviewed call signal output",
    "Synthesized coaching recommendation"
  ],
  "evidence_conflicts": [],
  "coaching_points": ["Strengthen the closing ask — propose a concrete next step with a date."],
  "recommended_next_action": "Schedule a follow-up with the decision-maker.",
  "evidence_used": ["structured_extraction", "rag_service", "call_signal_analyser"],
  "mock": true,
  "graph_trace": ["Planner", "Evidence Reconciliation", "Synthesizer"]
}
```

All fields above except `graph_trace` were already part of the documented contract (`docs/api_contracts.md` §4) and keep their exact existing meaning and type. `graph_trace` is new and additive (defaults to `[]` if ever absent) — it lists the LangGraph node names that actually ran, in order, so it can be used as evidence that a real graph executed rather than just trusted from a design doc. `mock` is unchanged and still `true`, but see **Limitations** for what it actually asserts now.

## Internal graph (`app/graph.py`)

```
START → Planner → Evidence Reconciliation → Synthesizer → END
```

This is a real, compiled `langgraph.graph.StateGraph` (built once at import time as `COMPILED_GRAPH`, invoked fresh per request in `run_graph()`) — not a plain function chain renamed to look like one. State flows through a `GraphState` `TypedDict` (defined in `app/graph.py`) seeded from the request, then extended by each node's return value as LangGraph merges it into the shared state.

- **Planner Node:** determines which evidence and questions must be evaluated (which of `structured_extraction`/`rag_results`/`signal_analysis` were actually provided).
- **Evidence Reconciliation Node:** compares the available evidence and detects conflicts. Two documented, deterministic rules: (1) `signal_analysis.confidence < 0.65` is flagged as unreliable evidence; (2) `signal_analysis.predicted_outcome == "Sale"` together with `signal_analysis.risk_level == "High"` is flagged as an internal conflict worth human attention.
- **Synthesizer Node:** produces `reasoning_steps` (one line per evidence source actually reviewed, plus a final synthesis step), `coaching_points` (a weak/none `closing_attempt` triggers a specific closing-technique coaching point; otherwise a default), and `recommended_next_action` (branches on `signal_analysis.predicted_outcome`).

**Architecture note (unchanged from the original design):** the generic "Tool Execution" step is adapted into "Evidence Reconciliation" because n8n performs the external HTTP tool calls (RAG Service, Call Signal Analyser) before this service is invoked — this service reasons over evidence it receives, it never fetches it. This service makes **no outbound HTTP calls of its own** — not to RAG, Signal Analyser, Gemini, or anywhere else.

## Limitations

Read this section before assuming more sophistication than exists today:

- **No LLM backend.** Every node (`planner_node`, `evidence_reconciliation_node`, `synthesizer_node` in `app/graph.py`) is deterministic, rule-based Python — no prompt is sent to any model. The Planner/Synthesizer LLM backend decision from the original Phase 14 plan is still open. `mock: true` in the response reflects exactly this: "no LLM call was made, reasoning is rule-based" — that meaning has **not** changed even though the graph itself is now real and executing (see `graph_trace` in the response for proof it ran).
- **No persistence or checkpointing between requests.** The graph is compiled once (`graph.compile()`, no checkpointer configured) and reused across requests, but each `invoke()` call starts from a fresh state built only from that request's payload. There is no memory of prior calls, no thread/session concept, and no LangGraph checkpoint store (SQLite/Postgres/etc.) wired in.
- **Single-turn only.** One `/agent/run` request is one complete graph run, start to finish, synchronously, in-process. There's no interrupt/resume, human-in-the-loop pause, or multi-turn conversation support in the graph itself (that kind of flow, if ever needed, lives in n8n's orchestration, not here).
- **Fixed, non-branching graph topology.** All three nodes always run in the same order for every request, regardless of which evidence is present — the Planner's output changes *what each downstream node does*, not *which nodes run*. There's no conditional routing/branching edge in this graph today.
- **This service still does not produce the complete final report.** It returns reasoning output only (`answer`, `reasoning_steps`, `evidence_conflicts`, `coaching_points`, `recommended_next_action`, `evidence_used`) — the Gemini Final Analysis LLM Chain (a separate n8n node) is still responsible for assembling the full final output JSON schema.

## Error handling

Same shared shape as the other services:

```json
{"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": [...]}}
```

## Running locally

```bash
cd services/langgraph_agent
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004
```

```bash
curl http://localhost:8004/health

curl -X POST http://localhost:8004/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why did this call fail and what should the agent improve?",
    "transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing.",
    "structured_extraction": {"closing_attempt": "weak", "main_objection": "price"},
    "rag_results": {"similar_calls": [{"call_id": "CALL_007"}], "insight": "Similar price objection.", "citations": ["CALL_007"]},
    "signal_analysis": {"predicted_outcome": "Follow-up Needed", "confidence": 0.72, "risk_level": "Medium"}
  }'
```

## Testing

```bash
cd services/langgraph_agent
pytest -v
```

## Docker

```bash
docker build -t xsight-langgraph-agent services/langgraph_agent
docker run -p 8004:8004 xsight-langgraph-agent
```

Or via the root `docker-compose.yml` (`docker compose up langgraph_agent`).

See [CLAUDE.md](../../CLAUDE.md#6-langgraph-sales-agent) and [docs/api_contracts.md](../../docs/api_contracts.md) for the full contract.
