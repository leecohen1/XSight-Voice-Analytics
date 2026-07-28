import type { CallAnalysisResult, GuardrailStatus, HumanReviewReason } from '../../types'
import StatusBadge, { type StatusTone } from '../ui/StatusBadge'
import ConfidenceIndicator from '../ui/ConfidenceIndicator'
import SectionCard from '../ui/SectionCard'
import HumanReviewBanner from './HumanReviewBanner'
import SimilarCallsList from './SimilarCallsList'
import CoachingFeedbackList from './CoachingFeedbackList'
import { CheckCircleIcon, FlagIcon } from '../icons'
import styles from './OfficialAnalysisPanel.module.css'

function sentimentTone(sentiment: string): StatusTone {
  if (sentiment === 'positive') return 'success'
  if (sentiment === 'negative') return 'danger'
  return 'neutral'
}

function outcomeTone(outcome: string): StatusTone {
  if (outcome === 'Sale') return 'success'
  if (outcome === 'No Sale') return 'danger'
  return 'neutral'
}

function riskTone(risk: string): StatusTone {
  if (risk === 'Low') return 'success'
  if (risk === 'High') return 'danger'
  return 'warning'
}

export interface OfficialAnalysisPanelProps {
  analysis: CallAnalysisResult
  guardrailStatus: GuardrailStatus
  humanReviewReasons?: HumanReviewReason[]
}

/**
 * The dominant, always-visible section of Call Details — never competing
 * visually with Ask XSight, which is opened separately and stays secondary.
 * Order is deliberate, per the approved Signal Room hierarchy: 1. verdict
 * (flat strip — outcome/risk/routing + confidence meter) → 2. Recommended
 * Next Action (the ONE lit amber element on this page) → 3. key call
 * understanding (summary, intent, objection, signals) → 4. similar calls
 * → coaching/email/limitations as supporting detail.
 */
export default function OfficialAnalysisPanel({ analysis, guardrailStatus, humanReviewReasons }: OfficialAnalysisPanelProps) {
  return (
    <div className={styles.wrap}>
      <div className={styles.eyebrow}>
        <span className={styles.eyebrowLabel}>
          <CheckCircleIcon size={14} />
          Official XSight Analysis
        </span>
        <span className={styles.eyebrowCaption}>Validated pipeline output</span>
      </div>

      <HumanReviewBanner guardrailStatus={guardrailStatus} limitations={analysis.limitations} humanReviewReasons={humanReviewReasons} />

      {/* 1. Verdict strip */}
      <SectionCard className={styles.heroCard}>
        <div className={styles.hero}>
          <div className={styles.heroLeft}>
            {/* Seeded historical records legitimately lack risk level,
                confidence and routing category — those are rendered as
                "not recorded" rather than as a fabricated default. */}
            <div className={styles.badgeRow}>
              <StatusBadge
                label={`Outcome: ${analysis.call_outcome ?? 'not recorded'}`}
                tone={analysis.call_outcome ? outcomeTone(analysis.call_outcome) : 'neutral'}
              />
              <StatusBadge
                label={`Sentiment: ${analysis.customer_sentiment ?? 'not recorded'}`}
                tone={analysis.customer_sentiment ? sentimentTone(analysis.customer_sentiment) : 'neutral'}
              />
              {analysis.risk_level && (
                <StatusBadge label={`Risk: ${analysis.risk_level}`} tone={riskTone(analysis.risk_level)} />
              )}
              {analysis.routing_category && (
                <StatusBadge label={`Routing: ${analysis.routing_category}`} tone="neutral" />
              )}
            </div>
            <div className={styles.scoreRow}>
              <div className={styles.scoreBadge}>
                <span className={styles.scoreLabel}>Agent Performance</span>
                <span className={styles.scoreValue}>
                  {analysis.agent_performance_score ?? '—'} <span className={styles.scoreMax}>/ 5</span>
                </span>
              </div>
              <div className={styles.scoreBadge}>
                <span className={styles.scoreLabel}>Lead Quality</span>
                <span className={styles.scoreValue}>
                  {analysis.lead_quality_score ?? '—'} <span className={styles.scoreMax}>/ 5</span>
                </span>
              </div>
            </div>
          </div>
          {analysis.confidence !== null && analysis.confidence !== undefined && (
            <ConfidenceIndicator confidence={analysis.confidence} />
          )}
        </div>
      </SectionCard>

      {/* 2. Recommended Next Action — the one lit element on this page */}
      <div className={styles.actionCallout}>
        <span className={styles.actionCalloutIcon}>
          <FlagIcon size={17} />
        </span>
        <div className={styles.actionCalloutBody}>
          <span className={styles.actionCalloutLabel}>Recommended Next Action</span>
          <p className={styles.actionCalloutText}>
            {analysis.recommended_next_action ?? 'No next action was recorded for this call.'}
          </p>
        </div>
      </div>

      {/* 3. Key call understanding */}
      <SectionCard title="Call Summary">
        <p className={styles.fieldValue}>{analysis.call_summary}</p>
      </SectionCard>

      <div className={styles.grid2}>
        <SectionCard title="Customer Intent">
          <p className={styles.fieldValue}>{analysis.customer_intent}</p>
        </SectionCard>
        <SectionCard title="Main Objection">
          <p className={styles.fieldValue}>{analysis.main_objection}</p>
        </SectionCard>
      </div>

      <SectionCard title="Detected Signals">
        {analysis.detected_signals.length > 0 ? (
          <div className={styles.tagList}>
            {analysis.detected_signals.map((signal, i) => (
              <span className={styles.tag} key={i}>
                {signal}
              </span>
            ))}
          </div>
        ) : (
          <p className={styles.fieldValue}>None detected.</p>
        )}
      </SectionCard>

      {/* 4. Similar calls */}
      <SectionCard title="Similar Historical Calls" subtitle="Grounded evidence with call_id citations">
        <SimilarCallsList calls={analysis.similar_calls} />
      </SectionCard>

      {/* Supporting detail */}
      <SectionCard title="Coaching Feedback">
        <CoachingFeedbackList feedback={analysis.coaching_feedback} />
      </SectionCard>

      <SectionCard title="Suggested Follow-up Email" collapsible defaultOpen>
        <pre className={styles.emailBlock}>{analysis.suggested_follow_up_email}</pre>
      </SectionCard>

      <SectionCard title="Limitations">
        <p className={styles.limitations}>{analysis.limitations}</p>
      </SectionCard>
    </div>
  )
}
