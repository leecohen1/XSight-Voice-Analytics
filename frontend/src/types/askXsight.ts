/**
 * Ask XSight domain types (CLAUDE.md §9). Mock-backed this phase — no
 * backend AI reasoning is implemented; see services/askXsightApi.ts for the
 * documented missing-contract boundary.
 */

export type AskXsightCitationType =
  | 'transcript'
  | 'analysis_field'
  | 'similar_call'
  | 'rag_evidence'
  | 'signal_analysis'
  | 'langgraph_reasoning'
  | 'router_reason'
  | 'human_review_reason'
  | 'limitation'
  | 'ragas_evaluation'

/** A single evidence pointer rendered as a citation chip in the chat. */
export interface AskXsightCitation {
  type: AskXsightCitationType
  label: string
  detail?: string
  /** Opaque reference the citation resolves to (call_id, field key, segment index, ...). */
  refId?: string
}

export type AskXsightRole = 'user' | 'assistant'

export interface AskXsightMessage {
  id: string
  role: AskXsightRole
  text: string
  citations?: AskXsightCitation[]
  notEnoughEvidence?: boolean
  createdAt: string
}

export interface AskXsightQuestion {
  id: string
  text: string
}

export interface AskXsightAnswer {
  text: string
  citations: AskXsightCitation[]
  notEnoughEvidence: boolean
}

export type AskXsightErrorCode = 'backend_error' | 'unsupported_request' | 'network_error'

export interface AskXsightError {
  code: AskXsightErrorCode
  message: string
}

/**
 * Panel/interaction state — drives which of the polished UI states (closed,
 * open, empty, suggested-questions, loading, answered, not-enough-evidence,
 * error) renders at any given moment.
 */
export type AskXsightState =
  | 'closed'
  | 'open'
  | 'loading'
  | 'answered'
  | 'not_enough_evidence'
  | 'error'

export interface AskXsightRequest {
  callId: string
  question: string
  conversationId?: string
}

export interface AskXsightResponse {
  answer: AskXsightAnswer | null
  error?: AskXsightError
}
