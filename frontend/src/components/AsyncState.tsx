import { Loader2, TriangleAlert } from 'lucide-react'

export function LoadingState() {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted">
      <Loader2 size={16} className="animate-spin" />
      Loading…
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center gap-2 rounded-lg border border-critical/20 bg-critical/5 py-10 text-sm text-critical">
      <TriangleAlert size={16} />
      {message}
    </div>
  )
}
