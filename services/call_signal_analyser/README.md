# call_signal_analyser

Voice / Call Signal Analyser.

**Status:** Phase 6 mock skeleton — API contract, enum/range validation, and error handling are real; scoring is a deterministic, documented mock. Full PyTorch classifier is Phase 13.

**Demo-day update (still Phase 6 engine, not Phase 13):** `audio_features` fields can now be `null`/omitted to represent a feature that couldn't be measured (no fabricated defaults — see Ground Truth Rules in `CLAUDE.md` and the "Missing audio evidence" section below). This did **not** change the response contract's existing fields (`predicted_outcome`, `lead_quality_score`, `agent_performance_score`, `risk_level`, `confidence`, `detected_signals`, `human_review_required`) — it only added a new optional `missing_features` field.

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

All enums (`customer_intent`, `main_objection`, `customer_sentiment`, `closing_attempt`) and numeric ranges (`call_duration_seconds` 180–900, `silence_ratio` 0.05–0.35, `speaking_rate_wpm` 100–190, `speech_to_non_speech_ratio` 0.65–0.95, `agent_talk_ratio` 0.35–0.75) match [docs/dataset_design.md](../../docs/dataset_design.md) §5–§11 exactly — when a value IS provided, these ranges still apply.

**Every field of `audio_features` is optional.** Any field may be `null`, or omitted entirely, to represent a feature that couldn't be measured (no audio file available, preprocessing failed to extract it, etc.). A missing feature is never silently defaulted to a fabricated value (e.g. `silence_ratio` is never defaulted to `0.0`) — see "Missing audio evidence" below for exactly how this affects the response.

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
  "mock": true,
  "missing_features": []
}
```

(This is the exact response for the request example above, with all audio features present — see `tests/test_main.py::test_analyse_call_matches_documented_example`, which pins it.)

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

## Missing audio evidence (demo-day uncertainty pass)

Per the Ground Truth Rules in `CLAUDE.md`, an audio-derived feature that could not be measured must be representable as missing and must never be silently defaulted to a fabricated value (e.g. `silence_ratio` must never quietly become `0.0`). This service handles that as follows:

1. **Detection.** Of the five scored `audio_features` fields (`call_duration_seconds`, `silence_ratio`, `speaking_rate_wpm`, `speech_to_non_speech_ratio`, `agent_talk_ratio` — `average_energy_level` is excluded since it was already optional and is not used in scoring), any field that is `null` or omitted is treated as missing. Nothing is inferred or defaulted in its place.
2. **Confidence penalty.** Each missing feature subtracts a fixed amount from the confidence score, applied on top of the existing structured-fields adjustments, before clamping to `[0, 1]` and rounding:

   | criticality | features | penalty per missing feature |
   |---|---|---|
   | critical | `silence_ratio`, `agent_talk_ratio` | −0.15 |
   | standard | `call_duration_seconds`, `speaking_rate_wpm`, `speech_to_non_speech_ratio` | −0.05 |

   `silence_ratio` and `agent_talk_ratio` are classified as critical because they're the load-bearing signals downstream reasoning leans on most: `agent_talk_ratio` is the only speaker-tagging-derived feature at all, and `silence_ratio` is the primary engagement/dead-air check used to sanity-check the transcript-derived intent/closing read. The other three are still real evidence (still penalized) but are corroborating/contextual rather than load-bearing on their own.
3. **Surfacing.** The response's `missing_features` field (additive to the contract) lists exactly which fields were missing, in the fixed order above. An empty list means every scored audio feature was present.
4. **Forced human review.** `human_review_required` is `true` whenever `confidence < 0.65` **or** at least one *critical* feature (`silence_ratio` or `agent_talk_ratio`) is missing — even if the confidence number alone would still clear 0.65. Reasoning: a confidence score computed without a load-bearing input isn't the same guarantee as the same number computed with complete evidence, so it must not silently pass as if it were. Missing only *standard* features does not force review on its own — it only lowers confidence, which may or may not cross the threshold on its own.

See `app/mock_rules.py` (`_AUDIO_FEATURE_FIELDS`, `_CRITICAL_AUDIO_FEATURES`, `_MISSING_FEATURE_CONFIDENCE_ADJ`, `detect_missing_audio_features`, `compute_missing_feature_penalty`) for the exact, complete rule set, and `tests/test_main.py` (the "Missing audio evidence" test block) for worked examples.

## Limitations

- **This is still a deterministic rule-based scoring engine, not a trained PyTorch classifier.** `predicted_outcome`, `lead_quality_score`, `agent_performance_score`, `confidence`, and `detected_signals` all come from the fixed lookup tables and formula in `app/mock_rules.py` — they are not learned from data. The real feature-based PyTorch classifier described in CLAUDE.md component 4 is Phase 13 (explicitly deferred as part of today's demo-day scope: the decision was to keep this deterministic engine and add honest uncertainty representation on top of it, not to train a model).
- The missing-audio-feature confidence penalties and criticality classification (critical vs. standard) are hand-authored heuristics for today's demo, not calibrated against labeled data — they should be revisited once `call_signal_training.csv` and the Phase 13 classifier exist.
- `audio_features` itself is still a required JSON object on the request (its fields are what became optional) — there is still no multipart/raw audio file upload in this service; that remains a Phase 13 concern, and is out of scope for today's change.
- `mock: true` remains accurate — nothing about this change makes the engine's underlying predictions a trained model.

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
