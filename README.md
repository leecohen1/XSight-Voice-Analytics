# XSight — AI Sales Call Analytics System

XSight is a voice-based sales call analytics system. A sales manager or team leader uploads a recorded sales call audio file, and the system transcribes it, analyzes the sales conversation, extracts structured insights, compares the call to similar historical sales calls, predicts sales signals, and returns practical coaching and follow-up recommendations — all displayed in a web dashboard.

This is a full rebuild of XSight from scratch, with a new architecture and a new technology stack. It is not related to any previous version of this project (the earlier version used Flask, Amazon Bedrock Agent, Bedrock Knowledge Base, S3, and Action Groups — none of that carries over).

## Status

Under active development. Built incrementally in 20 phases, one at a time, with explicit approval required before moving to the next — see [docs/PROGRESS.md](docs/PROGRESS.md) for current progress and open decisions.

## Why XSight

Sales managers listen to or read call transcripts to understand what happened, but doing this manually for every call does not scale, and it is hard to compare a call to relevant historical precedent or to give consistent, evidence-based coaching. XSight automates that analysis: it grounds its insights in retrieved historical calls (with citations), scores the call on measurable signals, and produces actionable coaching and follow-up output — while flagging low-confidence results for human review instead of guessing.

## Main users

- **Sales managers** — want to know which calls need attention and why, across their whole team.
- **Sales team leaders** — want comparable, consistent coaching feedback to give agents.
- **Sales agents** — want concrete, specific feedback on a call they just had.
- **Sales operations teams** — want structured, queryable data on call outcomes, objections, and risk for reporting and process improvement.

## Main questions the system answers

- Why did the call succeed or fail?
- What was the customer intent?
- What objections appeared?
- What was the customer sentiment?
- How well did the agent handle objections?
- Was there a missed opportunity?
- Is follow-up needed?
- What coaching feedback should be given?
- Which similar historical calls help explain this result?

## What you get back

For every analyzed call, XSight returns a structured result containing: the transcript, a call summary, customer intent, main objection, customer sentiment, call outcome, an agent performance score (1–5), a lead quality score (1–5), similar historical calls (each cited by `call_id`), coaching feedback, a recommended next action, a suggested follow-up email, a routing category, a confidence level, a risk level, detected signals, known limitations, and a guardrail status.

<details>
<summary>Example output (abridged)</summary>

```json
{
  "call_summary": "Customer showed strong interest but raised a price objection near the end; agent did not attempt to close.",
  "customer_intent": "Evaluating options, budget-conscious",
  "main_objection": "price",
  "customer_sentiment": "neutral",
  "call_outcome": "Follow-up Needed",
  "agent_performance_score": 3,
  "lead_quality_score": 4,
  "similar_calls": [
    {
      "call_id": "CALL_003",
      "agent_name": "Daniel Cohen",
      "sale_result": "Sale",
      "main_objection": "price",
      "similarity_score": 0.89,
      "reason": "Similar price objection with high customer interest."
    }
  ],
  "coaching_feedback": ["Attempt a trial close after addressing the price objection."],
  "recommended_next_action": "Send pricing breakdown and schedule a follow-up call within 3 days.",
  "confidence": 0.86,
  "risk_level": "Medium",
  "guardrail_status": "pass"
}
```

See [CLAUDE.md](CLAUDE.md) for the full JSON schema.
</details>

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Orchestration | n8n Cloud |
| Transcription | External API (TBD — Phase 9) |
| LLM (via n8n) | Gemini — Information Extractor + Final Analysis LLM Chain |
| Guardrails | NeMo Guardrails + FastAPI |
| RAG | LangChain + ChromaDB + HuggingFace embeddings + Llama.cpp |
| Call signal analysis | PyTorch (transcript + structured + lightweight audio features) |
| Agent reasoning | LangGraph + FastAPI |
| Local assistant | Ollama |
| Data | Two CSV files (RAG corpus + classifier training) + ChromaDB |
| Deployment | Docker (local) → AWS EC2 |

Rationale for these choices is documented in `docs/technology_decisions.md` (Phase 3).

## System components

- **React web application** — upload form, results page, analytics dashboard, and an Ollama-powered assistant sidebar. Built last (Phase 16+).
- **n8n Cloud workflow** — the central orchestrator. Calls every AI component directly: guardrails (both stages), transcription, Gemini extraction, the RAG Service and Call Signal Analyser (in parallel), the LangGraph agent, and a second Gemini call (Final Analysis LLM Chain) that assembles the complete result.
- **Sales Call RAG Service** (`services/rag_service`) — retrieves similar historical calls from ChromaDB with cited, grounded insights. Called directly by n8n, in parallel with the Call Signal Analyser.
- **Voice / Call Signal Analyser** (`services/call_signal_analyser`) — PyTorch classifier producing outcome prediction, lead quality, agent performance, and risk scoring from transcript, structured-extraction, and lightweight audio-derived features (it preprocesses the audio file itself). Called directly by n8n, in parallel with the RAG Service.
- **LangGraph Sales Agent** (`services/langgraph_agent`) — a multi-step reasoning layer, called by n8n after the RAG Service and Call Signal Analyser both return. Reasons over their results (evidence-conflict detection, coaching points, recommended action) but does not call other services and does not produce the final report — that's the Gemini Final Analysis Chain's job.
- **Guardrails Service** (`services/guardrails_service`) — NeMo Guardrails + deterministic input/output validation (off-topic content, prompt injection, invented facts, missing citations, etc.).

Full endpoint contracts, request/response schemas, and the architecture diagram are in [CLAUDE.md](CLAUDE.md).

## Architecture overview

```
User uploads audio → React → n8n Cloud → Pre-Transcription File Validation → Transcription
  → Post-Transcription Input Guardrails → Gemini Information Extractor (n8n)
  → n8n calls RAG Service + Call Signal Analyser in parallel
  → LangGraph agent (multi-step reasoning over both results)
  → Gemini Final Analysis LLM Chain (assembles the complete result)
  → Output Guardrails → Confidence & Category Routing → Results shown in React
```

n8n is the central orchestrator and calls every AI component directly — the RAG Service, Call Signal Analyser, LangGraph agent, and both Gemini calls. No AI component calls another. A confidence threshold of 0.65 (plus evidence-conflict and guardrail checks) gates the pipeline: results that don't clear it are routed to `human_review_required` instead of being returned automatically. See [docs/architecture.md](docs/architecture.md) for the full Mermaid diagram and component-level detail.

## Repository structure

```
xsight-ai-sales-call-analytics/
├── CLAUDE.md                  ← full project specification
├── frontend/                  ← React web application (Phase 16+)
├── n8n/                       ← n8n workflow exports and documentation
├── services/
│   ├── rag_service/           ← Sales Call RAG Service
│   ├── call_signal_analyser/  ← Voice / Call Signal Analyser
│   ├── guardrails_service/    ← NeMo Guardrails Service
│   └── langgraph_agent/       ← LangGraph Sales Agent
├── data/                      ← historical_sales_calls.csv (RAG) + call_signal_training.csv (classifier)
├── models/                    ← trained model artifacts (not committed)
├── docs/                      ← project documentation
├── demo/                      ← demo assets and script
├── docker-compose.yml
└── .gitignore
```

## Documentation index

| Document | Purpose |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Full project specification: architecture, schemas, phase plan — source of truth |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Phase completion status and open decisions |
| [docs/technology_decisions.md](docs/technology_decisions.md) | Rationale for each technology choice |
| [docs/architecture.md](docs/architecture.md) | Detailed architecture, request lifecycle, deployment topology |
| `docs/prompt_engineering_log.md` | Prompt iteration log across all prompting surfaces (Phase 20) |

## Development approach

The system is built in 20 phases, one at a time, with explicit approval required before moving to the next phase. The React frontend is built last (Phase 16 onwards); all backend services are tested via curl, Postman, and direct n8n webhook calls during Phases 1–15.

| Phases | Focus |
|---|---|
| 1–4 | Repository structure and project documentation |
| 5 | Historical sales calls dataset |
| 6–8 | Mock FastAPI services, Docker Compose, testing docs |
| 9–10 | Transcription API decision, n8n wiring |
| 11–14 | Real service implementations: guardrails, RAG, signal analyser, LangGraph agent |
| 15 | Full backend + n8n integration test (no frontend) |
| 16–18 | React frontend, dashboard, Ollama assistant |
| 19–20 | Deployment notes, prompt engineering log, final cleanup |

Full phase-by-phase breakdown and acceptance criteria are in [CLAUDE.md](CLAUDE.md).

## Getting started

Setup instructions will be added as services are implemented (see relevant phase in [docs/PROGRESS.md](docs/PROGRESS.md)). Until Phase 16, there is no frontend — every service is exercised directly via curl, Postman, or n8n webhook calls.
