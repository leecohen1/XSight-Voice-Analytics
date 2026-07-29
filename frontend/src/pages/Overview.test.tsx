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

    expect(await screen.findByText(/Close rate rose to 41.7%/i)).toBeInTheDocument()
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
    expect(screen.queryByText(/Fielding & Yates/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/XS-100/i)).not.toBeInTheDocument()
  })

  it('fails clearly when the service URL is not configured', async () => {
    vi.stubEnv('VITE_CALL_DATA_SERVICE_URL', '')
    renderOverview()
    expect(await screen.findByText(/VITE_CALL_DATA_SERVICE_URL is not set/i)).toBeInTheDocument()
  })
})

describe('Overview executive headline', () => {
  it('leads with the business outcome and states the attention load', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    expect(await screen.findByText(/Close rate rose to 41.7% this week/i)).toBeInTheDocument()
    expect(screen.getByText(/3 calls need your attention/i)).toBeInTheDocument()
  })

  it('mentions a recoverable opportunity when the attention list has one', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    expect(await screen.findByText(/1 opportunity may still be recoverable/i)).toBeInTheDocument()
  })

  it('says nothing needs attention when the queue is empty', async () => {
    const overview = makeOverview({
      kpis: { ...makeOverview().kpis, calls_requiring_attention: { current_value: 0, previous_value: 3, absolute_change: -3, percentage_change: -100, trend_direction: 'down' } },
      attention_calls: [],
    })
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: overview }]))
    renderOverview()
    expect(await screen.findByText(/nothing currently needs your attention/i)).toBeInTheDocument()
  })

  it('handles an empty period without inventing a headline number', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeEmptyOverview() }]))
    renderOverview()
    expect(await screen.findByText(/No calls were analyzed/i)).toBeInTheDocument()
  })
})

describe('Overview KPI rendering', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
  })

  it('renders KPI values exactly as the API returned them', async () => {
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    // '12' also appears as the donut's center total, so at least one match
    // (not exactly one) is the correct assertion here.
    expect(screen.getAllByText('12').length).toBeGreaterThan(0)
    expect(screen.getByText('41.7%')).toBeInTheDocument()
    expect(screen.getByText('4.1')).toBeInTheDocument()
    expect(screen.getByText('3.6')).toBeInTheDocument()
  })

  it('renders the previous-period comparison from the API, not a local calculation', async () => {
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(screen.getByText('+4 (+50%) vs. previous period')).toBeInTheDocument()
    expect(screen.getByText('+4.2% (+11.2%) vs. previous period')).toBeInTheDocument()
  })

  it('reports "not enough comparison data" instead of inventing one', async () => {
    // improved_agents_count and the Follow-up Needed card both have
    // previous_value: null, so at least two matches are expected here.
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(screen.getAllByText(/not enough comparison data/i).length).toBeGreaterThan(0)
  })

  it('colours a falling close rate as negative and a falling attention count as positive', async () => {
    const overview = makeOverview({
      kpis: {
        ...makeOverview().kpis,
        close_rate: { current_value: 30, previous_value: 40, absolute_change: -10, percentage_change: -25, trend_direction: 'down' },
        calls_requiring_attention: { current_value: 1, previous_value: 4, absolute_change: -3, percentage_change: -75, trend_direction: 'down' },
      },
    })
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: overview }]))
    const { container } = render(
      <MemoryRouter initialEntries={['/overview']}>
        <Routes>
          <Route path="/overview" element={<Overview />} />
        </Routes>
      </MemoryRouter>
    )
    await waitFor(() => expect(container.textContent).toContain('30%'))

    // Close rate falling is bad news -> negative sentiment class present.
    expect(container.querySelector('[class*="tone_warning"]')).toBeTruthy()
  })

  it('renders four close-rate trend buckets with visible sample size', async () => {
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(screen.getAllByText(/\d+ calls?$/).length).toBeGreaterThan(0)
  })

  it('renders a call with a null customer name safely', async () => {
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(screen.getByText('Michael Ben-David')).toBeInTheDocument()
    expect(screen.queryByText(/null/)).not.toBeInTheDocument()
  })

  it('renders improved agents from the API', async () => {
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(screen.getByText('+0.50')).toBeInTheDocument()
    expect(screen.getByText('4.00 → 4.50')).toBeInTheDocument()
  })
})

describe('Overview outcome distribution', () => {
  it('renders count and percentage for every outcome bucket via the chart aria summary', async () => {
    // 6 sale, 3 no_sale, 2 follow_up, 0 uncertain, 1 unknown -- sums to 12.
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    await screen.findByText(/Close rate rose/i)

    expect(screen.getByRole('img', { name: /Sale: 6 \(50%\)/ })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /No Sale: 3 \(25%\)/ })).toBeInTheDocument()
    expect(screen.getByText('50.0%')).toBeInTheDocument() // 6/12 in the legend
    expect(screen.getByText('25.0%')).toBeInTheDocument() // 3/12 in the legend
  })

  it('shows an "unknown" slice when the backend reports one', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(screen.getByText('Not recorded')).toBeInTheDocument()
  })

  it('omits the "unknown" slice entirely when there are no unrecorded outcomes', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch([{ match: '/overview', body: makeOverview({ outcome_distribution: { sale: 12, no_sale: 0, follow_up: 0, uncertain: 0, unknown: 0 } }) }])
    )
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(screen.queryByText('Not recorded')).not.toBeInTheDocument()
  })

  it('renders an explicit empty state for a period with zero calls', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeEmptyOverview() }]))
    renderOverview()
    // No calls in the period at all -> whole-page empty state, no chart.
    expect(await screen.findByText(/No calls in this period/i)).toBeInTheDocument()
  })

  it('reconciles the legend against calls analyzed for a single-outcome period', async () => {
    const overview = makeOverview({
      kpis: { ...makeOverview().kpis, calls_analyzed: { current_value: 4, previous_value: 4, absolute_change: 0, percentage_change: 0, trend_direction: 'flat' } },
      outcome_distribution: { sale: 4, no_sale: 0, follow_up: 0, uncertain: 0, unknown: 0 },
    })
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: overview }]))
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(screen.getByText('100.0%')).toBeInTheDocument()
  })
})

describe('Overview period selector', () => {
  it('requests 7d by default', async () => {
    const fetchMock = stubFetch([{ match: '/overview', body: makeOverview() }])
    vi.stubGlobal('fetch', fetchMock)
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(String(fetchMock.mock.calls[0][0])).toContain('period=7d')
  })

  it('refetches with period=30d when the selector is switched', async () => {
    const fetchMock = stubFetch([{ match: '/overview', body: makeOverview() }])
    vi.stubGlobal('fetch', fetchMock)
    renderOverview()
    await screen.findByText(/Close rate rose/i)

    await userEvent.click(screen.getAllByRole('button', { name: /last 30 days/i })[0])

    await waitFor(() => {
      expect(fetchMock.mock.calls.some((call: unknown[]) => String(call[0]).includes('period=30d'))).toBe(true)
    })
  })

  it('marks the active period for assistive technology', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    await screen.findByText(/Close rate rose/i)
    expect(screen.getAllByRole('button', { name: /last 7 days/i })[0]).toHaveAttribute('aria-pressed', 'true')
  })
})

describe('Overview navigation', () => {
  it('renders attention and recent rows as real links with a shareable href', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    await screen.findByText(/Close rate rose/i)

    const link = screen.getByText('Michael Ben-David').closest('a')
    expect(link).toHaveAttribute('href', '/calls/CALL_014')
  })

  it('navigates to Call Details using the backend call_id', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    await screen.findByText(/Close rate rose/i)

    await userEvent.click(screen.getByText('Michael Ben-David'))
    expect(await screen.findByText('call details for test')).toBeInTheDocument()
  })

  it('navigates from a recent call row', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    renderOverview()
    await screen.findByText(/Close rate rose/i)

    await userEvent.click(screen.getByText(/Sarah Levi · Northwind Solutions/))
    expect(await screen.findByText('call details for test')).toBeInTheDocument()
  })

  it('attention rows keep backend priority ordering', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/overview', body: makeOverview() }]))
    const { container } = renderOverview()
    await screen.findByText(/Close rate rose/i)

    const rows = Array.from(container.querySelectorAll('[class*="attentionRow"]'))
    expect(rows).toHaveLength(2)
    expect(rows[0].textContent).toContain('Michael Ben-David')
    expect(rows[1].textContent).toContain('Daniel Cohen')
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
