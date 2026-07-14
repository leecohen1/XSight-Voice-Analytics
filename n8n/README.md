# n8n

n8n workflow exports and orchestration documentation for XSight.

**Status:** Not yet implemented. Workflow design begins at Phase 9 (transcription decision + mock webhook flow) and is connected to real services from Phase 10 onwards.

## Purpose

n8n Cloud is the central workflow orchestrator for XSight — it calls every AI component in the pipeline directly. It receives the sales call submission from the React frontend, coordinates the two-stage Guardrails Service checks and the transcription API, calls Gemini for structured semantic extraction, calls a limited-role n8n AI Agent Node for intent classification and field enrichment, calls the RAG Service and Call Signal Analyser directly (in parallel, using the payloads the AI Agent Node prepared), calls the LangGraph agent for multi-step reasoning over their merged results, calls Gemini a second time (the Final Analysis LLM Chain) to assemble the complete result, calls the Output Guardrails, and routes the response. No AI component calls another — n8n orchestrates all of it directly. See [CLAUDE.md](../CLAUDE.md#component-responsibility-boundaries) for the full responsibility split.

## Planned nodes

1. Webhook Trigger
2. Pre-Transcription File Validation HTTP Request (deterministic checks)
3. IF pass/fail (file validation)
4. Transcription API HTTP Request
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
