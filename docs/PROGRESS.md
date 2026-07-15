# XSight — Progress Tracker

Tracks completed phases and open decisions. Updated at the end of every phase.

## Phase status

| Phase | Description | Status |
|---|---|---|
| 1 | Repository structure | Complete |
| 2 | README and project documentation | Complete |
| 3 | Technology decisions document | Complete |
| 4 | Architecture document with Mermaid diagram | Complete |
| 5A | Dataset Design | Complete |
| 5B | Dataset Generation | Complete |
| 5B.0 | Historical call matrix design | Complete |
| 5B.1 | Transcript and full CSV-row authoring | Complete |
| 5C | Dataset Validation | Complete |
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

**Phase 4 correction — n8n AI Agent Node aligned with course guideline for Layer 2 (same day):** the user provided the course's exact Layer 2 flow (webhook → input validation → Information Extractor → AI Agent Node → parallel EC2 calls → collect results → LLM Chain → route) and asked for an explicit, limited-role n8n AI Agent Node between the Gemini Information Extractor and the parallel RAG Service / Call Signal Analyser calls. Applied consistently across `CLAUDE.md`, `docs/architecture.md`, and `n8n/README.md` (`docs/technology_decisions.md` was not touched — nothing in it became factually inaccurate, since the AI Agent Node is additive to the already-correct n8n-centered design):

- **New node 8 — n8n AI Agent Node**, running inside the n8n workflow (not a new FastAPI service in `services/`). Its role is fixed and limited — **must**: classify the submission intent, enrich the extracted sales fields, determine which downstream services (RAG Service, Call Signal Analyser) are relevant, prepare their structured request payloads. **Must not**: generate the final report, replace LangGraph's reasoning, generate coaching feedback, reconcile evidence, or invent missing information.
- **n8n node count grew from 15 to 16** (AI Agent Node inserted, Merge node explicitly named "Merge Results", the routing IF node explicitly named "Router"). All node numbers 8 and above shifted by one throughout `CLAUDE.md` and `docs/architecture.md` — RAG Service (9), Call Signal Analyser (10), Merge Results (11), LangGraph (12), Final Analysis LLM Chain (13), Output Guardrails (14), Router (15), Respond (16).
- The Mermaid diagrams in `CLAUDE.md` and `docs/architecture.md` were redrawn: Gemini Information Extractor → AI Agent Node → parallel RAG Service / Call Signal Analyser → Merge Results → LangGraph → Gemini Final Analysis Chain → Output Guardrails → Router → Results.
- LangGraph's input schema gained an `agent_enrichment` field (the AI Agent Node's `submission_intent`, `enriched_fields`, `relevant_services`) alongside the existing transcript/metadata/extraction/RAG-results/signal-analysis fields.
- Clarified explicitly (per the user's request) that LangGraph runs *after* the parallel RAG and Call Signal Analyser calls because it consumes both of their results as input — it does not produce them and does not call either service.
- Added "n8n AI Agent Node prompt" as a new Prompt Engineering Log surface (component 8 in `CLAUDE.md`), between the Information Extractor prompt and the Final Analysis Chain prompt.
- **Open item flagged, not invented:** which LLM backs the n8n AI Agent Node's classification/enrichment was not specified in the course guideline or by the user. Noted as an open item in `docs/architecture.md` §8, alongside the already-open LangGraph LLM-backend decision (Phase 14).

**Note on user interaction during this correction:** an initial attempted edit renamed "LangGraph Agent" to "LangGraph Reasoning Agent" throughout `CLAUDE.md` for terminology consistency with the course flow; the user rejected that specific edit, so the component's existing name ("LangGraph Agent") was kept unchanged everywhere, and only the factual flow/role updates were applied.

**Phase 4 final refinement — LangGraph internal node naming (same day):** the user pointed out that the LangGraph internal graph's middle node was still called "Tool Execution Node" even though LangGraph never makes live HTTP calls — n8n already calls the RAG Service and Call Signal Analyser before LangGraph is invoked. Renamed the internal graph structure consistently across `CLAUDE.md`, `docs/architecture.md`, and `services/langgraph_agent/README.md`:

- **Planner Node** → **Evidence Reconciliation Node** → **Synthesizer Node** (was: Planner Node → Tool Execution Node → Synthesizer Node).
- Planner Node: determines which evidence and questions must be evaluated.
- Evidence Reconciliation Node: compares the transcript, Gemini's extraction, the AI Agent Node's enrichment, the RAG evidence, and the Call Signal Analyser results; detects conflicts, missing evidence, and inconsistencies.
- Synthesizer Node: produces `reasoning_steps`, `evidence_conflicts`, `coaching_points`, and `recommended_next_action`.
- Added the architecture note: "In this implementation, the generic Tool Execution step is adapted into an Evidence Reconciliation step because n8n performs the external HTTP tool calls before LangGraph is invoked."

No change to the overall architecture, node responsibilities elsewhere in the pipeline, or the LangGraph input/output JSON contract — this was a naming/clarity fix scoped to the internal graph structure only.

Phase 4 complete. Confirmed by user. Committed as "Phase 4 complete: finalize LangGraph reasoning structure".

### Phase 5A — Dataset Design (complete)

Phase 5 was split into three sub-phases per the user's request: **5A Dataset Design**, **5B Dataset Generation**, **5C Dataset Validation** — reflecting that designing the data strategy, generating the actual CSV files, and validating them are distinct bodies of work worth tracking and approving separately.

Created `docs/dataset_design.md`: the complete data strategy for both datasets, scoped to the fictional B2B SaaS sales-tooling product context (lead/customer management, sales automation, performance analytics, CRM integrations, AI sales tools). Covers:

- Rationale for keeping `data/historical_sales_calls.csv` (RAG corpus) and `data/call_signal_training.csv` (classifier training data) as two separate files with a compatible column subset.
- Four fictional agent profiles (Sarah Levi, Daniel Cohen, Michael Ben-David, Noa Friedman) with general styles and known limitations — explicitly no agent always succeeds or always fails, and `agent_name` is deliberately excluded from the classifier dataset to prevent identity leakage.
- Full taxonomies: `sale_result` (3 values), `main_objection` (10 values), `customer_intent` (4 values), `customer_sentiment` (4 values), `closing_attempt` (4 values), `call_category` (6 values, with `Invalid Submission` explicitly excluded as guardrails-only).
- Numeric score definitions (`agent_performance_score`, `objection_handling_quality`, `lead_quality_score`, all 1–5) with an explicit rule that sale outcome, agent performance, and lead quality are independent axes — enforced via required contrast cases.
- Audio-derived feature definitions and realistic ranges (`call_duration_seconds`, `silence_ratio`, `speaking_rate_wpm`, `speech_to_non_speech_ratio`, `agent_talk_ratio`, `average_energy_level`), with the missing-vs-fabricated rule carried over from `CLAUDE.md`.
- Planned distribution for the 24-call RAG corpus (8/8/8 by outcome; objection counts summing to 24) and 8 required contrast cases to keep retrieval grounded in transcript detail rather than superficial metadata.
- Full column-by-column schemas for both files — 26 columns for `historical_sales_calls.csv`, 20 columns for `call_signal_training.csv` (16 features + 4 targets: `predicted_outcome_label`, `risk_level`, `lead_quality_score`, `agent_performance_score`) — each with type, allowed values/range, required/feature-or-target status, description, and example.
- Synthetic generation rules (controlled variation, no exact/near-duplicates, no deterministic single-feature leakage, no agent identity leakage, class balance, realistic noise) and dataset validation rules (uniqueness, required fields, enum/range checks, transcript-label consistency, split-group integrity) for Phase 5C.
- Proposed 70/15/15 train/validation/test split with a leakage-prevention rule: related synthetic variations of the same base profile stay together in one split.
- The Phase 5B/5C execution plan.

No CSV data was generated in this phase — design and schema only, per explicit instruction. Updated `README.md` (documentation index link, phase-focus table) and this file (phase table split into 5A/5B/5C) to reflect the new sub-phase structure.

Phase 5A complete. Confirmed by user. Committed as "Phase 5A: Dataset design". Phase 5B has not been started.

### Phase 5B.0 — Historical call matrix design (complete)

Created `docs/historical_call_matrix.md`: a metadata-only planning matrix assigning all 24 planned RAG-corpus calls (per `docs/dataset_design.md` §12–§13) to a specific agent, customer segment, industry, company size, customer intent, main objection, customer sentiment, sale result, follow-up-needed flag, closing attempt, lead quality, decision-maker presence, and contrast-case role — before any transcript or CSV row is authored. No CSV files or transcripts were generated in this sub-phase.

Verified in the document itself: outcome balance (8 Sale / 8 No Sale / 8 Follow-up Needed), perfect agent balance (6 calls per agent, exactly 2 of each outcome per agent — also satisfying the "no agent with only one outcome" validation rule), objection distribution matching dataset_design.md §12 exactly, and all 8 required contrast cases (§13) mapped to specific call IDs — including Case 7 (CALL_007 vs. CALL_009: same agent, same objection, similar intent, opposite outcome) and Case 8 (CALL_004 vs. CALL_010: same outcome, different objections). `agent_performance_score`, `objection_handling_quality`, `manager_notes`, audio-derived fields, and the transcripts themselves are explicitly deferred to Phase 5B.1, with per-row flags for the two contrast cases (5 and 6) that constrain a specific score direction.

**Phase 5B.0 refinement (same day):** per user review, added a "Matrix Validation Status" checklist section at the end of the document (outcome/agent/objection/segment/industry/intent/sentiment/decision-maker diversity and contrast-case coverage, all verified), refined the CALL_014 (Case 6) wording from "the lead was already highly qualified and closed regardless of Michael's over-talking" to "the opportunity was already exceptionally strong before the conversation began, allowing the deal to close despite weaker sales execution" — separating opportunity quality from agent performance more cleanly — and added an explicit note that the matrix is the design blueprint for the RAG corpus, and every Phase 5B.1 transcript must remain fully consistent with it and with the Ground Truth Rules. No call assignments, outcomes, objections, distributions, or contrast cases were changed — wording and documentation only.

Phase 5B.0 complete. Confirmed by user. Committed as "Phase 5B.0 refinement: finalize historical call matrix". Phase 5B.1 has not been started.

### Phase 5B.1 — Transcript and full CSV-row authoring (complete)

Authored the full historical-call record (transcript, structured fields, audio-derived features, `manager_notes`, Ground Truth checklist) for all 24 calls fixed by the Phase 5B.0 matrix, in five batches: `docs/generated_calls_batch_01.md` (CALL_001–004), `_02.md` (CALL_005–008), `_03.md` (CALL_009–012), `_04.md` (CALL_013–018), `_05.md` (CALL_019–024). No matrix assignment (agent, segment, industry, intent, objection, sentiment, outcome, closing attempt, lead quality, decision-maker presence, contrast-case role) was changed at any point — only the fields the matrix explicitly deferred were authored.

**Mid-phase refinement — Transcript Writing Guidelines (after Batch 1):** the user reviewed Batch 1 and found the prose style too uniform across conversations (repeated acknowledgment templates like "That's fair...", "Understood.", "I'd rather... than...", every customer sounding similarly polished). Added a new **"Transcript Writing Guidelines"** section to `CLAUDE.md` (authentic conversation, dialogue diversity, a list of 8 banned reusable templates, natural spoken language, customer individuality, sales-rep consistency without signature phrases, independent generation per call) — applying from Batch 2 onward; Batch 1 was explicitly not rewritten retroactively. Committed separately as "Phase 5B.1 refinement: transcript writing guidelines".

**CALL_006 revision (mid-Batch 2):** per user feedback, revised CALL_006 in place to add a discovery opening, humanize the technical-vetter customer with grounded asides, give the agent two consultative questions, and soften the ending into a conditional follow-up offer — while leaving metadata, outcome, and all structured-field judgments unchanged. Audio-derived fields (`call_duration_seconds`, `speaking_rate_wpm`, `agent_talk_ratio`) were recomputed from the revised (longer) transcript to stay grounded, and the change was documented transparently in the batch file.

Each batch's self-QA (word/turn counts via `wc`/`grep`, banned-phrase greps, contrast-case verification) caught and fixed real issues before submission — most notably Batch 3, where an early draft of Daniel Cohen's "I'd rather ... than ..." closing line was accidentally reused across three of that batch's four calls. All 8 required contrast cases (`dataset_design.md` §13) were authored and individually verified against specific transcript evidence, including a dedicated line-by-line verification table for Case 6 (CALL_014, the highest-stakes row in the corpus — `Sale` outcome despite `agent_performance_score = 2`) and Case 3 (CALL_023, the mirror case — `Follow-up Needed` caused specifically by weak closing follow-through, not agent execution).

Phase 5B.1 complete. Confirmed by user across all five batches. Committed per-batch as "Phase 5B.1: Batch N historical calls" (Batches 1, 3, 4; Batches 2 and 5 were committed together with Phase 5C, see below, since they had not yet been committed when Phase 5C began). Phase 5C has not been started.

### Phase 5C — Dataset Validation (complete)

Consolidated all 24 authored calls into `data/historical_sales_calls.csv` (26 columns, exact schema and column order from `dataset_design.md` §14 — `company_size`, a matrix-planning-only field, correctly excluded), and built `scripts/validate_historical_dataset.py`: a reusable, independent validator that reads the CSV directly (not the batch markdown source) and checks schema, enums, numeric ranges, corpus-wide distributions (outcome/agent/objection balance, all 8 contrast cases), Ground Truth consistency heuristics, audio-feature internal consistency (recomputed `speaking_rate_wpm` and `agent_talk_ratio` directly from transcript text), mention-count recomputation against a documented keyword list, and transcript-style patterns (banned templates, repeated openings/closings, verbal-tic frequency) — writing `docs/dataset_validation_report.md` and exiting 0 for `READY`/`READY WITH WARNINGS`, non-zero for `NOT READY`.

**Result: READY WITH WARNINGS, 0 errors, 28 warnings.** No schema, Ground Truth, corpus-math, or hard-consistency rule was violated anywhere in the 24-row corpus. The warnings are all reported, not silently fixed, per the fix policy (only objective formatting issues — stray whitespace, boolean casing — are auto-corrected; none were needed, since the CSV was already clean):

- **20 `speaking_rate_wpm` values** are 3–6 wpm higher than an independent recomputation — root-caused to a systematic word-counting artifact from Phase 5B.1 (the hand-computed word counts via `wc -w` counted the literal `Agent:`/`Customer:` speaker-tag token as one word per turn). Reported, not auto-corrected, since redefining and rewriting 20 stored values is a data change, not an indisputable formatting fix.
- **5 mention-count mismatches** (`price_mentions_count` on CALL_003, 014, 017, 018, 023) between the original ad-hoc substring-based hand counts and the script's stricter word-boundary keyword matching — reported, not auto-corrected, for the same reason.
- **Batch 1's banned-phrase content** (CALL_001–004) — confirmed as exactly the pre-existing, documented exception from the Transcript Writing Guidelines refinement above, not a new defect.
- **Two corpus-wide style patterns not previously caught by per-batch review:** 20/24 calls (83%) open the agent's first line with the literal phrase "thanks for," and the filler word "honestly" appears 47 times across 21/24 calls. Neither violates an explicit rule (not on the 8-item banned list), but both are reported as genuine quality signals for any future revision pass.

Phase 5C complete. Committed together with the two previously-uncommitted Phase 5B.1 batches (CALL_005–008, CALL_019–024) as "Phase 5C: validate and freeze historical dataset". Phase 6 has not started.
