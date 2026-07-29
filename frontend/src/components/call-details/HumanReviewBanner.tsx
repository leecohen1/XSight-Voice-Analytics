import type { GuardrailStatus, HumanReviewReason } from '../../types'
import { AlertIcon, CheckCircleIcon, FlagIcon } from '../icons'
import styles from './HumanReviewBanner.module.css'

const COPY: Record<GuardrailStatus, { label: string; className: string; Icon: typeof CheckCircleIcon }> = {
  pass: { label: 'Guardrails: Pass', className: styles.pass, Icon: CheckCircleIcon },
  flagged: { label: 'Flagged — Review Recommended', className: styles.flagged, Icon: FlagIcon },
  human_review_required: { label: 'Human Review Required', className: styles.review, Icon: AlertIcon },
}

export interface HumanReviewBannerProps {
  guardrailStatus: GuardrailStatus
  limitations?: string
  humanReviewReasons?: HumanReviewReason[]
}

/**
 * Loud, top-of-panel banner reflecting guardrail_status — never buried.
 *
 * A human-review or flagged result is a valid analytical outcome, not a
 * system failure, so it gets a "Why review is required" bullet list as the
 * lead content: each of the Router's specific reasons (e.g. "Low
 * confidence", "Evidence conflict"), one per line, scannable in a glance
 * rather than buried in prose. The freeform `limitations` narrative is kept
 * as supporting detail underneath, and as the sole content on the rare case
 * the Router recorded no machine-readable reason at all.
 */
export default function HumanReviewBanner({ guardrailStatus, limitations, humanReviewReasons }: HumanReviewBannerProps) {
  const copy = COPY[guardrailStatus]
  const isUrgent = guardrailStatus !== 'pass'
  const reasons = humanReviewReasons ?? []

  return (
    <div className={[styles.banner, copy.className].join(' ')} role={isUrgent ? 'alert' : 'status'}>
      <div className={styles.title}>
        <copy.Icon size={16} />
        {copy.label}
      </div>

      {isUrgent && reasons.length > 0 && (
        <>
          <span className={styles.reasonHeading}>Why review is required</span>
          <ul className={styles.reasonList}>
            {reasons.map((reason) => (
              <li key={reason.code}>{reason.label}: {reason.detail}</li>
            ))}
          </ul>
        </>
      )}

      {isUrgent && limitations && <p className={styles.detail}>{limitations}</p>}
    </div>
  )
}
