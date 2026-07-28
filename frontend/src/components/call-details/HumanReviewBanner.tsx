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
 * For flagged/human_review_required, limitations and the specific router
 * reasons are shown inline rather than left for the user to hunt down.
 */
export default function HumanReviewBanner({ guardrailStatus, limitations, humanReviewReasons }: HumanReviewBannerProps) {
  const copy = COPY[guardrailStatus]
  const isUrgent = guardrailStatus !== 'pass'

  return (
    <div className={[styles.banner, copy.className].join(' ')} role={isUrgent ? 'alert' : 'status'}>
      <div className={styles.title}>
        <copy.Icon size={16} />
        {copy.label}
      </div>
      {isUrgent && limitations && <p className={styles.detail}>{limitations}</p>}
      {isUrgent && humanReviewReasons && humanReviewReasons.length > 0 && (
        <ul className={styles.reasonList}>
          {humanReviewReasons.map((reason) => (
            <li key={reason.code}>{reason.detail}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
