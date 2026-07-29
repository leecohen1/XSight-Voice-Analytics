/**
 * Calls screen: sorting and representative grouping.
 *
 * `listCalls()` fetches the complete stored set (limit=200, no server-side
 * pagination in front of it yet), so sorting and grouping here operate over
 * the whole dataset -- unlike Overview's attention_calls (capped at 5),
 * there is no truncation risk to worry about for these operations today.
 * If the backend ever paginates this endpoint, sorting/grouping must move
 * server-side at that point; this module is where that migration would
 * start from.
 */
import type { CallListItem } from '../types'

export type CallSortOrder = 'attention_first' | 'newest' | 'performance_high' | 'performance_low' | 'outcome'

export const SORT_LABELS: Record<CallSortOrder, string> = {
  attention_first: 'Needs attention first',
  newest: 'Newest first',
  performance_high: 'Highest agent performance',
  performance_low: 'Lowest agent performance',
  outcome: 'Outcome',
}

const OUTCOME_ORDER: Record<string, number> = {
  'Follow-up Needed': 0,
  Uncertain: 1,
  'No Sale': 2,
  Sale: 3,
}

function byNewest(a: CallListItem, b: CallListItem): number {
  return b.createdAt.localeCompare(a.createdAt)
}

/** The default triage order: attention first, then newest within each group. */
function byAttentionFirst(a: CallListItem, b: CallListItem): number {
  const aFlag = a.attentionRequired ? 0 : 1
  const bFlag = b.attentionRequired ? 0 : 1
  if (aFlag !== bFlag) return aFlag - bFlag
  return byNewest(a, b)
}

function byPerformance(direction: 1 | -1) {
  return (a: CallListItem, b: CallListItem): number => {
    // Unscored calls sort last regardless of direction -- "no score" must
    // never look like "the worst score".
    const aScore = a.agentPerformanceScore
    const bScore = b.agentPerformanceScore
    if (aScore === undefined && bScore === undefined) return byNewest(a, b)
    if (aScore === undefined) return 1
    if (bScore === undefined) return -1
    if (aScore !== bScore) return direction * (bScore - aScore)
    return byNewest(a, b)
  }
}

function byOutcome(a: CallListItem, b: CallListItem): number {
  const aRank = a.callOutcome ? (OUTCOME_ORDER[a.callOutcome] ?? 4) : 5
  const bRank = b.callOutcome ? (OUTCOME_ORDER[b.callOutcome] ?? 4) : 5
  if (aRank !== bRank) return aRank - bRank
  return byNewest(a, b)
}

export function sortCalls(calls: CallListItem[], order: CallSortOrder): CallListItem[] {
  const sorted = [...calls]
  if (order === 'attention_first') return sorted.sort(byAttentionFirst)
  if (order === 'newest') return sorted.sort(byNewest)
  if (order === 'performance_high') return sorted.sort(byPerformance(1))
  if (order === 'performance_low') return sorted.sort(byPerformance(-1))
  return sorted.sort(byOutcome)
}

export interface RepresentativeGroup {
  agentName: string
  calls: CallListItem[]
  callsAnalyzed: number
  /** Null when nothing in the group has a known outcome. */
  closeRate: number | null
  averageAgentPerformance: number | null
  attentionCount: number
  mostRecentCallDate: string
}

function mean(values: number[]): number | null {
  if (values.length === 0) return null
  return Math.round((values.reduce((a, b) => a + b, 0) / values.length) * 10) / 10
}

/**
 * Groups the full call list by representative. Close rate excludes
 * 'Uncertain' and missing outcomes from its denominator, mirroring the
 * backend's own close_rate rule -- a group summary must not silently
 * diverge from what Overview reports for the same representative.
 */
export function groupByRepresentative(calls: CallListItem[]): RepresentativeGroup[] {
  const byAgent = new Map<string, CallListItem[]>()
  for (const call of calls) {
    const bucket = byAgent.get(call.agentName) ?? []
    bucket.push(call)
    byAgent.set(call.agentName, bucket)
  }

  return [...byAgent.entries()]
    .map(([agentName, agentCalls]): RepresentativeGroup => {
      const known = agentCalls.filter((c) => c.callOutcome && c.callOutcome !== 'Uncertain')
      const sales = known.filter((c) => c.callOutcome === 'Sale').length
      const scored = agentCalls.map((c) => c.agentPerformanceScore).filter((s): s is number => s !== undefined)
      return {
        agentName,
        calls: sortCalls(agentCalls, 'newest'),
        callsAnalyzed: agentCalls.length,
        closeRate: known.length > 0 ? Math.round((sales / known.length) * 1000) / 10 : null,
        averageAgentPerformance: mean(scored),
        attentionCount: agentCalls.filter((c) => c.attentionRequired).length,
        mostRecentCallDate: agentCalls.reduce((latest, c) => (c.createdAt > latest ? c.createdAt : latest), ''),
      }
    })
    .sort((a, b) => {
      if (b.attentionCount !== a.attentionCount) return b.attentionCount - a.attentionCount
      return b.mostRecentCallDate.localeCompare(a.mostRecentCallDate)
    })
}
