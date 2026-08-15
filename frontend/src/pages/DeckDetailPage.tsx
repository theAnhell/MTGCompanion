import { useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { RefreshCw, Trash2 } from 'lucide-react'
import { ApiError, deleteDeck, getDeck, replaceDeckCards } from '../lib/api'
import { useApi } from '../lib/useApi'
import { LoadingState, ErrorState } from '../components/AsyncState'
import { SectionCard } from '../components/SectionCard'
import { StatTile } from '../components/StatTile'
import { Badge } from '../components/Badge'
import { DataTable, type Column } from '../components/DataTable'
import type { OwnedDeckCard } from '../lib/types'

const cardColumns: Column<OwnedDeckCard>[] = [
  {
    header: 'Card',
    sortValue: (c) => c.cardName,
    render: (c) => (
      <span className="flex items-center gap-2 font-medium text-primary">
        {c.cardName}
        {c.isCommander && <Badge tone="good">Commander</Badge>}
        {c.isFoil && <Badge>Foil</Badge>}
      </span>
    ),
  },
  { header: 'Qty', align: 'right', sortValue: (c) => c.quantity, render: (c) => c.quantity },
  { header: 'Set', sortValue: (c) => c.setCode ?? '', render: (c) => c.setCode ?? '—' },
  { header: '#', sortValue: (c) => c.collectorNumber ?? '', render: (c) => c.collectorNumber ?? '—' },
]

export function DeckDetailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const [refreshKey, setRefreshKey] = useState(0)
  const { data: deck, loading, error } = useApi(() => getDeck(id), [id, refreshKey])
  const [reimporting, setReimporting] = useState(false)
  const [exportText, setExportText] = useState('')
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />
  if (!deck) return null

  async function handleReimport(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setActionError(null)
    try {
      await replaceDeckCards(id, exportText)
      setReimporting(false)
      setExportText('')
      setRefreshKey((k) => k + 1)
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'Re-import failed.')
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete() {
    if (!confirm('Delete this deck? This removes its decklist permanently.')) return
    await deleteDeck(id)
    navigate(`/players/${deck!.ownerId}`)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-primary">{deck.name || deck.commanderName}</h1>
          <p className="text-sm text-muted">
            {deck.commanderName} · owned by{' '}
            <Link to={`/players/${deck.ownerId}`} className="hover:underline">
              {deck.ownerName}
            </Link>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setReimporting((v) => !v)}
            className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm text-secondary hover:bg-primary/5"
          >
            <RefreshCw size={14} />
            Re-import
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className="flex items-center gap-1.5 rounded-md border border-critical/30 px-3 py-1.5 text-sm text-critical hover:bg-critical/5"
          >
            <Trash2 size={14} />
            Delete
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <StatTile label="Cards" value={deck.cardCount} />
        <StatTile label="Source" value={deck.source} />
        {deck.moxfieldUrl && (
          <div className="flex items-center rounded-lg border border-border bg-surface px-4 py-3">
            <a href={deck.moxfieldUrl} target="_blank" rel="noreferrer" className="text-sm text-series-1 hover:underline">
              View on Moxfield ↗
            </a>
          </div>
        )}
      </div>

      {reimporting && (
        <SectionCard title="Re-import decklist">
          <form onSubmit={handleReimport} className="flex flex-col gap-3">
            <p className="text-sm text-muted">
              Pasting a new export fully replaces this deck's current card list.
            </p>
            <textarea
              value={exportText}
              onChange={(e) => setExportText(e.target.value)}
              rows={8}
              placeholder={'1 Sol Ring (LEA) 226\n1 Command Tower (CMR) 331\n…'}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 font-mono text-xs text-primary outline-none focus:border-series-1"
            />
            {actionError && <p className="text-sm text-critical">{actionError}</p>}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setReimporting(false)}
                className="rounded-md border border-border px-3 py-1.5 text-sm text-secondary hover:bg-primary/5"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={busy}
                className="rounded-md bg-series-1 px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
              >
                {busy ? 'Saving…' : 'Replace cards'}
              </button>
            </div>
          </form>
        </SectionCard>
      )}

      <SectionCard title={`${deck.cardCount} cards`}>
        <DataTable columns={cardColumns} rows={deck.cards} rowKey={(c) => `${c.cardName}-${c.setCode}-${c.collectorNumber}`} />
      </SectionCard>
    </div>
  )
}
