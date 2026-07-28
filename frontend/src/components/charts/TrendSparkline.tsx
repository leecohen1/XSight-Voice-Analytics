import type { TrendPoint } from '../../types'

export interface TrendSparklineProps {
  data: TrendPoint[]
  width?: number
  height?: number
  color?: string
  formatValue?: (value: number) => string
}

/**
 * A minimal hand-rolled SVG line chart — deliberately not a charting
 * library. This app never needs more than "one trend line," so a library
 * would be a dependency for a problem 40 lines of SVG already solves.
 */
export default function TrendSparkline({ data, width = 560, height = 140, color = 'var(--color-evidence)', formatValue }: TrendSparklineProps) {
  if (data.length === 0) return null

  const padding = 8
  const values = data.map((d) => d.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  const points = data.map((d, i) => {
    const x = padding + (i / Math.max(data.length - 1, 1)) * (width - padding * 2)
    const y = height - padding - ((d.value - min) / range) * (height - padding * 2)
    return { x, y, ...d }
  })

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  const areaPath = `${linePath} L ${points[points.length - 1].x.toFixed(1)} ${height - padding} L ${points[0].x.toFixed(1)} ${height - padding} Z`

  const gradientId = 'trend-fill'

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Trend over time" preserveAspectRatio="none" style={{ display: 'block' }}>
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.28" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${gradientId})`} stroke="none" />
      <path d={linePath} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
      {points.map((p, i) => (
        <g key={i}>
          <circle cx={p.x} cy={p.y} r={i === points.length - 1 ? 4 : 2.5} fill={color} />
          <title>
            {p.date}: {formatValue ? formatValue(p.value) : p.value}
          </title>
        </g>
      ))}
    </svg>
  )
}
