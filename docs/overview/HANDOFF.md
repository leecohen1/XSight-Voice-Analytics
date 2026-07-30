# XSight Overview Vertical Slice — Session Handoff

Written for the next Claude Code session. Read this before touching Overview,
Calls, Call Details, Analyze Call, `call_data_service`, or the n8n workflow.

---

# Current Repository State

- **Branch:** `main`
- **Latest pushed commit:** `c8c389d` — `Connect Overview and call screens to real backend APIs` (local `HEAD` and `origin/main` match exactly)
- **Repository status:** working tree has only pre-existing, unrelated local changes (below) — nothing from the Overview work is uncommitted
- **Remaining local-only excluded files** (deliberately not staged/committed/pushed this session — a separate, already-flagged-as-"awaiting review" workstream):
  ```
  M  docs/PROGRESS.md                                            (only the Langfuse paragraph, lines 297-315)
  M  docs/ai_observability_integration_design.md
  M  services/ai_observability_service/README.md
  M  services/ai_observability_service/app/langfuse_client.py
  M  services/ai_observability_service/app/langfuse_query_adapter.py
  M  services/ai_observability_service/tests/test_langfuse_client.py
  M  services/ai_observability_service/tests/test_langfuse_query_adapter.py
  ?? .agents/            (Claude Code plugin/skill tooling — not project code)
  ?? .claude/             (same)
  ?? frontend/.claude/    (same)
  ?? skills-lock.json     (same)
  ?? docs/FULL_PROJECT_AUDIT.md  (a separate, earlier audit deliverable)
  ```
  Do not commit these unless the user explicitly asks — they belong to a different, already-flagged workstream ("Langfuse instrumentation — MVP wiring", see `docs/PROGRESS.md`'s own note: "Not committed to git — awaiting user review, per explicit instruction").

---

# Completed

The Overview screen went from 100% frontend-mock (two hardcoded KPI constants, no backend read/write path at all) to a real, tested, end-to-end vertical slice. Three commits, in order:

| Commit | Contains |
|---|---|
| `544e8da` | `services/call_data_service/` (new FastAPI+S3 service), `docker-compose.yml` addition, `docs/api_contracts.md` §6, `docs/overview/01_Audit.md`, `docs/overview/03_API_Mapping.md` |
| `7b440b8` | n8n workflow contract changes, `docs/overview/02_Integration_Plan.md` |
| `c8c389d` | Full frontend (JS→TS migration bundled + real-API wiring), `docs/overview/04_Test_Plan.md`, `docs/overview/05_Completion_Report.md` |

## `call_data_service` (port 8006)

New standalone FastAPI service, `services/call_data_service/`. Owns **all** business persistence — no database, S3 only, under a new prefix:
```
xsight/application/analyzed-calls/v1/year=YYYY/month=MM/day=DD/<call_id>.json
```
— a **sibling**, never a child, of the Bedrock KB's `xsight/bedrock/historical-calls/v1/` prefix, so a live analyzed call can never be swept into the curated RAG corpus. Guarded three times: startup config check, per-key `_assert_safe_key` re-validation before every Get/Put/List, and tests.

Endpoints: `GET /health`, `POST /calls` (idempotent by `call_id`, re-derives `attention`/`recovery_opportunity` server-side), `GET /calls` (filterable list, summaries only), `GET /calls/{call_id}` (full record incl. transcript), `GET /overview?period=7d|30d` (the entire Overview screen, pre-aggregated — all business math happens here, never in the frontend).

Deterministic attention formula (`app/attention.py`): precedence `evidence_conflict > human_review > critical_coaching > customer_dissatisfaction > recoverable_opportunity > low_priority`, 0–100 priority score. Mirrored identically in the n8n Router node. Full formula documented in `docs/overview/03_API_Mapping.md` §5.

Historical seed script: `scripts/seed_historical_calls.py` — converts the 24-call CSV corpus deterministically (fixed date-offset table, no random dates, no AI calls of any kind) into the same S3 format live calls use. **Not yet run against the real bucket** — dry-run only, verified 24/24 built.

## n8n workflow contract

`n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`, 46→50 nodes (tracked JSON only — **the live n8n Cloud workflow was never touched this session**):
- `Capture Start Time` now mints a canonical `CALL_<uuid4>` (not `$execution.id`, which is kept separately as `workflow_execution_id` for observability only) and carries `agent_name`/`customer_name`/`call_date`/original filename forward.
- `Router - Confidence and Category` now also derives `attention` and `recovery_opportunity` deterministically, and emits a new response envelope: `{call_id, created_at, call_date, agent_name, customer_name, status, router_reasons, analysis}`.
- New `Build Persistence Payload → HTTP Request - Call Data Service` branch, non-blocking (`onError: continueRegularOutput`, 5s timeout) — a storage failure only flips `persistence.persisted` to `false`, it never costs the user their analysis.
- `HTTP Request - Call Data Service`'s URL is still the placeholder `REPLACE_WITH_CALL_DATA_SERVICE_URL:8006` — must be replaced before this goes live (see Remaining Live Deployment, step 4).

## Frontend

Overview, Calls, Call Details, and Analyze Call are now **real-backend-only, no mock fallback**. All business aggregation happens server-side; the frontend renders returned values without recomputing. Overview has a 7d/30d period selector with loading/error/empty/success states and retry. `frontend/src/data/mockCallStore.ts` and the in-memory call store are no longer used by these four screens. The frontend's previous client-generated `XS-100N` call-id scheme is gone — the backend-owned `CALL_<uuid4>` (or `CALL_0NN` for historical) is used everywhere, so a page refresh on Call Details actually re-fetches from `call_data_service` instead of losing state.

Team Intelligence, AI Operations, and Ask XSight remain mock-backed — no backend contract exists for them; out of scope, untouched.

## Docker validation

`docker compose build --no-cache call_data_service` → **exit 0**, image built and tagged. Root cause of an earlier "no output" hang was found and fixed: two orphaned build processes from earlier background attempts were still holding the shared BuildKit builder — not a Dockerfile or network issue (confirmed via a direct `docker pull` and daemon health check). Post-build: `docker compose up -d call_data_service` → health check passed, `GET /health` → 200, container logs clean, two validation-error paths both returned the expected 422, port `8006` confirmed bound. Container was stopped again afterward, environment left clean.

## Tests

```
services/call_data_service          220 passed  (in-memory S3 fake, zero network calls)
services/rag_service                 50 passed  (regression, untouched)
services/call_signal_analyser        15 passed  (regression, untouched)
services/guardrails_service           19 passed  (regression, untouched)
services/langgraph_agent             12 passed  (regression, untouched)
frontend  npm run typecheck          clean
frontend  npm run lint               clean (oxlint)
frontend  npm run test               52 passed (4 files — Vitest, newly added this session)
frontend  npm run build              clean
n8n workflow structural validator     38/38 checks, 14/14 Code nodes parse
```
**368 automated tests passing, 0 failing**, re-verified against the actual committed code (not just pre-commit).

## Commits pushed

```
c8c389d  Connect Overview and call screens to real backend APIs
7b440b8  Extend n8n workflow with call persistence contract
544e8da  Add S3-backed call data service and overview aggregation
```
`git push origin main` completed: `b5f4503..c8c389d main -> main`. `origin/main` and local `HEAD` match exactly.

---

# Remaining Live Deployment

Nothing below has real AWS/n8n-Cloud credentials applied yet — this environment could only build, test, and validate locally.

## 1. IAM permissions

- **Objective:** grant `call_data_service` write/read access to its own S3 prefix without touching the Bedrock role.
- **Files involved:** none in-repo (AWS console/CLI action). Reference: `services/call_data_service/.env.example` for the exact prefix names.
- **Commands:** none scripted — create/attach a policy scoped to:
  ```
  Actions: s3:GetObject, s3:PutObject, s3:ListBucket
  Resource: arn:aws:s3:::xsight-sales-call-analytics-881490130721-us-east-2/xsight/application/analyzed-calls/v1/*
  ```
  Do **not** extend the existing `AmazonBedrockExecutionRoleForKnowledgeBase_xsight` role — it is read-only on a different prefix by design.
- **Expected result:** the credentials that `call_data_service` runs with (wherever deployed) can `PutObject`/`GetObject`/`ListObjectsV2` under `xsight/application/analyzed-calls/v1/` and get `AccessDenied` on anything under `xsight/bedrock/`.

## 2. Seed historical calls into S3

- **Objective:** populate the real bucket with the 24-call corpus so Overview has non-trivial data on day one.
- **Files involved:** `services/call_data_service/scripts/seed_historical_calls.py`, `data/historical_sales_calls.csv` (read-only, never modified).
- **Commands:**
  ```bash
  cd services/call_data_service
  python scripts/seed_historical_calls.py --anchor-date <today's date, YYYY-MM-DD> --dry-run   # sanity check first
  python scripts/seed_historical_calls.py --anchor-date <today's date, YYYY-MM-DD>              # real write, needs AWS creds from step 1
  ```
- **Expected result:** console output `Wrote 24 records (0 overwritten, idempotent by call_id)`; safely re-runnable. Confirm in the S3 console: 24 objects under `xsight/application/analyzed-calls/v1/`, **none** under `xsight/bedrock/`.

## 3. Deploy `call_data_service` to EC2

- **Objective:** make the service reachable at a stable URL, matching how the other four services are already deployed.
- **Files involved:** `services/call_data_service/Dockerfile`, `docker-compose.yml` (for the env var reference list), `.env.example`.
- **Commands:** none scripted in-repo — mirror whatever deployment process stood up `rag_service` (`3.20.223.245:8001`), `call_signal_analyser`/`langgraph_agent` (`18.117.114.95:8002`/`:8004`), `guardrails_service` (`3.151.162.120:8003`). Open port 8006 on the target instance's security group.
- **Expected result:** `curl http://<EC2-IP>:8006/health` → `200 {"status":"ok","service":"call_data_service","version":"1.0.0"}` from outside the instance.

## 4. Update the live n8n Cloud workflow

- **Objective:** bring the live workflow (`RBII7JvRDFWwy98x`) up to the tracked JSON's contract, so the persistence branch actually reaches the deployed service.
- **Files involved:** `n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json` (import source).
- **Commands:** none scripted — via the n8n UI/MCP tools: import or diff-apply the tracked JSON, then:
  1. On `HTTP Request - Call Data Service`, replace `http://REPLACE_WITH_CALL_DATA_SERVICE_URL:8006/calls` with the real EC2 URL from step 3.
  2. **Reattach the `Google Gemini(PaLM) Api account` credential** to the three Gemini nodes (`Gemini Information Extractor`, `AI Agent Node - Classify and Enrich`, `Gemini Final Analysis Chain`) — a pre-existing, already-documented n8n API limitation (credential references never round-trip through the export API for this node type), not something this session introduced or can fix from the repo side.
- **Expected result:** a live test execution returns HTTP 200 with `persistence.persisted: true` in the response, and the corresponding object appears under `xsight/application/analyzed-calls/v1/` in S3 within seconds.

## 5. Configure frontend environment variables

- **Objective:** point the deployed (or locally-run) frontend at the real backend instead of erroring out.
- **Files involved:** `frontend/.env` (gitignored — create from `frontend/.env.example`).
- **Commands:**
  ```bash
  cd frontend
  cp .env.example .env
  # edit .env:
  #   VITE_CALL_DATA_SERVICE_URL=http://<EC2-IP-or-domain>:8006
  #   VITE_N8N_WEBHOOK_URL=<the live n8n webhook URL>
  npm run dev    # or npm run build && serve dist/ for a production check
  ```
- **Expected result:** Overview loads real data (no "VITE_CALL_DATA_SERVICE_URL is not set" error); Calls and Call Details resolve against real `call_id`s.

## 6. End-to-end browser validation

- **Objective:** the one verification step no prior session could do — no browser automation was available in this environment.
- **Files involved:** none — manual click-through.
- **Commands:** none.
- **Expected result, checklist:**
  - Overview loads for both `7d` and `30d`, shows real KPIs (not `4.0`/`3.4` placeholders), attention list, recent calls, close-rate trend, improved agents.
  - Calls list renders and is filterable.
  - Call Details opens by real `call_id`, and **a hard browser refresh on that URL still loads the record** (proves persistence, not in-memory state).
  - Submit one real audio file via Analyze Call → navigates to `/calls/<CALL_uuid>` → that same call shows up in Overview's "Recent Calls" and in the Calls list without needing a manual refresh-triggered re-fetch loop.

---

# Known Constraints

These are non-negotiable for any future work on this vertical slice — do not redesign around them:

- **n8n remains the sole orchestrator.** It calls every AI component directly; no AI service calls another AI service. `call_data_service` is called by n8n's post-Router branch — it is never itself an orchestrator and never calls n8n, Gemini, AssemblyAI, RAG, or LangGraph.
- **`call_data_service` owns persistence exclusively.** No other service and no direct S3 access from n8n or the frontend. n8n's `HTTP Request - Call Data Service` node is the only write path; the frontend's `GET /calls`, `GET /calls/{id}`, `GET /overview` are the only read paths.
- **RAG remains Amazon Bedrock Knowledge Base**, `Retrieve`-only (never `RetrieveAndGenerate`), over the existing `xsight/bedrock/historical-calls/v1/` prefix. `call_data_service`'s application prefix must never overlap it — this is enforced in code, not just convention; do not weaken or remove the `_assert_safe_key` guard or the startup prefix-overlap check.
- **LangGraph performs reasoning only** — it does not gain a persistence role, does not call `call_data_service`, and does not become a second source of the attention/recovery formula (that formula lives in exactly two places: `app/attention.py` and the n8n Router's mirrored JS — do not add a third).
- **No new database.** S3 is the only persistence layer for business call data. Do not introduce SQLite/Postgres/DynamoDB/etc. for this purpose even if it would simplify a future feature — that decision was explicit and deliberate.
- **No authentication has been added anywhere** — consistent with the project's existing, explicitly-accepted demo posture (`docs/FULL_PROJECT_AUDIT.md`, SEC-1). This is a known gap, not something to silently "fix" as a side effect of unrelated work — it needs its own explicit task.

---

# Current Risks

Only real, currently-true risks — not resolved-but-historical ones:

- **The n8n persistence branch has never run against a real deployed `call_data_service`.** Everything was verified in isolation (unit tests, local Docker, a dry-run seed script, a Node.js harness replicating the Router's JS). The first real end-to-end execution against a live EC2-deployed service and a live n8n Cloud workflow has not happened yet — deployment step 4 above is the first time these two sides will actually talk to each other for real.
- **The real S3 bucket has zero analyzed-call records right now.** Until step 2 runs, `GET /overview` against production will correctly return an empty-but-valid response (verified this degrades gracefully), not an error — but it will look empty to a demo audience until seeding happens.
- **The Gemini credential reattachment (step 4) is a known, recurring manual step**, not a one-time fix — this same n8n API limitation was already hit and worked around in a prior session. Anyone re-importing this workflow into a fresh n8n instance will hit it again.
- **No authentication on any of the five backend services or the n8n webhook.** Explicitly accepted for the current demo scope, but a real risk the moment this handles real customer audio or is exposed beyond a controlled demo.
- **`GET /calls` and `GET /calls/{call_id}` scan the entire application S3 prefix** rather than using an index. Fine at demo scale (dozens of records); would need revisiting before any larger real dataset.

---

# Next Recommended Task

Start with **Remaining Live Deployment, step 1 (IAM permissions) through step 4 (n8n Cloud update)**, in that exact order — each step is a hard prerequisite for the next (no IAM grant → seeding fails; no deployed service → n8n has nothing to call; no updated n8n workflow → the persistence branch stays a placeholder). Do not attempt step 6 (browser validation) until steps 1–5 are all confirmed working independently, since a failure there could be any of five different links in the chain and would be hard to isolate blind.

Before starting, re-read `docs/overview/05_Completion_Report.md` for the exact verified commands and expected outputs from local validation, and `docs/overview/03_API_Mapping.md` for the exact request/response shapes `call_data_service` expects — the deployment steps above assume that contract hasn't drifted, and any live discrepancy should be treated as a deployment-environment bug, not a reason to change the already-tested contract.
