/**
 * Deterministic executive copy.
 *
 * No LLM writes dashboard text. Everything here is a pure function of
 * numbers the backend already computed, so the headline can never drift
 * from the cards underneath it, and it costs nothing to render.
 *
 * The rule for every sentence: say what changed and what it means, not
 * what the numbers are. A manager can already read the numbers -- the
 * headline earns its space only by interpreting them.
 */
import type { KpiMetric, OverviewSummary } from '../types'

/** "no representatives" / "1 representative" / "4 representatives" */
export function pluralize(count: number, singular: string, plural?: string): string {
  const word = count === 1 ? singular : (plural ?? `${singular}s`)
  return `${count} ${word}`
}

/**
 * Renders a group of names against a total without listing everyone when
 * everyone qualifies -- "all 4 representatives" reads far better than
 * four names repeated in two consecutive sentences.
 */
export function describeGroup(names: string[], total: number, noun = 'representative'): string {
  if (names.length === 0) return `no ${noun}s`
  if (names.length === total && total > 1) return `all ${total} ${noun}s`
  if (names.length === 1) return names[0]
  if (names.length === 2) return `${names[0]} and ${names[1]}`
  if (names.length <= 3) return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`
  return `${names.slice(0, 2).join(', ')} and ${names.length - 2} others`
}

const PERIOD_LABEL: Record<string, string> = {
  '7d': 'this week',
  '30d': 'this month',
}

function periodLabel(period: string): string {
  return PERIOD_LABEL[period] ?? 'in this period'
}

/** Direction word for a metric that has a real previous value. */
function movement(metric: KpiMetric): 'rose' | 'fell' | 'held' | null {
  if (metric.previous_value === null || metric.previous_value === undefined) return null
  if (metric.absolute_change === null || metric.absolute_change === undefined) return null
  if (metric.absolute_change > 0) return 'rose'
  if (metric.absolute_change < 0) return 'fell'
  return 'held'
}

/**
 * The Overview headline: leads with the most consequential fact, then
 * adds attention load, then volume context. Falls back gracefully when
 * there is nothing to compare against or nothing was analysed at all.
 */
export function buildExecutiveSummary(data: OverviewSummary): string {
  const period = periodLabel(data.period.period)
  const calls = data.kpis.calls_analyzed.current_value ?? 0

  if (calls === 0) {
    return `No calls were analyzed ${period}. Analyze a call to start building the picture.`
  }

  const parts: string[] = []

  // 1. Close rate -- the headline business outcome.
  const closeRate = data.kpis.close_rate
  const closeMove = movement(closeRate)
  if (closeRate.current_value === null || closeRate.current_value === undefined) {
    parts.push(`${pluralize(calls, 'call')} analyzed ${period}, none with a recorded outcome yet`)
  } else if (closeMove === null) {
    parts.push(`Close rate is ${closeRate.current_value}% across ${pluralize(calls, 'call')} ${period}`)
  } else if (closeMove === 'held') {
    parts.push(`Close rate held at ${closeRate.current_value}% ${period}`)
  } else {
    const verb = closeMove === 'rose' ? 'rose to' : 'fell to'
    parts.push(`Close rate ${verb} ${closeRate.current_value}% ${period}`)
  }

  // 2. Attention load -- what the manager has to act on.
  const attention = data.kpis.calls_requiring_attention.current_value
  if (attention === null || attention === undefined) {
    // say nothing rather than guess
  } else if (attention === 0) {
    parts.push('nothing currently needs your attention')
  } else {
    parts.push(`${pluralize(attention, 'call')} ${attention === 1 ? 'needs' : 'need'} your attention`)
  }

  // 3. Recoverable opportunity -- only when there is something to recover.
  const recoverable = data.attention_calls.filter((c) => c.category === 'recoverable_opportunity').length
  if (recoverable > 0) {
    parts.push(`${pluralize(recoverable, 'opportunity', 'opportunities')} may still be recoverable`)
  }

  return `${parts.join(', ')}.`
}

/**
 * Team Intelligence headline. Same rules; additionally collapses the
 * "everyone qualifies" case instead of listing every name twice.
 */
export function buildTeamSummary(input: {
  callsAnalyzed: number
  agentCount: number
  teamPerformance: number | null
  attentionCalls: number
  agentsNeedingAttention: string[]
  improvingAgents: string[]
  periodLabel: string
}): { headline: string; detail: string } {
  const { callsAnalyzed, agentCount, teamPerformance, attentionCalls, agentsNeedingAttention, improvingAgents } = input

  if (callsAnalyzed === 0) {
    return {
      headline: 'No calls analyzed in this period',
      detail: 'Team intelligence appears once calls have been analyzed in the selected period.',
    }
  }

  const headline =
    attentionCalls > 0
      ? `${pluralize(attentionCalls, 'call')} of ${callsAnalyzed} need attention ${input.periodLabel}`
      : `${pluralize(callsAnalyzed, 'call')} analyzed ${input.periodLabel}, none needing attention`

  const sentences: string[] = []
  sentences.push(
    teamPerformance === null
      ? 'No agent performance scores were recorded in this period.'
      : `Team average agent performance is ${teamPerformance.toFixed(1)} out of 5 across ${pluralize(agentCount, 'representative')}.`
  )
  if (agentsNeedingAttention.length > 0) {
    const who = describeGroup(agentsNeedingAttention, agentCount)
    const verb = who.startsWith('all') || agentsNeedingAttention.length > 1 ? 'have' : 'has'
    sentences.push(`${who} ${verb} at least one call requiring attention.`)
  }
  if (improvingAgents.length > 0) {
    const who = describeGroup(improvingAgents, agentCount)
    sentences.push(`${who} improved compared with their earlier calls.`)
  }

  return { headline, detail: sentences.join(' ') }
}
