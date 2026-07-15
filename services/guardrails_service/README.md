# guardrails_service

Input and output safety validation for XSight.

**Status:** Phase 6 mock skeleton — deterministic rules, the two-stage `POST /check/input` contract, and error handling are real. NeMo Guardrails (topic restrictions, unsafe content, prompt-injection/jailbreak rails) is not integrated yet — Phase 11.

**Stack (planned, Phase 11):** FastAPI, NeMo Guardrails, deterministic custom validation rules. **Stack (this phase):** FastAPI + Pydantic only — no model downloads, no API keys.

## Endpoints

- `GET /health` → `{"status": "ok", "service": "guardrails_service", "version": "0.1.0"}`
- `POST /check/input` — one endpoint, two stages, driven by a `stage` discriminator field (not by which caller invokes it):
  - `stage: "pre_transcription"` — deterministic file/metadata checks, before a transcript exists.
  - `stage: "post_transcription"` — deterministic transcript-content checks (NeMo rails land here in Phase 11).
- `POST /check/output` — validates the assembled final analysis (missing citations, placeholder/unsupported facts, low-confidence routing).

### `POST /check/input` — pre-transcription request

```json
{
  "stage": "pre_transcription",
  "file_metadata": {
    "filename": "call.mp3",
    "mime_type": "audio/mpeg",
    "size_bytes": 1000000,
    "duration_seconds": 300
  },
  "submission_metadata": {
    "agent_name": "Sarah Levi",
    "call_date": "2026-07-15"
  }
}
```

**Deterministic checks:** filename present; extension in `{.mp3, .wav, .m4a, .flac, .ogg}`; MIME type in the matching allowed set; `0 < size_bytes ≤ 100 MB`; `duration_seconds ≤ 1800s` (30 min) when provided; `submission_metadata.agent_name` and `.call_date` required and non-empty.

### `POST /check/input` — post-transcription request

```json
{
  "stage": "post_transcription",
  "transcript": "Agent: ... Customer: ...",
  "submission_metadata": {}
}
```

**Deterministic checks:** transcript not empty; at least 20 characters; contains both `Agent:` and `Customer:` (case-insensitive); no keyword match against a documented prompt-injection phrase list (`ignore previous instructions`, `you are now`, `system prompt`, `jailbreak`, etc.); at least one keyword match against a documented sales-relevance list (`price`, `contract`, `demo`, `crm`, ...) — otherwise flagged `possible_off_topic`.

An invalid/unrecognized `stage` value (or a missing one) returns a `422 VALIDATION_ERROR` — the discriminator itself is schema-validated, not a business-rule check.

### `POST /check/output` request

```json
{
  "final_analysis": {"call_summary": "..."},
  "citations": ["CALL_007"],
  "historical_claims_present": true,
  "confidence": 0.82
}
```

**Deterministic checks:** `historical_claims_present: true` with an empty `citations` list → `missing_citation` (hard fail). Every string value inside `final_analysis` (recursively) is scanned against a documented placeholder-phrase list (`lorem ipsum`, `[insert`, `TODO:`, `fake data`, ...) → `unsupported_placeholder_fact` (hard fail) if matched. `confidence < 0.65` → `human_review_required: true` and a `low_confidence` flag, but — per CLAUDE.md's separation of guardrail validity from Router-level confidence routing — **does not by itself fail `pass`**.

### Shared response shape (`/check/input` and `/check/output`)

```json
{
  "pass": true,
  "reason": "",
  "flags": [],
  "safe_text": null,
  "human_review_required": false,
  "mock": true
}
```

`reason` is a semicolon-joined summary of every triggered check when `pass` is `false` (or `human_review_required` is `true`); `flags` lists the individual rule codes so callers can branch on specific failures.

## Error handling

Structural/schema failures (missing required fields, wrong types, invalid `stage` enum) return the shared error shape with `422 VALIDATION_ERROR` — distinct from a guardrail *content* failure, which is a normal `200` response with `"pass": false`.

```json
{"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": [...]}}
```

## Running locally

```bash
cd services/guardrails_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

```bash
curl http://localhost:8003/health

curl -X POST http://localhost:8003/check/input \
  -H "Content-Type: application/json" \
  -d '{"stage": "pre_transcription", "file_metadata": {"filename": "call.mp3", "mime_type": "audio/mpeg", "size_bytes": 1000000, "duration_seconds": 300}, "submission_metadata": {"agent_name": "Sarah Levi", "call_date": "2026-07-15"}}'

curl -X POST http://localhost:8003/check/output \
  -H "Content-Type: application/json" \
  -d '{"final_analysis": {"call_summary": "Price objection raised."}, "citations": ["CALL_007"], "historical_claims_present": true, "confidence": 0.82}'
```

## Testing

```bash
cd services/guardrails_service
pytest -v
```

## Docker

```bash
docker build -t xsight-guardrails-service services/guardrails_service
docker run -p 8003:8003 xsight-guardrails-service
```

Or via the root `docker-compose.yml` (`docker compose up guardrails_service`).

See [CLAUDE.md](../../CLAUDE.md) and [docs/api_contracts.md](../../docs/api_contracts.md) for the full contract.
