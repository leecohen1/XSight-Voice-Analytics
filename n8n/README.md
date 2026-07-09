# n8n

n8n workflow exports and orchestration documentation for XSight.

**Status:** Not yet implemented. Workflow design begins at Phase 9 (transcription decision + mock webhook flow) and is connected to real services from Phase 10 onwards.

## Purpose

n8n Cloud is the orchestration layer of XSight. It receives the sales call submission from the React frontend, coordinates calls to the Input/Output Guardrails Service, the transcription API, Gemini (for information extraction and final analysis), and the FastAPI AI microservices (RAG Service, Call Signal Analyser, LangGraph Agent), then returns the final structured analysis result.

## Planned nodes

1. Webhook Trigger
2. Input Guardrails HTTP Request (NeMo)
3. IF pass/fail
4. Transcription API HTTP Request
5. Information Extractor — Gemini
6. HTTP Request to RAG Service
7. HTTP Request to Call Signal Analyser
8. HTTP Request to LangGraph Agent
9. Final Analysis Generation — Gemini
10. Output Guardrails HTTP Request (NeMo)
11. IF safe / human review (confidence < 0.65 routes to human_review_required)
12. Respond to Webhook

See [CLAUDE.md](../CLAUDE.md) for full node details and the local-to-cloud connectivity note (ngrok / Cloudflare Tunnel / local n8n via Docker Compose).
