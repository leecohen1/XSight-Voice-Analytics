import exampleAnalysis from '../mocks/exampleAnalysis.json'

/**
 * Whether the app should skip the real n8n webhook and return a fixture instead.
 * Controlled by VITE_USE_MOCK in .env (string "true"/"false").
 */
export const isMockMode = () => {
  const raw = import.meta.env.VITE_USE_MOCK
  // Default to mock mode if unset, since no live webhook is guaranteed to exist yet.
  if (raw === undefined) return true
  return String(raw).toLowerCase() === 'true'
}

const MOCK_DELAY_MS = 900

/**
 * Submits a sales call upload (audio file + form metadata) for analysis.
 *
 * In mock mode, returns a realistic fixture shaped exactly like the final
 * output JSON schema (see CLAUDE.md "Final output JSON schema") without any
 * network call.
 *
 * In real mode, POSTs a multipart/form-data request (the payload includes an
 * audio file) to the n8n webhook URL configured via VITE_N8N_WEBHOOK_URL, and
 * returns the parsed JSON response — expected to match the same schema.
 *
 * @param {{
 *   audioFile: File,
 *   agentName: string,
 *   callDate: string,
 *   customerName?: string,
 *   notes?: string,
 * }} submission
 * @returns {Promise<object>} the final output JSON (see CLAUDE.md schema)
 */
export async function analyzeCall(submission) {
  if (isMockMode()) {
    await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY_MS))
    // Return a fresh deep copy so nothing downstream can mutate the shared fixture.
    return JSON.parse(JSON.stringify(exampleAnalysis))
  }

  const webhookUrl = import.meta.env.VITE_N8N_WEBHOOK_URL
  if (!webhookUrl) {
    throw new Error(
      'VITE_N8N_WEBHOOK_URL is not set. Set it in frontend/.env to point at the live n8n webhook, ' +
        'or set VITE_USE_MOCK=true to use fixture data.'
    )
  }

  const formData = new FormData()
  formData.append('audio_file', submission.audioFile)
  formData.append('agent_name', submission.agentName)
  formData.append('call_date', submission.callDate)
  if (submission.customerName) {
    formData.append('customer_name', submission.customerName)
  }
  if (submission.notes) {
    formData.append('notes', submission.notes)
  }

  let response
  try {
    response = await fetch(webhookUrl, {
      method: 'POST',
      body: formData,
    })
  } catch (networkError) {
    throw new Error(
      `Could not reach the n8n webhook at ${webhookUrl}. Check the URL and that the workflow is active. (${networkError.message})`
    )
  }

  if (!response.ok) {
    let detail = ''
    try {
      detail = await response.text()
    } catch {
      // ignore
    }
    throw new Error(
      `n8n webhook responded with ${response.status} ${response.statusText}.${detail ? ` ${detail}` : ''}`
    )
  }

  return response.json()
}
