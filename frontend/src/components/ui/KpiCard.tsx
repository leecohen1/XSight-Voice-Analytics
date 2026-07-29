import type { ReactNode } from 'react'
import type { KpiMetric } from '../../types'
import {
  directionGlyph,
  formatComparison,
  formatMetricValue,
  metricSemantics,
  scaleSuffix,
  type MetricFormat,
} from '../../analytics/kpiSemantics'
import styles from './KpiCard.module.css'

export interface KpiCardProps {
  /** Metric key -- drives polarity, so it must match the backend's name. */
  metricKey: string
  label: string
  metric: KpiMetric
  format: MetricFormat
  /** Denominator or clarifier, e.g. "of 19 calls with a known outcome". */
  context?: string
  icon?: ReactNode
  /** Supporting metrics render smaller so they don't rival the primary row. */
  variant?: 'primary' | 'supporting'
}

/**
 * A KPI whose colour means something.
 *
 * Tone and trend sentiment come from `metricSemantics`, not from the card's
 * position in a grid. The same +2 renders as good news on close rate and as
 * bad news on calls-needing-attention, which is the entire point.
 *
 * Direction is carried by an arrow glyph and by text as well as colour, so
 * it survives greyscale and colour-blindness.
 */
export default function KpiCard({
  metricKey,
  label,
  metric,
  format,
  context,
  icon,
  variant = 'primary',
}: KpiCardProps) {
  const { direction, sentiment, tone, ariaLabel } = metricSemantics(metricKey, metric)
  const value = formatMetricValue(metric.current_value, format)
  const suffix = scaleSuffix(format)
  const comparison = formatComparison(metric, format)
  const hasComparison = direction !== 'unknown'

  return (
    <article className={[styles.card, styles[`variant_${variant}`], styles[`tone_${tone}`]].join(' ')}>
      <header className={styles.head}>
        <span className={styles.label}>{label}</span>
        {icon && <span className={styles.icon} aria-hidden="true">{icon}</span>}
      </header>

      <p className={styles.value}>
        {value}
        {suffix && <span className={styles.suffix}>{suffix}</span>}
      </p>

      <p className={[styles.comparison, styles[`sentiment_${sentiment}`]].join(' ')} aria-label={ariaLabel}>
        {hasComparison && (
          <span className={styles.arrow} aria-hidden="true">
            {directionGlyph(direction)}
          </span>
        )}
        {comparison}
      </p>

      {context && <p className={styles.context}>{context}</p>}
    </article>
  )
}
