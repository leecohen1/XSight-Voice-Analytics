# guardrails_service

Input and output safety validation for XSight.

**Status:** Not yet implemented. Planned for Phase 11.

**Stack:** FastAPI, NeMo Guardrails (custom rule-based validation may supplement NeMo where needed).

**Endpoints:**
- `POST /check/input` — detects empty/too-short transcripts, off-topic or non-sales-call content, offensive content, prompt injection attempts, and unsupported/invalid metadata.
- `POST /check/output` — detects invented CRM facts, unsupported business conclusions, fake legal/financial promises, overconfident recommendations, invented call details, and missing `call_id` citations for historical-call claims.

See [CLAUDE.md](../../CLAUDE.md) for the full response contract.
