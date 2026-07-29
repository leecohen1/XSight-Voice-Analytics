/**
 * Team Intelligence aggregation.
 *
 * These lock the arithmetic behind the screen. The point of every case is
 * that a value the backend does not support is reported as unknown rather
 * than guessed — that is the property most likely to regress if someone
 * later "tidies up" a null into a 0.
 */
import { describe, expect, it } from 'vitest'
import { aggregateTeamIntelligence, filterByPeriod } from './teamApi'
import type { CallListItem } from '../types'

function call(overrides: Partial<CallListItem> = {}): CallListItem {
  return {
    callId: `CALL_${Math.random().toString(16).slice(2, 10)}`,
    status: 'completed',
    agentName: 'Sarah Levi',
    callDate: '2026-07-20',
    createdAt: '2026-07-20T09:00:00Z',
    guardrailStatus: 'pass',
    source: 'live_analysis',
    attentionRequired: false,
    attentionPriority: 'low',
    agentPerformanceScore: 4,
    leadQualityScore: 3,
    callOutcome: 'Sale',
    ...overrides,
  }
}

describe('aggregateTeamIntelligence', () => {
  it('reports an empty dataset without inventing zeros', () => {
    const { summary, insight } = aggregateTeamIntelligence([])
    expect(summary.callsAnalyzed).toBe(0)
    expect(summary.teamAverageAgentPerformance).toBeNull()
    expect(summary.teamAverageLeadQuality).toBeNull()
    expect(summary.agents).toEqual([])
    expect(insight.headline).toMatch(/no calls analyzed/i)
  })

  it('averages the scores the backend actually returned', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ agentPerformanceScore: 4, leadQualityScore: 3 }),
      call({ agentPerformanceScore: 5, leadQualityScore: 4 }),
    ])
    expect(summary.teamAverageAgentPerformance).toBe(4.5)
    expect(summary.teamAverageLeadQuality).toBe(3.5)
    expect(summary.callsAnalyzed).toBe(2)
  })

  it('returns null averages when no call carries a score', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ agentPerformanceScore: undefined, leadQualityScore: undefined }),
    ])
    expect(summary.teamAverageAgentPerformance).toBeNull()
    expect(summary.teamAverageLeadQuality).toBeNull()
  })

  it('excludes Uncertain outcomes from close rate instead of counting them as losses', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ callOutcome: 'Sale' }),
      call({ callOutcome: 'No Sale' }),
      call({ callOutcome: 'Uncertain' }),
    ])
    // 1 Sale out of 2 known outcomes — the Uncertain call is not a denominator.
    expect(summary.agents[0].closeRate).toBe(50)
  })

  it('reports close rate as null when no outcome is known', () => {
    const { summary } = aggregateTeamIntelligence([call({ callOutcome: undefined })])
    expect(summary.agents[0].closeRate).toBeNull()
  })

  it('groups per agent and counts their attention calls', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ agentName: 'Sarah Levi' }),
      call({ agentName: 'Sarah Levi', attentionRequired: true }),
      call({ agentName: 'Daniel Cohen' }),
    ])
    const sarah = summary.agents.find((a) => a.agentName === 'Sarah Levi')
    const daniel = summary.agents.find((a) => a.agentName === 'Daniel Cohen')
    expect(sarah?.callsAnalyzed).toBe(2)
    expect(sarah?.attentionCalls).toBe(1)
    expect(daniel?.attentionCalls).toBe(0)
    expect(summary.attentionCalls).toBe(1)
    // Agents needing attention sort first — this is the coaching queue order.
    expect(summary.agents[0].agentName).toBe('Sarah Levi')
  })

  it('refuses to call a trend with fewer than four scored calls', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ createdAt: '2026-07-01T09:00:00Z', agentPerformanceScore: 2 }),
      call({ createdAt: '2026-07-02T09:00:00Z', agentPerformanceScore: 5 }),
    ])
    expect(summary.agents[0].trendDirection).toBe('unknown')
    expect(summary.agents[0].trendDelta).toBeNull()
  })

  it('detects improvement by comparing the earlier half to the later half', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ createdAt: '2026-07-01T09:00:00Z', agentPerformanceScore: 2 }),
      call({ createdAt: '2026-07-02T09:00:00Z', agentPerformanceScore: 2 }),
      call({ createdAt: '2026-07-03T09:00:00Z', agentPerformanceScore: 5 }),
      call({ createdAt: '2026-07-04T09:00:00Z', agentPerformanceScore: 5 }),
    ])
    expect(summary.agents[0].trendDirection).toBe('improving')
    expect(summary.agents[0].trendDelta).toBe(3)
  })

  it('detects decline in the same way', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ createdAt: '2026-07-01T09:00:00Z', agentPerformanceScore: 5 }),
      call({ createdAt: '2026-07-02T09:00:00Z', agentPerformanceScore: 5 }),
      call({ createdAt: '2026-07-03T09:00:00Z', agentPerformanceScore: 2 }),
      call({ createdAt: '2026-07-04T09:00:00Z', agentPerformanceScore: 2 }),
    ])
    expect(summary.agents[0].trendDirection).toBe('declining')
    expect(summary.agents[0].trendDelta).toBe(-3)
  })

  it('treats a sub-0.2 swing as flat rather than a trend', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ createdAt: '2026-07-01T09:00:00Z', agentPerformanceScore: 4 }),
      call({ createdAt: '2026-07-02T09:00:00Z', agentPerformanceScore: 4 }),
      call({ createdAt: '2026-07-03T09:00:00Z', agentPerformanceScore: 4 }),
      call({ createdAt: '2026-07-04T09:00:00Z', agentPerformanceScore: 4 }),
    ])
    expect(summary.agents[0].trendDirection).toBe('flat')
  })

  it('buckets the performance trend by day and skips days with no scores', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ createdAt: '2026-07-01T09:00:00Z', agentPerformanceScore: 3 }),
      call({ createdAt: '2026-07-01T18:00:00Z', agentPerformanceScore: 5 }),
      call({ createdAt: '2026-07-02T09:00:00Z', agentPerformanceScore: undefined }),
    ])
    expect(summary.performanceTrend).toEqual([{ date: '2026-07-01', value: 4 }])
  })

  it('counts outcomes and labels a missing outcome Unknown', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ callOutcome: 'Sale' }),
      call({ callOutcome: 'Sale' }),
      call({ callOutcome: undefined }),
    ])
    expect(summary.outcomeBreakdown).toEqual([
      { outcome: 'Sale', count: 2 },
      { outcome: 'Unknown', count: 1 },
    ])
  })

  it('aggregates the router attention categories it was given', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ attentionRequired: true, attentionCategory: 'critical_coaching' }),
      call({ attentionRequired: true, attentionCategory: 'critical_coaching' }),
      call({ attentionCategory: 'low_priority' }),
    ])
    expect(summary.attentionBreakdown).toEqual([
      { category: 'critical_coaching', count: 2 },
      { category: 'low_priority', count: 1 },
    ])
  })

  it('derives the period from the real timestamps present', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ createdAt: '2026-07-04T09:00:00Z' }),
      call({ createdAt: '2026-07-01T09:00:00Z' }),
    ])
    expect(summary.periodStart).toBe('2026-07-01')
    expect(summary.periodEnd).toBe('2026-07-04')
  })

  it('states counts in the headline that match the summary numbers', () => {
    const { insight, summary } = aggregateTeamIntelligence([
      call({ attentionRequired: true }),
      call(),
      call(),
    ])
    expect(insight.headline).toBe(`${summary.attentionCalls} call of ${summary.callsAnalyzed} need attention this week`)
  })
})

describe('filterByPeriod', () => {
  const NOW = new Date('2026-07-28T12:00:00Z')

  it('keeps calls within the last 7 days and drops older ones', () => {
    const calls = [
      call({ callId: 'A', createdAt: '2026-07-27T00:00:00Z' }), // 1 day ago
      call({ callId: 'B', createdAt: '2026-07-01T00:00:00Z' }), // 27 days ago
    ]
    const kept = filterByPeriod(calls, '7d', NOW)
    expect(kept.map((c) => c.callId)).toEqual(['A'])
  })

  it('keeps calls within the last 30 days and drops older ones', () => {
    const calls = [
      call({ callId: 'A', createdAt: '2026-07-01T00:00:00Z' }), // 27 days ago
      call({ callId: 'B', createdAt: '2026-05-01T00:00:00Z' }), // ~89 days ago
    ]
    const kept = filterByPeriod(calls, '30d', NOW)
    expect(kept.map((c) => c.callId)).toEqual(['A'])
  })

  it('returns an empty list when nothing falls in the window', () => {
    const calls = [call({ createdAt: '2026-01-01T00:00:00Z' })]
    expect(filterByPeriod(calls, '7d', NOW)).toEqual([])
  })
})

describe('teamCloseRate', () => {
  it('excludes Uncertain from the team-wide close rate denominator', () => {
    const { summary } = aggregateTeamIntelligence([
      call({ callOutcome: 'Sale' }),
      call({ callOutcome: 'No Sale' }),
      call({ callOutcome: 'Uncertain' }),
    ])
    expect(summary.teamCloseRate).toBe(50)
  })

  it('is null when nothing has a known outcome', () => {
    const { summary } = aggregateTeamIntelligence([call({ callOutcome: undefined })])
    expect(summary.teamCloseRate).toBeNull()
  })
})

describe('period-aware copy', () => {
  it('labels the headline for this week on 7d', () => {
    const { insight } = aggregateTeamIntelligence([call({ attentionRequired: true })], '7d')
    expect(insight.headline).toContain('this week')
  })

  it('labels the headline for this month on 30d', () => {
    const { insight } = aggregateTeamIntelligence([call({ attentionRequired: true })], '30d')
    expect(insight.headline).toContain('this month')
  })
})
