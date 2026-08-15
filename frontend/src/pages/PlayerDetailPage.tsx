import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ExternalLink, Layers, Plus, Trash2 } from 'lucide-react'
import { deleteDeck, getPlayer, getPlayerSummary, listPlayerDecks } from '../lib/api'
import { useApi } from '../lib/useApi'
import { LoadingState, ErrorState } from '../components/AsyncState'
import { SectionCard } from '../components/SectionCard'
import { StatTile } from '../components/StatTile'
import { Badge } from '../components/Badge'
import { DataTable, type Column } from '../components/DataTable'
import { ImportDeckForm } from '../components/ImportDeckForm'
import type { DeckStat, SpeedDeckStat } from '../lib/types'

function fmtDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

const deckColumns: Column<DeckStat>[] = [
  {
    header: 'Commander',
    sortValue: (d) => d.commanderName,
    render: (d) => (
      <span className="flex items-center gap-2 font-medium text-primary">
        {d.commanderName}
        {d.retired && <Badge tone="critical">Retired</Badge>}
      </span>
    ),
  },
  { header: 'Games', align: 'right', sortValue: (d) => d.gamesPlayed, render: (d) => d.gamesPlayed },
  { header: 'Wins', align: 'right', sortValue: (d) => d.wins, render: (d) => d.wins },
  { header: 'Win rate', align: 'right', sortValue: (d) => d.winRate, render: (d) => `${d.winRate}%` },
  {
    header: 'Last played',
    align: 'right',
    sortValue: (d) => d.lastPlayed ?? '',
    render: (d) => fmtDate(d.lastPlayed),
  },
]

function speedColumns(unit: string): Column<SpeedDeckStat>[] {
  return [
    {
      header: 'Commander',
      sortValue: (d) => d.commanderName,
      render: (d) => <span className="font-medium text-primary">{d.commanderName}</span>,
    },
    { header: 'Wins sampled', align: 'right', sortValue: (d) => d.wins, render: (d) => d.wins },
    { header: `Avg (${unit})`, align: 'right', sortValue: (d) => d.avg, render: (d) => d.avg },
    { header: 'Range', align: 'right', sortValue: (d) => d.min, render: (d) => `${d.min}–${d.max}` },
  ]
}

export function PlayerDetailPage() {
  const { id = '' } = useParams()
  const player = useApi(() => getPlayer(id), [id])
  const summary = useApi(() => getPlayerSummary(id), [id])
  const [ownedDecksKey, setOwnedDecksKey] = useState(0)
  const ownedDecks = useApi(() => listPlayerDecks(id), [id, ownedDecksKey])
  const [showImportForm, setShowImportForm] = useState(false)

  if (player.loading || summary.loading) return <LoadingState />
  if (player.error) return <ErrorState message={player.error} />
  if (summary.error) return <ErrorState message={summary.error} />
  if (!player.data || !summary.data) return null

  const { decks, leastPlayed, longestSincePlayed, fastestToWin, slowestToWin, streaks } = summary.data
  const totalGames = decks.reduce((sum, d) => sum + d.gamesPlayed, 0)
  const totalWins = decks.reduce((sum, d) => sum + d.wins, 0)
  const winRate = totalGames ? Math.round((totalWins / totalGames) * 1000) / 10 : 0

  async function handleDeleteDeck(deckId: string) {
    if (!confirm('Delete this deck? This removes its decklist permanently.')) return
    await deleteDeck(deckId)
    setOwnedDecksKey((k) => k + 1)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <span
          className="inline-block h-4 w-4 rounded-full"
          style={{ backgroundColor: player.data.color ?? 'var(--text-muted)' }}
        />
        <h1 className="text-2xl font-semibold text-primary">{player.data.name}</h1>
        {player.data.favorite && <Badge tone="good">Favorite</Badge>}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Decks played" value={decks.length} />
        <StatTile label="Total games" value={totalGames} />
        <StatTile label="Win rate" value={`${winRate}%`} sublabel={`${totalWins} wins`} />
        <StatTile
          label="Best win streak"
          value={streaks.longestWinStreak.length}
          sublabel={streaks.longestWinStreak.startDate ? fmtDate(streaks.longestWinStreak.startDate) : undefined}
        />
      </div>

      <SectionCard
        title="Owned decks"
        action={
          <div className="flex items-center gap-2">
            <Link
              to={`/players/${id}/binder`}
              className="flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-secondary hover:bg-primary/5"
            >
              <Layers size={14} />
              Binder
            </Link>
            {!showImportForm && (
              <button
                type="button"
                onClick={() => setShowImportForm(true)}
                className="flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-secondary hover:bg-primary/5"
              >
                <Plus size={14} />
                Import deck
              </button>
            )}
          </div>
        }
      >
        {showImportForm && (
          <div className="mb-4">
            <ImportDeckForm
              ownerId={id}
              onCancel={() => setShowImportForm(false)}
              onImported={() => {
                setShowImportForm(false)
                setOwnedDecksKey((k) => k + 1)
              }}
            />
          </div>
        )}
        {ownedDecks.loading ? (
          <LoadingState />
        ) : ownedDecks.error ? (
          <ErrorState message={ownedDecks.error} />
        ) : ownedDecks.data && ownedDecks.data.length > 0 ? (
          <ul className="flex flex-col divide-y divide-gridline">
            {ownedDecks.data.map((deck) => (
              <li key={deck.id} className="flex items-center justify-between gap-3 py-2.5">
                <Link to={`/decks/${deck.id}`} className="flex flex-1 items-center gap-3 text-sm hover:underline">
                  <span className="font-medium text-primary">{deck.name || deck.commanderName}</span>
                  <span className="text-muted">{deck.cardCount} cards</span>
                  {deck.source === 'moxfield' && <Badge>Moxfield</Badge>}
                </Link>
                <a
                  href={deck.edhrecUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted hover:bg-primary/5 hover:text-series-1"
                >
                  <ExternalLink size={12} />
                  EDHREC
                </a>
                <button
                  type="button"
                  onClick={() => handleDeleteDeck(deck.id)}
                  className="rounded-md p-1.5 text-muted hover:bg-critical/10 hover:text-critical"
                  aria-label="Delete deck"
                >
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
          </ul>
        ) : (
          !showImportForm && <p className="py-6 text-center text-sm text-muted">No owned decks yet.</p>
        )}
      </SectionCard>

      <SectionCard title="Commander stats">
        <DataTable columns={deckColumns} rows={decks} rowKey={(d) => d.commanderId} />
      </SectionCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Least played">
          <DataTable columns={deckColumns} rows={leastPlayed} rowKey={(d) => d.commanderId} />
        </SectionCard>
        <SectionCard title="Longest since played">
          <DataTable columns={deckColumns} rows={longestSincePlayed} rowKey={(d) => d.commanderId} />
        </SectionCard>
        <SectionCard title="Fastest to win">
          <DataTable columns={speedColumns(fastestToWin[0]?.unit ?? 'minutes')} rows={fastestToWin} rowKey={(d) => d.commanderId} />
        </SectionCard>
        <SectionCard title="Slowest to win">
          <DataTable columns={speedColumns(slowestToWin[0]?.unit ?? 'minutes')} rows={slowestToWin} rowKey={(d) => d.commanderId} />
        </SectionCard>
      </div>

      <p className="text-sm text-muted">
        <Link to="/players" className="hover:underline">
          ← Back to players
        </Link>
      </p>
    </div>
  )
}
