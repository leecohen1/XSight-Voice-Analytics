# XSight — Progress Tracker

Tracks completed phases and open decisions. Updated at the end of every phase.

## Phase status

| Phase | Description | Status |
|---|---|---|
| 1 | Repository structure | In progress |
| 2 | README and project documentation | Not started |
| 3 | Technology decisions document | Not started |
| 4 | Architecture document with Mermaid diagram | Not started |
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

### Phase 1 — Repository structure (in progress)

Created the top-level repository structure: `frontend/`, `n8n/`, `services/` (with `rag_service/`, `call_signal_analyser/`, `guardrails_service/`, `langgraph_agent/`), `data/`, `models/`, `docs/`, `demo/`. Added placeholder `README.md` files to every main folder, a top-level `README.md` with project overview, `CLAUDE.md` with the full project specification, this `PROGRESS.md` file, and a `.gitignore` covering Python, Node, React, Docker, environment variables, model files, audio files, and local data artifacts (e.g. ChromaDB data).

Awaiting user confirmation to mark Phase 1 complete.
