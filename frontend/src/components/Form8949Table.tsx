import clsx from 'clsx'

interface Row {
  description: string
  date_acquired: string
  date_sold: string
  proceeds: string
  cost_basis: string
  gain_loss: string
  term: string
}

interface Props { report: any }

export default function Form8949Table({ report }: Props) {
  const rows: Row[] = report.form_8949 || report.tax_events?.map((e: any) => ({
    description: `${e.amount} ${e.asset} (${e.protocol})`,
    date_acquired: '—',
    date_sold: e.disposed_date?.split('T')[0] || '—',
    proceeds: e.proceeds_usd,
    cost_basis: e.cost_basis_usd,
    gain_loss: e.gain_loss_usd,
    term: e.holding_period === 'long' ? 'D' : 'A',
  })) || []

  if (!rows.length) {
    return (
      <div className="glass p-8 text-center text-gray-500">
        No Form 8949 data available. Generate a detailed report to see transaction-level data.
      </div>
    )
  }

  const termLabel: Record<string, string> = {
    A: 'Short-Term (Box A)',
    B: 'Short-Term (Box B)',
    C: 'Short-Term (Box C)',
    D: 'Long-Term (Box D)',
    E: 'Long-Term (Box E)',
    F: 'Long-Term (Box F)',
  }

  const fmt = (s: string) => {
    const n = parseFloat(s)
    if (isNaN(n)) return s
    return n.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
  }

  return (
    <div className="glass overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-white">IRS Form 8949 — Capital Asset Sales</h3>
          <p className="text-xs text-gray-500 mt-0.5">{rows.length} transactions · Ready for TurboTax / Koinly import</p>
        </div>
        <span className="tag bg-brand-900/60 text-brand-300 text-xs">
          {rows.filter(r => ['A','B','C'].includes(r.term)).length} short / {rows.filter(r => ['D','E','F'].includes(r.term)).length} long
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-xs text-gray-500">
              <th className="px-4 py-3 text-left">Description</th>
              <th className="px-4 py-3 text-left">Date Acquired</th>
              <th className="px-4 py-3 text-left">Date Sold</th>
              <th className="px-4 py-3 text-right">Proceeds</th>
              <th className="px-4 py-3 text-right">Cost Basis</th>
              <th className="px-4 py-3 text-right">Gain / Loss</th>
              <th className="px-4 py-3 text-center">Box</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const gl = parseFloat(row.gain_loss)
              const isGain = gl >= 0
              return (
                <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="px-4 py-3 text-gray-300 font-mono text-xs">{row.description}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{row.date_acquired}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{row.date_sold}</td>
                  <td className="px-4 py-3 text-right text-white text-xs">{fmt(row.proceeds)}</td>
                  <td className="px-4 py-3 text-right text-gray-400 text-xs">{fmt(row.cost_basis)}</td>
                  <td className={clsx('px-4 py-3 text-right text-xs font-semibold', isGain ? 'text-defi-green' : 'text-red-400')}>
                    {isGain ? '+' : ''}{fmt(row.gain_loss)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={clsx(
                      'tag text-xs',
                      ['A','B','C'].includes(row.term)
                        ? 'bg-brand-900/60 text-brand-300'
                        : 'bg-purple-900/60 text-purple-300'
                    )}>
                      {row.term}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
          <tfoot className="border-t border-white/20">
            <tr>
              <td colSpan={3} className="px-4 py-3 text-xs text-gray-500">Totals</td>
              <td className="px-4 py-3 text-right text-white text-xs font-semibold">
                {rows.reduce((s, r) => s + parseFloat(r.proceeds || '0'), 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
              </td>
              <td className="px-4 py-3 text-right text-gray-400 text-xs font-semibold">
                {rows.reduce((s, r) => s + parseFloat(r.cost_basis || '0'), 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
              </td>
              <td className="px-4 py-3 text-right text-xs font-semibold">
                {(() => {
                  const total = rows.reduce((s, r) => s + parseFloat(r.gain_loss || '0'), 0)
                  return <span className={total >= 0 ? 'text-defi-green' : 'text-red-400'}>{total >= 0 ? '+' : ''}{total.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span>
                })()}
              </td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
