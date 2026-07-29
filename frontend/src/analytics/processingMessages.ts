/**
 * Analyze Call's processing copy.
 *
 * The webhook is a single blocking request -- the frontend genuinely has no
 * signal for which internal pipeline stage is active, so these are purely
 * user-experience messages about elapsed wait time, never claims about
 * backend state. Kept as pure functions (rather than inline in the
 * component) so the escalation thresholds are testable without mocking
 * timers against a live React tree.
 */
const ELAPSED_MESSAGES: { after: number; text: string }[] = [
  { after: 0, text: 'Uploading and validating the conversation…' },
  { after: 20, text: 'AI analysis is running — transcription, extraction, and evidence retrieval all happen in this step.' },
  { after: 60, text: 'Still processing — the full analysis usually completes in about a minute for the demo recording.' },
  { after: 120, text: 'Taking longer than usual, but the pipeline is still running. The platform limit is 3 minutes.' },
]

export function elapsedMessage(seconds: number): string {
  let message = ELAPSED_MESSAGES[0].text
  for (const entry of ELAPSED_MESSAGES) {
    if (seconds >= entry.after) message = entry.text
  }
  return message
}

export function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}:${String(s).padStart(2, '0')}` : `${s}s`
}
