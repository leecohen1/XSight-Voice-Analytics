import styles from './Meter.module.css'

export type MeterTone = 'accent' | 'evidence' | 'success' | 'warning' | 'danger' | 'review' | 'neutral'

const TONE_VAR: Record<MeterTone, string> = {
  accent: 'var(--color-accent)',
  evidence: 'var(--color-evidence)',
  success: 'var(--color-status-success)',
  warning: 'var(--color-status-warning)',
  danger: 'var(--color-status-danger)',
  review: 'var(--color-status-review)',
  neutral: 'var(--color-status-neutral)',
}

export interface MeterProps {
  /** 0–1 */
  value: number
  tone?: MeterTone
  segments?: number
  orientation?: 'horizontal' | 'vertical'
  /** Segment thickness/length — px. */
  size?: number
  label?: string
  ariaLabel: string
}

/**
 * Instrument-style segmented meter — a VU meter, not a smooth progress
 * bar or ring. Used for confidence, evidence-channel contribution, and
 * anywhere else a measured quantity (not a completion percentage) needs
 * a visual. Segments light discretely rather than filling continuously,
 * matching the Signal Room "measured, not decorated" language.
 */
export default function Meter({ value, tone = 'accent', segments = 16, orientation = 'horizontal', size = 14, label, ariaLabel }: MeterProps) {
  const clamped = Math.max(0, Math.min(1, value))
  const litCount = Math.round(clamped * segments)
  const color = TONE_VAR[tone]

  return (
    <div className={[styles.wrap, orientation === 'vertical' ? styles.wrapVertical : ''].join(' ')}>
      {label && <span className={styles.label}>{label}</span>}
      <div
        className={[styles.track, orientation === 'vertical' ? styles.trackVertical : styles.trackHorizontal].join(' ')}
        role="meter"
        aria-valuenow={Math.round(clamped * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={ariaLabel}
      >
        {Array.from({ length: segments }).map((_, i) => {
          const lit = i < litCount
          const dimension = orientation === 'vertical' ? { width: size, height: 4 } : { width: 4, height: size }
          return (
            <span
              key={i}
              className={[styles.segment, orientation === 'vertical' ? styles.segmentVertical : styles.segmentHorizontal].join(' ')}
              style={{ ...dimension, background: lit ? color : undefined }}
            />
          )
        })}
      </div>
    </div>
  )
}
