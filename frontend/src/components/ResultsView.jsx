import GuardrailBanner from './GuardrailBanner'

function ScoreBadge({ label, value, max = 5 }) {
  return (
    <div className="score-badge">
      <span className="score-badge-label">{label}</span>
      <span className="score-badge-value">
        {value ?? '—'} <span className="score-badge-max">/ {max}</span>
      </span>
    </div>
  )
}

function Pill({ text, tone }) {
  return <span className={`pill pill-${tone ?? 'default'}`}>{text}</span>
}

function sentimentTone(sentiment) {
  if (sentiment === 'positive') return 'good'
  if (sentiment === 'negative') return 'bad'
  return 'neutral'
}

function riskTone(risk) {
  if (risk === 'Low') return 'good'
  if (risk === 'High') return 'bad'
  return 'neutral'
}

function outcomeTone(outcome) {
  if (outcome === 'Sale') return 'good'
  if (outcome === 'No Sale') return 'bad'
  return 'neutral'
}

/**
 * Renders the complete final output JSON (see CLAUDE.md "Final output JSON
 * schema") — every field from the schema is rendered somewhere on this page.
 * Used identically whether `result` came from the mock fixture or a live
 * n8n webhook response, so there is no code fork between mock/real modes.
 */
export default function ResultsView({ result }) {
  if (!result) return null

  const {
    transcript,
    call_summary,
    customer_intent,
    main_objection,
    customer_sentiment,
    call_outcome,
    agent_performance_score,
    lead_quality_score,
    similar_calls = [],
    coaching_feedback = [],
    recommended_next_action,
    suggested_follow_up_email,
    routing_category,
    confidence,
    risk_level,
    detected_signals = [],
    limitations,
    guardrail_status,
  } = result

  const confidencePct =
    typeof confidence === 'number' ? Math.round(confidence * 100) : null

  return (
    <div className="results-view">
      <GuardrailBanner status={guardrail_status} limitations={limitations} />

      <section className="results-section results-hero">
        <div className="results-hero-badges">
          <Pill text={`Outcome: ${call_outcome ?? '—'}`} tone={outcomeTone(call_outcome)} />
          <Pill
            text={`Sentiment: ${customer_sentiment ?? '—'}`}
            tone={sentimentTone(customer_sentiment)}
          />
          <Pill text={`Risk: ${risk_level ?? '—'}`} tone={riskTone(risk_level)} />
          <Pill text={`Routing: ${routing_category ?? '—'}`} />
          <Pill
            text={confidencePct !== null ? `Confidence: ${confidencePct}%` : 'Confidence: —'}
          />
        </div>
        <div className="results-hero-scores">
          <ScoreBadge label="Agent Performance" value={agent_performance_score} />
          <ScoreBadge label="Lead Quality" value={lead_quality_score} />
        </div>
      </section>

      <section className="results-section">
        <h2>Call Summary</h2>
        <p>{call_summary || '—'}</p>
      </section>

      <div className="results-grid-2">
        <section className="results-section">
          <h2>Customer Intent</h2>
          <p>{customer_intent || '—'}</p>
        </section>
        <section className="results-section">
          <h2>Main Objection</h2>
          <p>{main_objection || '—'}</p>
        </section>
      </div>

      <section className="results-section">
        <h2>Detected Signals</h2>
        {detected_signals.length > 0 ? (
          <div className="tag-list">
            {detected_signals.map((signal, i) => (
              <span className="tag" key={i}>
                {signal}
              </span>
            ))}
          </div>
        ) : (
          <p className="muted">None detected.</p>
        )}
      </section>

      <section className="results-section">
        <h2>Similar Historical Calls</h2>
        {similar_calls.length > 0 ? (
          <div className="similar-calls">
            {similar_calls.map((call) => (
              <div className="similar-call-card" key={call.call_id}>
                <div className="similar-call-header">
                  <span className="citation-badge" title="Historical call citation">
                    {call.call_id}
                  </span>
                  <span className="similar-call-agent">{call.agent_name}</span>
                  <Pill text={call.sale_result} tone={outcomeTone(call.sale_result)} />
                  <span className="similar-call-score">
                    similarity {Math.round((call.similarity_score ?? 0) * 100)}%
                  </span>
                </div>
                <p className="similar-call-objection">
                  Objection: <strong>{call.main_objection}</strong>
                </p>
                <p className="similar-call-reason">{call.reason}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">Not enough evidence — no similar historical calls retrieved.</p>
        )}
      </section>

      <section className="results-section">
        <h2>Coaching Feedback</h2>
        {coaching_feedback.length > 0 ? (
          <ul className="feedback-list">
            {coaching_feedback.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">No coaching feedback provided.</p>
        )}
      </section>

      <div className="results-grid-2">
        <section className="results-section">
          <h2>Recommended Next Action</h2>
          <p>{recommended_next_action || '—'}</p>
        </section>
        <section className="results-section">
          <h2>Suggested Follow-up Email</h2>
          <pre className="email-block">{suggested_follow_up_email || '—'}</pre>
        </section>
      </div>

      <section className="results-section">
        <h2>Limitations</h2>
        <p className="limitations-text">{limitations || '—'}</p>
      </section>

      <section className="results-section">
        <h2>Full Transcript</h2>
        <pre className="transcript-block">{transcript || '—'}</pre>
      </section>
    </div>
  )
}
