/**
 * Business Outcome must be the single most visually prominent fact on this
 * panel; the internal routing category must not compete with it. This
 * guards the redesign's specific rule: Outcome gets its own labelled hero
 * line, Routing is demoted to a small "Category:" metadata line with a
 * humanized (not raw snake_case) label.
 */
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import OfficialAnalysisPanel from './OfficialAnalysisPanel'
import type { CallAnalysisResult } from '../../types'

function analysis(overrides: Partial<CallAnalysisResult> = {}): CallAnalysisResult {
  return {
    transcript: 'Agent: Hi.\nCustomer: Hi.',
    call_summary: 'A summary.',
    customer_intent: 'high',
    main_objection: 'price',
    customer_sentiment: 'positive',
    call_outcome: 'Sale',
    agent_performance_score: 4,
    lead_quality_score: 5,
    similar_calls: [],
    coaching_feedback: [],
    recommended_next_action: 'Send the proposal.',
    suggested_follow_up_email: '',
    routing_category: 'pricing_negotiation_and_followup',
    confidence: 0.8,
    risk_level: 'Low',
    detected_signals: [],
    limitations: '',
    guardrail_status: 'pass',
    ...overrides,
  }
}

function renderPanel(props: Partial<Parameters<typeof OfficialAnalysisPanel>[0]> = {}) {
  return render(
    <MemoryRouter>
      <OfficialAnalysisPanel analysis={analysis()} guardrailStatus="pass" {...props} />
    </MemoryRouter>
  )
}

describe('OfficialAnalysisPanel — outcome prominence', () => {
  it('shows Business Outcome as its own labelled hero line', () => {
    renderPanel()
    expect(screen.getByText('Business Outcome')).toBeInTheDocument()
    expect(screen.getByText('Sale')).toBeInTheDocument()
  })

  it('humanizes the routing category instead of showing the raw snake_case value', () => {
    renderPanel()
    expect(screen.getByText(/Category: Pricing negotiation and followup/)).toBeInTheDocument()
    expect(screen.queryByText(/pricing_negotiation_and_followup/)).not.toBeInTheDocument()
  })

  it('does not render a routing badge inside the main badge row', () => {
    renderPanel()
    expect(screen.queryByText(/^Routing:/)).not.toBeInTheDocument()
  })

  it('omits the routing line entirely when no category is recorded', () => {
    renderPanel({ analysis: analysis({ routing_category: null }) })
    expect(screen.queryByText(/Category:/)).not.toBeInTheDocument()
  })

  it('shows "Not recorded" rather than a fabricated outcome when null', () => {
    renderPanel({ analysis: analysis({ call_outcome: null }) })
    expect(screen.getByText('Not recorded')).toBeInTheDocument()
  })
})
