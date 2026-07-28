# call_data_service

S3-backed business persistence and Overview aggregation for analyzed sales
calls. Port **8006**.

This is the only service in XSight that stores business data. It never calls
Gemini, AssemblyAI, Bedrock, or any sibling service -- it persists what the
pipeline already produced, and aggregates it for the dashboard.

```
n8n Router --> Build Persistence Payload --> POST /calls  --> S3
React Overview / Calls / Call Details  --> GET  /overview|/calls  --> S3
data/historical_sales_calls.csv --> seed script --> POST-equivalent --> S3
```

## Storage layout, and why the prefix matters

```
s3://xsight-sales-call-analytics-.../
├── xsight/bedrock/historical-calls/v1/      <-- Bedrock KB corpus. NEVER written here.
└── xsight/application/analyzed-calls/v1/    <-- this service
    └── year=YYYY/month=MM/day=DD/<call_id>.json
```

The Bedrock Knowledge Base data source's `inclusionPrefixes` covers
`xsight/bedrock/...`. The application prefix is deliberately a **sibling**,
never a child, so a live analyzed call can never be swept into the curated
RAG corpus by an ingestion sync and then cited back as if it were validated
historical evidence.

That separation is enforced three times over, not just by convention:

1. `app/config.py` refuses to start if `XSIGHT_APPLICATION_PREFIX` resolves
   inside `XSIGHT_BEDROCK_FORBIDDEN_PREFIX`.
2. `app/repository.py::_assert_safe_key` re-checks **every** key before any
   Get/Put/List, and also rejects `..` traversal segments.
3. Tests assert both (`tests/test_repository.py`, `tests/test_seed.py`).

Live calls are never ingested into Bedrock. Nothing in this service, or in
the seed script, calls any Bedrock API.

The date partition comes from the record's own `created_at` (UTC), so an
Overview window query lists only the two or three month prefixes it actually
touches instead of scanning the bucket.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Standard XSight health contract |
| POST | `/calls` | Persist one analyzed call (idempotent by `call_id`) |
| GET | `/calls` | List call summaries (no transcripts) |
| GET | `/calls/{call_id}` | One full record, including the transcript |
| GET | `/overview?period=7d\|30d` | The whole Overview screen, pre-aggregated |

`GET /calls` accepts `limit`, `cursor`, `agent_name`, `status`, `source`,
`from_date`, `to_date`. `agent_name` matching is trimmed and
case-insensitive.

Errors use the same structured shape as the other four services --
`{"error": {"code", "message", "details"}}` -- and never contain a bucket
name, object key, AWS error code, or credential detail.

| Status | When |
|---|---|
| 400 | (reserved; malformed query values surface as 422 via FastAPI) |
| 404 | `CALL_NOT_FOUND` -- no stored record for that id |
| 422 | `VALIDATION_ERROR` (bad request body/params) or `MALFORMED_RECORD` |
| 500 | `INTERNAL_ERROR`, or `STORAGE_KEY_REJECTED` if a prefix guard fired |
| 503 | `SERVICE_MISCONFIGURED` (missing env) or `STORAGE_UNAVAILABLE` (S3) |

## Call IDs

| Source | Format | Minted by |
|---|---|---|
| `historical_seed` | `CALL_001` .. `CALL_024` | the curated CSV, preserved as-is |
| `live_analysis` | `CALL_<uuid4>` | the n8n workflow, before the pipeline runs |

One canonical, backend-owned namespace. The frontend's previous
`XS-100N` client-generated scheme is gone -- `POST /calls` rejects it, and a
test pins that.

Idempotency: the S3 key is a pure function of `call_id` and the record's
`created_at` date, so an n8n retry overwrites one object rather than
creating a duplicate.

## Attention and recovery opportunity

Both blocks are **derived server-side on every write**, from the same pure
functions the seed script uses (`app/attention.py`). A caller may send them;
the service recomputes and overwrites them, so an LLM can never influence
routing severity and the stored value can never drift from the documented
formula. `tests/test_api.py::test_post_call_ignores_caller_supplied_attention`
pins this.

Precedence (first match wins, most severe first) and the full priority-score
formula are documented in `app/attention.py`'s module docstring, and mirrored
in `docs/overview/03_API_Mapping.md`.

## Ground Truth

A value that was never measured is `None` -- never a fabricated default.
Seeded historical records carry `confidence: null` and `risk_level: null`
because the corpus never produced them, and `similar_calls: []` because no
RAG retrieval is run during seeding. `silence_ratio`-style silent defaulting
does not happen anywhere in this service.

## Historical seed

```bash
# Preview without touching S3 or AWS at all
python scripts/seed_historical_calls.py --dry-run

# Pin the dates for a reproducible run
python scripts/seed_historical_calls.py --anchor-date 2026-07-28 --dry-run

# Write for real (needs AWS credentials + the env vars below)
python scripts/seed_historical_calls.py
```

The CSV has no date column, so dates are **assigned deterministically, never
randomly**: each call's timestamp is `anchor_date - <fixed offset> days`,
where the offset comes from a hardcoded table indexed by the call's position
within its agent's group (calls sorted by `call_id`). Same rows + same anchor
=> byte-identical output, regardless of input row order.

The anchor defaults to today (UTC) so seeded data stays inside the rolling
Overview windows; `--anchor-date` pins it. The offsets guarantee, for each of
the four agents: >= 1 call in the current 7d window, >= 1 in the previous 7d
window, 3 in the current 30d window, 2 in the previous 30d window, with a
total corpus span of ~68 days. The two-per-window floor is what makes the
improved-agent rule evaluable; the improvement values themselves come from
the CSV's real scores -- the script never arranges data to manufacture one.

`data/historical_sales_calls.csv` is read-only to this script and is never
modified.

## Environment variables

See `.env.example`. `AWS_REGION` and `XSIGHT_S3_BUCKET` are required;
everything else has a documented default. AWS credentials are resolved
through boto3's standard chain and are never read from a file this service
owns.

## Running

```bash
cd services/call_data_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8006
```

Or via the root `docker-compose.yml` (`docker compose up call_data_service`).

## Testing

```bash
cd services/call_data_service
python -m pytest -q
```

220 tests. Every one runs against an in-memory S3 fake
(`conftest.py::FakeS3Client`, which implements real `ListObjectsV2`
continuation-token pagination) -- **zero network calls, no AWS credentials
required, no real bucket touched.**

## Known limitations

- **No authentication**, consistent with the rest of this project's current
  demo posture (see `docs/FULL_PROJECT_AUDIT.md`, SEC-1). A hard blocker
  before any real customer data; explicitly out of scope for this phase.
- **`GET /calls/{call_id}` scans the application prefix** to find the record,
  because the caller does not know the date partition. Fine at this
  project's scale; a call-id index would be the fix if the corpus grew large.
- **`GET /calls` loads every record** to filter and sort in one place. Same
  reasoning; `GET /overview` is already partition-scoped and does not do this.
- **Cursor paging is `call_id`-based and stable only within a sort order** --
  adequate here, not a general-purpose paging contract.
