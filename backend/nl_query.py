"""
Natural Language Query Parser
Converts user NL questions into structured Liquify API queries.
Uses Claude for intent parsing and query generation.
"""
import os
import json
import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


class ParsedQuery(BaseModel):
    intent: str  # "tax_report", "trade_history", "income_events", "portfolio"
    wallet_address: Optional[str] = None
    networks: List[str] = ["ethereum"]
    protocols: List[str] = []  # uniswap, aave, curve
    tax_year: Optional[int] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    cost_basis_method: str = "FIFO"  # FIFO, LIFO, HIFO
    report_format: str = "summary"  # summary, detailed, csv, form8949
    raw_query: str = ""


SYSTEM_PROMPT = """You are a DeFi tax assistant that parses natural language queries into structured JSON.

Extract the following from the user's query:
- intent: one of "tax_report", "trade_history", "income_events", "portfolio_summary"
- wallet_address: Ethereum address (0x...) if mentioned
- networks: list of blockchain networks (ethereum, polygon, arbitrum, optimism, avalanche)
- protocols: list of DeFi protocols mentioned (uniswap, aave, curve, compound, maker)
- tax_year: year (e.g., 2024, 2023)
- from_date: start date in YYYY-MM-DD format
- to_date: end date in YYYY-MM-DD format
- cost_basis_method: FIFO, LIFO, or HIFO (default FIFO)
- report_format: "summary", "detailed", "csv", or "form8949"

Always respond with valid JSON only. No markdown, no explanation.

Example input: "Show me all my Uniswap trades from 2024 and calculate capital gains for wallet 0xabc123"
Example output:
{
  "intent": "tax_report",
  "wallet_address": "0xabc123",
  "networks": ["ethereum"],
  "protocols": ["uniswap"],
  "tax_year": 2024,
  "from_date": "2024-01-01",
  "to_date": "2024-12-31",
  "cost_basis_method": "FIFO",
  "report_format": "summary"
}"""


class NLQueryParser:
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or ANTHROPIC_API_KEY
        )

    def parse(self, user_query: str) -> ParsedQuery:
        """Parse a natural language query into a structured query."""
        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_query}
                ],
            )
            raw = message.content[0].text.strip()
            # Strip markdown code blocks if present
            raw = re.sub(r"```(?:json)?\n?", "", raw).strip()
            data = json.loads(raw)
            data["raw_query"] = user_query
            return ParsedQuery(**data)
        except Exception as e:
            # Fallback: basic extraction
            return self._fallback_parse(user_query)

    def _fallback_parse(self, query: str) -> ParsedQuery:
        """Simple regex-based fallback parser."""
        query_lower = query.lower()
        
        # Extract wallet address
        wallet_match = re.search(r"0x[a-fA-F0-9]{40}", query)
        wallet = wallet_match.group(0) if wallet_match else None

        # Extract year
        year_match = re.search(r"\b(202[0-9])\b", query)
        year = int(year_match.group(1)) if year_match else None

        # Detect protocols
        protocols = []
        if "uniswap" in query_lower:
            protocols.append("uniswap")
        if "aave" in query_lower:
            protocols.append("aave")
        if "curve" in query_lower:
            protocols.append("curve")

        # Detect networks
        networks = ["ethereum"]
        if "polygon" in query_lower or "matic" in query_lower:
            networks.append("polygon")
        if "arbitrum" in query_lower:
            networks.append("arbitrum")

        # Detect intent
        intent = "tax_report"
        if "portfolio" in query_lower or "balance" in query_lower:
            intent = "portfolio_summary"
        elif "income" in query_lower or "reward" in query_lower or "airdrop" in query_lower:
            intent = "income_events"
        elif "trade" in query_lower or "swap" in query_lower:
            intent = "trade_history"

        # Cost basis method
        cost_basis = "FIFO"
        if "lifo" in query_lower:
            cost_basis = "LIFO"
        elif "hifo" in query_lower:
            cost_basis = "HIFO"

        # Report format
        fmt = "summary"
        if "csv" in query_lower:
            fmt = "csv"
        elif "8949" in query_lower or "form" in query_lower:
            fmt = "form8949"
        elif "detail" in query_lower:
            fmt = "detailed"

        return ParsedQuery(
            intent=intent,
            wallet_address=wallet,
            networks=networks,
            protocols=protocols if protocols else ["uniswap", "aave", "curve"],
            tax_year=year,
            from_date=f"{year}-01-01" if year else None,
            to_date=f"{year}-12-31" if year else None,
            cost_basis_method=cost_basis,
            report_format=fmt,
            raw_query=query,
        )


_parser: Optional[NLQueryParser] = None


def get_parser() -> NLQueryParser:
    global _parser
    if _parser is None:
        _parser = NLQueryParser()
    return _parser
