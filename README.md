# XSight — AI Sales Call Analytics System

XSight is a voice-based sales call analytics system. Users upload a recorded sales call audio file, and the system transcribes it, analyzes the sales conversation, extracts structured insights, compares the call to similar historical sales calls, predicts sales signals, and returns practical coaching and follow-up recommendations.

This is a full rebuild of XSight from scratch, with a new architecture and a new technology stack. It is not related to any previous version of this project.

## Status

Under active development. Built incrementally in phases — see [docs/PROGRESS.md](docs/PROGRESS.md) for current progress.

## Main users

- Sales managers
- Sales team leaders
- Sales agents
- Sales operations teams

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

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Orchestration | n8n Cloud |
| Transcription | External API (TBD — Phase 9) |
| LLM (orchestration) | Gemini |
| Guardrails | NeMo Guardrails + FastAPI |
| RAG | LangChain + ChromaDB + HuggingFace embeddings + Llama.cpp |
| Call signal analysis | PyTorch (transcript-derived features) |
| Agent reasoning | LangGraph + FastAPI |
| Local assistant | Ollama |
| Data | CSV + ChromaDB |
| Deployment | Docker (local) → AWS EC2 |

See [CLAUDE.md](CLAUDE.md) for the full project specification, including architecture, JSON schemas, and phase plan.

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
├── data/                      ← historical sales calls dataset
├── models/                    ← trained model artifacts (not committed)
├── docs/                      ← project documentation
├── demo/                      ← demo assets and script
├── docker-compose.yml
└── .gitignore
```

## Architecture overview

See [CLAUDE.md](CLAUDE.md) for the full architecture flow and Mermaid diagram. In short:

```
User uploads audio → React → n8n Cloud → Input Guardrails → Transcription
  → Gemini extraction → RAG Service + Call Signal Analyser + LangGraph Agent
  → Output Guardrails → Results shown in React
```

## Development approach

The system is built in 20 phases, one at a time, with explicit approval required before moving to the next phase. The React frontend is built last (Phase 16 onwards); all backend services are tested via curl, Postman, and direct n8n webhook calls during Phases 1–15.

## Getting started

Setup instructions will be added as services are implemented (see relevant phase in [docs/PROGRESS.md](docs/PROGRESS.md)).
