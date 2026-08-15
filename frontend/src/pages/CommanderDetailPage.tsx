import { useParams, Link } from 'react-router-dom'
import { getCommander } from '../lib/api'
import { useApi } from '../lib/useApi'
import { LoadingState, ErrorState } from '../components/AsyncState'
import { StatTile } from '../components/StatTile'

export function CommanderDetailPage() {
  const { id = '' } = useParams()
  const { data: commander, loading, error } = useApi(() => getCommander(id), [id])

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />
  if (!commander) return null

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-6 sm:flex-row">
        {commander.imageUri && (
          <img
            src={commander.imageUri}
            alt={commander.name}
            className="h-64 w-auto self-start rounded-lg border border-border object-cover"
          />
        )}
        <div className="flex flex-col gap-3">
          <h1 className="text-2xl font-semibold text-primary">{commander.name}</h1>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <StatTile label="Colors" value={commander.colors?.join('') || '—'} />
            <StatTile label="CMC" value={commander.cmc ?? '—'} />
            <StatTile label="EDHREC rank" value={commander.edhrecRank ?? '—'} />
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {commander.decklistUrl && (
              <a
                href={commander.decklistUrl}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-series-1 hover:underline"
              >
                {commander.deckName ?? 'View decklist'} ↗
              </a>
            )}
            <a href={commander.edhrecUrl} target="_blank" rel="noreferrer" className="text-sm text-series-1 hover:underline">
              View on EDHREC ↗
            </a>
          </div>
        </div>
      </div>

      <p className="text-sm text-muted">
        <Link to="/commanders" className="hover:underline">
          ← Back to commanders
        </Link>
      </p>
    </div>
  )
}
