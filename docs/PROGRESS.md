# XSight — Progress Tracker

Tracks completed phases and open decisions. Updated at the end of every phase.

## Phase status

| Phase | Description | Status |
|---|---|---|
| 1 | Repository structure | Complete |
| 2 | README and project documentation | Complete |
| 3 | Technology decisions document | Complete |
| 4 | Architecture document with Mermaid diagram | In progress |
| 5 | Adapted CSV dataset | Not started |
| 6 | FastAPI mock service skeletons | Not started |
| 7 | Docker Compose for local backend services | Not started |
| 8 | curl/Postman testing documentation | Not started |
| 9 | Transcription API decision + mock n8n webhook flow | Not started |
| 10 | Connect n8n to mock FastAPI services (ngrok or local n8n) | Not started |
| 11 | Implement NeMo Guardrails service | Not started |
| 12 | Implement RAG service | Not started |
| 13 | Implement PyTorch call signal analyser | Not started |
| 14 | Implement LangGraph agent | Not started |
| 15 | Test full backend and n8n flow end-to-end without frontend | Not started |
| 16 | React application skeleton | Not started |
| 17 | Connect React to n8n webhook | Not started |
| 18 | Add results dashboard and Ollama Assistant panel | Not started |
| 19 | Docker, EC2 deployment notes and final demo documentation | Not started |
| 20 | Prompt engineering log and final cleanup | Not started |

## Open decisions

- **Transcription API:** Not yet chosen. To be decided at Phase 9.
- **n8n local development approach:** ngrok vs. Cloudflare Tunnel vs. local n8n in Docker Compose. To be decided and documented at Phase 9.

## Phase log

### Phase 1 — Repository structure (complete)

Created the top-level repository structure: `frontend/`, `n8n/`, `services/` (with `rag_service/`, `call_signal_analyser/`, `guardrails_service/`, `langgraph_agent/`), `data/`, `models/`, `docs/`, `demo/`. Added placeholder `README.md` files to every main folder, a top-level `README.md` with project overview, `CLAUDE.md` with the full project specification, this `PROGRESS.md` file, and a `.gitignore` covering Python, Node, React, Docker, environment variables, model files, audio files, and local data artifacts (e.g. ChromaDB data).

Confirmed by user. Committed as "Phase 1: Repository structure".

### Phase 2 — README and project documentation (complete)

Expanded the top-level `README.md` into comprehensive project documentation (per user's choice of scope): added a "Why XSight" motivation section, detailed user personas, an example (abridged) output JSON, a system components section summarizing each service's role, an architecture overview, a documentation index table pointing to `CLAUDE.md` and planned Phase 3/4/20 docs, and a phase-grouped development roadmap table. Technology decisions and the detailed architecture diagram remain out of scope here — they are dedicated documents built in Phase 3 and Phase 4.

Confirmed by user. Committed as "Phase 2: README and project documentation".

### Phase 3 — Technology decisions document (complete)

Created `docs/technology_decisions.md`: for every layer of the chosen stack (frontend, orchestration, transcription, n8n LLM, guardrails, RAG, call signal analysis, agent, local assistant, data, deployment), documents the alternatives considered, why the chosen technology won, and the trade-off accepted. Opens with a "Guiding constraints" section (backend-first local-service development, grounded/non-hallucinated output, breadth of AI engineering techniques, two separated local LLM runtimes) that explains the reasoning pattern applied throughout, and closes with a summary table. Updated the README documentation index to link directly to this file.

Confirmed by user. Committed as "Phase 3: Technology decisions document".

**Phase 3 refinement (same day):** the user reviewed the doc and requested corrections to align it with the actual project plan before moving on. Applied to `docs/technology_decisions.md`, `CLAUDE.md`, and this file:
- Replaced the "local-first development" framing (inaccurate given n8n Cloud is the orchestrator from day one) with "backend-first, local-service development".
- Finalized Guardrails as NeMo Guardrails + FastAPI + deterministic custom validation rules, with responsibilities split explicitly between the two.
- Split input validation into two stages — pre-transcription file validation (deterministic, no transcript yet) and post-transcription content guardrails (NeMo + deterministic) — and corrected the pipeline order, n8n node list, architecture flow text, and Mermaid diagram in `CLAUDE.md` accordingly (`POST /check/input` stays one endpoint, stage-aware).
- Expanded the Call Signal Analyser beyond transcript-only: added lightweight real audio-derived features (call duration, silence ratio, speaking rate, speech-to-non-speech ratio, optional average energy level) alongside transcript/structured features, while keeping it a feature-based (not raw-audio deep learning) classifier. Missing features must be marked unknown, never fabricated — `silence_ratio` is no longer auto-defaulted to `0.0`.
- Clarified the dataset design: the RAG corpus (≥20 detailed transcripts) and the PyTorch classifier dataset (~150–300 synthetic/adapted feature rows via controlled variations, split into train/validation/test with no duplicate-row leakage) are explicitly two separate datasets — the project does not contain 150–300 full transcripts.
- Expanded the transcription evaluation criteria (Phase 9) to include Hebrew support, diarization/speaker labels/timestamps, supported formats, size/duration limits, latency, cost, n8n integration complexity, and demo reliability.
- Refined the Llama.cpp/Ollama separation rationale: separate services provide prompt isolation, state isolation, independent testing, different validation rules, separate resource control, and clearer failure boundaries — but the process boundary alone doesn't guarantee no behavior leakage; that also requires keeping prompts and validation logic themselves separate.
- Preserved unchanged: React, n8n Cloud, Gemini, LangChain + ChromaDB + HuggingFace embeddings + Llama.cpp for RAG, `sentence-transformers/all-MiniLM-L6-v2`, LangGraph, Ollama, CSV + ChromaDB, Docker → AWS EC2.

Phase 4 has not been started.

### Phase 4 — Architecture document with Mermaid diagram (in progress)

Created `docs/architecture.md`: embeds the corrected flowchart from `CLAUDE.md`, then adds detail that doesn't belong in the spec file — design principles behind the flow, a step-by-step request lifecycle (§3.1–3.10) walking through both guardrails stages, the AI services call, and the confidence-based human-review routing decision; a component responsibility matrix (location, endpoints, callers, dependencies); a data-flow section (CSV → ChromaDB / PyTorch, Llama.cpp vs. Ollama isolation); a deployment topology section (local Docker Compose vs. EC2, n8n tunnel note); an error/rejection-paths table; and a list of open items still pending later phases (transcription provider, n8n connectivity approach, audio library). Updated the README documentation index to link directly to the file.

Awaiting user confirmation to mark Phase 4 complete.
