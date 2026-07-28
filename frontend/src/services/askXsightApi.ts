/**
 * Ask XSight API abstraction — mock-only this phase (CLAUDE.md §9.7: "if the
 * backend contract is not yet finalized, define the frontend boundary,
 * create an isolated mock adapter, document the missing backend contract").
 *
 * The mock logic deliberately mirrors the real grounding rule it will need
 * to enforce later: every answer is built from the selected call's actual
 * stored fields (never free-floating invented text), and anything the
 * keyword matcher can't ground in that call's evidence falls through to
 * "not enough evidence" rather than a guessed answer.
 */
import type {
  AskXsightAnswer,
  AskXsightCitation,
  AskXsightMessage,
  AskXsightQuestion,
  AskXsightRequest,
  AskXsightResponse,
  CallRecord,
} from '../types'
import { isMockMode, simulateLatency } from './config'
import { getMockCall } from '../data/mockCallStore'
import { mockRagasEvaluations } from '../data/mockAiOperations'
import { suggestedQuestionBank } from '../data/mockAskXsight'

const conversations = new Map<string, AskXsightMessage[]>()

function requireMock(fn: string): void {
  if (!isMockMode()) {
    throw new Error(`askXsightApi.${fn}: no backend AI-reasoning contract exists yet — Ask XSight is mock-backed this phase.`)
  }
}

export async function getSuggestedQuestions(callId: string): Promise<AskXsightQuestion[]> {
  requireMock('getSuggestedQuestions')
  await simulateLatency(200)

  const call = getMockCall(callId)
  if (!call?.analysis) return []
  const { analysis } = call
  const ragas = mockRagasEvaluations[callId]

  return suggestedQuestionBank.filter((q) => {
    switch (q.id) {
      case 'q-risk':
        return analysis.risk_level !== 'Low'
      case 'q-objection-evidence':
        return analysis.main_objection !== 'none'
      case 'q-human-review':
        return call.status === 'human_review_required'
      case 'q-compare-similar':
        return analysis.similar_calls.length > 0
      case 'q-coaching':
        return analysis.coaching_feedback.length > 0
      case 'q-agent-score':
        return true
      case 'q-limitations':
        return Boolean(analysis.limitations) && !analysis.limitations.toLowerCase().startsWith('none')
      case 'q-ragas-drop':
        return Boolean(ragas && ragas.metrics.some((m) => m.name === 'faithfulness' && m.score < 0.6))
      case 'q-unrelated-crm':
        return true
      default:
        return false
    }
  })
}

export async function getConversationHistory(callId: string): Promise<AskXsightMessage[]> {
  requireMock('getConversationHistory')
  await simulateLatency(150)
  return [...(conversations.get(callId) ?? [])]
}

function appendMessage(callId: string, message: AskXsightMessage): void {
  const history = conversations.get(callId) ?? []
  conversations.set(callId, [...history, message])
}

const WRITE_BACK_PATTERN = /\b(change|update|overwrite|modify|set|cancel)\b.{0,40}\b(outcome|score|classification|status|analysis|risk level|guardrail|human review)\b/i
const ERROR_SIMULATION_PATTERN = /simulate.?(a\s+)?error/i

function buildAnswer(call: CallRecord, question: string): AskXsightAnswer {
  const analysis = call.analysis!
  const ragas = mockRagasEvaluations[call.callId]
  const q = question.toLowerCase()

  const cite = (citations: AskXsightCitation[], text: string): AskXsightAnswer => ({ text, citations, notEnoughEvidence: false })

  if (/\brisk\b/.test(q)) {
    return cite(
      [
        { type: 'signal_analysis', label: 'Signal Analysis · Risk Level', detail: analysis.risk_level ?? undefined, refId: call.callId },
        { type: 'analysis_field', label: 'Analysis · Detected Signals', detail: analysis.detected_signals.join(', '), refId: 'detected_signals' },
      ],
      // Seeded historical calls have no measured risk or confidence; the
      // answer says so rather than printing "null risk" or "NaN%".
      `This call is scored ${analysis.risk_level ?? 'no recorded'} risk${
        analysis.confidence !== null && analysis.confidence !== undefined
          ? ` (confidence ${Math.round(analysis.confidence * 100)}%)`
          : ' (no confidence was recorded for this call)'
      }. The signals behind that score are: ${analysis.detected_signals.join('; ')}.`
    )
  }

  if (/objection/.test(q)) {
    const citations: AskXsightCitation[] = [{ type: 'analysis_field', label: 'Analysis · Main Objection', detail: analysis.main_objection ?? undefined, refId: 'main_objection' }]
    analysis.similar_calls.forEach((sc) => citations.push({ type: 'similar_call', label: `${sc.call_id} · Similar Historical Call`, detail: sc.reason, refId: sc.call_id }))
    return cite(
      citations,
      `The main objection identified was "${analysis.main_objection}". ${
        analysis.similar_calls.length > 0
          ? `This is grounded against ${analysis.similar_calls.length} similar historical call(s): ${analysis.similar_calls.map((c) => c.call_id).join(', ')}.`
          : 'No similar historical calls cleared the similarity threshold for this transcript, so this reading is based on the transcript alone.'
      }`
    )
  }

  if (/human review|review required/.test(q)) {
    if (call.status !== 'human_review_required' || !call.humanReviewReasons?.length) {
      return { text: 'This call was not routed to human review — it passed the Router\'s confidence, evidence-conflict, and citation checks.', citations: [], notEnoughEvidence: false }
    }
    return cite(
      call.humanReviewReasons.map((r) => ({ type: 'human_review_reason' as const, label: 'Router · Human Review Reason', detail: r.detail, refId: r.code })),
      `Human review was required because: ${call.humanReviewReasons.map((r) => r.detail).join(' ')}`
    )
  }

  if (/compare|similar/.test(q)) {
    if (analysis.similar_calls.length === 0) {
      return { text: 'No similar historical calls were retrieved for this transcript, so there is nothing to compare it against.', citations: [], notEnoughEvidence: true }
    }
    const best = [...analysis.similar_calls].sort((a, b) => b.similarity_score - a.similarity_score)[0]
    return cite(
      [{ type: 'similar_call', label: `${best.call_id} · Similar Historical Call`, detail: best.reason, refId: best.call_id }],
      `The closest match is ${best.call_id} (${Math.round(best.similarity_score * 100)}% similarity, outcome: ${best.sale_result}). ${best.reason}`
    )
  }

  if (/coaching/.test(q)) {
    if (analysis.coaching_feedback.length === 0) {
      return { text: 'No coaching feedback was generated for this call.', citations: [], notEnoughEvidence: true }
    }
    return cite(
      [{ type: 'analysis_field', label: 'Analysis · Coaching Feedback', detail: analysis.coaching_feedback[0], refId: 'coaching_feedback' }],
      analysis.coaching_feedback.join(' ')
    )
  }

  if (/agent score|performance score|agent perform/.test(q)) {
    return cite(
      [
        { type: 'analysis_field', label: 'Analysis · Agent Performance', detail: String(analysis.agent_performance_score), refId: 'agent_performance_score' },
        { type: 'transcript', label: 'Transcript · Full Call', refId: '0' },
      ],
      `Agent performance was scored ${analysis.agent_performance_score}/5. Coaching feedback explains the specific transcript moments behind that score: ${analysis.coaching_feedback[0] ?? 'see the Coaching Feedback section.'}`
    )
  }

  if (/limitation/.test(q)) {
    return cite(
      [{ type: 'limitation', label: 'Analysis · Limitations', detail: analysis.limitations, refId: 'limitations' }],
      analysis.limitations
    )
  }

  if (/ragas|faithfulness|quality (score|evaluation)/.test(q)) {
    if (!ragas || ragas.status === 'not_evaluated') {
      return { text: 'This call has not been evaluated by RAGAS yet.', citations: [], notEnoughEvidence: true }
    }
    const faithfulness = ragas.metrics.find((m) => m.name === 'faithfulness')
    return cite(
      [{ type: 'ragas_evaluation', label: 'Quality Evaluation · Faithfulness Note', detail: faithfulness?.explanation, refId: call.callId }],
      faithfulness
        ? `Faithfulness is ${faithfulness.score.toFixed(2)}. ${faithfulness.explanation}`
        : `Overall quality evaluation score is ${ragas.overallScore.toFixed(2)} (${ragas.status}).`
    )
  }

  return { text: '', citations: [], notEnoughEvidence: true }
}

export async function askCallQuestion(request: AskXsightRequest): Promise<AskXsightResponse> {
  requireMock('askCallQuestion')
  await simulateLatency(700)

  const question = request.question.trim()
  const now = new Date().toISOString()

  appendMessage(request.callId, { id: `msg-${Date.now()}-u`, role: 'user', text: question, createdAt: now })

  if (!question) {
    return { answer: null, error: { code: 'unsupported_request', message: 'Please enter a question to ask XSight.' } }
  }

  if (ERROR_SIMULATION_PATTERN.test(question)) {
    return { answer: null, error: { code: 'backend_error', message: 'XSight could not complete this request right now. Please try again in a moment.' } }
  }

  if (WRITE_BACK_PATTERN.test(question)) {
    return {
      answer: null,
      error: {
        code: 'unsupported_request',
        message: 'Ask XSight can explain the official analysis, but it cannot change classifications, scores, or the guardrail/router decision. Those come only from the validated pipeline.',
      },
    }
  }

  const call = getMockCall(request.callId)
  if (!call?.analysis) {
    return {
      answer: {
        text: '',
        citations: [],
        notEnoughEvidence: true,
      },
    }
  }

  const answer = buildAnswer(call, question)
  if (!answer.notEnoughEvidence) {
    appendMessage(request.callId, { id: `msg-${Date.now()}-a`, role: 'assistant', text: answer.text, citations: answer.citations, createdAt: new Date().toISOString() })
  } else {
    appendMessage(request.callId, { id: `msg-${Date.now()}-a`, role: 'assistant', text: answer.text, notEnoughEvidence: true, createdAt: new Date().toISOString() })
  }

  return { answer }
}
