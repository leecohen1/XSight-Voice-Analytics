# frontend

React web application for XSight.

**Status:** Not yet implemented. Built starting at Phase 16, after all backend services and the n8n workflow have been tested independently.

## Planned sections

- Home / project overview
- Sales Call Upload (audio file, agent name, call date, optional customer/company name, optional notes)
- Results Page — displays the full analysis output (transcript, summary, insights, scores, similar calls, coaching feedback, follow-up recommendation, routing category, confidence, limitations)
- Analytics Dashboard
- Ollama Assistant sidebar panel

The frontend communicates with the backend exclusively through the n8n Cloud webhook. See [CLAUDE.md](../CLAUDE.md) for the full output JSON schema and architecture flow.
