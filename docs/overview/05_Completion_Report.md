# Overview — Completion Report

## Status

The Overview vertical slice is implemented, tested, and documented — **and
the `call_data_service` Docker image is now built and verified live.**
Everything runs on real data paths end to end **except** the two steps that
need AWS/n8n credentials this session did not have: seeding the real S3
bucket, and importing the workflow into n8n Cloud. Both are listed below.

- Backend: 220 tests passing
- Frontend: 52 tests passing; typecheck, lint and build clean
- n8n workflow: 38/38 structural checks; all 14 Code nodes parse
- **Docker image built (`docker compose build --no-cache`, exit 0) and
  verified live: healthy, correct port, clean logs, both validation-error
  paths return the expected 422**
- No database introduced. Amazon S3 only.
- No mock fallback anywhere in Overview, Calls, Call Details or Analyze Call.

## Files created

```
services/call_data_service/
├── app/{__init__,config,errors,models,attention,repository,aggregation,dependencies,main}.py
├── scripts/seed_historical_calls.py
├── tests/{__init__,test_models,test_repository,test_aggregation,test_api,test_seed}.py
├── conftest.py
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md

frontend/src/test/{setup.ts,fixtures.ts}
frontend/src/pages/{Overview,CallDetails,AnalyzeCall}.test.tsx
frontend/src/services/callsApi.test.ts

docs/overview/{01_Audit,02_Integration_Plan,03_API_Mapping,04_Test_Plan,05_Completion_Report}.md
```

## Files modified

| File | Change |
|---|---|
| `docker-compose.yml` | Added `call_data_service` on 8006 with a health check and prefix env vars |
| `n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json` | Canonical `call_id`; submission metadata; attention/recovery in the Router; new response envelope; persistence branch (46 → 50 nodes) |
| `frontend/src/types/overview.ts` | Replaced with the backend Overview DTO |
| `frontend/src/types/call.ts` | Nullable analysis fields; attention/recovery; backend wire shapes; `PipelineResponse` |
| `frontend/src/services/analyticsApi.ts` | Real `GET /overview`; mock branch deleted |
| `frontend/src/services/callsApi.ts` | Real `GET /calls`, `GET /calls/{id}`; adapters; backend-owned `call_id`; mock store removed |
| `frontend/src/services/config.ts` | Added `callDataServiceUrl()` |
| `frontend/src/services/httpClient.ts` | Added `getJson()` with the services' error envelope |
| `frontend/src/pages/Overview.tsx` | Rewritten against the real API; period selector; all UI states |
| `frontend/src/pages/Overview.module.css` | Styles for the new elements |
| `frontend/src/pages/AnalyzeCall.tsx` | Backend `call_id`; persistence warning; mock simulation removed |
| `frontend/src/pages/CallDetails.tsx` | Fetch by `call_id`; just-analyzed fallback; unhandled-rejection fix |
| `frontend/src/components/call-details/OfficialAnalysisPanel.tsx` | Null-safe rendering |
| `frontend/src/services/askXsightApi.ts` | Null-safe confidence/risk |
| `frontend/vite.config.ts` | Vitest config |
| `frontend/package.json` | `test` scripts; Vitest/RTL/jsdom dev deps |
| `frontend/.env.example` | `VITE_CALL_DATA_SERVICE_URL`; clarified `VITE_USE_MOCK` scope |

## Historical seed result

Dry run against the real CSV, anchor `2026-07-28`: **24/24 records built,
0 failures.** Distribution:

- 4 agents × 6 calls; offsets `[1,10,22,36,52,68] + agent stagger (0–3)`
- Current 30d: 12 calls (3/agent). Previous 30d: 8 calls (2/agent).
- Current 7d and previous 7d: 1 call per agent each.
- Corpus span ≈ 68 days.
- 11 calls flagged for attention: 5 `human_review`, 3
  `customer_dissatisfaction`, 2 `recoverable_opportunity`, 1
  `critical_coaching` (CALL_014, score 80 — the corpus's documented `Sale`
  with `agent_performance_score = 2` contrast case, correctly surfaced).

Nothing was written to S3 — that needs real credentials (below).

## Remaining manual AWS / n8n steps

1. **IAM** — the role used by `call_data_service` needs `s3:GetObject`,
   `s3:PutObject` and `s3:ListBucket` scoped to
   `xsight/application/analyzed-calls/v1/*` on the existing bucket. The
   current Bedrock execution role is read-only on the ingestion prefix and
   is deliberately **not** the right role to extend.
2. **Confirm the Bedrock data source's `inclusionPrefixes`** is still exactly
   `["xsight/bedrock/historical-calls/v1/"]`, so the application prefix stays
   outside it. (Bedrock console → KB `EDCC0WT0OB` → data source `UDNMPNSGXZ`.)
3. **Seed the real bucket**:
   `python scripts/seed_historical_calls.py --anchor-date <today>` with
   credentials present. Re-runnable safely — writes are idempotent by key.
4. **Deploy `call_data_service`** to EC2 on 8006 and open the port, matching
   how the other four services were deployed.
5. **Import the workflow** into n8n Cloud from the tracked JSON, then:
   - replace `REPLACE_WITH_CALL_DATA_SERVICE_URL` on
     `HTTP Request - Call Data Service` with the deployed host;
   - **reattach the `Google Gemini(PaLM) Api account` credential to the three
     Gemini nodes** — this is a known, previously documented limitation of the
     n8n API for this node type, unchanged by this work.
6. **Frontend env** — set `VITE_CALL_DATA_SERVICE_URL` and
   `VITE_N8N_WEBHOOK_URL` in `frontend/.env`.
7. **Browser verification** — no browser automation was available in this
   session, so a manual click-through of Overview (7d/30d), Calls, Call
   Details (including a hard refresh) and one live Analyze Call is still
   worth doing.

## Docker build — verified

`docker compose build --progress=plain --no-cache call_data_service` was run
to completion in this session: **exit code 0**, all 6 build stages completed
(`FROM python:3.11-slim` → `WORKDIR` → `COPY requirements.txt` →
`RUN pip install` → `COPY app` → `COPY scripts`), image exported and tagged
`xsight-ai-sales-call-analytics-call_data_service:latest` (313MB disk /
79.3MB content — consistent with the other four services' image sizes).

**Root cause of the earlier "no output, no image" result, found and fixed:**
two `docker compose build call_data_service` process trees from earlier
background attempts in this session were still alive and never terminated
(their parent Bash-tool invocations had returned control, but the underlying
`sh.exe`/`docker.exe`/`docker-compose.exe`/`docker-buildx.exe` chain kept
running). All three attempts shared the same `desktop-linux` BuildKit
builder; the two stale trees held it, so every new build queued indefinitely
at `[internal] load metadata for docker.io/library/python:3.11-slim` — the
exact symptom seen twice before. This was **not** a Dockerfile, build-context,
dependency-resolution, or registry-networking problem: a direct
`docker pull python:3.11-slim` succeeded immediately throughout, and
`docker version`/`docker info` confirmed the daemon itself was healthy
(Docker Desktop 4.73.1, engine 29.4.3). Killing the two orphaned process
trees (confirmed via `Get-CimInstance Win32_Process`, then terminated)
unblocked the current build within seconds — the stuck metadata-load step
that had been pending for 387.4s completed as soon as the builder freed up.
No repository file needed to change; `services/call_data_service/Dockerfile`
was correct throughout (it mirrors the four working services' Dockerfiles
exactly, and 3 of those 4 also have no `.dockerignore`, so that was ruled
out as a contributing factor too).

**Post-build live verification** (`docker compose up -d call_data_service`,
then verified from the host, container stopped again afterward to leave the
environment clean):

| Check | Result |
|---|---|
| Health check | `healthy` (Docker `HEALTHCHECK`, confirmed via `docker inspect .State.Health`) |
| `GET /health` | `200 {"status":"ok","service":"call_data_service","version":"1.0.0"}` |
| Container logs | Clean startup (`Application startup complete`, `Uvicorn running on http://0.0.0.0:8006`), no errors or tracebacks |
| Validation-error path 1 | `GET /overview?period=90d` → `422 VALIDATION_ERROR` (`period` pattern mismatch) |
| Validation-error path 2 | `POST /calls` with `call_id: "XS-1004"` → `422 VALIDATION_ERROR` (rejects the retired frontend id scheme) |
| Port | `docker port` → `8006/tcp -> 0.0.0.0:8006` and `[::]:8006`; `docker inspect` confirms `Status: running`, `Health: healthy` |

## Known limitations

- **No authentication**, consistent with the project's current posture
  (`docs/FULL_PROJECT_AUDIT.md`, SEC-1). A hard blocker before real customer
  data.
- **Persistence sits in the response path**, not on a truly parallel branch,
  because the response must carry a persistence result. It cannot fail or
  stall the response (continue-on-error + 5s timeout), but it is not
  concurrent. Rationale in [02_Integration_Plan.md](02_Integration_Plan.md) §5.
- **`GET /calls` and `GET /calls/{id}` scan the application prefix** — fine at
  this scale, and `GET /overview` is partition-scoped instead.
- **Team Intelligence, AI Operations and Ask XSight remain mock-backed** — no
  backend contract exists for them. Out of scope, untouched.
- **Live calls are never added to the RAG corpus.** Deliberate: the Bedrock
  corpus stays curated and static.
