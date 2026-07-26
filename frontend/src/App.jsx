import { NavLink, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import Upload from './pages/Upload'
import Results from './pages/Results'

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-logo">XSight</span>
        <nav className="app-nav">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/upload">Upload</NavLink>
          <NavLink to="/results">Results</NavLink>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/results" element={<Results />} />
        </Routes>
      </main>
    </div>
  )
}
