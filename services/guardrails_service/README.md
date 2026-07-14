# guardrails_service

Input and output safety validation for XSight.

**Status:** Not yet implemented. Planned for Phase 11.

**Stack:** FastAPI, NeMo Guardrails, deterministic custom validation rules.

**Endpoints:**
- `POST /check/input` — invoked at two different stages: (1) before transcription, validating the uploaded file and submission metadata (deterministic checks — file type, size, duration limit, required metadata); (2) after transcription, validating the transcript content (NeMo + deterministic — empty/too-short transcript, off-topic content, offensive content, prompt injection). One endpoint; behavior driven by the request payload, not by which stage is calling it.
- `POST /check/output` — validates the Gemini Final Analysis LLM Chain's complete assembled result: invented CRM facts, unsupported business conclusions, fake legal/financial promises, overconfident recommendations, invented call details, and missing `call_id` citations for historical-call claims.

See [CLAUDE.md](../../CLAUDE.md) for the full response contract.
