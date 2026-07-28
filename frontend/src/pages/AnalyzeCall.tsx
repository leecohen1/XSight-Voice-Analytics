import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { CallStatus } from '../types'
import { uploadCall } from '../services/callsApi'
import { HttpError } from '../services/httpClient'
import PageHeader from '../components/ui/PageHeader'
import SectionCard from '../components/ui/SectionCard'
import Button from '../components/ui/Button'
import Waveform from '../components/visual/Waveform'
import { generateAmbientBars } from '../components/visual/generateAmbientBars'
import { CheckCircleIcon, UploadIcon, XCircleIcon } from '../components/icons'
import styles from './AnalyzeCall.module.css'

const STAGE_LABELS: Record<CallStatus, string> = {
  uploaded: 'Uploaded',
  validating: 'Validating file & metadata',
  transcribing: 'Transcribing audio',
  analyzing: 'Analyzing call',
  completed: 'Analysis complete',
  human_review_required: 'Analysis complete — needs review',
  flagged: 'Analysis complete — flagged',
  failed: 'Processing failed',
}

const STAGE_ORDER: CallStatus[] = ['uploaded', 'validating', 'transcribing', 'analyzing']

type PageState = 'idle' | 'submitting' | 'processing' | 'failed'

interface FailureInfo {
  /** Short, user-facing explanation — never contains a raw request URL. */
  message: string
  /** The pipeline stage that rejected the request, when the backend reports one. */
  stage?: string
  /** Raw technical payload (URL, HTTP status, backend response body) — shown only in the collapsible "Technical details" section. */
  technicalDetails?: string
}

function humanizeStage(stage: string): string {
  return stage
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function toFailureInfo(err: unknown): FailureInfo {
  if (err instanceof HttpError) {
    return {
      message: err.message,
      stage: err.stage,
      technicalDetails: err.details ? JSON.stringify(err.details, null, 2) : undefined,
    }
  }
  if (err instanceof Error) {
    return { message: err.message }
  }
  return { message: 'Something went wrong while submitting the call.' }
}

export default function AnalyzeCall() {
  const navigate = useNavigate()
  const [agentName, setAgentName] = useState('')
  const [callDate, setCallDate] = useState('')
  const [customerName, setCustomerName] = useState('')
  const [notes, setNotes] = useState('')
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [pageState, setPageState] = useState<PageState>('idle')
  const [validationError, setValidationError] = useState('')
  const [currentStage, setCurrentStage] = useState<CallStatus | null>(null)
  const [failure, setFailure] = useState<FailureInfo | null>(null)
  const [persistenceWarning, setPersistenceWarning] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const waveformBars = useMemo(() => generateAmbientBars(48), [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAudioFile(e.target.files?.[0] ?? null)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) setAudioFile(file)
  }

  const resetForm = () => {
    setPageState('idle')
    setCurrentStage(null)
    setFailure(null)
    setPersistenceWarning(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setValidationError('')

    if (!audioFile) {
      setValidationError('Please choose an audio file to upload.')
      return
    }
    if (!agentName.trim() || !callDate) {
      setValidationError('Agent name and call date are required.')
      return
    }

    setPageState('submitting')
    setCurrentStage('uploaded')
    try {
      const response = await uploadCall({ audioFile, agentName, callDate, customerName, notes })
      setPageState('processing')

      // The backend owns the id. n8n minted CALL_<uuid4> before the pipeline
      // ran and call_data_service stored the record under it, so this route
      // resolves against real storage and survives a refresh.
      if (!response.call_id) {
        throw new Error('The analysis completed but the pipeline did not return a call id.')
      }

      // A persistence failure must not cost the user their analysis: the
      // result is complete and was returned. Warn, then still navigate --
      // Call Details falls back to the just-returned analysis if the record
      // is not yet readable.
      if (response.persistence && response.persistence.persisted === false) {
        setPersistenceWarning(
          'This analysis completed successfully but could not be saved, so it may not appear in Overview or Calls.'
        )
      }

      navigate(`/calls/${response.call_id}`, { state: { justAnalyzed: response } })
    } catch (err) {
      setPageState('failed')
      setFailure(toFailureInfo(err))
    }
  }

  const isSubmitting = pageState === 'submitting' || pageState === 'processing'
  const currentIndex = currentStage ? STAGE_ORDER.indexOf(currentStage) : -1
  const progressPct = currentIndex >= 0 ? (currentIndex / (STAGE_ORDER.length - 1)) * 100 : 0
  const isProcessing = pageState === 'submitting' || pageState === 'processing'

  return (
    <>
      <PageHeader
        eyebrow="New Analysis"
        title="Analyze Call"
        insight="Upload a recorded sales call and XSight will transcribe it, extract structured insights, and ground its findings against similar historical calls."
      />

      <span className={styles.modeIndicator}>Mode: Live (n8n webhook)</span>

      {persistenceWarning && (
        <div className={styles.errorBanner} role="status">
          {persistenceWarning}
        </div>
      )}

      <div className={styles.layout}>
        <SectionCard title="Call Submission">
          <form className={styles.form} onSubmit={handleSubmit}>
            <div className={styles.field}>
              <label htmlFor="audio-file">Audio file *</label>
              <div
                className={[
                  styles.fileDrop,
                  audioFile ? styles.fileDropSelected : '',
                  isDragging ? styles.fileDropDragging : '',
                ].join(' ')}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault()
                  setIsDragging(true)
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click()
                }}
              >
                <span className={styles.fileDropIcon}>
                  <UploadIcon size={22} />
                </span>
                <p className={styles.fileDropLabel}>{audioFile ? audioFile.name : 'Drop an audio file here, or click to browse'}</p>
                <p className={styles.fileDropHint}>MP3, WAV, M4A, FLAC, or OGG</p>
              </div>
              <input
                ref={fileInputRef}
                id="audio-file"
                type="file"
                accept="audio/*"
                onChange={handleFileChange}
                disabled={isSubmitting}
                className="visually-hidden"
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="agent-name">Agent name *</label>
              <input
                id="agent-name"
                type="text"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
                placeholder="e.g. Sarah Levi"
                disabled={isSubmitting}
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="call-date">Call date *</label>
              <input
                id="call-date"
                type="date"
                value={callDate}
                onChange={(e) => setCallDate(e.target.value)}
                disabled={isSubmitting}
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="customer-name">Customer / company name (optional)</label>
              <input
                id="customer-name"
                type="text"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="e.g. Northwind Solutions"
                disabled={isSubmitting}
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="notes">Notes (optional)</label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Any extra context about this call"
                disabled={isSubmitting}
              />
              <span className={styles.hint}>File validation (format, size, duration) is enforced server-side by the Guardrails Service.</span>
            </div>

            {validationError && <div className={styles.errorBanner} role="alert">{validationError}</div>}

            <Button type="submit" loading={isSubmitting} disabled={isSubmitting}>
              {isSubmitting ? 'Analyzing…' : 'Submit for Analysis'}
            </Button>
          </form>
        </SectionCard>

        <SectionCard title="Processing Status">
          {pageState === 'idle' && (
            <>
              <div className={styles.processingVisual}>
                <Waveform bars={waveformBars} tone="neutral" height={56} barWidth={3} gap={3} ariaLabel="Idle" />
                <span className={styles.processingCaption}>Waiting for a call</span>
              </div>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', textAlign: 'center' }}>
                Submit a call to see live processing status here.
              </p>
            </>
          )}

          {isProcessing && (
            <>
              <div className={styles.processingVisual}>
                <Waveform bars={waveformBars} tone="accent" animated height={56} barWidth={3} gap={3} ariaLabel="Listening" />
                <span className={styles.processingCaption}>Listening…</span>
              </div>
              <div className={styles.stageTrack}>
                <span className={styles.stageTrackLine} aria-hidden="true" />
                <span className={styles.stageTrackFill} style={{ height: `${progressPct}%` }} aria-hidden="true" />
                {STAGE_ORDER.map((stage) => {
                  const stageIndex = STAGE_ORDER.indexOf(stage)
                  const done = currentIndex > stageIndex
                  const active = currentStage === stage
                  return (
                    <div key={stage} className={[styles.stage, active ? styles.stageActive : '', done ? styles.stageDone : ''].join(' ')}>
                      <span className={styles.stageIcon}>{active ? <span className={styles.stagePulse} /> : done ? <CheckCircleIcon size={13} /> : null}</span>
                      {STAGE_LABELS[stage]}
                    </div>
                  )
                })}
              </div>
            </>
          )}

          {pageState === 'failed' && failure && (
            <div className={styles.resultBox}>
              <div className={[styles.stage, styles.stageActive].join(' ')} style={{ color: 'var(--color-status-danger)' }}>
                <XCircleIcon size={20} />
                Processing failed
              </div>
              {failure.stage && <span className={styles.failureStage}>Failed during: {humanizeStage(failure.stage)}</span>}
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>{failure.message}</p>
              <Button variant="secondary" onClick={resetForm} type="button">
                Try again
              </Button>
              {failure.technicalDetails && (
                <details className={styles.technicalDetails}>
                  <summary>Technical details</summary>
                  <pre>{failure.technicalDetails}</pre>
                </details>
              )}
            </div>
          )}
        </SectionCard>
      </div>
    </>
  )
}
