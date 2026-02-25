# 🧾 DeFi Tax Intelligence — Powered by Liquify Indexer API

> **Natural-language DeFi tax reporting for retail users.** Ask questions in plain English, get regulatory-compliant tax reports from on-chain data — instantly.

[![Liquify Hackathon](https://img.shields.io/badge/Liquify%20Hackathon-%24100K-blue)](https://dorahacks.io/hackathon/liquify)
[![Category](https://img.shields.io/badge/Category-DeFi%20Tax%20Reporting-green)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

## 🎯 What It Does

Retail DeFi users can't read on-chain data. Tax accountants can't navigate 50 protocols. We bridge that gap:

1. **User types**: *"Show me all my Uniswap trades from 2024 and calculate my capital gains"*
2. **AI parses** the intent and maps to Liquify Indexer API queries
3. **Liquify indexes** the relevant contracts instantly (no full re-sync)
4. **System generates** a FIFO/LIFO capital gains report, CSV export, and Form 8949 summary

## 🏗️ Architecture

```
User NL Query
     │
     ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  React UI   │────▶│  FastAPI Backend  │────▶│  Liquify API    │
│  (Vercel)   │◀────│  (Railway)        │◀────│  Indexer        │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │
                    ┌──────┴──────┐
                    │  AI Layer   │
                    │  (Claude)   │
                    └─────────────┘
```

## 🔌 Protocol Adapters

| Protocol | Network | Events Indexed |
|----------|---------|----------------|
| Uniswap V2/V3 | Ethereum, Polygon, Arbitrum | Swap, Mint, Burn, Collect |
| Aave V2/V3 | Ethereum, Polygon, Avalanche | Deposit, Borrow, Repay, Liquidation |
| Curve | Ethereum | TokenExchange, AddLiquidity, RemoveLiquidity |

## 🚀 Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
export LIQUIFY_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📊 Tax Report Features

- **Capital Gains**: FIFO, LIFO, HIFO cost basis methods
- **Income Events**: Liquidity mining, staking rewards, airdrops
- **Form 8949**: US tax form summary
- **CSV Export**: Compatible with TurboTax, TaxAct, Koinly
- **Multi-chain**: Ethereum, Polygon, Arbitrum, Optimism, Avalanche

## 🔑 API Key Registration

1. Visit [liquify.io](https://www.liquify.io)
2. Sign up for free API key
3. Set `LIQUIFY_API_KEY` environment variable

## 📁 Project Structure

```
liquify-tax-intelligence/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── liquify_client.py    # Liquify Indexer API client
│   ├── nl_query.py          # NL → structured query parser
│   ├── tax_engine.py        # Capital gains calculations
│   ├── adapters/
│   │   ├── uniswap.py       # Uniswap V2/V3 adapter
│   │   ├── aave.py          # Aave V2/V3 adapter
│   │   └── curve.py         # Curve adapter
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── pages/           # Route pages
│   │   └── hooks/           # React hooks
│   ├── package.json
│   └── vite.config.ts
└── docs/
    └── API.md
```

## 🏆 Hackathon Submission

- **Event**: Liquify Indexer API Hackathon ($100K prize pool)
- **Category**: Seamless DeFi Tax Reporting Tool
- **Deadline**: June 14, 2026
- **Platform**: DoraHacks
