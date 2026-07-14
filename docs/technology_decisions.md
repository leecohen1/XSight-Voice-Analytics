# XSight — Technology Decisions

This document records the rationale behind each technology choice in the XSight stack: what was chosen, what alternatives were considered, and why. The final chosen stack itself is defined in [../CLAUDE.md](../CLAUDE.md); this document explains the reasoning behind it.

## Guiding constraints

A few constraints shaped every decision below:

- **Backend-first, local-service development.** FastAPI services, Docker containers, ChromaDB, local models, and service endpoints are developed and tested locally first, using curl and Postman, before any frontend integration exists. n8n Cloud is introduced once webhook orchestration begins (Phase 9–10) — n8n itself is a cloud service from the start, so "local-first" describes the services being orchestrated, not the orchestrator. The React frontend is intentionally deferred until the backend and n8n workflow are stable (Phase 16+), and AWS EC2 deployment happens only after local service validation (Phase 19).
- **Grounded, non-hallucinated output.** XSight makes claims about historical sales calls and gives coaching advice; the stack had to support retrieval-grounded generation with citations and explicit guardrails, not open-ended generation.
- **Breadth of AI engineering techniques.** As a final project, the stack is deliberately composed of distinct, complementary techniques (RAG, a trained classifier, an agentic graph, guardrails, orchestration) rather than one monolithic LLM call — each component should be independently demonstrable and testable.
- **Two clearly separated local LLM runtimes.** The project intentionally uses both Llama.cpp and Ollama for different purposes (see below), to keep the RAG generation path and the interactive assistant path architecturally independent.

---

## Frontend — React

**Alternatives considered:** Vue, Streamlit, plain HTML/JS.

**Why chosen:** React is the most common production choice for a dashboard-style results UI with multiple views (upload, results, analytics, assistant sidebar) and gives full control over layout and state. Streamlit was considered for speed of development but rejected because the results page needs custom, structured layouts (scored fields, cited similar calls, follow-up email preview) that go beyond Streamlit's widget model, and because the project explicitly separates backend-only phases from frontend work — a full framework keeps that separation clean.

**Trade-off accepted:** More setup and phase time cost (frontend is deliberately deferred to Phase 16+) in exchange for a UI that can properly present a rich, structured analysis result.

## Orchestration — n8n Cloud

**Alternatives considered:** Custom orchestration in a FastAPI backend, LangGraph as the sole orchestrator, Airflow.

**Why chosen:** n8n provides a visual, inspectable workflow (webhook → guardrails → transcription → extraction → services → guardrails → response) that is easy to demo, debug node-by-node, and modify without redeploying code — valuable both for iterative development and for the live demo. It also cleanly separates orchestration/business-flow concerns from the AI reasoning that lives in LangGraph.

**Trade-off accepted:** n8n Cloud cannot reach `localhost` directly, requiring a tunnel (ngrok / Cloudflare Tunnel) or a local n8n instance during early phases — this is addressed explicitly in Phase 9.

## Transcription — TBD (Phase 9)

Not yet decided. Will be evaluated at Phase 9 against:

- English transcription accuracy
- optional Hebrew support
- speaker diarization (needed for `Agent:`/`Customer:` tagging used by the Call Signal Analyser)
- speaker labels and timestamps
- supported audio formats
- maximum file size and duration
- latency
- cost per minute
- n8n Cloud integration complexity
- reliability for a live demo

## n8n LLM — Gemini

**Alternatives considered:** OpenAI GPT models, Anthropic Claude, a locally hosted model via Ollama.

**Why chosen:** Gemini offers a generous free/low-cost tier suitable for a student project with repeated iteration during prompt engineering (minimum 5 iterations per surface, per the prompt engineering log requirement), and integrates natively as an n8n node, avoiding custom HTTP request boilerplate for the two LLM-driven nodes (Information Extractor, Final Analysis Generation).

**Trade-off accepted:** Ties two orchestration-level prompting surfaces to a specific vendor API; mitigated by keeping those prompts isolated in n8n nodes rather than embedded in service code, so the model could be swapped later.

## Guardrails — NeMo Guardrails + FastAPI + deterministic custom validation rules

**Final decision:** NeMo Guardrails + FastAPI + deterministic custom validation rules. This is a three-part combination, not NeMo alone.

**Alternatives considered:** Pure prompt-based self-checking inside the Gemini calls, a fully custom rule engine with no LLM rails at all, Guardrails AI (the `guardrails-ai` library).

**Why chosen:** NeMo Guardrails and deterministic rules are given clearly separated responsibilities:
- **NeMo Guardrails** handles topic restrictions, unsafe content, prompt injection, jailbreak attempts, and other LLM-oriented input/output policies — the class of checks that need semantic judgment, not a fixed rule.
- **Deterministic custom rules** handle checks that don't need an LLM at all: empty input, transcript length, invalid schemas, unsupported file formats, required fields, and missing `call_id` citations. Running these as plain code is faster, free, and fully deterministic — there's no reason to pay an LLM rail to check whether a string is non-empty.
- **FastAPI** exposes both as one independently testable service, with two endpoints: `POST /check/input` and `POST /check/output`.

**Corrected input validation order:** Input validation is not a single step before transcription — it is split into two stages, because the data available differs before and after transcription:

1. **Pre-transcription file validation** (deterministic only — no transcript exists yet): file exists, supported MIME type/extension, file size limit, optional duration limit, required metadata validation, invalid/suspicious submission structure.
2. **Post-transcription input content guardrails** (NeMo + deterministic — the transcript text is now available): transcript not empty/too short, content is a sales call, off-topic detection, offensive content detection, prompt injection/instruction-override detection, optional language validation.

Pipeline order: `Webhook → Pre-transcription file validation → Transcription → Post-transcription input content guardrails → Information extraction → AI services → Final analysis generation → Output guardrails → Response.`

The Guardrails service exposes a single `POST /check/input` endpoint that is invoked at two different stages of the processing pipeline. During the first invocation (before transcription), the endpoint validates the uploaded audio file and submission metadata, including file type, file size, duration limits, required metadata, and submission integrity. During the second invocation (after transcription), the same endpoint validates the transcript content, including topic relevance, transcript quality, offensive content, prompt injection attempts, and other semantic checks. The validation logic is determined by the request payload and the data available at each stage, rather than by separate endpoints or by orchestration-specific logic. This keeps the external API simple while allowing the validation logic for each stage to evolve independently.

**Trade-off accepted:** An additional service and runtime to maintain, plus the extra complexity of stage-aware input validation instead of one flat check; accepted because guardrails-as-a-separate-service is a deliberate architectural requirement, and because pretending file-level and content-level validation are the same step would mean either skipping file checks (unsafe) or requiring a transcript that doesn't exist yet (impossible).

## RAG — LangChain + ChromaDB + HuggingFace embeddings + Llama.cpp

**Alternatives considered:** LlamaIndex instead of LangChain; Pinecone/Weaviate instead of ChromaDB; OpenAI embeddings instead of HuggingFace; calling Gemini instead of a local Llama.cpp model for RAG generation.

**Why chosen:**
- **LangChain** has mature retriever/chain abstractions and is the most widely documented option for wiring a retriever to a citation-constrained generation step.
- **ChromaDB** is embedded, file-based, and requires no external service or account — appropriate for backend-first local development and for a dataset of only 20–30 detailed historical calls.
- **HuggingFace embeddings (`sentence-transformers/all-MiniLM-L6-v2`)** run locally, are free, and are small/fast enough for the dataset size, avoiding an external embeddings API dependency and its cost/rate limits.
- **Llama.cpp** provides local, offline generation for the RAG service specifically, keeping the RAG service self-contained and independent of both the n8n/Gemini path and the Ollama assistant path — important since the RAG output must be strictly grounded and citation-checked, which is easier to control with a dedicated local model and explicit prompt constraints than through an external API shared with other orchestration prompts.

**Trade-off accepted:** Running a local GGUF model via Llama.cpp adds setup complexity (model download, `models/` artifact management, hardware dependency) compared to just calling an external API; accepted because it keeps RAG generation fully local and demonstrates local LLM inference as a distinct skill.

## Voice / Call Signal Analyser — PyTorch, transcript + structured + lightweight audio features

**Alternatives considered:** scikit-learn classifier, full librosa-based deep acoustic feature analysis on the raw audio, a transcript-only rules-based scorer with no trained model and no audio input at all.

**Why chosen:** PyTorch was chosen specifically to include a trained classifier as part of the project (a requirement to demonstrate model training, not only prompting/retrieval). The classifier is a feature-based model over an engineered feature vector — not a raw-audio deep learning model; it does not consume waveforms or spectrograms, and audio preprocessing stays lightweight rather than a full acoustic feature-extraction pipeline. The final feature set has three sources:
- **Transcript-derived and structured-extraction features:** word count, question count, price mention count, competitor mention count, customer intent, main objection, customer sentiment, closing attempt, and speaker-tagged agent talk ratio (only when the transcript is diarized with `Agent:`/`Customer:` tags).
- **Lightweight audio-derived features:** call duration, silence ratio, speaking rate, speech-to-non-speech ratio, and optionally average energy level — computed directly from the audio file with lightweight signal analysis (e.g. duration and basic energy/silence detection), not full acoustic feature extraction.

Including real audio-derived features (rather than treating the analyser as transcript-only) means signals like `silence_ratio` and `call_duration_seconds` reflect what was actually measured in the recording, instead of being approximated from word count alone.

**Trade-off accepted:** The service now depends on having access to the audio file for some features, not the transcript alone, which is a step up in complexity from a pure text-in service; the exact lightweight audio library and the input contract for supplying the audio file are finalized during implementation (Phase 13). Any feature that cannot be computed for a given call — no diarization tags, or the audio file unavailable — must be explicitly marked missing/unknown in the request/response, never fabricated or silently defaulted. In particular, `silence_ratio` must never be silently set to `0.0` when it was not actually measured; that would misrepresent an unmeasured signal as a real "no silence" reading.

## Agent — LangGraph

**Alternatives considered:** A single large synthesis prompt in n8n/Gemini, LangChain's older `AgentExecutor`, a custom hand-rolled state machine.

**Why chosen:** LangGraph gives an explicit, inspectable graph (Planner → Tool Execution → Synthesizer) with typed state passed between nodes, which produces the `reasoning_steps` and `tools_used` fields required by the output contract almost for free, and makes the reasoning process demoable and debuggable node-by-node — unlike a single opaque LLM call.

**Trade-off accepted:** More upfront structure than a single prompt; accepted because explicit reasoning steps are a specific requirement of the final output schema and a specific technique the project is meant to demonstrate.

## Local Assistant — Ollama (separate from Llama.cpp)

**Alternatives considered:** Reusing the same Llama.cpp runtime for both RAG generation and the sidebar assistant; calling Gemini for the assistant instead of a local model.

**Final distinction:** Llama.cpp is used *only* inside the RAG service, for grounded, citation-constrained generation over retrieved historical calls. Ollama is used *only* for the separate conversational sales assistant in the React application. Neither runtime serves both purposes.

**Why chosen:** Ollama is optimized for interactive, conversational local inference with simple model management (`ollama pull`, `ollama run`) and a stable local HTTP API, which fits a chat-style sidebar assistant well. Keeping it as a service fully separate from Llama.cpp gives:
- **Prompt isolation** — the assistant's conversational system prompt and the RAG service's strict citation/grounding instructions never live in the same context or risk being concatenated.
- **State isolation** — the assistant can hold multi-turn conversation state; the RAG service stays stateless per query.
- **Independent testing** — each service can be evaluated against its own benchmark (grounding/citation accuracy for RAG, helpfulness/tone for the assistant) without the other's behavior as a confound.
- **Different validation rules** — RAG output goes through the strict output guardrails (citation checks, no invented facts); the assistant is a lower-stakes conversational surface with different rules.
- **Separate resource control** — each runtime can be sized, started, and monitored independently.
- **Clearer failure boundaries** — if one runtime crashes or is misconfigured, it does not take down the other.

Running them as separate services makes these properties structural rather than incidental — but the separation itself is an enabler for isolation, not a guarantee of it. Prompt or behavior leakage is ultimately prevented by keeping the prompts, validation rules, and code paths of the two services separate, not by the process boundary alone; if the same prompts or validation logic were shared or copy-pasted between the two services, running them as separate runtimes would not by itself stop behavior from one leaking into the other.

**Trade-off accepted:** Two local LLM runtimes to install and run instead of one; accepted deliberately per the architectural requirement that these stay independent.

## Data — CSV + ChromaDB

**Alternatives considered:** A relational database (SQLite/Postgres) for the historical calls dataset.

**Why chosen:** A CSV is sufficient for a static, project-scale historical dataset, is trivial to version, inspect, and edit by hand, and loads directly into both the PyTorch training pipeline (via pandas) and the ChromaDB ingestion step for RAG — no database server needed for a dataset this size.

**Trade-off accepted:** No concurrent-write support or query language; acceptable since the dataset is read-only at runtime and only regenerated offline.

### Dataset design: two separate datasets, not one

The RAG corpus and the classifier training dataset serve different purposes and are deliberately kept separate — the project does not contain 150–300 complete transcripts.

- **RAG corpus:** at least 20 detailed historical sales call transcripts (up to 30), each with rich metadata. Used for ChromaDB retrieval and citation-based generation — retrieval quality depends on having real, varied, well-written transcripts, not volume.
- **Classifier dataset:** a larger structured dataset for PyTorch training — approximately 150–300 synthetic or adapted feature rows (features and labels only, no full transcript) is acceptable. Rows are generated through controlled variations (systematically varied feature combinations and outcomes) rather than duplicated boilerplate, and labels must remain logically consistent with their features. The dataset is split into train/validation/test sets, with no duplicate-row leakage across splits — a row generated as a variation of another must not appear in more than one split.

## Deployment — Docker locally, then AWS EC2

**Alternatives considered:** Deploying directly to a managed platform (e.g. Render, Railway) or serverless functions per service.

**Why chosen:** Docker Compose lets all four FastAPI services run together locally with consistent networking during Phases 7–15, matching how they will later run in production. EC2 was chosen over serverless because some services (RAG with Llama.cpp, the PyTorch model) benefit from a persistent process and loaded-in-memory models rather than cold-start-per-request billing, and because a single EC2 instance running the same Compose setup used locally minimizes the gap between the local and deployed environments.

**Trade-off accepted:** More manual ops work than a managed platform (no auto-scaling, manual instance management); acceptable given the project's fixed, demo-oriented scope rather than production traffic.

---

## Summary table

| Layer | Chosen | Key alternative(s) considered | Primary reason |
|---|---|---|---|
| Frontend | React | Streamlit, Vue | Full control over structured results UI |
| Orchestration | n8n Cloud | Custom FastAPI orchestration, Airflow | Visual, inspectable, demo-friendly workflow |
| Transcription | TBD (Phase 9) | — | Decision deferred pending accuracy/diarization/cost evaluation |
| n8n LLM | Gemini | GPT, Claude | Low-cost iteration, native n8n integration |
| Guardrails | NeMo Guardrails + FastAPI + deterministic rules | Guardrails AI, prompt-only self-checking | NeMo for semantic/LLM checks, deterministic rules for fixed checks, staged around transcription |
| RAG | LangChain + ChromaDB + HuggingFace + Llama.cpp | LlamaIndex, Pinecone, OpenAI embeddings | Self-contained, free, grounded generation |
| Call signal analysis | PyTorch (transcript + structured + lightweight audio features) | scikit-learn, full librosa acoustic pipeline, transcript-only heuristics | Trained feature-based classifier combining real (not fabricated) signals from text and audio |
| Agent | LangGraph | Single Gemini prompt, LangChain AgentExecutor | Explicit, inspectable reasoning graph |
| Local assistant | Ollama | Reuse Llama.cpp, call Gemini | Simple conversational runtime, kept independent from RAG generation |
| Data | CSV + ChromaDB | SQLite/Postgres | Sufficient for dataset size, trivial to version and inspect |
| Deployment | Docker → AWS EC2 | Managed PaaS, serverless | Persistent processes for loaded models, local/prod parity |
