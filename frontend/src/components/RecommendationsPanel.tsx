import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, CheckCheck, RotateCcw, Sparkles, X } from 'lucide-react'
import { ApiError, generateRecommendations, getRecommendations, updateRecommendation } from '../lib/api'
import { useApi } from '../lib/useApi'
import { LoadingState, ErrorState } from './AsyncState'
import { SectionCard } from './SectionCard'
import { Badge } from './Badge'
import type { Recommendation } from '../lib/types'

function RecommendationRow({ rec, onChange }: { rec: Recommendation; onChange: (r: Recommendation) => void }) {
  const [busy, setBusy] = useState(false)

  async function apply(update: { status?: Recommendation['status']; applied?: boolean }) {
    setBusy(true)
    try {
      onChange(await updateRecommendation(rec.id, update))
    } finally {
      setBusy(false)
    }
  }

  const iconButtonClass = 'rounded-md p-1.5 text-muted hover:bg-primary/5 hover:text-primary disabled:opacity-40'

  return (
    <li className="flex items-center justify-between gap-3 py-2">
      <div className="flex min-w-0 items-center gap-2 text-sm">
        <span className="truncate font-medium text-primary">{rec.cardName}</span>
        <span className="tabular-nums shrink-0 text-muted">{rec.inclusionRate}%</span>
        {rec.role && <Badge tone="good">{rec.role[0].toUpperCase() + rec.role.slice(1)}</Badge>}
        {rec.sourceType === 'binder' && <Badge>Binder</Badge>}
        {rec.sourceType === 'deck' && rec.sourceDeckId && (
          <Link
            to={`/decks/${rec.sourceDeckId}`}
            className="truncate text-xs text-muted hover:text-series-1 hover:underline"
          >
            from {rec.sourceDeckName}
          </Link>
        )}
        {rec.appliedAt ? (
          <Badge tone="good">Made</Badge>
        ) : rec.status === 'approved' ? (
          <Badge tone="good">Approved</Badge>
        ) : rec.status === 'ignored' ? (
          <Badge>Ignored</Badge>
        ) : null}
      </div>
      <div className="flex shrink-0 items-center gap-0.5">
        {rec.status === 'proposed' && (
          <>
            <button
              type="button"
              disabled={busy}
              onClick={() => apply({ status: 'approved' })}
              className={iconButtonClass}
              aria-label="Approve"
              title="Approve"
            >
              <Check size={14} />
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => apply({ status: 'ignored' })}
              className={iconButtonClass}
              aria-label="Ignore"
              title="Ignore"
            >
              <X size={14} />
            </button>
          </>
        )}
        {rec.status === 'approved' && !rec.appliedAt && (
          <>
            <button
              type="button"
              disabled={busy}
              onClick={() => apply({ applied: true })}
              className={iconButtonClass}
              aria-label="Mark as made"
              title="Mark as made"
            >
              <CheckCheck size={14} />
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => apply({ status: 'ignored' })}
              className={iconButtonClass}
              aria-label="Ignore"
              title="Ignore"
            >
              <X size={14} />
            </button>
          </>
        )}
        {(rec.status === 'ignored' || rec.appliedAt) && (
          <button
            type="button"
            disabled={busy}
            onClick={() => apply(rec.appliedAt ? { applied: false } : { status: 'proposed' })}
            className={iconButtonClass}
            aria-label="Reconsider"
            title="Reconsider"
          >
            <RotateCcw size={14} />
          </button>
        )}
      </div>
    </li>
  )
}

function RecommendationList({
  recs,
  onChange,
  emptyMessage,
}: {
  recs: Recommendation[]
  onChange: (r: Recommendation) => void
  emptyMessage: string
}) {
  if (recs.length === 0) {
    return <p className="py-4 text-sm text-muted">{emptyMessage}</p>
  }
  return (
    <ul className="flex flex-col divide-y divide-gridline">
      {recs.map((rec) => (
        <RecommendationRow key={rec.id} rec={rec} onChange={onChange} />
      ))}
    </ul>
  )
}

export function RecommendationsPanel({ deckId }: { deckId: string }) {
  const { data: fetched, loading, error } = useApi(() => getRecommendations(deckId), [deckId])
  const [recs, setRecs] = useState<Recommendation[] | null>(null)
  const [generating, setGenerating] = useState(false)
  const [genError, setGenError] = useState<string | null>(null)

  useEffect(() => {
    if (fetched) setRecs(fetched)
  }, [fetched])

  async function handleGenerate() {
    setGenerating(true)
    setGenError(null)
    try {
      setRecs(await generateRecommendations(deckId))
    } catch (err) {
      setGenError(err instanceof ApiError ? err.message : 'Failed to generate recommendations.')
    } finally {
      setGenerating(false)
    }
  }

  function handleRowChange(updated: Recommendation) {
    setRecs((prev) => (prev ?? []).map((r) => (r.id === updated.id ? updated : r)))
  }

  const list = recs ?? []
  const adds = list.filter((r) => r.action === 'add')
  const removes = list.filter((r) => r.action === 'remove')

  return (
    <SectionCard
      title="Recommendations"
      action={
        <button
          type="button"
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-secondary hover:bg-primary/5 disabled:opacity-50"
        >
          <Sparkles size={14} />
          {generating ? 'Generating…' : list.length > 0 ? 'Refresh' : 'Generate'}
        </button>
      }
    >
      {genError && <p className="mb-3 text-sm text-critical">{genError}</p>}
      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} />
      ) : list.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted">
          No recommendations yet — click Generate to compare this deck against your binder and other decks.
        </p>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">
              From your collection ({adds.length})
            </h3>
            <RecommendationList recs={adds} onChange={handleRowChange} emptyMessage="No add suggestions." />
          </div>
          <div>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">
              Low inclusion ({removes.length})
            </h3>
            <RecommendationList recs={removes} onChange={handleRowChange} emptyMessage="No cut suggestions." />
          </div>
        </div>
      )}
    </SectionCard>
  )
}
