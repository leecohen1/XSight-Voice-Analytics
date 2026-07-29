import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import type { CallRecord, PipelineResponse } from '../types'
import { getCall, pipelineResponseToRecord } from '../services/callsApi'
import CallStatusIndicator from '../components/ui/CallStatusIndicator'
import SectionCard from '../components/ui/SectionCard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import Button from '../components/ui/Button'
import OfficialAnalysisPanel from '../components/call-details/OfficialAnalysisPanel'
import EvidenceSection from '../components/call-details/EvidenceSection'
import TranscriptViewer from '../components/call-details/TranscriptViewer'
import { ClockIcon, XCircleIcon } from '../components/icons'
import styles from './CallDetails.module.css'

export default function CallDetails() {
  const { callId } = useParams<{ callId: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  /** Set only when arriving straight from a successful analysis. */
  const justAnalyzed = (location.state as { justAnalyzed?: PipelineResponse } | null)?.justAnalyzed
  const [call, setCall] = useState<CallRecord | null | undefined>(undefined)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!callId) return
    let cancelled = false
    setCall(undefined)
    setError(null)

    getCall(callId)
      .then((result) => {
        if (cancelled) return
        // A call analyzed seconds ago may not be readable yet if persistence
        // failed or is still settling. Falling back to the analysis the
        // pipeline just returned means a storage problem never costs the
        // user the result they already paid for.
        if (result === null && justAnalyzed) {
          setCall(pipelineResponseToRecord(justAnalyzed))
          return
        }
        setCall(result)
      })
      .catch((err) => {
        if (cancelled) return
        if (justAnalyzed) {
          setCall(pipelineResponseToRecord(justAnalyzed))
          return
        }
        setError(err instanceof Error ? err.message : String(err))
      })

    return () => {
      cancelled = true
    }
  }, [callId, justAnalyzed])

  if (error) return <ErrorState description={error} />
  if (call === undefined) return <LoadingSkeleton lines={8} />
  if (call === null) {
    return (
      <EmptyState
        title="Call not found"
        description={`No call with id "${callId}" exists.`}
        action={
          <Link to="/calls" style={{ color: 'var(--color-evidence)', fontSize: 'var(--text-sm)' }}>
            Back to Calls
          </Link>
        }
      />
    )
  }

  return (
    <>
      {/* The raw call id is shown once, in the header meta line below --
          repeating it here too was pure duplication. The breadcrumb's own
          last segment is the same human-readable identity as the H1, which
          is the normal breadcrumb convention, not a second copy of the id. */}
      <div className={styles.breadcrumb}>
        <Link to="/calls">Calls</Link>
        <span>/</span>
        <span>
          {call.agentName}
          {call.customerName ? ` · ${call.customerName}` : ''}
        </span>
      </div>

      <div className={styles.header}>
        <div className={styles.headerTitleGroup}>
          <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 'var(--weight-bold)' }}>
            {call.agentName}
            {call.customerName ? ` · ${call.customerName}` : ''}
          </h1>
          <div className={styles.headerMeta}>
            <CallStatusIndicator status={call.status} />
            <span>{call.callDate}</span>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>{call.callId}</span>
          </div>
        </div>
      </div>

      {/* Only calls that produced an analysis are persisted, so a stored
          record is never in a `failed` state. This branch remains for a
          record handed straight from a pipeline response. Re-analysing means
          resubmitting the audio -- there is no server-side retry endpoint. */}
      {call.status === 'failed' && (
        <SectionCard>
          <div className={styles.processingWrap}>
            <span style={{ color: 'var(--color-status-danger)', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600 }}>
              <XCircleIcon size={18} />
              Processing failed
            </span>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
              {call.failureReason ?? 'Processing failed for an unknown reason.'}
            </p>
            <Button onClick={() => navigate('/analyze')} type="button">
              Analyze Again
            </Button>
          </div>
        </SectionCard>
      )}

      {(call.status === 'uploaded' || call.status === 'validating' || call.status === 'transcribing' || call.status === 'analyzing') && (
        <SectionCard>
          <div className={styles.processingWrap}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, color: 'var(--color-status-processing)' }}>
              <ClockIcon size={18} />
              Still processing — check back shortly
            </span>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
              This call is currently in the <strong>{call.status}</strong> stage of the pipeline.
            </p>
          </div>
        </SectionCard>
      )}

      {call.analysis && call.guardrailStatus && (
        <>
          {/* humanReviewReasons reuses routerReasons -- the same shape
              (HumanReviewReason = RouterReason), and the field that is
              actually populated by the backend's router_reasons. */}
          <OfficialAnalysisPanel
            analysis={call.analysis}
            guardrailStatus={call.guardrailStatus}
            humanReviewReasons={call.routerReasons}
          />

          <div className={styles.section}>
            <SectionCard title="Evidence & Reasoning" subtitle="What each upstream service contributed" collapsible className={styles.operationalSection}>
              {call.evidence ? <EvidenceSection evidence={call.evidence} /> : <EmptyState title="No evidence trail recorded" />}
            </SectionCard>
          </div>

          {/* Collapsed by default: this supports the analysis above it, and
              an executive scanning the page should not have to pass a wall
              of raw dialogue before reaching the verdict and action -- which
              is already true, since it renders after them; collapsing it
              too keeps the initial scroll to those sections short. */}
          <div className={styles.section}>
            <SectionCard title="Full Transcript" collapsible defaultOpen={false} className={styles.operationalSection}>
              <TranscriptViewer transcript={call.analysis.transcript} />
            </SectionCard>
          </div>

          {/* AI Processing Cost, Quality Evaluation (RAGAS) and Ask XSight
              are intentionally not rendered here. Their data comes from
              aiOperationsApi/askXsightApi, which are mock-only -- no backend
              contract exists yet (see services/usage_monitoring_service for
              a candidate reference API for cost/quality). In the real
              deployed configuration (VITE_USE_MOCK=false) they always threw
              and silently resolved to "not shown", so every real call showed
              three permanently-empty collapsed sections. Removed rather than
              replaced with fake data or a "Coming Soon" block; see
              docs/PROGRESS.md for the future-module note. The components
              (UsageCostPanel, QualityEvaluationPanel, AskXsightPanel) and
              their APIs are untouched and ready to reconnect once a real
              contract exists. */}
        </>
      )}
    </>
  )
}
