import { useEffect, useRef, useState } from 'react'
import { Search } from 'lucide-react'
import { listCommanders } from '../lib/api'
import type { Commander } from '../lib/types'

interface CommanderPickerProps {
  value: Commander | null
  onChange: (commander: Commander | null) => void
}

export function CommanderPicker({ value, onChange }: CommanderPickerProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Commander[]>([])
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open || query.trim().length < 2) {
      setResults([])
      return
    }
    let cancelled = false
    const timeout = setTimeout(() => {
      listCommanders(query).then((commanders) => {
        if (!cancelled) setResults(commanders.slice(0, 20))
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
          placeholder="Search for a commander…"
          value={value ? value.name : query}
          onChange={(e) => {
            onChange(null)
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
            <li key={c.id}>
              <button
                type="button"
                className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-primary/5"
                onClick={() => {
                  onChange(c)
                  setQuery('')
                  setOpen(false)
                }}
              >
                <span className="text-primary">{c.name}</span>
                <span className="text-xs text-muted">{c.colors?.join('') ?? ''}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
