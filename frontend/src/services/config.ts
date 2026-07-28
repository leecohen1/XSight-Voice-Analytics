/**
 * Single source of truth for whether the app is in mock mode. Every API
 * module reads this instead of `import.meta.env` directly, so there is one
 * place to change if the mock/real switching strategy ever changes.
 */
export function isMockMode(): boolean {
  const raw = import.meta.env.VITE_USE_MOCK
  // Default to mock mode if unset — no live backend is guaranteed to exist.
  if (raw === undefined) return true
  return String(raw).toLowerCase() === 'true'
}

export function n8nWebhookUrl(): string | undefined {
  return import.meta.env.VITE_N8N_WEBHOOK_URL
}

/**
 * Base URL of `call_data_service` (the S3-backed business read/write API).
 *
 * Overview, Calls and Call Details read exclusively from here -- there is no
 * mock fallback on those paths, so an unset value must surface as a clear
 * error rather than silently degrading into demo data.
 */
export function callDataServiceUrl(): string {
  const raw = import.meta.env.VITE_CALL_DATA_SERVICE_URL
  if (!raw) {
    throw new Error(
      'VITE_CALL_DATA_SERVICE_URL is not set. Point it at the call data service (default port 8006) in frontend/.env.'
    )
  }
  return String(raw).replace(/\/+$/, '')
}

/** Simulated network latency for mock responses — gives loading states something real to render. */
export function simulateLatency(ms = 500): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
