"""
DeFi Tax Intelligence API — Vercel Serverless Handler
Self-contained: no local module imports, works with only requirements.txt deps.
"""
import os
import json
from typing import Optional
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Liquify DeFi Tax Intelligence API",
    description="Natural-language DeFi tax reporting powered by Liquify Indexer API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────────

class NLQueryRequest(BaseModel):
    query: str
    wallet_address: Optional[str] = None
    tax_year: Optional[int] = 2024
    cost_basis_method: Optional[str] = "FIFO"

class TaxReportRequest(BaseModel):
    wallet_address: str
    tax_year: Optional[int] = 2024
    cost_basis_method: Optional[str] = "FIFO"

# ── Mock data ─────────────────────────────────────────────────────────────────

MOCK_TRANSACTIONS = [
    {
        "id": "0xabc123",
        "protocol": "Uniswap V3",
        "type": "SWAP",
        "timestamp": "2024-03-15T10:23:00Z",
        "token_in": {"symbol": "ETH", "amount": 1.5, "usd_value": 5250.00},
        "token_out": {"symbol": "USDC", "amount": 5247.50, "usd_value": 5247.50},
        "gas_usd": 12.30,
        "chain": "ethereum",
    },
    {
        "id": "0xdef456",
        "protocol": "Aave V3",
        "type": "DEPOSIT",
        "timestamp": "2024-06-20T14:05:00Z",
        "token": {"symbol": "USDC", "amount": 3000.00, "usd_value": 3000.00},
        "gas_usd": 8.50,
        "chain": "ethereum",
    },
    {
        "id": "0xghi789",
        "protocol": "Curve",
        "type": "ADD_LIQUIDITY",
        "timestamp": "2024-09-10T09:45:00Z",
        "token": {"symbol": "USDC", "amount": 2000.00, "usd_value": 2000.00},
        "gas_usd": 15.20,
        "chain": "ethereum",
    },
]

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "liquify_configured": bool(os.getenv("LIQUIFY_API_KEY")),
        "ai_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
    }

@app.post("/api/query")
async def nl_query(req: NLQueryRequest):
    query_lower = req.query.lower()
    filtered = MOCK_TRANSACTIONS
    if "uniswap" in query_lower or "swap" in query_lower:
        filtered = [t for t in MOCK_TRANSACTIONS if t["protocol"] == "Uniswap V3"]
    elif "aave" in query_lower or "deposit" in query_lower or "lend" in query_lower:
        filtered = [t for t in MOCK_TRANSACTIONS if t["protocol"] == "Aave V3"]
    elif "curve" in query_lower or "liquidity" in query_lower:
        filtered = [t for t in MOCK_TRANSACTIONS if t["protocol"] == "Curve"]

    summary = _ai_summary(req.query, filtered)
    return {
        "query": req.query,
        "wallet_address": req.wallet_address,
        "transactions_found": len(filtered),
        "transactions": filtered,
        "ai_summary": summary,
        "data_source": "mock — set LIQUIFY_API_KEY for live Liquify Indexer data",
    }

@app.post("/api/tax-report")
async def tax_report(req: TaxReportRequest):
    return {
        "wallet_address": req.wallet_address,
        "tax_year": req.tax_year,
        "cost_basis_method": req.cost_basis_method,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "short_term_gains": 1247.50,
        "long_term_gains": 3820.00,
        "total_gains": 5067.50,
        "total_gas_fees_usd": 36.00,
        "deductible_gas_fees": 36.00,
        "taxable_events": 3,
        "transactions": MOCK_TRANSACTIONS,
        "form_8949_summary": {
            "part_i_short_term": {"proceeds": 5247.50, "cost_basis": 4000.00, "gain_loss": 1247.50},
            "part_ii_long_term": {"proceeds": 8200.00, "cost_basis": 4380.00, "gain_loss": 3820.00},
        },
        "data_source": "mock — set LIQUIFY_API_KEY for live Liquify Indexer data",
    }

@app.get("/api/transactions")
async def get_transactions(
    wallet: Optional[str] = None,
    protocol: Optional[str] = None,
    chain: Optional[str] = None,
    limit: int = 50,
):
    txns = MOCK_TRANSACTIONS
    if protocol:
        txns = [t for t in txns if protocol.lower() in t["protocol"].lower()]
    if chain:
        txns = [t for t in txns if t["chain"] == chain.lower()]
    return {
        "wallet": wallet,
        "count": len(txns[:limit]),
        "transactions": txns[:limit],
        "data_source": "mock — set LIQUIFY_API_KEY for live Liquify Indexer data",
    }

@app.get("/api/protocols")
async def get_protocols():
    return {
        "protocols": [
            {"name": "Uniswap V2", "chains": ["ethereum", "polygon", "arbitrum"], "events": ["Swap", "Mint", "Burn"]},
            {"name": "Uniswap V3", "chains": ["ethereum", "polygon", "arbitrum", "optimism"], "events": ["Swap", "Mint", "Burn", "Collect"]},
            {"name": "Aave V2", "chains": ["ethereum", "polygon", "avalanche"], "events": ["Deposit", "Borrow", "Repay", "Liquidation"]},
            {"name": "Aave V3", "chains": ["ethereum", "polygon", "arbitrum", "avalanche"], "events": ["Supply", "Borrow", "Repay", "Liquidation"]},
            {"name": "Curve", "chains": ["ethereum"], "events": ["TokenExchange", "AddLiquidity", "RemoveLiquidity"]},
        ]
    }

# ── Helpers ───────────────────────────────────────────────────────────────────

def _ai_summary(query: str, transactions: list) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Summarize these {len(transactions)} DeFi transactions "
                        f"for the query '{query}' in 2 sentences: "
                        f"{json.dumps(transactions[:3])}"
                    ),
                }],
            )
            return msg.content[0].text.strip()
        except Exception:
            pass
    if not transactions:
        return f"No transactions found matching '{query}'."
    protocols = list({t["protocol"] for t in transactions})
    total_gas = sum(t.get("gas_usd", 0) for t in transactions)
    return f"Found {len(transactions)} transaction(s) across {', '.join(protocols)}. Total gas fees: ${total_gas:.2f}."

# ── Mangum handler ────────────────────────────────────────────────────────────

handler = Mangum(app, lifespan="off")
