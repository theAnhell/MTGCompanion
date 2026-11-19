import { useMemo, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Upload } from 'lucide-react'
import { ApiError, getBinder, getBinderFits, getPlayer, replaceBinder } from '../lib/api'
import { useApi } from '../lib/useApi'
import { LoadingState, ErrorState } from '../components/AsyncState'
import { SectionCard } from '../components/SectionCard'
import { StatTile } from '../components/StatTile'
import { DataTable, type Column } from '../components/DataTable'
import { CardHoverName } from '../components/CardHoverName'
import type { BinderCard, BinderCardFit } from '../lib/types'

function buildColumns(fitsByCard: Map<string, BinderCardFit>): Column<BinderCard>[] {
  return [
    {
      header: 'Card',
      sortValue: (c) => c.cardName,
      render: (c) => (
        <span className="font-medium text-primary">
          <CardHoverName name={c.cardName} scryfallId={c.scryfallId} />
        </span>
      ),
    },
    { header: 'Qty', align: 'right', sortValue: (c) => c.quantity, render: (c) => c.quantity },
    { header: 'Set', sortValue: (c) => c.setCode ?? '', render: (c) => c.setCode ?? '—' },
    { header: '#', sortValue: (c) => c.collectorNumber ?? '', render: (c) => c.collectorNumber ?? '—' },
    { header: 'Foil', sortValue: (c) => (c.isFoil ? 1 : 0), render: (c) => (c.isFoil ? 'Yes' : '') },
    {
      header: 'Deck fit',
      sortValue: (c) => fitsByCard.get(c.cardName)?.deckName ?? '',
      render: (c) => {
        const fit = fitsByCard.get(c.cardName)
        if (!fit) return '—'
        return (
          <Link to={`/decks/${fit.deckId}`} className="text-series-1 hover:underline">
            {fit.deckName}
          </Link>
        )
      },
    },
    {
      header: 'Inclusion',
      align: 'right',
      sortValue: (c) => fitsByCard.get(c.cardName)?.inclusionRate ?? -1,
      render: (c) => {
        const fit = fitsByCard.get(c.cardName)
        return fit ? `${fit.inclusionRate}%` : '—'
      },
    },
  ]
}

export function BinderPage() {
  const { id = '' } = useParams()
  const player = useApi(() => getPlayer(id), [id])
  const [refreshKey, setRefreshKey] = useState(0)
  const binder = useApi(() => getBinder(id), [id, refreshKey])
  const binderFits = useApi(() => getBinderFits(id), [id, refreshKey])
  const [onlyWithFit, setOnlyWithFit] = useState(false)
  const [importing, setImporting] = useState(false)
  const [exportText, setExportText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fitsByCard = useMemo(() => {
    const map = new Map<string, BinderCardFit>()
    for (const fit of binderFits.data ?? []) map.set(fit.cardName, fit)
    return map
  }, [binderFits.data])

  const visibleCards = onlyWithFit ? (binder.data ?? []).filter((c) => fitsByCard.has(c.cardName)) : binder.data ?? []

  async function handleImport(e: React.FormEvent) {
    e.preventDefault()
    if (!exportText.trim()) {
      setError('Paste a Moxfield plain-text export.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await replaceBinder(id, exportText)
      setImporting(false)
      setExportText('')
      setRefreshKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Import failed.')
    } finally {
      setBusy(false)
    }
  }

  if (player.loading) return <LoadingState />
  if (player.error) return <ErrorState message={player.error} />
  if (!player.data) return null

  const totalQuantity = binder.data?.reduce((sum, c) => sum + c.quantity, 0) ?? 0
  const fitCount = fitsByCard.size

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-primary">{player.data.name}'s Binder</h1>
          <p className="text-sm text-muted">Loose cards owned outside of any deck.</p>
        </div>
        {!importing && (
          <button
            type="button"
            onClick={() => setImporting(true)}
            className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm text-secondary hover:bg-primary/5"
          >
            <Upload size={14} />
            Import binder
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <StatTile label="Unique cards" value={binder.data?.length ?? 0} />
        <StatTile label="Total cards" value={totalQuantity} />
        <StatTile label="With a deck fit" value={fitCount} sublabel="per EDHREC inclusion" />
      </div>

      {importing && (
        <SectionCard title="Import binder">
          <form onSubmit={handleImport} className="flex flex-col gap-3">
            <p className="text-sm text-muted">
              Pasting a new export fully replaces the current binder — it's a snapshot, not a diff.
            </p>
            <textarea
              value={exportText}
              onChange={(e) => setExportText(e.target.value)}
              rows={10}
              placeholder={'1 Sol Ring (LEA) 226\n1 Command Tower (CMR) 331\n…'}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 font-mono text-xs text-primary outline-none focus:border-series-1"
            />
            {error && <p className="text-sm text-critical">{error}</p>}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setImporting(false)}
                className="rounded-md border border-border px-3 py-1.5 text-sm text-secondary hover:bg-primary/5"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={busy}
                className="rounded-md bg-series-1 px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
              >
                {busy ? 'Saving…' : 'Replace binder'}
              </button>
            </div>
          </form>
        </SectionCard>
      )}

      {binder.loading ? (
        <LoadingState />
      ) : binder.error ? (
        <ErrorState message={binder.error} />
      ) : (
        <SectionCard
          title={`${visibleCards.length} cards`}
          action={
            <label className="flex items-center gap-1.5 text-xs text-secondary">
              <input
                type="checkbox"
                checked={onlyWithFit}
                onChange={(e) => setOnlyWithFit(e.target.checked)}
                className="accent-series-1"
              />
              Only cards with a deck fit
            </label>
          }
        >
          <DataTable
            columns={buildColumns(fitsByCard)}
            rows={visibleCards}
            rowKey={(c) => `${c.cardName}-${c.setCode}-${c.collectorNumber}`}
            emptyMessage="No binder cards yet — import one to get started."
          />
        </SectionCard>
      )}

      <p className="text-sm text-muted">
        <Link to={`/players/${id}`} className="hover:underline">
          ← Back to {player.data.name}
        </Link>
      </p>
    </div>
  )
}
