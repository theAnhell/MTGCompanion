interface RankingBarsProps {
  data: { label: string; value: number }[]
  valueFormatter?: (value: number) => string
}

export function RankingBars({ data, valueFormatter = String }: RankingBarsProps) {
  if (data.length === 0) {
    return <p className="py-6 text-center text-sm text-muted">No data yet.</p>
  }

  const max = Math.max(...data.map((d) => d.value), 1)

  return (
    <div className="flex flex-col gap-2.5">
      {data.map((d) => (
        <div key={d.label} className="flex items-center gap-3">
          <div className="w-32 shrink-0 truncate text-sm text-secondary" title={d.label}>
            {d.label}
          </div>
          <div className="flex min-w-0 flex-1 items-center gap-2">
            <div className="h-4 min-w-1 rounded-r bg-series-1" style={{ width: `${(d.value / max) * 100}%` }} />
            <span className="tabular-nums shrink-0 text-sm text-primary">{valueFormatter(d.value)}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
