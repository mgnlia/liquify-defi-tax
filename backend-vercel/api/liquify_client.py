"""
Liquify Indexer API Client
Handles contract indexing, event queries, and transaction history.
"""
import os
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

LIQUIFY_BASE_URL = os.getenv("LIQUIFY_BASE_URL", "https://api.liquify.io/v1")
LIQUIFY_API_KEY = os.getenv("LIQUIFY_API_KEY", "")


class IndexRequest(BaseModel):
    contract_address: str
    network: str  # ethereum, polygon, arbitrum, optimism, avalanche
    abi: Optional[list] = None
    start_block: Optional[int] = None


class EventQuery(BaseModel):
    contract_address: str
    network: str
    event_name: Optional[str] = None
    from_block: Optional[int] = None
    to_block: Optional[int] = None
    wallet_address: Optional[str] = None
    limit: int = 1000


class LiquifyClient:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or LIQUIFY_API_KEY
        self.base_url = base_url or LIQUIFY_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def index_contract(self, request: IndexRequest) -> Dict[str, Any]:
        """Register a contract for instant indexing."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/index",
                headers=self.headers,
                json=request.model_dump(exclude_none=True),
            )
            response.raise_for_status()
            return response.json()

    async def query_events(self, query: EventQuery) -> List[Dict[str, Any]]:
        """Query indexed events for a contract."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            params = {k: v for k, v in query.model_dump().items() if v is not None}
            response = await client.get(
                f"{self.base_url}/events",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("events", data if isinstance(data, list) else [])

    async def get_transactions(
        self,
        wallet_address: str,
        network: str,
        contract_address: Optional[str] = None,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all transactions for a wallet, optionally filtered by contract."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            params = {
                "wallet": wallet_address,
                "network": network,
            }
            if contract_address:
                params["contract"] = contract_address
            if from_timestamp:
                params["from_ts"] = from_timestamp
            if to_timestamp:
                params["to_ts"] = to_timestamp

            response = await client.get(
                f"{self.base_url}/transactions",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("transactions", data if isinstance(data, list) else [])

    async def get_token_prices(
        self,
        token_addresses: List[str],
        network: str,
        timestamps: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Get historical token prices for tax calculations."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/prices",
                headers=self.headers,
                json={
                    "tokens": token_addresses,
                    "network": network,
                    "timestamps": timestamps or [],
                },
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> Dict[str, Any]:
        """Check API connectivity."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self.headers,
                )
                return {"status": "ok", "code": response.status_code}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Singleton client
_client: Optional[LiquifyClient] = None


def get_liquify_client() -> LiquifyClient:
    global _client
    if _client is None:
        _client = LiquifyClient()
    return _client
