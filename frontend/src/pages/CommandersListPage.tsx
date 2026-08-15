import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import { listCommanders } from '../lib/api'
import { useApi } from '../lib/useApi'
import { LoadingState, ErrorState } from '../components/AsyncState'
import { SectionCard } from '../components/SectionCard'
import { DataTable, type Column } from '../components/DataTable'
import type { Commander } from '../lib/types'

const columns: Column<Commander>[] = [
  {
    header: 'Commander',
    sortValue: (c) => c.name,
    render: (c) => (
      <Link to={`/commanders/${c.id}`} className="font-medium text-primary hover:underline">
        {c.name}
      </Link>
    ),
  },
  { header: 'Colors', sortValue: (c) => c.colors?.join('') ?? '', render: (c) => c.colors?.join('') ?? '—' },
  { header: 'CMC', align: 'right', sortValue: (c) => c.cmc ?? -1, render: (c) => c.cmc ?? '—' },
  {
    header: 'EDHREC rank',
    align: 'right',
    sortValue: (c) => c.edhrecRank ?? Number.MAX_SAFE_INTEGER,
    render: (c) => c.edhrecRank ?? '—',
  },
]

export function CommandersListPage() {
  const [search, setSearch] = useState('')
  const { data: commanders, loading, error } = useApi(() => listCommanders(search || undefined), [search])

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-primary">Commanders</h1>
      <div className="relative max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input
          type="text"
          placeholder="Search commanders…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-md border border-border bg-surface py-2 pl-9 pr-3 text-sm text-primary outline-none focus:border-series-1"
        />
      </div>
      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} />
      ) : (
        <SectionCard title={`${commanders?.length ?? 0} commanders`}>
          <DataTable columns={columns} rows={commanders ?? []} rowKey={(c) => c.id} />
        </SectionCard>
      )}
    </div>
  )
}
