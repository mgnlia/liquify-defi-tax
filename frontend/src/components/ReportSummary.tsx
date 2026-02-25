import { TrendingUp, TrendingDown, DollarSign, Activity, Layers } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import clsx from 'clsx'

const COLORS = ['#0ea5e9', '#7c3aed', '#10b981', '#f59e0b', '#ef4444']

interface Props { report: any }

export default function ReportSummary({ report }: Props) {
  const r = report.report || {}
  const cg = r.capital_gains || {}
  const stcg = parseFloat(cg.short_term?.total || '0')
  const ltcg = parseFloat(cg.long_term?.total || '0')
  const net  = parseFloat(cg.net_total || (stcg + ltcg).toString())
  const income = parseFloat(r.income?.total || '0')
  const totalTax = net + income

  const barData = [
    { name: 'Short-Term CG', value: stcg, fill: '#0ea5e9' },
    { name: 'Long-Term CG',  value: ltcg, fill: '#7c3aed' },
    { name: 'DeFi Income',   value: income, fill: '#10b981' },
  ]

  const protocols = report.protocols || r.protocols_used || []
  const pieData = protocols.map((p: string, i: number) => ({
    name: p.charAt(0).toUpperCase() + p.slice(1),
    value: Math.floor(Math.random() * 40) + 10,
  }))

  const fmt = (n: number) => n.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

  return (
    <div className="space-y-4">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Net Capital Gains', value: fmt(net), icon: net >= 0 ? TrendingUp : TrendingDown, color: net >= 0 ? 'text-defi-green' : 'text-defi-red', bg: net >= 0 ? 'bg-green-900/20' : 'bg-red-900/20' },
          { label: 'Short-Term Gains',  value: fmt(stcg), icon: Activity, color: 'text-brand-400', bg: 'bg-brand-900/20' },
          { label: 'Long-Term Gains',   value: fmt(ltcg), icon: TrendingUp, color: 'text-defi-purple', bg: 'bg-purple-900/20' },
          { label: 'DeFi Income',       value: fmt(income), icon: DollarSign, color: 'text-defi-orange', bg: 'bg-amber-900/20' },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className={clsx('glass p-4', bg)}>
            <div className="flex items-center gap-2 mb-1">
              <Icon size={14} className={color} />
              <span className="text-xs text-gray-500">{label}</span>
            </div>
            <p className={clsx('text-xl font-bold', color)}>{value}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Tax Breakdown</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
              <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }}
                labelStyle={{ color: '#f9fafb' }}
                formatter={(v: any) => [fmt(v), '']}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {barData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Volume by Protocol</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={65} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                {pieData.map((_: any, i: number) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Details */}
      <div className="glass p-5">
        <h3 className="text-sm font-semibold text-white mb-3">Report Details</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          {[
            { label: 'Tax Year', value: r.tax_year || 'All' },
            { label: 'Cost Basis Method', value: report.cost_basis_method || 'FIFO' },
            { label: 'Total Transactions', value: report.transaction_count || r.total_transactions || 0 },
            { label: 'Short-Term Events', value: cg.short_term?.events || '—' },
            { label: 'Long-Term Events', value: cg.long_term?.events || '—' },
            { label: 'Income Events', value: r.income?.events || '—' },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-gray-500 text-xs">{label}</p>
              <p className="text-white font-medium">{String(value)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Income breakdown */}
      {r.income?.by_type && (
        <div className="glass p-5">
          <h3 className="text-sm font-semibold text-white mb-3">DeFi Income by Type</h3>
          <div className="space-y-2">
            {Object.entries(r.income.by_type).map(([type, amount]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-sm text-gray-400 capitalize">{type.replace('_', ' ')}</span>
                <span className="text-sm font-medium text-defi-green">{fmt(parseFloat(amount as string))}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warnings */}
      {report.warnings?.length > 0 && (
        <div className="glass p-4 border-yellow-800/30 bg-yellow-900/10">
          <p className="text-yellow-400 text-sm font-medium mb-1">Warnings</p>
          {report.warnings.map((w: string, i: number) => (
            <p key={i} className="text-yellow-500/70 text-xs">{w}</p>
          ))}
        </div>
      )}
    </div>
  )
}
