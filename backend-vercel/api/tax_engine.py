"""
DeFi Tax Engine
Implements FIFO/LIFO/HIFO cost basis accounting for DeFi transactions.
Generates capital gains reports, income summaries, and Form 8949 data.
"""
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from collections import defaultdict
import datetime
import csv
import io


@dataclass
class TaxLot:
    """A single cost-basis lot (purchase of an asset)."""
    asset: str
    amount: Decimal
    cost_basis_usd: Decimal
    acquired_date: datetime.datetime
    tx_hash: str
    protocol: str
    lot_id: str = ""

    @property
    def unit_cost(self) -> Decimal:
        if self.amount == 0:
            return Decimal(0)
        return self.cost_basis_usd / self.amount


@dataclass
class TaxEvent:
    """A taxable disposal event."""
    asset: str
    amount_disposed: Decimal
    proceeds_usd: Decimal
    cost_basis_usd: Decimal
    gain_loss_usd: Decimal
    acquired_date: datetime.datetime
    disposed_date: datetime.datetime
    holding_period: str  # "short" or "long"
    tx_hash: str
    protocol: str
    event_type: str  # "swap", "lp_withdrawal", "liquidation"


@dataclass
class IncomeEvent:
    """An income event (staking rewards, interest, airdrops)."""
    asset: str
    amount: Decimal
    fair_market_value_usd: Decimal
    date: datetime.datetime
    tx_hash: str
    protocol: str
    income_type: str  # "interest", "staking_reward", "airdrop", "liquidity_mining"


class TaxEngine:
    def __init__(self, cost_basis_method: str = "FIFO"):
        """
        Initialize tax engine.
        
        Args:
            cost_basis_method: "FIFO", "LIFO", or "HIFO"
        """
        self.method = cost_basis_method.upper()
        self.lots: Dict[str, List[TaxLot]] = defaultdict(list)  # asset -> lots
        self.tax_events: List[TaxEvent] = []
        self.income_events: List[IncomeEvent] = []

    def add_acquisition(
        self,
        asset: str,
        amount: Decimal,
        cost_basis_usd: Decimal,
        acquired_date: datetime.datetime,
        tx_hash: str,
        protocol: str,
    ) -> TaxLot:
        """Record an asset acquisition (creates a tax lot)."""
        lot = TaxLot(
            asset=asset,
            amount=amount,
            cost_basis_usd=cost_basis_usd,
            acquired_date=acquired_date,
            tx_hash=tx_hash,
            protocol=protocol,
            lot_id=f"{tx_hash[:8]}-{asset}-{len(self.lots[asset])}",
        )
        self.lots[asset].append(lot)
        return lot

    def add_disposal(
        self,
        asset: str,
        amount: Decimal,
        proceeds_usd: Decimal,
        disposed_date: datetime.datetime,
        tx_hash: str,
        protocol: str,
        event_type: str = "swap",
    ) -> List[TaxEvent]:
        """
        Record an asset disposal. Matches against lots using chosen method.
        Returns list of tax events (may be multiple if spanning lots).
        """
        events = []
        remaining = amount
        asset_lots = self.lots.get(asset, [])

        if not asset_lots:
            # No lots — treat as zero cost basis (common for airdrops/mining)
            event = TaxEvent(
                asset=asset,
                amount_disposed=amount,
                proceeds_usd=proceeds_usd,
                cost_basis_usd=Decimal(0),
                gain_loss_usd=proceeds_usd,
                acquired_date=disposed_date,
                disposed_date=disposed_date,
                holding_period="short",
                tx_hash=tx_hash,
                protocol=protocol,
                event_type=event_type,
            )
            self.tax_events.append(event)
            return [event]

        # Sort lots based on method
        sorted_lots = self._sort_lots(asset_lots, proceeds_usd / amount if amount > 0 else Decimal(0))

        for lot in sorted_lots:
            if remaining <= 0:
                break
            if lot.amount <= 0:
                continue

            disposed_amount = min(remaining, lot.amount)
            proportion = disposed_amount / lot.amount if lot.amount > 0 else Decimal(0)
            cost_basis = lot.cost_basis_usd * proportion
            proceeds = proceeds_usd * (disposed_amount / amount) if amount > 0 else Decimal(0)
            gain_loss = proceeds - cost_basis

            # Determine holding period (>1 year = long-term)
            days_held = (disposed_date - lot.acquired_date).days
            holding_period = "long" if days_held > 365 else "short"

            event = TaxEvent(
                asset=asset,
                amount_disposed=disposed_amount,
                proceeds_usd=proceeds,
                cost_basis_usd=cost_basis,
                gain_loss_usd=gain_loss,
                acquired_date=lot.acquired_date,
                disposed_date=disposed_date,
                holding_period=holding_period,
                tx_hash=tx_hash,
                protocol=protocol,
                event_type=event_type,
            )
            events.append(event)
            self.tax_events.append(event)

            # Update lot
            lot.amount -= disposed_amount
            lot.cost_basis_usd -= cost_basis
            remaining -= disposed_amount

        return events

    def add_income(
        self,
        asset: str,
        amount: Decimal,
        fmv_usd: Decimal,
        date: datetime.datetime,
        tx_hash: str,
        protocol: str,
        income_type: str,
    ) -> IncomeEvent:
        """Record an income event (staking, interest, airdrop)."""
        event = IncomeEvent(
            asset=asset,
            amount=amount,
            fair_market_value_usd=fmv_usd,
            date=date,
            tx_hash=tx_hash,
            protocol=protocol,
            income_type=income_type,
        )
        self.income_events.append(event)
        # Also create a lot at FMV cost basis
        self.add_acquisition(
            asset=asset,
            amount=amount,
            cost_basis_usd=fmv_usd,
            acquired_date=date,
            tx_hash=tx_hash,
            protocol=protocol,
        )
        return event

    def _sort_lots(self, lots: List[TaxLot], current_price: Decimal) -> List[TaxLot]:
        """Sort lots based on cost basis method."""
        if self.method == "FIFO":
            return sorted(lots, key=lambda l: l.acquired_date)
        elif self.method == "LIFO":
            return sorted(lots, key=lambda l: l.acquired_date, reverse=True)
        elif self.method == "HIFO":
            # Highest cost basis first (minimizes gains)
            return sorted(lots, key=lambda l: l.unit_cost, reverse=True)
        return lots

    def generate_summary(self, tax_year: Optional[int] = None) -> Dict[str, Any]:
        """Generate a tax summary report."""
        events = self.tax_events
        income = self.income_events

        if tax_year:
            events = [e for e in events if e.disposed_date.year == tax_year]
            income = [e for e in income if e.date.year == tax_year]

        short_term_gains = sum(
            e.gain_loss_usd for e in events if e.holding_period == "short"
        )
        long_term_gains = sum(
            e.gain_loss_usd for e in events if e.holding_period == "long"
        )
        total_income = sum(e.fair_market_value_usd for e in income)

        return {
            "tax_year": tax_year,
            "cost_basis_method": self.method,
            "capital_gains": {
                "short_term": {
                    "total": str(short_term_gains.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                    "events": len([e for e in events if e.holding_period == "short"]),
                },
                "long_term": {
                    "total": str(long_term_gains.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                    "events": len([e for e in events if e.holding_period == "long"]),
                },
                "net_total": str(
                    (short_term_gains + long_term_gains).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                ),
            },
            "income": {
                "total": str(total_income.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "events": len(income),
                "by_type": self._group_income_by_type(income),
            },
            "protocols_used": list(set(e.protocol for e in events + income)),
            "total_transactions": len(events),
        }

    def generate_form_8949(self, tax_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate IRS Form 8949 compatible records."""
        events = self.tax_events
        if tax_year:
            events = [e for e in events if e.disposed_date.year == tax_year]

        rows = []
        for event in events:
            rows.append({
                "description": f"{event.amount_disposed:.6f} {event.asset} ({event.protocol})",
                "date_acquired": event.acquired_date.strftime("%m/%d/%Y"),
                "date_sold": event.disposed_date.strftime("%m/%d/%Y"),
                "proceeds": str(event.proceeds_usd.quantize(Decimal("0.01"))),
                "cost_basis": str(event.cost_basis_usd.quantize(Decimal("0.01"))),
                "gain_loss": str(event.gain_loss_usd.quantize(Decimal("0.01"))),
                "term": "A" if event.holding_period == "short" else "D",  # Part I or Part II
                "tx_hash": event.tx_hash,
            })
        return rows

    def export_csv(self, tax_year: Optional[int] = None) -> str:
        """Export tax events as CSV string."""
        events = self.tax_events
        if tax_year:
            events = [e for e in events if e.disposed_date.year == tax_year]

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "date_sold", "date_acquired", "asset", "amount",
                "proceeds_usd", "cost_basis_usd", "gain_loss_usd",
                "holding_period", "protocol", "event_type", "tx_hash"
            ],
        )
        writer.writeheader()
        for event in events:
            writer.writerow({
                "date_sold": event.disposed_date.strftime("%Y-%m-%d"),
                "date_acquired": event.acquired_date.strftime("%Y-%m-%d"),
                "asset": event.asset,
                "amount": str(event.amount_disposed),
                "proceeds_usd": str(event.proceeds_usd.quantize(Decimal("0.01"))),
                "cost_basis_usd": str(event.cost_basis_usd.quantize(Decimal("0.01"))),
                "gain_loss_usd": str(event.gain_loss_usd.quantize(Decimal("0.01"))),
                "holding_period": event.holding_period,
                "protocol": event.protocol,
                "event_type": event.event_type,
                "tx_hash": event.tx_hash,
            })
        return output.getvalue()

    def _group_income_by_type(self, income: List[IncomeEvent]) -> Dict[str, str]:
        totals: Dict[str, Decimal] = defaultdict(Decimal)
        for event in income:
            totals[event.income_type] += event.fair_market_value_usd
        return {k: str(v.quantize(Decimal("0.01"))) for k, v in totals.items()}
