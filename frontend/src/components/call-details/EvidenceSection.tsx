import type { CallEvidence } from '../../types'
import Meter from '../ui/Meter'
import styles from './EvidenceSection.module.css'

export interface EvidenceSectionProps {
  evidence: CallEvidence
}

/**
 * A channel-meter view of what each upstream service contributed —
 * console channels feeding one verdict, not a wall of text. Levels are a
 * deliberately simple, documented heuristic (citation count / stated
 * confidence), not a fabricated precision metric the pipeline doesn't
 * actually compute — shown as a relative-contribution read, not an exact
 * measurement.
 *
 * Only RAG and Signal Analysis are shown. `toCallRecord` (services/
 * callsApi.ts) never populates `ragInsight`, `langgraphReasoningSteps` or
 * `langgraphEvidenceConflicts` — the stored record doesn't carry LangGraph's
 * raw reasoning output at all (the Final Analysis Chain folds it into
 * coaching_feedback/recommended_next_action instead, per the documented
 * architecture), and the RAG service's insight text isn't persisted onto
 * the record either. A "Reasoning" meter or an "Evidence Conflicts"/"RAG
 * Insight" section built on permanently-empty fields would either always
 * read zero (falsely implying LangGraph contributed nothing) or simply
 * never render — internal architecture exposed for decoration rather than
 * because it can ever show real data. If those fields are ever persisted,
 * add the corresponding section back then, not before.
 */
export default function EvidenceSection({ evidence }: EvidenceSectionProps) {
  const ragLevel = Math.min(1, evidence.ragCitations.length / 3)
  const signalLevel = evidence.signalConfidence ?? 0

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
      </div>

      {evidence.signalDetectedSignals.length > 0 && (
        <div className={styles.group}>
          <span className={styles.label}>Call Signal Analyser — Detected Signals</span>
          <p className={styles.text}>{evidence.signalDetectedSignals.join(', ')}</p>
        </div>
      )}
    </>
  )
}
