/**
 * Call domain types.
 *
 * `CallAnalysisResult` mirrors CLAUDE.md's "Final output JSON schema" — the
 * backend/frontend contract — field for field. It is never extended with
 * persistence concerns; those live in `CallListItem` / `CallRecord`, which
 * wrap it instead of mutating it, so the official schema stays traceable to
 * the spec at a glance.
 */

import type { AttentionCategory, AttentionPriority, CallSource } from './overview'

// ---- Internal vs. user-facing status --------------------------------------

/** Internal pipeline state (CLAUDE.md §5, "Persistent call history"). */
export type CallStatus =
  | 'uploaded'
  | 'validating'
  | 'transcribing'
  | 'analyzing'
  | 'completed'
  | 'human_review_required'
  | 'flagged'
  | 'failed'

/** Simplified state shown to the user (frontend display-only mapping). */
export type CallDisplayStatus = 'Processing' | 'Ready' | 'Needs Review' | 'Flagged' | 'Failed'

const PROCESSING_STATUSES: ReadonlySet<CallStatus> = new Set([
  'uploaded',
  'validating',
  'transcribing',
  'analyzing',
])

export function toDisplayStatus(status: CallStatus): CallDisplayStatus {
  if (PROCESSING_STATUSES.has(status)) return 'Processing'
  if (status === 'completed') return 'Ready'
  if (status === 'human_review_required') return 'Needs Review'
  if (status === 'flagged') return 'Flagged'
  return 'Failed'
}

// ---- Submission metadata (Analyze Call form) ------------------------------

/** Frontend form fields — sent as multipart form data to the intake endpoint. */
export interface CallSubmission {
  audioFile: File
  agentName: string
  callDate: string
  customerName?: string
  notes?: string
}

/** Backend-contract-adjacent: what was submitted for a given call record. */
export interface CallMetadata {
  agentName: string
  callDate: string
  customerName?: string
  notes?: string
  audioFileName?: string
  audioDurationSeconds?: number
}

// ---- Official analysis result — CLAUDE.md "Final output JSON schema" -----

export type CustomerSentiment = 'positive' | 'neutral' | 'negative'
export type CallOutcome = 'Sale' | 'No Sale' | 'Follow-up Needed' | 'Uncertain'
export type RiskLevel = 'Low' | 'Medium' | 'High'
export type GuardrailStatus = 'pass' | 'flagged' | 'human_review_required'

/** Backend contract — one entry in `similar_calls[]`. Never fabricated. */
export interface SimilarCall {
  call_id: string
  agent_name: string
  sale_result: string
  main_objection: string
  similarity_score: number
  reason: string
}

/**
 * Backend contract. Field names and casing match CLAUDE.md's documented
 * schema exactly (snake_case, matching the JSON the pipeline actually
 * returns) so this type can be dropped in against a real response with zero
 * mapping layer.
 */
export interface CallAnalysisResult {
  transcript: string
  call_summary: string
  /** Null on seeded historical records, where the corpus never recorded one. */
  customer_intent: string | null
  main_objection: string | null
  customer_sentiment: CustomerSentiment | null
  call_outcome: CallOutcome | null
  agent_performance_score: number | null
  lead_quality_score: number | null
  similar_calls: SimilarCall[]
  coaching_feedback: string[]
  recommended_next_action: string | null
  suggested_follow_up_email: string
  routing_category: string | null
  /** Null when never measured — seeded records have no confidence. */
  confidence: number | null
  risk_level: RiskLevel | null
  detected_signals: string[]
  limitations: string
  guardrail_status: GuardrailStatus
  /** Deterministically derived by the Router and re-derived on persistence. */
  attention?: CallAttention
  recovery_opportunity?: CallRecoveryOpportunity
}

/** Derived, never model-generated. See services/call_data_service/app/attention.py. */
export interface CallAttention {
  required: boolean
  priority: AttentionPriority
  priority_score: number
  category: AttentionCategory
  reason: string | null
}

export interface CallRecoveryOpportunity {
  detected: boolean
  confidence: number | null
  reason: string | null
  recommended_offer: string | null
  recommended_follow_up_window: string | null
}

// ---- Backend wire shapes (snake_case, exactly as call_data_service emits) --

/** `GET /calls` row. */
export interface BackendCallSummary {
  call_id: string
  source: CallSource
  created_at: string
  call_date: string | null
  agent_name: string
  customer_name: string | null
  status: string
  call_outcome: CallOutcome | null
  agent_performance_score: number | null
  lead_quality_score: number | null
  confidence: number | null
  risk_level: RiskLevel | null
  guardrail_status: GuardrailStatus
  attention_required: boolean
  attention_priority: AttentionPriority
  attention_priority_score: number
  attention_category: AttentionCategory
}

/** `GET /calls/{call_id}` full stored record. */
export interface BackendCallRecord {
  schema_version: string
  call_id: string
  source: CallSource
  created_at: string
  call_date: string | null
  agent_name: string
  agent_name_normalized: string
  customer_name: string | null
  status: string
  router_reasons: string[]
  analysis: CallAnalysisResult
}

/**
 * The n8n webhook's success envelope.
 *
 * Same shape as a stored record plus `persistence`, minus the storage-only
 * bookkeeping fields — so a just-analyzed call renders through exactly the
 * same code path as a fetched one.
 */
export interface PipelineResponse {
  call_id: string
  created_at: string
  call_date: string | null
  agent_name: string
  customer_name: string | null
  status: string
  router_reasons: string[]
  analysis: CallAnalysisResult
  persistence?: { persisted: boolean; detail: string }
}

// ---- Evidence, transcript & citations (frontend display-only aggregates) --

/** One speaker turn, derived client-side from the tagged transcript text. */
export interface TranscriptSegment {
  index: number
  speaker: 'Agent' | 'Customer' | 'Unknown'
  text: string
}

/** Splits a "Agent: ... \nCustomer: ..." transcript into speaker turns. */
export function parseTranscriptSegments(transcript: string): TranscriptSegment[] {
  const lines = transcript.split('\n').filter((line) => line.trim().length > 0)
  return lines.map((line, index) => {
    const match = line.match(/^(Agent|Customer):\s*(.*)$/)
    return {
      index,
      speaker: (match?.[1] as TranscriptSegment['speaker']) ?? 'Unknown',
      text: match?.[2] ?? line,
    }
  })
}

export interface TranscriptCitation {
  type: 'transcript'
  segmentIndex: number
  label: string
}

export interface AnalysisFieldCitation {
  type: 'analysis_field'
  field: keyof CallAnalysisResult
  label: string
}

/**
 * Not a backend contract — a frontend-only aggregation of what each
 * upstream service contributed, used to power Call Details' progressive
 * disclosure sections and Ask XSight's evidence citations.
 */
export interface CallEvidence {
  ragInsight?: string
  ragCitations: string[]
  signalDetectedSignals: string[]
  signalConfidence?: number
  langgraphReasoningSteps: string[]
  langgraphEvidenceConflicts: string[]
}

export type RouterReasonCode =
  | 'low_confidence'
  | 'evidence_conflict'
  | 'missing_citations'
  | 'guardrail_flag'
  | 'upstream_failure'

/** Why the Router (CLAUDE.md §2) sent this call to human review. */
export interface RouterReason {
  code: RouterReasonCode
  label: string
  detail: string
}

/** Same shape as RouterReason — named separately per the Ask XSight citation
 * taxonomy ("Router · Human Review Reason" is its own citation type). */
export type HumanReviewReason = RouterReason

// ---- Persistence envelope (not part of the documented JSON schema) -------

/** Row shown in the Calls list — the camelCase view of `BackendCallSummary`. */
export interface CallListItem {
  callId: string
  status: CallStatus
  agentName: string
  callDate: string
  customerName?: string
  createdAt: string
  callOutcome?: CallOutcome
  riskLevel?: RiskLevel
  confidence?: number
  guardrailStatus?: GuardrailStatus
  audioDurationSeconds?: number
  source?: CallSource
  attentionRequired?: boolean
  attentionPriority?: AttentionPriority
}

/** Full record backing Call Details — the list item plus everything else. */
export interface CallRecord extends CallListItem {
  metadata: CallMetadata
  analysis?: CallAnalysisResult
  evidence?: CallEvidence
  routerReasons?: RouterReason[]
  humanReviewReasons?: HumanReviewReason[]
  failureReason?: string
}
