import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import CallDetails from './CallDetails'
import { makeCallRecord, stubFetch } from '../test/fixtures'

const SERVICE_URL = 'http://localhost:8006'

function renderDetails(callId: string, state?: unknown) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: `/calls/${callId}`, state }]}>
      <Routes>
        <Route path="/calls/:callId" element={<CallDetails />} />
        <Route path="/calls" element={<div>calls list</div>} />
      </Routes>
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.stubEnv('VITE_CALL_DATA_SERVICE_URL', SERVICE_URL)
})

describe('CallDetails', () => {
  it('fetches the call by its backend call_id', async () => {
    const fetchMock = stubFetch([{ match: '/calls/CALL_001', body: makeCallRecord() }])
    vi.stubGlobal('fetch', fetchMock)

    renderDetails('CALL_001')
    // The agent name legitimately appears twice: once as the breadcrumb's
    // last segment (standard breadcrumb convention -- it names the current
    // page), once as the H1. It is the raw call id that must not repeat.
    expect((await screen.findAllByText('Sarah Levi')).length).toBeGreaterThan(0)
    expect(String(fetchMock.mock.calls[0][0])).toBe(`${SERVICE_URL}/calls/CALL_001`)
  })

  it('loads a live uuid call id on a cold page load (refresh works)', async () => {
    const id = 'CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c'
    vi.stubGlobal(
      'fetch',
      stubFetch([{ match: '/calls/', body: makeCallRecord({ call_id: id, source: 'live_analysis', agent_name: 'Daniel Cohen' }) }])
    )
    // No router state at all -- exactly what a browser refresh produces.
    renderDetails(id)
    expect((await screen.findAllByText('Daniel Cohen')).length).toBeGreaterThan(0)
  })

  it('shows the raw call id exactly once, as secondary metadata', async () => {
    const id = 'CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c'
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls/', body: makeCallRecord({ call_id: id, source: 'live_analysis' }) }]))
    renderDetails(id)
    await screen.findAllByText('Sarah Levi')
    expect(screen.getAllByText(id)).toHaveLength(1)
  })

  it('renders a seeded historical record whose optional fields are null', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls/', body: makeCallRecord() }]))
    renderDetails('CALL_001')
    await screen.findAllByText('Sarah Levi')
    // No "null", "NaN" or "undefined" leaks into the rendered output.
    expect(document.body.textContent).not.toMatch(/\bnull\b|\bNaN\b|\bundefined\b/)
  })

  it('shows a not-found state for a call that does not exist', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls/', status: 404, body: { error: { code: 'CALL_NOT_FOUND', message: 'nope' } } }]))
    renderDetails('CALL_999')
    expect(await screen.findByText(/Call not found/i)).toBeInTheDocument()
  })

  it('falls back to the just-analyzed result when the record is not yet readable', async () => {
    // Persistence failed, so the record is not in storage -- the user must
    // still see the analysis they just paid for.
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls/', status: 404, body: { error: { code: 'CALL_NOT_FOUND', message: 'nope' } } }]))
    const id = 'CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c'
    renderDetails(id, {
      justAnalyzed: {
        call_id: id,
        created_at: '2026-07-28T10:00:00Z',
        call_date: '2026-07-28',
        agent_name: 'Noa Friedman',
        customer_name: 'Basalt & Kerr',
        status: 'completed',
        router_reasons: [],
        analysis: makeCallRecord().analysis,
      },
    })
    expect((await screen.findAllByText(/Noa Friedman/)).length).toBeGreaterThan(0)
  })

  it('surfaces a storage error when there is no fallback analysis', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls/', status: 503, body: { error: { code: 'STORAGE_UNAVAILABLE', message: 'storage down' } } }]))
    renderDetails('CALL_001')
    expect(await screen.findByText(/storage down/i)).toBeInTheDocument()
  })
})
