# n8n

n8n workflow exports and orchestration documentation for XSight.

**Status:** Not yet implemented. Workflow design begins at Phase 9 (transcription decision + mock webhook flow) and is connected to real services from Phase 10 onwards.

## Purpose

n8n Cloud is the central workflow orchestrator for XSight — it calls every AI component in the pipeline directly. It receives the sales call submission from the React frontend, coordinates the two-stage Guardrails Service checks and the transcription API, calls Gemini for structured semantic extraction, calls the RAG Service and Call Signal Analyser directly (in parallel), calls the LangGraph agent for multi-step reasoning over their results, calls Gemini a second time (the Final Analysis LLM Chain) to assemble the complete result, calls the Output Guardrails, and returns the final structured analysis result. No AI component calls another — n8n orchestrates all of it directly. See [CLAUDE.md](../CLAUDE.md#component-responsibility-boundaries) for the full responsibility split.

## Planned nodes

1. Webhook Trigger
2. Pre-Transcription File Validation HTTP Request (deterministic checks)
3. IF pass/fail (file validation)
4. Transcription API HTTP Request
5. Post-Transcription Input Content Guardrails HTTP Request (NeMo + deterministic rules)
6. IF pass/fail (content guardrails)
7. Information Extractor — Gemini (structured semantic extraction only)
8. HTTP Request to RAG Service (parallel branch)
9. HTTP Request to Voice / Call Signal Analyser (parallel branch)
10. Merge — join the RAG Service and Call Signal Analyser results
11. HTTP Request to LangGraph Agent (multi-step reasoning over the transcript, extraction, RAG results, and Call Signal Analyser results — does not call those services itself)
12. Final Analysis LLM Chain — Gemini (combines the extraction, RAG results, Call Signal Analyser results, and LangGraph's reasoning output into the complete final output JSON)
13. Output Guardrails HTTP Request (NeMo + deterministic rules)
14. IF safe / human review / category routing (confidence < 0.65, conflicting evidence, missing citations, or severe guardrail flags all route to `human_review_required`)
15. Respond to Webhook

See [CLAUDE.md](../CLAUDE.md) for full node details and the local-to-cloud connectivity note (ngrok / Cloudflare Tunnel / local n8n via Docker Compose).
