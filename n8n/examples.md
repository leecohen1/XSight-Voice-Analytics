# n8n Webhook — Payload and curl Examples

**Update:** the live workflow now implements the full 16-node pipeline (see `README.md` and `workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`), not just the Iteration 1 slice these examples were originally written for. The request shape below (multipart form: `audio_file`, `agent_name`, `call_date`, optional `customer_name`/`notes`) is unchanged. What changed is the **response**: instead of stopping at a `202 Accepted` job-id acknowledgement, a successful submission now runs all the way through Gemini extraction, the AI Agent Node, the parallel RAG/Call-Signal-Analyser calls, LangGraph, the Final Analysis Chain, and the Router, returning the complete final-output JSON synchronously (see "6. Full pipeline — final analysis response" below). Sections 1–5 below are kept for historical reference (they described the old `202`/partial-flow behavior) but no longer match what the live workflow returns for a passing submission — see section 6 for the current contract.

Examples for `workflows/phase9_iteration1_intake_to_assemblyai.json`. Replace `<WEBHOOK_URL>` with the Webhook Trigger node's Test URL (while building/reviewing) or Production URL (once the workflow is activated) — see `n8n/SETUP.md`.

The webhook expects `multipart/form-data`, not JSON, because it carries a binary audio file alongside metadata fields.

---

## Request shape

| Field | Type | Required | Notes |
|---|---|---|---|
| `audio_file` | file (binary) | Yes | The call recording. Extension/MIME/size are validated by the pre-transcription guardrails check (see `services/guardrails_service/README.md` for the exact allowed lists and limits). |
| `agent_name` | text | Yes | Passed through to the guardrails check's `submission_metadata.agent_name`. |
| `call_date` | text | Yes | `YYYY-MM-DD`. Passed through to `submission_metadata.call_date`. |
| `customer_name` | text | No | Accepted but not used by this iteration (no downstream node reads it yet). |
| `notes` | text | No | Accepted but not used by this iteration. |

---

## 1. Successful submission (guardrails pass, AssemblyAI accepts)

```bash
curl -i -X POST "<WEBHOOK_URL>" \
  -F "audio_file=@./sample_call.mp3;type=audio/mpeg" \
  -F "agent_name=Sarah Levi" \
  -F "call_date=2026-07-15" \
  -F "customer_name=Acme Corp" \
  -F "notes=Discovery call, second contact"
```

**Expected response — `202 Accepted`:**

```json
{
  "status": "accepted",
  "assemblyai_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "assemblyai_status": "queued",
  "message": "Transcription job accepted. Callback/polling handling is not implemented yet (future Phase 9 iteration)."
}
```

At this point, AssemblyAI is transcribing the file in the background. Nothing in this iteration checks on it again — that's deliberately deferred (see `n8n/SETUP.md`'s scope note).

---

## 2. Rejected submission — unsupported file type

```bash
curl -i -X POST "<WEBHOOK_URL>" \
  -F "audio_file=@./not_actually_audio.txt;type=text/plain" \
  -F "agent_name=Sarah Levi" \
  -F "call_date=2026-07-15"
```

**Expected response — `422 Unprocessable Entity`:**

```json
{
  "error": {
    "code": "GUARDRAILS_REJECTED",
    "message": "File extension '.txt' is not in the allowed list ['.flac', '.m4a', '.mp3', '.ogg', '.wav']; MIME type 'text/plain' is not in the allowed list [...]",
    "details": ["unsupported_extension", "unsupported_mime_type"]
  }
}
```

The AssemblyAI nodes are never reached — the `Guardrails Passed?` IF node routes straight to the rejection response.

---

## 3. Rejected submission — missing required metadata

```bash
curl -i -X POST "<WEBHOOK_URL>" \
  -F "audio_file=@./sample_call.mp3;type=audio/mpeg"
  # agent_name and call_date omitted
```

**Expected response — `422 Unprocessable Entity`:**

```json
{
  "error": {
    "code": "GUARDRAILS_REJECTED",
    "message": "submission_metadata.agent_name is required.; submission_metadata.call_date is required.",
    "details": ["missing_agent_name", "missing_call_date"]
  }
}
```

---

## 4. Rejected submission — file too large

```bash
curl -i -X POST "<WEBHOOK_URL>" \
  -F "audio_file=@./huge_recording_over_100mb.wav;type=audio/wav" \
  -F "agent_name=Sarah Levi" \
  -F "call_date=2026-07-15"
```

**Expected response — `422 Unprocessable Entity`:**

```json
{
  "error": {
    "code": "GUARDRAILS_REJECTED",
    "message": "File size 150000000 bytes exceeds the 104857600 byte limit.",
    "details": ["file_too_large"]
  }
}
```

---

## Direct guardrails_service check (for isolating failures)

If a webhook test fails in an unexpected way, check whether the guardrails call itself would pass, independent of n8n and AssemblyAI:

```bash
curl -X POST http://localhost:8003/check/input \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "pre_transcription",
    "file_metadata": {"filename": "sample_call.mp3", "mime_type": "audio/mpeg", "size_bytes": 1000000},
    "submission_metadata": {"agent_name": "Sarah Levi", "call_date": "2026-07-15"}
  }'
```

This bypasses n8n and AssemblyAI entirely — useful for confirming the guardrails logic itself (already covered by `services/guardrails_service/tests/test_main.py`) versus an n8n wiring/connectivity issue (tunnel down, wrong `GUARDRAILS_SERVICE_URL`, etc.).

## Direct AssemblyAI check (for isolating failures)

```bash
curl -X POST https://api.assemblyai.com/v2/upload \
  -H "authorization: $ASSEMBLYAI_API_KEY" \
  --data-binary "@./sample_call.mp3"
# -> {"upload_url": "https://cdn.assemblyai.com/upload/..."}

curl -X POST https://api.assemblyai.com/v2/transcript \
  -H "authorization: $ASSEMBLYAI_API_KEY" \
  -H "content-type: application/json" \
  -d '{"audio_url": "<upload_url from above>", "speaker_labels": true}'
# -> {"id": "...", "status": "queued", ...}
```

If these two calls work directly but the n8n workflow fails at the AssemblyAI step, the issue is in the workflow's node wiring (binary property name, header expression, env var), not AssemblyAI itself.

---

## 6. Full pipeline — final analysis response (current behavior)

Once transcription completes and both guardrail stages pass, the same webhook call now continues through Gemini extraction, the AI Agent Node, RAG + Call Signal Analyser (parallel), LangGraph, the Final Analysis Chain, and the Router, and returns a single synchronous response matching CLAUDE.md's final output JSON schema:

```bash
curl -i -X POST "<WEBHOOK_URL>" \
  -F "audio_file=@./sample_call.mp3;type=audio/mpeg" \
  -F "agent_name=Sarah Levi" \
  -F "call_date=2026-07-26" \
  -F "customer_name=Acme Manufacturing"
```

**Expected response — `200 OK`, auto-pass case** (matches simulated test execution `15` — see `README.md`):

```json
{
  "transcript": "Agent: ...\nCustomer: ...",
  "call_summary": "...",
  "customer_intent": "medium",
  "main_objection": "price",
  "customer_sentiment": "neutral",
  "call_outcome": "Follow-up Needed",
  "agent_performance_score": 3,
  "lead_quality_score": 4,
  "similar_calls": [{"call_id": "CALL_007", "agent_name": "Daniel Cohen", "sale_result": "Sale", "main_objection": "price", "similarity_score": 0.88, "reason": "..."}],
  "coaching_feedback": ["...", "..."],
  "recommended_next_action": "...",
  "suggested_follow_up_email": "...",
  "routing_category": "pricing_negotiation",
  "confidence": 0.86,
  "risk_level": "Medium",
  "detected_signals": ["price objection", "competitor comparison", "weak closing attempt"],
  "limitations": "... (always includes the pipeline's known gaps -- inline guardrails, missing output guardrails, any clamped audio features, the speaker-mapping heuristic)",
  "guardrail_status": "pass"
}
```

**Expected response — `200 OK`, human-review-required case** (matches simulated test execution `16`): identical shape, but `"guardrail_status": "human_review_required"` whenever the Call Signal Analyser's confidence drops below `0.65` and/or LangGraph reports `evidence_conflicts` — see `README.md` for the exact router rule.

**Expected response on an upstream failure** (any of nodes 5–13 erroring, e.g. RAG/Call-Signal-Analyser/LangGraph/Gemini unreachable) — a structured error, never a raw n8n exception:

```json
{
  "status": "error",
  "stage": "rag_service",
  "error_code": "rag_service_unreachable",
  "message": "RAG Service (POST /query) call failed: ...",
  "processing_time_ms": 1234,
  "workflow_version": "phase9-16-full-pipeline"
}
```
