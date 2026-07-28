/**
 * Overview contract -- mirrors `call_data_service`'s `OverviewResponse`
 * (services/call_data_service/app/models.py) field for field, in the
 * backend's own snake_case, so the API response drops in with no mapping
 * layer and no place for a rename bug to hide.
 *
 * Every number here is computed by the backend. The Overview page renders
 * these values and never averages, filters, or recomputes anything.
 */

export type OverviewPeriod = '7d' | '30d'
export type TrendDirection = 'up' | 'down' | 'flat' | 'unknown'

export type AttentionPriority = 'low' | 'medium' | 'high' | 'critical'

export type AttentionCategory =
  | 'recoverable_opportunity'
  | 'human_review'
  | 'customer_dissatisfaction'
  | 'critical_coaching'
  | 'evidence_conflict'
  | 'low_priority'

export type CallSource = 'historical_seed' | 'live_analysis'

/**
 * One KPI with its previous-period comparison.
 *
 * `null` is meaningful, never a rendering bug: `current_value: null` means
 * nothing in the window was scored, and `percentage_change: null` means the
 * previous value was zero or unknown so the ratio is undefined. The UI must
 * say so rather than substituting 0.
 */
export interface KpiMetric {
  current_value: number | null
  previous_value: number | null
  absolute_change: number | null
  percentage_change: number | null
  trend_direction: TrendDirection
}

export interface OverviewKpis {
  calls_analyzed: KpiMetric
  close_rate: KpiMetric
  average_agent_performance: KpiMetric
  average_lead_quality: KpiMetric
  calls_requiring_attention: KpiMetric
  improved_agents_count: KpiMetric
}

export interface TrendBucket {
  label: string
  start_date: string
  end_date: string
  calls_analyzed: number
  known_outcomes: number
  sales: number
  close_rate: number | null
}

export interface ImprovedAgent {
  agent_name: string
  current_average_score: number
  previous_average_score: number
  improvement: number
  current_call_count: number
  previous_call_count: number
}

export interface AttentionCall {
  call_id: string
  created_at: string
  call_date: string | null
  agent_name: string
  customer_name: string | null
  call_outcome: string | null
  lead_quality_score: number | null
  agent_performance_score: number | null
  priority: AttentionPriority
  priority_score: number
  category: AttentionCategory
  reason: string | null
  guardrail_status: string
}

export interface RecentCall {
  call_id: string
  created_at: string
  call_date: string | null
  agent_name: string
  customer_name: string | null
  call_outcome: string | null
  agent_performance_score: number | null
  lead_quality_score: number | null
  guardrail_status: string
  source: CallSource
}

export interface PeriodWindow {
  period: OverviewPeriod
  current_start: string
  current_end: string
  previous_start: string
  previous_end: string
  current_window_inclusive_of_now: boolean
}

export interface DataQuality {
  loaded_records: number
  skipped_malformed_records: number
  current_period_records: number
  previous_period_records: number
}

export interface OverviewSummary {
  period: PeriodWindow
  generated_at: string
  executive_summary: string
  kpis: OverviewKpis
  close_rate_trend: TrendBucket[]
  improved_agents: ImprovedAgent[]
  attention_calls: AttentionCall[]
  recent_calls: RecentCall[]
  data_quality: DataQuality
}

/** Human-readable labels for the backend's attention categories. */
export const ATTENTION_CATEGORY_LABELS: Record<AttentionCategory, string> = {
  recoverable_opportunity: 'Recoverable opportunity',
  human_review: 'Human review',
  customer_dissatisfaction: 'Customer dissatisfaction',
  critical_coaching: 'Critical coaching',
  evidence_conflict: 'Evidence conflict',
  low_priority: 'Low priority',
}
