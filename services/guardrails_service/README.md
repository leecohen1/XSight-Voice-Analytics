# guardrails_service

Pre-transcription input safety validation for XSight.

**Status:** first real (non-mock) implementation — deterministic checks only. Covers `POST /check/input` for the `pre_transcription` stage and `GET /health`. NeMo Guardrails, an LLM, `post_transcription` content checks, and `POST /check/output` are **not** part of this version — they are future work, not yet built. (An earlier Phase 6 mock skeleton covered a broader, but entirely fake, surface — including `post_transcription` and `/check/output` — with every response labeled `"mock": true`. That skeleton has been replaced by this real, narrower implementation; see "Migration note" below.)

**Stack:** FastAPI + Pydantic only. No model downloads, no API keys, no LLM calls.

## Endpoints

- `GET /health` → `{"status": "ok", "service": "guardrails_service", "version": "0.2.0"}`
- `POST /check/input` — deterministic pre-transcription checks.

### `POST /check/input` — request

```json
{
  "stage": "pre_transcription",
  "file_metadata": {
    "filename": "call.mp3",
    "mime_type": "audio/mpeg",
    "file_size": 1000000,
    "duration_seconds": 300
  },
  "submission_metadata": {
    "agent_name": "Sarah Levi",
    "call_date": "2026-07-15",
    "customer_name": "Acme Corp",
    "notes": "Customer asked about pricing tiers."
  }
}
```

Every field is optional at the schema level (`string | null`, `number | null`) — a missing or invalid *value* is reported as a normal `pass: false` check result, not a schema error. Text fields are capped at a reasonable maximum length (filename 255, mime_type 100, agent_name 200, call_date 50, customer_name 200, notes 5000 chars); exceeding that cap is a genuine `422` schema failure, since it's a malformed-request concern rather than a business-rule one.

### Checks performed

| Check | Response key | Rule |
|---|---|---|
| 1 | `stage_valid` | `stage` must equal `"pre_transcription"` |
| 2 | `file_present` | `file_metadata.filename` must be present and non-empty |
| 3, 4 | `file_size_allowed` | `0 < file_metadata.file_size ≤ 100 MB` (104,857,600 bytes) — `file_metadata.size_bytes` is accepted as a backward-compatible alias (see below) |
| 5 | `mime_type_allowed` | `file_metadata.mime_type` in `audio/mpeg`, `audio/mp3`, `audio/wav`, `audio/x-wav`, `audio/mp4`, `audio/m4a`, `audio/x-m4a`, `audio/ogg`, `audio/webm` |
| 6 | `metadata_valid` | `submission_metadata.agent_name` must be present and non-empty |
| 7 | `prompt_injection_detected` | `submission_metadata.notes` (only) case-insensitively scanned for: `ignore previous instructions`, `ignore all instructions`, `system prompt`, `developer message`, `reveal your instructions`, `jailbreak` |

All checks are deterministic keyword/threshold rules — no NeMo Guardrails, no LLM call.

### `POST /check/input` — response

Always `HTTP 200` for both a pass and a content-based rejection (unexpected server errors return `500` — see below):

```json
{
  "pass": true,
  "stage": "pre_transcription",
  "checks": {
    "stage_valid": true,
    "file_present": true,
    "mime_type_allowed": true,
    "file_size_allowed": true,
    "metadata_valid": true,
    "prompt_injection_detected": false
  },
  "reasons": []
}
```

`pass` is `true` only when all five positive checks pass **and** `prompt_injection_detected` is `false`. `reasons` collects one safe, human-readable string per failed check — it never echoes the raw `notes` content back, even when prompt injection is detected, only that an indicator was found. `stage` in the response always identifies which validator ran (`"pre_transcription"`) — it does not echo back whatever the caller sent in the request's `stage` field.

## Error handling

Schema-level failures (wrong JSON types, oversized text fields, structurally missing top-level objects) return `422`:

```json
{"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": [...]}}
```

Unhandled server errors return `500` with a generic message — no stack trace or internal exception detail is ever included in the response body.

## Security notes

- No binary audio content is accepted or logged by this endpoint (it validates metadata about the file, not the file itself).
- Logging is limited to a boolean presence flag for the filename — never the filename, notes, or other submitted text.
- Responses never include credentials, stack traces, or raw exception messages.
- CORS is not enabled. Add it only when a real cross-origin caller requires it — do not enable unrestricted CORS.

## Backward compatibility: `size_bytes` alias

`file_metadata.size_bytes` is accepted as a backward-compatible alias for `file_metadata.file_size`, so the current n8n workflow (which still sends `size_bytes`) works against this service without modification:

- If `file_size` is present, it is used.
- Otherwise, `size_bytes` is used.
- Both are normalized into a single internal `file_size` value *before* any check runs — `app/guardrails.py` reads only `file_size` and is not aware `size_bytes` exists, so there is exactly one validation code path regardless of which field the caller sent.
- Neither `file_size` nor `size_bytes` (nor any other request field) is echoed back in the response — the response schema is unaffected by which alias was used.

New clients should send `file_size`; `size_bytes` remains supported indefinitely as an alias, not a deprecated-and-removed shim, since the currently-deployed n8n workflow depends on it and was intentionally not modified to match this service (per explicit instruction — see below).

## ⚠️ Remaining contract gap with the currently-built n8n workflow

The Phase 9 Iteration 2a n8n workflow (`RBII7JvRDFWwy98x`, node "Prepare Guardrails Payload") sends `file_metadata.size_bytes` — now handled by the alias above — but still sends only `submission_metadata.agent_name`/`.call_date`, **not** `customer_name`/`notes`. Since `notes` drives the prompt-injection check, that check will always see an absent `notes` value (`prompt_injection_detected: false` by default) until the n8n workflow is updated to send it. This is unresolved and was not addressed here, per explicit instruction not to modify the n8n workflow.

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
  -d '{"stage": "pre_transcription", "file_metadata": {"filename": "call.mp3", "mime_type": "audio/mpeg", "file_size": 1000000, "duration_seconds": 300}, "submission_metadata": {"agent_name": "Sarah Levi", "call_date": "2026-07-15", "customer_name": "Acme Corp", "notes": "Customer asked about pricing tiers."}}'
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

## Not yet implemented

- NeMo Guardrails (topic restrictions, unsafe content, jailbreak rails beyond the keyword list above)
- `post_transcription` content checks
- `POST /check/output` (final-analysis output validation)
- LLM-backed semantic checks
- Deployment
