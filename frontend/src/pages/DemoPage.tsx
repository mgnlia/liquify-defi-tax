import { useEffect } from 'react'
import { useDemo } from '../hooks/useApi'
import ReportSummary from '../components/ReportSummary'
import Form8949Table from '../components/Form8949Table'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import clsx from 'clsx'

export default function DemoPage() {
  const { loadDemo, loading, data } = useDemo()
  const [tab, setTab] = useState<'summary' | 'form8949'>('summary')
  const navigate = useNavigate()

  useEffect(() => { loadDemo() }, [])

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-900/30 border border-amber-700/40 text-amber-400 text-xs mb-3">
            ⚠ Demo Data — Not Real Tax Advice
          </div>
          <h1 className="text-3xl font-bold text-white">Sample Tax Report</h1>
          <p className="text-gray-500 mt-1">
            Wallet: <span className="font-mono text-brand-400">0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045</span> · FY 2024
          </p>
        </div>
        <button onClick={() => navigate('/report')} className="btn-primary text-sm">
          Generate My Report →
        </button>
      </div>

      {loading && (
        <div className="glass p-12 text-center">
          <div className="w-10 h-10 border-4 border-brand-600/30 border-t-brand-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-500">Loading demo data...</p>
        </div>
      )}

      {data && !loading && (
        <div className="space-y-4 animate-slide-up">
          <div className="flex gap-1 glass p-1 w-fit">
            {(['summary', 'form8949'] as const).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={clsx(
                  'px-4 py-1.5 rounded-lg text-sm font-medium transition-all',
                  tab === t ? 'bg-brand-600 text-white' : 'text-gray-400 hover:text-white'
                )}
              >
                {t === 'form8949' ? 'Form 8949' : 'Summary'}
              </button>
            ))}
          </div>

          {tab === 'summary' && <ReportSummary report={data} />}
          {tab === 'form8949' && <Form8949Table report={data} />}

          <div className="glass p-4 border-amber-800/30 bg-amber-900/10 text-amber-400 text-sm">
            {data.message}
          </div>
        </div>
      )}
    </div>
  )
}
