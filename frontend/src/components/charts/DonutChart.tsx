import styles from './DonutChart.module.css'

export interface DonutSlice {
  key: string
  label: string
  value: number
  /** CSS colour token. Semantic, never decorative. */
  color: string
}

export interface DonutChartProps {
  slices: DonutSlice[]
  /** Rendered in the hole. Usually the total the slices sum to. */
  centerValue: string
  centerLabel: string
  size?: number
}

/**
 * Outcome distribution.
 *
 * A donut is appropriate here for the one case it is actually good at:
 * a handful of mutually exclusive parts of a single known whole. The
 * legend carries both count and percentage because a ring alone cannot
 * be read precisely, and the centre states the total so the parts can be
 * checked against it at a glance.
 */
export default function DonutChart({ slices, centerValue, centerLabel, size = 168 }: DonutChartProps) {
  const total = slices.reduce((sum, s) => sum + s.value, 0)
  const stroke = 22
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius

  if (total === 0) {
    return (
      <div className={styles.wrap}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="No outcomes recorded">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--color-border-subtle)"
            strokeWidth={stroke}
          />
          <text x="50%" y="50%" className={styles.centerValue} textAnchor="middle" dominantBaseline="central">
            0
          </text>
        </svg>
        <p className={styles.emptyNote}>No outcomes recorded in this period.</p>
      </div>
    )
  }

  let offset = 0
  const arcs = slices
    .filter((s) => s.value > 0)
    .map((slice) => {
      const fraction = slice.value / total
      const arc = { ...slice, fraction, dash: fraction * circumference, offset }
      offset += fraction * circumference
      return arc
    })

  const summary = slices
    .map((s) => `${s.label}: ${s.value} (${total > 0 ? Math.round((s.value / total) * 100) : 0}%)`)
    .join(', ')

  return (
    <div className={styles.wrap}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`Outcome distribution. ${summary}`}>
        <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
          {arcs.map((arc) => (
            <circle
              key={arc.key}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={arc.color}
              strokeWidth={stroke}
              strokeDasharray={`${arc.dash} ${circumference - arc.dash}`}
              strokeDashoffset={-arc.offset}
            />
          ))}
        </g>
        <text x="50%" y="46%" className={styles.centerValue} textAnchor="middle" dominantBaseline="central">
          {centerValue}
        </text>
        <text x="50%" y="61%" className={styles.centerLabel} textAnchor="middle" dominantBaseline="central">
          {centerLabel}
        </text>
      </svg>

      <ul className={styles.legend}>
        {slices.map((slice) => {
          const pct = total > 0 ? (slice.value / total) * 100 : 0
          return (
            <li className={styles.legendRow} key={slice.key}>
              <span className={styles.legendSwatch} style={{ background: slice.color }} aria-hidden="true" />
              <span className={styles.legendLabel}>{slice.label}</span>
              <span className={styles.legendCount}>{slice.value}</span>
              <span className={styles.legendPct}>{pct.toFixed(1)}%</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
