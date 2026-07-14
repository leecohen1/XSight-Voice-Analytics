# XSight — Technology Decisions

This document records the rationale behind each technology choice in the XSight stack: what was chosen, what alternatives were considered, and why. The final chosen stack itself is defined in [../CLAUDE.md](../CLAUDE.md); this document explains the reasoning behind it.

## Guiding constraints

A few constraints shaped every decision below:

- **Local-first development.** Phases 1–15 run entirely on a local machine, tested via curl/Postman/n8n webhooks, before any cloud deployment or frontend exists. Tooling had to work well offline and without paid infrastructure during development.
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

Not yet decided. Will be evaluated at Phase 9 against: English accuracy, speaker diarization support (needed for `Agent:`/`Customer:` tagging used by the Call Signal Analyser), API cost, and latency.

## n8n LLM — Gemini

**Alternatives considered:** OpenAI GPT models, Anthropic Claude, a locally hosted model via Ollama.

**Why chosen:** Gemini offers a generous free/low-cost tier suitable for a student project with repeated iteration during prompt engineering (minimum 5 iterations per surface, per the prompt engineering log requirement), and integrates natively as an n8n node, avoiding custom HTTP request boilerplate for the two LLM-driven nodes (Information Extractor, Final Analysis Generation).

**Trade-off accepted:** Ties two orchestration-level prompting surfaces to a specific vendor API; mitigated by keeping those prompts isolated in n8n nodes rather than embedded in service code, so the model could be swapped later.

## Guardrails — NeMo Guardrails + FastAPI

**Alternatives considered:** Pure prompt-based self-checking inside the Gemini calls, a fully custom rule engine, Guardrails AI (the `guardrails-ai` library).

**Why chosen:** NeMo Guardrails provides a structured way to define input/output rails (topic restriction, jailbreak/injection detection) declaratively, separate from the main reasoning prompts, which matches the requirement for a dedicated, independently testable guardrails service with its own input/output contract. Custom rule-based validation supplements it where rail-based detection is insufficient (e.g. deterministic checks like "transcript too short" or "missing `call_id` citation").

**Trade-off accepted:** An additional service and runtime to maintain; accepted because guardrails-as-a-separate-service is also a deliberate architectural requirement (input guardrails must run before transcription, output guardrails before results are returned).

## RAG — LangChain + ChromaDB + HuggingFace embeddings + Llama.cpp

**Alternatives considered:** LlamaIndex instead of LangChain; Pinecone/Weaviate instead of ChromaDB; OpenAI embeddings instead of HuggingFace; calling Gemini instead of a local Llama.cpp model for RAG generation.

**Why chosen:**
- **LangChain** has mature retriever/chain abstractions and is the most widely documented option for wiring a retriever to a citation-constrained generation step.
- **ChromaDB** is embedded, file-based, and requires no external service or account — appropriate for local-first development and for a dataset of only 20–30 detailed historical calls.
- **HuggingFace embeddings (`sentence-transformers/all-MiniLM-L6-v2`)** run locally, are free, and are small/fast enough for the dataset size, avoiding an external embeddings API dependency and its cost/rate limits.
- **Llama.cpp** provides local, offline generation for the RAG service specifically, keeping the RAG service self-contained and independent of both the n8n/Gemini path and the Ollama assistant path — important since the RAG output must be strictly grounded and citation-checked, which is easier to control with a dedicated local model and explicit prompt constraints than through an external API shared with other orchestration prompts.

**Trade-off accepted:** Running a local GGUF model via Llama.cpp adds setup complexity (model download, `models/` artifact management, hardware dependency) compared to just calling an external API; accepted because it keeps RAG generation fully local and demonstrates local LLM inference as a distinct skill.

## Voice / Call Signal Analysis — PyTorch (transcript-derived features)

**Alternatives considered:** scikit-learn classifier, librosa-based acoustic feature analysis on the raw audio, a rules-only heuristic scorer with no trained model.

**Why chosen:** PyTorch was chosen specifically to include a trained neural classifier as part of the project (course requirement to demonstrate model training, not only prompting/retrieval). Features are deliberately derived from the transcript only (word count, speaker-tagged talk ratio, speaking rate, keyword counts) rather than from raw audio — this avoids a librosa/audio-signal-processing dependency and keeps the service consistent with the rest of the pipeline, which operates on text after transcription, not on audio directly.

**Trade-off accepted:** Some real acoustic signals (tone, pauses, actual silence) are not observable from text alone; `silence_ratio` is explicitly set to `0.0` with a documented limitation rather than estimated, to avoid fabricating a signal the system cannot actually measure.

## Agent — LangGraph

**Alternatives considered:** A single large synthesis prompt in n8n/Gemini, LangChain's older `AgentExecutor`, a custom hand-rolled state machine.

**Why chosen:** LangGraph gives an explicit, inspectable graph (Planner → Tool Execution → Synthesizer) with typed state passed between nodes, which produces the `reasoning_steps` and `tools_used` fields required by the output contract almost for free, and makes the reasoning process demoable and debuggable node-by-node — unlike a single opaque LLM call.

**Trade-off accepted:** More upfront structure than a single prompt; accepted because explicit reasoning steps are a specific requirement of the final output schema and a specific technique the project is meant to demonstrate.

## Local Assistant — Ollama (separate from Llama.cpp)

**Alternatives considered:** Reusing the same Llama.cpp runtime for both RAG generation and the sidebar assistant; calling Gemini for the assistant instead of a local model.

**Why chosen:** Ollama is optimized for interactive, conversational local inference with simple model management (`ollama pull`, `ollama run`) and a stable local HTTP API, which fits a chat-style sidebar assistant well. It is kept as a runtime fully separate from Llama.cpp (which only serves the RAG service) so the two local-inference concerns — grounded citation-constrained retrieval generation vs. free-form conversational assistance — do not share state, prompts, or failure modes. Merging them would risk the assistant's more relaxed conversational behavior leaking into the strictly-grounded RAG generation path, or vice versa.

**Trade-off accepted:** Two local LLM runtimes to install and run instead of one; accepted deliberately per the architectural requirement that these stay independent.

## Data — CSV + ChromaDB

**Alternatives considered:** A relational database (SQLite/Postgres) for the historical calls dataset.

**Why chosen:** A CSV is sufficient for a static, project-scale historical dataset (20–30 detailed calls + 150–300 synthetic rows), is trivial to version, inspect, and edit by hand, and loads directly into both the PyTorch training pipeline (via pandas) and the ChromaDB ingestion step for RAG — no database server needed for a dataset this size.

**Trade-off accepted:** No concurrent-write support or query language; acceptable since the dataset is read-only at runtime and only regenerated offline.

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
| Guardrails | NeMo Guardrails + FastAPI | Guardrails AI, prompt-only self-checking | Declarative rails as an independent, testable service |
| RAG | LangChain + ChromaDB + HuggingFace + Llama.cpp | LlamaIndex, Pinecone, OpenAI embeddings | Local-first, free, self-contained, grounded generation |
| Call signal analysis | PyTorch (transcript features) | scikit-learn, librosa audio features | Demonstrates trained-model skill without audio dependency |
| Agent | LangGraph | Single Gemini prompt, LangChain AgentExecutor | Explicit, inspectable reasoning graph |
| Local assistant | Ollama | Reuse Llama.cpp, call Gemini | Simple conversational runtime, kept independent from RAG generation |
| Data | CSV + ChromaDB | SQLite/Postgres | Sufficient for dataset size, trivial to version and inspect |
| Deployment | Docker → AWS EC2 | Managed PaaS, serverless | Persistent processes for loaded models, local/prod parity |
