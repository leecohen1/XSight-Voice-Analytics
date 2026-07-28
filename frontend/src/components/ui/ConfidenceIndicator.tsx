import Meter, { type MeterTone } from './Meter'
import styles from './ConfidenceIndicator.module.css'

const AUTO_APPROVE_THRESHOLD = 0.65

export interface ConfidenceIndicatorProps {
  confidence: number
  showCaption?: boolean
}

function confidenceTone(confidence: number, belowThreshold: boolean): MeterTone {
  if (belowThreshold) return 'review'
  if (confidence >= 0.85) return 'success'
  return 'evidence'
}

/** Instrument-style confidence meter — replaces the old ring/bar. Color carries meaning: review (below threshold), evidence-teal (measured, solid), success (high confidence) — never a generic gradient. */
export default function ConfidenceIndicator({ confidence, showCaption = true }: ConfidenceIndicatorProps) {
  const pct = Math.round(confidence * 100)
  const belowThreshold = confidence < AUTO_APPROVE_THRESHOLD
  const tone = confidenceTone(confidence, belowThreshold)

  return (
    <div className={styles.wrap}>
      <div className={styles.labelRow}>
        <span className={styles.label}>Confidence</span>
        <span className={styles.value}>{pct}%</span>
      </div>
      <Meter value={confidence} tone={tone} segments={20} size={16} ariaLabel="Confidence" />
      {showCaption && (
        <span className={styles.caption}>
          {belowThreshold ? 'Below the 65% auto-approve threshold' : 'Above the 65% auto-approve threshold'}
        </span>
      )}
    </div>
  )
}
