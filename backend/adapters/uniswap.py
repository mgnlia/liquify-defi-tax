"""
Uniswap V2/V3 Protocol Adapter
Indexes swap events and calculates trade P&L for tax reporting.
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
import datetime

# Uniswap contract addresses by network
UNISWAP_CONTRACTS = {
    "ethereum": {
        "v2_router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "v3_router2": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        "v3_quoter": "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
        "v3_factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "v2_factory": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    },
    "polygon": {
        "v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "v3_router2": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
    },
    "arbitrum": {
        "v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "v3_router2": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
    },
}

# Uniswap V3 Swap event ABI
UNISWAP_V3_SWAP_ABI = {
    "name": "Swap",
    "type": "event",
    "inputs": [
        {"name": "sender", "type": "address", "indexed": True},
        {"name": "recipient", "type": "address", "indexed": True},
        {"name": "amount0", "type": "int256"},
        {"name": "amount1", "type": "int256"},
        {"name": "sqrtPriceX96", "type": "uint160"},
        {"name": "liquidity", "type": "uint128"},
        {"name": "tick", "type": "int24"},
    ],
}

# Common ERC20 tokens
KNOWN_TOKENS = {
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": {"symbol": "WETH", "decimals": 18},
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": {"symbol": "USDC", "decimals": 6},
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": {"symbol": "USDT", "decimals": 6},
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": {"symbol": "DAI", "decimals": 18},
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": {"symbol": "WBTC", "decimals": 8},
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": {"symbol": "UNI", "decimals": 18},
}


class UniswapTrade:
    def __init__(
        self,
        tx_hash: str,
        timestamp: datetime.datetime,
        wallet: str,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        amount_out: Decimal,
        amount_in_usd: Decimal,
        amount_out_usd: Decimal,
        network: str,
        version: str = "v3",
    ):
        self.tx_hash = tx_hash
        self.timestamp = timestamp
        self.wallet = wallet
        self.token_in = token_in
        self.token_out = token_out
        self.amount_in = amount_in
        self.amount_out = amount_out
        self.amount_in_usd = amount_in_usd
        self.amount_out_usd = amount_out_usd
        self.network = network
        self.version = version

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_hash": self.tx_hash,
            "timestamp": self.timestamp.isoformat(),
            "wallet": self.wallet,
            "token_in": self.token_in,
            "token_out": self.token_out,
            "amount_in": str(self.amount_in),
            "amount_out": str(self.amount_out),
            "amount_in_usd": str(self.amount_in_usd),
            "amount_out_usd": str(self.amount_out_usd),
            "network": self.network,
            "version": self.version,
            "protocol": "uniswap",
        }


class UniswapAdapter:
    def __init__(self, liquify_client):
        self.client = liquify_client

    def get_contracts(self, network: str) -> List[str]:
        """Get all Uniswap contract addresses for a network."""
        contracts = UNISWAP_CONTRACTS.get(network, {})
        return list(contracts.values())

    async def index_contracts(self, network: str) -> Dict[str, Any]:
        """Register Uniswap contracts for indexing via Liquify."""
        from liquify_client import IndexRequest
        results = []
        for name, address in UNISWAP_CONTRACTS.get(network, {}).items():
            try:
                result = await self.client.index_contract(
                    IndexRequest(
                        contract_address=address,
                        network=network,
                    )
                )
                results.append({"contract": name, "address": address, "result": result})
            except Exception as e:
                results.append({"contract": name, "address": address, "error": str(e)})
        return {"network": network, "indexed": results}

    async def get_swaps(
        self,
        wallet_address: str,
        network: str = "ethereum",
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all Uniswap swaps for a wallet."""
        swaps = []
        contracts = UNISWAP_CONTRACTS.get(network, {})

        for contract_name, contract_addr in contracts.items():
            if "router" not in contract_name:
                continue
            try:
                txns = await self.client.get_transactions(
                    wallet_address=wallet_address,
                    network=network,
                    contract_address=contract_addr,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp,
                )
                for tx in txns:
                    tx["protocol"] = "uniswap"
                    tx["contract_name"] = contract_name
                    swaps.append(tx)
            except Exception as e:
                print(f"Error fetching {contract_name}: {e}")

        return swaps

    def parse_swap_event(self, raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a raw Liquify event into a normalized swap record."""
        try:
            return {
                "tx_hash": raw_event.get("transactionHash", ""),
                "block_number": raw_event.get("blockNumber", 0),
                "timestamp": raw_event.get("timestamp", ""),
                "sender": raw_event.get("args", {}).get("sender", ""),
                "recipient": raw_event.get("args", {}).get("recipient", ""),
                "amount0": raw_event.get("args", {}).get("amount0", "0"),
                "amount1": raw_event.get("args", {}).get("amount1", "0"),
                "protocol": "uniswap",
                "event": "Swap",
            }
        except Exception:
            return None
