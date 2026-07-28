import type { CallEvidence } from '../../types'
import Meter from '../ui/Meter'
import styles from './EvidenceSection.module.css'

export interface EvidenceSectionProps {
  evidence: CallEvidence
}

/**
 * A channel-meter view of what each upstream service contributed —
 * console channels feeding one verdict, not a wall of text. Levels are
 * a deliberately simple, documented heuristic (citation count / stated
 * confidence / reasoning-step count), not a fabricated precision metric
 * the pipeline doesn't actually compute — shown as a relative-contribution
 * read, not an exact measurement.
 */
export default function EvidenceSection({ evidence }: EvidenceSectionProps) {
  const ragLevel = Math.min(1, evidence.ragCitations.length / 3)
  const signalLevel = evidence.signalConfidence ?? 0
  const reasoningLevel = Math.min(1, evidence.langgraphReasoningSteps.length / 4)

  return (
    <>
      <div className={styles.channels}>
        <span className={styles.channelsCaption}>Relative evidence contribution per source</span>
        <div className={styles.channelRow}>
          <span className={styles.channelName}>RAG</span>
          <Meter value={ragLevel} tone="evidence" segments={20} size={12} ariaLabel="RAG evidence contribution" />
        </div>
        <div className={styles.channelRow}>
          <span className={styles.channelName}>Signal Analysis</span>
          <Meter value={signalLevel} tone="evidence" segments={20} size={12} ariaLabel="Signal analysis contribution" />
        </div>
        <div className={styles.channelRow}>
          <span className={styles.channelName}>Reasoning</span>
          <Meter value={reasoningLevel} tone="evidence" segments={20} size={12} ariaLabel="Reasoning contribution" />
        </div>
      </div>

      {evidence.langgraphEvidenceConflicts.length > 0 && (
        <div className={styles.group}>
          <span className={styles.label}>Evidence Conflicts</span>
          {evidence.langgraphEvidenceConflicts.map((conflict, i) => (
            <p className={styles.conflict} key={i}>
              {conflict}
            </p>
          ))}
        </div>
      )}

      {evidence.ragInsight && (
        <div className={styles.group}>
          <span className={styles.label}>RAG Service Insight</span>
          <p className={styles.text}>{evidence.ragInsight}</p>
        </div>
      )}

      {evidence.signalDetectedSignals.length > 0 && (
        <div className={styles.group}>
          <span className={styles.label}>Call Signal Analyser — Detected Signals</span>
          <p className={styles.text}>{evidence.signalDetectedSignals.join(', ')}</p>
        </div>
      )}

      {evidence.langgraphReasoningSteps.length > 0 && (
        <div className={styles.group}>
          <span className={styles.label}>LangGraph Reasoning Steps</span>
          <ol className={styles.steps}>
            {evidence.langgraphReasoningSteps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      )}
    </>
  )
}
