import { useEffect, useRef, useState } from 'react'
import { ExternalLink, Search } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ApiError, getCardFit, searchCards } from '../lib/api'
import type { CardFitResult, CardSummary } from '../lib/types'
import { LoadingState, ErrorState } from './AsyncState'
import { SectionCard } from './SectionCard'

function CardPicker({ onSelect }: { onSelect: (card: CardSummary) => void }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<CardSummary[]>([])
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open || query.trim().length < 2) {
      setResults([])
      return
    }
    let cancelled = false
    const timeout = setTimeout(() => {
      searchCards(query).then((cards) => {
        if (!cancelled) setResults(cards)
      })
    }, 200)
    return () => {
      cancelled = true
      clearTimeout(timeout)
    }
  }, [query, open])

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input
          type="text"
          placeholder="Search for a card…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          className="w-full rounded-md border border-border bg-surface py-2 pl-9 pr-3 text-sm text-primary outline-none focus:border-series-1"
        />
      </div>
      {open && results.length > 0 && (
        <ul className="absolute z-10 mt-1 max-h-64 w-full overflow-y-auto rounded-md border border-border bg-surface shadow-lg">
          {results.map((c) => (
            <li key={c.name}>
              <button
                type="button"
                className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-primary/5"
                onClick={() => {
                  onSelect(c)
                  setQuery(c.name)
                  setOpen(false)
                }}
              >
                <span className="text-primary">{c.name}</span>
                <span className="text-xs text-muted">{c.typeLine ?? ''}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function FitRow({ fit }: { fit: CardFitResult }) {
  return (
    <li className="flex items-center justify-between gap-3 py-2">
      <Link to={`/decks/${fit.deckId}`} className="min-w-0 flex-1 truncate text-sm font-medium text-primary hover:underline">
        {fit.deckName}
      </Link>
      <span className="tabular-nums shrink-0 text-sm text-muted">{fit.inclusionRate}%</span>
      <a
        href={fit.edhrecUrl}
        target="_blank"
        rel="noreferrer"
        className="flex shrink-0 items-center gap-1 rounded-md px-2 py-1 text-xs text-muted hover:bg-primary/5 hover:text-series-1"
      >
        <ExternalLink size={12} />
        EDHREC
      </a>
    </li>
  )
}

export function CardFitFinder({ playerId }: { playerId: string }) {
  const [selected, setSelected] = useState<CardSummary | null>(null)
  const [fits, setFits] = useState<CardFitResult[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSelect(card: CardSummary) {
    setSelected(card)
    setFits(null)
    setError(null)
    setLoading(true)
    try {
      setFits(await getCardFit(playerId, card.name))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to look up card fit.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SectionCard title="Card fit finder">
      <div className="flex flex-col gap-3">
        <CardPicker onSelect={handleSelect} />
        {!selected ? (
          <p className="py-6 text-center text-sm text-muted">
            Search a card to see which of your decks want it most, based on EDHREC inclusion rates.
          </p>
        ) : loading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState message={error} />
        ) : fits && fits.length > 0 ? (
          <ul className="flex flex-col divide-y divide-gridline">
            {fits.map((fit) => (
              <FitRow key={fit.deckId} fit={fit} />
            ))}
          </ul>
        ) : (
          <p className="py-6 text-center text-sm text-muted">
            No fit found — every deck already runs {selected.name}, or EDHREC has no data for it with your commanders.
          </p>
        )}
      </div>
    </SectionCard>
  )
}
