import styles from './RankedBarChart.module.css'

export interface RankedBar {
  key: string
  label: string
  /** Null renders as "not scored" rather than a zero-length bar. */
  value: number | null
  /** How many calls back this value. Drives the low-sample caveat. */
  sampleSize: number
  /** Optional secondary fact shown beside the bar, e.g. "2 need attention". */
  meta?: string
  href?: string
}

export interface RankedBarChartProps {
  bars: RankedBar[]
  /** Fixed domain. Never derived from the data -- see note below. */
  max: number
  /** Below this, the value is shown but explicitly marked as low-sample. */
  minConfidentSample?: number
  formatValue?: (value: number) => string
}

/**
 * Ranked comparison on a fixed scale.
 *
 * Two deliberate honesty rules:
 *
 * 1. `max` is a fixed domain supplied by the caller (5 for a /5 score),
 *    never `Math.max(...values)`. Auto-scaling makes a 0.2 spread fill the
 *    whole chart and reads as a dramatic gap that does not exist.
 * 2. Sample size is always visible, and anything under `minConfidentSample`
 *    is visually de-emphasised and labelled. Ranking someone bottom of the
 *    team on a single call is not a finding, and the chart should not imply
 *    it is.
 */
export default function RankedBarChart({
  bars,
  max,
  minConfidentSample = 3,
  formatValue = (v) => v.toFixed(1),
}: RankedBarChartProps) {
  if (bars.length === 0) return null

  return (
    <ul className={styles.list}>
      {bars.map((bar) => {
        const lowSample = bar.sampleSize < minConfidentSample
        const pct = bar.value === null ? 0 : Math.min(100, (bar.value / max) * 100)
        const RowTag = bar.href ? 'a' : 'div'
        const rowProps = bar.href ? { href: bar.href } : {}

        return (
          <li key={bar.key}>
            <RowTag
              {...rowProps}
              className={[styles.row, bar.href ? styles.rowLink : ''].join(' ')}
              aria-label={
                bar.value === null
                  ? `${bar.label}: not scored, ${bar.sampleSize} calls`
                  : `${bar.label}: ${formatValue(bar.value)} out of ${max}, based on ${bar.sampleSize} calls${lowSample ? ', low sample' : ''}`
              }
            >
              <span className={styles.label}>{bar.label}</span>

              <span className={styles.track}>
                <span
                  className={[styles.fill, lowSample ? styles.fillLowSample : ''].join(' ')}
                  style={{ width: `${pct}%` }}
                />
              </span>

              <span className={[styles.value, bar.value === null ? styles.valueMissing : ''].join(' ')}>
                {bar.value === null ? '—' : formatValue(bar.value)}
                <span className={styles.max}>/ {max}</span>
              </span>

              <span className={styles.sample}>
                {bar.sampleSize} call{bar.sampleSize === 1 ? '' : 's'}
                {lowSample && <span className={styles.lowSampleTag}>low sample</span>}
              </span>

              {bar.meta && <span className={styles.meta}>{bar.meta}</span>}
            </RowTag>
          </li>
        )
      })}
    </ul>
  )
}
