# Overview — Architecture and Integration Plan

The architecture as built. No database was introduced; Amazon S3 is the
business persistence layer, in the existing bucket, under a new prefix.

## 1. Final architecture

```
                     React Analyze Call
                            |
                            v
              n8n full analysis workflow (46 -> 50 nodes)
                            |
                 Router - Confidence and Category
                   (deterministic: guardrail_status,
                    router_reasons, attention,
                    recovery_opportunity)
                       /            \
                      /              \
        Build Persistence      Build Observability
            Payload                 Events
              |                        |
   HTTP Request - Call        HTTP Request -
      Data Service            Observability Events
     (onError: continue)          (unchanged)
              |
   Build Success Response --> Respond - Full Analysis --> React
              |
        call_data_service (:8006)
              |
             S3


  React Overview / Calls / Call Details
              |
        call_data_service (:8006)
              |
             S3
```

Historical seed (offline, one-off):

```
data/historical_sales_calls.csv
        |
  seed_historical_calls.py   (deterministic; no AI calls)
        |
  CallRepository.put_record  (same abstraction the API uses)
        |
       S3
```

## 2. S3 separation

```
s3://xsight-sales-call-analytics-881490130721-us-east-2/
├── xsight/bedrock/historical-calls/v1/      Bedrock KB corpus — UNTOUCHED
└── xsight/application/analyzed-calls/v1/    NEW — this work
    └── year=YYYY/month=MM/day=DD/<call_id>.json
```

The application prefix is a **sibling** of the Bedrock prefix, never a child,
so it falls outside the data source's `inclusionPrefixes` and can never be
swept into the RAG corpus.

Enforced three independent times, not by convention:

| Layer | File | Behaviour |
|---|---|---|
| Startup | `services/call_data_service/app/config.py` | Refuses to start if the application prefix resolves inside the forbidden prefix |
| Every operation | `app/repository.py::_assert_safe_key` | Re-validates every key before any Get/Put/List; also rejects `..` traversal |
| Tests | `tests/test_repository.py`, `tests/test_seed.py` | Assert both, including that seeding writes 24 objects all under the application prefix and none under `xsight/bedrock/` |

Live calls are **never** ingested into Bedrock. No code in this service or
the seed script calls any Bedrock API. The n8n workflow contains no S3 or
Bedrock-ingestion node (asserted by the workflow validator).

The date partition comes from each record's own `created_at` (UTC), so an
Overview window lists only the 2–3 month prefixes it actually touches instead
of scanning the bucket.

## 3. Why S3 and not a database

The constraint was explicit, but it is also a reasonable fit here: the
working set is tens to low-hundreds of records, reads are window-scoped by a
date-partitioned key, and the bucket, region and credential path already
existed. The cost is that `GET /calls` and `GET /calls/{id}` scan a prefix
rather than hitting an index — documented as a known limitation in the
service README, and the reason `GET /overview` is partition-scoped instead.

## 4. Call ID unification

| Kind | Format | Minted by |
|---|---|---|
| Historical | `CALL_001` … `CALL_024` | The curated CSV, preserved verbatim |
| Live | `CALL_<uuid4>` | n8n's `Capture Start Time` node, before the pipeline runs |

One backend-owned namespace. `$execution.id` is retained separately as
`workflow_execution_id` for observability correlation only — it is never the
public identifier. The frontend's `XS-100N` scheme is gone; `POST /calls`
rejects it and a test pins that.

## 5. Persistence is non-blocking

`HTTP Request - Call Data Service` sets `onError: continueRegularOutput` with
a 5-second timeout, so:

- A storage failure, or an undeployed service, **continues** to the success
  response instead of failing it.
- The user always receives their analysis; only `persistence.persisted`
  changes.
- No retries: the write is idempotent by `call_id`, so an n8n-level retry
  would add latency without adding safety.

**Trade-off, stated plainly:** the node sits in the response path rather than
on a truly parallel branch, because the requirement also asked for a
persistence result in the response — which is unobtainable from a fire-and-
forget branch. "Non-blocking" is therefore implemented as *cannot fail or
stall the response* (continue-on-error + bounded timeout), not as *runs
concurrently*. The observability branch remains genuinely parallel.

## 6. Attention is deterministic, never model-generated

Derived twice from the same documented formula — once in the n8n Router (so
the immediate response carries it) and once in `call_data_service` on write
(so the stored record can never drift, and a caller cannot inflate its own
priority). Gemini never sets `guardrail_status`, `attention`, or
`recovery_opportunity`.

Rules and the priority-score formula: [03_API_Mapping.md](03_API_Mapping.md).

## 7. Deliberate scope boundaries

- **No authentication** — consistent with the project's current demo posture
  (`docs/FULL_PROJECT_AUDIT.md`, SEC-1). A hard blocker before real customer
  data.
- **Team Intelligence / AI Operations / Ask XSight remain mock-backed** — no
  backend contract exists for them. Untouched by this work.
- **No live n8n Cloud edit** — only the tracked JSON export was modified; see
  [05_Completion_Report.md](05_Completion_Report.md) for the import steps.
