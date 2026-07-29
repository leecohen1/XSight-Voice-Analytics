/**
 * Team Intelligence API.
 *
 * There is no team-level aggregation endpoint on `call_data_service`, so this
 * module derives the whole screen from `GET /calls` — the same real, stored
 * records Calls and Call Details read. There is no mock branch: if the
 * service is unreachable the screen shows a real error rather than demo data.
 *
 * `aggregateTeamIntelligence` is a pure function over the fetched list, kept
 * separate from the fetch so the arithmetic is directly testable. Every rule
 * it applies is deterministic and documented inline; nothing is inferred by
 * an LLM and no label is invented. Where a value cannot be computed (no
 * scores present, no known outcomes, too few calls to compare halves) it
 * returns null / 'unknown' instead of a plausible-looking number.
 */
import type {
  AgentPerformanceSummary,
  AgentTrendDirection,
  AttentionBreakdownEntry,
  CallListItem,
  OutcomeBreakdownEntry,
  OverviewPeriod,
  TeamInsight,
  TeamPerformanceSummary,
  TrendPoint,
} from '../types'
import { listCalls } from './callsApi'
import { buildTeamSummary } from '../analytics/executiveSummary'

export interface TeamIntelligenceData {
  insight: TeamInsight
  summary: TeamPerformanceSummary
}

const PERIOD_DAYS: Record<OverviewPeriod, number> = { '7d': 7, '30d': 30 }
const PERIOD_LABEL: Record<OverviewPeriod, string> = { '7d': 'this week', '30d': 'this month' }

/**
 * Rolling N-day window ending now, computed client-side over the complete
 * fetched list. `listCalls()` currently has no server-side pagination in
 * front of it (limit=200, comfortably above the live dataset size), so
 * filtering here is safe and complete today -- the same "operates over the
 * full set" reasoning already used in analytics/callGrouping.ts. This is
 * the same rolling-window *spirit* as Overview's 7d/30d, not a byte-for-byte
 * replica of its server-computed window_bounds() -- Overview's boundaries
 * live in call_data_service and are not something the frontend can or
 * should reimplement. If GET /calls ever gains real pagination, this must
 * move server-side, the same migration note callGrouping.ts already carries.
 */
export function filterByPeriod(calls: CallListItem[], period: OverviewPeriod, now: Date): CallListItem[] {
  const cutoff = new Date(now.getTime() - PERIOD_DAYS[period] * 24 * 60 * 60 * 1000)
  return calls.filter((c) => new Date(c.createdAt) >= cutoff)
}

/** Mean of the defined values, or null when there are none. Rounded to 1dp. */
function mean(values: (number | undefined)[]): number | null {
  const present = values.filter((v): v is number => typeof v === 'number')
  if (present.length === 0) return null
  return Math.round((present.reduce((a, b) => a + b, 0) / present.length) * 10) / 10
}

/**
 * Close rate over calls with a *known* outcome. 'Uncertain' and missing
 * outcomes are excluded from both numerator and denominator rather than
 * being counted as losses, which would understate the rate.
 */
function closeRate(calls: CallListItem[]): number | null {
  const known = calls.filter((c) => c.callOutcome && c.callOutcome !== 'Uncertain')
  if (known.length === 0) return null
  const sales = known.filter((c) => c.callOutcome === 'Sale').length
  return Math.round((sales / known.length) * 1000) / 10
}

/**
 * Splits an agent's calls chronologically in half and compares mean
 * performance. Needs at least 4 scored calls to say anything — below that a
 * single call swings the average and the signal is noise, so it reports
 * 'unknown'. A delta within ±0.2 counts as flat.
 */
function agentTrend(scored: CallListItem[]): { direction: AgentTrendDirection; delta: number | null } {
  if (scored.length < 4) return { direction: 'unknown', delta: null }
  const ordered = [...scored].sort((a, b) => a.createdAt.localeCompare(b.createdAt))
  const mid = Math.floor(ordered.length / 2)
  const earlier = mean(ordered.slice(0, mid).map((c) => c.agentPerformanceScore))
  const later = mean(ordered.slice(mid).map((c) => c.agentPerformanceScore))
  if (earlier === null || later === null) return { direction: 'unknown', delta: null }
  const delta = Math.round((later - earlier) * 10) / 10
  if (Math.abs(delta) < 0.2) return { direction: 'flat', delta }
  return { direction: delta > 0 ? 'improving' : 'declining', delta }
}

/** One trend point per calendar day that actually has calls — no gap filling. */
function performanceTrend(calls: CallListItem[]): TrendPoint[] {
  const byDay = new Map<string, (number | undefined)[]>()
  for (const call of calls) {
    const day = call.createdAt.slice(0, 10)
    const bucket = byDay.get(day) ?? []
    bucket.push(call.agentPerformanceScore)
    byDay.set(day, bucket)
  }
  return [...byDay.entries()]
    .map(([date, scores]) => ({ date, value: mean(scores) }))
    .filter((p): p is TrendPoint => p.value !== null)
    .sort((a, b) => a.date.localeCompare(b.date))
}

export function aggregateTeamIntelligence(
  calls: CallListItem[],
  period: OverviewPeriod = '7d',
  now = new Date()
): TeamIntelligenceData {
  const generatedAt = now.toISOString()

  if (calls.length === 0) {
    const empty = buildTeamSummary({
      callsAnalyzed: 0,
      agentCount: 0,
      teamPerformance: null,
      attentionCalls: 0,
      agentsNeedingAttention: [],
      improvingAgents: [],
      periodLabel: PERIOD_LABEL[period],
    })
    return {
      insight: {
        id: 'team-empty',
        headline: empty.headline,
        detail: empty.detail,
        generatedAt,
      },
      summary: {
        periodStart: '',
        periodEnd: '',
        callsAnalyzed: 0,
        teamAverageAgentPerformance: null,
        teamAverageLeadQuality: null,
        teamCloseRate: null,
        attentionCalls: 0,
        performanceTrend: [],
        agents: [],
        outcomeBreakdown: [],
        attentionBreakdown: [],
      },
    }
  }

  const timestamps = calls.map((c) => c.createdAt).sort((a, b) => a.localeCompare(b))
  const teamPerformance = mean(calls.map((c) => c.agentPerformanceScore))
  const teamLeadQuality = mean(calls.map((c) => c.leadQualityScore))
  const teamCloseRate = closeRate(calls)
  const attentionCalls = calls.filter((c) => c.attentionRequired).length

  // Group by display name. call_data_service normalizes agent names on write
  // (agent_name_normalized), so casing/whitespace variants of the same person
  // already arrive consistently.
  const byAgent = new Map<string, CallListItem[]>()
  for (const call of calls) {
    const bucket = byAgent.get(call.agentName) ?? []
    bucket.push(call)
    byAgent.set(call.agentName, bucket)
  }

  const agents: AgentPerformanceSummary[] = [...byAgent.entries()]
    .map(([agentName, agentCalls]) => {
      const scored = agentCalls.filter((c) => typeof c.agentPerformanceScore === 'number')
      const { direction, delta } = agentTrend(scored)
      return {
        agentName,
        callsAnalyzed: agentCalls.length,
        averageAgentPerformance: mean(agentCalls.map((c) => c.agentPerformanceScore)),
        averageLeadQuality: mean(agentCalls.map((c) => c.leadQualityScore)),
        attentionCalls: agentCalls.filter((c) => c.attentionRequired).length,
        closeRate: closeRate(agentCalls),
        trendDirection: direction,
        trendDelta: delta,
      }
    })
    // Coaching view: whoever needs attention most surfaces first. Agents with
    // no score at all sort last rather than pretending to be a perfect 5.
    .sort((a, b) => {
      if (b.attentionCalls !== a.attentionCalls) return b.attentionCalls - a.attentionCalls
      return (
        (a.averageAgentPerformance ?? Number.POSITIVE_INFINITY) -
        (b.averageAgentPerformance ?? Number.POSITIVE_INFINITY)
      )
    })

  const outcomeCounts = new Map<string, number>()
  for (const call of calls) {
    const key = call.callOutcome ?? 'Unknown'
    outcomeCounts.set(key, (outcomeCounts.get(key) ?? 0) + 1)
  }
  const outcomeBreakdown = [...outcomeCounts.entries()]
    .map(([outcome, count]) => ({ outcome, count }) as OutcomeBreakdownEntry)
    .sort((a, b) => b.count - a.count)

  const attentionCounts = new Map<string, number>()
  for (const call of calls) {
    if (!call.attentionCategory) continue
    attentionCounts.set(call.attentionCategory, (attentionCounts.get(call.attentionCategory) ?? 0) + 1)
  }
  const attentionBreakdown = [...attentionCounts.entries()]
    .map(([category, count]) => ({ category, count }) as AttentionBreakdownEntry)
    .sort((a, b) => b.count - a.count)

  const needsCoaching = agents.filter((a) => a.attentionCalls > 0)
  const improving = agents.filter((a) => a.trendDirection === 'improving')

  // buildTeamSummary handles the grammar cases that broke in production:
  // when every representative qualifies for a clause, it collapses to
  // "all 4 representatives" instead of listing every name twice in a row.
  const { headline, detail } = buildTeamSummary({
    callsAnalyzed: calls.length,
    agentCount: byAgent.size,
    teamPerformance,
    attentionCalls,
    agentsNeedingAttention: needsCoaching.map((a) => a.agentName),
    improvingAgents: improving.map((a) => a.agentName),
    periodLabel: PERIOD_LABEL[period],
  })

  return {
    insight: {
      id: 'team-derived',
      headline,
      detail,
      generatedAt,
    },
    summary: {
      periodStart: timestamps[0].slice(0, 10),
      periodEnd: timestamps[timestamps.length - 1].slice(0, 10),
      callsAnalyzed: calls.length,
      teamAverageAgentPerformance: teamPerformance,
      teamAverageLeadQuality: teamLeadQuality,
      teamCloseRate,
      attentionCalls,
      performanceTrend: performanceTrend(calls),
      agents,
      outcomeBreakdown,
      attentionBreakdown,
    },
  }
}

export async function getTeamIntelligence(
  period: OverviewPeriod = '7d',
  signal?: AbortSignal
): Promise<TeamIntelligenceData> {
  const calls = await listCalls(signal)
  const now = new Date()
  return aggregateTeamIntelligence(filterByPeriod(calls, period, now), period, now)
}
