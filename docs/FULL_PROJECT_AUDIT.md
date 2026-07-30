# XSight — Full Project Audit

**Audit date:** 2026-07-27
**Auditor:** Claude Code (review-first, no modifications made to production, AWS resources, n8n credentials/workflow, or deployed services during this audit)
**Baseline treated as verified-working (regression baseline):** the live end-to-end execution described in the task (real Gemini extraction/final analysis, grounded Bedrock RAG, real Call Signal Analyser + LangGraph responses from the deployed EC2 services, correct multi-signal Router routing, frontend in live mode).

This report is evidence-driven. Every finding below cites the file/line or command output it is based on. Where a check could not be run (missing tool, out-of-scope git-history depth, etc.), that limitation is stated explicitly rather than assumed passing.

---

## 1. Executive Summary

The backend architecture is implemented largely as documented: n8n is the sole orchestrator, no AI service calls another AI service directly, and each service's responsibility boundary (extraction-only, retrieval-only, scoring-only, reasoning-only, synthesis) is respected in the actual code paths, not just in naming. All 96 backend pytest tests pass, the frontend builds and lints cleanly, and `docker compose config` validates.

However, the audit surfaced one **Critical** class of findings that directly threatens the reproducibility of the verified-working pipeline: **the four real bugs fixed live in n8n today (a Gemini-response-shape parsing bug, an LLM-echo grounding bug, a thinking-token/output-token misconfiguration, and the resulting silent-fallback cascade) are not reflected in the git-tracked n8n workflow export.** If that exported JSON were ever re-imported (disaster recovery, a new environment, onboarding a teammate), it would reproduce the exact broken state debugged today, silently — every Gemini call would truncate, every parser would fall back to defaults, and Bedrock citations could be silently overwritten by LLM-echoed content. `docs/PROGRESS.md` also has no record of today's work at all, so there is currently no durable, reviewable record of what was fixed or why outside this conversation.

Beyond that, findings cluster around three real (not hypothetical) classes: (1) frontend robustness gaps that are currently masked by backend guarantees but would surface if any upstream contract drifts (null-vs-undefined array handling, no ErrorBoundary, results lost on page refresh); (2) unauthenticated public exposure of all four backend services and the n8n webhook itself, which is an explicit, accepted decision for today's demo but is a hard blocker before any real customer data; and (3) normal supply-chain hygiene gaps (a moderate react-router CVE, test packages shipped in production images, root containers) that are low-effort to fix.

No secrets were found anywhere in the working tree or across the full 34-commit git history (verified by direct scan, not assumed).

**Release readiness: not production-ready, demo-ready.** The verified E2E behavior is real and reproducible *today* only because the live n8n workflow still holds the undocumented fixes. See §16.

---

## 2. Audit Scope

Reviewed: `CLAUDE.md`, `README.md`, `docs/architecture.md`, `docs/technology_decisions.md`, `docs/api_contracts.md`, `docs/PROGRESS.md`, `docs/dataset_design.md`, `docs/dataset_validation_report.md`, `docs/historical_call_matrix.md`, `docs/generated_calls_batch_0{1-5}.md`, all four FastAPI services (`app/`, `tests/`, `Dockerfile`, `requirements.txt`, `.env.example`, `README.md`), the React frontend (all `src/` files, `package.json`, `vite.config.js`, `.gitignore`), both n8n workflow exports, `docker-compose.yml`, `scripts/*.py` and `scripts/test_mock_services.sh`, `services/rag_service/ingestion/*`, `.mcp.json`, `.gitignore`, and the full git commit history (34 commits).

Not exhaustively reviewed (stated as limitations, not silently skipped): `frontend/src/index.css` (large stylesheet, not scanned for unused classes); the full word-for-word content of all 24 historical call transcripts in `data/historical_sales_calls.csv` for adversarial phrasing; the complete IAM policy JSON for the `user10` interactive AWS identity or the Bedrock execution role (relied on `docs/PROGRESS.md`'s existing provisioning record for the latter); n8n Cloud's own platform-level upload body-size limits; live production log output (reviewed logging *call sites* in source, not captured runtime logs).

---

## 3. Commands and Tools Used

```
git ls-files | sort
git status --porcelain=2 --untracked-files=all
git log --oneline | wc -l                                  # 34 commits
git log --all --diff-filter=A --name-only --pretty=format:  # ever-added .env/.pem/.key/credentials files -> none
git log --all -p | grep -nE "AKIA...|aws_secret_access_key...|BEGIN ... PRIVATE KEY|ghp_...|AIza..."  # no matches

cd services/rag_service            && python -m pytest -q   # 50 passed
cd services/call_signal_analyser   && python -m pytest -q   # 15 passed
cd services/guardrails_service     && python -m pytest -q   # 19 passed
cd services/langgraph_agent        && python -m pytest -q   # 12 passed

cd frontend && npm run build       # succeeds, 26 modules, ~230KB JS / 6KB CSS gz
cd frontend && npm run lint        # oxlint, exit 0, no findings
cd frontend && npm audit --json    # 2 moderate (react-router)

docker compose config --quiet      # valid
docker compose ps                  # all 4 containers still healthy from prior session

pip check                          # "No broken requirements found" (global env only, not per-service isolated)
python -m pip_audit --version      # NOT INSTALLED
safety --version                  # NOT INSTALLED
ruff --version                    # NOT INSTALLED
ls tsconfig*.json                  # none — project is plain JS/JSX, no type-check step to run

grep -rniE "<secret-pattern-list>" (working tree, all tracked source/text file types)   # no matches
```

Live n8n workflow (`RBII7JvRDFWwy98x`) inspected via the connected n8n MCP tools (`get_workflow_details`, `search_executions`, `get_execution`) and diffed programmatically against the git-tracked export at `n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`.

**Not run, reported as a limitation, not assumed:** `pip-audit`, `safety`, `ruff` (none installed in this environment); a TypeScript type-check (project has no `tsconfig.json` — plain JS/JSX); any load/concurrency test; a live re-scan of IAM policy documents via AWS API.

---

## 4. Architecture Conformance Matrix

| # | Rule | Verdict | Evidence |
|---|---|---|---|
| 1 | n8n is the central orchestrator | **PASS** | Live execution trace (execution `21`) shows every AI call — guardrails, both Gemini calls, RAG, Signal Analyser, LangGraph — invoked directly by n8n nodes, in the documented order, with no service calling another. |
| 2 | No AI service directly calls another AI service | **PASS** | `services/rag_service/app/*.py`, `services/call_signal_analyser/app/*.py`, `services/langgraph_agent/app/*.py` contain no outbound HTTP client code (no `requests`/`httpx` client usage for calling sibling services). RAG's only outbound call is to Bedrock (its own retrieval backend, not another AI service in this architecture). |
| 3 | Gemini Information Extractor performs extraction only | **PASS** | System prompt (live workflow, node "Gemini Information Extractor") explicitly forbids coaching/recommendations/final analysis; live execution `21`'s `Parse Gemini Extraction` output contains only the documented extraction fields, no coaching text. |
| 4 | n8n AI Agent Node has limited classification/enrichment/payload-prep role | **PASS** | System prompt matches CLAUDE.md's constraint list verbatim ("must NEVER reason over evidence, generate coaching feedback, recommend actions, reconcile conflicting evidence, or invent information"); live output (`Parse AI Agent Enrichment`) contains only `submission_intent`/`decision_maker_present`/`relevant_services`/`enriched_call_category`. |
| 5 | RAG performs retrieval and returns grounded historical evidence | **PASS** | `services/rag_service/app/response_builder.py:29-53` drops any Bedrock result missing a required metadata field or similarity score rather than fabricating one; `test_query_malformed_bedrock_result_is_dropped_not_fabricated` (rag_service/tests/test_main.py:152-169) passes. Live execution shows `grounded: true` with 3 real `CALL_0xx` citations and real `retrieval_metadata`. |
| 6 | Call Signal Analyser performs signal scoring only | **PASS** | `services/call_signal_analyser/app/mock_rules.py` consumes `structured_fields` (Gemini's own extraction) rather than re-deriving intent/objection/sentiment from the transcript itself — no transcript-parsing/NLP logic exists in this service beyond what's already provided in the request body. |
| 7 | LangGraph reasons only over evidence already supplied to it | **PASS** | `services/langgraph_agent/app/graph.py` and `app/main.py` contain no outbound HTTP calls anywhere; `GraphState` is populated entirely from the incoming `AgentRunRequest`. |
| 8 | Gemini Final Analysis synthesizes but does not replace deterministic source data | **PASS (live) / FAIL (as committed)** | Live: `Parse Final Analysis Output`'s current jsCode forces `transcript` and `similar_calls` from the deterministic pipeline context (`ctx.tagged_transcript`, `ctx.rag_results.similar_calls`), never the LLM's echoed values — verified today with an adversarial fixture containing a hallucinated `CALL_999_HALLUCINATED` citation and a wrong transcript; both were correctly discarded. **As committed to git, the same node still contains the OLD code that prefers `parsed.transcript`/`parsed.similar_calls` over the deterministic source** — see DOC-1/BUG-2. |
| 9 | Guardrails, routing, and human-review logic remain separate from final generation | **PASS** | `Router - Confidence and Category` is a plain, deterministic n8n Code node operating on the Gemini output plus `signal_analysis`/`langgraph_reasoning`/`rag_results` — it is not part of the Gemini prompt/response; Gemini is explicitly instructed *not* to set `guardrail_status` ("that is assigned deterministically by the workflow after you respond, not by you"). |
| 10 | The frontend only submits calls and renders the returned contract | **PASS** | `frontend/src/api/analyzeCall.js` and `frontend/src/components/ResultsView.jsx` contain no scoring, routing, or business-rule logic — only form submission and read-only rendering/formatting (percentage rounding, tone-coloring badges) of fields already present in the response. |

**Rules 1, 2, 3, 4, 6, 7, 9, 10: fully conformant, live and as committed.**
**Rule 5: fully conformant.**
**Rule 8: conformant only in the live, unexported state — see DOC-1 (Critical).**

---

## 5. Critical and High Findings

### DOC-1 — n8n workflow export does not reflect four real, live-verified bug fixes
- **Severity:** Critical
- **Confidence:** Confirmed (programmatic diff performed, not inferred)
- **Component:** `n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json` vs. live workflow `RBII7JvRDFWwy98x`
- **Evidence:** Direct field-by-field comparison via the n8n MCP `get_workflow_details` tool against the repo file:
  - All 3 Gemini nodes: repo shows `credentials: None`, `options.thinkingBudget: None` (defaults to n8n's dynamic `-1`), `options.maxOutputTokens: 1024/512/2048`. Live: credential attached, `thinkingBudget: 0`, `maxOutputTokens: 2048/1024/4096`.
  - `HTTP Request - RAG Service` / `- Call Signal Analyser` / `- LangGraph Agent`: repo uses `={{ $env.RAG_SERVICE_URL }}` etc. (unresolved env-var expressions); live uses hardcoded working URLs (`http://3.20.223.245:8001`, `http://18.117.114.95:8002`, `http://18.117.114.95:8004`).
  - `Parse Gemini Extraction` / `Parse AI Agent Enrichment` / `Parse Final Analysis Output`: repo's `extractText()` only checks `item.candidates[0].content.parts[0].text` (the raw Google API shape); it does **not** check `item.content.parts[0].text`, which is the shape this n8n node version actually returns. Confirmed with a minimal Node reproduction: old function returns `null` for the real shape, fixed function returns the text correctly.
  - `Parse Final Analysis Output`: repo's `similar_calls`/`transcript` still prefer `parsed.*` (the LLM echo) over `ctx.rag_results.similar_calls`/`ctx.tagged_transcript` (the deterministic source) — the grounding fix is absent.
- **File and line:** `n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`, all four `Parse *` node `jsCode` parameters and the three Gemini node `parameters.options`/`credentials` blocks.
- **Reproduction:** Import the committed JSON into a fresh n8n instance and run it against real audio → every Gemini call hits `finishReason: MAX_TOKENS` after producing ~0 visible tokens (thinking-budget exhaustion) → every `Parse *` node's `extractText()` returns `null` → every field silently falls back to `unclear`/`other`/`neutral`/deterministic defaults → **the exact broken state debugged and fixed today reproduces itself, silently, with no error surfaced to the operator** (the pipeline still returns HTTP 200).
- **Impact:** Anyone recovering, redeploying, or onboarding onto this workflow from the repository alone gets a silently degraded pipeline that still "looks like" it's working (200 OK, schema-valid JSON) but produces zero real Gemini-derived content.
- **Recommended smallest safe fix:** Re-export the current live workflow (`get_workflow_details` → save as the tracked JSON) and commit it, replacing the stale file. This is a pure data-sync operation, not a design change — explicitly flagged here rather than performed, per this audit's no-modification constraint.
- **Regression-test recommendation:** Add a one-time script (or a documented manual step) that diffs the tracked export against the live workflow's key fields (credentials-present, `thinkingBudget`, `maxOutputTokens`, hardcoded URLs, `extractText` shape-check presence) before every "phase complete" commit touching n8n.
- **Architecture impact:** None — this is a sync/documentation gap, not an architecture change.
- **Approval required before changing:** No architectural approval needed to re-export/commit the current live workflow; **recommend explicit owner confirmation before overwriting the tracked file**, since it's a meaningful, security/behavior-relevant file.

### DOC-4 — Zero record of today's entire session in `docs/PROGRESS.md`
- **Severity:** High
- **Confidence:** Confirmed
- **Component:** `docs/PROGRESS.md`
- **Evidence:** The file's phase log ends at the Phase 12 RAG implementation entry from a prior session. There is no entry for: the four parallel "demo day" workstreams, the merge, the EC2 deployments of Call Signal Analyser and LangGraph, the credential/thinking-budget/extractText/grounding bug fixes, or the frontend live-mode wiring.
- **File and line:** `docs/PROGRESS.md` (entire file — nothing after the Phase 12 entry).
- **Reproduction:** N/A (absence, not a behavior).
- **Impact:** The project's own single source of truth for "what happened and why" is silent on the highest-risk work performed to date (three production-blocking bugs found and fixed live against a running system). Combined with DOC-1, there is currently no durable record — inside or outside this conversation — of what was actually fixed.
- **Recommended smallest safe fix:** Add a dated phase-log entry summarizing today's session, per the project's own established log format (this is explicitly a documentation task, not a code change).
- **Regression-test recommendation:** N/A (documentation).
- **Architecture impact:** None.
- **Approval required:** No — this is exactly the kind of update `docs/PROGRESS.md` exists for, per `CLAUDE.md`'s own working conventions. Still listed here rather than performed, per the audit's explicit no-modification scope.

### DOC-9 / DOC-10 — `n8n/README.md` and `n8n/SETUP.md` actively misstate current implementation status
- **Severity:** High
- **Confidence:** Confirmed
- **Component:** `n8n/README.md`, `n8n/SETUP.md`
- **Evidence:** `n8n/README.md`'s Status line states "Everything from post-transcription guardrails onward (nodes 5-16) is not yet implemented." `n8n/SETUP.md` states the workflow "stops once the transcription job is accepted." Both are false as of today — the same workflow ID has been extended in place to all 16 nodes and live-verified end-to-end (execution `21`, HTTP 200).
- **File and line:** `n8n/README.md` lines 5, 7; `n8n/SETUP.md` lines 5-6, 13-14.
- **Impact:** A reader (including a future Claude Code session or a teammate) consulting these files to understand current state would be actively misled into believing the pipeline is far less complete than it is.
- **Recommended smallest safe fix:** Rewrite the Status sections to reflect the full 16-node implementation and today's live verification.
- **Regression-test recommendation:** N/A (documentation).
- **Architecture impact:** None.
- **Approval required:** No, but flagged rather than performed per audit scope.

### SEC-1 — All four backend services and the n8n webhook are publicly reachable with no authentication
- **Severity:** High (explicitly accepted as an intentional demo-scope decision — see classification below)
- **Confidence:** Confirmed
- **Component:** `services/rag_service`, `services/call_signal_analyser`, `services/guardrails_service`, `services/langgraph_agent`, n8n `Webhook Trigger` node
- **Evidence:** All four services' `app/main.py` files contain no authentication dependency, API-key check, or bearer-token validation of any kind (confirmed by reading every route handler in all four files). Security group `sg-0c472b2b3bd93b3a1` has ports `22, 80, 8002, 8004` open to `0.0.0.0/0` (confirmed via `aws ec2 describe-security-groups` earlier this project). The n8n webhook path is a plain POST URL with no header-auth/HMAC signature configured on the `Webhook Trigger` node's parameters.
- **File and line:** all four `services/*/app/main.py` (no auth dependency anywhere in the file); n8n `Webhook Trigger` node parameters.
- **Reproduction:** `curl -X POST http://18.117.114.95:8002/analyse-call -d '{...}'` from any machine on the internet succeeds with no credential.
- **Impact:** (a) Anyone who discovers these IPs/ports can call any backend service directly, bypassing guardrails, the AI Agent Node, and the Router entirely. (b) Anyone who obtains the webhook URL can trigger real, paid pipeline runs (AssemblyAI transcription, 3 Gemini calls, Bedrock retrieval) with arbitrary audio content, at the owner's expense.
- **Recommended smallest safe fix:** Add a shared-secret header check (simplest) or n8n's built-in header-auth webhook option, plus basic API-key middleware on the four FastAPI services, before any use beyond today's controlled demo.
- **Regression-test recommendation:** Add a test asserting each service's protected endpoint returns 401/403 without the expected credential once auth is added.
- **Architecture impact:** None — additive, does not change the documented architecture.
- **Approval required:** **Yes.** This is explicitly called out in the task's own decisions as accepted for today ("Use HTTP for the demo microservices... Do not add HTTPS, reverse proxies, API Gateway, authentication"). Classified here as an **intentional, already-approved limitation for the demo**, not a hidden defect — but it is a hard blocker before any production use with real customer data, and is restated here at High severity because the audit's job is to surface exactly this kind of accepted-but-consequential trade-off clearly.

---

## 6. Medium Findings

### BUG-1 — (Duplicate of DOC-1's root cause, listed separately for the correctness-review record) `extractText()` shape mismatch in all three `Parse *` Code nodes
- **Severity:** Medium (as committed) / was Critical in live production until fixed today
- **Confidence:** Confirmed (minimal reproduction run: old function returns `null`, fixed function returns the correct string, for the exact response shape this n8n Google Gemini node version returns)
- **Component:** n8n Code nodes `Parse Gemini Extraction`, `Parse AI Agent Enrichment`, `Parse Final Analysis Output`
- **Evidence:** `extractText()`'s candidate list checks `item.text`, `item.content` (an object, never a string, so always filtered out), `item.output`, `item.response`, `item.message`, and `item.candidates[0].content.parts[0].text` — but never the flat `item.content.parts[0].text` shape this specific `@n8n/n8n-nodes-langchain.googleGemini` node actually returns.
- **Reproduction:** See DOC-1.
- **Whether an existing test catches it:** No automated test exists for this n8n Code node logic at all (n8n Code nodes have no pytest/CI coverage in this repository).
- **Smallest safe fix:** Already applied live: add `item.content && item.content.parts && item.content.parts[0] && item.content.parts[0].text` to the candidate list in all three nodes. Needs re-export to the repo (see DOC-1).

### BUG-2 — Grounding bypass: LLM-echoed `transcript`/`similar_calls` could overwrite deterministic pipeline data
- **Severity:** Medium (as committed) / was High in live production until fixed today
- **Confidence:** Confirmed (adversarial-fixture unit test run today: hallucinated `CALL_999_HALLUCINATED` citation and a fabricated transcript were both discarded by the fixed code; the old code would have let both through)
- **Component:** `Parse Final Analysis Output` Code node
- **Evidence:** Old logic: `transcript: typeof parsed.transcript === 'string' ? parsed.transcript : ctx.tagged_transcript` and `similar_calls: Array.isArray(parsed.similar_calls) ? parsed.similar_calls : (ctx.rag_results.similar_calls || [])` — both prefer the LLM's own JSON over the deterministic source whenever Gemini happens to return well-formed JSON (which it usually does), directly contradicting the project's own "Grounding is enforced structurally, not just by instruction" principle (`docs/architecture.md` §2).
- **Reproduction:** Feed the node a Gemini response containing a fabricated `call_id` not in `ctx.rag_results.citations` → old code passes it through to the end user as if it were a real citation.
- **Whether an existing test catches it:** No (same gap as BUG-1 — no n8n Code node test harness exists in this repo).
- **Smallest safe fix:** Already applied live: always use `ctx.tagged_transcript` / `ctx.rag_results.similar_calls`, never `parsed.*`, for these two fields specifically. Needs re-export to the repo.

### BUG-3 — Dynamic thinking budget silently exhausts the entire output-token allowance
- **Severity:** Medium (as committed) / was Critical in live production until fixed today
- **Confidence:** Confirmed (live execution logs before/after the fix, showing `finishReason: MAX_TOKENS` with ~0 visible output tokens, then `finishReason: STOP` with complete JSON after setting `thinkingBudget: 0`)
- **Component:** All 3 Gemini nodes' `options.thinkingBudget` (defaulted to `-1`, dynamic)
- **Evidence:** Execution `18` (before fix): `Gemini Information Extractor` used 30 output tokens and produced only `"{\n  \"customer_intent\": \"medium\",\n  \"main_objection\": \"price\",\n  \"customer_sentiment\": \"` before hitting `finishReason: MAX_TOKENS` — the model's internal reasoning tokens (visible in the `thoughtSignature` field, a large opaque blob) consumed the rest of the 1024-token budget before any answer text was written.
- **Reproduction:** Any Gemini node in this n8n version with `thinkingBudget: -1` and a `maxOutputTokens` value under a few thousand will reliably truncate on non-trivial prompts.
- **Whether an existing test catches it:** No — there is no automated test exercising the real Gemini API call path at all (by design, per the project's mocked-boto3/no-live-AI-call testing philosophy for the FastAPI services; but the n8n Gemini nodes have zero test coverage of any kind).
- **Smallest safe fix:** Already applied live: `thinkingBudget: 0` (disables it — not needed for structured extraction) plus raised `maxOutputTokens` ceilings as a safety margin. Needs re-export to the repo.

### SEC-7 — Unauthenticated public webhook can trigger real, paid pipeline runs
- **Severity:** Medium-High depending on how widely the URL is shared
- **Confidence:** Confirmed
- **Component:** n8n `Webhook Trigger` node
- **Evidence:** No header-auth/HMAC configured; the production URL (`https://xsight.app.n8n.cloud/webhook/xsight-phase9-iteration1-mock-input-validation`) is a plain public POST endpoint.
- **Reproduction:** Any third party with the URL can POST an audio file and trigger AssemblyAI + 3x Gemini + Bedrock calls at the account owner's cost.
- **Impact:** Cost/abuse risk proportional to how widely the URL circulates (e.g., this conversation).
- **Recommended smallest safe fix:** Add n8n's built-in header-auth option to the Webhook Trigger node, or a shared-secret query parameter checked by an early IF node.
- **Regression-test recommendation:** A test asserting an unauthenticated request is rejected before any paid call executes.
- **Architecture impact:** None.
- **Approval required:** Yes — same accepted-for-today trade-off as SEC-1.

### OPS-3 — `retryOnFail: true` on paid external POST calls with no idempotency protection
- **Severity:** Medium
- **Confidence:** Confirmed for node configuration; reasoning-based (not reproduced live) for the duplicate-call scenario itself
- **Component:** n8n nodes `Gemini Information Extractor`, `AI Agent Node - Classify and Enrich`, `Gemini Final Analysis Chain`, `HTTP Request - RAG Service`, `HTTP Request - Call Signal Analyser`, `HTTP Request - LangGraph Agent` (all confirmed `onError: continueErrorOutput`, `retryOnFail: true`); AssemblyAI submission node not re-verified this session for the same setting.
- **Evidence:** Confirmed via `get_workflow_details` earlier this session: all six nodes have `retryOnFail: true`.
- **Reproduction (reasoning-based, not executed):** If Gemini or AssemblyAI processes a request successfully but the HTTP response is delayed past n8n's node timeout, n8n's transport-level retry will resubmit the same request — Gemini/AssemblyAI have no idempotency-key mechanism accessible from this integration, so this could produce a duplicate paid call and (for AssemblyAI) a duplicate transcription job.
- **Impact:** Low-probability but nonzero double-billing risk on slow responses.
- **Recommended smallest safe fix:** Either disable `retryOnFail` on paid external calls and let the existing `Error - *` nodes handle failure explicitly, or add a client-generated idempotency/request-id header where the provider supports one (AssemblyAI does not appear to; Gemini's API does not either, as used here).
- **Regression-test recommendation:** N/A without a way to simulate n8n transport-level timeouts in this repo's current test setup.
- **Architecture impact:** None.
- **Approval required:** Yes (n8n workflow change).

### BUG-8 — Frontend array destructuring defaults do not cover explicit `null`
- **Severity:** Medium (latent — not currently triggered by the live pipeline)
- **Confidence:** Confirmed via JS semantics + code reading; not reproduced against a live payload (current pipeline never sends `null` for these fields)
- **Component:** `frontend/src/components/ResultsView.jsx`
- **Evidence:** Lines 54, 55, 61: `similar_calls = []`, `coaching_feedback = []`, `detected_signals = []` — JS destructuring defaults apply only when the source property is `undefined`, not when it is explicitly `null`. `.length`/`.map()` on `null` throws `TypeError: Cannot read properties of null`.
- **File and line:** `frontend/src/components/ResultsView.jsx:54,55,61,110,125,153`.
- **Reproduction:** Render `<ResultsView result={{ ...validFields, similar_calls: null }} />` → throws, uncaught (no ErrorBoundary anywhere — see FE-2).
- **Whether an existing test catches it:** No frontend component tests exist at all (see TEST-gap section).
- **Smallest safe fix:** `similar_calls: result.similar_calls ?? []` (nullish coalescing) instead of destructuring defaults, for all three array fields.
- **Regression-test recommendation:** A component test rendering `ResultsView` with each array field explicitly `null`.
- **Architecture impact:** None.
- **Approval required:** No — this is a pure frontend robustness fix within the frontend workstream's own file ownership.

### BUG-9 — Results page loses its result on refresh/direct navigation
- **Severity:** Medium
- **Confidence:** Confirmed by code reading
- **Component:** `frontend/src/pages/Results.jsx`
- **Evidence:** `const result = location.state?.result` (line 6) — React Router's `location.state` exists only in-memory for the current navigation; it is not present after a page reload, a shared/bookmarked `/results` URL, or opening in a new tab.
- **File and line:** `frontend/src/pages/Results.jsx:5-6`.
- **Reproduction:** Submit a real call, wait for the Results page to render, then press F5 → "No analysis result to show yet" is shown, even though the analysis succeeded moments earlier.
- **Whether an existing test catches it:** No.
- **Smallest safe fix:** Persist the result to `sessionStorage` on receipt and hydrate from it if `location.state` is absent.
- **Regression-test recommendation:** A test simulating a reload after a successful submission.
- **Architecture impact:** None.
- **Approval required:** No.

### BUG-10 — No client-side timeout on the live webhook call
- **Severity:** Medium
- **Confidence:** Confirmed by code reading; latency range (26-44s observed) confirmed empirically this session
- **Component:** `frontend/src/api/analyzeCall.js`
- **Evidence:** The `fetch(webhookUrl, { method: 'POST', body: formData })` call (lines 64-67) has no `AbortController`/timeout. Observed real pipeline latency this session: 26-45 seconds; no documented upper bound exists (AssemblyAI polling alone is capped at 120s per `n8n/README.md`).
- **File and line:** `frontend/src/api/analyzeCall.js:62-67`.
- **Reproduction:** Any hang on the n8n/webhook side leaves the "Analyzing call…" spinner running indefinitely with no user-facing way to cancel or time out.
- **Whether an existing test catches it:** No.
- **Smallest safe fix:** Wrap the fetch in an `AbortController` with a generous timeout (e.g., 150s, comfortably above the observed 26-45s and the documented 120s AssemblyAI cap) and surface a clear timeout error message.
- **Regression-test recommendation:** A test mocking a hung fetch and asserting the UI recovers with an error state within the configured timeout.
- **Architecture impact:** None.
- **Approval required:** No.

### FE-2 — No ErrorBoundary anywhere in the React tree
- **Severity:** Medium
- **Confidence:** Confirmed (absence verified by reading `App.jsx`, `main.jsx`, and every component)
- **Component:** Frontend, whole tree
- **Evidence:** No `componentDidCatch`/`ErrorBoundary` component exists anywhere in `frontend/src/`.
- **Impact:** Any unexpected render exception (including BUG-8) crashes the entire app to a blank white screen with no recovery UI.
- **Recommended smallest safe fix:** Wrap `<App />` (or at minimum `<Results />`) in a simple ErrorBoundary component.
- **Regression-test recommendation:** A test that throws inside `ResultsView` and asserts the boundary's fallback UI renders instead of a blank page.
- **Architecture impact:** None.
- **Approval required:** No.

### SEC-10 — Pre-transcription file validation is metadata-only, never inspects file bytes
- **Severity:** Medium
- **Confidence:** Confirmed
- **Component:** `services/guardrails_service/app/guardrails.py`
- **Evidence:** `check_pre_transcription_input` validates only `filename`, client-supplied `mime_type`, and `file_size`/`size_bytes` — the endpoint "does not accept or log any binary audio content" (its own README, "Security notes"), so no magic-byte/content-sniffing check exists anywhere in this project's own code for the uploaded file.
- **File and line:** `services/guardrails_service/app/guardrails.py:43-102`.
- **Reproduction:** A client can claim `mime_type: audio/mpeg` / `filename: call.mp3` while the actual bytes (handled only by n8n → AssemblyAI, never parsed by this project's own code) are anything else.
- **Impact:** Bounded — no XSight-controlled service ever parses/executes the raw bytes; they are only ever forwarded to AssemblyAI's own (external, presumably hardened) API. Still worth documenting as a known gap.
- **Recommended smallest safe fix:** If/when a service in this project ever parses the raw audio bytes directly (e.g., a future local audio-preprocessing step), add magic-byte verification there — not urgent while no such step exists.
- **Regression-test recommendation:** N/A until real byte-level handling exists.
- **Architecture impact:** None.
- **Approval required:** No (informational until real file-byte handling exists).

### BUG-6 — n8n RAG-call timeout may be shorter than the RAG service's own worst-case retry chain
- **Severity:** Medium
- **Confidence:** Confirmed by reading both sides of the timing budget; not reproduced under an actual slow-Bedrock scenario
- **Component:** n8n node `HTTP Request - RAG Service` (`options.timeout: 15000`) vs. `services/rag_service/app/bedrock_client.py`
- **Evidence:** `bedrock_client.py:21-22` sets a 10s connect + 10s read timeout with 2 botocore-level retries (`retries={"max_attempts": 2, "mode": "standard"}`), and `retrieve()` (lines 109-115) can additionally issue a second logical `Retrieve` call (the empty-filter retry). In the worst case this is well above 15 seconds.
- **File and line:** `services/rag_service/app/bedrock_client.py:21-22,53-58,109-115`.
- **Reproduction (reasoning-based):** A slow-but-eventually-successful Bedrock response could cause n8n to time out and report a pipeline error even though RAG would have succeeded shortly after.
- **Smallest safe fix:** Either raise the n8n HTTP node's timeout for this call, or lower/align `bedrock_client.py`'s worst-case latency budget so it can never exceed n8n's configured timeout.
- **Regression-test recommendation:** N/A without a way to inject artificial Bedrock latency in this repo's current test setup.
- **Architecture impact:** None.
- **Approval required:** Yes (n8n timeout change) / No (Python-side change, in `rag_service`'s own file ownership).

---

## 7. Low and Informational Findings

| ID | Title | Severity | Component | Note |
|---|---|---|---|---|
| BUG-4 | `agent_enrichment` handling in `graph.py:228` is currently always `{}` — `AgentRunRequest` has no such field | Informational | langgraph_agent | Intentionally reserved for a documented future contract change (CLAUDE.md component 6); not a bug, currently inert. |
| BUG-5 | RAG passes the full, unbounded transcript as the Bedrock `retrievalQuery.text` with no length cap | Low | rag_service | Could hit a Bedrock query-length limit on an unusually long call; mapped correctly to 400 if it happens, just no proactive truncation/warning. |
| BUG-7 | `state["plan"]` accessed via direct indexing, not `.get()`, in `graph.py` | Low | langgraph_agent | Safe today (fixed linear graph topology); any future exception is still caught by the global FastAPI exception handler (500, no leak) — defensive-style note only. |
| BUG-11 | `call_signal_analyser/app/main.py` module docstring describes Phase-6-only behavior | Low | call_signal_analyser | `app/models.py`/`app/mock_rules.py` correctly document the newer uncertainty-exposure behavior; only the top-of-file docstring in `main.py` lags. |
| BUG-12 | `SERVICE_VERSION` left at `"0.1.0"` for `call_signal_analyser` and `langgraph_agent` despite real behavior changes, while `rag_service`/`guardrails_service` were bumped to `"0.2.0"` | Informational | call_signal_analyser, langgraph_agent | Versioning-discipline inconsistency, not a functional bug. |
| FE-3 | `isMockMode()` shown as a raw technical string on the Upload page | Low | frontend | Appropriate for today's demo; would need separating from end-user-facing text before a real sales-manager rollout. |
| FE-6 | Array-index React keys used for `detected_signals`/`coaching_feedback` lists | Informational | frontend | Acceptable for these specific non-reorderable display lists; not a defect in this usage. |
| DEP-4 | `FROM python:3.11-slim` is a floating minor-version tag (not `latest`, not pinned to a digest) | Low | all 4 Python Dockerfiles | Minor reproducibility risk over long time horizons. |
| DEP-6 | `pydantic` pin diverges between `langgraph_agent` (2.13.4) and the other three services (2.9.2) | Informational | dependency management | Documented and intentional (see the service's own requirements.txt comment); each service is a fully isolated image, so no real conflict. |
| DEP-7 | Frontend uses caret-range dependencies with a committed lockfile | Informational | frontend | Standard and fine as long as deploys use `npm ci`, not `npm install` — not verified which command any real deployment step uses. |
| DOC-2 | `docs/api_contracts.md`'s opening framing paragraph still describes RAG's real content as pending "Phase 12," while its own §1 section correctly says "Real implementation (Phase 12)" | Low | docs/api_contracts.md | Internal inconsistency within the same file. |
| DOC-5 | Same class of staleness as BUG-11, documentation-adjacent | Low | call_signal_analyser/app/main.py | See BUG-11. |
| DOC-8 | ChromaDB/Llama.cpp references were checked and confirmed to be correctly-framed historical/superseded context everywhere they appear | — (positive finding) | docs, README | Explicitly verified, not assumed — one apparent hit (`services/rag_service/README.md:15`, "No LangChain, no ChromaDB...") was checked in context and found to be an accurate *negation* statement, not stale drift. |
| OPS-4 | No request-correlation ID threaded through the pipeline | Low/Medium | n8n, all services | Makes cross-service log correlation for a single request harder; no functional impact observed. |
| OPS-7 | The two newly-EC2-deployed services were deployed via manual `docker build`/`run`, not via the same `docker-compose.yml` used locally | Low/Medium | deployment | Minor local/EC2 parity gap; fine for today's demo scope. |
| OPS-8 | No image versioning/rollback procedure documented for the EC2 deployments | Medium | deployment | Standard gap for a demo-stage deployment; would need addressing before a real release process. |

---

## 8. Security and Secret Scan

**Method:** pattern-based grep across the full working tree (all tracked source/text file types) for AWS access/secret key shapes, generic high-entropy API-key-looking strings, PEM/private-key headers, GitHub tokens, Google API key shapes; plus a full `git log --all -p` scan of the same patterns across all 34 commits; plus an explicit check for any commit that ever *added* a `.env`, `.pem`, `.key`, or credentials-named file.

**Result: no secrets found, in the working tree or anywhere in git history.** This is a positive, directly-verified finding, not an assumption.

**Details:**
- `.env.example` files (all four services + frontend) contain only placeholders and non-secret resource identifiers (Bedrock KB ID `EDCC0WT0OB`, S3 bucket name containing the AWS account ID `881490130721`, region, model ID) — the account ID appearing as part of a bucket name is an acceptable identifier per the task's own framing, not a secret.
- `frontend/.env` (the real, locally-created live-mode file) is correctly excluded from git via `frontend/.gitignore` (confirmed: `git status --porcelain` does not list it as untracked-but-visible; verified this session by adding the missing `.env`/`.env.*` patterns to `frontend/.gitignore`, since the pre-existing file had none at all).
- `.mcp.json` (tracked) contains only the n8n Cloud MCP server's URL (`https://xsight.app.n8n.cloud/mcp-server/http`) — an endpoint identifier, not a credential; the MCP connection itself relies on the connecting client's own authenticated session, not anything embedded in this file.
- Both n8n workflow JSON exports were checked programmatically for embedded `credentials` objects on any node — none found in either file (n8n's export format references credentials by ID/name only, never serializes the underlying secret value, confirmed for this project's exports specifically).
- `VITE_`-prefixed frontend variables (`VITE_USE_MOCK`, `VITE_N8N_WEBHOOK_URL`) are both non-secret by design — a boolean flag and a URL that is *meant* to be called by the browser bundle. Correctly not a secret-exposure risk.
- IAM: the Bedrock Knowledge Base execution role was documented (at provisioning time, per `docs/PROGRESS.md`) as scoped to model-ARN-specific `InvokeModel`, prefix-scoped S3 access, and index-scoped S3 Vectors access — **not independently re-verified this session** (would require re-fetching the live policy document via the AWS API, which was not done in this audit pass). The interactive `user10` AWS identity used for today's deployment work was observed to have EC2 write permissions (security-group modification succeeded) beyond a narrowly-scoped deploy role — this is a human developer identity, and the full attached policy was not enumerated this session. **Requires owner confirmation**, not reported as a confirmed over-privilege defect.
- Security groups: `sg-0c472b2b3bd93b3a1` (the Call Signal Analyser / LangGraph EC2 host) has ports `22, 80, 8002, 8004` open to `0.0.0.0/0` — two of these (8002, 8004) were opened by this session's own deployment work, per explicit task instruction, and are an accepted demo-scope decision (see SEC-1).
- No CORS policy is configured on any of the four FastAPI services (no `CORSMiddleware` anywhere) — not a vulnerability given the frontend never calls them directly by design, but noted for completeness.
- No authentication exists on any FastAPI service or on the n8n webhook (see SEC-1, SEC-7).

---

## 9. Dead and Unused Code Inventory

| Item | Classification | Reasoning |
|---|---|---|
| `agent_enrichment` handling in `langgraph_agent/app/graph.py:228` | **Intentionally retained** | Reserved for a documented future contract field (CLAUDE.md component 6); currently always evaluates to `{}` since `AgentRunRequest` has no such field yet. Not safe to delete — it's forward-compatibility scaffolding, not orphaned code. |
| `services/call_signal_analyser/.env.example`'s `MODEL_PATH`, `guardrails_service/.env.example`'s `NEMO_CONFIG_DIR` | **Intentionally retained placeholder** | Explicitly labeled in the file's own header as Phase 13/11 placeholders, not implemented yet. Not code, not dead — documented future config surface. |
| `services/rag_service/ingestion/*.py` (`convert_csv_to_documents.py`, `validate_documents.py`, `schema_loader.py`) | **Currently used** (indirectly) | `schema_loader.py`'s output (`metadata_schema.json`) is copied into the RAG service's Docker image (`Dockerfile:14`) and loaded at runtime by `app/filters.py:32-36` — this is load-bearing at runtime, not just dev tooling, even though the conversion/validation scripts themselves only run offline/one-time. |
| `scripts/normalize_dataset_fields.py` | **Intentionally retained (historical/audit record)** | Per `docs/PROGRESS.md`, this was an explicit one-time normalization script; its job is done and it won't be re-run in normal operation, but it documents how two CSV fields were derived — kept for reproducibility/audit trail, not accidentally orphaned. |
| Top-level directory `README.md` placeholders (`demo/`, `models/`, `data/`, `docs/`, `services/`, `frontend/`) | **Currently used** | Still serve their documented Phase-1 navigational purpose. |
| Frontend components (`App`, `Home`, `Upload`, `Results`, `ResultsView`, `GuardrailBanner`) | **Currently used** | All reachable via the router; no unused component or import found in any file read. |
| `frontend/src/index.css` | **Not exhaustively checked** | Not scanned for unused CSS classes this session — flagged as a limitation, not classified either way. |
| `n8n/workflows/phase9_iteration1_intake_to_assemblyai.json` | **Likely obsolete but needs confirmation** | Superseded by the full 16-node workflow (same underlying live workflow ID was extended, not replaced) — this earlier export may now only have historical/documentation value. Confirm with the owner before deleting, since it may be intentionally kept as a milestone snapshot. |

**Deletion-risk summary:** nothing in this inventory is safe to delete without owner confirmation; every item traced to either live runtime usage, documented forward-compatibility, or an intentional historical record.

---

## 10. Dependency Review

**Python (4 services, each fully isolated via its own Docker image):**
- `fastapi==0.115.0`, `uvicorn[standard]==0.30.6` — identical, exact-pinned across all four services.
- `pydantic`: `2.9.2` (rag_service, call_signal_analyser, guardrails_service) vs. `2.13.4` (langgraph_agent) — intentional, documented divergence (see DEP-6), not a conflict since each is a separate image.
- `boto3==1.43.21` — rag_service only, exact-pinned.
- `langgraph==1.2.9` — langgraph_agent only, exact-pinned.
- `pytest==8.3.3`, `httpx==0.27.2` — declared in the SAME `requirements.txt` as production deps in all four services, and every Dockerfile runs a single-stage `pip install -r requirements.txt` — **test packages ship inside every production image** (DEP-3, Low/Medium).
- `pip check`: no broken requirement sets (global environment only — each service's real isolation is validated via successful `docker build`, not via a local per-service venv in this session).
- **pip-audit, safety: not installed — could not run a Python vulnerability scan.** Reported as a limitation.

**JavaScript (frontend):**
- `react ^19.2.7`, `react-dom ^19.2.7`, `react-router-dom ^6.30.4` (direct); `@vitejs/plugin-react ^6.0.3`, `vite ^8.1.1`, `oxlint ^1.71.0`, `@types/react`/`@types/react-dom` (dev-only, IDE-hint use since there's no `tsconfig.json`).
- `npm audit`: **2 moderate vulnerabilities**, both in `react-router` (transitive via `react-router-dom`): an open-redirect issue (CVE-2025-68470-related) and an SSR-hydration constructor-injection issue. Fix requires a semver-major bump to `react-router-dom@7.18.1`. Practical exploitability in this app is low — no SSR is used, and no `navigate()`/`<Link to=>` call anywhere in the reviewed source uses a user-controlled target (all are hardcoded literals: `/upload`, `/results`) — but the dependency itself should be tracked (DEP-1).
- `package-lock.json` is committed; caret ranges plus a lockfile is standard/reproducible practice as long as `npm ci` is used for real deploys (not independently verified which command any deployment step actually uses).
- No TypeScript type-check exists (no `tsconfig.json` — plain JS/JSX project) — not a gap given the project's own stated stack, just noted as "nothing to run" rather than skipped.

**Docker:**
- All four Python images: `FROM python:3.11-slim` (floating minor tag, DEP-4, Low), no `USER` directive (all run as root, DEP-5, Medium), consistent `HEALTHCHECK` on all four (good), no explicit resource limits or read-only filesystem (expected gap for demo scope).

---

## 11. Test and Build Results

| Check | Command | Result |
|---|---|---|
| rag_service tests | `python -m pytest -q` (in `services/rag_service`) | **50 passed**, 24 warnings (pre-existing `StarletteDeprecationWarning`/`asyncio.iscoroutinefunction` noise from the local Python 3.14 global env, not a regression) |
| call_signal_analyser tests | same, in `services/call_signal_analyser` | **15 passed**, 15 warnings (same noise) |
| guardrails_service tests | same, in `services/guardrails_service` | **19 passed**, 12 warnings (same noise) |
| langgraph_agent tests | same, in `services/langgraph_agent` | **12 passed**, 14 warnings (same noise) |
| **Total backend** | | **96 passed, 0 failed** |
| Frontend build | `npm run build` | **Success** — 26 modules, `dist/index.html` 0.49 kB, CSS 6.07 kB gz 1.84 kB, JS 230.07 kB gz 73.63 kB, built in 938ms |
| Frontend lint | `npm run lint` (oxlint) | **Success**, exit code 0, no findings |
| Frontend type-check | N/A | No `tsconfig.json` — plain JS/JSX project, nothing to run |
| Frontend component/unit tests | N/A | **No test files exist** (`*.test.jsx`/`*.spec.jsx` — none found in `git ls-files`) — see coverage gaps below |
| `docker compose config` | `docker compose config --quiet` | Valid, no errors |
| `docker compose ps` | | All four containers still `Up ... (healthy)` from the prior session |
| `npm audit` | `npm audit --json` | 2 moderate vulnerabilities (react-router, see DEP-1) |
| `pip check` | `pip check` | No broken requirements (global env, informational only) |
| `pip-audit` | — | **Not installed — not run** |
| `safety` | — | **Not installed — not run** |
| `ruff` | — | **Not installed — not run** |

**Coverage gaps identified (no test exists for):**
- Every n8n Code node (`Parse Gemini Extraction`, `Parse AI Agent Enrichment`, `Parse Final Analysis Output`, `Router - Confidence and Category`, etc.) — zero automated test coverage of any kind; today's three real bugs (BUG-1/2/3) were all in this exact untested surface.
- Gemini response-shape variants (the flat `item.content.parts[...]` shape vs. the raw-API `item.candidates[...]` shape) — no test pins either shape.
- Truncated/`MAX_TOKENS` model output handling.
- Any frontend component (Upload form validation, Results rendering, GuardrailBanner states, mock-vs-live mode switching, error states) — zero frontend tests exist.
- Large/adversarial transcript input (prompt-injection phrasing beyond the fixed keyword list) against the actual deployed guardrails logic.
- RAG citation validation against a live (non-mocked) Bedrock response shape drift.
- Partial-pipeline-failure scenarios (e.g., RAG succeeds but Call Signal Analyser fails) at the n8n level — the FastAPI-level tests don't cover n8n's own merge/error-branch behavior.
- Large file uploads / service-unavailability scenarios end-to-end.

---

## 12. Documentation Drift

| Doc | Drift found | Which side is stale |
|---|---|---|
| `n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json` | Missing 4 real fixes + hardcoded URLs (DOC-1) | **The repo file is stale** relative to the live, verified-working workflow. |
| `docs/PROGRESS.md` | No entry for today's entire session (DOC-4) | **The doc is stale** — the implementation has moved far ahead of the record. |
| `n8n/README.md`, `n8n/SETUP.md` | Status sections describe the pipeline as stopping at transcription (DOC-9/10) | **The docs are stale** — implementation is far ahead. |
| `docs/api_contracts.md` | Opening paragraph vs. its own §1 section disagree on RAG's status (DOC-2) | **Internal drift within the same file** — the later, more specific section is correct; the framing paragraph is stale. |
| `services/call_signal_analyser/app/main.py` docstring | Describes Phase-6-only behavior (DOC-5/BUG-11) | **The docstring is stale** relative to `app/models.py`/`app/mock_rules.py` in the same service. |
| ChromaDB/Llama.cpp mentions across `docs/PROGRESS.md`, `docs/technology_decisions.md`, `README.md`, `services/rag_service/README.md` | Checked explicitly | **No drift** — every occurrence is correctly framed as historical/superseded or as an explicit negation ("no ChromaDB"). Confirmed, not assumed. |
| `docs/PROGRESS.md` Phase 11/13/14 status ("Not started") | Checked against actual code | **Accurate** — no NeMo integration, no PyTorch model, no LLM call inside LangGraph exist anywhere in the codebase. Confirmed, not assumed. |
| IP/port references in docs (`CLAUDE.md`, `README.md`, `docs/*.md`) | Searched for hardcoded IPs | **None found** — the documented architecture correctly keeps IPs out of docs (they live in `.env`/deployment config, which is the right place for them). |
| `SERVICE_VERSION` constants | `0.2.0` (rag_service, guardrails_service) vs. `0.1.0` (call_signal_analyser, langgraph_agent) despite real behavior changes in the latter two | **Versioning is stale/inconsistent**, not a documentation-content drift per se, but flagged here since it's a version-string accuracy issue. |

---

## 13. Recommended Remediation Order

1. **Re-sync the n8n workflow export** (DOC-1) — the single highest-leverage fix; everything else about the live pipeline's correctness depends on this being the actual source of truth.
2. **Add a `docs/PROGRESS.md` entry for today's session** (DOC-4) — cheap, high-value, restores the project's own audit trail.
3. **Rewrite `n8n/README.md` / `n8n/SETUP.md` status sections** (DOC-9/10) — cheap, prevents future confusion.
4. **Fix `BUG-8` (null-vs-undefined array defaults) and add an ErrorBoundary (FE-2)** — small, contained, frontend-only, removes a real (if latent) whole-page-crash risk.
5. **Add a client-side fetch timeout (BUG-10) and persist the result across refresh (BUG-9)** — small, contained, frontend-only.
6. **Decide and implement an authentication layer (SEC-1/SEC-7)** before any use beyond the current controlled demo — larger, cross-cutting, needs explicit sign-off since it touches n8n, all four services, and possibly the frontend's request headers.
7. **Address `retryOnFail`/idempotency risk on paid calls (OPS-3)** — needs an n8n workflow decision.
8. **Dependency/Docker hygiene batch:** bump `react-router-dom` (DEP-1, breaking — needs its own review), add non-root `USER` to all four Dockerfiles (DEP-5), separate test-only Python deps from production images (DEP-3).
9. **Everything in §7 (Low/Informational)** — cleanup, no urgency.

---

## 14. Items Requiring Owner Confirmation

- Whether to re-export and commit the current live n8n workflow now, or hold until a further review (DOC-1).
- Whether authentication should be added to the backend services / webhook before any wider sharing of the demo (SEC-1, SEC-7), and if so, which mechanism (shared-secret header vs. n8n native auth vs. something else).
- Whether the full IAM policy for the `user10` interactive identity and the Bedrock execution role should be re-pulled and reviewed for least-privilege as a follow-up (not done this session).
- Whether `n8n/workflows/phase9_iteration1_intake_to_assemblyai.json` should be kept as a historical milestone snapshot or removed now that it's superseded.
- Whether `react-router-dom`'s major-version bump (6.x → 7.18.1) should be scheduled given it is a breaking change, weighed against the moderate/low-practical-risk severity of the underlying CVEs in this app's specific usage.

---

## 15. Checks That Could Not Be Completed

- **pip-audit, safety, ruff**: not installed in this environment; no Python dependency-vulnerability scan or additional static-analysis pass was run. Only `pip check` (env-wide, not per-service-isolated) and manual `requirements.txt` inspection were performed.
- **Full IAM policy documents** for the `user10` AWS identity and the Bedrock execution role were not re-fetched this session; findings rely on this session's observed permissions (EC2 security-group write succeeded) and `docs/PROGRESS.md`'s existing provisioning record, respectively.
- **A full word-for-word scan of all 24 historical RAG transcripts** (`data/historical_sales_calls.csv`) for adversarial/prompt-injection-style phrasing was not performed this session.
- **`frontend/src/index.css`** was not scanned for unused CSS classes/rules.
- **Live captured runtime logs** were not reviewed for accidental PII leakage — only the logging call sites in source were reviewed (all log short labels/booleans/lengths, never full transcript text, in every file read).
- **A load/concurrency test** to independently verify the "no data leakage between concurrent requests" conclusion was not run — that conclusion rests on code-level reasoning (stateless services, no shared cache/DB) rather than an executed test.
- **n8n Cloud's own platform-level webhook body-size limit** was not independently confirmed — SEC-11-adjacent risk framed as "requires confirmation," not asserted either way.
- A literal, click-through UI test of the frontend Results page (browser automation) was not performed in this audit (no browser-automation tool available in this environment) — the frontend findings above are based on code reading, the successful `npm run build`, and the schema-match already established between the fixture and the live webhook response in the prior session.

---

## 16. Final Release-Readiness Assessment

**Not production-ready. Demo-ready, conditionally.**

The verified end-to-end behavior described as this audit's baseline is real and was independently re-confirmed today (96/96 backend tests pass, build/lint clean, no secrets anywhere, architecture rules conformant in the live system). But that verified behavior currently depends entirely on state that exists **only in the live n8n Cloud workflow** and is **not reflected anywhere in the git repository** (DOC-1, DOC-4). Today, that's a documentation gap. The moment anyone treats the repository as the deployable source of truth — a redeploy, a disaster-recovery restore, a new teammate importing the workflow — it becomes a silent regression to a broken pipeline, with no error surfaced (the pipeline still returns HTTP 200 with schema-valid, fallback-only content).

Before any use beyond the current controlled demo: close the DOC-1/DOC-4 gap, add authentication (SEC-1/SEC-7), and address the frontend robustness findings (BUG-8, FE-2) that currently rely entirely on upstream guarantees never changing.

No findings in this audit contradict or require reversing the approved architecture. No technology was found to have been silently replaced. No broad refactor is recommended — every fix above is small, contained, and mapped to a specific file and owner decision.
