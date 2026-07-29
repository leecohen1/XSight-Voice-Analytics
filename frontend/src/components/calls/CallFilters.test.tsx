/**
 * Regression found during manual browser verification of Calls.
 *
 * The status chips offered 'Processing' and 'Failed', which no stored call
 * can ever have: call_data_service persists only completed / flagged /
 * human_review_required, and `toCallStatus` narrows anything else onto that
 * set. Both chips returned an empty list every time, which reads as a factual
 * claim ("no failed calls") instead of an unsupported query.
 */
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CallFilters from './CallFilters'
import { toDisplayStatus, type CallStatus } from '../../types'

function renderFilters(overrides: Partial<React.ComponentProps<typeof CallFilters>> = {}) {
  const props = {
    search: '',
    onSearchChange: vi.fn(),
    statusFilter: 'All' as const,
    onStatusFilterChange: vi.fn(),
    ...overrides,
  }
  render(<CallFilters {...props} />)
  return props
}

/** The only statuses call_data_service can return (see models.py CallStatus). */
const PERSISTABLE: CallStatus[] = ['completed', 'flagged', 'human_review_required']

describe('CallFilters', () => {
  it('offers only status filters a stored call can actually match', () => {
    renderFilters()
    const reachable = new Set(PERSISTABLE.map(toDisplayStatus))
    const chips = screen
      .getAllByRole('button')
      .map((b) => b.textContent?.trim())
      .filter((t): t is string => Boolean(t))

    for (const chip of chips) {
      if (chip === 'All') continue
      expect(reachable.has(chip as ReturnType<typeof toDisplayStatus>)).toBe(true)
    }
  })

  it('does not offer the unreachable Processing and Failed chips', () => {
    renderFilters()
    expect(screen.queryByRole('button', { name: 'Processing' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Failed' })).not.toBeInTheDocument()
  })

  it('still offers every reachable status', () => {
    renderFilters()
    for (const name of ['All', 'Ready', 'Needs Review', 'Flagged']) {
      expect(screen.getByRole('button', { name })).toBeInTheDocument()
    }
  })

  it('marks the active filter with aria-pressed', () => {
    renderFilters({ statusFilter: 'Flagged' })
    expect(screen.getByRole('button', { name: 'Flagged' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'All' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('reports the chosen filter', async () => {
    const props = renderFilters()
    await userEvent.click(screen.getByRole('button', { name: 'Needs Review' }))
    expect(props.onStatusFilterChange).toHaveBeenCalledWith('Needs Review')
  })

  it('reports search input', async () => {
    const props = renderFilters()
    await userEvent.type(screen.getByLabelText(/search calls/i), 'Noa')
    expect(props.onSearchChange).toHaveBeenCalled()
  })
})
