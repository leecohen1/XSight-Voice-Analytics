import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

// Every test starts from a clean DOM and a clean fetch stub. No test in this
// suite is allowed to reach the network: `fetch` is replaced per test, and an
// unstubbed call fails loudly rather than silently hanging.
beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.reject(new Error('Unexpected network call: stub fetch in the test that needs it.')))
  )
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
  vi.restoreAllMocks()
})
