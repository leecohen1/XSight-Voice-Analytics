# frontend

React web application for XSight — the persistent AI sales-call intelligence
product described in `CLAUDE.md`. This is the **Frontend Foundation** build:
application shell, design tokens, domain types, a mock-isolated API layer,
and polished page shells for every confirmed product area, including Ask
XSight. It supersedes the earlier one-day demo build (Home/Upload/Results,
plain JS, no design system) described in this file's previous revision.

## Stack

Vite + React 19 + TypeScript, `react-router-dom` for routing. Styling is
plain CSS: one global design-token file (`src/styles/tokens.css`) plus
per-component **CSS Modules** — no styling framework, no icon library, no
chart library, no state-management library. See "Why no framework/library
X" below for the reasoning.

## Running it

```bash
cd frontend
npm install
npm run dev        # Vite dev server, http://localhost:5173
npm run build       # production build → dist/
npm run lint        # oxlint
npm run typecheck   # tsc --noEmit
```

## Mock vs. real mode

Configuration lives in `frontend/.env` (see `.env.example`):

```
VITE_USE_MOCK=true
VITE_N8N_WEBHOOK_URL=
```

Every page reads data exclusively through `src/services/*Api.ts` — never
directly from `src/data/mock*.ts` and never via a raw `fetch` call. Each API
module checks `isMockMode()` (`src/services/config.ts`) internally:

- **`callsApi.uploadCall`** is the one function with a real implementation:
  in real mode it POSTs a `multipart/form-data` request (audio file + form
  fields) to `VITE_N8N_WEBHOOK_URL` and wraps the response into a
  `CallRecord`. This is ported from the original demo build's working
  `analyzeCall.js`.
- **Every other function** (`listCalls`, `getCall`, `getOverview`,
  `getTeamIntelligence`, `getUsageSummary`, `getQualitySummary`,
  `askCallQuestion`, ...) throws a clear `"no backend contract exists
  yet"` error in real mode rather than silently returning mock data or
  nothing — there is no persistence/analytics/cost/RAGAS/Ask-XSight
  backend yet, and pretending otherwise would be misleading. Set
  `VITE_USE_MOCK=true` (the default) to use them.

This means the UI never has an `if (mock) {...} else {...}` branch — the
branching lives once, inside each API module.

## Persistent call history (mock mode)

`src/data/mockCallStore.ts` is an in-memory, module-singleton "database"
seeded from `src/data/mockCalls.ts` (11 realistic calls covering every
required state: clean sale, no sale, follow-up needed, unresolved price
objection + human review, an evidence conflict, a flagged output, failed
transcription, in-progress processing, a high-cost long call, a
high-quality RAGAS evaluation, and a weak-faithfulness RAGAS evaluation).
Submitting Analyze Call writes a new record into this store and — in mock
mode — `callsApi.runMockProcessing` advances it through
`uploaded → validating → transcribing → analyzing → completed` with
realistic delays, so Calls and Call Details reflect it immediately. This
resets on a full page reload (no `localStorage`/backend) — intentional for
this phase, documented rather than hidden.

## Ask XSight

Implemented per `CLAUDE.md` §9: a floating "Ask XSight" action inside Call
Details (never in primary navigation, never auto-opened) opening a
contained side panel (bottom sheet on mobile). `src/features/ask-xsight/useAskXsight.ts`
drives the full state machine (closed/open/loading/answered/not enough
evidence/error). `src/services/askXsightApi.ts` is mock-only: it builds
every answer from the selected call's *actual* stored fields (never
free-floating text), refuses to simulate a write-back to the official
analysis ("change the outcome to Sale" → an explicit `unsupported_request`
error), and falls back to "Not enough evidence" for anything it can't
ground. This mirrors the real grounding rule the future backend will need
to enforce, not just its visual shape.

## Design tokens & "AI Command Center" direction

`src/styles/tokens.css` defines every color, spacing, radius, shadow,
typography, and motion value as a semantic CSS custom property
(`--color-status-review`, `--space-4`, `--radius-lg`, ...). Components
never hardcode a raw color. The product commits to a **single dark theme**
(no light/dark toggle) — see "Design-quality notes" below.

## Folder structure

```
src/
  types/       Domain types — call.ts, team.ts, aiOperations.ts, askXsight.ts, api.ts, overview.ts
  data/        Centralized mock fixtures (mockCalls, mockTeam, mockAiOperations, mockAskXsight) + mockCallStore
  services/    API abstraction — callsApi, analyticsApi, teamApi, aiOperationsApi, askXsightApi, config, httpClient
  components/  layout/ ui/ icons/ charts/ calls/ call-details/ ask-xsight/
  features/    ask-xsight/useAskXsight.ts
  pages/       Overview, AnalyzeCall, Calls, CallDetails, TeamIntelligence, AiOperations, Settings
  styles/      tokens.css, base.css
```

## Routes

`/overview` (landing redirect target) · `/analyze` · `/calls` ·
`/calls/:callId` · `/team` · `/ai-operations` · `/settings`. Ask XSight has
no route — it only exists inside `/calls/:callId`.

## Why no framework/library X

- **No Tailwind / CSS-in-JS**: the existing app already used plain CSS
  successfully; CSS Modules (native to Vite) give the same component-scoped
  styling without a new dependency.
- **No icon library**: the product's icon vocabulary is small and stable
  (`src/components/icons/`, ~20 hand-rolled inline SVGs) — smaller and more
  consistent than pulling in a general-purpose set.
- **No chart library**: every chart in this phase is "one trend line"
  (`src/components/charts/TrendSparkline.tsx`, ~50 lines of SVG). A
  charting library would be scope creep for that.
- **No Redux/Zustand**: page-local `useState`/`useEffect` plus the
  module-singleton mock store cover this phase's state needs.

## Design-quality notes

- **Single dark theme, not a toggle.** The approved direction ("AI Command
  Center with restrained 3D elements") specifies one committed look. A
  toggle would double the visual-QA surface of every component for no
  product requirement in this phase.
- **Official analysis vs. Ask XSight**: Call Details always renders
  "Official XSight Analysis · Validated pipeline output" as the dominant,
  first-rendered section; Ask XSight is opened by explicit action, appears
  in a secondary panel, and is visually distinct (chat bubbles vs. section
  cards).
- **Not enough evidence** and **human review** are treated as first-class,
  designed states (not error styling) — see `HumanReviewBanner` and
  `AskXsightNotEnoughEvidence`.
- **AI Usage & Cost** types (`src/types/aiOperations.ts`) are deliberately
  shaped to align with the parallel `services/usage_monitoring_service`
  workstream's real response models, as a coordination reference for
  whoever wires up the real adapter later — this frontend does not call
  that service.

## Known limitations (honest, as of this phase)

- **No backend for anything except `uploadCall`.** Every other API method
  is mock-only, with the missing contract documented in the corresponding
  service file's comments.
- **No persistence beyond the browser tab.** The mock call store resets on
  reload.
- **No automated tests.** No test framework exists yet; adding one is out
  of this phase's scope.
- **No authentication.**
- **Team Intelligence and AI Operations have no per-agent/per-call live
  linkage beyond mock fixtures** — numbers are illustrative, clearly
  labeled as estimates where the product requires it (cost, RAGAS).
