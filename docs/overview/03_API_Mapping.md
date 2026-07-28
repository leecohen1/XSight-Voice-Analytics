# Overview — API Contracts and Field Mapping

Authoritative reference for the stored schema, the endpoints, the
aggregation rules, and the deterministic attention formula.

## 1. Stored S3 record

`s3://<bucket>/xsight/application/analyzed-calls/v1/year=YYYY/month=MM/day=DD/<call_id>.json`

```json
{
  "schema_version": "1.0",
  "call_id": "CALL_001 | CALL_<uuid4>",
  "source": "historical_seed | live_analysis",
  "created_at": "2026-07-27T09:00:00Z",
  "call_date": "2026-07-27",
  "agent_name": "Sarah Levi",
  "agent_name_normalized": "sarah levi",
  "customer_name": "Northwind Solutions | null",
  "status": "completed | flagged | human_review_required",
  "router_reasons": ["..."],
  "analysis": {
    "transcript": "...",
    "call_summary": "...",
    "customer_intent": "...", "main_objection": "...",
    "customer_sentiment": "positive | neutral | negative | null",
    "call_outcome": "Sale | No Sale | Follow-up Needed | Uncertain | null",
    "agent_performance_score": 4, "lead_quality_score": 5,
    "similar_calls": [], "coaching_feedback": ["..."],
    "recommended_next_action": "...", "suggested_follow_up_email": "",
    "routing_category": "...", "confidence": null, "risk_level": null,
    "detected_signals": ["..."], "limitations": "...",
    "guardrail_status": "pass | flagged | human_review_required",
    "attention": {
      "required": true, "priority": "low|medium|high|critical",
      "priority_score": 0, "category": "...", "reason": "..."
    },
    "recovery_opportunity": {
      "detected": true, "confidence": null, "reason": "...",
      "recommended_offer": "...", "recommended_follow_up_window": "within_3_days"
    }
  }
}
```

`agent_name_normalized` is always re-derived from `agent_name` on write; a
caller-supplied value is ignored, so two records for one agent can never
disagree and split an aggregate.

**Null is meaningful.** A value never measured is `null`, never a fabricated
default. Seeded records carry `confidence: null` and `risk_level: null`
because the corpus never produced them, and `similar_calls: []` because no
RAG retrieval runs during seeding.

## 2. Endpoints (`call_data_service`, port 8006)

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | `{status, service, version}` |
| POST | `/calls` | 201. Idempotent by `call_id`. Re-derives attention/recovery server-side. |
| GET | `/calls` | `limit, cursor, agent_name, status, source, from_date, to_date`. Summaries only (no transcripts). |
| GET | `/calls/{call_id}` | Full record incl. transcript. 404 if absent. |
| GET | `/overview?period=7d\|30d` | The whole screen, pre-aggregated. |

Errors: `{"error": {code, message, details}}` — never a bucket name, object
key, AWS error code, or credential.

| Status | Codes |
|---|---|
| 404 | `CALL_NOT_FOUND` |
| 422 | `VALIDATION_ERROR`, `MALFORMED_RECORD` |
| 500 | `INTERNAL_ERROR`, `STORAGE_KEY_REJECTED` |
| 503 | `SERVICE_MISCONFIGURED`, `STORAGE_UNAVAILABLE` |

## 3. `GET /overview` response

Top level: `period`, `generated_at`, `executive_summary`, `kpis`,
`close_rate_trend`, `improved_agents`, `attention_calls`, `recent_calls`,
`data_quality`.

Each KPI: `current_value`, `previous_value`, `absolute_change`,
`percentage_change`, `trend_direction`.

KPIs: `calls_analyzed`, `close_rate`, `average_agent_performance`,
`average_lead_quality`, `calls_requiring_attention`, `improved_agents_count`.

## 4. Aggregation rules

| Rule | Definition |
|---|---|
| Calls analyzed | Records with status `completed`, `flagged`, or `human_review_required` |
| Close rate | `Sale / calls-with-a-known-outcome × 100`. **`Uncertain` excluded from the denominator.** Matching is case-insensitive; output stays canonical. `null` when no outcome is known. |
| Avg. agent performance | Mean of non-null `agent_performance_score`. `null` if none scored. |
| Avg. lead quality | Mean of non-null `lead_quality_score` |
| Calls requiring attention | Count of `analysis.attention.required == true` |
| Improved agents | ≥2 calls in **each** period, and `current_avg − previous_avg ≥ 0.2`. Grouped by trimmed, case-insensitive name; display name is the most recent real spelling. |
| Attention sorting | `priority_score` DESC, then `created_at` DESC |
| Recent calls sorting | `created_at` DESC |
| `percentage_change` | `null` when the previous value is 0 or unknown — an undefined ratio is reported as undefined, never as 0 or 100 |
| `improved_agents_count.previous_value` | Always `null` — there is no third window to compare against, so the trend is honestly `unknown` |

### Comparison windows (UTC)

```
current  = [now - N days, now]          <- INCLUSIVE of now, and so of today
previous = [now - 2N days, now - N days) <- half-open at its end
```

They are contiguous (`previous_end == current_start`), never overlap, and
leave no gap. A call landing exactly on the boundary belongs to the current
window only. `N` is 7 or 30. **The current day is inclusive.**

### Trend buckets

The current window is split into exactly 4 contiguous, non-overlapping
buckets by duration (not calendar weeks), so 7d and 30d split identically.
Every bucket is half-open `[start, end)` except the last, which closes on the
window end so the final instant is never dropped. Each call falls in exactly
one bucket (asserted by test).

## 5. Deterministic attention

Implemented in `services/call_data_service/app/attention.py` and mirrored in
the n8n Router node. Both produce identical output for identical input.

### Precedence — first match wins, most severe first

| # | Category | Condition |
|---|---|---|
| 1 | `evidence_conflict` | A router reason marks an evidence conflict |
| 2 | `human_review` | `guardrail_status == human_review_required`, a human-review router reason, **or** `follow_up_needed && !next_meeting_scheduled` |
| 3 | `critical_coaching` | `agent_performance_score <= 2` |
| 4 | `customer_dissatisfaction` | `customer_sentiment == "negative"` |
| 5 | `recoverable_opportunity` | `lead_quality_score >= 4 && call_outcome != "Sale"` |
| 6 | `low_priority` | Nothing matched → `required = false` |

A call frequently matches several rules at once. Ranking by *who must act and
how urgently* — system conflict, then human-review obligation, then coaching,
then customer risk, then revenue upside — keeps the single reported category
the most actionable one rather than whichever rule was evaluated first.

### Priority score (0–100 integer)

```
score = category_base + modifiers, clamped to [0, 100]

category_base:
  evidence_conflict 70 | human_review 60 | critical_coaching 55
  customer_dissatisfaction 45 | recoverable_opportunity 40 | low_priority 0

modifiers (only when a category other than low_priority matched):
  lead_quality_score == 5                       +15
  lead_quality_score == 4                       +10
  agent_performance_score <= 2                  +10
  risk_level == "High"                          +10
  risk_level == "Medium"                         +5
  confidence is not null and confidence < 0.65   +8
  call_outcome == "Follow-up Needed"             +5
```

**A missing input contributes 0.** A null confidence never scores as low
confidence; a null risk level never scores as High. Both are pinned by tests.

Bands: `>=80 critical`, `>=60 high`, `>=35 medium`, else `low`.

### Recovery opportunity

`detected` when `lead_quality_score >= 4 && call_outcome != "Sale"`.
`recommended_offer` maps from `main_objection` (price, timing, trust,
competitor, authority, no_need, integration, security, else a generic
fallback). `recommended_follow_up_window` maps from the priority band
(critical → `within_24_hours` … low → `within_2_weeks`). `confidence` passes
through the analysis value and stays `null` when never measured.

## 6. n8n final response envelope

```json
{
  "call_id": "CALL_<uuid4>",
  "created_at": "...", "call_date": "...",
  "agent_name": "...", "customer_name": "... | null",
  "status": "completed | flagged | human_review_required",
  "router_reasons": ["..."],
  "analysis": { /* as above, incl. attention + recovery_opportunity */ },
  "persistence": { "persisted": true, "detail": "Record stored." }
}
```

Changed from the previous flat schema: the 18 analysis fields moved under
`analysis`, and the identity/metadata/persistence fields were added.

## 7. Frontend mapping

`frontend/src/types/overview.ts` mirrors the Overview DTO in the backend's
own snake_case — no mapping layer, so a rename bug has nowhere to hide.

`frontend/src/services/callsApi.ts` holds two small adapters
(`toCallListItem`, `toCallRecord`) that rename snake_case onto the camelCase
view types the existing components already consume. Pure field renaming — no
filtering, aggregation, or business rules. Router reason codes map onto the
typed union, with an unknown future code degrading to `upstream_failure`
rather than crashing.
