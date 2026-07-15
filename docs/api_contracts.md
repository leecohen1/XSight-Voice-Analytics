# XSight — API Contracts (Phase 6 mock services)

This document is the single reference for the four backend services' HTTP contracts, as implemented by their **Phase 6 mock skeletons**. Every endpoint, request/response shape, and validation rule here is real and enforced today; the *content* of `POST` responses (beyond `/health`) is a deterministic, clearly-labeled mock (`"mock": true`) until each service's real logic phase (RAG Service: Phase 12, Call Signal Analyser: Phase 13, Guardrails NeMo rails: Phase 11, LangGraph: Phase 14).

All four services are independently runnable FastAPI apps. See [docker-compose.yml](../docker-compose.yml) for local ports, and `services/<name>/README.md` for service-specific detail.

| Service | Port | Health | Main endpoint(s) |
|---|---|---|---|
| `rag_service` | 8001 | `GET /health` | `POST /query` |
| `call_signal_analyser` | 8002 | `GET /health` | `POST /analyse-call` |
| `guardrails_service` | 8003 | `GET /health` | `POST /check/input`, `POST /check/output` |
| `langgraph_agent` | 8004 | `GET /health` | `POST /agent/run` |

---

## Shared conventions

### Health response (all four services)

```json
{"status": "ok", "service": "<service_name>", "version": "0.1.0"}
```

### Structured error shape (all four services)

Every error response — validation failures, 404s, unhandled exceptions — uses this shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [{"loc": ["body", "transcript"], "msg": "...", "type": "..."}]
  }
}
```

| `code` | HTTP status | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Request body failed Pydantic schema/constraint validation. `details` lists every failing field. |
| `HTTP_ERROR` | 4xx (typically 404/405) | Routing or method error (wrong path, wrong verb). |
| `INTERNAL_ERROR` | 500 | Unhandled exception — should not occur in normal use of these mock skeletons. |

**Note (guardrails_service only):** a guardrail *content* failure (bad file, off-topic transcript, missing citation) is **not** an HTTP error — it's a normal `200` response with `"pass": false`. Only structurally invalid requests (missing fields, wrong types, invalid `stage`) return `422`.

---

## 1. `rag_service` (port 8001)

### `GET /health`

```bash
curl http://localhost:8001/health
```

### `POST /query`

```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing.",
    "metadata": {"agent_name": "Sarah Levi", "call_duration_seconds": 420, "sale_result": "Sale"},
    "top_k": 3
  }'
```

**Validation:** `transcript` required, min 20 characters. `top_k` integer, 1–10. `metadata` optional, all sub-fields optional.

**Response (mock, deterministic):**

```json
{
  "similar_calls": [
    {"call_id": "CALL_007", "agent_name": "Daniel Cohen", "sale_result": "Sale", "main_objection": "price", "similarity_score": 0.89, "reason": "Mock similarity result based on a price objection resolved through a quantified reframe."}
  ],
  "insight": "Mock grounded insight referencing 1 historical call(s) (CALL_007). Real retrieval is not implemented yet.",
  "citations": ["CALL_007"],
  "grounded": true,
  "mock": true
}
```

Drawn from a fixed 5-call hardcoded pool, sliced to `top_k` — not sourced from `data/historical_sales_calls.csv` (its existence is optionally logged at startup only).

**Invalid request example:**

```bash
curl -i -X POST http://localhost:8001/query -H "Content-Type: application/json" -d '{"transcript": ""}'
# HTTP/1.1 422 Unprocessable Entity
```

---

## 2. `call_signal_analyser` (port 8002)

### `GET /health`

```bash
curl http://localhost:8002/health
```

### `POST /analyse-call`

```bash
curl -X POST http://localhost:8002/analyse-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing.",
    "audio_features": {"call_duration_seconds": 420, "silence_ratio": 0.18, "speaking_rate_wpm": 145, "speech_to_non_speech_ratio": 0.82, "agent_talk_ratio": 0.62, "average_energy_level": "medium"},
    "structured_fields": {"customer_intent": "high", "main_objection": "price", "customer_sentiment": "mixed", "closing_attempt": "weak", "decision_maker_present": true}
  }'
```

**Validation:** JSON input only (multipart audio upload is not implemented in this phase). Enums (`customer_intent`, `main_objection`, `customer_sentiment`, `closing_attempt`) and numeric ranges (`call_duration_seconds` 180–900, `silence_ratio` 0.05–0.35, `speaking_rate_wpm` 100–190, `speech_to_non_speech_ratio` 0.65–0.95, `agent_talk_ratio` 0.35–0.75) match `docs/dataset_design.md` §5–§11 exactly.

**Response (mock, deterministic — documented rules in `services/call_signal_analyser/README.md`):**

```json
{
  "predicted_outcome": "Follow-up Needed",
  "lead_quality_score": 4,
  "agent_performance_score": 3,
  "risk_level": "Medium",
  "confidence": 0.72,
  "detected_signals": ["price objection", "high customer interest", "weak closing attempt"],
  "human_review_required": false,
  "mock": true
}
```

`human_review_required` is `true` whenever `confidence < 0.65` (matches the production threshold in CLAUDE.md §4).

**Invalid request example:**

```bash
curl -i -X POST http://localhost:8002/analyse-call -H "Content-Type: application/json" -d '{"transcript": "too short"}'
# HTTP/1.1 422 Unprocessable Entity
```

---

## 3. `guardrails_service` (port 8003)

### `GET /health`

```bash
curl http://localhost:8003/health
```

### `POST /check/input` — pre-transcription stage

```bash
curl -X POST http://localhost:8003/check/input \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "pre_transcription",
    "file_metadata": {"filename": "call.mp3", "mime_type": "audio/mpeg", "size_bytes": 1000000, "duration_seconds": 300},
    "submission_metadata": {"agent_name": "Sarah Levi", "call_date": "2026-07-15"}
  }'
```

**Deterministic checks:** filename present; extension in `{.mp3, .wav, .m4a, .flac, .ogg}`; MIME type in the matching allowed set; `0 < size_bytes ≤ 100 MB`; `duration_seconds ≤ 1800s` when provided; `agent_name`/`call_date` required.

### `POST /check/input` — post-transcription stage

```bash
curl -X POST http://localhost:8003/check/input \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "post_transcription",
    "transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing and the contract.",
    "submission_metadata": {}
  }'
```

**Deterministic checks:** transcript non-empty, ≥ 20 characters; contains both `Agent:` and `Customer:`; no prompt-injection phrase match (`ignore previous instructions`, `system prompt`, `jailbreak`, ...); at least one sales-relevance keyword match (`price`, `contract`, `crm`, ...) — otherwise `possible_off_topic`. NeMo Guardrails rails are not integrated in this phase (Phase 11).

**Response shape (both stages):**

```json
{"pass": true, "reason": "", "flags": [], "safe_text": null, "human_review_required": false, "mock": true}
```

### `POST /check/output`

```bash
curl -X POST http://localhost:8003/check/output \
  -H "Content-Type: application/json" \
  -d '{
    "final_analysis": {"call_summary": "Price objection raised."},
    "citations": ["CALL_007"],
    "historical_claims_present": true,
    "confidence": 0.82
  }'
```

**Deterministic checks:** `historical_claims_present: true` with empty `citations` → `missing_citation` (hard fail). Every string inside `final_analysis` scanned against a placeholder-phrase list (`lorem ipsum`, `[insert`, `TODO:`, ...) → `unsupported_placeholder_fact` (hard fail). `confidence < 0.65` → `human_review_required: true` (does not by itself fail `pass`).

**Invalid request examples:**

```bash
curl -i -X POST http://localhost:8003/check/input -H "Content-Type: application/json" -d '{"stage": "bogus_stage"}'
# HTTP/1.1 422 Unprocessable Entity — invalid discriminator value

curl -i -X POST http://localhost:8003/check/output -H "Content-Type: application/json" -d '{"final_analysis": {}, "citations": []}'
# HTTP/1.1 422 Unprocessable Entity — confidence is required
```

---

## 4. `langgraph_agent` (port 8004)

### `GET /health`

```bash
curl http://localhost:8004/health
```

### `POST /agent/run`

```bash
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

**Validation:** `question` required, min 5 characters. `transcript` required, min 20 characters. `metadata`, `structured_extraction`, `rag_results`, `signal_analysis` all optional, default to empty.

**Response (mock, deterministic — see `services/langgraph_agent/README.md` for the full Planner → Evidence Reconciliation → Synthesizer rule set):**

```json
{
  "answer": "Mock reasoning answer based on the supplied evidence citing CALL_007. Real reasoning is not implemented yet (Phase 14).",
  "reasoning_steps": ["Reviewed structured extraction", "Reviewed historical evidence", "Reviewed call signal output", "Synthesized coaching recommendation"],
  "evidence_conflicts": [],
  "coaching_points": ["Strengthen the closing ask — propose a concrete next step with a date."],
  "recommended_next_action": "Schedule a follow-up with the decision-maker.",
  "evidence_used": ["structured_extraction", "rag_service", "call_signal_analyser"],
  "mock": true
}
```

This service never calls the RAG Service or Call Signal Analyser itself — n8n fetches their results first and passes them in (`rag_results`, `signal_analysis`). No LangGraph graph is installed or executed in this phase; the three-node shape is implemented as three plain, deterministic Python functions.

**Invalid request example:**

```bash
curl -i -X POST http://localhost:8004/agent/run -H "Content-Type: application/json" -d '{}'
# HTTP/1.1 422 Unprocessable Entity — question and transcript are required
```

---

## Running all four services

```bash
docker compose up -d
docker compose ps            # confirm all four are "healthy"
bash scripts/test_mock_services.sh
docker compose down
```

Or locally without Docker, one terminal per service:

```bash
cd services/<service_name>
pip install -r requirements.txt
uvicorn app.main:app --reload --port <8001|8002|8003|8004>
```

See `scripts/test_mock_services.sh` for an automated smoke test covering all four `/health` endpoints, one successful request per main endpoint, and one intentionally invalid request per service (15 checks total).
