import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Overview from './Overview'
import { makeEmptyOverview, makeOverview, stubFetch } from '../test/fixtures'

const SERVICE_URL = 'http://localhost:8006'

function renderOverview() {
  return render(
    <MemoryRouter initialEntries={['/overview']}>
      <Routes>
        <Route path="/overview" element={<Overview />} />
        <Route path="/calls/:callId" element={<div>call details for test</div>} />
        <Route path="/analyze" element={<div>analyze page</div>} />
      </Routes>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.stubEnv('VITE_CALL_DATA_SERVICE_URL', SERVICE_URL)
})

describe('Overview data states', () => {
  it('shows a loading state before the API responds', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    renderOverview()
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
  })

  it('shows an error state and a retry control when the API fails', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch([{ match: '/overview', status: 503, body: { error: { code: 'STORAGE_UNAVAILABLE', message: 'Object storage did not respond successfully.' } } }])
    )
    renderOverview()
    expect(await screen.findByText(/Object storage did not respond/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('retries the request when Retry is clicked', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: { message: 'boom' } }), { status: 503 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(makeOverview()), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    renderOverview()
    await screen.findByRole('button', { name: /retry/i })
    await userEvent.click(screen.getByRole('button', { name: /retry/i }))

    expect(await screen.findByText(/12 calls analyzed/i)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('shows an empty state when the period has no calls', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeEmptyOverview() }]))
    renderOverview()
    expect(await screen.findByText(/No calls in this period/i)).toBeInTheDocument()
  })

  it('never falls back to mock data when the backend is unavailable', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', status: 503, body: { error: { message: 'down' } } }]))
    renderOverview()
    await screen.findByText(/down/i)
    // The retired demo fixtures must not appear anywhere on a failed load.
    expect(screen.queryByText(/Fielding & Yates/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/XS-100/i)).not.toBeInTheDocument()
  })

  it('fails clearly when the service URL is not configured', async () => {
    vi.stubEnv('VITE_CALL_DATA_SERVICE_URL', '')
    renderOverview()
    expect(await screen.findByText(/VITE_CALL_DATA_SERVICE_URL is not set/i)).toBeInTheDocument()
  })
})

describe('Overview rendering', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
  })

  it('renders the 7d view with the backend executive summary', async () => {
    renderOverview()
    expect(await screen.findByText(/12 calls analyzed in the last 7 days/i)).toBeInTheDocument()
  })

  it('renders KPI values exactly as the API returned them', async () => {
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)

    // calls_analyzed = 12, close_rate = 41.7%, avg agent perf = 4.1
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('41.7%')).toBeInTheDocument()
    expect(screen.getByText('4.1')).toBeInTheDocument()
    expect(screen.getByText('3.6')).toBeInTheDocument()
  })

  it('renders the previous-period comparison from the API, not a local calculation', async () => {
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)
    // calls_analyzed: 12 vs 8 -> the backend's own +4 / +50%.
    expect(screen.getByText('+4 (+50%) vs. previous period')).toBeInTheDocument()
    // close_rate: 41.7 vs 37.5 -> +4.2% / +11.2%, also straight from the API.
    expect(screen.getByText('+4.2% (+11.2%) vs. previous period')).toBeInTheDocument()
  })

  it('reports an undefined percentage change instead of inventing one', async () => {
    // improved_agents_count has previous_value: null.
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)
    expect(screen.getByText(/no comparable previous period/i)).toBeInTheDocument()
  })

  it('renders attention calls in the order the backend supplied', async () => {
    const { container } = renderOverview()
    await screen.findByText(/12 calls analyzed/i)

    const rows = Array.from(container.querySelectorAll('[class*="attentionRow"]'))
    expect(rows).toHaveLength(2)
    // Backend sorted critical (80) before medium (50); the UI must not reorder.
    expect(rows[0].textContent).toContain('Michael Ben-David')
    expect(rows[1].textContent).toContain('Daniel Cohen')
  })

  it('renders recent calls', async () => {
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)
    expect(screen.getByText(/Sarah Levi · Northwind Solutions/)).toBeInTheDocument()
  })

  it('renders improved agents from the API', async () => {
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)
    expect(screen.getByText('+0.50')).toBeInTheDocument()
    expect(screen.getByText('4.00 → 4.50')).toBeInTheDocument()
  })

  it('renders four close-rate trend buckets', async () => {
    const { container } = renderOverview()
    await screen.findByText(/12 calls analyzed/i)
    expect(container.querySelectorAll('[class*="trendBucket"]').length).toBeGreaterThanOrEqual(4)
  })

  it('renders a call with a null customer name safely', async () => {
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)
    // CALL_014 has customer_name: null -- the agent name renders with no
    // trailing separator and no "null".
    expect(screen.getByText('Michael Ben-David')).toBeInTheDocument()
    expect(screen.queryByText(/null/)).not.toBeInTheDocument()
  })
})

describe('Overview period selector', () => {
  it('requests 7d by default', async () => {
    const fetchMock = stubFetch([{ match: '/overview', body: makeOverview() }])
    vi.stubGlobal('fetch', fetchMock)
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)
    expect(String(fetchMock.mock.calls[0][0])).toContain('period=7d')
  })

  it('refetches with period=30d when the selector is switched', async () => {
    const fetchMock = stubFetch([{ match: '/overview', body: makeOverview() }])
    vi.stubGlobal('fetch', fetchMock)
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)

    await userEvent.click(screen.getAllByRole('button', { name: /last 30 days/i })[0])

    await waitFor(() => {
      expect(fetchMock.mock.calls.some((call: unknown[]) => String(call[0]).includes('period=30d'))).toBe(true)
    })
  })

  it('marks the active period for assistive technology', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)
    expect(screen.getAllByRole('button', { name: /last 7 days/i })[0]).toHaveAttribute('aria-pressed', 'true')
  })
})

describe('Overview navigation', () => {
  it('navigates to Call Details using the backend call_id', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)

    await userEvent.click(screen.getByText('Michael Ben-David'))
    expect(await screen.findByText('call details for test')).toBeInTheDocument()
  })

  it('navigates from a recent call row', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    await screen.findByText(/12 calls analyzed/i)

    await userEvent.click(screen.getByText(/Sarah Levi · Northwind Solutions/))
    expect(await screen.findByText('call details for test')).toBeInTheDocument()
  })
})

describe('Overview data quality', () => {
  it('discloses skipped malformed records', async () => {
    const overview = makeOverview()
    overview.data_quality.skipped_malformed_records = 2
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: overview }]))
    renderOverview()
    expect(await screen.findByText(/2 stored records were unreadable/i)).toBeInTheDocument()
  })
})
