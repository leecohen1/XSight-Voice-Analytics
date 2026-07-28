import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getCall, listCalls, pipelineResponseToRecord, toCallListItem, uploadCall } from './callsApi'
import { makeCallRecord, makeCallSummary, stubFetch } from '../test/fixtures'
import type { PipelineResponse } from '../types'

const SERVICE_URL = 'http://localhost:8006'

beforeEach(() => {
  vi.stubEnv('VITE_CALL_DATA_SERVICE_URL', SERVICE_URL)
  vi.stubEnv('VITE_N8N_WEBHOOK_URL', 'http://n8n.test/webhook/xsight')
})

describe('listCalls', () => {
  it('calls the real backend endpoint', async () => {
    const fetchMock = stubFetch([
      { match: '/calls', body: { calls: [makeCallSummary()], count: 1, total_scanned: 1, skipped_malformed_records: 0, next_cursor: null } },
    ])
    vi.stubGlobal('fetch', fetchMock)

    await listCalls()
    expect(String(fetchMock.mock.calls[0][0])).toContain(`${SERVICE_URL}/calls`)
  })

  it('maps the backend contract onto the view model', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch([
        { match: '/calls', body: { calls: [makeCallSummary({ customer_name: 'Acme', confidence: 0.82 })], count: 1, total_scanned: 1, skipped_malformed_records: 0, next_cursor: null } },
      ])
    )
    const [call] = await listCalls()
    expect(call.callId).toBe('CALL_001')
    expect(call.agentName).toBe('Sarah Levi')
    expect(call.customerName).toBe('Acme')
    expect(call.confidence).toBe(0.82)
    expect(call.status).toBe('completed')
  })

  it('surfaces a backend error rather than returning demo data', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls', status: 503, body: { error: { code: 'STORAGE_UNAVAILABLE', message: 'storage down' } } }]))
    await expect(listCalls()).rejects.toThrow(/storage down/)
  })

  it('throws a clear error when the service URL is unset', async () => {
    vi.stubEnv('VITE_CALL_DATA_SERVICE_URL', '')
    await expect(listCalls()).rejects.toThrow(/VITE_CALL_DATA_SERVICE_URL is not set/)
  })
})

describe('toCallListItem', () => {
  it('leaves a null customer name undefined rather than rendering "null"', () => {
    const item = toCallListItem(makeCallSummary({ customer_name: null }))
    expect(item.customerName).toBeUndefined()
  })

  it('falls back to the created_at date when call_date is null', () => {
    const item = toCallListItem(makeCallSummary({ call_date: null, created_at: '2026-07-27T09:00:00Z' }))
    expect(item.callDate).toBe('2026-07-27')
  })

  it('carries the attention flags through for list rendering', () => {
    const item = toCallListItem(makeCallSummary({ attention_required: true, attention_priority: 'high' }))
    expect(item.attentionRequired).toBe(true)
    expect(item.attentionPriority).toBe('high')
  })
})

describe('getCall', () => {
  it('fetches one record by its backend call_id', async () => {
    const fetchMock = stubFetch([{ match: '/calls/CALL_001', body: makeCallRecord() }])
    vi.stubGlobal('fetch', fetchMock)

    const call = await getCall('CALL_001')
    expect(String(fetchMock.mock.calls[0][0])).toBe(`${SERVICE_URL}/calls/CALL_001`)
    expect(call?.callId).toBe('CALL_001')
    expect(call?.analysis?.transcript).toContain('Agent:')
  })

  it('url-encodes a uuid-style live call id', async () => {
    const id = 'CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c'
    const fetchMock = stubFetch([{ match: '/calls/', body: makeCallRecord({ call_id: id, source: 'live_analysis' }) }])
    vi.stubGlobal('fetch', fetchMock)

    const call = await getCall(id)
    expect(call?.callId).toBe(id)
  })

  it('returns null for a missing call instead of throwing', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls/', status: 404, body: { error: { code: 'CALL_NOT_FOUND', message: 'No stored call matches that id.' } } }]))
    await expect(getCall('CALL_999')).resolves.toBeNull()
  })

  it('rethrows genuine failures instead of hiding them as "not found"', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls/', status: 503, body: { error: { code: 'STORAGE_UNAVAILABLE', message: 'storage down' } } }]))
    await expect(getCall('CALL_001')).rejects.toThrow(/storage down/)
  })

  it('renders a seeded record whose optional AI fields are all null', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls/', body: makeCallRecord() }]))
    const call = await getCall('CALL_001')
    expect(call?.analysis?.confidence).toBeNull()
    expect(call?.analysis?.risk_level).toBeNull()
    expect(call?.analysis?.similar_calls).toEqual([])
    expect(call?.confidence).toBeUndefined()
    expect(call?.riskLevel).toBeUndefined()
  })

  it('maps router reason codes onto the typed union', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch([
        { match: '/calls/', body: makeCallRecord({ router_reasons: ['call_signal_analyser_confidence_below_0.65', 'langgraph_evidence_conflicts_detected'] }) },
      ])
    )
    const call = await getCall('CALL_001')
    expect(call?.routerReasons?.map((r) => r.code)).toEqual(['low_confidence', 'evidence_conflict'])
  })

  it('degrades an unknown router reason code without crashing', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: '/calls/', body: makeCallRecord({ router_reasons: ['some_future_code'] }) }]))
    const call = await getCall('CALL_001')
    expect(call?.routerReasons?.[0].code).toBe('upstream_failure')
    expect(call?.routerReasons?.[0].detail).toBe('some future code')
  })
})

describe('uploadCall', () => {
  const pipelineResponse: PipelineResponse = {
    call_id: 'CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c',
    created_at: '2026-07-28T10:00:00Z',
    call_date: '2026-07-28',
    agent_name: 'Sarah Levi',
    customer_name: 'Northwind Solutions',
    status: 'completed',
    router_reasons: [],
    analysis: makeCallRecord().analysis,
    persistence: { persisted: true, detail: 'Record stored.' },
  }

  function submission() {
    return {
      audioFile: new File(['audio'], 'call.mp3', { type: 'audio/mpeg' }),
      agentName: 'Sarah Levi',
      callDate: '2026-07-28',
      customerName: 'Northwind Solutions',
      notes: '',
    }
  }

  it('posts multipart to the n8n webhook', async () => {
    const fetchMock = stubFetch([{ match: 'n8n.test', body: pipelineResponse }])
    vi.stubGlobal('fetch', fetchMock)

    await uploadCall(submission())
    expect(String(fetchMock.mock.calls[0][0])).toContain('n8n.test')
  })

  it('returns the backend-owned call_id and never generates one', async () => {
    vi.stubGlobal('fetch', stubFetch([{ match: 'n8n.test', body: pipelineResponse }]))
    const response = await uploadCall(submission())

    expect(response.call_id).toBe('CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c')
    expect(response.call_id).not.toMatch(/^XS-/)
  })

  it('reports a persistence failure without losing the analysis', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch([{ match: 'n8n.test', body: { ...pipelineResponse, persistence: { persisted: false, detail: 'unreachable' } } }])
    )
    const response = await uploadCall(submission())
    expect(response.persistence?.persisted).toBe(false)
    expect(response.analysis.transcript).toBeTruthy()
  })

  it('throws a clear error when the webhook URL is unset', async () => {
    vi.stubEnv('VITE_N8N_WEBHOOK_URL', '')
    await expect(uploadCall(submission())).rejects.toThrow(/VITE_N8N_WEBHOOK_URL is not set/)
  })
})

describe('pipelineResponseToRecord', () => {
  it('converts a pipeline envelope into the same view model as a fetched call', () => {
    const record = pipelineResponseToRecord({
      call_id: 'CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c',
      created_at: '2026-07-28T10:00:00Z',
      call_date: '2026-07-28',
      agent_name: 'Sarah Levi',
      customer_name: null,
      status: 'human_review_required',
      router_reasons: ['langgraph_evidence_conflicts_detected'],
      analysis: makeCallRecord().analysis,
    })

    expect(record.callId).toBe('CALL_3f2b9c1a-4d5e-4f6a-8b7c-9d0e1f2a3b4c')
    expect(record.status).toBe('human_review_required')
    expect(record.customerName).toBeUndefined()
    expect(record.routerReasons?.[0].code).toBe('evidence_conflict')
  })
})
