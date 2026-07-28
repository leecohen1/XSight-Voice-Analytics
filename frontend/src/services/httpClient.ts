import type { ApiError } from '../types'

export class HttpError extends Error implements ApiError {
  code: string
  stage?: string
  details?: unknown

  constructor(error: ApiError) {
    super(error.message)
    this.name = 'HttpError'
    this.code = error.code
    this.stage = error.stage
    this.details = error.details
  }
}

/**
 * The n8n webhook's own error envelope (from its "Build Error Response" /
 * "Respond Error" nodes) — reverse-engineered from a live execution trace,
 * not documented in docs/api_contracts.md (that file only covers the four
 * backend services' direct contracts, not n8n's response shape). Kept
 * separate from the official `CallAnalysisResult` contract so a shape
 * mismatch here never gets confused with the documented schema.
 */
interface N8nErrorEnvelope {
  status?: string
  stage?: string
  error_code?: string
  message?: string
  processing_time_ms?: number
  workflow_version?: string
}

function isN8nErrorEnvelope(value: unknown): value is N8nErrorEnvelope {
  return typeof value === 'object' && value !== null && ('message' in value || 'stage' in value || 'error_code' in value)
}

/**
 * Thin fetch wrapper used by the one real integration this phase has
 * (`callsApi.uploadCall`'s multipart POST to the n8n webhook). Not used by
 * any other API module yet — every other module is mock-only and documents
 * that explicitly rather than routing through here to a URL that doesn't
 * exist.
 *
 * Error messages here are written for display in the UI's main failure
 * text — never include the raw request URL in `message`. The URL and any
 * raw backend payload are attached under `details` instead, for a
 * "Technical details" section only.
 */
/** The backend services' shared error envelope: {"error": {code, message, details}}. */
interface ServiceErrorEnvelope {
  error?: { code?: string; message?: string; details?: unknown }
}

function isServiceErrorEnvelope(value: unknown): value is ServiceErrorEnvelope {
  return typeof value === 'object' && value !== null && 'error' in value
}

/**
 * GET + parse JSON from one of the backend services.
 *
 * Used by every real read path (Overview, Calls, Call Details). Like
 * `postMultipart`, the user-facing `message` never contains the request
 * URL — that goes under `details` for a "Technical details" disclosure only.
 */
export async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  let response: Response
  try {
    response = await fetch(url, { method: 'GET', headers: { Accept: 'application/json' }, signal })
  } catch (networkError) {
    if (networkError instanceof DOMException && networkError.name === 'AbortError') throw networkError
    const technicalMessage = networkError instanceof Error ? networkError.message : String(networkError)
    throw new HttpError({
      code: 'NETWORK_ERROR',
      message: 'Could not reach the call data service. Check that it is running and try again.',
      details: { url, technicalMessage },
    })
  }

  let bodyText = ''
  let parsed: unknown = null
  try {
    bodyText = await response.text()
    parsed = bodyText ? JSON.parse(bodyText) : null
  } catch {
    // Non-JSON body; bodyText is still carried into details below.
  }

  if (!response.ok) {
    const envelope = isServiceErrorEnvelope(parsed) ? parsed.error : undefined
    throw new HttpError({
      code: envelope?.code ?? 'HTTP_ERROR',
      message: envelope?.message ?? `The call data service returned HTTP ${response.status}.`,
      details: { url, httpStatus: response.status, responseBody: parsed ?? (bodyText || undefined) },
    })
  }

  return parsed as T
}

export async function postMultipart<T>(url: string, formData: FormData): Promise<T> {
  let response: Response
  try {
    response = await fetch(url, { method: 'POST', body: formData })
  } catch (networkError) {
    const technicalMessage = networkError instanceof Error ? networkError.message : String(networkError)
    throw new HttpError({
      code: 'NETWORK_ERROR',
      message: 'Could not reach the analysis service. Check your connection and try again.',
      details: { url, technicalMessage },
    })
  }

  if (!response.ok) {
    let bodyText = ''
    let parsed: unknown = null
    try {
      bodyText = await response.text()
      parsed = bodyText ? JSON.parse(bodyText) : null
    } catch {
      // Response body wasn't JSON (or was empty) — bodyText is still kept for details.
    }

    const envelope = isN8nErrorEnvelope(parsed) ? parsed : null

    throw new HttpError({
      code: envelope?.error_code ?? 'HTTP_ERROR',
      message: envelope?.message ?? `The analysis service could not process this request (HTTP ${response.status}).`,
      stage: envelope?.stage,
      details: {
        url,
        httpStatus: response.status,
        statusText: response.statusText,
        responseBody: parsed ?? (bodyText || undefined),
      },
    })
  }

  return response.json() as Promise<T>
}
