/**
 * Team Intelligence domain types.
 *
 * Every field here is derived deterministically from `GET /calls` — the same
 * records Calls and Call Details read. There is no team-level backend
 * aggregation endpoint yet, and nothing on this screen is invented: if a
 * concept cannot be computed from the stored call summaries it is not
 * modelled here.
 *
 * Deliberately absent (and why): `strongestSkill`, `growthArea` and free-text
 * "recurring patterns" were previously mock strings. `GET /calls` exposes no
 * skill/strength taxonomy, and the fields that could support one
 * (`coaching_feedback`, `detected_signals`, `main_objection`) live only on the
 * full record, not the list summary. Deriving them would mean inventing
 * labels, so they are omitted until a real aggregation contract exists.
 */
import type { TrendPoint } from './aiOperations'
import type { CallOutcome } from './call'
import type { AttentionCategory } from './overview'

export interface TeamInsight {
  id: string
  headline: string
  detail: string
  generatedAt: string
}

/** Whether an agent's later calls score better than their earlier ones. */
export type AgentTrendDirection = 'improving' | 'declining' | 'flat' | 'unknown'

export interface AgentPerformanceSummary {
  agentName: string
  callsAnalyzed: number
  /** Null when none of the agent's calls carried a score. */
  averageAgentPerformance: number | null
  averageLeadQuality: number | null
  attentionCalls: number
  /** Share of the agent's calls with a known outcome that closed, 0–100. */
  closeRate: number | null
  trendDirection: AgentTrendDirection
  /** Signed change in average performance, earlier half → later half. */
  trendDelta: number | null
}

export interface OutcomeBreakdownEntry {
  outcome: CallOutcome | 'Unknown'
  count: number
}

export interface AttentionBreakdownEntry {
  category: AttentionCategory
  count: number
}

export interface TeamPerformanceSummary {
  /** Earliest and latest `created_at` actually present in the dataset. */
  periodStart: string
  periodEnd: string
  callsAnalyzed: number
  teamAverageAgentPerformance: number | null
  teamAverageLeadQuality: number | null
  /** Sale / calls-with-a-known-outcome * 100, same exclusion rule as
      call_data_service's own close_rate: 'Uncertain' and missing outcomes
      are excluded from the denominator, not counted as losses. */
  teamCloseRate: number | null
  attentionCalls: number
  performanceTrend: TrendPoint[]
  agents: AgentPerformanceSummary[]
  outcomeBreakdown: OutcomeBreakdownEntry[]
  attentionBreakdown: AttentionBreakdownEntry[]
}
