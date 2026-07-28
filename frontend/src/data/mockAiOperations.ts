import type {
  AIComponentUsage,
  AIUsageSummary,
  CallProcessingCost,
  RagasEvaluation,
  RagasSystemSummary,
} from '../types'

const COST_LABELS = [
  'All cost figures are estimates derived from measured usage and configured provider pricing — not an actual provider invoice.',
  'Variable cost reflects measured token / audio-duration / request usage only.',
  'Figures update as new calls are processed; totals for the current period may still be partial.',
]

const SYSTEM_COMPONENT_BREAKDOWN: AIComponentUsage[] = [
  { component: 'transcription', label: 'Transcription (AssemblyAI)', costUsd: 3.85, eventsCount: 11, pricingGapCount: 0 },
  { component: 'gemini_extraction', label: 'Gemini Information Extractor', costUsd: 1.92, totalTokens: 184000, eventsCount: 11, pricingGapCount: 0 },
  { component: 'embeddings', label: 'Embeddings (Bedrock Titan)', costUsd: 0.41, totalTokens: 96000, eventsCount: 11, pricingGapCount: 0 },
  { component: 'rag_retrieval', label: 'RAG Retrieval', costUsd: 0.18, eventsCount: 11, pricingGapCount: 0 },
  { component: 'rag_generation', label: 'RAG Generation (not used — deterministic template, no LLM call)', costUsd: 0, eventsCount: 0, pricingGapCount: 0 },
  { component: 'call_signal_analyser', label: 'Call Signal Analyser', costUsd: 0.62, eventsCount: 11, pricingGapCount: 0 },
  { component: 'langgraph_reasoning', label: 'LangGraph Reasoning', costUsd: 2.14, totalTokens: 210000, eventsCount: 11, pricingGapCount: 1 },
  { component: 'gemini_final_analysis', label: 'Gemini Final Analysis Chain', costUsd: 3.47, totalTokens: 268000, eventsCount: 11, pricingGapCount: 0 },
  { component: 'guardrails', label: 'Guardrails (input + output)', costUsd: 0.29, eventsCount: 22, pricingGapCount: 0 },
  { component: 'ragas_evaluation', label: 'RAGAS Quality Evaluation', costUsd: 1.04, totalTokens: 88000, eventsCount: 9, pricingGapCount: 2 },
]

export const mockAiUsageSummary: AIUsageSummary = {
  periodStart: '2026-06-27',
  periodEnd: '2026-07-27',
  totalCostUsd: 13.92,
  averageCostPerCallUsd: 1.55,
  totalCallsProcessed: 11,
  totalProcessingDurationSeconds: 5315,
  averageProcessingDurationSeconds: 664,
  failedExecutions: 1,
  retriedExecutions: 2,
  callVolumeTrend: [
    { date: '2026-06-27', value: 1 },
    { date: '2026-07-03', value: 1 },
    { date: '2026-07-10', value: 2 },
    { date: '2026-07-17', value: 3 },
    { date: '2026-07-24', value: 4 },
  ],
  costTrend: [
    { date: '2026-06-27', value: 1.42 },
    { date: '2026-07-03', value: 1.38 },
    { date: '2026-07-10', value: 2.61 },
    { date: '2026-07-17', value: 3.74 },
    { date: '2026-07-24', value: 4.77 },
  ],
  componentBreakdown: SYSTEM_COMPONENT_BREAKDOWN,
  labels: COST_LABELS,
}

function scaledBreakdown(scale: number, pricingGap = false): AIComponentUsage[] {
  return SYSTEM_COMPONENT_BREAKDOWN.filter((c) => c.costUsd > 0).map((c) => ({
    ...c,
    costUsd: Math.round(c.costUsd * scale * 100) / 100,
    totalTokens: c.totalTokens ? Math.round(c.totalTokens * scale) : undefined,
    eventsCount: 1,
    pricingGapCount: pricingGap && c.component === 'langgraph_reasoning' ? 1 : 0,
  }))
}

export const mockCallCosts: Record<string, CallProcessingCost> = {
  'XS-1001': { callId: 'XS-1001', totalCostUsd: 1.32, processingDurationSeconds: 612, failedSteps: [], retriedSteps: [], componentBreakdown: scaledBreakdown(0.095) },
  'XS-1002': { callId: 'XS-1002', totalCostUsd: 1.08, processingDurationSeconds: 498, failedSteps: [], retriedSteps: [], componentBreakdown: scaledBreakdown(0.078) },
  'XS-1003': { callId: 'XS-1003', totalCostUsd: 1.61, processingDurationSeconds: 731, failedSteps: [], retriedSteps: ['langgraph_reasoning'], componentBreakdown: scaledBreakdown(0.116, true) },
  'XS-1004': { callId: 'XS-1004', totalCostUsd: 1.19, processingDurationSeconds: 540, failedSteps: [], retriedSteps: [], componentBreakdown: scaledBreakdown(0.086) },
  'XS-1005': { callId: 'XS-1005', totalCostUsd: 3.24, processingDurationSeconds: 1487, failedSteps: [], retriedSteps: [], componentBreakdown: scaledBreakdown(0.234) },
  'XS-1006': { callId: 'XS-1006', totalCostUsd: 1.02, processingDurationSeconds: 455, failedSteps: [], retriedSteps: [], componentBreakdown: scaledBreakdown(0.074) },
  'XS-1007': { callId: 'XS-1007', totalCostUsd: 0.31, processingDurationSeconds: 42, failedSteps: ['transcription'], retriedSteps: ['transcription', 'transcription'], componentBreakdown: [{ component: 'transcription', label: 'Transcription (AssemblyAI)', costUsd: 0.31, eventsCount: 3, pricingGapCount: 0 }] },
  'XS-1008': { callId: 'XS-1008', totalCostUsd: 0.58, processingDurationSeconds: 210, failedSteps: [], retriedSteps: [], componentBreakdown: [{ component: 'transcription', label: 'Transcription (AssemblyAI)', costUsd: 0.35, eventsCount: 1, pricingGapCount: 0 }, { component: 'gemini_extraction', label: 'Gemini Information Extractor', costUsd: 0.18, totalTokens: 17000, eventsCount: 1, pricingGapCount: 0 }, { component: 'guardrails', label: 'Guardrails (input + output)', costUsd: 0.05, eventsCount: 2, pricingGapCount: 0 }] },
  'XS-1009': { callId: 'XS-1009', totalCostUsd: 0.03, processingDurationSeconds: 4, failedSteps: [], retriedSteps: [], componentBreakdown: [{ component: 'guardrails', label: 'Guardrails (input + output)', costUsd: 0.03, eventsCount: 1, pricingGapCount: 0 }] },
  'XS-1010': { callId: 'XS-1010', totalCostUsd: 0.84, processingDurationSeconds: 389, failedSteps: [], retriedSteps: [], componentBreakdown: scaledBreakdown(0.061) },
  'XS-1011': { callId: 'XS-1011', totalCostUsd: 1.31, processingDurationSeconds: 603, failedSteps: [], retriedSteps: [], componentBreakdown: scaledBreakdown(0.095) },
}

const METRIC_LABELS: Record<RagasEvaluation['metrics'][number]['name'], string> = {
  faithfulness: 'Faithfulness',
  context_relevance: 'Context Relevance',
  answer_relevance: 'Answer Relevance',
  citation_coverage: 'Citation Coverage',
}

function metrics(f: number, cr: number, ar: number, cc: number, explain: Partial<Record<string, string>> = {}): RagasEvaluation['metrics'] {
  const defaults: Record<string, string> = {
    faithfulness: 'How well the generated analysis sticks to what the transcript and cited evidence actually support.',
    context_relevance: 'How relevant the retrieved historical calls and evidence were to this specific transcript.',
    answer_relevance: 'How directly the coaching feedback and recommended action address this call\'s actual situation.',
    citation_coverage: 'The share of evidence-based claims that carry a traceable call_id or evidence citation.',
  }
  return [
    { name: 'faithfulness', label: METRIC_LABELS.faithfulness, score: f, explanation: explain.faithfulness ?? defaults.faithfulness },
    { name: 'context_relevance', label: METRIC_LABELS.context_relevance, score: cr, explanation: explain.context_relevance ?? defaults.context_relevance },
    { name: 'answer_relevance', label: METRIC_LABELS.answer_relevance, score: ar, explanation: explain.answer_relevance ?? defaults.answer_relevance },
    { name: 'citation_coverage', label: METRIC_LABELS.citation_coverage, score: cc, explanation: explain.citation_coverage ?? defaults.citation_coverage },
  ]
}

export const mockRagasEvaluations: Record<string, RagasEvaluation> = {
  'XS-1001': { scope: 'call', callId: 'XS-1001', status: 'passed', overallScore: 0.91, metrics: metrics(0.94, 0.9, 0.92, 0.88), evaluatedAt: '2026-07-24T14:09:00Z', notes: [], evaluationFailures: [] },
  'XS-1002': { scope: 'call', callId: 'XS-1002', status: 'passed', overallScore: 0.89, metrics: metrics(0.92, 0.87, 0.88, 0.9), evaluatedAt: '2026-07-22T10:44:00Z', notes: [], evaluationFailures: [] },
  'XS-1003': { scope: 'call', callId: 'XS-1003', status: 'needs_review', overallScore: 0.71, metrics: metrics(0.78, 0.6, 0.75, 0.72, { context_relevance: 'Retrieved historical evidence (CALL_003) only partially matches this call\'s deal-size/authority pattern, consistent with the evidence conflict LangGraph flagged.' }), evaluatedAt: '2026-07-21T16:26:00Z', notes: ['Lower context relevance correlates with the evidence conflict already surfaced by LangGraph — treat both signals together, not independently.'], evaluationFailures: [] },
  'XS-1004': { scope: 'call', callId: 'XS-1004', status: 'needs_review', overallScore: 0.68, metrics: metrics(0.75, 0.7, 0.68, 0.72), evaluatedAt: '2026-07-20T09:20:00Z', notes: ['Consistent with this call\'s own low Call Signal Analyser confidence (0.58) and human-review routing.'], evaluationFailures: [] },
  'XS-1005': { scope: 'call', callId: 'XS-1005', status: 'passed', overallScore: 0.95, metrics: metrics(0.97, 0.94, 0.95, 0.93), evaluatedAt: '2026-07-18T13:26:00Z', notes: [], evaluationFailures: [] },
  'XS-1006': { scope: 'call', callId: 'XS-1006', status: 'needs_review', overallScore: 0.74, metrics: metrics(0.8, 0.72, 0.74, 0.7), evaluatedAt: '2026-07-17T11:34:00Z', notes: ['Aligned with this call\'s own output-guardrail flag on the pricing-hold commitment language.'], evaluationFailures: [] },
  'XS-1007': { scope: 'call', callId: 'XS-1007', status: 'not_evaluated', overallScore: 0, metrics: [], evaluatedAt: '2026-07-16T15:51:00Z', notes: [], evaluationFailures: ['No final analysis was produced — transcription failed before any output existed to evaluate.'] },
  'XS-1008': { scope: 'call', callId: 'XS-1008', status: 'not_evaluated', overallScore: 0, metrics: [], evaluatedAt: '2026-07-27T08:12:00Z', notes: [], evaluationFailures: ['Analysis is still in progress — evaluation runs only after the final output is produced.'] },
  'XS-1009': { scope: 'call', callId: 'XS-1009', status: 'not_evaluated', overallScore: 0, metrics: [], evaluatedAt: '2026-07-27T09:02:00Z', notes: [], evaluationFailures: ['Analysis has not started yet.'] },
  'XS-1010': { scope: 'call', callId: 'XS-1010', status: 'passed', overallScore: 0.93, metrics: metrics(0.95, 0.91, 0.93, 0.92), evaluatedAt: '2026-07-14T12:06:00Z', notes: [], evaluationFailures: [] },
  'XS-1011': {
    scope: 'call',
    callId: 'XS-1011',
    status: 'needs_review',
    overallScore: 0.55,
    metrics: metrics(0.41, 0.62, 0.7, 0.5, {
      faithfulness: 'Weak — the transcript is unusually short on specifics, so several phrases in the call summary ("successful trial period") lean on interpretation rather than a directly quotable statement in the transcript.',
    }),
    evaluatedAt: '2026-07-12T17:31:00Z',
    notes: ["Faithfulness dropped specifically because the source transcript itself was thin — this is a transcript-detail limitation, not a sign the pipeline invented facts. See this call's own `limitations` field."],
    evaluationFailures: [],
  },
}

export const mockRagasSystemSummary: RagasSystemSummary = {
  periodStart: '2026-06-27',
  periodEnd: '2026-07-27',
  overallScore: 0.82,
  scoreTrend: [
    { date: '2026-06-27', value: 0.85 },
    { date: '2026-07-03', value: 0.83 },
    { date: '2026-07-10', value: 0.79 },
    { date: '2026-07-17', value: 0.8 },
    { date: '2026-07-24', value: 0.82 },
  ],
  evaluatedCalls: 9,
  evaluationFailures: 2,
  metricAverages: metrics(0.82, 0.78, 0.82, 0.8),
  records: Object.values(mockRagasEvaluations),
}
