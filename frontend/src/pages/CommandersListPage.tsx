import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ExternalLink, RefreshCw, Search } from 'lucide-react'
import { ApiError, getCardSyncStatus, listCommanders, syncCards } from '../lib/api'
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
  {
    header: 'EDHREC',
    align: 'right',
    render: (c) => (
      <a
        href={c.edhrecUrl}
        target="_blank"
        rel="noreferrer"
        onClick={(e) => e.stopPropagation()}
        className="inline-flex items-center gap-1 text-series-1 hover:underline"
      >
        View <ExternalLink size={12} />
      </a>
    ),
  },
]

function fmtSyncedAt(d: string | null) {
  if (!d) return 'never synced'
  return `synced ${new Date(d).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}`
}

function BulkDataRefresh() {
  const [refreshKey, setRefreshKey] = useState(0)
  const { data: status } = useApi(() => getCardSyncStatus(), [refreshKey])
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSync() {
    setSyncing(true)
    setError(null)
    try {
      await syncCards()
      setRefreshKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Sync failed.')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={handleSync}
        disabled={syncing}
        className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm text-secondary hover:bg-primary/5 disabled:opacity-50"
      >
        <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
        {syncing ? 'Syncing… (can take a minute)' : 'Refresh bulk data'}
      </button>
      {error ? (
        <span className="text-xs text-critical">{error}</span>
      ) : status ? (
        <span className="text-xs text-muted">
          {status.cardCount.toLocaleString()} cards · {fmtSyncedAt(status.syncedAt)}
        </span>
      ) : null}
    </div>
  )
}

export function CommandersListPage() {
  const [search, setSearch] = useState('')
  const { data: commanders, loading, error } = useApi(() => listCommanders(search || undefined), [search])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h1 className="text-2xl font-semibold text-primary">Commanders</h1>
        <BulkDataRefresh />
      </div>
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
