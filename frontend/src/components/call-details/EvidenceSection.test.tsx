/**
 * Regression guard: `toCallRecord` (services/callsApi.ts) never populates
 * ragInsight, langgraphReasoningSteps or langgraphEvidenceConflicts on a
 * real record -- they are always undefined/[]. This component must not
 * render a "Reasoning" meter (which would always read zero, falsely
 * implying LangGraph contributed nothing) or empty sections built on
 * fields that can never carry data today.
 */
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import EvidenceSection from './EvidenceSection'
import type { CallEvidence } from '../../types'

function evidence(overrides: Partial<CallEvidence> = {}): CallEvidence {
  return {
    ragCitations: ['CALL_023', 'CALL_018'],
    signalDetectedSignals: ['price objection'],
    signalConfidence: 0.72,
    langgraphReasoningSteps: [],
    langgraphEvidenceConflicts: [],
    ...overrides,
  }
}

describe('EvidenceSection', () => {
  it('shows only the RAG and Signal Analysis meters, never a Reasoning meter', () => {
    render(<EvidenceSection evidence={evidence()} />)
    expect(screen.getByText('RAG')).toBeInTheDocument()
    expect(screen.getByText('Signal Analysis')).toBeInTheDocument()
    expect(screen.queryByText('Reasoning')).not.toBeInTheDocument()
  })

  it('shows detected signals when present', () => {
    render(<EvidenceSection evidence={evidence()} />)
    expect(screen.getByText(/price objection/)).toBeInTheDocument()
  })

  it('never renders a RAG Insight, Evidence Conflicts, or Reasoning Steps section', () => {
    // Even if a future backend response happened to populate these, the
    // fields real records carry today are always empty -- confirming that
    // shape produces no dead sections.
    render(<EvidenceSection evidence={evidence({ langgraphReasoningSteps: [], langgraphEvidenceConflicts: [] })} />)
    expect(screen.queryByText('RAG Service Insight')).not.toBeInTheDocument()
    expect(screen.queryByText('Evidence Conflicts')).not.toBeInTheDocument()
    expect(screen.queryByText('LangGraph Reasoning Steps')).not.toBeInTheDocument()
  })
})
