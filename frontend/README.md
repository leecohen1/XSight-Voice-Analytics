# frontend

React web application for XSight — built as part of a one-day cross-phase demo push
(frontend work normally starts at Phase 16 per `CLAUDE.md`; that gate was explicitly
overridden for today only, per user instruction, to produce a working end-to-end demo).

**Status:** minimal but functional. Covers Home, Sales Call Upload, and the Results
Page only (Analytics Dashboard and the Ollama Assistant sidebar are out of scope for
today — deferred to Phase 18 as originally planned).

## Stack

Vite + React (JS, no TypeScript) + `react-router-dom` for the three pages. No UI
component library — plain CSS in `src/index.css`.

## Running it

```bash
cd frontend
npm install
npm run dev
```

This starts the Vite dev server (prints the local URL, typically
`http://localhost:5173`). `npm run build` produces a production build in `dist/`.

## Mock vs. real mode

The app never forks its rendering code between mock and real data — both paths call
the same `analyzeCall()` function (`src/api/analyzeCall.js`) and render the result
through the same `<ResultsView />` component. Only the data source changes.

Configuration lives in `frontend/.env` (see `.env.example`):

```
VITE_USE_MOCK=true
VITE_N8N_WEBHOOK_URL=
```

- **`VITE_USE_MOCK=true`** (default): submitting the Upload form skips the network
  call entirely and returns the fixture at `src/mocks/exampleAnalysis.json` after a
  short simulated delay. Use this to demo the Results Page — including the
  `human_review_required` guardrail banner — without any backend running.
- **`VITE_USE_MOCK=false`**: submitting the form POSTs a `multipart/form-data`
  request (audio file + `agent_name`, `call_date`, optional `customer_name`/`notes`)
  to the URL in **`VITE_N8N_WEBHOOK_URL`**, and renders whatever JSON comes back
  through the same Results Page. This is the flag/URL the coordinator needs to set
  once the n8n workflow (built in parallel by a sibling workstream) is live:

  ```
  VITE_USE_MOCK=false
  VITE_N8N_WEBHOOK_URL=https://<your-n8n-instance>/webhook/<path>
  ```

  Restart `npm run dev` after changing `.env` (Vite only reads env vars at startup).

The Upload page also shows a small "Mode: Mock / Live" indicator so it's obvious
which mode is active during a demo.

## Pages

- **Home** (`/`) — one-screen project overview.
- **Upload** (`/upload`) — the submission form: audio file, agent name, call date,
  optional customer/company name, optional notes. Shows a spinner while the request
  is in flight and an inline error message if the webhook call fails (network error,
  non-2xx response, or missing `VITE_N8N_WEBHOOK_URL` in real mode).
- **Results** (`/results`) — renders every field from `CLAUDE.md`'s final output JSON
  schema: `transcript`, `call_summary`, `customer_intent`, `main_objection`,
  `customer_sentiment`, `call_outcome`, `agent_performance_score`,
  `lead_quality_score`, `similar_calls[]` (each rendered with a visible `call_id`
  citation badge), `coaching_feedback[]`, `recommended_next_action`,
  `suggested_follow_up_email`, `routing_category`, `confidence`, `risk_level`,
  `detected_signals[]`, `limitations`, and `guardrail_status`. A banner is shown at
  the **top** of the page whenever `guardrail_status` is `flagged` or
  `human_review_required` — in the latter cases the `limitations` text is shown
  inline in the banner itself, not buried at the bottom of the page.

  Reaching `/results` directly (without submitting the form first) shows a fallback
  message instead of a blank/broken page, since the result is passed via router
  state rather than persisted anywhere.

## Limitations (honest, as of today's demo build)

- **No Analytics Dashboard.** Out of scope for today per the task brief; deferred to
  Phase 18.
- **No Ollama Assistant sidebar.** Same — deferred to Phase 18.
- **Mock mode is a static fixture, not a real backend.** `src/mocks/exampleAnalysis.json`
  is one hand-written example shaped to match the schema; it does not reflect actual
  model output, actual RAG retrieval, or actual guardrail evaluation. It exists to let
  the Results Page be demoed and reviewed before the n8n workflow is live.
- **The real-webhook path is implemented but not verified against a live n8n
  instance** — the n8n workflow was being built in parallel by a sibling workstream
  at the time this was written. The `fetch`/`FormData` logic follows the documented
  contract (multipart upload in, final-output JSON out) and fails visibly if the URL
  is unset or the request errors, but the coordinator should do one live round-trip
  once both sides are ready.
- **No persistence.** The analysis result only lives in router state for the current
  session; refreshing `/results` loses it. Fine for a live demo walkthrough, not
  meant for production use.
- **Minimal styling, no design system.** Plain hand-written CSS, no component
  library, no responsive breakpoints beyond a single mobile check on the results
  grid. Today's goal was a working demo, not visual polish (explicitly the lowest
  priority for today, per the task brief).
- **No client-side validation beyond required-field checks** (file selected, agent
  name, call date). No file-size/duration/MIME checks — those are the Guardrails
  Service's job (Stage A, pre-transcription), not the frontend's.
- **No automated tests.** Verified manually via `npm run build` and a local dev
  server smoke check.
