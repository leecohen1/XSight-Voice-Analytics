/**
 * Regressions found during manual browser verification of Call Details.
 *
 * 1. Cited call ids rendered as inert text, so the evidence trail dead-ended
 *    on the one screen whose whole job is letting a manager check the
 *    evidence.
 * 2. A null similarity_score rendered "NaN% similar", which reads as a real
 *    measurement rather than a missing one.
 */
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import SimilarCallsList from './SimilarCallsList'
import type { SimilarCall } from '../../types'

function similar(overrides: Partial<SimilarCall> = {}): SimilarCall {
  return {
    call_id: 'CALL_023',
    agent_name: 'Noa Friedman',
    sale_result: 'Follow-up Needed',
    main_objection: 'price',
    similarity_score: 0.798,
    reason: "Historical call CALL_023 with a 'price' objection.",
    ...overrides,
  }
}

function renderList(calls: SimilarCall[]) {
  return render(
    <MemoryRouter>
      <SimilarCallsList calls={calls} />
    </MemoryRouter>
  )
}

describe('SimilarCallsList', () => {
  it('links each cited call id to its Call Details page', () => {
    renderList([similar()])
    const link = screen.getByRole('link', { name: /CALL_023/ })
    expect(link).toHaveAttribute('href', '/calls/CALL_023')
  })

  it('links every citation when several are returned', () => {
    renderList([similar(), similar({ call_id: 'CALL_018' }), similar({ call_id: 'CALL_015' })])
    expect(screen.getByRole('link', { name: /CALL_023/ })).toHaveAttribute('href', '/calls/CALL_023')
    expect(screen.getByRole('link', { name: /CALL_018/ })).toHaveAttribute('href', '/calls/CALL_018')
    expect(screen.getByRole('link', { name: /CALL_015/ })).toHaveAttribute('href', '/calls/CALL_015')
  })

  it('renders a real similarity score as a percentage', () => {
    renderList([similar({ similarity_score: 0.798 })])
    expect(screen.getByText('80% similar')).toBeInTheDocument()
  })

  it('omits the similarity figure entirely when the score is missing', () => {
    renderList([similar({ similarity_score: null as unknown as number })])
    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument()
    expect(screen.queryByText(/% similar/)).not.toBeInTheDocument()
    // The citation itself must still be there — a missing score is not a
    // reason to drop the evidence.
    expect(screen.getByRole('link', { name: /CALL_023/ })).toBeInTheDocument()
  })

  it('omits the similarity figure when the score is undefined', () => {
    renderList([similar({ similarity_score: undefined as unknown as number })])
    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument()
    expect(screen.queryByText(/% similar/)).not.toBeInTheDocument()
  })

  it('reports insufficient evidence rather than an empty panel', () => {
    renderList([])
    expect(screen.getByText(/not enough evidence/i)).toBeInTheDocument()
  })
})
