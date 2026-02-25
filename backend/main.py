"""
DeFi Tax Intelligence API
FastAPI backend — natural language → Liquify Indexer → tax report
"""
import os
import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import io

from liquify_client import get_liquify_client, EventQuery
from nl_query import get_parser, ParsedQuery
from tax_engine import TaxEngine
from adapters import UniswapAdapter, AaveAdapter, CurveAdapter

app = FastAPI(
    title="DeFi Tax Intelligence API",
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

class TaxReportRequest(BaseModel):
    wallet_address: str
    networks: List[str] = ["ethereum"]
    protocols: List[str] = ["uniswap", "aave", "curve"]
    tax_year: Optional[int] = None
    cost_basis_method: str = "FIFO"
    report_format: str = "summary"

class IndexContractRequest(BaseModel):
    contract_address: str
    network: str = "ethereum"

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "defi-tax-intelligence",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }

@app.get("/")
async def root():
    return {
        "name": "DeFi Tax Intelligence",
        "description": "Natural-language DeFi tax reporting powered by Liquify Indexer API",
        "docs": "/docs",
        "health": "/health",
    }

# ── NL Query ──────────────────────────────────────────────────────────────────

@app.post("/api/query")
async def natural_language_query(request: NLQueryRequest):
    """
    Parse a natural language DeFi tax question.
    Returns structured query intent + preliminary answer.
    """
    parser = get_parser()
    parsed = parser.parse(request.query)

    # Override wallet if provided in request
    if request.wallet_address and not parsed.wallet_address:
        parsed.wallet_address = request.wallet_address

    return {
        "parsed_query": parsed.model_dump(),
        "message": _generate_response_message(parsed),
        "next_step": "call /api/tax-report with the parsed parameters to get full report",
    }

def _generate_response_message(parsed: ParsedQuery) -> str:
    parts = []
    if parsed.wallet_address:
        parts.append(f"wallet {parsed.wallet_address[:6]}...{parsed.wallet_address[-4:]}")
    if parsed.protocols:
        parts.append(f"protocols: {', '.join(parsed.protocols)}")
    if parsed.tax_year:
        parts.append(f"tax year {parsed.tax_year}")
    if parsed.cost_basis_method:
        parts.append(f"{parsed.cost_basis_method} cost basis")
    desc = ", ".join(parts) if parts else "all DeFi activity"
    return f"Generating {parsed.intent.replace('_', ' ')} for {desc}"

# ── Tax Report ────────────────────────────────────────────────────────────────

@app.post("/api/tax-report")
async def generate_tax_report(request: TaxReportRequest):
    """
    Generate a full DeFi tax report for a wallet.
    Queries Liquify Indexer API for on-chain data, runs tax calculations.
    """
    if not request.wallet_address or not request.wallet_address.startswith("0x"):
        raise HTTPException(status_code=400, detail="Valid Ethereum wallet address required (0x...)")

    client = get_liquify_client()
    engine = TaxEngine(cost_basis_method=request.cost_basis_method)

    # Calculate timestamp range
    from_ts, to_ts = _get_timestamp_range(request.tax_year)

    all_transactions = []
    errors = []

    # Fetch from each requested protocol × network
    for network in request.networks:
        if "uniswap" in request.protocols:
            adapter = UniswapAdapter(client)
            try:
                swaps = await adapter.get_swaps(
                    request.wallet_address, network, from_ts, to_ts
                )
                all_transactions.extend(swaps)
            except Exception as e:
                errors.append(f"Uniswap/{network}: {str(e)}")

        if "aave" in request.protocols:
            adapter = AaveAdapter(client)
            try:
                events = await adapter.get_user_events(
                    request.wallet_address, network, from_ts, to_ts
                )
                all_transactions.extend(events)
            except Exception as e:
                errors.append(f"Aave/{network}: {str(e)}")

        if "curve" in request.protocols:
            adapter = CurveAdapter(client)
            try:
                exchanges = await adapter.get_exchanges(
                    request.wallet_address, network, from_ts, to_ts
                )
                all_transactions.extend(exchanges)
            except Exception as e:
                errors.append(f"Curve/{network}: {str(e)}")

    # Process transactions through tax engine
    _process_transactions(engine, all_transactions)

    # Generate report
    summary = engine.generate_summary(tax_year=request.tax_year)

    response = {
        "wallet": request.wallet_address,
        "report": summary,
        "transaction_count": len(all_transactions),
        "networks": request.networks,
        "protocols": request.protocols,
        "cost_basis_method": request.cost_basis_method,
    }

    if errors:
        response["warnings"] = errors

    if request.report_format == "form8949":
        response["form_8949"] = engine.generate_form_8949(request.tax_year)
    elif request.report_format == "detailed":
        response["tax_events"] = [
            {
                "asset": e.asset,
                "amount": str(e.amount_disposed),
                "proceeds_usd": str(e.proceeds_usd),
                "cost_basis_usd": str(e.cost_basis_usd),
                "gain_loss_usd": str(e.gain_loss_usd),
                "holding_period": e.holding_period,
                "disposed_date": e.disposed_date.isoformat(),
                "protocol": e.protocol,
                "tx_hash": e.tx_hash,
            }
            for e in engine.tax_events
        ]

    return response

@app.get("/api/tax-report/csv")
async def export_csv(
    wallet_address: str = Query(...),
    tax_year: Optional[int] = Query(None),
    cost_basis_method: str = Query("FIFO"),
    networks: str = Query("ethereum"),
    protocols: str = Query("uniswap,aave,curve"),
):
    """Export tax report as CSV (TurboTax/Koinly compatible)."""
    request = TaxReportRequest(
        wallet_address=wallet_address,
        networks=networks.split(","),
        protocols=protocols.split(","),
        tax_year=tax_year,
        cost_basis_method=cost_basis_method,
        report_format="csv",
    )
    report_data = await generate_tax_report(request)

    client = get_liquify_client()
    engine = TaxEngine(cost_basis_method=cost_basis_method)
    csv_content = engine.export_csv(tax_year=tax_year)

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=defi_tax_{wallet_address[:8]}_{tax_year or 'all'}.csv"
        },
    )

# ── Protocol Indexing ─────────────────────────────────────────────────────────

@app.post("/api/index-contract")
async def index_contract(request: IndexContractRequest):
    """Register a contract for instant indexing via Liquify."""
    client = get_liquify_client()
    from liquify_client import IndexRequest
    try:
        result = await client.index_contract(
            IndexRequest(
                contract_address=request.contract_address,
                network=request.network,
            )
        )
        return {"status": "indexed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/protocols")
async def list_protocols():
    """List supported DeFi protocols and their contract addresses."""
    from adapters.uniswap import UNISWAP_CONTRACTS
    from adapters.aave import AAVE_CONTRACTS
    from adapters.curve import CURVE_CONTRACTS
    return {
        "uniswap": UNISWAP_CONTRACTS,
        "aave": AAVE_CONTRACTS,
        "curve": CURVE_CONTRACTS,
    }

@app.get("/api/demo")
async def demo_report():
    """
    Demo endpoint — returns a sample tax report with mock data.
    Use this to test the UI without a real API key.
    """
    engine = TaxEngine(cost_basis_method="FIFO")

    # Seed mock data
    _seed_demo_data(engine)

    summary = engine.generate_summary(tax_year=2024)
    form_8949 = engine.generate_form_8949(tax_year=2024)

    return {
        "demo": True,
        "wallet": "0xDEMO...1234",
        "report": summary,
        "form_8949": form_8949[:5],  # First 5 rows
        "transaction_count": 47,
        "networks": ["ethereum", "polygon"],
        "protocols": ["uniswap", "aave", "curve"],
        "cost_basis_method": "FIFO",
        "message": "This is demo data. Connect a real wallet to generate your actual tax report.",
    }

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_timestamp_range(tax_year: Optional[int]):
    if not tax_year:
        return None, None
    start = int(datetime.datetime(tax_year, 1, 1).timestamp())
    end = int(datetime.datetime(tax_year, 12, 31, 23, 59, 59).timestamp())
    return start, end

def _process_transactions(engine: TaxEngine, transactions: List[Dict[str, Any]]):
    """Process raw transactions through the tax engine."""
    for tx in transactions:
        try:
            protocol = tx.get("protocol", "unknown")
            tx_hash = tx.get("hash", tx.get("transactionHash", "0x0"))
            timestamp = tx.get("timestamp")
            if isinstance(timestamp, (int, float)):
                dt = datetime.datetime.utcfromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                try:
                    dt = datetime.datetime.fromisoformat(timestamp)
                except Exception:
                    dt = datetime.datetime.utcnow()
            else:
                dt = datetime.datetime.utcnow()

            # Map protocol events to tax engine calls
            event_type = tx.get("event", tx.get("type", ""))
            if event_type in ("Swap", "TokenExchange", "swap"):
                token_in = tx.get("token_in", tx.get("tokenIn", "UNKNOWN"))
                token_out = tx.get("token_out", tx.get("tokenOut", "UNKNOWN"))
                amount_in = Decimal(str(tx.get("amount_in", tx.get("amountIn", "0"))))
                amount_out = Decimal(str(tx.get("amount_out", tx.get("amountOut", "0"))))
                value_usd = Decimal(str(tx.get("value_usd", tx.get("valueUSD", "0"))))

                if amount_in > 0:
                    engine.add_acquisition(token_in, amount_in, value_usd, dt, tx_hash, protocol)
                if amount_out > 0:
                    engine.add_disposal(token_out, amount_out, value_usd, dt, tx_hash, protocol, "swap")

        except Exception as e:
            pass  # Skip malformed transactions

def _seed_demo_data(engine: TaxEngine):
    """Seed demo data for the /api/demo endpoint."""
    import random
    random.seed(42)
    tokens = ["ETH", "USDC", "WBTC", "UNI", "AAVE", "CRV"]
    protocols = ["uniswap", "aave", "curve"]

    base_date = datetime.datetime(2024, 1, 15)
    for i in range(20):
        token = random.choice(tokens)
        dt = base_date + datetime.timedelta(days=i * 12)
        cost = Decimal(str(round(random.uniform(100, 5000), 2)))
        amount = Decimal(str(round(random.uniform(0.1, 10.0), 4)))
        engine.add_acquisition(token, amount, cost, dt, f"0xabc{i:04x}", random.choice(protocols))

    for i in range(15):
        token = random.choice(tokens)
        dt = base_date + datetime.timedelta(days=i * 18 + 5)
        proceeds = Decimal(str(round(random.uniform(80, 6000), 2)))
        amount = Decimal(str(round(random.uniform(0.05, 5.0), 4)))
        engine.add_disposal(token, amount, proceeds, dt, f"0xdef{i:04x}", random.choice(protocols))

    for i in range(5):
        dt = base_date + datetime.timedelta(days=i * 30)
        engine.add_income(
            "USDC", Decimal(str(round(random.uniform(10, 200), 2))),
            Decimal(str(round(random.uniform(10, 200), 2))),
            dt, f"0xinc{i:04x}", "aave", "interest"
        )
