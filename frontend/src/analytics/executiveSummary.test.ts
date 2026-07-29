/**
 * Dashboard copy is generated, so its grammar is a testable contract.
 * The case that actually broke in production: every representative
 * qualified, so the sentence listed all four names twice in a row.
 */
import { describe, expect, it } from 'vitest'
import { buildExecutiveSummary, buildTeamSummary, describeGroup, pluralize } from './executiveSummary'
import type { OverviewSummary, KpiMetric } from '../types'

function kpi(current: number | null, previous: number | null = null): KpiMetric {
  const change = current !== null && previous !== null ? current - previous : null
  return {
    current_value: current,
    previous_value: previous,
    absolute_change: change,
    percentage_change: change !== null && previous ? Math.round((change / previous) * 1000) / 10 : null,
    trend_direction: 'flat',
  }
}

function overview(overrides: Partial<OverviewSummary> = {}): OverviewSummary {
  return {
    period: {
      period: '7d',
      current_start: '',
      current_end: '',
      previous_start: '',
      previous_end: '',
      current_window_inclusive_of_now: true,
    },
    generated_at: '',
    executive_summary: '',
    kpis: {
      calls_analyzed: kpi(9, 4),
      close_rate: kpi(36.4, 44.4),
      average_agent_performance: kpi(4.1),
      average_lead_quality: kpi(3.3),
      calls_requiring_attention: kpi(2, 0),
      improved_agents_count: kpi(0),
    },
    close_rate_trend: [],
    improved_agents: [],
    attention_calls: [],
    recent_calls: [],
    data_quality: { loaded_records: 0, skipped_malformed_records: 0, current_period_records: 0, previous_period_records: 0 },
    ...overrides,
  }
}

describe('pluralize', () => {
  it('handles singular, plural and zero', () => {
    expect(pluralize(0, 'call')).toBe('0 calls')
    expect(pluralize(1, 'call')).toBe('1 call')
    expect(pluralize(2, 'call')).toBe('2 calls')
  })

  it('supports irregular plurals', () => {
    expect(pluralize(1, 'opportunity', 'opportunities')).toBe('1 opportunity')
    expect(pluralize(3, 'opportunity', 'opportunities')).toBe('3 opportunities')
  })
})

describe('describeGroup', () => {
  it('collapses to "all N" instead of listing everyone', () => {
    expect(describeGroup(['A', 'B', 'C', 'D'], 4)).toBe('all 4 representatives')
  })

  it('names a single person', () => {
    expect(describeGroup(['Sarah Levi'], 4)).toBe('Sarah Levi')
  })

  it('joins two names with and', () => {
    expect(describeGroup(['A', 'B'], 4)).toBe('A and B')
  })

  it('summarises long partial lists rather than enumerating', () => {
    expect(describeGroup(['A', 'B', 'C', 'D'], 9)).toBe('A, B and 2 others')
  })

  it('handles nobody', () => {
    expect(describeGroup([], 4)).toBe('no representatives')
  })

  it('does not claim "all" when the group is one of one', () => {
    // A single-person team qualifying is better said by name than as "all 1".
    expect(describeGroup(['A'], 1)).toBe('A')
  })
})

describe('buildExecutiveSummary', () => {
  it('leads with a falling close rate and states the attention load', () => {
    const text = buildExecutiveSummary(overview())
    expect(text).toContain('Close rate fell to 36.4%')
    expect(text).toContain('2 calls need your attention')
  })

  it('says nothing needs attention when the queue is empty', () => {
    const text = buildExecutiveSummary(
      overview({ kpis: { ...overview().kpis, calls_requiring_attention: kpi(0, 3) } })
    )
    expect(text).toContain('nothing currently needs your attention')
  })

  it('uses singular grammar for exactly one call', () => {
    const text = buildExecutiveSummary(
      overview({ kpis: { ...overview().kpis, calls_requiring_attention: kpi(1, 0) } })
    )
    expect(text).toContain('1 call needs your attention')
  })

  it('handles an empty period without inventing numbers', () => {
    const text = buildExecutiveSummary(
      overview({ kpis: { ...overview().kpis, calls_analyzed: kpi(0, 0) } })
    )
    expect(text).toContain('No calls were analyzed')
  })

  it('does not claim a direction when there is no previous period', () => {
    const text = buildExecutiveSummary(
      overview({ kpis: { ...overview().kpis, close_rate: kpi(36.4, null) } })
    )
    expect(text).toContain('Close rate is 36.4%')
    expect(text).not.toContain('fell')
    expect(text).not.toContain('rose')
  })

  it('mentions recoverable opportunities only when some exist', () => {
    const withRecovery = buildExecutiveSummary(
      overview({
        attention_calls: [
          { category: 'recoverable_opportunity' } as never,
          { category: 'human_review' } as never,
        ],
      })
    )
    expect(withRecovery).toContain('1 opportunity may still be recoverable')
    expect(buildExecutiveSummary(overview())).not.toContain('recoverable')
  })
})

describe('buildTeamSummary', () => {
  const base = {
    callsAnalyzed: 29,
    agentCount: 4,
    teamPerformance: 4.1,
    attentionCalls: 11,
    agentsNeedingAttention: ['A', 'B', 'C', 'D'],
    improvingAgents: ['A', 'B', 'C', 'D'],
    periodLabel: 'this week',
  }

  it('collapses the all-representatives case instead of listing names twice', () => {
    const { detail } = buildTeamSummary(base)
    expect(detail).toContain('all 4 representatives have at least one call requiring attention')
    expect(detail).toContain('all 4 representatives improved')
    expect(detail).not.toMatch(/A, B, C and D.*A, B, C and D/)
  })

  it('names a single representative', () => {
    const { detail } = buildTeamSummary({ ...base, agentsNeedingAttention: ['Sarah Levi'], improvingAgents: [] })
    expect(detail).toContain('Sarah Levi has at least one call requiring attention')
  })

  it('omits clauses entirely when nobody qualifies', () => {
    const { detail } = buildTeamSummary({ ...base, agentsNeedingAttention: [], improvingAgents: [] })
    expect(detail).not.toContain('requiring attention')
    expect(detail).not.toContain('improved')
  })

  it('reports an empty period without fabricating a score', () => {
    const { headline, detail } = buildTeamSummary({ ...base, callsAnalyzed: 0 })
    expect(headline).toContain('No calls analyzed')
    expect(detail).toContain('appears once calls have been analyzed')
  })

  it('says scores were not recorded rather than showing zero', () => {
    const { detail } = buildTeamSummary({ ...base, teamPerformance: null })
    expect(detail).toContain('No agent performance scores were recorded')
  })
})
