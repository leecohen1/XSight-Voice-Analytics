# AI Observability Integration Design (Phase 1C)

**Status update (2026-07-28): implemented, success-path only, scope cut
from this document.** The wiring described below (section 4) has since
been built into the live workflow — see `docs/PROGRESS.md`'s "Langfuse
instrumentation — MVP wiring" entry for exactly what changed, what was
deliberately cut (error-path tracing, EC2 deployment, all 8 n8n stages
below narrowed to the 6 the implementation task fixed), and two real
Langfuse-SDK integration bugs found and fixed while validating against a
real account. The rest of this document is kept as the original design
record and is **not** rewritten to match the smaller implemented scope —
read it as history, and read `docs/PROGRESS.md` for current state.

**Original status: design document only. No live n8n workflow edits have
been made as part of this work.** This document maps how `ai_observability_service`
(component: standalone "AI Usage, Token, and Cost Monitoring" backend, see
`services/ai_observability_service/README.md`) would integrate with the
live n8n pipeline (`n8n/workflows/phase9_16_full_pipeline_intake_to_final_analysis.json`,
workflow ID `RBII7JvRDFWwy98x`) once that integration is actually built.
Every claim below about the current workflow's node names and shape is
taken from the committed export — no assumption is invented.

## 1. Why this is a design doc, not an implementation

Per `CLAUDE.md`'s working convention ("work on ONE phase at a time"; "if
anything is ambiguous, ask instead of inventing a solution") and the
explicit scope of this Phase 1 effort (Langfuse foundation only), this
task builds the service-side capability to *receive and serve*
observability data, but does not touch the live, already-verified,
end-to-end-tested production workflow. Wiring in a new HTTP call to a
frozen, working pipeline is a change with real blast radius (see the
"Executing actions with care" guidance this session operates under) and
belongs in its own reviewed step, not bundled silently into a backend
refactor.

## 2. What gets recorded: one trace per call, mapped to today's pipeline stages

`ai_observability_service` records one Langfuse **trace** per analyzed
call, with one **span** or **generation** observation per pipeline stage
(see `app/trace_recorder.py`). The table below maps each real node in the
current live workflow to the `pipeline_stage` name and observation kind
it would report as, if wired in:

| n8n node (live workflow) | `pipeline_stage` | Kind | `provider`/`service` | Usage signal |
|---|---|---|---|---|
| `HTTP Request - Pre-Transcription Guardrails` | `guardrails_pre_transcription` | span | `internal` / `guardrails_service` | none (deterministic) |
| `Upload Audio to AssemblyAI` + `Submit Transcription Job` + `Poll AssemblyAI Transcript Status` | `transcription` | generation | `assemblyai` / `transcription` | `audio_duration_seconds` |
| `Post-Transcription Content Check` | `guardrails_post_transcription` | span | `internal` / `guardrails_service` | none |
| `Gemini Information Extractor` | `information_extraction` | generation | `gemini` / `generative_ai` | `input_tokens`/`output_tokens` |
| `AI Agent Node - Classify and Enrich` | `ai_agent_enrichment` | generation | `gemini` / `generative_ai` | `input_tokens`/`output_tokens` |
| `HTTP Request - RAG Service` | `rag_retrieval` | span | `internal` / `rag_service` | none (Bedrock `Retrieve`, deterministic template — see `CLAUDE.md` component 3) |
| `HTTP Request - Call Signal Analyser` | `call_signal_analysis` | span | `internal` / `call_signal_analyser` | none |
| `HTTP Request - LangGraph Agent` | `langgraph_reasoning` | span (until an LLM backend is chosen — `CLAUDE.md` Phase 14 TBD) | `internal` / `langgraph_agent` | none today |
| `Gemini Final Analysis Chain` | `final_analysis` | generation | `gemini` / `generative_ai` | `input_tokens`/`output_tokens` |
| `Router - Confidence and Category` | `routing` | span | `internal` / `router` | none |

A stage is only ever recorded as a **generation** if it names a model
*and* has a measurable usage signal (see `app/trace_recorder.py`'s
`_is_generation`) — every deterministic stage above (guardrails, RAG,
signal analysis, routing, and LangGraph until it gets an LLM backend) is
a **span**, so a deterministic step is never mis-recorded as a priced LLM
call.

## 3. Trace-ID propagation

- **Trace identity = `call_id`.** `ObservabilityClient.create_trace_id(seed=call_id)`
  (`app/langfuse_client.py`) derives a stable, deterministic trace ID from
  whatever `call_id` the caller supplies — the same `call_id` always maps
  to the same trace, whether Langfuse is enabled or not (a local
  SHA-256-derived fallback ID is used when disabled). Today's live
  workflow does not yet mint or thread a `call_id` through its nodes — see
  gap analysis (section 5).
- **Correlation with n8n's own execution ID.** `TraceIngestRequest.workflow_execution_id`
  is recorded into `trace_metadata.n8n_execution_id` (see
  `app/trace_recorder.py`'s `record_call_trace`), so a Langfuse trace can
  always be cross-referenced back to the exact n8n execution that produced
  it — the same execution ID already used throughout `docs/PROGRESS.md`'s
  "demo-day" entry (e.g. execution `21`) to tie a workflow run to its
  outcome.
- **One request per call, not one per node.** The design is a single
  `POST /observability/events` call carrying every stage's event in one
  batch (`TraceIngestRequest.events: list[dict]`), issued once near the end
  of the workflow — not one HTTP call per node. This keeps the number of
  new HTTP calls against the live pipeline to exactly one, regardless of
  how many stages exist.

## 4. Where the new call would go, and why (not yet implemented)

**Proposed integration point:** a new node in parallel with
`Build Success Response - Full Analysis` / `Build Pipeline Error Response`
— reading from whichever branch actually executed — that assembles the
accumulated per-stage events (timing, token counts already available on
each HTTP Request/Gemini node's own response, status) and makes exactly
one `POST /observability/events` call, with `onError: continueErrorOutput`
(matching this workflow's existing error-handling convention for every
other external call — see `docs/PROGRESS.md`'s Phase 9 iteration 2a entry).
This mirrors the same pattern already used for
`Respond - Full Analysis`/`Respond Error`: a telemetry write must never
delay or break the user-facing response.

**Why this is not implemented yet, concretely:**
1. **No `call_id` currently exists in the live workflow.** The webhook
   payload accepts `agent_name`/`call date`/audio file (see `CLAUDE.md`'s
   upload form fields) but the workflow has no minted per-submission
   identifier today — introducing one is itself a small, separate,
   reviewable change to the frozen workflow, not something to fold in
   silently here.
2. **Per-stage timing/token data is not yet collected into one place.**
   Each `HTTP Request`/Gemini node's response is available at that point
   in the graph, but nothing in the current workflow accumulates it across
   branches (especially across the parallel RAG/Call-Signal-Analyser
   branches and the `Merge RAG and Signal Results` join) into the single
   event array `POST /observability/events` expects.
3. **No real Langfuse account exists yet** (see the service's own README,
   "Known limitations") — wiring in the call before there is anywhere for
   the data to actually go would only add a network dependency to the
   live pipeline for no observable benefit, and the disabled-mode
   fallback (recording nothing, returning a local deterministic trace ID)
   would be the only thing ever exercised.

## 5. Payload contract (what the new n8n node would send)

Using the real node/stage names from section 2, a fully wired call would
look like this — this exact shape already matches
`TraceIngestRequest`/`ValidatedEvent` (`app/models.py`, `app/validation.py`)
as built and tested in this phase; no schema change would be needed to
adopt it:

```json
{
  "call_id": "<to be minted by a future workflow change>",
  "workflow_execution_id": "{{$execution.id}}",
  "trace_metadata": {
    "environment": "production",
    "workflow_version": "<n8n workflow versionId>",
    "final_status": "pass | human_review_required | error",
    "use_case": "analyze_sales_call"
  },
  "events": [
    {
      "idempotency_key": "{{$execution.id}}:information_extraction",
      "provider": "gemini",
      "service": "generative_ai",
      "model": "gemini-3.5-flash",
      "pipeline_stage": "information_extraction",
      "use_case": "analyze_sales_call",
      "input_tokens": 512,
      "output_tokens": 210,
      "total_tokens": 722,
      "audio_duration_seconds": null,
      "request_count": 1,
      "latency_ms": 1840,
      "status": "success",
      "occurred_at": "2026-07-27T12:03:11Z",
      "metadata": {}
    }
  ]
}
```

`metadata` on each event is passed through `app/metadata_safety.py`'s
allow-list — only the keys already enumerated there (e.g.
`filter_applied`, `results_returned`, `human_review_required`,
`risk_level`) would ever reach Langfuse; anything else (transcript
snippets, customer names, raw provider errors) is stripped, never sent.

## 6. Explicitly out of scope for this document

- Actually creating a Langfuse account/project and populating
  `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`.
- Minting a `call_id` in the live workflow.
- Adding the accumulator + `POST /observability/events` node to the live,
  frozen, already-demo-verified workflow.
- Building the "AI Usage & Cost" React dashboard page that would consume
  `GET /observability/*`.

Each of the above is a separate, reviewable follow-up step, to be executed
only with explicit approval — consistent with this session's scope
("Phase 1C: write integration design doc ... no live n8n edits").
