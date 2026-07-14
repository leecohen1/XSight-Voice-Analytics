# call_signal_analyser

Voice / Call Signal Analyser.

**Status:** Not yet implemented. Planned for Phase 13.

**Stack:** FastAPI, PyTorch, pandas, lightweight audio preprocessing (not librosa-scale acoustic feature extraction).

**Called by:** the LangGraph agent only, as a tool. Not called directly by n8n.

**Endpoint:** `POST /analyse-call` — predicts call outcome, lead quality score, agent performance score, risk level, confidence, detected signals, and a `feature_summary` of the key values behind the score.

**Important:** a feature-based classifier over transcript-derived, structured-extraction (from Gemini — not re-derived here), and lightweight audio-derived features (call duration, silence ratio, speaking rate, pause duration, interruptions, etc.) — not a raw-audio deep learning model. Unavailable features are marked missing/unknown, never fabricated (e.g. `silence_ratio` is never silently defaulted to 0.0). If confidence < 0.65, the result is flagged as "Uncertain" for human review.

See [CLAUDE.md](../../CLAUDE.md) for the full feature list and input/output contract.
