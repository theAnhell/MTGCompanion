import { useState } from 'react'
import { Link } from 'react-router-dom'
import { getYearlyReport } from '../lib/api'
import { useApi } from '../lib/useApi'
import { LoadingState, ErrorState } from '../components/AsyncState'
import { SectionCard } from '../components/SectionCard'
import { StatTile } from '../components/StatTile'
import { DataTable, type Column } from '../components/DataTable'
import { RankingBars } from '../components/RankingBars'
import type {
  YearlyCommanderByMostPlayed,
  YearlyCommanderByMostWins,
  YearlyCommanderSpeed,
  YearlyPlayerByGames,
  YearlyPlayerByUniqueDecks,
  YearlyPlayerByWinRate,
  YearlyPlayerStreak,
} from '../lib/types'

const defaultYear = new Date().getFullYear() - 1

export function YearlyReportPage() {
  const [year, setYear] = useState(defaultYear)
  const { data: report, loading, error } = useApi(() => getYearlyReport(year), [year])

  const winRateColumns: Column<YearlyPlayerByWinRate>[] = [
    {
      header: 'Player',
      sortValue: (p) => p.name,
      render: (p) => (
        <Link to={`/players/${p.playerId}`} className="font-medium text-primary hover:underline">
          {p.name}
        </Link>
      ),
    },
    { header: 'Win rate', align: 'right', sortValue: (p) => p.rate, render: (p) => `${p.rate}%` },
    { header: 'Wins', align: 'right', sortValue: (p) => p.wins, render: (p) => p.wins },
    { header: 'Games', align: 'right', sortValue: (p) => p.games, render: (p) => p.games },
  ]

  const gamesColumns: Column<YearlyPlayerByGames>[] = [
    {
      header: 'Player',
      sortValue: (p) => p.name,
      render: (p) => (
        <Link to={`/players/${p.playerId}`} className="font-medium text-primary hover:underline">
          {p.name}
        </Link>
      ),
    },
    { header: 'Games', align: 'right', sortValue: (p) => p.games, render: (p) => p.games },
    { header: 'Unique decks', align: 'right', sortValue: (p) => p.uniqueDecks, render: (p) => p.uniqueDecks },
  ]

  const uniqueDeckColumns: Column<YearlyPlayerByUniqueDecks>[] = [
    {
      header: 'Player',
      sortValue: (p) => p.name,
      render: (p) => (
        <Link to={`/players/${p.playerId}`} className="font-medium text-primary hover:underline">
          {p.name}
        </Link>
      ),
    },
    { header: 'Unique decks', align: 'right', sortValue: (p) => p.uniqueDecks, render: (p) => p.uniqueDecks },
    { header: 'Games', align: 'right', sortValue: (p) => p.games, render: (p) => p.games },
  ]

  const streakColumns: Column<YearlyPlayerStreak>[] = [
    {
      header: 'Player',
      sortValue: (p) => p.name,
      render: (p) => (
        <Link to={`/players/${p.playerId}`} className="font-medium text-primary hover:underline">
          {p.name}
        </Link>
      ),
    },
    { header: 'Length', align: 'right', sortValue: (p) => p.length, render: (p) => p.length },
    { header: 'Start', align: 'right', sortValue: (p) => p.startDate ?? '', render: (p) => p.startDate ?? '—' },
    { header: 'End', align: 'right', sortValue: (p) => p.endDate ?? '', render: (p) => p.endDate ?? '—' },
  ]

  const mostPlayedColumns: Column<YearlyCommanderByMostPlayed>[] = [
    {
      header: 'Commander',
      sortValue: (c) => c.name,
      render: (c) => (
        <Link to={`/commanders/${c.commanderId}`} className="font-medium text-primary hover:underline">
          {c.name}
        </Link>
      ),
    },
    { header: 'Games', align: 'right', sortValue: (c) => c.games, render: (c) => c.games },
    { header: 'Players', align: 'right', sortValue: (c) => c.players, render: (c) => c.players },
    { header: 'Wins', align: 'right', sortValue: (c) => c.wins, render: (c) => c.wins },
  ]

  const mostWinsColumns: Column<YearlyCommanderByMostWins>[] = [
    {
      header: 'Commander',
      sortValue: (c) => c.name,
      render: (c) => (
        <Link to={`/commanders/${c.commanderId}`} className="font-medium text-primary hover:underline">
          {c.name}
        </Link>
      ),
    },
    { header: 'Wins', align: 'right', sortValue: (c) => c.wins, render: (c) => c.wins },
    { header: 'Win rate', align: 'right', sortValue: (c) => c.rate, render: (c) => `${c.rate}%` },
    { header: 'Games', align: 'right', sortValue: (c) => c.games, render: (c) => c.games },
  ]

  const speedColumns: Column<YearlyCommanderSpeed>[] = [
    {
      header: 'Commander',
      sortValue: (c) => c.name,
      render: (c) => (
        <Link to={`/commanders/${c.commanderId}`} className="font-medium text-primary hover:underline">
          {c.name}
        </Link>
      ),
    },
    { header: 'Wins sampled', align: 'right', sortValue: (c) => c.wins, render: (c) => c.wins },
    { header: 'Avg', align: 'right', sortValue: (c) => c.avg, render: (c) => c.avg },
    { header: 'Range', align: 'right', sortValue: (c) => c.min, render: (c) => `${c.min}–${c.max}` },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-primary">Yearly Report</h1>
        <div className="flex items-center gap-2">
          <button
            className="rounded-md border border-border px-3 py-1.5 text-sm text-secondary hover:bg-primary/5"
            onClick={() => setYear((y) => y - 1)}
          >
            ← {year - 1}
          </button>
          <span className="tabular-nums w-14 text-center text-lg font-semibold text-primary">{year}</span>
          <button
            className="rounded-md border border-border px-3 py-1.5 text-sm text-secondary hover:bg-primary/5"
            onClick={() => setYear((y) => y + 1)}
          >
            {year + 1} →
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} />
      ) : report ? (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <StatTile label="Total games" value={report.totalGames} />
            <StatTile label="Unique players" value={report.uniquePlayers} />
            <StatTile label="Unique commanders" value={report.uniqueCommanders} />
            <StatTile label="Avg minutes/game" value={report.avgMinutesPerGame ?? '—'} />
            <StatTile label="Avg turns/game" value={report.avgTurnsPerGame ?? '—'} />
          </div>

          <SectionCard title="Players by wins">
            <RankingBars data={report.playersByWins.map((p) => ({ label: p.name, value: p.wins }))} />
          </SectionCard>

          <div className="grid gap-6 lg:grid-cols-2">
            <SectionCard title="Players by win rate">
              <DataTable columns={winRateColumns} rows={report.playersByWinRate} rowKey={(p) => p.playerId} />
            </SectionCard>
            <SectionCard title="Players by games">
              <DataTable columns={gamesColumns} rows={report.playersByGames} rowKey={(p) => p.playerId} />
            </SectionCard>
            <SectionCard title="Players by unique decks">
              <DataTable columns={uniqueDeckColumns} rows={report.playersByUniqueDecks} rowKey={(p) => p.playerId} />
            </SectionCard>
            <SectionCard title="Players by win streak">
              <DataTable columns={streakColumns} rows={report.playersByWinStreak} rowKey={(p) => p.playerId} />
            </SectionCard>
            <SectionCard title="Players by loss streak">
              <DataTable columns={streakColumns} rows={report.playersByLossStreak} rowKey={(p) => p.playerId} />
            </SectionCard>
            <SectionCard title="Commanders by most played">
              <DataTable columns={mostPlayedColumns} rows={report.commandersByMostPlayed} rowKey={(c) => c.commanderId} />
            </SectionCard>
            <SectionCard title="Commanders by most wins">
              <DataTable columns={mostWinsColumns} rows={report.commandersByMostWins} rowKey={(c) => c.commanderId} />
            </SectionCard>
            <SectionCard title="Commanders fastest to win">
              <DataTable columns={speedColumns} rows={report.commandersFastestToWin} rowKey={(c) => c.commanderId} />
            </SectionCard>
            <SectionCard title="Commanders slowest to win">
              <DataTable columns={speedColumns} rows={report.commandersSlowestToWin} rowKey={(c) => c.commanderId} />
            </SectionCard>
          </div>
        </>
      ) : null}
    </div>
  )
}
