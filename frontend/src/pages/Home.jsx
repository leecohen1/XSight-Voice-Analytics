import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="page page-home">
      <h1>XSight</h1>
      <p className="tagline">AI-powered sales call analytics</p>
      <p>
        XSight analyzes recorded sales calls to explain why a call succeeded or failed:
        customer intent, objections raised, sentiment, agent performance, and whether
        follow-up is needed — grounded against similar historical calls, with clear
        limitations and a human-review flag whenever the evidence isn't strong enough
        for an automatic call.
      </p>
      <ul className="home-points">
        <li>Upload a sales call recording and basic call metadata</li>
        <li>Automatic transcription and structured extraction</li>
        <li>Comparison against similar historical calls, with call_id citations</li>
        <li>Coaching feedback, a recommended next action, and a draft follow-up email</li>
        <li>Guardrail status surfaced up front — flagged results are never hidden</li>
      </ul>
      <Link className="button button-primary" to="/upload">
        Analyze a Sales Call
      </Link>
    </div>
  )
}
