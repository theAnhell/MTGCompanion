import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { PlayersListPage } from './pages/PlayersListPage'
import { PlayerDetailPage } from './pages/PlayerDetailPage'
import { CommandersListPage } from './pages/CommandersListPage'
import { CommanderDetailPage } from './pages/CommanderDetailPage'
import { DeckDetailPage } from './pages/DeckDetailPage'
import { BinderPage } from './pages/BinderPage'
import { YearlyReportPage } from './pages/YearlyReportPage'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/players" replace />} />
        <Route path="/players" element={<PlayersListPage />} />
        <Route path="/players/:id" element={<PlayerDetailPage />} />
        <Route path="/players/:id/binder" element={<BinderPage />} />
        <Route path="/commanders" element={<CommandersListPage />} />
        <Route path="/commanders/:id" element={<CommanderDetailPage />} />
        <Route path="/decks/:id" element={<DeckDetailPage />} />
        <Route path="/reports/yearly" element={<YearlyReportPage />} />
      </Route>
    </Routes>
  )
}

export default App
