# n8n Setup — Full Pipeline (Nodes 1–16)

Setup instructions for the live workflow `XSight - Full Pipeline (Nodes 1-16) - Intake to Final Analysis and Routing` (n8n Cloud workflow ID `RBII7JvRDFWwy98x`), exported to `workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`. This supersedes the old Iteration 1 setup notes below for the connectivity/credential steps; the AssemblyAI section of that original file is still accurate and repeated here for completeness.

**Everything through node 15 (the Router) has been verified with simulated end-to-end test executions** (real Code/Set/IF logic, simulated external responses for AssemblyAI/Gemini/RAG/Call-Signal-Analyser/LangGraph) — see `README.md`'s "Verified test runs" section. **A fully live run (real credentials, real network calls to all four services) has not been executed** — the steps below are exactly what's needed to do that.

---

## 1. Gemini credential (blocks a live run)

Three nodes need a Gemini credential that does **not exist yet** in the connected n8n instance:

- `Gemini Information Extractor`
- `AI Agent Node - Classify and Enrich`
- `Gemini Final Analysis Chain`

All three reference a credential named exactly **`Gemini API - XSight`** (n8n credential type `Google Gemini(PaLM) Api`, internally `googlePalmApi`). To fix:

1. In n8n, go to **Credentials → Add Credential → Google Gemini(PaLM) Api**.
2. Name it exactly `Gemini API - XSight` (or bind the existing unresolved reference to whatever credential you create — n8n will prompt you to select one for each of the three nodes since the reference currently has no ID).
3. Paste a real Gemini API key (from Google AI Studio / Google Cloud).
4. Open each of the three nodes and confirm the credential is now resolved (no red warning icon).
5. Each node currently targets `modelId: models/gemini-2.5-flash`. This has **not been confirmed reachable** with a real key/region — open each Gemini node and verify the model is available to your key, adjusting if needed.

**Do not** treat any placeholder/mock string as a working key — the workflow will not call Gemini successfully until a real key is bound.

---

## 2. Backend service URLs (blocks a live run for nodes 9, 10, 12)

Three environment variables must be set to URLs n8n can actually reach:

| Variable | Used by | Notes |
|---|---|---|
| `RAG_SERVICE_URL` | `HTTP Request - RAG Service` (node 9) | No trailing slash. Real service (Amazon Bedrock KB) — already deployed per `docs/PROGRESS.md`, but **this build could not confirm which host/port it's reachable at from n8n**. |
| `CALL_SIGNAL_ANALYSER_URL` | `HTTP Request - Call Signal Analyser` (node 10) | No trailing slash. Per `docs/PROGRESS.md`, still a Phase 6 mock skeleton as of this build — confirm it's actually running somewhere reachable before testing live. |
| `LANGGRAPH_AGENT_URL` | `HTTP Request - LangGraph Agent` (node 12) | No trailing slash. Per `docs/PROGRESS.md`, still a Phase 6 mock skeleton as of this build. |

**What we know for certain:** `guardrails_service` is deployed to a real AWS EC2 instance and the existing pre-transcription guardrails node is hardcoded to `http://3.151.162.120:8003` (confirmed by reading the live workflow's node parameters directly). **What we do not know:** whether `rag_service`, `call_signal_analyser`, and `langgraph_agent` are deployed on that same EC2 host on ports 8001/8002/8004 (matching `docker-compose.yml`'s port assignments), or are only runnable locally. **Before setting these env vars, verify with curl**, e.g.:

```bash
curl http://3.151.162.120:8001/health   # if this responds, RAG_SERVICE_URL=http://3.151.162.120:8001
curl http://3.151.162.120:8002/health   # if this responds, CALL_SIGNAL_ANALYSER_URL=http://3.151.162.120:8002
curl http://3.151.162.120:8004/health   # if this responds, LANGGRAPH_AGENT_URL=http://3.151.162.120:8004
```

If any of those don't respond, that service is likely only running locally via `docker compose up -d` (see `docs/api_contracts.md`), in which case it needs the same tunnel treatment as `guardrails_service` originally did: stand up ngrok or a Cloudflare Tunnel pointed at the relevant local port (8001/8002/8004) and set the corresponding env var to the tunnel's public HTTPS URL. **This step could not be completed from this environment** — no shell access to the actual service hosts or ability to start a tunnel from here. This is the single manual step most likely to block a fully live end-to-end test today.

Set these in n8n Cloud under **Settings → Environment Variables**, or as container environment variables if running n8n locally via Docker Compose.

---

## 3. AssemblyAI (unchanged from the earlier iteration — already working)

An `AssemblyAI` credential (type `httpHeaderAuth`) already exists in the connected instance and is already bound to the `Upload Audio to AssemblyAI` and `Submit Transcription Job` / `Poll AssemblyAI Transcript Status` nodes. No action needed unless the key has expired.

---

## 4. Import / activation steps

1. If working from a fresh n8n instance instead of the already-connected one: **Workflows → Import from File**, select `n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`.
2. Complete steps 1 and 2 above (Gemini credential, three service URLs).
3. Test with a real submission against the Webhook Trigger's Test URL (multipart form: `audio_file`, `agent_name`, `call_date`, optional `customer_name`/`notes` — see `examples.md`).
4. Confirm the response is a `200` with the complete final-output JSON (`guardrail_status: "pass"` or `"human_review_required"`), or a structured `error` response if something upstream failed — **never a raw n8n exception**.
5. Only then consider activating the workflow (**Active** toggle) for anything beyond manual/test-mode runs.

## 5. What "done" looks like without a live run

Because of the two open items above (Gemini credential, three service URLs), this build's verification is a **simulated end-to-end test**, not a live one: `test_workflow` executed every Code/Set/IF node for real and substituted realistic mock responses only for the four external HTTP/Gemini calls. See `README.md`'s "Verified test runs" for exact results (execution IDs `15` auto-pass, `16` human-review-required). Once sections 1 and 2 above are completed, the same webhook payload should produce an equivalent live result — nothing in the node logic itself depends on the calls being simulated.

---

## Historical: Iteration 1 setup (nodes 1–4 only, superseded by the above for full-pipeline testing)

**Scope of that original iteration:** Webhook Trigger → Pre-Transcription Guardrails Check → AssemblyAI upload → job accepted (no polling, no downstream analysis). The live workflow has since grown real AssemblyAI polling (Iteration 2a) and then the full pipeline documented above — kept here only for historical context.

### Prerequisites (still accurate)

1. **An n8n Cloud account** (or a local n8n instance).
2. **An AssemblyAI account and API key** — already configured (see section 3 above).
3. **`services/guardrails_service` running and reachable from n8n** — already resolved: deployed to `http://3.151.162.120:8003`.

### Known gaps to expect on first import (still accurate for any node in the workflow)

- **Binary data handling on the Webhook node** varies slightly by n8n version. This workflow assumes multipart/form-data is parsed automatically into `$binary.audio_file` (matching a form field literally named `audio_file`) and other fields into `$json.body.*`.
- **HTTP Request node `typeVersion`** — built against `4.4` throughout the full pipeline (a recent, common version).
- **AssemblyAI response field names** are current as of this build — verify against AssemblyAI's current API docs if anything fails.
