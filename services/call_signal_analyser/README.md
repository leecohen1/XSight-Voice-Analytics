# call_signal_analyser

Voice / Call Signal Analyser.

**Status:** Phase 6 mock skeleton — API contract, enum/range validation, and error handling are real; scoring is a deterministic, documented mock. Full PyTorch classifier is Phase 13.

**Stack (planned, Phase 13):** FastAPI, PyTorch, pandas, lightweight audio preprocessing (not librosa-scale acoustic feature extraction). **Stack (this phase):** FastAPI + Pydantic only — no model downloads, no API keys, JSON input only (no multipart audio upload yet).

**Called by:** n8n, directly — in parallel with the RAG Service. Not called by the LangGraph agent.

## Endpoints

- `GET /health` → `{"status": "ok", "service": "call_signal_analyser", "version": "0.1.0"}`
- `POST /analyse-call` → mock prediction (see below). Real behavior in Phase 13: PyTorch inference over transcript-derived, structured-extraction, and lightweight audio-derived features.

### `POST /analyse-call` request

```json
{
  "transcript": "Agent: ... Customer: ...",
  "audio_features": {
    "call_duration_seconds": 420,
    "silence_ratio": 0.18,
    "speaking_rate_wpm": 145,
    "speech_to_non_speech_ratio": 0.82,
    "agent_talk_ratio": 0.62,
    "average_energy_level": "medium"
  },
  "structured_fields": {
    "customer_intent": "high",
    "main_objection": "price",
    "customer_sentiment": "mixed",
    "closing_attempt": "weak",
    "decision_maker_present": true
  }
}
```

All enums (`customer_intent`, `main_objection`, `customer_sentiment`, `closing_attempt`) and numeric ranges (`call_duration_seconds` 180–900, `silence_ratio` 0.05–0.35, `speaking_rate_wpm` 100–190, `speech_to_non_speech_ratio` 0.65–0.95, `agent_talk_ratio` 0.35–0.75) match [docs/dataset_design.md](../../docs/dataset_design.md) §5–§11 exactly.

### `POST /analyse-call` response (mock)

```json
{
  "predicted_outcome": "Follow-up Needed",
  "lead_quality_score": 4,
  "agent_performance_score": 3,
  "risk_level": "Medium",
  "confidence": 0.72,
  "detected_signals": ["price objection", "high customer interest", "weak closing attempt"],
  "human_review_required": false,
  "mock": true
}
```

(This is the exact response for the request example above — see `tests/test_main.py::test_analyse_call_matches_documented_example`, which pins it.)

## Documented mock scoring rules (`app/mock_rules.py`)

These rules exist only to produce a repeatable, testable response shape. **They are not a trained model** — real inference is a PyTorch classifier (Phase 13). Every table is complete and deterministic; nothing here is randomized.

**Confidence** = `0.70 + intent_adj + closing_adj + sentiment_adj + decision_maker_adj`, clamped to `[0, 1]` and rounded to 2 decimals:

| `customer_intent` | adj | | `closing_attempt` | adj | | `customer_sentiment` | adj | | `decision_maker_present` | adj |
|---|---|---|---|---|---|---|---|---|---|---|
| high | +0.10 | | strong | +0.05 | | positive | +0.05 | | true | 0.00 |
| medium | 0.00 | | medium | +0.02 | | neutral | 0.00 | | false | −0.08 |
| low | −0.15 | | weak | −0.05 | | mixed | −0.03 | | | |
| unclear | −0.25 | | none | −0.15 | | negative | −0.10 | | | |

`human_review_required = confidence < 0.65` (matches the production threshold in CLAUDE.md §4).

**`risk_level`:** `confidence ≥ 0.75` → Low; `0.50 ≤ confidence < 0.75` → Medium; `confidence < 0.50` → High.

**`predicted_outcome`:** `closing_attempt` in (`weak`, `none`) → always `Follow-up Needed` (mirrors Contrast Case 3 in the historical dataset — a well-qualified call left open by weak closing, regardless of intent); else `customer_intent == "high"` with `closing_attempt` in (`strong`, `medium`) → `Sale`; else `customer_intent == "low"` → `No Sale`; else `Follow-up Needed`.

**`lead_quality_score`** (1–5) from `customer_intent`: high→4, medium→3, low→2, unclear→1.

**`agent_performance_score`** (1–5) from `closing_attempt`: strong→5, medium→4, weak→3, none→1.

**`detected_signals`:** `"{main_objection} objection"` (omitted if `main_objection == "none"`), `"{intent label} customer interest"`, `"{closing_attempt} closing attempt"`, plus `"decision-maker not present"` if `decision_maker_present` is false.

## Error handling

Same shared shape as the other services:

```json
{"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": [...]}}
```

## Running locally

```bash
cd services/call_signal_analyser
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

```bash
curl http://localhost:8002/health

curl -X POST http://localhost:8002/analyse-call \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing.",
    "audio_features": {"call_duration_seconds": 420, "silence_ratio": 0.18, "speaking_rate_wpm": 145, "speech_to_non_speech_ratio": 0.82, "agent_talk_ratio": 0.62, "average_energy_level": "medium"},
    "structured_fields": {"customer_intent": "high", "main_objection": "price", "customer_sentiment": "mixed", "closing_attempt": "weak", "decision_maker_present": true}
  }'
```

## Testing

```bash
cd services/call_signal_analyser
pytest -v
```

## Docker

```bash
docker build -t xsight-call-signal-analyser services/call_signal_analyser
docker run -p 8002:8002 xsight-call-signal-analyser
```

Or via the root `docker-compose.yml` (`docker compose up call_signal_analyser`).

See [CLAUDE.md](../../CLAUDE.md) and [docs/api_contracts.md](../../docs/api_contracts.md) for the full contract.
