/**
 * AI Usage & Cost / Quality Evaluation (RAGAS) API abstraction — mock-only
 * this phase. Shapes are deliberately aligned with `services/usage_monitoring_service`'s
 * real response models (a parallel workstream) as a coordination reference for
 * whoever wires up the real adapter later; this module does not call that
 * service or assume its base URL/auth.
 */
import type { AIUsageSummary, CallProcessingCost, RagasEvaluation, RagasSystemSummary } from '../types'
import { isMockMode, simulateLatency } from './config'
import { mockAiUsageSummary, mockCallCosts, mockRagasEvaluations, mockRagasSystemSummary } from '../data/mockAiOperations'

export async function getUsageSummary(): Promise<AIUsageSummary> {
  if (!isMockMode()) {
    throw new Error('aiOperationsApi.getUsageSummary: no backend contract exists yet — see services/usage_monitoring_service for a candidate reference API.')
  }
  await simulateLatency(400)
  return mockAiUsageSummary
}

export async function getCallCost(callId: string): Promise<CallProcessingCost | null> {
  if (!isMockMode()) {
    throw new Error('aiOperationsApi.getCallCost: no backend contract exists yet.')
  }
  await simulateLatency(300)
  return mockCallCosts[callId] ?? null
}

export async function getQualitySummary(): Promise<RagasSystemSummary> {
  if (!isMockMode()) {
    throw new Error('aiOperationsApi.getQualitySummary: no backend contract exists yet for RAGAS evaluation.')
  }
  await simulateLatency(400)
  return mockRagasSystemSummary
}

export async function getCallEvaluation(callId: string): Promise<RagasEvaluation | null> {
  if (!isMockMode()) {
    throw new Error('aiOperationsApi.getCallEvaluation: no backend contract exists yet.')
  }
  await simulateLatency(300)
  return mockRagasEvaluations[callId] ?? null
}
