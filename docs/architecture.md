# XSight — Architecture

This document describes the end-to-end architecture of XSight in detail: the high-level flow, every component's responsibility and contract, the request-by-request sequence through the pipeline (including the two-stage guardrails split and the confidence-based human-review path), and the deployment topology. The system-wide flow diagram and full request/response JSON schemas are defined in [../CLAUDE.md](../CLAUDE.md); this document expands on them with the reasoning and detail needed to understand *why* the pipeline is shaped the way it is, not just what it contains. The rationale for each technology choice is in [technology_decisions.md](technology_decisions.md).

## 1. High-level architecture

```mermaid
flowchart LR

    A["User / Sales Manager\nuploads sales call audio"]
    --> B["XSight Website Interface\nReact Web Application"]

    B --> C["n8n Workflow\nOrchestration Layer"]

    C --> D1["Pre-Transcription\nFile Validation\nDeterministic checks"]

    D1 --> E["Transcription\nAudio to Text\nTBD — Phase 9"]

    E --> D2["Post-Transcription\nInput Content Guardrails\nNeMo Guardrails + deterministic rules"]

    D2 --> F["Sales Call Understanding\nExtract intent, objection,\nsentiment and call metadata\nGemini via n8n"]

    F --> G["AI Services\nFastAPI Microservices on AWS EC2"]

    G --> H["Sales Call RAG Service\nLangChain + ChromaDB + Llama.cpp"]

    G --> I["Voice / Call Signal Analyser\nPyTorch — transcript + lightweight audio features"]

    G --> J["LangGraph Sales Agent\nReasoning and recommendations"]

    H --> K["XSight Analysis Results"]
    I --> K
    J --> K

    K --> L["Output Guardrails Service\nNeMo Guardrails + deterministic rules"]

    L --> M["Results Displayed in Website\nTranscript, insights, scores,\nsimilar calls, coaching feedback,\nfollow-up recommendation and routing"]

    M --> B

    subgraph DataModels["Data and Local AI Components"]
        N["Historical Sales Calls CSV"]
        O["ChromaDB Vector Store"]
        P["Llama.cpp\nLocal RAG Generation\ninside RAG service"]
        Q["Ollama Assistant\nSidebar only — separate runtime"]
    end

    N --> O
    O --> H
    P --> H
    Q --> B
```

D1 and D2 are two invocations of the same Guardrails service endpoint (`POST /check/input`), not two services — see §3.3.

## 2. Design principles behind the flow

- **Guardrails wrap every LLM-facing boundary.** Input is validated twice (once before transcription exists, once after) and output is validated once before anything reaches the user — no unvalidated text crosses from the user into an LLM prompt, or from an LLM output back to the user.
- **Every AI service is independently callable and independently testable.** The RAG service, Call Signal Analyser, and LangGraph agent each have their own FastAPI endpoint, their own input/output contract, and no direct dependency on each other's internals — n8n and the LangGraph agent are the only components that call more than one of them.
- **Low confidence routes to a human, not a guess.** Whenever the pipeline cannot support a confident answer, the result is explicitly marked `human_review_required` rather than silently returned as if it were certain (see §3.6).
- **Grounding is enforced structurally, not just by instruction.** The RAG service's citation requirement and the output guardrails' citation check are two independent layers — a prompt asking the model to cite sources is not trusted alone.

## 3. Request lifecycle, step by step

This section walks through one full analysis request in the order it actually executes, referencing the n8n node numbers from [CLAUDE.md](../CLAUDE.md#2-n8n-cloud-workflow).

### 3.1 Submission (React → n8n)

The user submits the upload form (audio file, agent name, call date, optional customer/company name, optional notes) from the React app. The form POSTs to the n8n Cloud webhook (node 1), which is the single entry point into the backend — the React app never calls any FastAPI service directly.

### 3.2 Pre-transcription file validation (n8n nodes 2–3)

Before a transcript exists, only the uploaded file and form metadata can be validated. n8n calls the Guardrails service's `POST /check/input` with the file/metadata payload. The service applies deterministic checks only at this stage — an LLM rail has nothing useful to say about whether a file is a valid MIME type or under the size limit:

- audio file exists
- supported MIME type and extension
- file size limit
- optional duration limit
- required metadata present (agent name, call date, etc.)
- submission structure is not malformed or suspicious

An IF node (node 3) branches on the result: fail → respond immediately with a rejection, no further processing; pass → continue to transcription.

### 3.3 Transcription (n8n node 4)

The audio file is sent to the transcription API (provider TBD — Phase 9). Output is a transcript, ideally speaker-tagged (`Agent:`/`Customer:`) if the chosen provider supports diarization — this tagging is what later enables `agent_talk_ratio` in the Call Signal Analyser.

### 3.4 Post-transcription input content guardrails (n8n nodes 5–6)

Now that the transcript exists, n8n calls the *same* `POST /check/input` endpoint again, this time with the transcript text. The service applies NeMo rails plus deterministic checks appropriate to text content:

- transcript not empty or too short
- content is actually a sales call (off-topic rejection)
- offensive content detection
- prompt injection / instruction-override attempts
- optional language validation

The endpoint's behavior is driven entirely by what's in the request payload (file-only vs. transcript-present), not by a flag identifying which orchestration step is calling it — see [technology_decisions.md](technology_decisions.md#guardrails--nemo-guardrails--fastapi--deterministic-custom-validation-rules) for why this was kept as one endpoint. Another IF node (node 6) branches: fail → reject; pass → continue.

### 3.5 Information extraction (n8n node 7)

Gemini (via an n8n node) reads the validated transcript and extracts structured fields: customer intent, main objection, customer sentiment, closing attempt, and other fields the downstream services need. This is the first LLM call in the pipeline that sees the transcript.

### 3.6 AI services (n8n nodes 8–10)

n8n calls the three FastAPI microservices — order between them is not strictly sequential where there's no data dependency, but the Call Signal Analyser and RAG service outputs both feed the LangGraph agent, so in practice RAG and signal analysis run first:

- **RAG service** (`POST /query`, node 8) — retrieves similar historical calls from ChromaDB, cited by `call_id`.
- **Call Signal Analyser** (`POST /analyse-call`, node 9) — scores the call (predicted outcome, lead quality, agent performance, risk level) from transcript, structured-extraction, and lightweight audio-derived features, and returns a `confidence` value.
- **LangGraph agent** (`POST /agent/run`, node 10) — takes the transcript, metadata, and the RAG/signal-analyser outputs as input, and runs Planner → Tool Execution → Synthesizer to produce coaching feedback and a recommended next action, with explicit `reasoning_steps`.

### 3.7 Final analysis generation (n8n node 11)

Gemini assembles the outputs of the three AI services plus the extracted fields into the full result shape defined by the [final output JSON schema](../CLAUDE.md#final-output-json-schema-contract-between-backend-and-react-frontend).

### 3.8 Output guardrails (n8n node 12)

The assembled result is sent to `POST /check/output`, which checks for invented CRM facts, unsupported business conclusions, fake legal/financial promises, overconfident recommendations, invented call details, and — critically — that every claim about a historical call carries a `call_id` citation.

### 3.9 Confidence routing and human review (n8n node 13)

An IF node inspects the Call Signal Analyser's `confidence` value (carried through from step 3.6) together with the output guardrails result:

- `confidence < 0.65` → route to `human_review_required`, regardless of what the guardrails said, per the confidence routing rule in [CLAUDE.md](../CLAUDE.md#2-n8n-cloud-workflow).
- output guardrails flagged → route to `flagged` or `human_review_required` depending on severity.
- otherwise → `pass`, return the result directly.

This is the only branching point in the pipeline that can override an otherwise-passing result — it exists specifically so a technically-valid-but-uncertain analysis is never presented to the user as if it were reliable.

### 3.10 Response (n8n → React)

n8n responds to the original webhook call with the final JSON payload (node 14). React renders it on the Results Page; `guardrail_status` in the payload (`pass | flagged | human_review_required`) drives whether the UI shows the result normally or with a review banner.

## 4. Component responsibility matrix

| Component | Location | Endpoint(s) | Called by | Depends on |
|---|---|---|---|---|
| React app | `frontend/` | — (calls n8n webhook) | User | n8n webhook |
| n8n workflow | `n8n/` | Webhook trigger | React | All services below |
| Guardrails service | `services/guardrails_service` | `POST /check/input`, `POST /check/output` | n8n | NeMo Guardrails |
| Transcription | external (TBD) | provider-specific | n8n | — |
| RAG service | `services/rag_service` | `POST /query` | n8n, LangGraph agent | ChromaDB, Llama.cpp, historical calls CSV |
| Call Signal Analyser | `services/call_signal_analyser` | `POST /analyse-call` | n8n, LangGraph agent | trained PyTorch model |
| LangGraph agent | `services/langgraph_agent` | `POST /agent/run` | n8n | RAG service, Call Signal Analyser |
| Ollama assistant | external runtime | local HTTP API | React sidebar only | — (independent of Llama.cpp) |

## 5. Data flow

- **Historical Sales Calls CSV** (`data/historical_sales_calls.csv`) is the single source of truth for both: the RAG corpus (ingested into ChromaDB with HuggingFace embeddings) and the Call Signal Analyser's training data (loaded via pandas for PyTorch training, offline). See [technology_decisions.md](technology_decisions.md#dataset-design-two-separate-datasets-not-one) for why these are treated as two logically separate datasets sourced from the same file.
- **ChromaDB** is populated once (offline ingestion step) from the CSV's RAG-corpus rows and queried at request time by the RAG service — it is not written to during a normal analysis request.
- **Llama.cpp** runs only inside the RAG service process, generating the grounded, citation-constrained `insight` text from the retrieved calls.
- **Ollama** runs as a fully separate process, serving only the React sidebar assistant; it never touches the RAG service, the historical calls data, or ChromaDB directly.

## 6. Deployment topology

### Local development (Phases 1–15)

All four FastAPI services, plus ChromaDB (embedded) and the Llama.cpp/Ollama runtimes, run locally — via Docker Compose from Phase 7 onward. n8n Cloud cannot reach `localhost`, so local services are exposed to it through ngrok or a Cloudflare Tunnel, or n8n itself is run locally in Docker Compose during early phases (decision documented at Phase 9, per [CLAUDE.md](../CLAUDE.md#n8n-and-local-services-connectivity-note)). The React frontend does not exist yet during this period; every service is exercised via curl, Postman, or direct n8n webhook calls.

### Production (Phase 19+)

The same Docker Compose configuration is deployed to a single AWS EC2 instance, so the local and production environments match as closely as possible. n8n Cloud calls the EC2-hosted services directly (no tunnel needed once there's a public endpoint). React is built and served separately (static hosting or the same instance, decided at Phase 19).

## 7. Error and rejection paths

| Failure point | Trigger | Result |
|---|---|---|
| Pre-transcription file validation fails | invalid file type, oversized file, missing metadata | immediate rejection, no transcription attempted |
| Post-transcription content guardrails fail | off-topic, offensive, empty transcript, prompt injection | rejection after transcription, no AI services called |
| Call Signal Analyser confidence < 0.65 | model uncertain | `human_review_required`, result still returned but flagged |
| Output guardrails flag the result | invented facts, missing citations, overconfident claims | `flagged` or `human_review_required` depending on severity |
| Any FastAPI service unreachable/erroring | infra issue | n8n node fails; webhook returns an error response (exact retry/error-handling behavior finalized at Phase 10) |

## 8. Open items carried from technology decisions

- Exact transcription provider (Phase 9) — affects whether diarization is available, which in turn affects whether `agent_talk_ratio` can be computed.
- n8n-to-localhost connectivity approach for development (Phase 9).
- Exact lightweight audio library and audio-file input contract for the Call Signal Analyser (Phase 13).
