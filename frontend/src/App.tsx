import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import Overview from './pages/Overview'
import AnalyzeCall from './pages/AnalyzeCall'
import Calls from './pages/Calls'
import CallDetails from './pages/CallDetails'
import TeamIntelligence from './pages/TeamIntelligence'
import AiOperations from './pages/AiOperations'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<Overview />} />
        <Route path="/analyze" element={<AnalyzeCall />} />
        <Route path="/calls" element={<Calls />} />
        <Route path="/calls/:callId" element={<CallDetails />} />
        <Route path="/team" element={<TeamIntelligence />} />
        <Route path="/ai-operations" element={<AiOperations />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/overview" replace />} />
      </Route>
    </Routes>
  )
}
