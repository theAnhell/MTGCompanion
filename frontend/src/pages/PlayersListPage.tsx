import { Link } from 'react-router-dom'
import { Star, User } from 'lucide-react'
import { listPlayers } from '../lib/api'
import { useApi } from '../lib/useApi'
import { LoadingState, ErrorState } from '../components/AsyncState'
import { SectionCard } from '../components/SectionCard'
import { DataTable, type Column } from '../components/DataTable'
import type { Player } from '../lib/types'

export function PlayersListPage() {
  const { data: players, loading, error } = useApi(listPlayers, [])

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />

  const columns: Column<Player>[] = [
    {
      header: 'Player',
      sortValue: (p) => p.name,
      render: (p) => (
        <Link to={`/players/${p.id}`} className="flex items-center gap-2 font-medium text-primary hover:underline">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: p.color ?? 'var(--text-muted)' }}
          />
          {p.name}
          {p.isYou && <User size={14} className="text-series-1" />}
          {p.favorite && <Star size={14} className="fill-series-4 text-series-4" />}
        </Link>
      ),
    },
    { header: 'Username', sortValue: (p) => p.username ?? '', render: (p) => p.username ?? '—' },
  ]

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-primary">Players</h1>
      <SectionCard title={`${players?.length ?? 0} players`}>
        <DataTable columns={columns} rows={players ?? []} rowKey={(p) => p.id} />
      </SectionCard>
    </div>
  )
}
