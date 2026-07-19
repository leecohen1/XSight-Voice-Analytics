# n8n

n8n workflow exports and orchestration documentation for XSight.

**Status:** Phase 9, Iteration 1 implemented — `workflows/phase9_iteration1_intake_to_assemblyai.json` covers nodes 1–4 below (webhook intake through AssemblyAI job submission and an immediate acknowledgement) with node 2 built as a real Pre-Transcription Guardrails call against `services/guardrails_service`, not a placeholder. Everything from post-transcription guardrails onward (nodes 5–16) is not yet implemented. See `SETUP.md` for import/connectivity instructions and `examples.md` for payload/curl examples.

## Iteration 1 (current)

**Scope:** Webhook Trigger → Pre-Transcription Guardrails Check → (reject with `422` **or** continue) → Upload Audio to AssemblyAI → Submit Transcription Job → Respond `202 Accepted` with the AssemblyAI job id.

**Deliberately out of scope for this iteration:** AssemblyAI callback/webhook handling, polling for job completion, post-transcription content guardrails, Gemini extraction, the AI Agent Node, RAG Service, Call Signal Analyser, LangGraph, the Final Analysis Chain, output guardrails, routing. The workflow stops once the transcription job is accepted.

**Not yet verified against a live n8n instance** — built against n8n's documented node schema, not confirmed by an actual import/execution (no n8n Cloud access in this environment). See `SETUP.md` for what to check on first import.

**Open dependency:** which local-to-cloud connectivity approach (ngrok / Cloudflare Tunnel / local n8n via Docker Compose) exposes `guardrails_service` to n8n is still an open decision (`docs/PROGRESS.md`) — `SETUP.md` documents both paths generically via an environment variable (`GUARDRAILS_SERVICE_URL`) so the workflow doesn't hardcode one before that's settled.

## Purpose

n8n Cloud is the central workflow orchestrator for XSight — it calls every AI component in the pipeline directly. It receives the sales call submission from the React frontend, coordinates the two-stage Guardrails Service checks and the transcription API, calls Gemini for structured semantic extraction, calls a limited-role n8n AI Agent Node for intent classification and field enrichment, calls the RAG Service and Call Signal Analyser directly (in parallel, using the payloads the AI Agent Node prepared), calls the LangGraph agent for multi-step reasoning over their merged results, calls Gemini a second time (the Final Analysis LLM Chain) to assemble the complete result, calls the Output Guardrails, and routes the response. No AI component calls another — n8n orchestrates all of it directly. See [CLAUDE.md](../CLAUDE.md#component-responsibility-boundaries) for the full responsibility split.

## Planned nodes

*(Nodes 1–4 are implemented as of Iteration 1 — adapted slightly from the original plan since AssemblyAI's real API is a two-call upload-then-submit flow, not one "Transcription API HTTP Request." Node 4 below is that pair plus the acknowledgement response. Nodes 5+ are not yet implemented.)*

1. Webhook Trigger — **implemented**
2. Pre-Transcription File Validation HTTP Request (deterministic checks) — **implemented** (as "Pre-Transcription Guardrails Check")
3. IF pass/fail (file validation) — **implemented** (as "Guardrails Passed?", with an explicit reject-response node on the false branch)
4. Transcription API HTTP Request — **implemented**, as three nodes: Upload Audio to AssemblyAI → Submit Transcription Job → Respond - Job Accepted (202, with the AssemblyAI job id)
5. Post-Transcription Input Content Guardrails HTTP Request (NeMo + deterministic rules)
6. IF pass/fail (content guardrails)
7. Information Extractor — Gemini (structured semantic extraction only)
8. n8n AI Agent Node — intent classification and field enrichment (limited role — see below)
9. HTTP Request to RAG Service (parallel branch, using the AI Agent Node's payload)
10. HTTP Request to Voice / Call Signal Analyser (parallel branch, using the AI Agent Node's payload)
11. Merge Results — join the RAG Service and Call Signal Analyser results
12. HTTP Request to LangGraph Agent (multi-step reasoning over the transcript, extraction, enrichment, RAG results, and Call Signal Analyser results — runs after the parallel calls because it consumes both; does not call those services itself)
13. Final Analysis LLM Chain — Gemini (combines the extraction, enrichment, RAG results, Call Signal Analyser results, and LangGraph's reasoning output into the complete final output JSON)
14. Output Guardrails HTTP Request (NeMo + deterministic rules)
15. Router — confidence and category routing (confidence < 0.65, conflicting evidence, missing citations, or severe guardrail flags all route to `human_review_required`)
16. Respond to Webhook

**n8n AI Agent Node (node 8) — limited role.** Must: classify the submission intent, enrich the extracted sales fields, determine which downstream services are relevant, prepare their structured payloads. Must not: generate the final report, replace LangGraph's reasoning, generate coaching feedback, reconcile evidence, or invent missing information.

See [CLAUDE.md](../CLAUDE.md) for full node details and the local-to-cloud connectivity note (ngrok / Cloudflare Tunnel / local n8n via Docker Compose).
