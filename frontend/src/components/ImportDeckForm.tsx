import { useState } from 'react'
import { createDeck, ApiError } from '../lib/api'
import { CommanderPicker } from './CommanderPicker'
import type { Commander, OwnedDeckDetail } from '../lib/types'

interface ImportDeckFormProps {
  ownerId: string
  onImported: (deck: OwnedDeckDetail) => void
  onCancel: () => void
}

export function ImportDeckForm({ ownerId, onImported, onCancel }: ImportDeckFormProps) {
  const [commander, setCommander] = useState<Commander | null>(null)
  const [exportText, setExportText] = useState('')
  const [moxfieldUrl, setMoxfieldUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!commander) {
      setError('Pick a commander first.')
      return
    }
    if (!exportText.trim()) {
      setError('Paste a Moxfield plain-text export.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const deck = await createDeck({
        ownerId,
        commanderId: commander.id,
        exportText,
        moxfieldUrl: moxfieldUrl.trim() || undefined,
      })
      onImported(deck)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Import failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-4">
      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-muted">Commander</label>
        <CommanderPicker value={commander} onChange={setCommander} />
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-muted">
          Moxfield URL (optional)
        </label>
        <input
          type="text"
          value={moxfieldUrl}
          onChange={(e) => setMoxfieldUrl(e.target.value)}
          placeholder="https://moxfield.com/decks/…"
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary outline-none focus:border-series-1"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-muted">
          Moxfield plain-text export
        </label>
        <textarea
          value={exportText}
          onChange={(e) => setExportText(e.target.value)}
          rows={8}
          placeholder={'1 Sol Ring (LEA) 226\n1 Command Tower (CMR) 331\n…'}
          className="w-full rounded-md border border-border bg-surface px-3 py-2 font-mono text-xs text-primary outline-none focus:border-series-1"
        />
      </div>
      {error && <p className="text-sm text-critical">{error}</p>}
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-border px-3 py-1.5 text-sm text-secondary hover:bg-primary/5"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-series-1 px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {submitting ? 'Importing…' : 'Import deck'}
        </button>
      </div>
    </form>
  )
}
