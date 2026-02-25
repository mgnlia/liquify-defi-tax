import { useState, useCallback } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'https://defi-tax-intelligence-api.up.railway.app'

const api = axios.create({ baseURL: API_BASE, timeout: 60000 })

export function useNLQuery() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)

  const query = useCallback(async (q: string, wallet?: string) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post('/api/query', { query: q, wallet_address: wallet })
      setResult(data)
      return data
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Query failed'
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { query, loading, error, result }
}

export function useTaxReport() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [report, setReport] = useState<any>(null)

  const generate = useCallback(async (params: {
    wallet_address: string
    networks?: string[]
    protocols?: string[]
    tax_year?: number | null
    cost_basis_method?: string
    report_format?: string
  }) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post('/api/tax-report', params)
      setReport(data)
      return data
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Report generation failed'
      setError(msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { generate, loading, error, report }
}

export function useDemo() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)

  const loadDemo = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/api/demo')
      setData(res.data)
      return res.data
    } catch {
      // Fallback to local mock
      const mock = generateMockReport()
      setData(mock)
      return mock
    } finally {
      setLoading(false)
    }
  }, [])

  return { loadDemo, loading, data }
}

function generateMockReport() {
  return {
    demo: true,
    wallet: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
    report: {
      tax_year: 2024,
      cost_basis_method: 'FIFO',
      capital_gains: {
        short_term: { total: '4821.33', events: 23 },
        long_term: { total: '12440.17', events: 11 },
        net_total: '17261.50',
      },
      income: {
        total: '843.22',
        events: 7,
        by_type: { interest: '612.10', staking_reward: '231.12' },
      },
      protocols_used: ['uniswap', 'aave', 'curve'],
      total_transactions: 47,
    },
    transaction_count: 47,
    networks: ['ethereum', 'polygon'],
    protocols: ['uniswap', 'aave', 'curve'],
    cost_basis_method: 'FIFO',
    message: 'This is demo data. Connect a real wallet to generate your actual tax report.',
    form_8949: [
      { description: '2.5 ETH (uniswap)', date_acquired: '01/15/2024', date_sold: '03/22/2024', proceeds: '8750.00', cost_basis: '6200.00', gain_loss: '2550.00', term: 'A' },
      { description: '1500 USDC (curve)', date_acquired: '02/01/2024', date_sold: '04/10/2024', proceeds: '1500.00', cost_basis: '1500.00', gain_loss: '0.00', term: 'A' },
      { description: '0.08 WBTC (uniswap)', date_acquired: '11/20/2023', date_sold: '05/15/2024', proceeds: '4800.00', cost_basis: '3200.00', gain_loss: '1600.00', term: 'D' },
    ],
  }
}
