/**
 * AI Operations domain types — AI Usage & Cost, and Quality Evaluation (RAGAS).
 *
 * No official contract exists yet for these. `AIUsageSummary` /
 * `AIComponentUsage` / `CallProcessingCost` are shaped to align with the
 * parallel `services/usage_monitoring_service` workstream's real Pydantic
 * response models (UsageSummaryResponse, StageBreakdownItem,
 * ProviderBreakdownItem, CostBreakdownResponse) as a coordination reference
 * — this is a deliberate alignment for a low-friction future integration,
 * not a claim that a live contract exists or that this service is called
 * directly (see `services/aiOperationsApi.ts`). RAGAS types have no known
 * backend reference at all and are frontend-facing placeholders only.
 */

export interface TrendPoint {
  date: string
  value: number
}

/** Matches the pipeline-stage vocabulary from CLAUDE.md's component list. */
export type AIComponentName =
  | 'transcription'
  | 'gemini_extraction'
  | 'embeddings'
  | 'rag_retrieval'
  | 'rag_generation'
  | 'call_signal_analyser'
  | 'langgraph_reasoning'
  | 'gemini_final_analysis'
  | 'guardrails'
  | 'ragas_evaluation'

export interface AIComponentUsage {
  component: AIComponentName
  label: string
  costUsd: number
  totalTokens?: number
  eventsCount: number
  pricingGapCount: number
}

export interface AIUsageSummary {
  periodStart: string
  periodEnd: string
  totalCostUsd: number
  averageCostPerCallUsd: number
  totalCallsProcessed: number
  totalProcessingDurationSeconds: number
  averageProcessingDurationSeconds: number
  failedExecutions: number
  retriedExecutions: number
  callVolumeTrend: TrendPoint[]
  costTrend: TrendPoint[]
  componentBreakdown: AIComponentUsage[]
  /** Standing disclaimer surfaced with every cost figure — never omitted. */
  labels: string[]
}

export interface CallProcessingCost {
  callId: string
  totalCostUsd: number
  processingDurationSeconds: number
  failedSteps: string[]
  retriedSteps: string[]
  componentBreakdown: AIComponentUsage[]
}

// ---- Quality Evaluation (RAGAS) — frontend-facing placeholder, no backend --

export type EvaluationStatus = 'passed' | 'needs_review' | 'failed' | 'not_evaluated'

export type RagasMetricName =
  | 'faithfulness'
  | 'context_relevance'
  | 'answer_relevance'
  | 'citation_coverage'

export interface RagasMetric {
  name: RagasMetricName
  label: string
  score: number
  explanation: string
}

export interface RagasEvaluation {
  scope: 'call' | 'system'
  callId?: string
  status: EvaluationStatus
  overallScore: number
  metrics: RagasMetric[]
  evaluatedAt: string
  notes: string[]
  evaluationFailures: string[]
}

export interface RagasSystemSummary {
  periodStart: string
  periodEnd: string
  overallScore: number
  scoreTrend: TrendPoint[]
  evaluatedCalls: number
  evaluationFailures: number
  metricAverages: RagasMetric[]
  records: RagasEvaluation[]
}
