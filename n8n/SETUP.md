# n8n Setup — Full Pipeline (Nodes 1–16)

Setup instructions for the live workflow `XSight - Full Pipeline (Nodes 1-16) - Intake to Final Analysis and Routing` (n8n Cloud workflow ID `RBII7JvRDFWwy98x`), exported to `workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`. This supersedes the old Iteration 1 setup notes below for the connectivity/credential steps; the AssemblyAI section of that original file is still accurate and repeated here for completeness.

**Update — a fully live run has since been executed and verified.** All steps below (Gemini credential, backend service URLs) are now complete for the current connected n8n instance; this document originally described what blocked a live run, and now doubles as the record of exactly what was done to unblock it, plus what a *fresh* n8n instance (a new environment, disaster recovery, onboarding) would still need to redo. See `docs/PROGRESS.md`'s "Demo-day cross-phase push" entry for the live execution result and the four real bugs found and fixed along the way. The original framing is otherwise preserved below, since the instructions themselves are still exactly what a fresh setup needs.

**Everything through node 15 (the Router) was first verified with simulated end-to-end test executions** (real Code/Set/IF logic, simulated external responses for AssemblyAI/Gemini/RAG/Call-Signal-Analyser/LangGraph) — see `README.md`'s "Verified test runs" section — before the live run described above superseded it.

---

## 1. Gemini credential — done for the current instance; needed again on any fresh import

Three nodes need a Gemini credential:

- `Gemini Information Extractor`
- `AI Agent Node - Classify and Enrich`
- `Gemini Final Analysis Chain`

**Current status:** all three now have a real credential (`Google Gemini(PaLM) Api account`) attached and confirmed working via a real live execution, targeting `modelId: models/gemini-3.5-flash`. This was done manually in the n8n editor UI — attaching it programmatically via the n8n MCP tools' `setNodeCredential` operation was attempted and failed silently three times (confirmed reproducible, isolated from other changes) — a tool limitation, not a sign the workflow itself was misconfigured.

**Important, confirmed limitation:** the credential *reference* cannot be read back through the n8n API for this specific node type, at all — so `workflows/phase9_16_full_pipeline_intake_to_final_analysis.json` contains no `credentials` field on these three nodes, even though the live workflow has it attached and working. **Importing this file does NOT restore the Gemini credential.** The three Gemini nodes must be manually reattached to a working credential before activating or executing the imported workflow — without this, every Gemini call will fail immediately on the first real or test execution. **Anyone importing that file into a fresh n8n instance must redo this step**:

1. In n8n, go to **Credentials → Add Credential → Google Gemini(PaLM) Api**.
2. Name it whatever you like (the exported workflow's reference has no ID to match against, so n8n will prompt you to select a credential for each of the three nodes on import).
3. Paste a real Gemini API key (from Google AI Studio / Google Cloud).
4. Open each of the three nodes and confirm the credential is now resolved (no red warning icon).
5. Each node targets `modelId: models/gemini-3.5-flash`, confirmed working with a real key in this project's own instance — if unavailable to your key/region, pick an available equivalent.

**Do not** treat any placeholder/mock string as a working key — the workflow will not call Gemini successfully until a real key is bound.

---

## 2. Backend service URLs — done for the current instance

**Current status:** all three URLs are hardcoded directly into each HTTP Request node's `url` parameter (no `$env.*` expression remains — this was a deliberate choice for demo reliability, since n8n Cloud environment variables added an extra point of failure without adding value once the URLs were confirmed stable):

| Node | Live URL |
|---|---|
| `HTTP Request - RAG Service` (node 9) | `http://3.20.223.245:8001/query` |
| `HTTP Request - Call Signal Analyser` (node 10) | `http://18.117.114.95:8002/analyse-call` |
| `HTTP Request - LangGraph Agent` (node 12) | `http://18.117.114.95:8004/agent/run` |
| `HTTP Request - Pre-Transcription Guardrails` (node 2, unchanged from the earlier iteration) | `http://3.151.162.120:8003/check/input` |

`call_signal_analyser` and `langgraph_agent` were deployed as live Docker containers on the `18.117.114.95` EC2 host during this session (ports 8002/8004 opened on that host's security group via the AWS API); `rag_service` and `guardrails_service` were already deployed separately, as documented in `docs/PROGRESS.md`. All four were confirmed reachable with `curl .../health` before being wired in.

**If re-importing this workflow into a fresh n8n instance or a redeployed set of services**, verify each URL still responds before relying on it:

```bash
curl http://3.20.223.245:8001/health
curl http://18.117.114.95:8002/health
curl http://18.117.114.95:8004/health
curl http://3.151.162.120:8003/health
```

If a service has moved or been redeployed elsewhere, update the corresponding node's `url` parameter directly (or reintroduce an `$env.*` expression and set it in n8n Cloud under **Settings → Environment Variables**, if centralizing these again is preferred over hardcoding).

---

## 3. AssemblyAI (unchanged from the earlier iteration — already working)

An `AssemblyAI` credential (type `httpHeaderAuth`) already exists in the connected instance and is already bound to the `Upload Audio to AssemblyAI` and `Submit Transcription Job` / `Poll AssemblyAI Transcript Status` nodes. No action needed unless the key has expired.

---

## 4. Import / activation steps

1. If working from a fresh n8n instance instead of the already-connected one: **Workflows → Import from File**, select `n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`.
2. Complete steps 1 and 2 above (Gemini credential — required again on fresh import; service URLs — already hardcoded, verify reachability).
3. Test with a real submission against the Webhook Trigger's URL (multipart form: `audio_file`, `agent_name`, `call_date`, optional `customer_name`/`notes` — see `examples.md`).
4. Confirm the response is a `200` with the complete final-output JSON (`guardrail_status: "pass"` or `"human_review_required"`), or a structured `error` response if something upstream failed — **never a raw n8n exception**.
5. **Current status: the connected instance's workflow is already Active** and has been run successfully against real production traffic (execution `21`). On a fresh import, only activate after confirming step 3/4 succeed in test mode first.

## 5. What "done" looks like — now includes a real live run

This build's verification started as a **simulated end-to-end test** (`test_workflow` executed every Code/Set/IF node for real, substituting realistic mock responses only for the four external HTTP/Gemini calls — see `README.md`'s "Verified test runs" for those results, execution IDs `15`/`16`) and has since been superseded by a **fully live run**: sections 1 and 2 above were completed, and the same kind of webhook payload (real synthesized audio, real form fields) produced a complete, correctly-routed final analysis with no simulated data anywhere in the chain (execution `21`). Getting there required finding and fixing four real bugs live against this exact workflow — see `docs/PROGRESS.md`'s "Demo-day cross-phase push" entry for the full account, and `docs/FULL_PROJECT_AUDIT.md` for the broader audit it prompted (including the finding that this workflow's own git-tracked export had fallen out of sync with these fixes — since resolved by the synchronization documented there).

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
