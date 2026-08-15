import clsx from 'clsx'
import type { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  tone?: 'neutral' | 'good' | 'critical'
}

const toneClass: Record<NonNullable<BadgeProps['tone']>, string> = {
  neutral: 'bg-primary/5 text-secondary',
  good: 'bg-good/10 text-good',
  critical: 'bg-critical/10 text-critical',
}

export function Badge({ children, tone = 'neutral' }: BadgeProps) {
  return (
    <span className={clsx('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium', toneClass[tone])}>
      {children}
    </span>
  )
}
