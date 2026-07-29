/**
 * Semantic meaning for dashboard metrics.
 *
 * The rule this module exists to enforce: a number's colour and its
 * trend arrow must be derived from what the number *means*, never from
 * where its card happens to sit in a grid. Before this existed, "Needs
 * Attention" rendered in a calm violet purely because it was third in a
 * list, and every comparison caption was the same neutral grey whether
 * the movement was good news or bad.
 *
 * Direction is metric-specific and cannot be generalised:
 *   - close rate up            -> good
 *   - calls needing attention up -> bad
 *   - calls analysed up        -> neither (it is volume, not performance)
 *
 * Everything here is pure and deterministic. No LLM writes dashboard copy.
 */
import type { KpiMetric } from '../types'

/** How a metric should be read when it moves. */
export type MetricPolarity =
  /** Higher is better (close rate, performance scores). */
  | 'higher_is_better'
  /** Lower is better (calls needing attention). */
  | 'lower_is_better'
  /** Movement carries no inherent verdict (volume counts). */
  | 'neutral'

/** Semantic role driving colour. Maps onto the existing status tokens. */
export type MetricTone = 'neutral' | 'success' | 'warning' | 'critical' | 'muted'

/** Which way the value moved, independent of whether that is good. */
export type MetricDirection = 'up' | 'down' | 'flat' | 'unknown'

/** Whether the movement is good news, bad news, or neither. */
export type MetricSentiment = 'positive' | 'negative' | 'neutral' | 'unknown'

export interface MetricSemantics {
  direction: MetricDirection
  sentiment: MetricSentiment
  tone: MetricTone
  /** Screen-reader / tooltip text, e.g. "up 5, which is an improvement". */
  ariaLabel: string
}

export const METRIC_POLARITY: Record<string, MetricPolarity> = {
  calls_analyzed: 'neutral',
  close_rate: 'higher_is_better',
  calls_requiring_attention: 'lower_is_better',
  average_agent_performance: 'higher_is_better',
  average_lead_quality: 'higher_is_better',
  improved_agents_count: 'higher_is_better',
  recovery_opportunities: 'lower_is_better',
}

function directionOf(metric: KpiMetric): MetricDirection {
  // previous_value === null means there is nothing to compare against --
  // that is "unknown", not "flat". Flat is a real measured no-change.
  if (metric.previous_value === null || metric.previous_value === undefined) return 'unknown'
  if (metric.absolute_change === null || metric.absolute_change === undefined) return 'unknown'
  if (metric.absolute_change > 0) return 'up'
  if (metric.absolute_change < 0) return 'down'
  return 'flat'
}

function sentimentOf(direction: MetricDirection, polarity: MetricPolarity): MetricSentiment {
  if (direction === 'unknown') return 'unknown'
  if (direction === 'flat') return 'neutral'
  if (polarity === 'neutral') return 'neutral'
  const movingUpIsGood = polarity === 'higher_is_better'
  const isGood = direction === 'up' ? movingUpIsGood : !movingUpIsGood
  return isGood ? 'positive' : 'negative'
}

/**
 * Tone for the *current standing* of an attention-style count, independent
 * of movement: any outstanding attention is worth colouring even when the
 * number improved. A manager cares that 2 calls need them today, not only
 * that it used to be 3.
 */
function standingTone(key: string, metric: KpiMetric): MetricTone | null {
  if (key !== 'calls_requiring_attention' && key !== 'recovery_opportunities') return null
  const value = metric.current_value
  if (value === null || value === undefined) return 'muted'
  if (value === 0) return 'success'
  return key === 'calls_requiring_attention' ? 'critical' : 'warning'
}

export function metricSemantics(key: string, metric: KpiMetric): MetricSemantics {
  const polarity = METRIC_POLARITY[key] ?? 'neutral'
  const direction = directionOf(metric)
  const sentiment = sentimentOf(direction, polarity)

  let tone: MetricTone
  if (metric.current_value === null || metric.current_value === undefined) {
    tone = 'muted'
  } else {
    tone =
      standingTone(key, metric) ??
      (sentiment === 'positive' ? 'success' : sentiment === 'negative' ? 'warning' : 'neutral')
  }

  const movement =
    direction === 'unknown'
      ? 'no comparable previous period'
      : direction === 'flat'
        ? 'unchanged versus the previous period'
        : `${direction === 'up' ? 'up' : 'down'} versus the previous period`
  const verdict =
    sentiment === 'positive'
      ? ', an improvement'
      : sentiment === 'negative'
        ? ', a decline'
        : ''

  return { direction, sentiment, tone, ariaLabel: `${movement}${verdict}` }
}

/** Arrow glyph for a direction. Never the sole carrier of meaning. */
export function directionGlyph(direction: MetricDirection): string {
  if (direction === 'up') return '▲'
  if (direction === 'down') return '▼'
  if (direction === 'flat') return '■'
  return '–'
}

// ---- Value formatting ------------------------------------------------------

export type MetricFormat = 'count' | 'percent' | 'score'

/**
 * A null value means "not measured in this window" and must never render
 * as 0 -- those are different business facts.
 */
export function formatMetricValue(value: number | null | undefined, format: MetricFormat): string {
  if (value === null || value === undefined) return '—'
  if (format === 'percent') return `${value}%`
  if (format === 'score') return value.toFixed(1)
  return String(Math.round(value))
}

/** Fixed, always-visible denominator so a score is never ambiguous. */
export function scaleSuffix(format: MetricFormat): string | null {
  return format === 'score' ? '/ 5' : null
}

/**
 * The comparison caption. Says plainly when there is nothing to compare
 * against rather than implying a change of zero.
 */
export function formatComparison(metric: KpiMetric, format: MetricFormat): string {
  if (metric.previous_value === null || metric.previous_value === undefined) {
    return 'Not enough comparison data'
  }
  if (metric.absolute_change === null || metric.absolute_change === undefined) {
    return 'No change data'
  }
  if (metric.absolute_change === 0) return 'Unchanged vs. previous period'

  const change = metric.absolute_change
  const sign = change > 0 ? '+' : ''
  const magnitude =
    format === 'score' ? change.toFixed(2) : format === 'percent' ? `${change}%` : String(Math.round(change))
  // percentage_change === null means the previous value was zero, so the
  // ratio is undefined -- omit it rather than printing a fabricated number.
  const pct =
    metric.percentage_change === null || metric.percentage_change === undefined
      ? ''
      : ` (${metric.percentage_change > 0 ? '+' : ''}${metric.percentage_change}%)`
  return `${sign}${magnitude}${pct} vs. previous period`
}
