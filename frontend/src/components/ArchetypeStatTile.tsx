import { Check, TriangleAlert } from 'lucide-react'
import type { ArchetypeRoleStat } from '../lib/types'

interface ArchetypeStatTileProps {
  label: string
  stat: ArchetypeRoleStat
}

export function ArchetypeStatTile({ label, stat }: ArchetypeStatTileProps) {
  return (
    <div className="rounded-lg border border-border bg-surface px-4 py-3">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="tabular-nums mt-1 flex items-baseline gap-1.5 text-2xl font-semibold text-primary">
        {stat.count}
        <span className="text-sm font-normal text-muted">/ {stat.target}</span>
      </div>
      <div className={`mt-0.5 flex items-center gap-1 text-xs ${stat.met ? 'text-good' : 'text-warning'}`}>
        {stat.met ? <Check size={12} /> : <TriangleAlert size={12} />}
        {stat.met ? 'Target met' : `${stat.target - stat.count} short`}
      </div>
    </div>
  )
}
