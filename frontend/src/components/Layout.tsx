import { Outlet, Link, useLocation } from 'react-router-dom'
import { BarChart3, FileText, Zap, Github } from 'lucide-react'
import clsx from 'clsx'

export default function Layout() {
  const loc = useLocation()

  const nav = [
    { to: '/',      label: 'Query',  icon: Zap },
    { to: '/report', label: 'Report', icon: FileText },
    { to: '/demo',   label: 'Demo',   icon: BarChart3 },
  ]

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-white/10 bg-gray-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-defi-purple flex items-center justify-center">
              <span className="text-white font-bold text-sm">₿</span>
            </div>
            <span className="font-semibold text-white">DeFi Tax Intelligence</span>
            <span className="tag bg-brand-900/60 text-brand-300 ml-1">Liquify</span>
          </Link>

          <nav className="flex items-center gap-1">
            {nav.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  loc.pathname === to
                    ? 'bg-brand-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-white/10'
                )}
              >
                <Icon size={14} />
                {label}
              </Link>
            ))}
            <a
              href="https://github.com/mgnlia/liquify-tax-intelligence"
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 text-gray-500 hover:text-white transition-colors"
            >
              <Github size={18} />
            </a>
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-6 text-center text-sm text-gray-600">
        <p>
          Built for{' '}
          <a href="https://dorahacks.io/hackathon/liquify" className="text-brand-400 hover:underline" target="_blank" rel="noopener noreferrer">
            Liquify Indexer API Hackathon
          </a>{' '}
          · $100K Prize Pool · Powered by{' '}
          <span className="text-brand-400">Liquify Indexer API</span>
        </p>
      </footer>
    </div>
  )
}
