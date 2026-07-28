import type { CSSProperties } from 'react'
import styles from './Waveform.module.css'

export interface WaveformBar {
  /** 0–1 */
  height: number
  /** CSS color value; defaults to the `tone` color. */
  color?: string
  active?: boolean
}

export type WaveformTone = 'accent' | 'evidence' | 'neutral'

const TONE_VAR: Record<WaveformTone, string> = {
  accent: 'var(--color-accent)',
  evidence: 'var(--color-evidence)',
  neutral: 'var(--color-text-secondary)',
}

export interface WaveformProps {
  bars: WaveformBar[]
  /** Pulses each bar with a staggered idle animation — reserved for Overview's hero and Analyze Call's live processing state. Transcript navigation uses static bars. */
  animated?: boolean
  tone?: WaveformTone
  height?: number
  barWidth?: number
  gap?: number
  onBarClick?: (index: number) => void
  ariaLabel?: string
}

/**
 * XSight's signature visual — a real waveform, not a decorative
 * abstraction. Used in exactly three places per the approved direction:
 * the Overview hero, Analyze Call's live processing state, and the
 * transcript navigator inside Call Details. Never inside a card or
 * repeated per-row.
 */
export default function Waveform({
  bars,
  animated = false,
  tone = 'neutral',
  height = 64,
  barWidth = 3,
  gap = 3,
  onBarClick,
  ariaLabel,
}: WaveformProps) {
  const defaultColor = TONE_VAR[tone]

  return (
    <div
      className={styles.wrap}
      style={{ ['--waveform-height' as string]: `${height}px`, gap }}
      role={ariaLabel ? 'img' : undefined}
      aria-label={ariaLabel}
    >
      {bars.map((bar, i) => {
        const barHeight = Math.max(0.06, Math.min(1, bar.height)) * height
        const color = bar.color ?? (bar.active ? 'var(--color-text-primary)' : defaultColor)
        const commonStyle: CSSProperties = {
          width: barWidth,
          height: barHeight,
          background: color,
          opacity: bar.active ? 1 : 0.75,
          ['--bar-delay' as string]: `${(i % 12) * 0.12}s`,
        }
        const className = [styles.bar, animated ? styles.barAnimated : '', onBarClick ? styles.barButton : ''].join(' ')

        if (onBarClick) {
          return (
            <button
              key={i}
              type="button"
              className={className}
              style={commonStyle}
              onClick={() => onBarClick(i)}
              aria-label={`Segment ${i + 1}`}
            />
          )
        }
        return <span key={i} className={className} style={commonStyle} />
      })}
    </div>
  )
}
