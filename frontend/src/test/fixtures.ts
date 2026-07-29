/**
 * Test fixtures shaped exactly like `call_data_service`'s real responses
 * (snake_case, nullable fields present). If the backend contract changes,
 * these break -- which is the point.
 */
import { vi } from 'vitest'
import type { BackendCallRecord, BackendCallSummary, OverviewSummary } from '../types'

export function kpi(current: number | null, previous: number | null = null) {
  const absolute = current !== null && previous !== null ? Number((current - previous).toFixed(2)) : null
  return {
    current_value: current,
    previous_value: previous,
    absolute_change: absolute,
    percentage_change: previous !== null && previous !== 0 && current !== null
      ? Number((((current - previous) / Math.abs(previous)) * 100).toFixed(1))
      : null,
    trend_direction: absolute === null ? ('unknown' as const) : absolute > 0 ? ('up' as const) : absolute < 0 ? ('down' as const) : ('flat' as const),
  }
}

export function makeOverview(overrides: Partial<OverviewSummary> = {}): OverviewSummary {
  return {
    period: {
      period: '7d',
      current_start: '2026-07-21T12:00:00Z',
      current_end: '2026-07-28T12:00:00Z',
      previous_start: '2026-07-14T12:00:00Z',
      previous_end: '2026-07-21T12:00:00Z',
      current_window_inclusive_of_now: true,
    },
    generated_at: '2026-07-28T12:00:00Z',
    executive_summary: '12 calls analyzed in the last 7 days, a 41.7% close rate, 3 calls needing attention.',
    kpis: {
      calls_analyzed: kpi(12, 8),
      close_rate: kpi(41.7, 37.5),
      average_agent_performance: kpi(4.1, 3.8),
      average_lead_quality: kpi(3.6, 3.4),
      calls_requiring_attention: kpi(3, 5),
      improved_agents_count: kpi(2, null),
    },
    // Sums to calls_analyzed.current_value (12) -- see outcome_distribution's
    // reconciliation invariant in aggregation.py.
    outcome_distribution: { sale: 6, no_sale: 3, follow_up: 2, uncertain: 0, unknown: 1 },
    close_rate_trend: [
      { label: 'b1', start_date: '2026-07-21', end_date: '2026-07-23', calls_analyzed: 3, known_outcomes: 3, sales: 1, close_rate: 33.3 },
      { label: 'b2', start_date: '2026-07-23', end_date: '2026-07-25', calls_analyzed: 3, known_outcomes: 3, sales: 2, close_rate: 66.7 },
      { label: 'b3', start_date: '2026-07-25', end_date: '2026-07-26', calls_analyzed: 3, known_outcomes: 3, sales: 1, close_rate: 33.3 },
      { label: 'b4', start_date: '2026-07-26', end_date: '2026-07-28', calls_analyzed: 3, known_outcomes: 3, sales: 1, close_rate: 33.3 },
    ],
    improved_agents: [
      {
        agent_name: 'Sarah Levi',
        current_average_score: 4.5,
        previous_average_score: 4.0,
        improvement: 0.5,
        current_call_count: 3,
        previous_call_count: 2,
      },
    ],
    attention_calls: [
      {
        call_id: 'CALL_014',
        created_at: '2026-07-27T09:00:00Z',
        call_date: '2026-07-27',
        agent_name: 'Michael Ben-David',
        customer_name: null,
        call_outcome: 'Sale',
        lead_quality_score: 5,
        agent_performance_score: 2,
        priority: 'critical',
        priority_score: 80,
        category: 'critical_coaching',
        reason: 'Agent performance scored 2/5 on this call; coaching is warranted.',
        guardrail_status: 'pass',
      },
      {
        call_id: 'CALL_009',
        created_at: '2026-07-26T09:00:00Z',
        call_date: '2026-07-26',
        agent_name: 'Daniel Cohen',
        customer_name: 'Harrow Retail',
        call_outcome: 'No Sale',
        lead_quality_score: 4,
        agent_performance_score: 4,
        priority: 'medium',
        priority_score: 50,
        category: 'recoverable_opportunity',
        reason: 'Lead quality scored 4/5 but the call did not close.',
        guardrail_status: 'pass',
      },
    ],
    recent_calls: [
      {
        call_id: 'CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c',
        created_at: '2026-07-28T10:00:00Z',
        call_date: '2026-07-28',
        agent_name: 'Sarah Levi',
        customer_name: 'Northwind Solutions',
        call_outcome: 'Sale',
        agent_performance_score: 5,
        lead_quality_score: 5,
        guardrail_status: 'pass',
        source: 'live_analysis',
      },
      {
        call_id: 'CALL_001',
        created_at: '2026-07-27T09:00:00Z',
        call_date: '2026-07-27',
        agent_name: 'Sarah Levi',
        customer_name: null,
        call_outcome: 'Sale',
        agent_performance_score: 4,
        lead_quality_score: 5,
        guardrail_status: 'pass',
        source: 'historical_seed',
      },
    ],
    data_quality: {
      loaded_records: 24,
      skipped_malformed_records: 0,
      current_period_records: 12,
      previous_period_records: 8,
    },
    ...overrides,
  }
}

export function makeEmptyOverview(): OverviewSummary {
  return makeOverview({
    executive_summary: 'No calls were analyzed in the last 7 days.',
    kpis: {
      calls_analyzed: kpi(0, 0),
      close_rate: kpi(null, null),
      average_agent_performance: kpi(null, null),
      average_lead_quality: kpi(null, null),
      calls_requiring_attention: kpi(0, 0),
      improved_agents_count: kpi(0, null),
    },
    outcome_distribution: { sale: 0, no_sale: 0, follow_up: 0, uncertain: 0, unknown: 0 },
    close_rate_trend: [],
    improved_agents: [],
    attention_calls: [],
    recent_calls: [],
    data_quality: { loaded_records: 0, skipped_malformed_records: 0, current_period_records: 0, previous_period_records: 0 },
  })
}

export function makeCallSummary(overrides: Partial<BackendCallSummary> = {}): BackendCallSummary {
  return {
    call_id: 'CALL_001',
    source: 'historical_seed',
    created_at: '2026-07-27T09:00:00Z',
    call_date: '2026-07-27',
    agent_name: 'Sarah Levi',
    customer_name: null,
    status: 'completed',
    call_outcome: 'Sale',
    agent_performance_score: 4,
    lead_quality_score: 5,
    confidence: null,
    risk_level: null,
    guardrail_status: 'pass',
    attention_required: false,
    attention_priority: 'low',
    attention_priority_score: 0,
    attention_category: 'low_priority',
    ...overrides,
  }
}

/** A seeded historical record: every optional AI field is legitimately null. */
export function makeCallRecord(overrides: Partial<BackendCallRecord> = {}): BackendCallRecord {
  return {
    schema_version: '1.0',
    call_id: 'CALL_001',
    source: 'historical_seed',
    created_at: '2026-07-27T09:00:00Z',
    call_date: '2026-07-27',
    agent_name: 'Sarah Levi',
    agent_name_normalized: 'sarah levi',
    customer_name: null,
    status: 'completed',
    router_reasons: [],
    analysis: {
      transcript: 'Agent: Hello there.\nCustomer: Hi.',
      call_summary: 'Mid-Market Finance call handled by Sarah Levi.',
      customer_intent: 'high',
      main_objection: 'price',
      customer_sentiment: 'positive',
      call_outcome: 'Sale',
      agent_performance_score: 4,
      lead_quality_score: 5,
      similar_calls: [],
      coaching_feedback: ['Handled the price objection well.'],
      recommended_next_action: null,
      suggested_follow_up_email: '',
      routing_category: 'new_business',
      confidence: null,
      risk_level: null,
      detected_signals: ['price objection'],
      limitations: 'Seeded from data/historical_sales_calls.csv.',
      guardrail_status: 'pass',
      attention: { required: false, priority: 'low', priority_score: 0, category: 'low_priority', reason: null },
      recovery_opportunity: {
        detected: false,
        confidence: null,
        reason: null,
        recommended_offer: null,
        recommended_follow_up_window: null,
      },
    },
    ...overrides,
  }
}

/** Stub `fetch` with a URL-matched routing table. */
export function stubFetch(routes: { match: string; status?: number; body: unknown }[]) {
  return vi.fn((input: RequestInfo | URL) => {
    const url = String(input)
    const route = routes.find((r) => url.includes(r.match))
    if (!route) {
      return Promise.resolve(new Response(JSON.stringify({ error: { code: 'NOT_STUBBED', message: url } }), { status: 500 }))
    }
    return Promise.resolve(
      new Response(JSON.stringify(route.body), {
        status: route.status ?? 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })
}
