import { NavLink, Outlet } from 'react-router-dom'
import { Swords } from 'lucide-react'
import clsx from 'clsx'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  clsx(
    'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
    isActive
      ? 'bg-series-1/10 text-series-1'
      : 'text-secondary hover:text-primary hover:bg-primary/5',
  )

export function Layout() {
  return (
    <div className="min-h-svh bg-plane">
      <header className="sticky top-0 z-10 border-b border-border bg-surface/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3 sm:px-6">
          <NavLink to="/players" className="flex items-center gap-2 text-primary">
            <Swords size={20} className="text-series-1" strokeWidth={2.25} />
            <span className="text-base font-semibold tracking-tight">MythicTrack</span>
          </NavLink>
          <nav className="flex items-center gap-1">
            <NavLink to="/players" className={navLinkClass}>
              Players
            </NavLink>
            <NavLink to="/commanders" className={navLinkClass}>
              Commanders
            </NavLink>
            <NavLink to="/reports/yearly" className={navLinkClass}>
              Yearly Report
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  )
}
