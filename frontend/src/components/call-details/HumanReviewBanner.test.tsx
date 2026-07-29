/**
 * Human review is a valid analytical outcome, not a system failure -- the
 * banner must state specific, real reasons as a scannable list rather than
 * leaving the manager to parse a paragraph. The regression this guards
 * against: `humanReviewReasons` was previously never populated by the app
 * (see CallDetails.tsx, which now passes call.routerReasons -- the field
 * that actually carries this data end to end).
 */
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import HumanReviewBanner from './HumanReviewBanner'
import type { HumanReviewReason } from '../../types'

const REASONS: HumanReviewReason[] = [
  { code: 'low_confidence', label: 'Low confidence', detail: 'confidence 0.64 is below the 0.65 threshold' },
  { code: 'evidence_conflict', label: 'Evidence conflict', detail: 'RAG and signal analysis disagreed' },
]

describe('HumanReviewBanner', () => {
  it('leads with a "Why review is required" bullet list built from real reasons', () => {
    render(<HumanReviewBanner guardrailStatus="human_review_required" limitations="Some narrative text." humanReviewReasons={REASONS} />)
    expect(screen.getByText('Why review is required')).toBeInTheDocument()
    expect(screen.getByText(/Low confidence: confidence 0.64/)).toBeInTheDocument()
    expect(screen.getByText(/Evidence conflict: RAG and signal analysis disagreed/)).toBeInTheDocument()
  })

  it('still shows the narrative limitations text as supporting detail', () => {
    render(<HumanReviewBanner guardrailStatus="human_review_required" limitations="Some narrative text." humanReviewReasons={REASONS} />)
    expect(screen.getByText('Some narrative text.')).toBeInTheDocument()
  })

  it('falls back to the narrative alone when no structured reasons exist', () => {
    render(<HumanReviewBanner guardrailStatus="flagged" limitations="Only prose here." humanReviewReasons={[]} />)
    expect(screen.queryByText('Why review is required')).not.toBeInTheDocument()
    expect(screen.getByText('Only prose here.')).toBeInTheDocument()
  })

  it('treats human review as a valid outcome, not an error banner', () => {
    render(<HumanReviewBanner guardrailStatus="human_review_required" humanReviewReasons={REASONS} />)
    expect(screen.getByText('Human Review Required')).toBeInTheDocument()
    // role=alert (urgent, needs attention) rather than being hidden/muted --
    // but the label itself must never read as a system failure.
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('shows no reasons or limitations for a passing call', () => {
    render(<HumanReviewBanner guardrailStatus="pass" />)
    expect(screen.getByText('Guardrails: Pass')).toBeInTheDocument()
    expect(screen.queryByText('Why review is required')).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
