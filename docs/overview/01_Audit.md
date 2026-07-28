# Overview — Pre-Integration Audit

State of the Overview screen and its backing data **before** this work, and
the gaps that had to close before it could show real data. Recorded as the
baseline the rest of this folder is measured against.

## 1. What the screen showed

Hero headline, a 4-tile KPI grid, "Calls Requiring Attention" and "Recent
Calls" lists, a "Call Volume" sparkline, and a next-action banner.

## 2. Where the numbers came from

| Element | Source before | Real? |
|---|---|---|
| Hero headline | Template string built client-side from a mock array length | No |
| Calls Analyzed | `.length` over `frontend/src/data/mockCalls.ts` | No |
| Needs Attention | Client-side `.filter()` over the same array | No |
| Avg. Agent Performance | **Hardcoded literal `4.0`** in `analyticsApi.ts` | No |
| Avg. Lead Quality | **Hardcoded literal `3.4`** | No |
| Calls Requiring Attention list | Client-side filter + `.slice(0, 5)` | No |
| Recent Calls list | Client-side sort + `.slice(0, 6)` | No |
| Call Volume trend | Borrowed from `mockAiOperations.ts` (a different domain) | No |
| Next action | Derived client-side from the mock array | No |

Nothing on the screen came from a backend. Two KPIs were literal constants
with a code comment admitting it.

## 3. The blocking gaps

1. **No persistence of any kind.** The n8n pipeline was a stateless
   request/response webhook: it returned the analysis and discarded it. No
   database, no S3 write, no store anywhere held a completed analysis.
2. **No read API.** No endpoint anywhere returned more than one call.
   `services/ai_observability_service` had read endpoints, but they carry
   only token/cost/latency telemetry — no `call_outcome`, `agent_name`, or
   score — so they could not serve Overview even if fixed.
3. **No `call_id` reached the client.** n8n minted `call_id = $execution.id`
   internally but never returned it. The frontend invented its own `XS-100N`
   ids purely for in-session routing.
4. **No dates on historical data.** `data/historical_sales_calls.csv` has 26
   columns and no `call_date`/`created_at`, so "recent calls" and any
   period-over-period comparison were impossible from the corpus alone.
5. **`router_reasons` computed then discarded.** The Router calculated them
   and `Build Success Response` dropped them.
6. **No attention/priority concept existed** anywhere in the repository.
7. **Results were lost on refresh.** `mockCallStore.ts` was a module-level
   array; a page reload reset it to static fixtures.
8. **No frontend test runner** was configured at all.

## 4. What already existed and was reused

- The 24-call curated corpus (`CALL_001`–`CALL_024`, 4 agents, balanced
  8 Sale / 8 No Sale / 8 Follow-up Needed) with real scores and objections.
- The S3 bucket `xsight-sales-call-analytics-881490130721-us-east-2`.
- The 46-node n8n pipeline, live and verified end-to-end.
- The repo's service conventions: FastAPI + Pydantic + a structured error
  envelope + `GET /health` + Dockerfile + `.env.example` + pytest.

## 5. S3 finding that shaped the design

`xsight/bedrock/historical-calls/v1/` is the Bedrock Knowledge Base data
source's `inclusionPrefixes`. Writing live analyses there would let an
ingestion sync pull unvalidated live calls into the curated RAG corpus, which
would then be cited back as if it were verified historical evidence.

That is why the application prefix is a **sibling**, not a child — and why
the separation is enforced in config, in the repository's key guard, and in
tests, rather than by naming convention alone.

See [02_Integration_Plan.md](02_Integration_Plan.md) for what was built.
