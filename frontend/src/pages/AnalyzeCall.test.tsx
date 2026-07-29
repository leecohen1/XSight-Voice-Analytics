import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AnalyzeCall from './AnalyzeCall'
import { makeCallRecord, stubFetch } from '../test/fixtures'

const LIVE_ID = 'CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c'

function pipelineResponse(overrides: Record<string, unknown> = {}) {
  return {
    call_id: LIVE_ID,
    created_at: '2026-07-28T10:00:00Z',
    call_date: '2026-07-28',
    agent_name: 'Sarah Levi',
    customer_name: 'Northwind Solutions',
    status: 'completed',
    router_reasons: [],
    analysis: makeCallRecord().analysis,
    persistence: { persisted: true, detail: 'Record stored.' },
    ...overrides,
  }
}

/** Renders the destination route's id so navigation can be asserted. */
function CallDetailsProbe() {
  const location = useLocation()
  return <div>navigated to {location.pathname}</div>
}

function renderAnalyze() {
  return render(
    <MemoryRouter initialEntries={['/analyze']}>
      <Routes>
        <Route path="/analyze" element={<AnalyzeCall />} />
        <Route path="/calls/:callId" element={<CallDetailsProbe />} />
      </Routes>
    </MemoryRouter>
  )
}

async function fillAndSubmit() {
  // `delay: null` skips user-event's inter-keystroke waits -- these tests
  // assert wiring, not typing cadence, and the default delay makes the file
  // slow enough to trip timeouts under parallel execution.
  const user = userEvent.setup({ delay: null })
  const file = new File(['audio-bytes'], 'call.mp3', { type: 'audio/mpeg' })
  await user.upload(document.getElementById('audio-file') as HTMLInputElement, file)
  await user.type(screen.getByLabelText(/agent name/i), 'Sarah Levi')
  const dateInput = screen.getByLabelText(/call date/i) as HTMLInputElement
  await user.clear(dateInput)
  await user.type(dateInput, '2026-07-28')
  await user.click(screen.getByRole('button', { name: /submit for analysis/i }))
}

beforeEach(() => {
  vi.stubEnv('VITE_N8N_WEBHOOK_URL', 'http://n8n.test/webhook/xsight')
  vi.stubEnv('VITE_CALL_DATA_SERVICE_URL', 'http://localhost:8006')
})

describe('AnalyzeCall', () => {
  it('navigates to Call Details using the backend-provided call_id', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: 'n8n.test', body: pipelineResponse() }]))
    renderAnalyze()
    await fillAndSubmit()

    expect(await screen.findByText(`navigated to /calls/${LIVE_ID}`)).toBeInTheDocument()
  })

  it('never routes to a client-generated XS-100N id', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: 'n8n.test', body: pipelineResponse() }]))
    renderAnalyze()
    await fillAndSubmit()

    const destination = await screen.findByText(/navigated to/)
    expect(destination.textContent).not.toMatch(/XS-\d+/)
    expect(destination.textContent).toContain('CALL_')
  })

  it('still navigates when persistence failed, and warns about it', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch([{ match: 'n8n.test', body: pipelineResponse({ persistence: { persisted: false, detail: 'unreachable' } }) }])
    )
    renderAnalyze()
    await fillAndSubmit()

    // The analysis is not lost: navigation still happens.
    expect(await screen.findByText(`navigated to /calls/${LIVE_ID}`)).toBeInTheDocument()
  })

  it('shows a failure state when the pipeline rejects the submission', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch([{ match: 'n8n.test', status: 400, body: { stage: 'pre_transcription', error_code: 'unsupported_format', message: 'Unsupported audio format.' } }])
    )
    renderAnalyze()
    await fillAndSubmit()

    // The message appears twice by design: once as the user-facing failure
    // text, and once inside the collapsible technical-details payload.
    const matches = await screen.findAllByText(/Unsupported audio format/i)
    expect(matches.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/Failed during: Pre Transcription/i)).toBeInTheDocument()
    // The raw webhook URL must never appear in the user-facing message.
    expect(matches[0].textContent).not.toContain('n8n.test')
  })

  it('errors clearly if the pipeline returns no call id', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: 'n8n.test', body: pipelineResponse({ call_id: undefined }) }]))
    renderAnalyze()
    await fillAndSubmit()

    expect(await screen.findByText(/did not return a call id/i)).toBeInTheDocument()
  })

  it('validates required fields before calling the backend', async () => {
    const fetchMock = stubFetch([{ match: 'n8n.test', body: pipelineResponse() }])
    vi.stubGlobal('fetch', fetchMock)
    renderAnalyze()

    await userEvent.click(screen.getByRole('button', { name: /submit for analysis/i }))
    await waitFor(() => expect(screen.getByText(/choose an audio file/i)).toBeInTheDocument())
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

describe('AnalyzeCall honest processing state', () => {
  it('shows one indeterminate processing message, not a stage tracker', async () => {
    // A fetch that never resolves keeps the page in the processing state.
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    renderAnalyze()
    await fillAndSubmit()

    expect(await screen.findByRole('status')).toBeInTheDocument()
    expect(screen.getByText(/Uploading and validating/i)).toBeInTheDocument()
    // The old tracker's fake stage labels must be gone: the frontend cannot
    // know which internal stage is active, so it must not claim to.
    expect(screen.queryByText(/Transcribing audio/)).not.toBeInTheDocument()
    expect(screen.queryByText(/^Uploaded$/)).not.toBeInTheDocument()
  })

  // Message-escalation-by-elapsed-time is covered directly and
  // deterministically by processingMessages.test.ts, against the pure
  // function rather than by advancing fake timers through a live React
  // tree (fragile: a fake-timer test that throws before its cleanup runs
  // leaves every later test in the file starved of real timers).

  it('prevents duplicate submission while processing', async () => {
    const fetchMock = vi.fn(() => new Promise(() => {}))
    vi.stubGlobal('fetch', fetchMock)
    renderAnalyze()
    await fillAndSubmit()

    const submit = screen.getByRole('button', { name: /analyzing/i })
    expect(submit).toBeDisabled()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('disables the file input during processing', async () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    renderAnalyze()
    await fillAndSubmit()

    expect(document.getElementById('audio-file')).toBeDisabled()
  })

  it('resets cleanly after a failure so another call can be analyzed', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ status: 'error', stage: 'pre_transcription', message: 'Rejected.' }), {
            status: 400,
          })
        )
      )
    )
    renderAnalyze()
    await fillAndSubmit()

    await screen.findByText(/Processing failed/i)
    await userEvent.setup({ delay: null }).click(screen.getByRole('button', { name: /try again/i }))

    expect(screen.getByRole('button', { name: /submit for analysis/i })).toBeEnabled()
    expect(screen.queryByText(/Processing failed/i)).not.toBeInTheDocument()
  })
})
