# n8n Setup — Phase 9, Iteration 1

Setup instructions for importing and running `workflows/phase9_iteration1_intake_to_assemblyai.json` — the first slice of the real n8n workflow (webhook → pre-transcription guardrails → AssemblyAI upload → job accepted).

**Scope of this iteration (do not expect more than this):**

1. Webhook Trigger receives the submission.
2. Pre-Transcription Guardrails Check calls `guardrails_service POST /check/input` (`stage: pre_transcription`).
3. If guardrails reject, respond `422` immediately — stop.
4. If guardrails pass, upload the audio file to AssemblyAI (`POST /v2/upload`).
5. Submit a transcription job (`POST /v2/transcript`, with `speaker_labels: true`).
6. Respond `202 Accepted` with the AssemblyAI job id.

**Explicitly NOT in this iteration** (see CLAUDE.md's architecture flow for where these fit later): AssemblyAI callback/webhook handling, polling for job completion, post-transcription content guardrails, Gemini extraction, the n8n AI Agent Node, RAG Service calls, Call Signal Analyser calls, LangGraph, the Final Analysis Chain, output guardrails, or routing. The workflow **stops** at "job accepted."

**Not yet verified against a live n8n instance.** This JSON was hand-built against n8n's documented node schema (Webhook, HTTP Request, IF, Respond to Webhook at their current typeVersions) but has not been imported into an actual n8n Cloud workspace and executed — I don't have access to one. Import it, run a test submission, and treat any node-parameter mismatch as an n8n-version quirk to fix on import, not a sign the overall flow is wrong.

---

## Prerequisites

1. **An n8n Cloud account** (or a local n8n instance — see the connectivity note below).
2. **An AssemblyAI account and API key** — sign up at assemblyai.com, copy the API key from your dashboard. Free tier is sufficient for this iteration's testing.
3. **`services/guardrails_service` running and reachable from n8n.**
   - If using **n8n Cloud**: n8n Cloud cannot reach `localhost` directly. You need a tunnel (ngrok, Cloudflare Tunnel) exposing your local `guardrails_service` (port 8003), or a deployed instance. **This connectivity approach is still an open decision** (see `docs/PROGRESS.md` — "n8n local development approach"), deferred to a later Phase 9 iteration. For now, stand up whichever tunnel you have available and use its public URL.
   - If using **local n8n via Docker Compose**: n8n can reach `guardrails_service` via the Docker network directly (e.g. `http://guardrails_service:8003` if both are on the same compose network) — no tunnel needed. This repo's root `docker-compose.yml` (Phase 6) already runs `guardrails_service`; adding an n8n service to that compose file is part of the still-open connectivity decision.

## Environment variables (set in n8n)

In n8n Cloud: **Settings → Environment Variables** (or per-credential, if you prefer n8n's credential store over the plain expressions this workflow uses). In local n8n via Docker Compose: pass as container environment variables.

| Variable | Example value | Notes |
|---|---|---|
| `GUARDRAILS_SERVICE_URL` | `https://your-tunnel-id.ngrok-free.app` | No trailing slash. Must be reachable from wherever n8n actually runs. |
| `ASSEMBLYAI_API_KEY` | `your-assemblyai-api-key` | From your AssemblyAI dashboard. Never commit this value — it's a secret, kept out of the workflow JSON itself (referenced via `{{ $env.ASSEMBLYAI_API_KEY }}`, not hardcoded). |

## Import steps

1. In n8n, go to **Workflows → Import from File** (or **Import from URL**) and select `n8n/workflows/phase9_iteration1_intake_to_assemblyai.json`.
2. Set the two environment variables above.
3. Open the **Webhook Trigger** node and copy its **Test URL** (and **Production URL**, once you activate the workflow) — you'll need this for the curl examples in `n8n/examples.md`.
4. Make sure `guardrails_service` is running and reachable at `GUARDRAILS_SERVICE_URL` (test with `curl $GUARDRAILS_SERVICE_URL/health` first).
5. Click **Execute Workflow** in n8n (test mode) or send a real request to the Test URL (see `n8n/examples.md`).
6. Do **not** toggle the workflow to **Active** for production use yet — this iteration is for review and local/test-mode validation only.

## Known gaps to expect on first import

- **Binary data handling on the Webhook node** varies slightly by n8n version. This workflow assumes multipart/form-data is parsed automatically into `$binary.audio_file` (matching a form field literally named `audio_file`) and other fields into `$json.body.*`. If your n8n version handles this differently, adjust the Webhook node's options and the two downstream expressions that reference `$binary.audio_file` accordingly.
- **HTTP Request node `typeVersion`** — built against `4.2` (a recent, common version). Older n8n installs may present a slightly different parameter panel (e.g. `bodyParametersJson` instead of `jsonBody`) after import; the request shape and target URLs are correct regardless.
- **AssemblyAI response field names** are current as of this iteration's design (`upload_url` from `/v2/upload`, `id`/`status` from `/v2/transcript`) — verify against AssemblyAI's current API docs if anything fails, since third-party APIs can change.

## Testing this iteration

See `n8n/examples.md` for full webhook payload examples and curl commands. Quick smoke test once imported and env vars are set:

```bash
curl -i -X POST "<your webhook test URL>" \
  -F "audio_file=@/path/to/a/short/test.mp3" \
  -F "agent_name=Sarah Levi" \
  -F "call_date=2026-07-15"
```

Expect either:
- `202 Accepted` with an `assemblyai_job_id`, or
- `422` with a `GUARDRAILS_REJECTED` error (check the `flags` for why — likely a file-format/size/metadata issue if this happens on a clean test file).

Stop here and report back for review — do not proceed to the next iteration (callback handling, post-transcription guardrails) without explicit approval.
