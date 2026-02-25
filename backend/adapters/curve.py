"""
Curve Finance Protocol Adapter
Indexes token exchanges and liquidity events for tax reporting.
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal

# Curve key contracts on Ethereum
CURVE_CONTRACTS = {
    "ethereum": {
        "3pool": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",
        "steth_pool": "0xDC24316b9AE028F1497c275EB9192a3Ea0f67022",
        "tricrypto2": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46",
        "router": "0xF0d4c12A5768D806021F80a262B4d39d26C58b8D",
        "address_provider": "0x0000000022D53366457F9d5E68Ec105046FC4383",
    }
}

CURVE_TAX_EVENTS = ["TokenExchange", "AddLiquidity", "RemoveLiquidity", "RemoveLiquidityOne"]


class CurveAdapter:
    def __init__(self, liquify_client):
        self.client = liquify_client

    def get_contracts(self, network: str) -> List[str]:
        return list(CURVE_CONTRACTS.get(network, {}).values())

    async def index_contracts(self, network: str) -> Dict[str, Any]:
        from liquify_client import IndexRequest
        results = []
        for name, address in CURVE_CONTRACTS.get(network, {}).items():
            try:
                result = await self.client.index_contract(
                    IndexRequest(contract_address=address, network=network)
                )
                results.append({"contract": name, "address": address, "result": result})
            except Exception as e:
                results.append({"contract": name, "address": address, "error": str(e)})
        return {"network": network, "indexed": results}

    async def get_exchanges(
        self,
        wallet_address: str,
        network: str = "ethereum",
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all Curve exchanges for a wallet."""
        exchanges = []
        for contract_name, contract_addr in CURVE_CONTRACTS.get(network, {}).items():
            try:
                txns = await self.client.get_transactions(
                    wallet_address=wallet_address,
                    network=network,
                    contract_address=contract_addr,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp,
                )
                for tx in txns:
                    tx["protocol"] = "curve"
                    tx["pool"] = contract_name
                    exchanges.append(tx)
            except Exception as e:
                print(f"Error fetching Curve {contract_name}: {e}")
        return exchanges

    def classify_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Classify Curve events for tax purposes."""
        event_type = event.get("event", "")
        classifications = {
            "TokenExchange": {
                "taxable": True,
                "type": "swap",
                "note": "Token exchange - taxable disposal",
            },
            "AddLiquidity": {
                "taxable": False,
                "type": "lp_deposit",
                "note": "Adding liquidity - tracks cost basis",
            },
            "RemoveLiquidity": {
                "taxable": True,
                "type": "lp_withdrawal",
                "note": "Removing liquidity - may trigger gain/loss",
            },
            "RemoveLiquidityOne": {
                "taxable": True,
                "type": "lp_withdrawal",
                "note": "Single-sided LP withdrawal - taxable event",
            },
        }
        classification = classifications.get(
            event_type,
            {"taxable": False, "type": "unknown", "note": "Unknown event"},
        )
        return {**event, **classification}
