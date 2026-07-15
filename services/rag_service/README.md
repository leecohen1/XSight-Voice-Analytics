# rag_service

Sales Call RAG Service.

**Status:** Phase 6 mock skeleton — API contract, validation, and error handling are real; retrieval is a deterministic mock. Full ChromaDB/LangChain implementation is Phase 12.

**Stack (planned, Phase 12):** FastAPI, LangChain, ChromaDB, HuggingFace embeddings (`sentence-transformers/all-MiniLM-L6-v2`), Llama.cpp. **Stack (this phase):** FastAPI + Pydantic only — no model downloads, no API keys.

**Called by:** n8n, directly — in parallel with the Call Signal Analyser. Not called by the LangGraph agent.

## Endpoints

- `GET /health` → `{"status": "ok", "service": "rag_service", "version": "0.1.0"}`
- `POST /query` → mock similar-calls response (see below). Real behavior in Phase 12: retrieves grounded, cited historical calls from ChromaDB.

### `POST /query` request

```json
{
  "transcript": "Agent: ... Customer: ...",
  "metadata": {
    "agent_name": "Sarah Levi",
    "call_duration_seconds": 420,
    "sale_result": "Sale"
  },
  "top_k": 3
}
```

Validation: `transcript` is required, non-empty, minimum 20 characters. `top_k` must be an integer between 1 and 10. `metadata` is optional and every field inside it is optional.

### `POST /query` response (mock)

```json
{
  "similar_calls": [
    {
      "call_id": "CALL_007",
      "agent_name": "Daniel Cohen",
      "sale_result": "Sale",
      "main_objection": "price",
      "similarity_score": 0.89,
      "reason": "Mock similarity result based on a price objection resolved through a quantified reframe."
    }
  ],
  "insight": "Mock grounded insight referencing 1 historical call(s) (CALL_007). Real retrieval is not implemented yet.",
  "citations": ["CALL_007"],
  "grounded": true,
  "mock": true
}
```

The mock response is drawn from a small hardcoded pool of five example calls (not from `data/historical_sales_calls.csv` — that file's existence is optionally logged at startup, but it is never read or ingested in this phase) and is fully deterministic: the same request always returns the same response, so tests are repeatable.

## Error handling

All errors use the shared structured shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [{"loc": ["body", "transcript"], "msg": "...", "type": "..."}]
  }
}
```

`VALIDATION_ERROR` (422) for request-shape/constraint failures, `HTTP_ERROR` (4xx) for routing/method errors, `INTERNAL_ERROR` (500) for unexpected exceptions.

## Running locally

```bash
cd services/rag_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

```bash
curl http://localhost:8001/health

curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing.", "top_k": 2}'
```

## Testing

```bash
cd services/rag_service
pytest -v
```

## Docker

```bash
docker build -t xsight-rag-service services/rag_service
docker run -p 8001:8001 xsight-rag-service
```

Or via the root `docker-compose.yml` (`docker compose up rag_service`).

See [CLAUDE.md](../../CLAUDE.md) and [docs/api_contracts.md](../../docs/api_contracts.md) for the full contract, and [docs/dataset_design.md](../../docs/dataset_design.md) for the corpus schema this service will eventually retrieve from.
