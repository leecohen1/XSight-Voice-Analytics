# n8n

n8n workflow exports and orchestration documentation for XSight.

**Status:** The full 16-node pipeline (webhook intake through the confidence/category Router and the final webhook response) is built, **active**, and verified end-to-end against **real deployed services** — not just simulated test executions. The live workflow is `XSight - Full Pipeline (Nodes 1-16) - Intake to Final Analysis and Routing` (workflow ID `RBII7JvRDFWwy98x` on the connected n8n Cloud instance), exported to `workflows/phase9_16_full_pipeline_intake_to_final_analysis.json` (kept in sync with the live workflow — see `docs/PROGRESS.md`'s "Demo-day cross-phase push" entry for the synchronization record). A real submission (real synthesized speech audio, posted to the production webhook) returned a complete, schema-correct final analysis: real Gemini extraction and synthesis, grounded Bedrock RAG citations, real Call Signal Analyser and LangGraph responses from their deployed EC2 instances, and a correct Router decision. The earlier simulated-only verification (executions `15`/`16`, described below) has been superseded by this live result, not replaced as documentation — both are kept for the record. See `docs/PROGRESS.md` for the full account of four real bugs found and fixed live before this verification succeeded (a Gemini-response-shape parsing bug, an LLM-echo grounding bypass, a thinking-token/output-token misconfiguration, and the missing Gemini credential), and `docs/FULL_PROJECT_AUDIT.md` for the broader audit these fixes prompted.

Nodes 1–4 (webhook intake, pre-transcription guardrails, AssemblyAI upload/submit/poll) were already implemented and live-verified by an earlier iteration (Phase 9, Iteration 2a — see `workflows/phase9_iteration1_intake_to_assemblyai.json` for the original, simpler Iteration 1 export, kept for history; the live workflow evolved past it to add real polling before this build started). This document now covers the complete pipeline built on top of that: nodes 5–16.

## What's fully implemented (real logic, not a stub)

- **Node 5 — Post-transcription content check.** Implemented as an **inline n8n Code node** (`Post-Transcription Content Check`), not a second call to `guardrails_service`. Checked in `services/guardrails_service/app/main.py`: the real `POST /check/input` only ever runs `check_pre_transcription_input`, regardless of the `stage` field sent — there is no `post_transcription` branch. Calling it a second time with `stage: "post_transcription"` would just re-run file-presence checks against a request that has no file, and reject every submission. Per the user's explicit decision ("keep Guardrails limited to the currently working pre-transcription implementation unless the missing stages block the end-to-end flow"), this inline check reimplements the same rule set documented in `docs/api_contracts.md` (transcript non-empty/length, sales-topic keyword match, prompt-injection phrase match, a small offensive-word list) directly in the workflow. **Gap:** this is a lightweight regex/keyword check, not NeMo Guardrails — flagged in every result's `limitations` field.
- **Node 6 — IF pass/fail** on the above.
- **Node 7 — Gemini Information Extractor** (`Gemini Information Extractor`, `@n8n/n8n-nodes-langchain.googleGemini`, resource `text`/operation `message`, `jsonOutput: true`). Extraction-only prompt (customer_intent, main_objection, customer_sentiment, closing_attempt, key_sales_events, call_category) — explicitly instructed never to generate coaching feedback or a final analysis. Followed by `Parse Gemini Extraction` (Code node), which defensively parses the model's text output and clamps every field to the exact enum lists `services/call_signal_analyser` expects, so a malformed LLM response can never break downstream schema validation.
- **Node 8 — n8n AI Agent Node** (`AI Agent Node - Classify and Enrich`, same Gemini node type). Scoped strictly to classification + enrichment per CLAUDE.md's limited role: submission intent, `decision_maker_present`, `relevant_services` (default both), an enriched call category. The prompt explicitly forbids reasoning over evidence, coaching feedback, evidence reconciliation, or inventing information. **Design decision:** the actual downstream HTTP payload construction (`Prepare Downstream Payloads`) is a separate, fully deterministic Code node — the LLM's output is enrichment only, wire-format construction is never left to the model.
- **Nodes 9–10 — parallel HTTP calls** to the RAG Service (`POST /query`) and Call Signal Analyser (`POST /analyse-call`), built from `docs/api_contracts.md` sections 1 and 2 exactly (verified against the real Pydantic models in `services/rag_service` and `services/call_signal_analyser/app/models.py`, not just the docs).
- **Node 11 — Merge** (`Merge RAG and Signal Results`, combine/combineByPosition) waits for both branches.
- **Node 12 — LangGraph Agent call** (`HTTP Request - LangGraph Agent`, `POST /agent/run`), payload built from `docs/api_contracts.md` section 4 / `services/langgraph_agent/app/models.py`.
- **Node 13 — Gemini Final Analysis Chain** (`Gemini Final Analysis Chain`), a second Gemini call grounded explicitly in the extraction + RAG results + signal analysis + LangGraph's reasoning output, instructed never to invent facts and to cite `call_id`s exactly as given. Followed by `Parse Final Analysis Output`, which defensively parses the response and — regardless of what the model wrote — always appends the pipeline's own known limitations (inline guardrails, missing output guardrails, any clamped audio features, the speaker-mapping heuristic) to the `limitations` field, so it stays honest even if the model omits something.
- **Node 14 — Output guardrails: intentionally skipped**, not stubbed as a fake pass. `services/guardrails_service` does not implement `POST /check/output` yet. Rather than fabricate a `pass`, every result's `limitations` field states plainly that output guardrails were not run, and the Router (node 15) records `output_guardrails_not_implemented_skipped_check` in its internal `router_reasons` on every single request — this is a permanent, visible gap marker, not a one-time note.
- **Node 15 — Router** (`Router - Confidence and Category`, Code node). Implements CLAUDE.md's exact rule: `guardrail_status` becomes `human_review_required` when the Call Signal Analyser's `confidence < 0.65`, OR LangGraph's `evidence_conflicts` is non-empty, OR historical-call claims are missing `call_id` citations, OR the Final Analysis Chain's response could not be parsed as JSON. Otherwise `guardrail_status: pass` and `routing_category` is kept from the Final Analysis Chain (or defaulted to `human_review_required` as the category too, if that path was taken and no category was set).
- **Node 16 — Respond to Webhook** with the complete final JSON, matching CLAUDE.md's "Final output JSON schema" field-for-field.
- **Speaker tagging.** AssemblyAI's diarization returns generic `Speaker 0`/`Speaker 1` labels, not named roles. `Build Speaker-Tagged Transcript` (Code node) applies a heuristic — the first speaker to talk is assumed to be the Agent, every other distinct speaker is folded into Customer — to produce the `Agent:`/`Customer:` tagged transcript the rest of the pipeline (and the Call Signal Analyser's `agent_talk_ratio`) depends on. **This is an assumption, not a verified mapping** — recorded per-request in `pipeline_assumptions` and folded into the final `limitations` field.
- **Audio-derived features.** `call_duration_seconds` is measured from AssemblyAI's real `audio_duration`; `silence_ratio` and `speech_to_non_speech_ratio` are estimated from the gaps between AssemblyAI's utterance timestamps (a real, lightweight measurement from returned data, not a fabricated default); `speaking_rate_wpm` and `agent_talk_ratio` are computed from real word counts. **Known limitation:** `services/call_signal_analyser`'s current (mock-phase) Pydantic schema enforces narrow synthetic-dataset ranges (e.g. `call_duration_seconds` 180–900s, `silence_ratio` 0.05–0.35) inherited from `docs/dataset_design.md`. Real calls outside these bounds are clamped to the nearest bound before the request is sent, purely so the demo can complete a live call to that service — this is a stopgap, not a grounded transformation, and every clamped field is recorded in `clamped_fields` and surfaced in the final `limitations` text.
- **Error handling.** Every new HTTP/Gemini node uses `onError: continueErrorOutput` with retries; a failure at any of nodes 5–13 produces a structured `error` HTTP response (via a shared `Build Pipeline Error Response` node feeding the existing `Respond Error` node) rather than a raw n8n exception, matching CLAUDE.md's error-table row "a required upstream call fails → webhook returns an error response."

## What's stubbed, skipped, or a known gap

- **Output guardrails (`POST /check/output`) are not called** — `services/guardrails_service` doesn't implement that route yet. See node 14 above.
- **Post-transcription content guardrails are inline n8n logic, not NeMo Guardrails** — see node 5 above. No LLM-based topic/jailbreak rail runs on the transcript; only deterministic keyword/regex checks.
- **Audio-derived feature clamping** — see "Audio-derived features" above. `average_pause_duration_seconds`, `interruptions_count`, `average_pitch_hz`, `average_energy_level` are not computed at all (optional fields, correctly omitted rather than fabricated).
- **Gemini credential — resolved.** All three Gemini nodes (`Gemini Information Extractor`, `AI Agent Node - Classify and Enrich`, `Gemini Final Analysis Chain`) now have a real credential (`Google Gemini(PaLM) Api account`) attached, bound manually in the n8n editor UI (attaching it programmatically via the n8n MCP tools was attempted and failed silently, three times, isolated — a confirmed tool limitation, not a workflow issue). The model in use is `models/gemini-3.5-flash`, confirmed working against a real key (the model shown in `modelId` was updated from `gemini-2.5-flash` during the manual credential setup and is what actually ran in the verified live execution). **Known gap:** the credential *reference* cannot be read back through the n8n API for this node type at all — it will not appear in `workflows/phase9_16_full_pipeline_intake_to_final_analysis.json` even though it is genuinely attached and working live. Re-importing that file into a fresh n8n instance requires manually reattaching the credential to all three nodes, exactly as this session had to do — see `SETUP.md` section 1.
- **RAG/Call-Signal-Analyser/LangGraph reachability — resolved.** All three are deployed and confirmed reachable from n8n: RAG at `http://3.20.223.245:8001`, Call Signal Analyser and LangGraph Agent at `http://18.117.114.95:8002` and `:8004` respectively (deployed live during this session; ports opened on the host's security group via the AWS API). `guardrails_service` remains at `http://3.151.162.120:8003`. All four URLs are hardcoded directly into their respective HTTP Request nodes' `url` parameter (no `$env.*` expression remains) — see `SETUP.md` section 2 for the full mapping.

## Persistence + response contract (fixed and verified live)

Three defects were found and fixed against the live workflow while validating
the `call_data_service` persistence integration. All three are reflected in
`workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`.

1. **`Build Persistence Payload` read the wrong source.** It read
   `$json.final_output`, but its upstream node `Build Success Response - Full
   Analysis` is a Set node in `raw` mode that had *already* unwrapped that
   envelope. Every field resolved to `undefined`, `JSON.stringify` dropped
   them, and `POST /calls` received a 4-key body → **422** on the required
   `call_id` and `analysis`. It now reads the Router node directly, mints a
   contract-valid `CALL_<uuid4>` (`models.py` `LIVE_CALL_ID_RE` — `$execution.id`
   would also have been rejected), and maps `analysis` from the real final
   output. `status`, `created_at`, `attention` and `recovery_opportunity` are
   deliberately **not** sent: `call_data_service` derives them on write so the
   stored record cannot drift from the documented formula.

2. **`Respond - Full Analysis` returned the wrong object.** It answered
   `{{ $json }}`, which after the persistence node meant the webhook returned
   `CreateCallResponse` (`{call_id, key, created, overwritten}`) — or, on
   failure, a raw Axios error. `frontend/src/services/callsApi.ts` consumes a
   `PipelineResponse` envelope and needs `call_id` to route to
   `/calls/<id>`, so **Analyze Call could not complete a real upload.** The
   node now assembles the full envelope (`call_id`, `created_at`, `call_date`,
   `agent_name`, `customer_name`, `status`, `router_reasons`, `analysis`,
   `persistence`), reading the minted id from `Build Persistence Payload`, the
   analysis from `Build Success Response`, and the write result from the
   `call_data_service` call.

3. **Optional observability failed the whole run.** `HTTP Request -
   Observability Events` points at the placeholder
   `REPLACE_WITH_AI_OBSERVABILITY_SERVICE_URL` and fails `ENOTFOUND`. Its own
   note claimed `onError: continueErrorOutput`, but no `onError` was actually
   set, so the default `stopWorkflow` marked fully successful business runs as
   failed. `onError` is now genuinely set. The node runs *after* the
   persistence branch, so it never affected stored data — only execution
   status. It stays pointed at the placeholder until
   `ai_observability_service` is deployed somewhere n8n Cloud can reach.

**Export sync note.** This export is patched surgically, not re-dumped from
the n8n API. The API's workflow view is lossy for the Gemini LangChain nodes —
it drops `"role": "user"` from `messages.values` and rewrites
`builtInTools: null` to `{}` — so a wholesale re-export would commit a file
that no longer re-imports correctly. Sync individual changed fields instead.

## Verified live end-to-end runs

| Execution | Status | Result |
|---|---|---|
| `36` | error (observability only) | First green business pipeline; `CALL_a99e53c5-…` persisted, 201 |
| `38` | **success** | First run after the observability fix — confirms the fix |
| `39` | **success** | `CALL_293b515c-…` persisted |
| `40` | **success** | Envelope contract verified: all 9 `PipelineResponse` fields, `persisted: true` |

Every run used the same 61-second WAV, so the AI stages are exercised
identically. **Observed nondeterminism:** the same audio produced
`confidence 0.64 → human_review_required` on one run and `0.72 → pass` on the
next. The Router behaved correctly in both cases — this is expected AI
nondeterminism, not a defect. Demos that need to show the human-review path
should not rely on a specific confidence value being reproduced.

## Verified test runs (simulated, via n8n MCP `test_workflow`)

Both runs used realistic pinned data for the AssemblyAI/Gemini/RAG/Call-Signal-Analyser/LangGraph nodes (a 14-turn price-objection sales call transcript) and ran the real logic for every Code/Set/IF node in between — i.e. every line of new orchestration logic executed for real, only the four external services' responses were simulated.

1. **Auto-pass** (execution `15`): Call Signal Analyser confidence `0.86`, no evidence conflicts, one cited historical call → final `guardrail_status: "pass"`, `routing_category: "pricing_negotiation"`. `call_duration_seconds` was measured at 130s and clamped up to the service's 180s floor (recorded in `clamped_fields` and `limitations`); all other audio features fell naturally inside the accepted ranges.
2. **Human review required** (execution `16`): Call Signal Analyser confidence dropped to `0.42` and LangGraph reported an `evidence_conflicts` entry → final `guardrail_status: "human_review_required"`, with `router_reasons: ["call_signal_analyser_confidence_below_0.65", "langgraph_evidence_conflicts_detected", "output_guardrails_not_implemented_skipped_check"]`.

Both runs produced a complete, schema-matching final JSON (`transcript`, `call_summary`, `customer_intent`, `main_objection`, `customer_sentiment`, `call_outcome`, `agent_performance_score`, `lead_quality_score`, `similar_calls[]`, `coaching_feedback[]`, `recommended_next_action`, `suggested_follow_up_email`, `routing_category`, `confidence`, `risk_level`, `detected_signals[]`, `limitations`, `guardrail_status`).

**Note on `customer_sentiment`:** CLAUDE.md's final-output schema only allows `positive | neutral | negative` (no `mixed`), while the internal extraction/Call-Signal-Analyser schemas allow a fourth value, `mixed`. `Parse Final Analysis Output` intentionally downgrades `mixed` to `neutral` in the final output only, to satisfy the customer-facing contract — this is a deliberate mapping, not a bug.

**Superseded by a real live run.** The two simulated runs above (executions `15`/`16`) were this build's original verification, before a Gemini credential existed and before the other three services were deployed anywhere reachable. Both gaps are now closed: a real submission (real audio, real network calls to all four services, no pinned/simulated data) was run through the production webhook and returned a complete, correctly-routed final analysis (execution `21`), after four real bugs were found and fixed against this exact live workflow — see `docs/PROGRESS.md`'s "Demo-day cross-phase push" entry for the full account. The simulated runs are kept here as a historical record of the orchestration-logic verification, not as the current state of the credential/connectivity gaps they were originally testing around.

## Purpose

n8n Cloud is the central workflow orchestrator for XSight — it calls every AI component in the pipeline directly. It receives the sales call submission from the React frontend, coordinates the two-stage Guardrails Service checks and the transcription API, calls Gemini for structured semantic extraction, calls a limited-role n8n AI Agent Node for intent classification and field enrichment, calls the RAG Service and Call Signal Analyser directly (in parallel, using the payloads the AI Agent Node prepared), calls the LangGraph agent for multi-step reasoning over their merged results, calls Gemini a second time (the Final Analysis LLM Chain) to assemble the complete result, calls the Output Guardrails, and routes the response. No AI component calls another — n8n orchestrates all of it directly. See [CLAUDE.md](../CLAUDE.md#component-responsibility-boundaries) for the full responsibility split.

## All 16 nodes (final status)

1. Webhook Trigger — **implemented** (live-verified, earlier iteration)
2. Pre-Transcription File Validation HTTP Request — **implemented** (live-verified, earlier iteration; calls the real deployed `guardrails_service`)
3. IF pass/fail (file validation) — **implemented** (earlier iteration)
4. Transcription API (AssemblyAI upload/submit/poll) — **implemented** (live-verified, earlier iteration)
5. Post-Transcription Input Content Guardrails — **implemented as an inline n8n check**, not a `guardrails_service` call (see "What's stubbed" above)
6. IF pass/fail (content guardrails) — **implemented**
7. Information Extractor — Gemini — **implemented, live-verified** (real credential attached, `models/gemini-3.5-flash`)
8. n8n AI Agent Node — **implemented, live-verified** (real credential attached)
9. HTTP Request to RAG Service — **implemented, live-verified** (`http://3.20.223.245:8001`)
10. HTTP Request to Voice / Call Signal Analyser — **implemented, live-verified** (`http://18.117.114.95:8002`)
11. Merge Results — **implemented**
12. HTTP Request to LangGraph Agent — **implemented, live-verified** (`http://18.117.114.95:8004`)
13. Final Analysis LLM Chain — Gemini — **implemented, live-verified** (real credential attached, `models/gemini-3.5-flash`)
14. Output Guardrails HTTP Request — **not implemented** (service gap, not an oversight — see above)
15. Router — confidence and category routing — **implemented**
16. Respond to Webhook — **implemented**

**n8n AI Agent Node (node 8) — limited role.** Must: classify the submission intent, enrich the extracted sales fields, determine which downstream services are relevant, prepare their structured payloads. Must not: generate the final report, replace LangGraph's reasoning, generate coaching feedback, reconcile evidence, or invent missing information. Enforced here by keeping payload construction in a separate deterministic Code node (see above).

See [CLAUDE.md](../CLAUDE.md) for full node details, and `SETUP.md` for exact setup steps (credentials, environment variables, connectivity) required before a live (non-simulated) run.
