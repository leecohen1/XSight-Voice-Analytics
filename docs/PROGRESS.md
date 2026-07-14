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

Created `docs/architecture.md`: embeds the corrected flowchart from `CLAUDE.md`, then adds detail that doesn't belong in the spec file — design principles behind the flow, a step-by-step request lifecycle (originally §3.1–3.10, later renumbered to §3.1–3.11 by the correction below) walking through both guardrails stages, the AI services calls, and the confidence-based human-review routing decision; a component responsibility matrix (location, endpoints, callers, dependencies); a data-flow section (CSV → ChromaDB / PyTorch, Llama.cpp vs. Ollama isolation); a deployment topology section (local Docker Compose vs. EC2, n8n tunnel note); an error/rejection-paths table; and a list of open items still pending later phases (transcription provider, n8n connectivity approach, audio library).

**Phase 4 architectural decision (same day):** the user decided to make LangGraph the system's single AI orchestrator and final synthesis layer, removing the separate "Final Analysis Generation — Gemini" step. New responsibility boundaries, applied consistently across `CLAUDE.md`, `docs/architecture.md`, and `docs/technology_decisions.md`:
- **n8n:** operational workflow orchestration only (webhook, guardrails, transcription, a single call to LangGraph, response routing) — no direct calls to the RAG Service or Call Signal Analyser.
- **Gemini:** structured semantic extraction only (customer intent, main objection, customer sentiment, closing attempt, key sales events, call metadata) — no longer generates the final analysis.
- **LangGraph:** AI orchestration, tool execution, evidence reconciliation, reasoning, and final response generation — invokes the RAG Service and Call Signal Analyser as tools and returns the complete final output JSON.
- **RAG Service / Call Signal Analyser:** unchanged responsibilities (retrieval-only / scoring-only), but now called by LangGraph exclusively, not by n8n.
- **Guardrails Service:** unchanged — input (both stages) and output validation only; output guardrails now validate LangGraph's assembled result instead of Gemini's.

Consequences applied: the n8n node list dropped from 14 to 11 nodes (direct RAG/Signal-Analyser/Final-Analysis nodes collapsed into one LangGraph call); the Mermaid diagrams in `CLAUDE.md` and `docs/architecture.md` were redrawn so Gemini feeds LangGraph directly and LangGraph fans out to RAG/Signal-Analyser as tool calls; the LangGraph agent's endpoint contract was rewritten to return the complete final output JSON schema (plus `tools_used`, `reasoning_steps`, `evidence_conflicts` for transparency) instead of a narrow `answer`/`recommended_next_action` shape; the human-review routing rule was expanded beyond confidence alone to include evidence conflicts, missing citations, severe guardrail flags, and tool failure; the Call Signal Analyser gained a `feature_summary` output field and must source semantic fields from Gemini's extraction rather than re-deriving them; the Prompt Engineering Log surfaces list replaced "n8n Final Analysis prompt" with "LangGraph synthesizer prompt". The two-stage input guardrails design, the shared `POST /check/input` endpoint, the output guardrails stage, and the deployment topology were preserved unchanged, per explicit instruction.

**Open item flagged, not invented:** which LLM backs LangGraph's Planner/Synthesizer nodes (Gemini via API, a separate model, or a local model) was never specified in the original spec and is now load-bearing (LangGraph does the reasoning/synthesis work the removed Gemini step used to do). Marked as "TBD — Phase 14" in `CLAUDE.md`, `docs/architecture.md`, and `docs/technology_decisions.md` rather than assumed.

**Phase 4 correction — restored n8n-centered orchestration (same day):** after reviewing the LangGraph-centralization decision above, the user reverted it and asked for n8n-centered orchestration instead, with LangGraph scoped to reasoning only, and a separate Gemini Final Analysis step restored. This supersedes the "Phase 4 architectural decision" entry above. Applied consistently across `CLAUDE.md`, `docs/architecture.md`, and `docs/technology_decisions.md`:
- **n8n:** the central workflow orchestrator again — calls every AI component directly (guardrails, transcription, Gemini extraction, RAG Service, Call Signal Analyser, LangGraph, Gemini Final Analysis Chain, output guardrails, routing). No AI component calls another.
- **Gemini:** two distinct roles, both via n8n — Information Extractor (structured extraction only, unchanged) and a restored **Final Analysis LLM Chain** that assembles the complete final output JSON from the extraction, RAG results, Call Signal Analyser results, and LangGraph's reasoning output.
- **RAG Service / Call Signal Analyser:** unchanged responsibilities, but called directly by n8n again (in parallel with each other), not by LangGraph.
- **LangGraph:** narrowed to multi-step reasoning only. Receives the transcript, metadata, Gemini's extraction, RAG results, and Call Signal Analyser results as input (does not call those services itself) and returns a reasoning output (`answer`, `evidence_used`, `reasoning_steps`, `evidence_conflicts`, `recommended_next_action`, `coaching_points`) — not the complete final report.
- **Guardrails Service:** unchanged; output guardrails now validate the Gemini Final Analysis Chain's result (not LangGraph's).

Consequences applied: the n8n node list grew from 11 to 15 nodes (RAG Service, Call Signal Analyser, a Merge node, the LangGraph call, and the restored Final Analysis Chain are all explicit nodes again; RAG and Call Signal Analyser run in parallel, merged before the LangGraph call); the Mermaid diagrams in `CLAUDE.md` and `docs/architecture.md` were redrawn so n8n fans out to RAG + Signal Analyser in parallel, both feed LangGraph, and LangGraph feeds the Gemini Final Analysis Chain; the LangGraph endpoint contract was rewritten back to a narrow reasoning-output shape (dropped `tools_used`/full schema fields, added `evidence_used`/`coaching_points`); the Prompt Engineering Log surfaces list restored "Final Analysis LLM Chain prompt" in place of "LangGraph synthesizer prompt"; the "Agent — LangGraph" rationale in `docs/technology_decisions.md` was rewritten and explicitly notes the superseded design rather than silently deleting the history. The two-stage input guardrails design, the shared `POST /check/input` endpoint, the output guardrails stage, and the deployment topology were preserved unchanged, per explicit instruction.

**Corrections made per this request:**
1. **Audio feature flow clarified:** the Call Signal Analyser performs its own lightweight audio preprocessing internally (no separate preprocessing microservice); n8n forwards the audio file (or a reference to it) to the analyser's request payload, the same file already validated pre-transcription and sent to the transcription API.
2. **Datasets clarified as two separate files:** `data/historical_sales_calls.csv` (RAG corpus, ≥20 detailed transcripts) and `data/call_signal_training.csv` (classifier training data, ~150–300 rows, no transcripts) — compatible but distinct schemas, not one file serving both purposes. Reflected in `CLAUDE.md`'s repository structure tree as well.

Phase 5 has not been started. Phase 4 remains in progress pending review of this correction.
