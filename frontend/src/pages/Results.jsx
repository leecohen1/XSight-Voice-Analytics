import { Link, useLocation } from 'react-router-dom'
import ResultsView from '../components/ResultsView'

export default function Results() {
  const location = useLocation()
  const result = location.state?.result

  if (!result) {
    return (
      <div className="page page-results">
        <h1>Results</h1>
        <p>
          No analysis result to show yet — this page is populated right after you submit
          a call on the Upload page.
        </p>
        <Link className="button button-primary" to="/upload">
          Go to Upload
        </Link>
      </div>
    )
  }

  return (
    <div className="page page-results">
      <ResultsView result={result} />
    </div>
  )
}
