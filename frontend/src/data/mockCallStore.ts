/**
 * In-memory mock "database" for calls — an ES module singleton, so it
 * persists for the lifetime of the browser tab (not across reloads). This
 * is what gives the mock-mode demo its "persistent call history" feel:
 * Analyze Call writes a new record here, and Calls / Call Details read it
 * back. `services/callsApi.ts` is the only module allowed to import this —
 * pages never touch it directly.
 */
import type { CallRecord } from '../types'
import { mockCalls } from './mockCalls'

let calls: CallRecord[] = [...mockCalls]

export function listMockCalls(): CallRecord[] {
  return [...calls].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
}

export function getMockCall(callId: string): CallRecord | undefined {
  return calls.find((call) => call.callId === callId)
}

export function addMockCall(record: CallRecord): void {
  calls = [record, ...calls]
}

export function updateMockCall(callId: string, patch: Partial<CallRecord>): CallRecord | undefined {
  let updated: CallRecord | undefined
  calls = calls.map((call) => {
    if (call.callId !== callId) return call
    updated = { ...call, ...patch }
    return updated
  })
  return updated
}

let nextSequence = calls.length + 1

export function generateMockCallId(): string {
  const id = `XS-${1000 + nextSequence}`
  nextSequence += 1
  return id
}
