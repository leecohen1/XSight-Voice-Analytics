# langgraph_agent

LangGraph Sales Agent.

**Status:** Phase 6 mock skeleton — API contract, validation, and error handling are real; reasoning is a deterministic mock structured as the three planned nodes (see below), implemented as plain Python functions. No LangGraph graph is installed or executed yet — full implementation (including the LLM backend for the Planner/Synthesizer nodes, TBD) is Phase 14.

**Stack (planned, Phase 14):** FastAPI, LangGraph. **Stack (this phase):** FastAPI + Pydantic only — no model downloads, no API keys.

**Role:** a multi-step reasoning layer — called by n8n after the RAG Service and Call Signal Analyser have both already returned. This service does not call those services itself; n8n fetches their results first and passes them in. It reasons over the transcript, structured extraction, RAG results, and Call Signal Analyser results, but does **not** produce the complete final report — that's the Gemini Final Analysis LLM Chain's job (a separate n8n node), using this service's reasoning output as one of its inputs.

## Endpoints

- `GET /health` → `{"status": "ok", "service": "langgraph_agent", "version": "0.1.0"}`
- `POST /agent/run` → mock reasoning output (see below).

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

### `POST /agent/run` response (mock)

```json
{
  "answer": "Mock reasoning answer based on the supplied evidence citing CALL_007. Real reasoning is not implemented yet (Phase 14).",
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
  "mock": true
}
```

## Planned internal graph (`app/graph.py`)

```
Planner Node → Evidence Reconciliation Node → Synthesizer Node
```

- **Planner Node:** determines which evidence and questions must be evaluated (which of `structured_extraction`/`rag_results`/`signal_analysis` were actually provided).
- **Evidence Reconciliation Node:** compares the available evidence and detects conflicts. Two documented, deterministic rules in this phase: (1) `signal_analysis.confidence < 0.65` is flagged as unreliable evidence; (2) `signal_analysis.predicted_outcome == "Sale"` together with `signal_analysis.risk_level == "High"` is flagged as an internal conflict worth human attention.
- **Synthesizer Node:** produces `reasoning_steps` (one line per evidence source actually reviewed, plus a final synthesis step), `coaching_points` (a weak/none `closing_attempt` triggers a specific closing-technique coaching point; otherwise a default), and `recommended_next_action` (branches on `signal_analysis.predicted_outcome`).

**Architecture note (unchanged from the original design):** the generic "Tool Execution" step is adapted into "Evidence Reconciliation" because n8n performs the external HTTP tool calls (RAG Service, Call Signal Analyser) before this service is invoked — this service reasons over evidence it receives, it never fetches it.

This phase implements the three-node *shape* as three plain Python functions (`planner_node`, `evidence_reconciliation_node`, `synthesizer_node` in `app/graph.py`), chained together — not an installed/executed LangGraph graph, and no LLM call. This preserves the documented API contract and node responsibilities so Phase 14 can swap in real LangGraph/LLM logic behind the same function boundaries without changing the response shape.

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
