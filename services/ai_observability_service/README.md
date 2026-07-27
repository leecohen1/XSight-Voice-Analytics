# ai_observability_service

AI Usage, Token, and Cost Monitoring — Phase 1 (backend only).

## Purpose

Records one Langfuse trace (with nested span/generation observations) per
analyzed call, and serves frontend-safe, product-specific aggregation
endpoints that combine Langfuse-measured LLM usage/cost with locally
configured fixed infrastructure cost. This service is the standalone
persistence + aggregation backend for the "AI Usage & Cost" dashboard
planned in `CLAUDE.md` (component 1, "Analytics Dashboard"). It is not
wired into the main n8n pipeline yet, and does not touch the frontend —
see "Known limitations" below.

## Architecture decision: why Langfuse, not a local `usage_events` table

This service was originally built (and named `usage_monitoring_service`)
around a local SQLite `usage_events` table: the pipeline would `POST` one
row per measured usage event, and this service's own SQL aggregated them.
That table has been **removed** and replaced with a Langfuse-backed
design:

- **Langfuse is now the single source of truth for per-event token/cost/
  latency telemetry** (traces, spans, generations, measured usage, cost).
  This service no longer stores or aggregates that data itself — it
  records it into Langfuse and reads it back out through Langfuse's own
  Metrics/Observations/Scores APIs.
- **`pricing_config` and `infrastructure_cost_config` are unchanged.**
  Langfuse has no equivalent for either: `pricing_config` still computes
  the `cost_details` this service *sends to* Langfuse per generation (no
  provider price is hardcoded anywhere in this codebase); fixed
  infrastructure cost (EC2, the n8n subscription, etc.) has no Langfuse
  concept at all — it runs regardless of call volume and remains entirely
  XSight-owned.
- **The product-facing API contract does not change.** The read endpoints'
  response shapes (`UsageSummaryResponse` and friends in `app/models.py`)
  keep their exact prior field names — only *where the numbers come from*
  changed, not what the frontend will eventually receive.

**Current status: foundation only, not live-integrated.** No real Langfuse
account has been created as part of this work. `LANGFUSE_PUBLIC_KEY` /
`LANGFUSE_SECRET_KEY` are unset placeholders in `.env.example`, and every
code path in this service is written to behave correctly — never crash,
never fabricate a number — whether or not those credentials are ever
configured (see `app/langfuse_client.py`'s "disabled mode"). The
Metrics/Observations API calls in `app/langfuse_query_adapter.py` are
structurally ready against the current, confirmed Langfuse Python SDK v4
API surface, but have never been exercised against a real Langfuse
project — see "Known limitations."

## Cost terminology (read this before trusting any number from this service)

| Term | Meaning |
|---|---|
| **Measured usage** | A quantity a provider actually returned (token counts, audio duration) or the pipeline actually recorded (request count, latency), as recorded into Langfuse. Never fabricated — a value this service couldn't measure is passed through as `null`, never `0`. |
| **Estimated variable cost** | `measured usage × a configured price`, computed by `app/pricing.py` at write time and sent to Langfuse as `cost_details`. An estimate derived from real usage and a price you entered — not a number the provider returned, and never a real invoice. |
| **Allocated fixed infrastructure cost** | A *share* of a fixed monthly cost (EC2, n8n subscription, etc.) that runs regardless of call volume. Attributing part of it to "this call" or "this day" is an accounting allocation, not a cost that call actually caused. |
| **Estimated total cost** | Estimated variable cost + allocated fixed cost. Still an estimate, still not an invoice. |

Every cost-bearing response from this service is a **decimal string**, not
a float — the whole point of using `Decimal` internally is to preserve
exact precision (a single Gemini call can cost a fraction of a cent);
returning a JSON float would reintroduce binary-float rounding at the API
boundary. Consumers should parse these as decimals, not implicitly coerce
them through JS/Python float arithmetic.

## Architecture

Follows the exact conventions of the other four XSight services: plain
FastAPI + Pydantic, no ORM, the same structured error shape
(`{"error": {"code","message","details"}}`), the same `GET /health`
contract, the same `conftest.py`/`Dockerfile`/`.env.example` layout.

Local persistence is **SQLite** (stdlib `sqlite3`, no ORM), now holding
only `pricing_config` and `infrastructure_cost_config` — per-event
telemetry lives in Langfuse, not this database. Money is stored as
`Decimal`-parseable `TEXT`, never `REAL`/float.

```
app/
  main.py                   FastAPI app, routes, error handlers, health
  config.py                 env-var settings (DB path, batch limit, log level, Langfuse)
  db.py                     SQLite connection + schema (pricing_config, infrastructure_cost_config)
  models.py                 Pydantic request/response schemas
  validation.py             per-event manual validation (see design note below)
  metadata_safety.py        allow-listed metadata keys for anything sent to Langfuse
  langfuse_client.py        the ONLY module that touches the Langfuse SDK directly
  langfuse_query_adapter.py read-path: normalizes Langfuse API responses into XSight's contract
  trace_recorder.py         write-path orchestrator: composes langfuse_client + pricing.py
  pricing.py                pricing selection + Decimal cost formulas
  time_utils.py             UTC period-boundary helpers
  repository.py             fixed infrastructure cost allocation queries (unchanged)
tests/                      129 tests across 8 files
conftest.py                 isolated temp-SQLite-db fixtures + fake Langfuse client/query-client fixtures
```

**Design note — why `events` in the write API is a list of raw dicts, not
a strict Pydantic model:** Pydantic validates a list field as a single
unit, so a strict per-item model would reject an entire batch (422) the
moment *any one* event has a missing field or a bad value. That directly
conflicts with the requirement that one invalid event must not corrupt the
rest of the batch. Instead, each event dict is validated by hand in
`app/validation.py`, so a bad event becomes one rejection entry in the
response while the rest of the batch is still processed.

## Write path: `POST /observability/events`

One request records one call's full trace. `app/validation.py` validates
each raw event dict independently (bad events are rejected individually,
never the whole batch); `app/trace_recorder.py` then, for each validated
event:

1. Looks up active pricing (`app/pricing.py`, unchanged) and computes
   `cost_details` when possible — `None`, never `0`, when pricing is
   missing.
2. Classifies the event as a Langfuse **generation** (has both a `model`
   name and a usage signal — tokens or audio duration) or a **span**
   (every other stage: guardrails, routing, deterministic scoring/
   reasoning). A stage named with a model but no usage signal is still
   recorded as a span, never mis-recorded as a priced generation.
3. Records it via `app/langfuse_client.py`, nested under one deterministic
   trace per `call_id` (`ObservabilityClient.create_trace_id(seed=call_id)`
   — the same `call_id` always maps to the same trace ID, whether or not
   Langfuse is enabled).

The response reports `trace_id`, `observability_enabled`,
`recorded_stage_names`, and any `rejected` events with per-item reasons —
there is no local per-event row `id` anymore (see architecture decision
above).

## Read path: `GET /observability/*`

Each read endpoint calls `app/langfuse_query_adapter.py`'s
`LangfuseQueryClient` (Langfuse's Metrics/Observations APIs) and passes the
result through a `normalize_*()` function that reshapes it into XSight's
stable product contract, combined where relevant with the locally-owned
`infrastructure_cost_config` allocation (`app/repository.py`). Every
response includes `observability_enabled: bool` so a consumer can tell
"zero usage this period" apart from "Langfuse isn't configured yet."

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Standard health check |
| POST | `/observability/events` | Record one call's trace (spans/generations) |
| GET | `/observability/summary` | Token/cost KPI rollup for a period |
| GET | `/observability/daily` | Daily token/cost buckets |
| GET | `/observability/by-stage` | Breakdown by `pipeline_stage` |
| GET | `/observability/by-provider` | Breakdown by `provider` |
| GET | `/observability/calls` | Paginated, filterable call-level list |
| GET | `/observability/calls/{call_id}` | Full event breakdown for one call |
| GET | `/observability/cost-breakdown` | Variable vs. allocated-fixed vs. total, explicitly separated |

All `GET /observability/*` endpoints accept `range=today|month` and/or
explicit `from`/`to` (ISO 8601; `from`/`to` win if both are given), and
compute periods in **UTC only** — never the server's local timezone.
Ranges are half-open: `[period_start, period_end)`.

The old `/usage/*` paths have been removed, except `GET /usage/summary`,
kept only as a **deprecated, undocumented** alias of
`GET /observability/summary` for any in-flight caller still using the old
path (`deprecated=True, include_in_schema=False` — it does not appear in
the OpenAPI schema and should not be used by new integrations).

## Environment variables

See `.env.example`. `AI_OBSERVABILITY_DB_PATH` (default
`./data/ai_observability.db`), `MAX_EVENTS_PER_BATCH` (default `100`),
`LOG_LEVEL` (default `INFO`), and the Langfuse block
(`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`,
`LANGFUSE_ENVIRONMENT`, `LANGFUSE_RELEASE`, `LANGFUSE_TIMEOUT_SECONDS`) —
all optional; observability is "enabled" only when both keys are present.

## Running locally

```bash
cd services/ai_observability_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8005
```

## Running via Docker

```bash
docker build -t xsight-ai-observability-service services/ai_observability_service
docker run -p 8005:8005 -v "$(pwd)/services/ai_observability_service/data:/service/data" xsight-ai-observability-service
```

Or via the root `docker-compose.yml` (`docker compose up ai_observability_service`)
— the database file persists at `services/ai_observability_service/data/`
via a bind mount, and is gitignored.

## Testing

```bash
cd services/ai_observability_service
pytest -v
```

129 tests across 8 files. Persistence tests use an isolated temporary
SQLite file (`tmp_path` fixture) — no test ever reads or writes the real
configured database. Langfuse-touching tests mock the SDK entirely (see
`conftest.py`'s `FakeObservabilityClient`/`FakeQueryClient` and
`tests/test_langfuse_client.py`) — **zero network calls, zero real Langfuse
account required to run this suite.**

## Privacy constraints

Any metadata sent to Langfuse (trace-level or observation-level) is
allow-listed (`app/metadata_safety.py`) to a small, fixed set of
structured signal keys already visible elsewhere in this project's own API
contracts (e.g. `filter_applied`, `results_returned`,
`decision_maker_present`). Any other key is silently **stripped**, not
sent — the rest of the event is still recorded, just without the
disallowed key. This service never sends transcripts, prompts, customer
names/email/phone, raw model responses, credentials, or API keys to
Langfuse, by construction — there is no allow-listed field for free-text
call content.

## Known limitations

- **No real Langfuse account exists yet.** `LANGFUSE_PUBLIC_KEY`/
  `LANGFUSE_SECRET_KEY` are unset; every code path runs in "disabled mode"
  in this repository's current state. `app/langfuse_query_adapter.py`'s
  `fetch_metrics`/`fetch_observations`/`fetch_scores` are structurally
  built against the current documented Langfuse Python SDK v4 API surface
  but are **not yet live-verified** against a real project.
- **No real pricing data is seeded.** `pricing_config` and
  `infrastructure_cost_config` are empty until populated with real,
  cited provider prices (a manual data-entry step, deliberately kept
  separate from this phase per the "do not hardcode pricing" constraint).
- **`estimated_variable_cost_usd` is not yet derivable from a mocked/
  disabled Langfuse connection** on the read side — it is explicitly
  `None` (never fabricated as `0`) in every read endpoint's response today,
  pending live Langfuse integration; only `allocated_fixed_cost_usd` (from
  the still-locally-owned `infrastructure_cost_config`) is populated.
- **Not wired into the n8n workflow yet.** This is a standalone backend
  service only. The frozen main analysis workflow does not call
  `POST /observability/events` — that integration is designed (see
  `docs/ai_observability_integration_design.md`, Phase 1C) but not yet
  implemented against the live workflow. **Do not treat n8n integration as
  complete** — it does not exist yet.
- **RAGAS is not implemented.** The schema (`use_case`, `pipeline_stage`
  as free-form-but-conventioned strings) is deliberately generic enough to
  accept a future RAGAS evaluation run as just another `provider`/`service`
  value, but no RAGAS-specific code exists here yet.
- **No frontend.** The "AI Usage & Cost" React page is a separate,
  not-yet-started piece of work.
- **SQLite, single-writer.** Appropriate for this project's actual scale;
  would need reconsideration under real concurrent multi-writer load. Only
  applies to the two remaining locally-owned tables — Langfuse's own
  storage is out of this project's control.
- **`GET /observability/cost-breakdown`'s `allocation_method=per_call_share`**
  divides the period's fixed cost across *distinct calls in that period*,
  not a fixed number decided in advance — if call volume is unusually low
  in a given period, the per-call share for that period will be
  correspondingly higher. This is a documented, deliberate MVP behavior,
  not a bug.
- **One combined cost figure per stage, not split by usage type.**
  `app/trace_recorder.py`'s `cost_details` sends a single `"total"` key;
  Langfuse's own worked examples support splitting cost per usage-type key
  (e.g. input/output separately) — this project computes one combined
  figure via `app/pricing.py` today. An intentional MVP simplification,
  not a defect.

## Integration design (Phase 1C)

See `docs/ai_observability_integration_design.md` for the planned n8n
integration map, trace-ID propagation strategy, and payload contracts —
a design document only; no live n8n workflow edits have been made as part
of this work.
