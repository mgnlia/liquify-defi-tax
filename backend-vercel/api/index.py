"""
DeFi Tax Intelligence API — Vercel Python Serverless (native http.server handler)
Uses Vercel's native Python handler signature: handler(request) -> Response
Compatible with @vercel/python runtime without mangum/ASGI.
Zero external dependencies — stdlib only.
"""
import json
import os
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs


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


def _json_response(handler, data, status=200):
    body = json.dumps(data).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def _read_body(handler):
    length = int(handler.headers.get("Content-Length", 0))
    if length:
        return json.loads(handler.rfile.read(length))
    return {}


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress access logs

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ("/health", ""):
            _json_response(self, {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "liquify_configured": bool(os.getenv("LIQUIFY_API_KEY")),
                "ai_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            })

        elif path == "/api/protocols":
            _json_response(self, {
                "protocols": [
                    {"name": "Uniswap V2", "chains": ["ethereum", "polygon", "arbitrum"], "events": ["Swap", "Mint", "Burn"]},
                    {"name": "Uniswap V3", "chains": ["ethereum", "polygon", "arbitrum", "optimism"], "events": ["Swap", "Mint", "Burn", "Collect"]},
                    {"name": "Aave V2", "chains": ["ethereum", "polygon", "avalanche"], "events": ["Deposit", "Borrow", "Repay", "Liquidation"]},
                    {"name": "Aave V3", "chains": ["ethereum", "polygon", "arbitrum", "avalanche"], "events": ["Supply", "Borrow", "Repay", "Liquidation"]},
                    {"name": "Curve", "chains": ["ethereum"], "events": ["TokenExchange", "AddLiquidity", "RemoveLiquidity"]},
                ]
            })

        elif path == "/api/transactions":
            qs = parse_qs(parsed.query)
            protocol = qs.get("protocol", [None])[0]
            chain = qs.get("chain", [None])[0]
            limit = int(qs.get("limit", ["50"])[0])
            txns = MOCK_TRANSACTIONS
            if protocol:
                txns = [t for t in txns if protocol.lower() in t["protocol"].lower()]
            if chain:
                txns = [t for t in txns if t["chain"] == chain.lower()]
            _json_response(self, {
                "count": len(txns[:limit]),
                "transactions": txns[:limit],
                "data_source": "mock — set LIQUIFY_API_KEY for live data",
            })

        else:
            _json_response(self, {"error": "Not found", "path": path}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = _read_body(self)

        if path == "/api/query":
            query = body.get("query", "")
            wallet = body.get("wallet_address")
            query_lower = query.lower()
            filtered = MOCK_TRANSACTIONS
            if "uniswap" in query_lower or "swap" in query_lower:
                filtered = [t for t in MOCK_TRANSACTIONS if t["protocol"] == "Uniswap V3"]
            elif "aave" in query_lower or "deposit" in query_lower:
                filtered = [t for t in MOCK_TRANSACTIONS if t["protocol"] == "Aave V3"]
            elif "curve" in query_lower or "liquidity" in query_lower:
                filtered = [t for t in MOCK_TRANSACTIONS if t["protocol"] == "Curve"]

            protocols = list({t["protocol"] for t in filtered})
            total_gas = sum(t.get("gas_usd", 0) for t in filtered)
            summary = (
                f"Found {len(filtered)} transaction(s) across {', '.join(protocols)}. "
                f"Total gas fees: ${total_gas:.2f}."
            ) if filtered else f"No transactions found matching '{query}'."

            _json_response(self, {
                "query": query,
                "wallet_address": wallet,
                "transactions_found": len(filtered),
                "transactions": filtered,
                "ai_summary": summary,
                "data_source": "mock — set LIQUIFY_API_KEY for live data",
            })

        elif path == "/api/tax-report":
            wallet = body.get("wallet_address", "unknown")
            tax_year = body.get("tax_year", 2024)
            method = body.get("cost_basis_method", "FIFO")
            _json_response(self, {
                "wallet_address": wallet,
                "tax_year": tax_year,
                "cost_basis_method": method,
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
                "data_source": "mock — set LIQUIFY_API_KEY for live data",
            })

        else:
            _json_response(self, {"error": "Not found", "path": path}, 404)
