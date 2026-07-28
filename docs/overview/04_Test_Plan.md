# Overview — Test Plan and Results

## Commands

```bash
# Backend
cd services/call_data_service && python -m pytest -q          # 220 passed

# Frontend
cd frontend && npm run typecheck                              # clean
cd frontend && npm run lint                                   # clean (oxlint)
cd frontend && npm run test                                   # 52 passed
cd frontend && npm run build                                  # built in 1.17s

# n8n workflow (structural + JS syntax)
python scratchpad/validate_workflow.py n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json
                                                              # 38/38 checks passed
```

## Backend — 220 tests, 5 files

Every test runs against an in-memory S3 fake (`conftest.py::FakeS3Client`)
implementing real `ListObjectsV2` continuation-token pagination. **Zero
network calls; no AWS credentials required; no real bucket touched.**

| File | Covers |
|---|---|
| `test_models.py` | Historical/live call-id validation; rejection of the retired `XS-100N` scheme; status/source/priority/category enums; score and confidence bounds; agent-name normalization (incl. the caller cannot override the grouping key); naive datetimes read as UTC; unknown fields default to null/`[]` not zero; forward-compatible extra fields |
| `test_repository.py` | Date-partitioned key generation, zero-padding, UTC conversion, determinism; **Bedrock-prefix write refusal**; outside-application-prefix read refusal; `..` traversal refusal; config-level prefix guard; idempotent overwrite by `call_id`; `ListObjectsV2` pagination (7 objects at page size 2); malformed JSON and schema-violating objects skipped not raised; all-malformed dataset; non-`.json` keys ignored; storage failure → typed error; month-prefix range incl. year boundary; 7d/30d window bounds, contiguity, non-overlap |
| `test_aggregation.py` | Current/previous 7d and 30d selection; boundary call belongs to current only; close-rate denominator **excludes `Uncertain`**; zero-denominator → null; case-insensitive outcome matching with canonical output; averages ignoring nulls; KPI absolute/percentage change; **percentage change null when previous is 0**; improved-agent minimum-call and improvement thresholds (incl. a just-under-threshold case); case/whitespace-insensitive agent grouping; declining agents excluded; attention and recent ordering; exactly 4 trend buckets, chronological, non-overlapping, each call in exactly one; empty and all-malformed datasets; **every attention precedence pair; the priority-score formula component-by-component; missing confidence/risk never scoring as low/high; clamping at 100; all four priority bands** |
| `test_api.py` | Health; POST persists at the expected key; **server-side derivation of attention (a caller cannot inflate its own priority)**; status derived from guardrail status; idempotent double-POST; rejection of `XS-1004`; missing/out-of-range field 422s; list ordering, limit, cursor paging, and filters (agent/status/source/date); malformed records reported not fatal; get by id; 404; **error bodies never leak bucket or key**; full Overview contract shape; period defaulting/validation; 4 buckets; empty storage; entirely malformed storage still 200; storage failure → 503; a posted live call appearing in the Overview |
| `test_seed.py` | Row conversion; preservation of call id, agent, outcome, objection, scores, transcript; outcome canonicalization; `mixed` sentiment → `neutral`; unknown sentiment → null; **no fabricated confidence, risk, similar calls, or follow-up email**; `manager_notes` used verbatim; null customer name; deterministic attention per rule; date determinism independent of row order; no future dates; ≥60-day span; every agent in both 7d and both 30d windows; UTC timestamps; the real 24-call corpus converting completely; dry run touching no AWS; missing CSV exit code; **seeding through the repository writing 24 objects all under the application prefix and none under `xsight/bedrock/`**; re-seed idempotency; the seeded corpus producing a working Overview (12 current / 8 previous) |

## Frontend — 52 tests, 4 files

`fetch` is stubbed per test; the shared setup rejects any unstubbed call, so
no test can silently reach the network.

| File | Covers |
|---|---|
| `Overview.test.tsx` (21) | Loading, error, empty, and success states; retry re-issuing the request; **no mock fallback on failure** (retired fixtures asserted absent); clear failure when the service URL is unset; KPI values rendered exactly as returned; comparison strings from the API; undefined percentage change reported as such; **attention order preserved as the backend sent it**; recent calls; improved agents; 4 trend buckets; null customer name rendering safely; `period=7d` by default and `period=30d` on switch; `aria-pressed`; navigation by backend `call_id` from both lists; malformed-record disclosure |
| `callsApi.test.ts` (19) | Real endpoint URLs; contract mapping; backend errors surfaced instead of demo data; unset URL error; null customer/date handling; attention flags; fetch by id incl. uuid ids; 404 → null; genuine failures rethrown; all-null seeded record; router-reason code mapping and unknown-code degradation; multipart upload; **backend-owned `call_id`, never `XS-`**; persistence failure not losing the analysis |
| `CallDetails.test.tsx` (6) | Fetch by backend id; **cold load of a uuid id with no router state (a real refresh)**; seeded record with null fields rendering with no `null`/`NaN`/`undefined` leaking to the DOM; not-found state; fallback to the just-analyzed result when persistence failed; storage error surfaced |
| `AnalyzeCall.test.tsx` (6) | Navigation using the backend `call_id`; **never routing to `XS-100N`**; navigation still occurring on persistence failure; pipeline rejection surfaced with its stage and no raw webhook URL in the user-facing message; missing-call-id error; client validation before any network call |

## n8n workflow — 38 structural checks

50 nodes, unique names/ids, no dangling connections; canonical `CALL_<uuid4>`
with `$execution.id` retained separately; all four submission-metadata fields
carried forward; the full response envelope incl. `persistence`; attention and
recovery derived in the Router; `guardrail_status` still deterministic;
persistence branch connected after the Router with `continueRegularOutput` and
a bounded timeout; persistence result flowing into the success response, which
still reaches the responder; **no S3 write, no Bedrock ingestion, no reference
to the Bedrock prefix anywhere in the workflow**; RAG path unchanged; and all
14 Code nodes parsed with `node --check`.

The Router's JavaScript was additionally dry-run in Node against three mocked
pipeline payloads and produced output identical to the Python implementation
(clean sale → no attention; conflict + low confidence → `evidence_conflict`,
score clamped to 100; missing customer name → `null`, not `""`).

## Live service validation (uvicorn, real boto3)

- `GET /health` → 200 `{"status":"ok","service":"call_data_service","version":"1.0.0"}`
- `GET /overview` with unusable credentials → **503 with no AWS detail in the
  body**; the underlying `InvalidAccessKeyId` / `AccessDenied` appears only in
  the server log. This is the credential-leak guarantee, verified rather than
  assumed.
- `GET /overview?period=90d` → 422
- `POST /calls` with `XS-1004` → 422
- Missing `AWS_REGION` + `XSIGHT_S3_BUCKET` → both reported in one
  `ConfigurationError`
- `XSIGHT_APPLICATION_PREFIX=xsight/bedrock/live/` → refused at startup

## Not verified

`docker compose build call_data_service` did not complete in this session
(the build produced no output and no image; the four pre-existing containers
were running, so the daemon was up). `docker compose config` validates, the
Dockerfile mirrors the four working services exactly, and the app's import,
startup, health and error paths were all verified directly via uvicorn — but
the image build itself remains unconfirmed. See
[05_Completion_Report.md](05_Completion_Report.md).
