import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Calls from './Calls'
import { makeCallSummary, stubFetch } from '../test/fixtures'

const SERVICE_URL = 'http://localhost:8006'

function renderCalls(initialEntries: string[] = ['/calls']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/calls" element={<Calls />} />
        <Route path="/calls/:callId" element={<div>call details for test</div>} />
        <Route path="/analyze" element={<div>analyze page</div>} />
      </Routes>
    </MemoryRouter>
  )
}

const CALLS = [
  makeCallSummary({
    call_id: 'CALL_a1111111-1111-1111-1111-111111111111',
    agent_name: 'Sarah Levi',
    customer_name: 'Acme Corp',
    call_outcome: 'Sale',
    agent_performance_score: 5,
    attention_required: false,
    created_at: '2026-07-28T09:00:00Z',
  }),
  makeCallSummary({
    call_id: 'CALL_b2222222-2222-2222-2222-222222222222',
    agent_name: 'Sarah Levi',
    customer_name: 'Beta LLC',
    call_outcome: 'No Sale',
    agent_performance_score: 2,
    attention_required: true,
    attention_priority: 'critical',
    created_at: '2026-07-27T09:00:00Z',
  }),
  makeCallSummary({
    call_id: 'CALL_c3333333-3333-3333-3333-333333333333',
    agent_name: 'Daniel Cohen',
    customer_name: 'Gamma Inc',
    call_outcome: 'Follow-up Needed',
    agent_performance_score: 4,
    attention_required: false,
    created_at: '2026-07-26T09:00:00Z',
  }),
]

beforeEach(() => {
  vi.stubEnv('VITE_CALL_DATA_SERVICE_URL', SERVICE_URL)
  vi.stubGlobal('fetch', stubFetch([{ match: '/calls', body: { calls: CALLS, count: 3, total_scanned: 3, skipped_malformed_records: 0, next_cursor: null } }]))
})

describe('Calls loading and error states', () => {
  it('shows a loading skeleton before the API responds', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    renderCalls()
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
  })

  it('shows an error state when the API fails', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls', status: 503, body: { error: { message: 'Storage unavailable' } } }]))
    renderCalls()
    expect(await screen.findByText(/Storage unavailable/i)).toBeInTheDocument()
  })

  it('shows an empty state when there are no calls at all', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls', body: { calls: [], count: 0, total_scanned: 0, skipped_malformed_records: 0, next_cursor: null } }]))
    renderCalls()
    expect(await screen.findByText(/No calls match your filters/i)).toBeInTheDocument()
  })
})

describe('Calls table rendering', () => {
  it('does not show the raw call UUID as a primary visible column', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    // The id must not appear as rendered text content anywhere in the row.
    expect(screen.queryByText(/CALL_a1111111-1111/)).not.toBeInTheDocument()
    // It is still present, just as a title attribute for hover/copy access.
    const link = screen.getByText('Acme Corp').closest('a')
    expect(link).toHaveAttribute('title', 'CALL_a1111111-1111-1111-1111-111111111111')
  })

  it('shows the count of matching vs. total calls', async () => {
    renderCalls()
    expect(await screen.findByText('3 of 3 calls')).toBeInTheDocument()
  })

  it('links each row to its Call Details page', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    const link = screen.getByText('Acme Corp').closest('a')
    expect(link).toHaveAttribute('href', '/calls/CALL_a1111111-1111-1111-1111-111111111111')
  })

  it('navigates to Call Details on click', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    await userEvent.click(screen.getByText('Acme Corp'))
    expect(await screen.findByText('call details for test')).toBeInTheDocument()
  })
})

describe('Calls filtering and search', () => {
  it('filters by search across agent, customer and call id', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    await userEvent.type(screen.getByLabelText(/search calls/i), 'Gamma')
    expect(await screen.findByText('1 of 3 calls')).toBeInTheDocument()
    expect(screen.getByText('Daniel Cohen')).toBeInTheDocument()
    expect(screen.queryByText('Acme Corp')).not.toBeInTheDocument()
  })

  it('filters by status', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    await userEvent.click(screen.getByRole('button', { name: 'Needs Review' }))
    expect(await screen.findByText('0 of 3 calls')).toBeInTheDocument()
  })

  it('shows an empty result with a usable message when filters match nothing', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    await userEvent.type(screen.getByLabelText(/search calls/i), 'nobody-matches-this')
    expect(await screen.findByText(/No calls match your filters/i)).toBeInTheDocument()
  })

  it('filters to a representative via the agent query param', async () => {
    renderCalls(['/calls?agent=Daniel%20Cohen'])
    expect(await screen.findByText('1 of 3 calls')).toBeInTheDocument()
    expect(screen.getByText(/Showing calls for/i)).toBeInTheDocument()
    // "Daniel Cohen" legitimately appears twice: once in the banner, once
    // in the (sole remaining) row.
    expect(screen.getAllByText('Daniel Cohen').length).toBe(2)
  })

  it('clears the representative filter', async () => {
    renderCalls(['/calls?agent=Daniel%20Cohen'])
    await screen.findByText('1 of 3 calls')
    await userEvent.click(screen.getByRole('button', { name: /clear/i }))
    expect(await screen.findByText('3 of 3 calls')).toBeInTheDocument()
  })
})

describe('Calls sorting', () => {
  it('defaults to attention-first ordering', async () => {
    const { container } = renderCalls()
    await screen.findByText('Acme Corp')
    const rows = container.querySelectorAll('a[href^="/calls/CALL_"]')
    // Beta LLC's call has attention_required: true and must lead.
    expect(within(rows[0] as HTMLElement).queryByText('Beta LLC')).toBeInTheDocument()
  })

  it('re-sorts by newest when selected', async () => {
    const { container } = renderCalls()
    await screen.findByText('Acme Corp')
    await userEvent.selectOptions(screen.getByLabelText(/sort/i), 'Newest first')
    const rows = container.querySelectorAll('a[href^="/calls/CALL_"]')
    expect(within(rows[0] as HTMLElement).queryByText('Acme Corp')).toBeInTheDocument()
  })
})

describe('Calls — By Representative view', () => {
  it('groups calls under each representative with totals', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    await userEvent.click(screen.getByRole('tab', { name: 'By Representative' }))

    expect(await screen.findByText(/across 2 representatives/i)).toBeInTheDocument()
    const sarahGroup = screen.getByText('Sarah Levi').closest('button')!
    expect(within(sarahGroup).getByText('2')).toBeInTheDocument() // calls analyzed
  })

  it('shows close rate excluding nothing but known outcomes', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    await userEvent.click(screen.getByRole('tab', { name: 'By Representative' }))
    // Sarah: 1 Sale, 1 No Sale -> 50% close rate.
    const sarahGroup = screen.getByText('Sarah Levi').closest('button')!
    expect(within(sarahGroup).getByText('50%')).toBeInTheDocument()
  })

  it('does not repeat the representative name on every call row when expanded', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    await userEvent.click(screen.getByRole('tab', { name: 'By Representative' }))
    await userEvent.click(screen.getByText('Sarah Levi').closest('button')!)

    // The name appears once as the group header; the expanded rows show
    // customer names, not a repeated agent name per row.
    expect(screen.getAllByText('Sarah Levi')).toHaveLength(1)
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Beta LLC')).toBeInTheDocument()
  })

  it('links "View all" to the representative-filtered All Calls view', async () => {
    renderCalls()
    await screen.findByText('Acme Corp')
    await userEvent.click(screen.getByRole('tab', { name: 'By Representative' }))
    const viewAll = screen.getAllByText('View all')[0]
    expect(viewAll).toHaveAttribute('href', expect.stringContaining('agent='))
  })
})
