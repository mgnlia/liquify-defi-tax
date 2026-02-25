"""
Aave V2/V3 Protocol Adapter
Indexes deposit, borrow, repay events for DeFi income tax reporting.
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
import datetime

AAVE_CONTRACTS = {
    "ethereum": {
        "v3_pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "v2_lending_pool": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
        "v3_pool_data_provider": "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3",
    },
    "polygon": {
        "v3_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    },
    "avalanche": {
        "v3_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    },
}

# Aave V3 events relevant for tax
AAVE_TAX_EVENTS = [
    "Supply",
    "Withdraw",
    "Borrow",
    "Repay",
    "LiquidationCall",
    "ReserveDataUpdated",  # For interest income tracking
]


class AaveEvent:
    def __init__(
        self,
        event_type: str,
        tx_hash: str,
        timestamp: datetime.datetime,
        user: str,
        asset: str,
        amount: Decimal,
        amount_usd: Decimal,
        network: str,
        version: str = "v3",
        is_taxable: bool = False,
        income_type: Optional[str] = None,
    ):
        self.event_type = event_type
        self.tx_hash = tx_hash
        self.timestamp = timestamp
        self.user = user
        self.asset = asset
        self.amount = amount
        self.amount_usd = amount_usd
        self.network = network
        self.version = version
        self.is_taxable = is_taxable
        self.income_type = income_type  # "interest_income", "liquidation_loss"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "tx_hash": self.tx_hash,
            "timestamp": self.timestamp.isoformat(),
            "user": self.user,
            "asset": self.asset,
            "amount": str(self.amount),
            "amount_usd": str(self.amount_usd),
            "network": self.network,
            "version": self.version,
            "is_taxable": self.is_taxable,
            "income_type": self.income_type,
            "protocol": "aave",
        }


class AaveAdapter:
    def __init__(self, liquify_client):
        self.client = liquify_client

    def get_contracts(self, network: str) -> List[str]:
        return list(AAVE_CONTRACTS.get(network, {}).values())

    async def index_contracts(self, network: str) -> Dict[str, Any]:
        from liquify_client import IndexRequest
        results = []
        for name, address in AAVE_CONTRACTS.get(network, {}).items():
            try:
                result = await self.client.index_contract(
                    IndexRequest(contract_address=address, network=network)
                )
                results.append({"contract": name, "address": address, "result": result})
            except Exception as e:
                results.append({"contract": name, "address": address, "error": str(e)})
        return {"network": network, "indexed": results}

    async def get_user_events(
        self,
        wallet_address: str,
        network: str = "ethereum",
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all Aave events for a user wallet."""
        events = []
        for contract_name, contract_addr in AAVE_CONTRACTS.get(network, {}).items():
            try:
                txns = await self.client.get_transactions(
                    wallet_address=wallet_address,
                    network=network,
                    contract_address=contract_addr,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp,
                )
                for tx in txns:
                    tx["protocol"] = "aave"
                    tx["contract_name"] = contract_name
                    events.append(tx)
            except Exception as e:
                print(f"Error fetching Aave {contract_name}: {e}")
        return events

    def classify_tax_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Classify whether an Aave event is taxable and what type."""
        event_type = event.get("event", "")

        tax_classification = {
            "Supply": {"taxable": False, "type": None, "note": "Deposit - not taxable"},
            "Withdraw": {"taxable": False, "type": None, "note": "Withdrawal - not taxable"},
            "Borrow": {"taxable": False, "type": None, "note": "Borrowing - not taxable"},
            "Repay": {"taxable": False, "type": None, "note": "Repayment - not taxable"},
            "LiquidationCall": {
                "taxable": True,
                "type": "liquidation_loss",
                "note": "Liquidation - capital loss event",
            },
        }

        classification = tax_classification.get(
            event_type,
            {"taxable": False, "type": None, "note": "Unknown event"},
        )
        return {**event, **classification}
