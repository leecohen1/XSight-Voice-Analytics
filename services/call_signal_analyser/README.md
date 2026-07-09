# call_signal_analyser

Voice / Call Signal Analyser.

**Status:** Not yet implemented. Planned for Phase 13.

**Stack:** FastAPI, PyTorch, pandas.

**Endpoint:** `POST /analyse-call` — predicts call outcome, lead quality score, agent performance score, risk level, confidence, and detected signals.

**Important:** All features are derived from the transcript text only (word count, speaker-tagged talk ratio, keyword counts, etc.). No audio file is processed by this service — no librosa, no waveform analysis. If confidence < 0.65, the result is flagged as "Uncertain" for human review.

See [CLAUDE.md](../../CLAUDE.md) for the full feature list and input/output contract.
