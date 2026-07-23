# rag_service

Sales Call RAG Service.

**Status:** Phase 12 — real implementation. `POST /query` retrieves grounded
historical-call evidence from a provisioned Amazon Bedrock Knowledge Base
(`Retrieve` API only, never `RetrieveAndGenerate`) and shapes the response
deterministically — no LLM call happens inside this service. See
[docs/PROGRESS.md](../../docs/PROGRESS.md) for the full provisioning record
(resource ARNs, ingestion job IDs) and
[ingestion/README.md](ingestion/README.md) for the pipeline that populated
the Knowledge Base from `data/historical_sales_calls.csv`.

**Stack:** FastAPI + boto3 (`bedrock-agent-runtime`). No LangChain, no
ChromaDB, no local embedding model, no local LLM.

**Called by:** n8n, directly — in parallel with the Call Signal Analyser.
Not called by the LangGraph agent. This service never calls Gemini or
LangGraph itself.

## Endpoints

- `GET /health` → `{"status": "ok", "service": "rag_service", "version": "0.2.0"}`
- `POST /query` → retrieves and returns grounded, cited historical calls.

### `POST /query` request

```json
{
  "transcript": "Agent: ... Customer: ...",
  "metadata": {
    "agent_name": "Sarah Levi",
    "call_duration_seconds": 420,
    "sale_result": "Sale"
  },
  "top_k": 3,
  "filters": {
    "main_objection": "price"
  }
}
```

- `transcript` — required, minimum 20 characters. Used as the retrieval query text.
- `metadata` — optional context about the *current* call. Accepted for
  contract backward-compatibility; it does not affect retrieval.
- `top_k` — optional, integer 1–10, default 3. Maps to Bedrock's `numberOfResults`.
- `filters` — optional. Only field names marked `allowed_for_filtering: true`
  in [ingestion/metadata_schema.json](ingestion/metadata_schema.json) are
  honored (currently 11 fields: `customer_segment`, `industry`,
  `main_objection`, `customer_intent`, `customer_sentiment`, `sale_result`,
  `call_category`, `closing_attempt`, `follow_up_needed`,
  `next_meeting_scheduled`, `decision_maker_present`). Unrecognized or
  invalid-value keys are dropped, not rejected — the request still succeeds,
  reported in `retrieval_metadata.dropped_filter_keys`. At most one filter
  is ever applied, per the ingestion README's Small-Corpus Filter Policy —
  a filtered query that returns zero results is retried once unfiltered.

### `POST /query` response

```json
{
  "similar_calls": [
    {
      "call_id": "CALL_023",
      "agent_name": "Noa Friedman",
      "sale_result": "Follow-up Needed",
      "main_objection": "price",
      "similarity_score": 0.6725632548332214,
      "reason": "Historical call CALL_023 with a 'price' objection; outcome: Follow-up Needed."
    }
  ],
  "insight": "Found 1 similar historical call(s) (CALL_023) — see each result's reason for the specific match.",
  "citations": ["CALL_023"],
  "grounded": true,
  "retrieval_metadata": {
    "knowledge_base_id": "EDCC0WT0OB",
    "search_type": "SEMANTIC",
    "filter_requested": null,
    "filter_applied": false,
    "dropped_filter_keys": [],
    "results_returned": 1,
    "results_above_threshold": 1
  }
}
```

Every field in `similar_calls[]` is read directly from Bedrock's own
returned metadata for that result — never invented. A retrieval result
missing a required field (`call_id`, `agent_name`, `sale_result`,
`main_objection`) or a similarity score is dropped, not filled in. Results
below the similarity-score floor (`app/response_builder.py`,
`SIMILARITY_SCORE_FLOOR = 0.5`) are excluded from `similar_calls`/`citations`
even though `retrieval_metadata.results_returned` still counts them. When
nothing clears the floor, `insight` is exactly `"Not enough evidence to
identify similar historical calls for this transcript."`, `citations` is
empty, and `grounded` is `false` — explicit uncertainty, never a guess.

`overrideSearchType` is always `SEMANTIC` — Amazon S3 Vectors (the
provisioned backend) does not support Bedrock's `HYBRID` search mode.

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

| Code | HTTP | Cause |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Request body fails Pydantic validation |
| `SERVICE_MISCONFIGURED` | 503 | Required environment variables missing, or the metadata schema file couldn't be loaded |
| `UPSTREAM_ACCESS_DENIED` | 502 | Bedrock rejected the service's own AWS credentials/role |
| `UPSTREAM_VALIDATION_ERROR` | 400 | Bedrock rejected the retrieval request itself |
| `UPSTREAM_THROTTLED` | 429 | Bedrock is rate-limiting requests |
| `UPSTREAM_UNAVAILABLE` | 503 | Network/timeout error, or any other Bedrock service error |
| `HTTP_ERROR` | 4xx | Routing/method errors |
| `INTERNAL_ERROR` | 500 | Unexpected exception |

No response ever includes a raw AWS exception message, stack trace, ARN, or
account ID — every Bedrock/boto3 exception is caught, logged server-side
with full detail, and mapped to one of the generic messages above before it
reaches the client.

## Running locally

```bash
cd services/rag_service
pip install -r requirements.txt
cp .env.example .env   # already has the provisioned, non-secret resource IDs
uvicorn app.main:app --reload --port 8001
```

AWS credentials are resolved through the standard boto3 credential chain
(environment variables, `~/.aws/credentials`, or an IAM role) — never from
`.env`/`.env.example`, which contain only non-secret resource identifiers.

```bash
curl http://localhost:8001/health

curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing and whether it fits our budget.", "top_k": 3}'
```

## Testing

```bash
cd services/rag_service
pytest -v
```

All unit and endpoint tests mock `boto3` (patched at
`app.bedrock_client._client`) — no live AWS access or credentials are
required for the normal test suite. `tests/test_filters.py` runs against the
real `ingestion/metadata_schema.json`, not a stub, so the filter allowlist
tests can't silently drift from the actual schema.

**Live smoke test** (requires real AWS credentials with access to the
provisioned Knowledge Base):

```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"transcript": "customer felt the price was too high and wanted a discount"}'
```

## Docker

```bash
docker build -t xsight-rag-service services/rag_service
docker run -p 8001:8001 --env-file .env xsight-rag-service
```

Or via the root `docker-compose.yml` (`docker compose up rag_service`) —
`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN` are read from
the host shell environment or a gitignored `.env` file at the repo root,
never hardcoded into `docker-compose.yml` itself.

See [CLAUDE.md](../../CLAUDE.md) and [docs/api_contracts.md](../../docs/api_contracts.md)
for the full contract, [docs/dataset_design.md](../../docs/dataset_design.md)
for the corpus schema, [ingestion/README.md](ingestion/README.md) for the
data-preparation pipeline, and [docs/PROGRESS.md](../../docs/PROGRESS.md)
for the AWS provisioning record.
