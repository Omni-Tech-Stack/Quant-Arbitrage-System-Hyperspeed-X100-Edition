#!/usr/bin/env python3
"""
Comprehensive Observability and Metrics System
Tracks latency, success rate, P&L per trade, gas usage, and failed transactions
Provides structured logging and metrics export
"""

import time
import json
import logging
import os
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Optional

def setup_logging():
    """
    Configures logging for the observability module.
    Log level and log file can be set via environment variables:
    - OBSERVABILITY_LOG_LEVEL (default: INFO)
    - OBSERVABILITY_LOG_FILE (default: logs/observability.log)
    """
    log_level = os.environ.get("OBSERVABILITY_LOG_LEVEL", "INFO").upper()
    log_file = os.environ.get("OBSERVABILITY_LOG_FILE", "logs/observability.log")
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        handlers=handlers
    )

logger = logging.getLogger(__name__)

class ObservabilityMetrics:
    """
    Comprehensive metrics collection for arbitrage system
    Tracks performance, profitability, and operational metrics
    """
    
    def __init__(self):
        # Performance metrics
        self.latency_metrics = {
            "opportunity_detection": deque(maxlen=1000),
            "trade_execution": deque(maxlen=1000),
            "blockchain_confirmation": deque(maxlen=1000),
            "total_trade_time": deque(maxlen=1000)
        }
        
        # Success metrics
        self.trade_outcomes = {
            "successful": 0,
            "failed": 0,
            "reverted": 0,
            "timeout": 0
        }
        
        # Financial metrics
        self.pnl_metrics = {
            "total_profit_usd": 0.0,
            "total_loss_usd": 0.0,
            "total_gas_cost_usd": 0.0,
            "total_flashloan_fees_usd": 0.0,
            "net_profit_usd": 0.0,
            "trades_profitable": 0,
            "trades_unprofitable": 0
        }
        
        # Per-trade history
        self.trade_history = deque(maxlen=10000)
        
        # Gas metrics
        self.gas_metrics = {
            "total_gas_used": 0,
            "avg_gas_price_gwei": 0.0,
            "max_gas_price_gwei": 0.0,
            "min_gas_price_gwei": None
        }
        
        # Protocol-specific metrics
        self.protocol_metrics = defaultdict(lambda: {
            "trades": 0,
            "successes": 0,
            "failures": 0,
            "total_profit": 0.0
        })
        
        # Time-based aggregations
        self.hourly_stats = defaultdict(lambda: {
            "trades": 0,
            "profit": 0.0,
            "gas_cost": 0.0
        })
        
        # Error tracking
        self.error_counts = defaultdict(int)
        self.recent_errors = deque(maxlen=100)
        
        # Anomaly detection
        self.anomalies = deque(maxlen=100)
        
        # Start time
        self.start_time = time.time()
    
    def record_trade_start(self, trade_id: str, trade_data: Dict):
        """Record the start of a trade"""
        trade_data["trade_id"] = trade_id
        trade_data["start_time"] = time.time()
        trade_data["start_timestamp"] = datetime.now().isoformat()
        
        logger.info(f"Trade {trade_id} started", extra=trade_data)
        return trade_data
    
    def record_trade_complete(self, trade_data: Dict):
        """Record completion of a trade with full metrics"""
        end_time = time.time()
        start_time = trade_data.get("start_time", end_time)
        duration = end_time - start_time
        
        trade_data["end_time"] = end_time
        trade_data["end_timestamp"] = datetime.now().isoformat()
        trade_data["duration_seconds"] = duration
        
        # Update latency metrics
        self.latency_metrics["total_trade_time"].append(duration)
        
        # Update success metrics
        success = trade_data.get("success", False)
        status = trade_data.get("status", "unknown")
        
        if success:
            self.trade_outcomes["successful"] += 1
        elif status == "reverted":
            self.trade_outcomes["reverted"] += 1
        elif status == "timeout":
            self.trade_outcomes["timeout"] += 1
        else:
            self.trade_outcomes["failed"] += 1
        
        # Update financial metrics
        profit = trade_data.get("profit_usd", 0.0)
        gas_cost = trade_data.get("gas_cost_usd", 0.0)
        flashloan_fee = trade_data.get("flashloan_fee_usd", 0.0)
        
        if profit > 0:
            self.pnl_metrics["total_profit_usd"] += profit
            self.pnl_metrics["trades_profitable"] += 1
        else:
            self.pnl_metrics["total_loss_usd"] += abs(profit)
            self.pnl_metrics["trades_unprofitable"] += 1
        
        self.pnl_metrics["total_gas_cost_usd"] += gas_cost
        self.pnl_metrics["total_flashloan_fees_usd"] += flashloan_fee
        self.pnl_metrics["net_profit_usd"] = (
            self.pnl_metrics["total_profit_usd"] 
            - self.pnl_metrics["total_loss_usd"] 
            - self.pnl_metrics["total_gas_cost_usd"]
            - self.pnl_metrics["total_flashloan_fees_usd"]
        )
        
        # Update gas metrics
        gas_price = trade_data.get("gas_price_gwei", 0)
        gas_used = trade_data.get("gas_used", 0)
        
        if gas_used > 0:
            self.gas_metrics["total_gas_used"] += gas_used
            
        if gas_price > 0:
            self.gas_metrics["max_gas_price_gwei"] = max(
                self.gas_metrics["max_gas_price_gwei"], gas_price
            )
            self.gas_metrics["min_gas_price_gwei"] = min(
                self.gas_metrics["min_gas_price_gwei"], gas_price
            )
        
        # Update protocol metrics
        protocol = trade_data.get("protocol", "unknown")
        self.protocol_metrics[protocol]["trades"] += 1
        if success:
            self.protocol_metrics[protocol]["successes"] += 1
            self.protocol_metrics[protocol]["total_profit"] += profit
        else:
            self.protocol_metrics[protocol]["failures"] += 1
        
        # Update hourly stats
        hour_key = datetime.now().strftime("%Y-%m-%d %H:00")
        self.hourly_stats[hour_key]["trades"] += 1
        self.hourly_stats[hour_key]["profit"] += profit
        self.hourly_stats[hour_key]["gas_cost"] += gas_cost
        
        # Store in history
        self.trade_history.append(trade_data)
        
        # Log completion
        logger.info(
            f"Trade {trade_data.get('trade_id')} completed: "
            f"success={success}, profit=${profit:.2f}, gas=${gas_cost:.2f}, "
            f"duration={duration:.2f}s",
            extra=trade_data
        )
        
        # Check for anomalies
        self._check_anomalies(trade_data)
    
    def record_latency(self, metric_name: str, duration_ms: float):
        """Record latency for a specific operation"""
        if metric_name in self.latency_metrics:
            self.latency_metrics[metric_name].append(duration_ms)
            logger.debug(f"Latency recorded: {metric_name} = {duration_ms:.2f}ms")
    
    def record_error(self, error_type: str, error_message: str, context: Dict = None):
        """Record an error occurrence"""
        self.error_counts[error_type] += 1
        
        error_data = {
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self.recent_errors.append(error_data)
        logger.error(f"Error recorded: {error_type} - {error_message}", extra=error_data)
    
    def _check_anomalies(self, trade_data: Dict):
        """Detect anomalies in trade data"""
        anomalies_found = []
        
        # Check for unusual profit/loss
        profit = trade_data.get("profit_usd", 0)
        if abs(profit) > 1000:  # More than $1000 profit/loss
            anomalies_found.append({
                "type": "unusual_profit_loss",
                "value": profit,
                "trade_id": trade_data.get("trade_id")
            })
        
        # Check for high gas cost
        gas_cost = trade_data.get("gas_cost_usd", 0)
        if gas_cost > 200:  # More than $200 in gas
            anomalies_found.append({
                "type": "high_gas_cost",
                "value": gas_cost,
                "trade_id": trade_data.get("trade_id")
            })
        
        # Check for high slippage
        slippage = trade_data.get("actual_slippage_percent", 0)
        if slippage > 5.0:  # More than 5% slippage
            anomalies_found.append({
                "type": "high_slippage",
                "value": slippage,
                "trade_id": trade_data.get("trade_id")
            })
        
        # Check for slow execution
        duration = trade_data.get("duration_seconds", 0)
        if duration > 60:  # More than 60 seconds
            anomalies_found.append({
                "type": "slow_execution",
                "value": duration,
                "trade_id": trade_data.get("trade_id")
            })
        
        for anomaly in anomalies_found:
            anomaly["timestamp"] = datetime.now().isoformat()
            self.anomalies.append(anomaly)
            logger.warning(f"Anomaly detected: {anomaly['type']}", extra=anomaly)
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        total = sum(self.trade_outcomes.values())
        if total == 0:
            return 0.0
        return (self.trade_outcomes["successful"] / total) * 100
    
    def get_avg_latency(self, metric_name: str) -> float:
        """Get average latency for a metric"""
        if metric_name not in self.latency_metrics:
            return 0.0
        
        values = self.latency_metrics[metric_name]
        if not values:
            return 0.0
        
        return sum(values) / len(values)
    
    def get_percentile_latency(self, metric_name: str, percentile: float) -> float:
        """Get percentile latency (e.g., p95, p99)"""
        if metric_name not in self.latency_metrics:
            return 0.0
        
        values = sorted(self.latency_metrics[metric_name])
        if not values:
            return 0.0
        
        index = int(len(values) * (percentile / 100))
        return values[min(index, len(values) - 1)]
    
    def get_metrics_summary(self) -> Dict:
        """Get comprehensive metrics summary"""
        uptime = time.time() - self.start_time
        total_trades = sum(self.trade_outcomes.values())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            
            # Trade outcomes
            "trade_outcomes": dict(self.trade_outcomes),
            "total_trades": total_trades,
            "success_rate_percent": self.get_success_rate(),
            
            # Latency metrics
            "latency": {
                name: {
                    "avg_ms": self.get_avg_latency(name),
                    "p50_ms": self.get_percentile_latency(name, 50),
                    "p95_ms": self.get_percentile_latency(name, 95),
                    "p99_ms": self.get_percentile_latency(name, 99)
                }
                for name in self.latency_metrics.keys()
            },
            
            # Financial metrics
            "pnl": dict(self.pnl_metrics),
            
            # Gas metrics
            "gas": dict(self.gas_metrics),
            
            # Protocol breakdown
            "protocols": dict(self.protocol_metrics),
            
            # Error rates
            "errors": {
                "total_errors": sum(self.error_counts.values()),
                "error_types": dict(self.error_counts),
                "error_rate_percent": (sum(self.error_counts.values()) / max(total_trades, 1)) * 100
            },
            
            # Anomalies
            "anomalies": {
                "total": len(self.anomalies),
                "recent": list(self.anomalies)[-10:]  # Last 10 anomalies
            }
        }
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        metrics = []
        
        # Success rate
        metrics.append(f"arbitrage_success_rate {self.get_success_rate()}")
        
        # Trade counts
        for status, count in self.trade_outcomes.items():
            metrics.append(f'arbitrage_trades_total{{status="{status}"}} {count}')
        
        # Financial metrics
        metrics.append(f"arbitrage_profit_total_usd {self.pnl_metrics['total_profit_usd']}")
        metrics.append(f"arbitrage_loss_total_usd {self.pnl_metrics['total_loss_usd']}")
        metrics.append(f"arbitrage_net_profit_usd {self.pnl_metrics['net_profit_usd']}")
        metrics.append(f"arbitrage_gas_cost_total_usd {self.pnl_metrics['total_gas_cost_usd']}")
        
        # Latency metrics
        for name in self.latency_metrics.keys():
            avg = self.get_avg_latency(name)
            p95 = self.get_percentile_latency(name, 95)
            p99 = self.get_percentile_latency(name, 99)
            metrics.append(f'arbitrage_latency_avg_ms{{operation="{name}"}} {avg:.2f}')
            metrics.append(f'arbitrage_latency_p95_ms{{operation="{name}"}} {p95:.2f}')
            metrics.append(f'arbitrage_latency_p99_ms{{operation="{name}"}} {p99:.2f}')
        
        # Error rate
        total_trades = sum(self.trade_outcomes.values())
        error_rate = (sum(self.error_counts.values()) / max(total_trades, 1)) * 100
        metrics.append(f"arbitrage_error_rate_percent {error_rate:.2f}")
        
        return "\n".join(metrics)
    
    def save_to_file(self, filepath: str = "logs/metrics_summary.json"):
        """Save metrics summary to JSON file"""
        summary = self.get_metrics_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Metrics summary saved to {filepath}")

# Global metrics instance
_global_metrics = None

def get_metrics():
    """Get global metrics instance"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = ObservabilityMetrics()
    return _global_metrics

if __name__ == "__main__":
    # Test the observability system
    print("Testing Observability Metrics\n")
    print("=" * 80)
    
    metrics = ObservabilityMetrics()
    
    # Simulate some trades
    for i in range(10):
        trade = metrics.record_trade_start(f"trade_{i}", {
            "protocol": "uniswap" if i % 2 == 0 else "sushiswap",
            "expected_profit": 50 + i * 10
        })
        
        time.sleep(0.1)  # Simulate execution time
        
        trade["success"] = i % 3 != 0  # 2/3 success rate
        trade["profit_usd"] = 50 + i * 10 if trade["success"] else -20
        trade["gas_cost_usd"] = 15 + i
        trade["gas_price_gwei"] = 50 + i * 5
        trade["gas_used"] = 150000
        
        metrics.record_trade_complete(trade)
    
    # Print summary
    print("\n" + "=" * 80)
    print("Metrics Summary:")
    print("=" * 80)
    summary = metrics.get_metrics_summary()
    print(json.dumps(summary, indent=2, default=str))
    
    print("\n" + "=" * 80)
    print("Prometheus Metrics:")
    print("=" * 80)
    print(metrics.export_prometheus_metrics())
