import type { EvaluationStatus, RagasEvaluation } from '../../types'
import StatusBadge, { type StatusTone } from '../ui/StatusBadge'
import Meter from '../ui/Meter'
import LoadingSkeleton from '../ui/LoadingSkeleton'
import EmptyState from '../ui/EmptyState'
import styles from './QualityEvaluationPanel.module.css'

const STATUS_TONE: Record<EvaluationStatus, StatusTone> = {
  passed: 'success',
  needs_review: 'warning',
  failed: 'danger',
  not_evaluated: 'neutral',
}

const STATUS_LABEL: Record<EvaluationStatus, string> = {
  passed: 'Passed',
  needs_review: 'Needs Review',
  failed: 'Failed',
  not_evaluated: 'Not Evaluated',
}

export interface QualityEvaluationPanelProps {
  evaluation: RagasEvaluation | null
  loading?: boolean
}

/** RAGAS meters use the evidence teal — this is "evaluating the system," visually distinct from confidence meters (which evaluate a call) and from the semantic status badge (which carries the verdict color). */
export default function QualityEvaluationPanel({ evaluation, loading }: QualityEvaluationPanelProps) {
  if (loading) return <LoadingSkeleton lines={4} />
  if (!evaluation || evaluation.status === 'not_evaluated') {
    return (
      <EmptyState
        title="Not evaluated yet"
        description={evaluation?.evaluationFailures[0] ?? 'This call has not been evaluated by RAGAS yet.'}
      />
    )
  }

  return (
    <div>
      <div className={styles.header}>
        <span className={styles.overallScore}>{evaluation.overallScore.toFixed(2)}</span>
        <StatusBadge label={STATUS_LABEL[evaluation.status]} tone={STATUS_TONE[evaluation.status]} />
      </div>

      <div className={styles.metrics}>
        {evaluation.metrics.map((metric) => (
          <div className={styles.metric} key={metric.name}>
            <div className={styles.metricTop}>
              <span className={styles.metricName}>{metric.label}</span>
              <span className={styles.metricScore}>{metric.score.toFixed(2)}</span>
            </div>
            <Meter value={metric.score} tone="evidence" segments={24} size={10} ariaLabel={metric.label} />
            <span className={styles.metricExplanation}>{metric.explanation}</span>
          </div>
        ))}
      </div>

      {evaluation.notes.length > 0 && (
        <ul className={styles.notes}>
          {evaluation.notes.map((note, i) => (
            <li key={i}>{note}</li>
          ))}
        </ul>
      )}

      <p className={styles.disclaimer}>
        Evaluation Framework: RAGAS. RAGAS evaluates the generated output and retrieved context — it is not the
        official call analysis. A high score does not remove the need for guardrails, and a low score may require
        human review or further investigation.
      </p>
    </div>
  )
}
