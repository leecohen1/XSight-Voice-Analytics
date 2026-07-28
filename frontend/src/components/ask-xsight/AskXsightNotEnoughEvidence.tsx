import { AlertIcon } from '../icons'
import styles from './AskXsightNotEnoughEvidence.module.css'

export default function AskXsightNotEnoughEvidence() {
  return (
    <div className={styles.wrap}>
      <span className={styles.title}>
        <AlertIcon size={15} />
        Not enough evidence
      </span>
      <p className={styles.body}>
        XSight could not find sufficient support in the transcript, official analysis, similar calls, or review
        reasons to answer this question reliably.
      </p>
    </div>
  )
}
