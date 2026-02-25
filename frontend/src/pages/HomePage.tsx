import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, ArrowRight, Shield, Clock, Globe, TrendingUp } from 'lucide-react'
import { useNLQuery } from '../hooks/useApi'
import clsx from 'clsx'

const EXAMPLE_QUERIES = [
  'Show me all my Uniswap trades from 2024 and calculate capital gains',
  'What DeFi income did I earn from Aave in 2023?',
  'Generate a Form 8949 for my crypto trades using HIFO method',
  'How much did I lose on Curve liquidity positions in 2024?',
  'Show me all taxable events across Uniswap, Aave and Curve for 2024',
]

export default function HomePage() {
  const navigate = useNavigate()
  const { query, loading, error, result } = useNLQuery()
  const [input, setInput] = useState('')
  const [wallet, setWallet] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    const data = await query(input, wallet || undefined)
    if (data) {
      navigate('/report', { state: { parsed: data.parsed_query, nlQuery: input } })
    }
  }

  const handleExample = (q: string) => {
    setInput(q)
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      {/* Hero */}
      <div className="text-center mb-12 animate-slide-up">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-900/40 border border-brand-700/50 text-brand-300 text-sm mb-6">
          <Zap size={12} className="animate-pulse-slow" />
          Powered by Liquify Indexer API — Instant Contract Indexing
        </div>
        <h1 className="text-5xl font-bold text-white mb-4 leading-tight">
          DeFi Taxes in
          <span className="bg-gradient-to-r from-brand-400 to-defi-purple bg-clip-text text-transparent"> Plain English</span>
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          Ask any DeFi tax question. We query the blockchain instantly via Liquify,
          calculate your gains/losses, and generate regulatory-compliant reports.
        </p>
      </div>

      {/* Query Box */}
      <div className="glass p-6 mb-8 animate-slide-up">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Ask a DeFi tax question
            </label>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="e.g. Show me all my Uniswap trades from 2024 and calculate capital gains"
              rows={3}
              className="input-field resize-none text-base"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Wallet address <span className="text-gray-600">(optional — add later)</span>
            </label>
            <input
              type="text"
              value={wallet}
              onChange={e => setWallet(e.target.value)}
              placeholder="0x..."
              className="input-field font-mono text-sm"
            />
          </div>
          {error && (
            <div className="text-red-400 text-sm bg-red-900/20 border border-red-800/50 rounded-lg px-4 py-2">
              {error}
            </div>
          )}
          <div className="flex gap-3">
            <button type="submit" disabled={loading || !input.trim()} className="btn-primary flex items-center gap-2">
              {loading ? (
                <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Analyzing...</>
              ) : (
                <><Zap size={16} />Analyze Query<ArrowRight size={16} /></>
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate('/demo')}
              className="btn-secondary"
            >
              View Demo Report
            </button>
          </div>
        </form>
      </div>

      {/* Example Queries */}
      <div className="mb-12">
        <p className="text-sm text-gray-500 mb-3">Try an example:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map(q => (
            <button
              key={q}
              onClick={() => handleExample(q)}
              className="text-xs px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 hover:text-white transition-all"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Zap, title: 'Instant Indexing', desc: 'Liquify indexes contracts in milliseconds, not hours', color: 'text-brand-400' },
          { icon: Shield, title: 'FIFO/LIFO/HIFO', desc: 'All IRS-accepted cost basis methods supported', color: 'text-defi-green' },
          { icon: Globe, title: 'Multi-Chain', desc: 'Ethereum, Polygon, Arbitrum, Optimism, Avalanche', color: 'text-defi-purple' },
          { icon: TrendingUp, title: 'Form 8949', desc: 'Export directly to TurboTax, Koinly, TaxAct', color: 'text-defi-orange' },
        ].map(({ icon: Icon, title, desc, color }) => (
          <div key={title} className="glass p-4 hover:border-white/20 transition-all">
            <Icon size={20} className={clsx(color, 'mb-2')} />
            <h3 className="text-sm font-semibold text-white mb-1">{title}</h3>
            <p className="text-xs text-gray-500">{desc}</p>
          </div>
        ))}
      </div>

      {/* Protocol badges */}
      <div className="mt-8 flex items-center justify-center gap-6 text-gray-600 text-sm">
        <span>Supports:</span>
        {['Uniswap V2/V3', 'Aave V2/V3', 'Curve', 'Compound', 'MakerDAO'].map(p => (
          <span key={p} className="text-gray-500">{p}</span>
        ))}
      </div>
    </div>
  )
}
