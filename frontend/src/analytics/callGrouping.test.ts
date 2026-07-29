import { describe, expect, it } from 'vitest'
import { groupByRepresentative, sortCalls } from './callGrouping'
import type { CallListItem } from '../types'

function call(overrides: Partial<CallListItem> = {}): CallListItem {
  return {
    callId: `CALL_${Math.random().toString(16).slice(2, 8)}`,
    status: 'completed',
    agentName: 'Sarah Levi',
    callDate: '2026-07-20',
    createdAt: '2026-07-20T09:00:00Z',
    guardrailStatus: 'pass',
    source: 'live_analysis',
    attentionRequired: false,
    attentionPriority: 'low',
    agentPerformanceScore: 4,
    callOutcome: 'Sale',
    ...overrides,
  }
}

describe('sortCalls — attention_first', () => {
  it('puts attention-required calls before everything else', () => {
    const calls = [
      call({ callId: 'A', attentionRequired: false, createdAt: '2026-07-25T00:00:00Z' }),
      call({ callId: 'B', attentionRequired: true, createdAt: '2026-07-20T00:00:00Z' }),
    ]
    const sorted = sortCalls(calls, 'attention_first')
    expect(sorted[0].callId).toBe('B')
  })

  it('sorts newest first within the same attention state', () => {
    const calls = [
      call({ callId: 'A', createdAt: '2026-07-20T00:00:00Z' }),
      call({ callId: 'B', createdAt: '2026-07-25T00:00:00Z' }),
    ]
    expect(sortCalls(calls, 'attention_first').map((c) => c.callId)).toEqual(['B', 'A'])
  })
})

describe('sortCalls — performance', () => {
  it('sorts highest performance first, unscored calls last', () => {
    const calls = [
      call({ callId: 'A', agentPerformanceScore: 3 }),
      call({ callId: 'B', agentPerformanceScore: undefined }),
      call({ callId: 'C', agentPerformanceScore: 5 }),
    ]
    expect(sortCalls(calls, 'performance_high').map((c) => c.callId)).toEqual(['C', 'A', 'B'])
  })

  it('sorts lowest performance first, unscored calls still last', () => {
    const calls = [
      call({ callId: 'A', agentPerformanceScore: 3 }),
      call({ callId: 'B', agentPerformanceScore: undefined }),
      call({ callId: 'C', agentPerformanceScore: 5 }),
    ]
    expect(sortCalls(calls, 'performance_low').map((c) => c.callId)).toEqual(['A', 'C', 'B'])
  })
})

describe('sortCalls — outcome', () => {
  it('surfaces open/uncertain outcomes ahead of decided ones', () => {
    const calls = [
      call({ callId: 'A', callOutcome: 'Sale' }),
      call({ callId: 'B', callOutcome: 'Follow-up Needed' }),
      call({ callId: 'C', callOutcome: 'No Sale' }),
    ]
    expect(sortCalls(calls, 'outcome').map((c) => c.callId)).toEqual(['B', 'C', 'A'])
  })
})

describe('groupByRepresentative', () => {
  it('groups calls under their agent', () => {
    const groups = groupByRepresentative([
      call({ agentName: 'Sarah Levi' }),
      call({ agentName: 'Sarah Levi' }),
      call({ agentName: 'Daniel Cohen' }),
    ])
    const sarah = groups.find((g) => g.agentName === 'Sarah Levi')
    expect(sarah?.callsAnalyzed).toBe(2)
  })

  it('excludes Uncertain from the close-rate denominator, mirroring the backend rule', () => {
    const groups = groupByRepresentative([
      call({ callOutcome: 'Sale' }),
      call({ callOutcome: 'No Sale' }),
      call({ callOutcome: 'Uncertain' }),
    ])
    expect(groups[0].closeRate).toBe(50) // 1 sale of 2 known outcomes
  })

  it('reports null close rate when nothing has a known outcome', () => {
    const groups = groupByRepresentative([call({ callOutcome: undefined })])
    expect(groups[0].closeRate).toBeNull()
  })

  it('averages only the scored calls', () => {
    const groups = groupByRepresentative([
      call({ agentPerformanceScore: 4 }),
      call({ agentPerformanceScore: undefined }),
      call({ agentPerformanceScore: 2 }),
    ])
    expect(groups[0].averageAgentPerformance).toBe(3)
  })

  it('sorts groups by attention count, then by most recent activity', () => {
    const groups = groupByRepresentative([
      call({ agentName: 'Quiet Rep', attentionRequired: false, createdAt: '2026-07-28T00:00:00Z' }),
      call({ agentName: 'Busy Rep', attentionRequired: true, createdAt: '2026-07-01T00:00:00Z' }),
    ])
    expect(groups[0].agentName).toBe('Busy Rep')
  })

  it('counts attention calls per representative', () => {
    const groups = groupByRepresentative([
      call({ agentName: 'A', attentionRequired: true }),
      call({ agentName: 'A', attentionRequired: false }),
    ])
    expect(groups[0].attentionCount).toBe(1)
  })
})
