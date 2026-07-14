# n8n

n8n workflow exports and orchestration documentation for XSight.

**Status:** Not yet implemented. Workflow design begins at Phase 9 (transcription decision + mock webhook flow) and is connected to real services from Phase 10 onwards.

## Purpose

n8n Cloud handles operational workflow orchestration only for XSight — it does not perform AI reasoning. It receives the sales call submission from the React frontend, coordinates the two-stage Guardrails Service checks and the transcription API, calls Gemini for structured semantic extraction only, makes a single call into the LangGraph agent (which internally invokes the RAG Service and Call Signal Analyser as tools and returns the complete final output), calls the Output Guardrails, and returns the final structured analysis result. n8n never calls the RAG Service or Call Signal Analyser directly — see [CLAUDE.md](../CLAUDE.md#component-responsibility-boundaries) for the full responsibility split.

## Planned nodes

1. Webhook Trigger
2. Pre-Transcription File Validation HTTP Request (deterministic checks)
3. IF pass/fail (file validation)
4. Transcription API HTTP Request
5. Post-Transcription Input Content Guardrails HTTP Request (NeMo + deterministic rules)
6. IF pass/fail (content guardrails)
7. Information Extractor — Gemini (structured semantic extraction only)
8. HTTP Request to LangGraph Agent (single call — RAG Service and Call Signal Analyser are invoked internally by LangGraph as tools)
9. Output Guardrails HTTP Request (NeMo + deterministic rules)
10. IF safe / human review (confidence < 0.65, conflicting evidence, missing citations, or severe guardrail flags all route to `human_review_required`)
11. Respond to Webhook

See [CLAUDE.md](../CLAUDE.md) for full node details and the local-to-cloud connectivity note (ngrok / Cloudflare Tunnel / local n8n via Docker Compose).
