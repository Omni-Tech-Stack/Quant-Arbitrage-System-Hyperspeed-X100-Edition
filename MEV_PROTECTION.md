# MEV Protection & Front-Running Defense Strategy

## Overview

This document outlines comprehensive strategies to protect arbitrage transactions from MEV (Maximal Extractable Value) attacks and front-running.

## Table of Contents

1. [MEV Threat Model](#mev-threat-model)
2. [Private Transaction Relayers](#private-transaction-relayers)
3. [Transaction Bundling](#transaction-bundling)
4. [Anti-Sandwich Protection](#anti-sandwich-protection)
5. [Transaction Ordering Strategies](#transaction-ordering-strategies)
6. [Implementation Guide](#implementation-guide)

## MEV Threat Model

### Common MEV Attack Vectors

1. **Front-Running**
   - Attacker sees your transaction in mempool
   - Submits similar transaction with higher gas price
   - Executes before yours

2. **Back-Running**
   - Attacker places transaction immediately after yours
   - Extracts value from price change you created

3. **Sandwich Attacks**
   - Front-run with buy order
   - Your transaction executes (moving price)
   - Back-run with sell order
   - Attacker profits from your slippage

4. **Time-Bandit Attacks**
   - Miners reorganize blocks to extract MEV
   - Potentially revert your transactions

## Private Transaction Relayers

### Supported Relayers

#### 1. Flashbots Protect

**Advantages:**
- Most widely used
- No failed transaction costs
- Direct connection to miners
- Bundle support

**Setup:**

```python
from web3 import Web3
import requests

FLASHBOTS_RELAY_URL = "https://relay.flashbots.net"
FLASHBOTS_SIGNATURE_KEY = "YOUR_PRIVATE_KEY"

def send_via_flashbots(signed_transaction, target_block):
    """
    Send transaction via Flashbots relay
    
    Args:
        signed_transaction: Signed transaction hex
        target_block: Target block number for inclusion
    """
    # Create bundle
    bundle = [{
        "signed_transaction": signed_transaction
    }]
    
    # Send to Flashbots
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_sendBundle",
        "params": [{
            "txs": [tx["signed_transaction"] for tx in bundle],
            "blockNumber": hex(target_block),
            "minTimestamp": 0,
            "maxTimestamp": 0
        }]
    }
    
    # Sign request
    headers = {
        "X-Flashbots-Signature": f"{FLASHBOTS_SIGNATURE_KEY}:signature"
    }
    
    response = requests.post(
        FLASHBOTS_RELAY_URL,
        json=payload,
        headers=headers
    )
    
    return response.json()
```

**Configuration:**

```python
# config/mev_protection.py

FLASHBOTS_CONFIG = {
    "relay_url": "https://relay.flashbots.net",
    "min_priority_fee": 3,  # gwei
    "max_priority_fee": 100,  # gwei
    "bundle_timeout_blocks": 25,
    "enable_simulation": True
}
```

#### 2. bloXroute

**Advantages:**
- Low latency global network
- Multiple submission options
- Good for high-frequency trading

**Setup:**

```python
import asyncio
import websockets
import json

BLOXROUTE_GATEWAY = "wss://api.bloxroute.com/ws"
BLOXROUTE_AUTH_HEADER = "YOUR_AUTH_TOKEN"

async def send_via_bloxroute(signed_transaction):
    """Send transaction via bloXroute gateway"""
    
    async with websockets.connect(
        BLOXROUTE_GATEWAY,
        extra_headers={"Authorization": BLOXROUTE_AUTH_HEADER}
    ) as ws:
        # Send transaction
        message = {
            "method": "blxr_tx",
            "params": {
                "transaction": signed_transaction,
                "blockchain_network": "Ethereum"
            }
        }
        
        await ws.send(json.dumps(message))
        response = await ws.recv()
        
        return json.loads(response)

# Configuration
BLOXROUTE_CONFIG = {
    "gateway_url": "wss://api.bloxroute.com/ws",
    "auth_token": "YOUR_AUTH_TOKEN",
    "network": "Ethereum",
    "enable_frontrunning_protection": True
}
```

#### 3. Eden Network

**Advantages:**
- Slot-based block production
- Predictable ordering
- Good for MEV-aware applications

**Setup:**

```python
from web3 import Web3

EDEN_RPC = "https://api.edennetwork.io/v1/rpc"

def send_via_eden(signed_transaction):
    """Send transaction via Eden Network"""
    
    w3 = Web3(Web3.HTTPProvider(EDEN_RPC))
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_transaction)
    
    return tx_hash

# Configuration
EDEN_CONFIG = {
    "rpc_url": "https://api.edennetwork.io/v1/rpc",
    "staking_required": False,  # For non-stakers
    "slot_priority": "medium"
}
```

### Relay Selection Strategy

Implement intelligent relay selection based on:
- Historical success rates
- Network conditions
- Transaction urgency
- Gas price

```python
class RelaySelector:
    """Intelligent relay selection based on conditions"""
    
    def __init__(self):
        self.relay_stats = {
            "flashbots": {"success_rate": 0.85, "avg_latency_ms": 150},
            "bloxroute": {"success_rate": 0.82, "avg_latency_ms": 120},
            "eden": {"success_rate": 0.78, "avg_latency_ms": 180}
        }
    
    def select_relay(self, transaction_params):
        """
        Select best relay for given transaction
        
        Args:
            transaction_params: dict with urgency, value, etc.
            
        Returns:
            str: Selected relay name
        """
        urgency = transaction_params.get("urgency", "normal")
        value_usd = transaction_params.get("value_usd", 0)
        
        # High value = Flashbots (most reliable)
        if value_usd > 10000:
            return "flashbots"
        
        # High urgency = bloXroute (lowest latency)
        if urgency == "high":
            return "bloxroute"
        
        # Default to best success rate
        best_relay = max(
            self.relay_stats.items(),
            key=lambda x: x[1]["success_rate"]
        )
        
        return best_relay[0]
    
    def update_stats(self, relay_name, success, latency_ms):
        """Update relay statistics based on results"""
        stats = self.relay_stats[relay_name]
        
        # Update success rate (exponential moving average)
        alpha = 0.1
        stats["success_rate"] = (
            alpha * (1.0 if success else 0.0) + 
            (1 - alpha) * stats["success_rate"]
        )
        
        # Update latency
        stats["avg_latency_ms"] = (
            alpha * latency_ms + 
            (1 - alpha) * stats["avg_latency_ms"]
        )
```

## Transaction Bundling

### Bundle Construction

```python
class TransactionBundler:
    """
    Build transaction bundles for atomic execution
    """
    
    def __init__(self):
        self.pending_bundles = []
    
    def create_flashloan_bundle(self, flashloan_tx, arbitrage_txs):
        """
        Create atomic bundle for flashloan arbitrage
        
        Args:
            flashloan_tx: Flashloan initiation transaction
            arbitrage_txs: List of arbitrage transactions
            
        Returns:
            dict: Bundle configuration
        """
        bundle = {
            "transactions": [flashloan_tx] + arbitrage_txs,
            "target_block": None,  # Will be set at submission
            "min_timestamp": 0,
            "max_timestamp": 0,
            "reverting_tx_hashes": []  # Allow these to revert
        }
        
        return bundle
    
    def optimize_bundle_order(self, transactions):
        """
        Optimize transaction order within bundle
        
        Returns transactions in optimal execution order
        """
        # Sort by dependency and profitability
        optimized = sorted(
            transactions,
            key=lambda tx: (
                tx.get("dependency_level", 0),
                -tx.get("expected_profit", 0)
            )
        )
        
        return optimized
```

### Bundle Simulation

Always simulate bundles before submission:

```python
def simulate_bundle(bundle, block_number):
    """
    Simulate bundle execution using Flashbots simulate API
    
    Args:
        bundle: Bundle configuration
        block_number: Target block for simulation
        
    Returns:
        dict: Simulation results
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_callBundle",
        "params": [{
            "txs": [tx["signed_transaction"] for tx in bundle["transactions"]],
            "blockNumber": hex(block_number),
            "stateBlockNumber": "latest"
        }]
    }
    
    response = requests.post(FLASHBOTS_RELAY_URL, json=payload)
    result = response.json()
    
    # Check for reverts
    if "error" in result:
        return {"success": False, "error": result["error"]}
    
    # Calculate profitability
    results = result["result"]["results"]
    total_profit = sum(r.get("coinbaseDiff", 0) for r in results)
    
    return {
        "success": True,
        "profit": total_profit,
        "gas_used": sum(r.get("gasUsed", 0) for r in results),
        "results": results
    }
```

## Anti-Sandwich Protection

### Slippage Protection

```python
def calculate_sandwich_safe_params(
    pool_reserves_in,
    pool_reserves_out,
    amount_in,
    max_slippage_percent=1.0
):
    """
    Calculate parameters that protect against sandwich attacks
    
    Returns minimum output amount that prevents profitable sandwiching
    """
    # Calculate expected output
    k = pool_reserves_in * pool_reserves_out
    new_reserve_in = pool_reserves_in + amount_in
    new_reserve_out = k / new_reserve_in
    amount_out = pool_reserves_out - new_reserve_out
    
    # Apply conservative slippage for sandwich protection
    min_amount_out = amount_out * (1 - max_slippage_percent / 100)
    
    # Calculate max price impact that still allows profit
    # Sandwich attack needs: (front-run profit + back-run profit) > gas costs
    # Typical gas costs: ~$50-100
    # We want to make sandwich attacks unprofitable
    
    sandwich_protection_buffer = 0.5  # Additional 0.5% buffer
    min_amount_out *= (1 - sandwich_protection_buffer / 100)
    
    return int(min_amount_out)
```

### Deadline Protection

```solidity
// Smart contract: Use tight deadlines to prevent delayed execution
function executeArbitrage(
    address[] memory path,
    uint256 amountIn,
    uint256 minAmountOut,
    uint256 deadline
) external {
    require(block.timestamp <= deadline, "Transaction expired");
    require(deadline <= block.timestamp + 60, "Deadline too far in future");
    
    // Execute swap with strict parameters
    _executeSwap(path, amountIn, minAmountOut);
}
```

### Private Mempool

```python
# Always use private relays for arbitrage transactions
def submit_arbitrage_transaction(signed_tx):
    """
    Submit arbitrage transaction through private relay
    NEVER submit directly to public mempool
    """
    # Choose relay
    relay_selector = RelaySelector()
    relay = relay_selector.select_relay({
        "urgency": "high",
        "value_usd": estimate_trade_value(signed_tx)
    })
    
    # Submit based on selected relay
    if relay == "flashbots":
        return send_via_flashbots(signed_tx)
    elif relay == "bloxroute":
        return send_via_bloxroute(signed_tx)
    elif relay == "eden":
        return send_via_eden(signed_tx)
    else:
        raise ValueError(f"Unknown relay: {relay}")
```

## Transaction Ordering Strategies

### Priority Fee Optimization

```python
def calculate_optimal_priority_fee(
    base_fee,
    expected_profit,
    urgency="normal"
):
    """
    Calculate optimal priority fee to beat competition without overpaying
    
    Args:
        base_fee: Current base fee in gwei
        expected_profit: Expected profit in USD
        urgency: Trade urgency level
        
    Returns:
        int: Priority fee in gwei
    """
    # Minimum priority fee
    min_priority = 2  # gwei
    
    # Maximum we're willing to pay (% of expected profit)
    max_priority_usd = expected_profit * 0.1  # 10% of profit
    
    # Convert to gwei (assuming ETH price)
    eth_price = 2000  # USD - should be fetched dynamically
    max_priority_gwei = (max_priority_usd / eth_price) * 1e9
    
    # Adjust based on urgency
    if urgency == "high":
        target_priority = base_fee * 1.5  # 150% of base fee
    elif urgency == "normal":
        target_priority = base_fee * 1.2  # 120% of base fee
    else:
        target_priority = min_priority
    
    # Clamp to min/max
    priority_fee = max(min_priority, min(target_priority, max_priority_gwei))
    
    return int(priority_fee)
```

### Randomization

```python
import random

def add_randomization_to_avoid_detection(transaction_params):
    """
    Add randomization to avoid MEV bot pattern detection
    """
    # Randomize nonce timing
    import time
    time.sleep(random.uniform(0.1, 0.5))
    
    # Randomize gas price slightly (within acceptable range)
    gas_price = transaction_params["maxPriorityFeePerGas"]
    jitter = random.uniform(0.95, 1.05)
    transaction_params["maxPriorityFeePerGas"] = int(gas_price * jitter)
    
    # Randomize amount slightly (for non-atomic operations)
    if "amount_randomization_allowed" in transaction_params:
        amount = transaction_params["value"]
        jitter = random.uniform(0.98, 1.02)
        transaction_params["value"] = int(amount * jitter)
    
    return transaction_params
```

## Implementation Guide

### Integrated MEV Protection System

```python
#!/usr/bin/env python3
"""
Integrated MEV Protection System
"""

from enum import Enum
from typing import Dict, Optional
import asyncio

class MEVProtectionLevel(Enum):
    """MEV protection levels"""
    NONE = "none"  # Public mempool (not recommended)
    BASIC = "basic"  # Single private relay
    STANDARD = "standard"  # Multiple relays, simulation
    MAXIMUM = "maximum"  # Bundles, multi-relay, full protection

class MEVProtectionSystem:
    """
    Comprehensive MEV protection system
    """
    
    def __init__(self, protection_level: MEVProtectionLevel = MEVProtectionLevel.STANDARD):
        self.protection_level = protection_level
        self.relay_selector = RelaySelector()
        self.bundler = TransactionBundler()
        
        # Statistics
        self.stats = {
            "transactions_sent": 0,
            "transactions_successful": 0,
            "mev_attacks_prevented": 0,
            "total_gas_saved": 0
        }
    
    async def submit_protected_transaction(
        self,
        signed_transaction: str,
        expected_profit: float,
        urgency: str = "normal"
    ) -> Dict:
        """
        Submit transaction with MEV protection
        
        Args:
            signed_transaction: Signed transaction hex
            expected_profit: Expected profit in USD
            urgency: Transaction urgency
            
        Returns:
            dict: Submission result
        """
        if self.protection_level == MEVProtectionLevel.NONE:
            # Not recommended!
            return await self._submit_public(signed_transaction)
        
        elif self.protection_level == MEVProtectionLevel.BASIC:
            # Single relay submission
            return await self._submit_single_relay(signed_transaction, urgency)
        
        elif self.protection_level == MEVProtectionLevel.STANDARD:
            # Multiple relays with simulation
            return await self._submit_multi_relay(
                signed_transaction,
                expected_profit,
                urgency
            )
        
        elif self.protection_level == MEVProtectionLevel.MAXIMUM:
            # Full protection with bundling
            return await self._submit_maximum_protection(
                signed_transaction,
                expected_profit,
                urgency
            )
    
    async def _submit_single_relay(self, signed_tx: str, urgency: str) -> Dict:
        """Submit via single relay"""
        relay = self.relay_selector.select_relay({"urgency": urgency})
        
        if relay == "flashbots":
            result = await send_via_flashbots(signed_tx)
        elif relay == "bloxroute":
            result = await send_via_bloxroute(signed_tx)
        else:
            result = await send_via_eden(signed_tx)
        
        self.stats["transactions_sent"] += 1
        return result
    
    async def _submit_multi_relay(
        self,
        signed_tx: str,
        expected_profit: float,
        urgency: str
    ) -> Dict:
        """Submit via multiple relays simultaneously"""
        
        # Simulate first
        # simulation = simulate_bundle({"transactions": [signed_tx]})
        # if not simulation.get("success"):
        #     return {"success": False, "error": "Simulation failed"}
        
        # Submit to multiple relays in parallel
        relay_tasks = [
            send_via_flashbots(signed_tx),
            send_via_bloxroute(signed_tx),
            send_via_eden(signed_tx)
        ]
        
        results = await asyncio.gather(*relay_tasks, return_exceptions=True)
        
        # Return first successful result
        for result in results:
            if isinstance(result, dict) and result.get("success"):
                self.stats["transactions_sent"] += 1
                self.stats["transactions_successful"] += 1
                return result
        
        return {"success": False, "error": "All relays failed"}
    
    async def _submit_maximum_protection(
        self,
        signed_tx: str,
        expected_profit: float,
        urgency: str
    ) -> Dict:
        """Submit with maximum MEV protection using bundles"""
        
        # Create bundle (can include additional protection txs)
        bundle = self.bundler.create_flashloan_bundle(
            flashloan_tx={"signed_transaction": signed_tx},
            arbitrage_txs=[]
        )
        
        # Simulate bundle
        # simulation = simulate_bundle(bundle)
        # if not simulation.get("success"):
        #     return {"success": False, "error": "Bundle simulation failed"}
        
        # Submit bundle to Flashbots (best for bundles)
        result = await send_via_flashbots(signed_tx)
        
        if result.get("success"):
            self.stats["transactions_sent"] += 1
            self.stats["transactions_successful"] += 1
            self.stats["mev_attacks_prevented"] += 1
        
        return result
    
    def get_statistics(self) -> Dict:
        """Get MEV protection statistics"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["transactions_successful"] / 
                max(self.stats["transactions_sent"], 1)
            ) * 100
        }

# Global MEV protection instance
_mev_protection = None

def get_mev_protection(level: MEVProtectionLevel = MEVProtectionLevel.STANDARD):
    """Get global MEV protection instance"""
    global _mev_protection
    if _mev_protection is None:
        _mev_protection = MEVProtectionSystem(level)
    return _mev_protection

if __name__ == "__main__":
    # Test MEV protection system
    print("MEV Protection System - Test Mode")
    print("=" * 60)
    
    mev = MEVProtectionSystem(MEVProtectionLevel.STANDARD)
    print(f"Protection Level: {mev.protection_level.value}")
    print(f"Statistics: {mev.get_statistics()}")
```

## Best Practices Summary

1. **Always use private relays** for arbitrage transactions
2. **Never submit to public mempool** - visible to MEV bots
3. **Use tight slippage limits** to prevent sandwich attacks
4. **Implement deadlines** on all swaps (max 60 seconds)
5. **Simulate transactions** before submission
6. **Use bundles** for atomic multi-step operations
7. **Monitor and adapt** - track relay success rates
8. **Randomize** transaction parameters to avoid patterns
9. **Calculate optimal priority fees** - don't overpay
10. **Test on mainnet fork** before live deployment

## Monitoring MEV Protection

```python
# Add to observability system
def log_mev_protection_metrics(trade_result):
    """Log MEV protection effectiveness"""
    metrics = {
        "relay_used": trade_result.get("relay"),
        "bundle_used": trade_result.get("bundle", False),
        "simulation_passed": trade_result.get("simulation_passed", False),
        "priority_fee_paid": trade_result.get("priority_fee_gwei"),
        "inclusion_time_seconds": trade_result.get("inclusion_time"),
        "mev_attack_detected": trade_result.get("mev_attack_detected", False)
    }
    
    # Send to monitoring system
    observability.record_trade_metrics(metrics)
```

## References

- [Flashbots Documentation](https://docs.flashbots.net/)
- [bloXroute Documentation](https://docs.bloxroute.com/)
- [Eden Network Documentation](https://docs.edennetwork.io/)
- [MEV Protection Best Practices](https://collective.flashbots.net/)
- [Ethereum MEV Research](https://ethereum.org/en/developers/docs/mev/)
