#!/usr/bin/env python3
"""
Comprehensive P&L Monitoring and Accounting System
Transaction-level logging, per-trade P&L, fees, slippage tracking
Automated reconciliation and tax reporting support
"""

import time
import json
import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    """Complete record of a single trade"""
    trade_id: str
    timestamp: str
    block_number: int
    transaction_hash: str
    
    # Trade details
    strategy: str  # e.g., "triangular_arbitrage", "flashloan_arb"
    protocol: str  # e.g., "uniswap", "sushiswap"
    token_path: List[str]
    
    # Amounts
    amount_in: float
    amount_in_token: str
    amount_out: float
    amount_out_token: str
    
    # Pricing
    entry_price: float
    exit_price: float
    expected_price: float
    
    # Costs
    gas_used: int
    gas_price_gwei: float
    gas_cost_usd: float
    flashloan_fee_usd: float
    protocol_fees_usd: float
    slippage_cost_usd: float
    
    # P&L
    gross_profit_usd: float
    net_profit_usd: float
    # ROI is calculated as (net_profit_usd / amount_in) * 100
    roi_percent: float
    
    # Execution
    execution_time_ms: float
    slippage_percent: float
    market_impact_percent: float
    
    # Status
    success: bool
    revert_reason: Optional[str] = None
    
    # Additional context
    chain: str = "ethereum"
    wallet_address: str = ""
    notes: str = ""

class PnLAccountingSystem:
    """
    Comprehensive P&L monitoring and accounting system
    """
    
    def __init__(self, data_dir: str = "data/accounting"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory trade storage
        self.trades: List[TradeRecord] = []
        self.trades_by_date: Dict[str, List[TradeRecord]] = defaultdict(list)
        self.trades_by_strategy: Dict[str, List[TradeRecord]] = defaultdict(list)
        
        # Aggregated metrics
        self.daily_pnl: Dict[str, float] = defaultdict(float)
        self.monthly_pnl: Dict[str, float] = defaultdict(float)
        self.yearly_pnl: Dict[str, float] = defaultdict(float)
        
        # Cost tracking
        self.total_gas_cost_usd = 0.0
        self.total_fees_usd = 0.0
        self.total_slippage_cost_usd = 0.0
        
        # Tax reporting
        self.taxable_events: List[Dict] = []
        
        # Load existing data
        self._load_existing_data()
        
        logger.info(f"PnLAccountingSystem initialized with data dir: {self.data_dir}")
    
    def record_trade(self, trade: TradeRecord):
        """
        Record a new trade in the accounting system
        
        Args:
            trade: TradeRecord object with complete trade information
        """
        # Add to in-memory storage
        self.trades.append(trade)
        
        # Index by date
        trade_date = trade.timestamp.split('T')[0]
        self.trades_by_date[trade_date].append(trade)
        
        # Index by strategy
        self.trades_by_strategy[trade.strategy].append(trade)
        
        # Update aggregated metrics
        self._update_aggregated_metrics(trade)
        
        # Update cost tracking
        if trade.success:
            self.total_gas_cost_usd += trade.gas_cost_usd
            self.total_fees_usd += trade.flashloan_fee_usd + trade.protocol_fees_usd
            self.total_slippage_cost_usd += trade.slippage_cost_usd
        
        # Record taxable event if applicable
        if trade.success and trade.net_profit_usd > 0:
            self._record_taxable_event(trade)
        
        # Persist to disk
        self._save_trade_to_disk(trade)
        
        logger.info(
            f"Trade recorded: {trade.trade_id} | "
            f"{'✓' if trade.success else '✗'} | "
            f"Net P&L: ${trade.net_profit_usd:.2f}"
        )
    
    def _update_aggregated_metrics(self, trade: TradeRecord):
        """Update daily, monthly, and yearly P&L aggregations"""
        if not trade.success:
            return
        
        # Parse date
        dt = datetime.fromisoformat(trade.timestamp.replace('Z', '+00:00'))
        
        # Daily
        day_key = dt.strftime('%Y-%m-%d')
        self.daily_pnl[day_key] += trade.net_profit_usd
        
        # Monthly
        month_key = dt.strftime('%Y-%m')
        self.monthly_pnl[month_key] += trade.net_profit_usd
        
        # Yearly
        year_key = dt.strftime('%Y')
        self.yearly_pnl[year_key] += trade.net_profit_usd
    
    def _record_taxable_event(self, trade: TradeRecord):
        """Record a taxable event for tax reporting"""
        event = {
            "date": trade.timestamp,
            "type": "trading_income",
            "description": f"Arbitrage trade {trade.trade_id}",
            "income_usd": trade.net_profit_usd,
            "transaction_hash": trade.transaction_hash,
            "tokens": f"{trade.token_path[0]} -> {trade.token_path[-1]}"
        }
        self.taxable_events.append(event)
    
    def _save_trade_to_disk(self, trade: TradeRecord):
        """Save trade to disk in multiple formats"""
        trade_date = trade.timestamp.split('T')[0]
        
        # JSON format (detailed)
        json_file = self.data_dir / f"trades_{trade_date}.jsonl"
        with open(json_file, 'a') as f:
            f.write(json.dumps(asdict(trade)) + '\n')
        
        # CSV format (for spreadsheet analysis)
        csv_file = self.data_dir / f"trades_{trade_date}.csv"
        
        # Check if file exists to write header
        write_header = not csv_file.exists()
        
        with open(csv_file, 'a', newline='') as f:
            if write_header:
                writer = csv.DictWriter(f, fieldnames=asdict(trade).keys())
                writer.writeheader()
                writer.writerow(asdict(trade))
            else:
                writer = csv.DictWriter(f, fieldnames=asdict(trade).keys())
                writer.writerow(asdict(trade))
    
    def _load_existing_data(self):
        """Load existing trade data from disk"""
        if not self.data_dir.exists():
            return
        
        # Load JSONL files
        for json_file in self.data_dir.glob("trades_*.jsonl"):
            try:
                with open(json_file, 'r') as f:
                    for line in f:
                        trade_dict = json.loads(line)
                        trade = TradeRecord(**trade_dict)
                        self.trades.append(trade)
                        
                        # Update indices
                        trade_date = trade.timestamp.split('T')[0]
                        self.trades_by_date[trade_date].append(trade)
                        self.trades_by_strategy[trade.strategy].append(trade)
                        
                        # Update metrics
                        self._update_aggregated_metrics(trade)
                
                logger.info(f"Loaded trades from {json_file}")
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
    
    def get_daily_pnl(self, date: Optional[str] = None) -> float:
        """
        Get P&L for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            float: Net P&L for the date
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return self.daily_pnl.get(date, 0.0)
    
    def get_monthly_pnl(self, month: Optional[str] = None) -> float:
        """
        Get P&L for a specific month
        
        Args:
            month: Month in YYYY-MM format (defaults to current month)
            
        Returns:
            float: Net P&L for the month
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        return self.monthly_pnl.get(month, 0.0)
    
    def get_yearly_pnl(self, year: Optional[str] = None) -> float:
        """
        Get P&L for a specific year
        
        Args:
            year: Year in YYYY format (defaults to current year)
            
        Returns:
            float: Net P&L for the year
        """
        if year is None:
            year = datetime.now().strftime('%Y')
        
        return self.yearly_pnl.get(year, 0.0)
    
    def get_pnl_summary(self, period: str = "all") -> Dict:
        """
        Get comprehensive P&L summary
        
        Args:
            period: "today", "week", "month", "year", or "all"
            
        Returns:
            dict: P&L summary with various metrics
        """
        # Filter trades by period
        if period == "today":
            cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            cutoff = datetime.now() - timedelta(days=7)
        elif period == "month":
            cutoff = datetime.now() - timedelta(days=30)
        elif period == "year":
            cutoff = datetime.now() - timedelta(days=365)
        else:
            cutoff = datetime.min
        
        # Filter trades
        filtered_trades = [
            t for t in self.trades
            if datetime.fromisoformat(t.timestamp.replace('Z', '+00:00')) >= cutoff
        ]
        
        # Calculate metrics
        successful_trades = [t for t in filtered_trades if t.success]
        failed_trades = [t for t in filtered_trades if not t.success]
        
        if not filtered_trades:
            return {
                "period": period,
                "total_trades": 0,
                "message": "No trades in this period"
            }
        
        total_gross_profit = sum(t.gross_profit_usd for t in successful_trades)
        total_net_profit = sum(t.net_profit_usd for t in successful_trades)
        total_gas_cost = sum(t.gas_cost_usd for t in successful_trades)
        total_fees = sum(t.flashloan_fee_usd + t.protocol_fees_usd for t in successful_trades)
        total_slippage = sum(t.slippage_cost_usd for t in successful_trades)
        
        avg_net_profit = total_net_profit / len(successful_trades) if successful_trades else 0
        avg_roi = sum(t.roi_percent for t in successful_trades) / len(successful_trades) if successful_trades else 0
        
        # Best and worst trades
        best_trade = max(successful_trades, key=lambda t: t.net_profit_usd) if successful_trades else None
        worst_trade = min(successful_trades, key=lambda t: t.net_profit_usd) if successful_trades else None
        
        return {
            "period": period,
            "total_trades": len(filtered_trades),
            "successful_trades": len(successful_trades),
            "failed_trades": len(failed_trades),
            "success_rate": f"{(len(successful_trades) / len(filtered_trades)) * 100:.1f}%",
            
            "gross_profit_usd": round(total_gross_profit, 2),
            "net_profit_usd": round(total_net_profit, 2),
            "avg_net_profit_usd": round(avg_net_profit, 2),
            "avg_roi_percent": round(avg_roi, 2),
            
            "total_costs": {
                "gas_usd": round(total_gas_cost, 2),
                "fees_usd": round(total_fees, 2),
                "slippage_usd": round(total_slippage, 2),
                "total_usd": round(total_gas_cost + total_fees + total_slippage, 2)
            },
            
            "best_trade": {
                "trade_id": best_trade.trade_id if best_trade else None,
                "net_profit_usd": round(best_trade.net_profit_usd, 2) if best_trade else 0,
                "roi_percent": round(best_trade.roi_percent, 2) if best_trade else 0
            },
            
            "worst_trade": {
                "trade_id": worst_trade.trade_id if worst_trade else None,
                "net_profit_usd": round(worst_trade.net_profit_usd, 2) if worst_trade else 0,
                "roi_percent": round(worst_trade.roi_percent, 2) if worst_trade else 0
            }
        }
    
    def get_strategy_performance(self) -> Dict:
        """Get performance breakdown by strategy"""
        performance = {}
        
        for strategy, trades in self.trades_by_strategy.items():
            successful = [t for t in trades if t.success]
            
            if successful:
                total_profit = sum(t.net_profit_usd for t in successful)
                avg_profit = total_profit / len(successful)
                success_rate = len(successful) / len(trades) * 100
                
                performance[strategy] = {
                    "total_trades": len(trades),
                    "successful_trades": len(successful),
                    "success_rate": f"{success_rate:.1f}%",
                    "total_profit_usd": round(total_profit, 2),
                    "avg_profit_usd": round(avg_profit, 2)
                }
        
        return performance
    
    def generate_tax_report(self, year: str) -> Dict:
        """
        Generate tax report for a specific year
        
        Args:
            year: Year in YYYY format
            
        Returns:
            dict: Tax report with income breakdown
        """
        # Filter taxable events for the year
        year_events = [
            e for e in self.taxable_events
            if e["date"].startswith(year)
        ]
        
        total_income = sum(e["income_usd"] for e in year_events)
        
        # Group by month
        monthly_income = defaultdict(float)
        for event in year_events:
            month = event["date"][:7]  # YYYY-MM
            monthly_income[month] += event["income_usd"]
        
        return {
            "year": year,
            "total_taxable_income_usd": round(total_income, 2),
            "total_events": len(year_events),
            "monthly_breakdown": {
                month: round(income, 2)
                for month, income in sorted(monthly_income.items())
            },
            "notes": [
                "This is for reference only and not tax advice",
                "Consult with a tax professional for accurate filing",
                "Keep all transaction records for audit purposes"
            ]
        }
    
    def export_to_csv(self, filename: str, period: str = "all"):
        """
        Export trades to CSV file
        
        Args:
            filename: Output CSV filename
            period: Period to export ("today", "week", "month", "year", "all")
        """
        # Get trades for period
        summary = self.get_pnl_summary(period)
        
        if period == "today":
            cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            cutoff = datetime.now() - timedelta(days=7)
        elif period == "month":
            cutoff = datetime.now() - timedelta(days=30)
        elif period == "year":
            cutoff = datetime.now() - timedelta(days=365)
        else:
            cutoff = datetime.min
        
        filtered_trades = [
            t for t in self.trades
            if datetime.fromisoformat(t.timestamp.replace('Z', '+00:00')) >= cutoff
        ]
        
        # Write to CSV
        with open(filename, 'w', newline='') as f:
            if filtered_trades:
                writer = csv.DictWriter(f, fieldnames=asdict(filtered_trades[0]).keys())
                writer.writeheader()
                for trade in filtered_trades:
                    writer.writerow(asdict(trade))
        
        logger.info(f"Exported {len(filtered_trades)} trades to {filename}")
    
    def reconcile(self) -> Dict:
        """
        Perform reconciliation to verify data consistency
        
        Returns:
            dict: Reconciliation report
        """
        # Calculate totals from individual trades
        calculated_total = sum(t.net_profit_usd for t in self.trades if t.success)
        
        # Compare with aggregated totals
        aggregated_total = sum(self.yearly_pnl.values())
        
        difference = abs(calculated_total - aggregated_total)
        
        report = {
            "reconciliation_date": datetime.now().isoformat(),
            "total_trades": len(self.trades),
            "calculated_total_pnl": round(calculated_total, 2),
            "aggregated_total_pnl": round(aggregated_total, 2),
            "difference": round(difference, 2),
            "reconciled": difference < 0.01  # Within 1 cent
        }
        
        if not report["reconciled"]:
            logger.warning(f"Reconciliation mismatch: ${difference:.2f}")
        else:
            logger.info("Reconciliation successful: All totals match")
        
        return report

# Global accounting instance
_global_accounting = None

def get_accounting():
    """Get global accounting instance"""
    global _global_accounting
    if _global_accounting is None:
        _global_accounting = PnLAccountingSystem()
    return _global_accounting

if __name__ == "__main__":
    # Test P&L accounting system
    print("Testing P&L Accounting System\n")
    print("=" * 80)
    
    accounting = PnLAccountingSystem(data_dir="data/accounting_test")
    
    # Create sample trades
    for i in range(10):
        trade = TradeRecord(
            trade_id=f"trade_{i+1}",
            timestamp=datetime.now().isoformat(),
            block_number=18000000 + i,
            transaction_hash=f"0x{'a'*64}",
            strategy="triangular_arbitrage" if i % 2 == 0 else "flashloan_arb",
            protocol="uniswap" if i % 3 == 0 else "sushiswap",
            token_path=["USDC", "WETH", "DAI", "USDC"],
            amount_in=10000.0 + i * 1000,
            amount_in_token="USDC",
            amount_out=10050.0 + i * 1000,
            amount_out_token="USDC",
            entry_price=1.0,
            exit_price=1.005,
            expected_price=1.004,
            gas_used=250000,
            gas_price_gwei=50.0 + i,
            gas_cost_usd=25.0 + i,
            flashloan_fee_usd=9.0 + i,
            protocol_fees_usd=3.0,
            slippage_cost_usd=2.0,
            gross_profit_usd=50.0 + i * 5,
            net_profit_usd=11.0 + i * 3,
            roi_percent=0.11 + i * 0.03,
            execution_time_ms=150.0 + i * 10,
            slippage_percent=0.1 + i * 0.01,
            market_impact_percent=0.2 + i * 0.02,
            success=i % 5 != 0,  # 80% success rate
            revert_reason="Insufficient liquidity" if i % 5 == 0 else None,
            chain="ethereum",
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        )
        
        accounting.record_trade(trade)
    
    # Print summary
    print("\n" + "=" * 80)
    print("P&L Summary (All Time)")
    print("=" * 80)
    summary = accounting.get_pnl_summary("all")
    print(json.dumps(summary, indent=2))
    
    print("\n" + "=" * 80)
    print("Strategy Performance")
    print("=" * 80)
    strategy_perf = accounting.get_strategy_performance()
    print(json.dumps(strategy_perf, indent=2))
    
    print("\n" + "=" * 80)
    print("Reconciliation")
    print("=" * 80)
    reconciliation = accounting.reconcile()
    print(json.dumps(reconciliation, indent=2))
    
    print("\n" + "=" * 80)
    print("Test complete. Data saved to: data/accounting_test/")
