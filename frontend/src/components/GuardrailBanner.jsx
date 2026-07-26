const STATUS_COPY = {
  pass: {
    label: 'Guardrails: Pass',
    className: 'guardrail-banner guardrail-pass',
  },
  flagged: {
    label: 'Flagged — Review Recommended',
    className: 'guardrail-banner guardrail-flagged',
  },
  human_review_required: {
    label: 'Human Review Required',
    className: 'guardrail-banner guardrail-review',
  },
}

/**
 * Prominent top-of-page banner reflecting guardrail_status.
 * For "flagged" / "human_review_required" this is intentionally loud and
 * carries the limitations text inline, per today's priority on making
 * limitations/human-review state impossible to miss (not buried at the
 * bottom of the results page).
 */
export default function GuardrailBanner({ status, limitations }) {
  const copy = STATUS_COPY[status] ?? {
    label: `Guardrails: ${status ?? 'unknown'}`,
    className: 'guardrail-banner guardrail-unknown',
  }

  const isUrgent = status === 'flagged' || status === 'human_review_required'

  return (
    <div className={copy.className} role={isUrgent ? 'alert' : 'status'}>
      <div className="guardrail-banner-title">
        <span className="guardrail-dot" aria-hidden="true" />
        {copy.label}
      </div>
      {isUrgent && limitations && (
        <p className="guardrail-banner-limitations">{limitations}</p>
      )}
    </div>
  )
}
