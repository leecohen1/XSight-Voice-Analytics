/**
 * Calls API.
 *
 * Read paths (`listCalls`, `getCall`) go to `call_data_service`, which reads
 * the S3 application prefix. There is no mock branch and no in-memory store:
 * a real call survives a page refresh because it is genuinely persisted, not
 * because a module-level array happens to still be in memory.
 *
 * Write path (`uploadCall`) still POSTs multipart to the n8n webhook, which
 * runs the pipeline and returns the analysis envelope. n8n mints the
 * canonical `call_id` (CALL_<uuid4>) before the pipeline runs, so the id the
 * frontend routes to is the same id the backend stored — the previous
 * client-generated `XS-100N` scheme is gone.
 *
 * The backend speaks snake_case. The small `toCallRecord`/`toCallListItem`
 * adapters below rename fields onto the camelCase view types the existing
 * components already consume. That is a pure field mapping — no filtering,
 * no aggregation, no business rules.
 */
import type {
  BackendCallRecord,
  BackendCallSummary,
  CallListItem,
  CallRecord,
  CallStatus,
  CallSubmission,
  CallAnalysisResult,
  PipelineResponse,
  RouterReason,
  RouterReasonCode,
} from '../types'
import { callDataServiceUrl, n8nWebhookUrl } from './config'
import { getJson, postMultipart } from './httpClient'

interface CallListResponse {
  calls: BackendCallSummary[]
  count: number
  total_scanned: number
  skipped_malformed_records: number
  next_cursor: string | null
}

/**
 * The Router emits machine reason codes. Known ones map onto the typed
 * `RouterReasonCode` union; anything else (a future code) degrades to
 * `upstream_failure` with its raw text preserved as the detail, rather than
 * being dropped or crashing the page.
 */
const ROUTER_REASON_CODES: Record<string, RouterReasonCode> = {
  'call_signal_analyser_confidence_below_0.65': 'low_confidence',
  langgraph_evidence_conflicts_detected: 'evidence_conflict',
  missing_historical_call_citations: 'missing_citations',
  final_analysis_response_not_parseable: 'upstream_failure',
  output_guardrails_not_implemented_skipped_check: 'guardrail_flag',
}

const ROUTER_REASON_LABELS: Record<RouterReasonCode, string> = {
  low_confidence: 'Low confidence',
  evidence_conflict: 'Evidence conflict',
  missing_citations: 'Missing citations',
  guardrail_flag: 'Guardrail flag',
  upstream_failure: 'Upstream failure',
}

function toRouterReason(raw: string): RouterReason {
  const code = ROUTER_REASON_CODES[raw] ?? 'upstream_failure'
  return { code, label: ROUTER_REASON_LABELS[code], detail: raw.replace(/_/g, ' ') }
}

/** Backend statuses are a subset of the frontend's display vocabulary. */
function toCallStatus(status: string): CallStatus {
  if (status === 'flagged' || status === 'human_review_required' || status === 'completed') return status
  return 'completed'
}

export function toCallListItem(summary: BackendCallSummary): CallListItem {
  return {
    callId: summary.call_id,
    status: toCallStatus(summary.status),
    agentName: summary.agent_name,
    callDate: summary.call_date ?? summary.created_at.slice(0, 10),
    customerName: summary.customer_name ?? undefined,
    createdAt: summary.created_at,
    callOutcome: summary.call_outcome ?? undefined,
    riskLevel: summary.risk_level ?? undefined,
    confidence: summary.confidence ?? undefined,
    guardrailStatus: summary.guardrail_status,
    source: summary.source,
    attentionRequired: summary.attention_required,
    attentionPriority: summary.attention_priority,
    attentionCategory: summary.attention_category,
    agentPerformanceScore: summary.agent_performance_score ?? undefined,
    leadQualityScore: summary.lead_quality_score ?? undefined,
  }
}

export function toCallRecord(record: BackendCallRecord): CallRecord {
  const a = record.analysis
  return {
    callId: record.call_id,
    status: toCallStatus(record.status),
    agentName: record.agent_name,
    callDate: record.call_date ?? record.created_at.slice(0, 10),
    customerName: record.customer_name ?? undefined,
    createdAt: record.created_at,
    callOutcome: a.call_outcome ?? undefined,
    riskLevel: a.risk_level ?? undefined,
    confidence: a.confidence ?? undefined,
    guardrailStatus: a.guardrail_status,
    source: record.source,
    attentionRequired: a.attention?.required ?? false,
    attentionPriority: a.attention?.priority ?? 'low',
    metadata: {
      agentName: record.agent_name,
      callDate: record.call_date ?? record.created_at.slice(0, 10),
      customerName: record.customer_name ?? undefined,
    },
    analysis: a,
    // Evidence is a display-only aggregation of what each upstream service
    // contributed; it is reconstructed from the stored analysis rather than
    // stored separately.
    evidence: {
      ragCitations: (a.similar_calls ?? []).map((c) => c.call_id),
      signalDetectedSignals: a.detected_signals ?? [],
      signalConfidence: a.confidence ?? undefined,
      langgraphReasoningSteps: [],
      langgraphEvidenceConflicts: [],
    },
    routerReasons: (record.router_reasons ?? []).map(toRouterReason),
  }
}

export async function listCalls(signal?: AbortSignal): Promise<CallListItem[]> {
  const response = await getJson<CallListResponse>(`${callDataServiceUrl()}/calls?limit=200`, signal)
  return (response.calls ?? []).map(toCallListItem)
}

export async function getCall(callId: string, signal?: AbortSignal): Promise<CallRecord | null> {
  try {
    const record = await getJson<BackendCallRecord>(
      `${callDataServiceUrl()}/calls/${encodeURIComponent(callId)}`,
      signal
    )
    return toCallRecord(record)
  } catch (error) {
    // A 404 is a legitimate "no such call", not a failure to report.
    if (error && typeof error === 'object' && 'code' in error && error.code === 'CALL_NOT_FOUND') {
      return null
    }
    throw error
  }
}

// ---- Upload / analyze -------------------------------------------------------

/**
 * Submits the audio to the n8n webhook and returns the pipeline's envelope.
 *
 * The returned `call_id` is authoritative: n8n minted it and (unless
 * `persistence.persisted` is false) `call_data_service` has already stored
 * the record under it, so navigating to `/calls/<call_id>` resolves against
 * real storage.
 */
export async function uploadCall(submission: CallSubmission): Promise<PipelineResponse> {
  const webhookUrl = n8nWebhookUrl()
  if (!webhookUrl) {
    throw new Error(
      'VITE_N8N_WEBHOOK_URL is not set. Point it at the live n8n webhook in frontend/.env.'
    )
  }

  const formData = new FormData()
  formData.append('audio_file', submission.audioFile)
  formData.append('agent_name', submission.agentName)
  formData.append('call_date', submission.callDate)
  if (submission.customerName) formData.append('customer_name', submission.customerName)
  if (submission.notes) formData.append('notes', submission.notes)

  return postMultipart<PipelineResponse>(webhookUrl, formData)
}

/** Convenience for rendering a just-completed analysis before any refetch. */
export function pipelineResponseToRecord(response: PipelineResponse): CallRecord {
  return toCallRecord({
    schema_version: '1.0',
    call_id: response.call_id,
    source: 'live_analysis',
    created_at: response.created_at,
    call_date: response.call_date,
    agent_name: response.agent_name,
    agent_name_normalized: response.agent_name.trim().toLowerCase(),
    customer_name: response.customer_name,
    status: response.status,
    router_reasons: response.router_reasons ?? [],
    analysis: response.analysis as CallAnalysisResult,
  })
}
