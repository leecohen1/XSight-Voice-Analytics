import styles from './PeriodTrendChart.module.css'

export interface TrendBucketPoint {
  label: string
  value: number | null
  /** Calls behind this bucket. Drives bar opacity and the caveat line. */
  sampleSize: number
}

export interface PeriodTrendChartProps {
  buckets: TrendBucketPoint[]
  /** Fixed upper bound of the domain. 100 for %, 5 for scores. */
  max: number
  unit?: string
  /** Buckets below this are drawn muted and flagged as thin evidence. */
  minConfidentSample?: number
  ariaLabel: string
}

/**
 * Period trend as fixed-domain bars.
 *
 * Replaces an auto-scaled sparkline. The old chart set its Y-axis to the
 * visible min/max, so a 3-point move in close rate filled the entire chart
 * height and read as a collapse. Here the domain is always 0..max, so the
 * height of a bar means the same thing on every render and between screens.
 *
 * Buckets are period-level, not daily: with a small corpus a daily line is
 * mostly one-call noise, and a bar chart of a handful of periods is both
 * more honest and easier to read than a jagged line.
 */
export default function PeriodTrendChart({
  buckets,
  max,
  unit = '',
  minConfidentSample = 3,
  ariaLabel,
}: PeriodTrendChartProps) {
  if (buckets.length === 0) {
    return <p className={styles.empty}>No data in this period yet.</p>
  }

  const measured = buckets.filter((b) => b.value !== null)
  if (measured.length === 0) {
    return <p className={styles.empty}>No scored calls in this period yet.</p>
  }

  const thin = buckets.filter((b) => b.value !== null && b.sampleSize < minConfidentSample).length
  const gridLines = [0, 0.25, 0.5, 0.75, 1]

  return (
    <div className={styles.wrap}>
      <div className={styles.plot} role="img" aria-label={ariaLabel}>
        {/* Fixed reference grid -- the anchor that makes bar heights comparable. */}
        <div className={styles.gridLayer} aria-hidden="true">
          {gridLines.map((g) => (
            <div className={styles.gridLine} key={g} style={{ bottom: `${g * 100}%` }}>
              <span className={styles.gridLabel}>
                {Math.round(max * g)}
                {unit}
              </span>
            </div>
          ))}
        </div>

        <div className={styles.bars}>
          {buckets.map((bucket) => {
            const isMissing = bucket.value === null
            const lowSample = !isMissing && bucket.sampleSize < minConfidentSample
            const heightPct = isMissing ? 0 : Math.min(100, (bucket.value! / max) * 100)
            return (
              <div className={styles.barCol} key={bucket.label}>
                <div className={styles.barTrack}>
                  {isMissing ? (
                    <span className={styles.noData}>—</span>
                  ) : (
                    <>
                      <span className={styles.barValue}>
                        {bucket.value}
                        {unit}
                      </span>
                      <span
                        className={[styles.bar, lowSample ? styles.barLowSample : ''].join(' ')}
                        style={{ height: `${heightPct}%` }}
                      />
                    </>
                  )}
                </div>
                <span className={styles.barLabel}>{bucket.label}</span>
                <span className={styles.barSample}>
                  {bucket.sampleSize} call{bucket.sampleSize === 1 ? '' : 's'}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {thin > 0 && (
        <p className={styles.caveat}>
          {thin} period{thin === 1 ? '' : 's'} shown with fewer than {minConfidentSample} calls — read those bars as
          indicative, not conclusive.
        </p>
      )}
    </div>
  )
}
