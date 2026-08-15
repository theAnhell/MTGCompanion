import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { ChevronDown, ChevronUp, ChevronsUpDown } from 'lucide-react'
import clsx from 'clsx'

export interface Column<T> {
  header: string
  align?: 'left' | 'right'
  render: (row: T) => ReactNode
  sortValue?: (row: T) => string | number
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string
  emptyMessage?: string
}

type SortDirection = 'asc' | 'desc'

export function DataTable<T>({ columns, rows, rowKey, emptyMessage = 'No data yet.' }: DataTableProps<T>) {
  const [sort, setSort] = useState<{ header: string; direction: SortDirection } | null>(null)

  const sortedRows = useMemo(() => {
    if (!sort) return rows
    const col = columns.find((c) => c.header === sort.header)
    if (!col?.sortValue) return rows
    const { sortValue } = col
    const dir = sort.direction === 'asc' ? 1 : -1
    return [...rows].sort((a, b) => {
      const av = sortValue(a)
      const bv = sortValue(b)
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
      return String(av).localeCompare(String(bv)) * dir
    })
  }, [rows, sort, columns])

  if (rows.length === 0) {
    return <p className="py-6 text-center text-sm text-muted">{emptyMessage}</p>
  }

  function toggleSort(header: string) {
    setSort((prev) => {
      if (prev?.header !== header) return { header, direction: 'desc' }
      return { header, direction: prev.direction === 'desc' ? 'asc' : 'desc' }
    })
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-gridline text-xs uppercase tracking-wide text-muted">
            {columns.map((col) => {
              const active = sort?.header === col.header
              return (
                <th
                  key={col.header}
                  className={`px-2 py-2 font-medium ${col.align === 'right' ? 'text-right' : 'text-left'}`}
                >
                  {col.sortValue ? (
                    <button
                      type="button"
                      onClick={() => toggleSort(col.header)}
                      className={clsx(
                        'inline-flex items-center gap-1 hover:text-primary',
                        col.align === 'right' && 'flex-row-reverse',
                        active && 'text-primary',
                      )}
                    >
                      {col.header}
                      {active ? (
                        sort?.direction === 'asc' ? (
                          <ChevronUp size={12} />
                        ) : (
                          <ChevronDown size={12} />
                        )
                      ) : (
                        <ChevronsUpDown size={12} className="opacity-40" />
                      )}
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row) => (
            <tr key={rowKey(row)} className="border-b border-gridline last:border-0 hover:bg-primary/[0.03]">
              {columns.map((col) => (
                <td
                  key={col.header}
                  className={`px-2 py-2.5 text-secondary ${col.align === 'right' ? 'text-right tabular-nums' : 'text-left'}`}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
