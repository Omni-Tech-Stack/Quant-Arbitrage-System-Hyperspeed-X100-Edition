#!/usr/bin/env python3
"""
Circuit Breaker Implementation
Runtime safety system that aborts execution when thresholds are exceeded
Includes kill switch, emergency pause, and automatic cooldown
"""

import time
from datetime import datetime, timedelta
from collections import deque
from config.safety_limits import EMERGENCY_SHUTDOWN, TRADING_PAUSED, CIRCUIT_BREAKER_COOLDOWN_SECONDS

class CircuitBreaker:
    """
    Circuit breaker for runtime safety monitoring and enforcement
    """
    
    def __init__(self):
        self.trade_history = deque(maxlen=1000)  # Keep last 1000 trades
        self.failed_trades = deque(maxlen=100)
        self.hourly_losses = deque(maxlen=60)  # Track losses per minute for hourly totals
        self.daily_losses = deque(maxlen=1440)  # Track losses per minute for daily totals
        
        self.circuit_open = False
        self.circuit_open_time = None
        self.circuit_open_reason = None
        
        self.emergency_shutdown = EMERGENCY_SHUTDOWN
        self.trading_paused = TRADING_PAUSED
        
        self.metrics = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit_usd": 0.0,
            "total_loss_usd": 0.0,
            "trades_last_minute": 0,
            "trades_last_hour": 0
        }
    
    def record_trade(self, trade_result):
        """
        Record a trade result and update metrics
        
        Args:
            trade_result: dict with keys: success, profit_usd, loss_usd, 
                         timestamp, slippage, gas_cost, etc.
        """
        timestamp = time.time()
        trade_result["timestamp"] = timestamp
        
        self.trade_history.append(trade_result)
        self.metrics["total_trades"] += 1
        
        if trade_result.get("success"):
            self.metrics["successful_trades"] += 1
            profit = trade_result.get("profit_usd", 0)
            self.metrics["total_profit_usd"] += profit
        else:
            self.metrics["failed_trades"] += 1
            self.failed_trades.append(trade_result)
            loss = abs(trade_result.get("loss_usd", 0))
            self.metrics["total_loss_usd"] += loss
            self.hourly_losses.append((timestamp, loss))
            self.daily_losses.append((timestamp, loss))
    
    def check_safety_limits(self, opportunity):
        """
        Check if a trade opportunity meets all safety requirements
        
        Args:
            opportunity: dict with trade parameters
            
        Returns:
            tuple: (allowed: bool, reason: str)
        """
        # Emergency shutdown check
        if self.emergency_shutdown or EMERGENCY_SHUTDOWN:
            return False, "EMERGENCY_SHUTDOWN_ACTIVE"
        
        # Trading pause check
        if self.trading_paused or TRADING_PAUSED:
            return False, "TRADING_PAUSED"
        
        # Circuit breaker cooldown check
        if self.circuit_open:
            if self._check_cooldown():
                return False, f"CIRCUIT_OPEN: {self.circuit_open_reason}"
        
        # Check profit threshold
        expected_profit = opportunity.get("expected_profit_usd", 0)
        if expected_profit < MIN_PROFIT_USD:
            return False, f"PROFIT_TOO_LOW: ${expected_profit:.2f} < ${MIN_PROFIT_USD}"
        
        # Check slippage
        slippage = opportunity.get("estimated_slippage_percent", 0)
        if slippage > MAX_SLIPPAGE_PERCENT:
            return False, f"SLIPPAGE_TOO_HIGH: {slippage:.2f}% > {MAX_SLIPPAGE_PERCENT}%"
        
        # Check market impact
        market_impact = opportunity.get("market_impact_percent", 0)
        if market_impact > MAX_MARKET_IMPACT_PERCENT:
            return False, f"MARKET_IMPACT_TOO_HIGH: {market_impact:.2f}% > {MAX_MARKET_IMPACT_PERCENT}%"
        
        # Check gas price
        gas_price = opportunity.get("gas_price_gwei", 0)
        if gas_price > MAX_GAS_PRICE_GWEI:
            return False, f"GAS_PRICE_TOO_HIGH: {gas_price} > {MAX_GAS_PRICE_GWEI} gwei"
        
        # Check gas cost
        gas_cost = opportunity.get("estimated_gas_cost_usd", 0)
        if gas_cost > MAX_GAS_COST_USD:
            return False, f"GAS_COST_TOO_HIGH: ${gas_cost:.2f} > ${MAX_GAS_COST_USD}"
        
        # Check position size
        position_size = opportunity.get("position_size_usd", 0)
        if position_size > MAX_POSITION_SIZE_USD:
            return False, f"POSITION_TOO_LARGE: ${position_size:.2f} > ${MAX_POSITION_SIZE_USD}"
        
        # Check pool depth ratio
        pool_size = opportunity.get("pool_reserve_usd", float('inf'))
        if pool_size > 0:
            trade_percent = (position_size / pool_size) * 100
            if trade_percent > MAX_TRADE_SIZE_PERCENT_OF_POOL:
                return False, f"TRADE_TOO_LARGE_FOR_POOL: {trade_percent:.1f}% > {MAX_TRADE_SIZE_PERCENT_OF_POOL}%"
        
        # Check recent loss limits
        hourly_loss = self._get_hourly_loss()
        if hourly_loss > MAX_LOSS_PER_HOUR_USD:
            self._trigger_circuit_breaker(f"HOURLY_LOSS_LIMIT: ${hourly_loss:.2f} > ${MAX_LOSS_PER_HOUR_USD}")
            return False, self.circuit_open_reason
        
        daily_loss = self._get_daily_loss()
        if daily_loss > MAX_LOSS_PER_DAY_USD:
            self._trigger_circuit_breaker(f"DAILY_LOSS_LIMIT: ${daily_loss:.2f} > ${MAX_LOSS_PER_DAY_USD}")
            return False, self.circuit_open_reason
        
        # Check recent failure rate
        recent_failures = self._count_recent_failures(hours=1)
        if recent_failures >= MAX_FAILED_TRADES_PER_HOUR:
            self._trigger_circuit_breaker(f"TOO_MANY_FAILURES: {recent_failures} in last hour")
            return False, self.circuit_open_reason
        
        # Check rate limiting
        trades_last_minute = self._count_recent_trades(minutes=1)
        if trades_last_minute >= MAX_TRADES_PER_MINUTE:
            return False, f"RATE_LIMIT_MINUTE: {trades_last_minute} >= {MAX_TRADES_PER_MINUTE}"
        
        trades_last_hour = self._count_recent_trades(minutes=60)
        if trades_last_hour >= MAX_TRADES_PER_HOUR:
            return False, f"RATE_LIMIT_HOUR: {trades_last_hour} >= {MAX_TRADES_PER_HOUR}"
        
        return True, "ALL_CHECKS_PASSED"
    
    def _trigger_circuit_breaker(self, reason):
        """Trigger the circuit breaker"""
        self.circuit_open = True
        self.circuit_open_time = time.time()
        self.circuit_open_reason = reason
        print(f"⚠️  CIRCUIT BREAKER TRIGGERED: {reason}")
        print(f"   Cooldown period: {CIRCUIT_BREAKER_COOLDOWN_SECONDS} seconds")
    
    def _check_cooldown(self):
        """Check if circuit breaker cooldown has expired"""
        if not self.circuit_open:
            return False
        
        elapsed = time.time() - self.circuit_open_time
        if elapsed >= CIRCUIT_BREAKER_COOLDOWN_SECONDS:
            print(f"✓ Circuit breaker cooldown complete. Resuming trading.")
            self.circuit_open = False
            self.circuit_open_reason = None
            return False
        
        return True
    
    def _get_hourly_loss(self):
        """Calculate total loss in the last hour"""
        cutoff = time.time() - 3600
        return sum(loss for ts, loss in self.hourly_losses if ts > cutoff)
    
    def _get_daily_loss(self):
        """Calculate total loss in the last 24 hours"""
        cutoff = time.time() - 86400
        return sum(loss for ts, loss in self.daily_losses if ts > cutoff)
    
    def _count_recent_failures(self, hours=1):
        """Count failed trades in recent hours"""
        cutoff = time.time() - (hours * 3600)
        return sum(1 for trade in self.failed_trades if trade.get("timestamp", 0) > cutoff)
    
    def _count_recent_trades(self, minutes=1):
        """Count trades in recent minutes"""
        cutoff = time.time() - (minutes * 60)
        return sum(1 for trade in self.trade_history if trade.get("timestamp", 0) > cutoff)
    
    def emergency_stop(self, reason="MANUAL_EMERGENCY_STOP"):
        """Activate emergency shutdown"""
        self.emergency_shutdown = True
        self.circuit_open = True
        self.circuit_open_reason = reason
        print(f"🚨 EMERGENCY SHUTDOWN ACTIVATED: {reason}")
        return True
    
    def pause_trading(self, reason="MANUAL_PAUSE"):
        """Pause trading temporarily"""
        self.trading_paused = True
        print(f"⏸️  Trading paused: {reason}")
        return True
    
    def resume_trading(self):
        """Resume trading after pause"""
        if not self.emergency_shutdown:
            self.trading_paused = False
            print("▶️  Trading resumed")
            return True
        else:
            print("❌ Cannot resume: Emergency shutdown is active")
            return False
    
    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker (use with caution)"""
        self.circuit_open = False
        self.circuit_open_reason = None
        self.circuit_open_time = None
        print("🔄 Circuit breaker manually reset")
    
    def get_status(self):
        """Get current status of circuit breaker"""
        return {
            "emergency_shutdown": self.emergency_shutdown,
            "trading_paused": self.trading_paused,
            "circuit_open": self.circuit_open,
            "circuit_open_reason": self.circuit_open_reason,
            "circuit_open_time": self.circuit_open_time,
            "metrics": self.metrics,
            "hourly_loss": self._get_hourly_loss(),
            "daily_loss": self._get_daily_loss(),
            "recent_failures": self._count_recent_failures(hours=1),
            "trades_last_minute": self._count_recent_trades(minutes=1),
            "trades_last_hour": self._count_recent_trades(minutes=60)
        }

# Global circuit breaker instance
_global_circuit_breaker = None

def get_circuit_breaker():
    """Get global circuit breaker instance"""
    global _global_circuit_breaker
    if _global_circuit_breaker is None:
        _global_circuit_breaker = CircuitBreaker()
    return _global_circuit_breaker

if __name__ == "__main__":
    import json
    
    # Test circuit breaker
    cb = CircuitBreaker()
    
    print("Testing Circuit Breaker\n")
    print("=" * 60)
    
    # Test 1: Normal trade
    print("\nTest 1: Normal profitable trade")
    opportunity = {
        "expected_profit_usd": 50,
        "estimated_slippage_percent": 1.5,
        "market_impact_percent": 2.0,
        "gas_price_gwei": 50,
        "estimated_gas_cost_usd": 25,
        "position_size_usd": 10000,
        "pool_reserve_usd": 500000
    }
    allowed, reason = cb.check_safety_limits(opportunity)
    print(f"Allowed: {allowed}, Reason: {reason}")
    
    # Test 2: High slippage
    print("\nTest 2: High slippage trade")
    opportunity["estimated_slippage_percent"] = 5.0
    allowed, reason = cb.check_safety_limits(opportunity)
    print(f"Allowed: {allowed}, Reason: {reason}")
    
    # Test 3: Emergency shutdown
    print("\nTest 3: Emergency shutdown")
    cb.emergency_stop("Testing emergency stop")
    opportunity["estimated_slippage_percent"] = 1.5
    allowed, reason = cb.check_safety_limits(opportunity)
    print(f"Allowed: {allowed}, Reason: {reason}")
    
    print("\n" + "=" * 60)
    print("Circuit Breaker Status:")
    print(json.dumps(cb.get_status(), indent=2, default=str))
