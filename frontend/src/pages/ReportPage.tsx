import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Download, RefreshCw, AlertCircle, TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react'
import { useTaxReport } from '../hooks/useApi'
import ReportSummary from '../components/ReportSummary'
import Form8949Table from '../components/Form8949Table'
import clsx from 'clsx'

const NETWORKS = ['ethereum', 'polygon', 'arbitrum', 'optimism', 'avalanche']
const PROTOCOLS = ['uniswap', 'aave', 'curve', 'compound', 'maker']
const METHODS = ['FIFO', 'LIFO', 'HIFO', 'SPECIFIC_ID']

export default function ReportPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { generate, loading, error, report } = useTaxReport()

  const parsed = location.state?.parsed

  const [wallet, setWallet] = useState(parsed?.wallet_address || '')
  const [taxYear, setTaxYear] = useState<string>(parsed?.tax_year?.toString() || '2024')
  const [method, setMethod] = useState(parsed?.cost_basis_method || 'FIFO')
  const [networks, setNetworks] = useState<string[]>(parsed?.networks || ['ethereum'])
  const [protocols, setProtocols] = useState<string[]>(parsed?.protocols || ['uniswap', 'aave', 'curve'])
  const [format, setFormat] = useState('detailed')
  const [activeTab, setActiveTab] = useState<'summary' | 'form8949'>('summary')

  const toggleArr = (arr: string[], set: (v: string[]) => void, val: string) => {
    set(arr.includes(val) ? arr.filter(x => x !== val) : [...arr, val])
  }

  const handleGenerate = async () => {
    if (!wallet.trim()) return
    await generate({
      wallet_address: wallet,
      networks,
      protocols,
      tax_year: taxYear ? parseInt(taxYear) : null,
      cost_basis_method: method,
      report_format: format,
    })
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-white mb-2">Tax Report Generator</h1>
      <p className="text-gray-500 mb-8">Configure your report parameters and generate a comprehensive DeFi tax analysis.</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Config Panel */}
        <div className="lg:col-span-1 space-y-4">
          <div className="glass p-5 space-y-4">
            <h2 className="font-semibold text-white">Configuration</h2>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Wallet Address *</label>
              <input
                type="text"
                value={wallet}
                onChange={e => setWallet(e.target.value)}
                placeholder="0x..."
                className="input-field font-mono text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Tax Year</label>
              <select
                value={taxYear}
                onChange={e => setTaxYear(e.target.value)}
                className="input-field"
              >
                <option value="">All years</option>
                {[2024, 2023, 2022, 2021, 2020].map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Cost Basis Method</label>
              <div className="grid grid-cols-2 gap-1.5">
                {METHODS.map(m => (
                  <button
                    key={m}
                    onClick={() => setMethod(m)}
                    className={clsx(
                      'text-xs py-1.5 rounded-lg border transition-all font-medium',
                      method === m
                        ? 'bg-brand-600 border-brand-500 text-white'
                        : 'bg-white/5 border-white/10 text-gray-400 hover:text-white hover:border-white/20'
                    )}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Networks</label>
              <div className="flex flex-wrap gap-1.5">
                {NETWORKS.map(n => (
                  <button
                    key={n}
                    onClick={() => toggleArr(networks, setNetworks, n)}
                    className={clsx(
                      'text-xs px-2.5 py-1 rounded-full border transition-all capitalize',
                      networks.includes(n)
                        ? 'bg-defi-purple/30 border-defi-purple/50 text-purple-300'
                        : 'bg-white/5 border-white/10 text-gray-500 hover:text-white'
                    )}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Protocols</label>
              <div className="flex flex-wrap gap-1.5">
                {PROTOCOLS.map(p => (
                  <button
                    key={p}
                    onClick={() => toggleArr(protocols, setProtocols, p)}
                    className={clsx(
                      'text-xs px-2.5 py-1 rounded-full border transition-all capitalize',
                      protocols.includes(p)
                        ? 'bg-brand-900/60 border-brand-600/50 text-brand-300'
                        : 'bg-white/5 border-white/10 text-gray-500 hover:text-white'
                    )}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading || !wallet.trim()}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {loading ? (
                <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Generating...</>
              ) : (
                <><Activity size={16} />Generate Report</>
              )}
            </button>

            {error && (
              <div className="flex items-start gap-2 text-red-400 text-xs bg-red-900/20 border border-red-800/50 rounded-lg px-3 py-2">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                {error}
              </div>
            )}
          </div>

          {/* CSV Export */}
          {report && (
            <div className="glass p-4">
              <h3 className="text-sm font-medium text-white mb-3">Export</h3>
              <a
                href={`${import.meta.env.VITE_API_URL || 'https://defi-tax-intelligence-api.up.railway.app'}/api/tax-report/csv?wallet_address=${wallet}&tax_year=${taxYear}&cost_basis_method=${method}&networks=${networks.join(',')}&protocols=${protocols.join(',')}`}
                className="btn-secondary w-full flex items-center justify-center gap-2 text-sm"
              >
                <Download size={14} />
                Download CSV (TurboTax/Koinly)
              </a>
            </div>
          )}
        </div>

        {/* Report Panel */}
        <div className="lg:col-span-2">
          {!report && !loading && (
            <div className="glass p-12 text-center">
              <Activity size={48} className="text-gray-700 mx-auto mb-4" />
              <p className="text-gray-500">Configure your wallet and parameters, then generate your tax report.</p>
              <button
                onClick={() => navigate('/demo')}
                className="mt-4 text-brand-400 text-sm hover:underline"
              >
                Or view a demo report →
              </button>
            </div>
          )}

          {loading && (
            <div className="glass p-12 text-center">
              <div className="w-12 h-12 border-4 border-brand-600/30 border-t-brand-500 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-400">Querying Liquify Indexer API...</p>
              <p className="text-gray-600 text-sm mt-1">Fetching on-chain events across {protocols.join(', ')}</p>
            </div>
          )}

          {report && !loading && (
            <div className="space-y-4 animate-slide-up">
              {/* Tab bar */}
              <div className="flex gap-1 glass p-1 w-fit">
                {(['summary', 'form8949'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={clsx(
                      'px-4 py-1.5 rounded-lg text-sm font-medium transition-all',
                      activeTab === tab ? 'bg-brand-600 text-white' : 'text-gray-400 hover:text-white'
                    )}
                  >
                    {tab === 'form8949' ? 'Form 8949' : 'Summary'}
                  </button>
                ))}
              </div>

              {activeTab === 'summary' && <ReportSummary report={report} />}
              {activeTab === 'form8949' && <Form8949Table report={report} />}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
