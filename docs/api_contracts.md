# XSight — API Contracts (Phase 6 mock services)

This document is the single reference for the four backend services' HTTP contracts, as implemented by their **Phase 6 mock skeletons**. Every endpoint, request/response shape, and validation rule here is real and enforced today; the *content* of `POST` responses (beyond `/health`) is a deterministic, clearly-labeled mock (`"mock": true`) until each service's real logic phase (RAG Service: Phase 12, Call Signal Analyser: Phase 13, Guardrails NeMo rails: Phase 11, LangGraph: Phase 14).

All five services are independently runnable FastAPI apps. See [docker-compose.yml](../docker-compose.yml) for local ports, and `services/<name>/README.md` for service-specific detail.

| Service | Port | Health | Main endpoint(s) |
|---|---|---|---|
| `rag_service` | 8001 | `GET /health` | `POST /query` |
| `call_signal_analyser` | 8002 | `GET /health` | `POST /analyse-call` |
| `guardrails_service` | 8003 | `GET /health` | `POST /check/input`, `POST /check/output` |
| `langgraph_agent` | 8004 | `GET /health` | `POST /agent/run` |
| `ai_observability_service` | 8005 | `GET /health` | `POST /observability/events`, `GET /observability/summary`, `GET /observability/daily`, `GET /observability/by-stage`, `GET /observability/by-provider`, `GET /observability/calls`, `GET /observability/calls/{call_id}`, `GET /observability/cost-breakdown` |

`ai_observability_service` (renamed from `usage_monitoring_service`) is a real (non-mock) implementation from the day it was added — it is a standalone backend feature (AI Usage, Token, and Cost Monitoring), not part of the four-service analysis pipeline above, and is **not yet wired into the n8n workflow or the frontend** — see its own README's "Known limitations" and `docs/ai_observability_integration_design.md` for the planned (not yet built) n8n integration. Its persistence architecture changed from a local SQLite `usage_events` table to Langfuse-backed tracing — see the README's "Architecture decision" section.

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

Real implementation (Phase 12) — retrieves from the provisioned Amazon
Bedrock Knowledge Base (`Retrieve` API only) over Amazon S3 Vectors. See
[services/rag_service/README.md](../services/rag_service/README.md) for the
full contract and [docs/PROGRESS.md](PROGRESS.md) for the provisioning
record.

```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing.",
    "metadata": {"agent_name": "Sarah Levi", "call_duration_seconds": 420, "sale_result": "Sale"},
    "top_k": 3,
    "filters": {"main_objection": "price"}
  }'
```

**Validation:** `transcript` required, min 20 characters. `top_k` integer, 1–10. `metadata` optional, all sub-fields optional. `filters` optional — only the 11 fields marked `allowed_for_filtering: true` in `services/rag_service/ingestion/metadata_schema.json` are honored; other keys are dropped, not rejected. At most one filter is ever applied.

**Response:**

```json
{
  "similar_calls": [
    {"call_id": "CALL_023", "agent_name": "Noa Friedman", "sale_result": "Follow-up Needed", "main_objection": "price", "similarity_score": 0.67, "reason": "Historical call CALL_023 with a 'price' objection; outcome: Follow-up Needed."}
  ],
  "insight": "Found 1 similar historical call(s) (CALL_023) — see each result's reason for the specific match.",
  "citations": ["CALL_023"],
  "grounded": true,
  "retrieval_metadata": {
    "knowledge_base_id": "EDCC0WT0OB",
    "search_type": "SEMANTIC",
    "filter_requested": "main_objection",
    "filter_applied": true,
    "dropped_filter_keys": [],
    "results_returned": 1,
    "results_above_threshold": 1
  }
}
```

Every `similar_calls[]` entry is read from Bedrock's own returned metadata — never fabricated. A result missing a required field is dropped, not filled in. When nothing clears the similarity-score floor, `insight` is `"Not enough evidence to identify similar historical calls for this transcript."`, `citations` is empty, and `grounded` is `false`.

**Invalid request example:**

```bash
curl -i -X POST http://localhost:8001/query -H "Content-Type: application/json" -d '{"transcript": ""}'
# HTTP/1.1 422 Unprocessable Entity
```

**Upstream error example** (Bedrock throttling, access denial, etc. — see `services/rag_service/README.md`'s error table for the full mapping):

```bash
# HTTP/1.1 429 Too Many Requests
{"error": {"code": "UPSTREAM_THROTTLED", "message": "Amazon Bedrock is throttling requests. Retry shortly.", "details": []}}
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

## 5. `ai_observability_service` (port 8005)

Real (non-mock) implementation — AI Usage, Token, and Cost Monitoring backend, renamed from `usage_monitoring_service` and rebuilt on Langfuse (see `services/ai_observability_service/README.md`, "Architecture decision"). Standalone: not called by n8n or the frontend yet — see the README's "Known limitations" and `docs/ai_observability_integration_design.md` for the planned integration. Per-event token/cost/latency telemetry is recorded into Langfuse (traces/spans/generations), not a local table; only `pricing_config` and `infrastructure_cost_config` remain locally SQLite-backed. Every cost figure is a decimal **string**, and every cost is explicitly an estimate, never a provider invoice. No real Langfuse account exists yet in this project — every request below runs with observability in "disabled mode" (a documented no-op) until `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` are configured.

### `GET /health`

```bash
curl http://localhost:8005/health
```

### `POST /observability/events`

Records one call's trace (spans/generations for each pipeline stage).

```bash
curl -X POST http://localhost:8005/observability/events \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "call-abc-123",
    "workflow_execution_id": "21",
    "trace_metadata": {"environment": "development", "use_case": "analyze_sales_call"},
    "events": [{
      "idempotency_key": "exec-21:information_extraction",
      "provider": "gemini",
      "service": "generative_ai",
      "model": "gemini-3.5-flash",
      "pipeline_stage": "information_extraction",
      "use_case": "analyze_sales_call",
      "input_tokens": 501,
      "output_tokens": 30,
      "total_tokens": 531,
      "audio_duration_seconds": null,
      "request_count": 1,
      "latency_ms": 840,
      "status": "success",
      "occurred_at": "2026-07-27T12:00:00Z",
      "metadata": {}
    }]
  }'
```

**Response** — reports `recorded_stage_names` / `rejected` separately; one malformed event never fails the whole batch:

```json
{
  "call_id": "call-abc-123",
  "workflow_execution_id": "21",
  "trace_id": "a1b2c3d4e5f6...",
  "observability_enabled": false,
  "recorded_stage_names": ["information_extraction"],
  "rejected": [],
  "recorded_count": 1,
  "rejected_count": 0
}
```

`trace_id` is deterministic per `call_id` — the same `call_id` always maps to the same trace, whether or not Langfuse is enabled (see the README). There is no local per-event row `id` anymore: Langfuse owns that telemetry. A malformed event is reported under `rejected` with per-item reasons, never failing the rest of the batch. `POST /usage/events` (the old path) has been removed — it now returns 404.

### `GET /observability/summary`, `/daily`, `/by-stage`, `/by-provider`, `/calls`, `/calls/{call_id}`, `/cost-breakdown`

All accept `range=today|month` and/or explicit `from`/`to` (ISO 8601, UTC, half-open `[from, to)`); `/observability/calls` additionally supports `status`, `page`, `page_size`. Every response includes `observability_enabled: bool` so a consumer can tell "zero usage this period" apart from "Langfuse isn't configured yet." See `services/ai_observability_service/README.md` for the full field-by-field breakdown and the cost-terminology table (measured usage vs. estimated variable cost vs. allocated fixed cost vs. estimated total cost). `GET /usage/summary` still works as a deprecated, undocumented alias of `GET /observability/summary` for any in-flight caller — new integrations should not use it.

```bash
curl "http://localhost:8005/observability/summary?range=month"
curl "http://localhost:8005/observability/cost-breakdown?range=month&allocation_method=flat_monthly"
```

---

## Running all five services

```bash
docker compose up -d
docker compose ps            # confirm all five are "healthy"
bash scripts/test_mock_services.sh   # covers the original four services only; ai_observability_service is not yet included in this script
docker compose down
```

Or locally without Docker, one terminal per service:

```bash
cd services/<service_name>
pip install -r requirements.txt
uvicorn app.main:app --reload --port <8001|8002|8003|8004|8005>
```

See `scripts/test_mock_services.sh` for an automated smoke test covering all four `/health` endpoints, one successful request per main endpoint, and one intentionally invalid request per service (15 checks total).

---

## 6. `call_data_service` (port 8006)

S3-backed business persistence and Overview aggregation. Written by n8n's
post-Router persistence branch; read by the React Overview / Calls / Call
Details screens. Stores records under
`xsight/application/analyzed-calls/v1/year=YYYY/month=MM/day=DD/<call_id>.json`
— deliberately outside the Bedrock Knowledge Base ingestion prefix, so a live
analyzed call can never be swept into the curated RAG corpus.

Full contract, aggregation rules and the deterministic attention formula:
[docs/overview/03_API_Mapping.md](overview/03_API_Mapping.md).

### `GET /health`

```bash
curl -s http://localhost:8006/health
# {"status":"ok","service":"call_data_service","version":"1.0.0"}
```

### `POST /calls`

Idempotent by `call_id`. Re-derives `attention` and `recovery_opportunity`
server-side from the documented formula, so a caller cannot influence routing
severity.

```bash
curl -s -X POST http://localhost:8006/calls \
  -H 'Content-Type: application/json' \
  -d '{
    "call_id": "CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c",
    "source": "live_analysis",
    "created_at": "2026-07-28T10:00:00Z",
    "call_date": "2026-07-28",
    "agent_name": "Sarah Levi",
    "customer_name": "Northwind Solutions",
    "router_reasons": [],
    "analysis": {
      "transcript": "Agent: ...\nCustomer: ...",
      "call_summary": "...",
      "call_outcome": "No Sale",
      "customer_sentiment": "neutral",
      "agent_performance_score": 4,
      "lead_quality_score": 5,
      "confidence": 0.82,
      "risk_level": "Medium",
      "guardrail_status": "pass"
    }
  }'
# 201 {"call_id":"...","key":"xsight/application/...","created":true,"overwritten":false}
```

### `GET /calls`

Query params: `limit`, `cursor`, `agent_name`, `status`, `source`,
`from_date`, `to_date`. Returns summaries without transcripts.

```bash
curl -s "http://localhost:8006/calls?limit=20&status=human_review_required"
```

### `GET /calls/{call_id}`

Full stored record including the transcript. `404 CALL_NOT_FOUND` if absent.

### `GET /overview?period=7d|30d`

The entire Overview screen, pre-aggregated: `period`, `generated_at`,
`executive_summary`, `kpis`, `close_rate_trend`, `improved_agents`,
`attention_calls`, `recent_calls`, `data_quality`. All business calculation
happens here; the frontend renders the returned values without recomputing.

```bash
curl -s "http://localhost:8006/overview?period=30d"
```

### Errors

Same structured envelope as the other services. Bodies never contain a bucket
name, object key, AWS error code, or credential detail.

| Status | Codes |
|---|---|
| 404 | `CALL_NOT_FOUND` |
| 422 | `VALIDATION_ERROR`, `MALFORMED_RECORD` |
| 500 | `INTERNAL_ERROR`, `STORAGE_KEY_REJECTED` |
| 503 | `SERVICE_MISCONFIGURED`, `STORAGE_UNAVAILABLE` |
