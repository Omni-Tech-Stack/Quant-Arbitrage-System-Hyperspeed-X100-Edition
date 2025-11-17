#!/usr/bin/env python3
"""
GAS ORACLE INTEGRATION
Fetches real-time gas prices from Infura Gas API (line 68 in .env)
Provides gas price data for no-revert validation and transaction simulation
"""

import os
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from statistics import mean, median
import logging
from dotenv import load_dotenv

# Load environment from .env (single global config file)
load_dotenv('.env')

# Import currency formatter for consistent decimal precision
from currency_formatter import format_currency_usd, format_gas_price, fmt_usd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GasOracleIntegration:
    """
    Fetches and monitors gas prices from multiple RPC providers
    Provides gas price predictions and spike detection for no-revert validation
    """
    
    # Chain IDs
    CHAIN_IDS = {
        'polygon': 137,
        'ethereum': 1,
        'base': 8453,
        'arbitrum': 42161,
        'bsc': 56,
        'optimism': 10,
    }
    
    def __init__(
        self,
        update_interval_seconds: int = 12,  # Update every 12 seconds (Polygon block time)
        spike_threshold_percent: float = 150.0,  # 150% = gas spike
        history_window_blocks: int = 20,  # Track last 20 blocks for baseline
    ):
        """
        Initialize Gas Oracle with RPC endpoints from environment
        
        Args:
            update_interval_seconds: How often to fetch gas prices
            spike_threshold_percent: % increase to consider a gas spike
            history_window_blocks: Number of blocks to track for baseline
        """
        self.update_interval = update_interval_seconds
        self.spike_threshold = spike_threshold_percent
        self.history_window = history_window_blocks
        
        # Gas price history: {chain: [prices...]}
        self.gas_history: Dict[str, List[float]] = {}
        self.last_update: Dict[str, float] = {}
        self.cached_gas_prices: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Web3 connections
        self.web3_connections = self._initialize_web3_connections()
        
        # Fetch initial gas prices
        self._initial_fetch()
        
        logger.info(f"[GasOracle] ✓ Initialized with {len(self.web3_connections)} active chains")
        logger.info(f"  - Update Interval: {self.update_interval}s")
        logger.info(f"  - Spike Threshold: {self.spike_threshold}%")
        logger.info(f"  - History Window: {self.history_window} blocks")
    
    def _initialize_web3_connections(self) -> Dict[str, Web3]:
        """
        Initialize Web3 connections using RPC endpoints from environment
        Uses global .env file configuration
        """
        connections = {}
        
        # Polygon (primary chain) - try all available endpoints
        polygon_rpc = os.getenv('POLYGON_RPC_URL') or \
                      os.getenv('QUICKNODE_RPC_URL') or \
                      os.getenv('ALCHEMY_RPC_URL') or \
                      os.getenv('INFURA_POLYGON_RPC_HTTP')
        if polygon_rpc:
            try:
                w3 = Web3(Web3.HTTPProvider(polygon_rpc))
                if w3.is_connected():
                    connections['polygon'] = w3
                    logger.info(f"[GasOracle] ✓ Polygon connected: {polygon_rpc[:50]}...")
            except Exception as e:
                logger.warning(f"[GasOracle] ✗ Polygon connection failed: {e}")
        
        # Ethereum
        eth_rpc = os.getenv('ETHEREUM_RPC_URL') or os.getenv('ETHEREUM_RPC')
        if eth_rpc:
            try:
                w3 = Web3(Web3.HTTPProvider(eth_rpc))
                if w3.is_connected():
                    connections['ethereum'] = w3
                    logger.info(f"[GasOracle] ✓ Ethereum connected")
            except Exception as e:
                logger.warning(f"[GasOracle] ✗ Ethereum connection failed: {e}")
        
        # Arbitrum
        arb_rpc = os.getenv('ARBITRUM_RPC_URL') or os.getenv('ARBITRUM_RPC')
        if arb_rpc:
            try:
                w3 = Web3(Web3.HTTPProvider(arb_rpc))
                if w3.is_connected():
                    connections['arbitrum'] = w3
                    logger.info(f"[GasOracle] ✓ Arbitrum connected")
            except Exception as e:
                logger.warning(f"[GasOracle] ✗ Arbitrum connection failed: {e}")
        
        # BSC
        bsc_rpc = os.getenv('BSC_RPC_URL')
        if bsc_rpc:
            try:
                w3 = Web3(Web3.HTTPProvider(bsc_rpc))
                if w3.is_connected():
                    connections['bsc'] = w3
                    logger.info(f"[GasOracle] ✓ BSC connected")
            except Exception as e:
                logger.warning(f"[GasOracle] ✗ BSC connection failed: {e}")
        
        # Optimism
        op_rpc = os.getenv('OPTIMISM_RPC_URL')
        if op_rpc:
            try:
                w3 = Web3(Web3.HTTPProvider(op_rpc))
                if w3.is_connected():
                    connections['optimism'] = w3
                    logger.info(f"[GasOracle] ✓ Optimism connected")
            except Exception as e:
                logger.warning(f"[GasOracle] ✗ Optimism connection failed: {e}")
        
        # Base
        base_rpc = os.getenv('BASE_RPC_URL')
        if base_rpc:
            try:
                w3 = Web3(Web3.HTTPProvider(base_rpc))
                if w3.is_connected():
                    connections['base'] = w3
                    logger.info(f"[GasOracle] ✓ Base connected")
            except Exception as e:
                logger.warning(f"[GasOracle] ✗ Base connection failed: {e}")
        
        return connections
    
    def _initial_fetch(self):
        """Fetch initial gas prices for all connected chains"""
        for chain_name in self.web3_connections.keys():
            try:
                self.fetch_gas_price(chain_name, force_update=True)
            except Exception as e:
                logger.warning(f"[GasOracle] Failed initial fetch for {chain_name}: {e}")
    
    def fetch_gas_price(
        self,
        chain_name: str = 'polygon',
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch current gas price from RPC endpoint
        
        Args:
            chain_name: Chain to fetch gas for ('polygon', 'ethereum', etc.)
            force_update: Force fetch even if cache is fresh
        
        Returns:
            {
                'chain': 'polygon',
                'gas_price_gwei': 45.5,
                'max_fee_per_gas_gwei': 50.0,
                'max_priority_fee_per_gas_gwei': 35.0,
                'base_fee_gwei': 15.0,
                'timestamp': '2025-01-20T12:00:00',
                'is_spike': False,
                'spike_multiplier': 1.0,
                'baseline_gwei': 45.0,
                'source': 'infura'
            }
        """
        # Check cache freshness
        if not force_update and chain_name in self.last_update:
            time_since_update = time.time() - self.last_update[chain_name]
            if time_since_update < self.update_interval:
                # Return cached data
                return self.cached_gas_prices.get(chain_name, {})
        
        # Validate chain exists
        if chain_name not in self.web3_connections:
            raise ValueError(f"Chain '{chain_name}' not connected. Available: {list(self.web3_connections.keys())}")
        
        w3 = self.web3_connections[chain_name]
        
        try:
            # Fetch fee data from RPC
            fee_data = w3.eth.fee_history(1, 'latest', [50])  # Get median fee
            latest_block = w3.eth.get_block('latest')
            
            # Extract gas prices
            base_fee = latest_block.get('baseFeePerGas', 0)
            base_fee_gwei = float(Web3.from_wei(base_fee, 'gwei'))
            
            # EIP-1559 support (post-London fork)
            if base_fee > 0:
                # Priority fee from fee_history
                priority_fee = fee_data['reward'][0][0] if fee_data['reward'] else 0
                priority_fee_gwei = float(Web3.from_wei(priority_fee, 'gwei'))
                
                max_fee_gwei = base_fee_gwei + priority_fee_gwei
                gas_price_gwei = max_fee_gwei  # Use max fee as current price
            else:
                # Legacy gas price (pre-EIP-1559 or chains without base fee)
                gas_price = w3.eth.gas_price
                gas_price_gwei = float(Web3.from_wei(gas_price, 'gwei'))
                max_fee_gwei = gas_price_gwei
                priority_fee_gwei = 0
            
            # Update history
            if chain_name not in self.gas_history:
                self.gas_history[chain_name] = []
            
            self.gas_history[chain_name].append(gas_price_gwei)
            
            # Keep only recent history
            if len(self.gas_history[chain_name]) > self.history_window:
                self.gas_history[chain_name] = self.gas_history[chain_name][-self.history_window:]
            
            # Calculate baseline and detect spikes
            baseline_gwei = median(self.gas_history[chain_name]) if len(self.gas_history[chain_name]) > 3 else gas_price_gwei
            spike_multiplier = gas_price_gwei / baseline_gwei if baseline_gwei > 0 else 1.0
            is_spike = spike_multiplier >= (self.spike_threshold / 100.0)
            
            # Determine source (Infura, Alchemy, QuickNode)
            rpc_url = str(w3.provider.endpoint_uri) if hasattr(w3.provider, 'endpoint_uri') else 'unknown'
            if 'infura' in rpc_url.lower():
                source = 'infura'
            elif 'alchemy' in rpc_url.lower():
                source = 'alchemy'
            elif 'quiknode' in rpc_url.lower() or 'quicknode' in rpc_url.lower():
                source = 'quicknode'
            else:
                source = 'rpc'
            
            # Build response
            gas_data = {
                'chain': chain_name,
                'chain_id': self.CHAIN_IDS.get(chain_name, 0),
                'gas_price_gwei': round(gas_price_gwei, 2),
                'max_fee_per_gas_gwei': round(max_fee_gwei, 2),
                'max_priority_fee_per_gas_gwei': round(priority_fee_gwei, 2),
                'base_fee_gwei': round(base_fee_gwei, 2),
                'timestamp': datetime.now().isoformat(),
                'block_number': latest_block['number'],
                'is_spike': is_spike,
                'spike_multiplier': round(spike_multiplier, 2),
                'baseline_gwei': round(baseline_gwei, 2),
                'source': source,
                'history_samples': len(self.gas_history[chain_name])
            }
            
            # Update cache
            self.cached_gas_prices[chain_name] = gas_data
            self.last_update[chain_name] = time.time()
            
            if is_spike:
                logger.warning(f"[GasOracle] ⚠️  GAS SPIKE DETECTED on {chain_name}: {gas_price_gwei:.1f} gwei ({spike_multiplier:.1f}x baseline)")
            
            return gas_data
            
        except Exception as e:
            logger.error(f"[GasOracle] Failed to fetch gas price for {chain_name}: {e}")
            
            # Return cached data if available
            if chain_name in self.cached_gas_prices:
                logger.warning(f"[GasOracle] Using cached gas data for {chain_name}")
                return self.cached_gas_prices[chain_name]
            
            # Return safe default
            return {
                'chain': chain_name,
                'gas_price_gwei': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def validate_gas_for_transaction(
        self,
        estimated_gas_units: int,
        max_gas_price_gwei: float,
        chain_name: str = 'polygon',
        safety_multiplier: float = 1.5
    ) -> Dict[str, Any]:
        """
        Validate if current gas price is acceptable for transaction
        
        Args:
            estimated_gas_units: Expected gas units for transaction
            max_gas_price_gwei: Maximum acceptable gas price
            chain_name: Chain to validate
            safety_multiplier: Safety buffer (1.5 = 50% buffer)
        
        Returns:
            {
                'approved': True/False,
                'current_gas_gwei': 45.5,
                'max_gas_gwei': 100.0,
                'estimated_cost_usd': 2.50,
                'is_spike': False,
                'reason': 'Gas price acceptable',
                'wait_recommended': False
            }
        """
        gas_data = self.fetch_gas_price(chain_name)
        
        if 'error' in gas_data:
            return {
                'approved': False,
                'reason': f"Failed to fetch gas price: {gas_data['error']}",
                'wait_recommended': True
            }
        
        current_gas_gwei = gas_data['gas_price_gwei']
        is_spike = gas_data['is_spike']
        
        # Apply safety multiplier during spikes
        effective_max_gas = max_gas_price_gwei
        if is_spike:
            effective_max_gas = max_gas_price_gwei * safety_multiplier
        
        # Check if gas price exceeds limit
        if current_gas_gwei > effective_max_gas:
            return {
                'approved': False,
                'current_gas_gwei': current_gas_gwei,
                'max_gas_gwei': max_gas_price_gwei,
                'effective_max_gas_gwei': effective_max_gas,
                'is_spike': is_spike,
                'reason': f"Gas price too high: {current_gas_gwei:.1f} gwei > {effective_max_gas:.1f} gwei limit",
                'wait_recommended': True
            }
        
        # Estimate cost in USD (approximate ETH price: $3500)
        eth_price_usd = 3500.0 if chain_name == 'ethereum' else 0.60  # Polygon MATIC ~$0.60
        estimated_cost_eth = (estimated_gas_units * current_gas_gwei * 1e9) / 1e18
        estimated_cost_usd = estimated_cost_eth * eth_price_usd
        
        return {
            'approved': True,
            'current_gas_gwei': current_gas_gwei,
            'max_gas_gwei': max_gas_price_gwei,
            'estimated_cost_usd': round(estimated_cost_usd, 6),  # Use 6 decimals
            'estimated_gas_units': estimated_gas_units,
            'is_spike': is_spike,
            'spike_multiplier': gas_data['spike_multiplier'],
            'reason': 'Gas price acceptable' if not is_spike else 'Gas spike detected but within limits',
            'wait_recommended': False,
            'source': gas_data['source']
        }
    
    def get_gas_statistics(self, chain_name: str = 'polygon') -> Dict[str, Any]:
        """Get gas price statistics for a chain"""
        if chain_name not in self.gas_history or len(self.gas_history[chain_name]) < 2:
            return {'error': 'Insufficient history data'}
        
        history = self.gas_history[chain_name]
        
        return {
            'chain': chain_name,
            'samples': len(history),
            'current_gwei': round(history[-1], 2),
            'average_gwei': round(mean(history), 2),
            'median_gwei': round(median(history), 2),
            'min_gwei': round(min(history), 2),
            'max_gwei': round(max(history), 2),
            'volatility_pct': round((max(history) - min(history)) / mean(history) * 100, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def print_gas_report(self):
        """Print comprehensive gas price report"""
        print("\n" + "=" * 80)
        print("  GAS ORACLE REPORT - REAL-TIME NETWORK GAS PRICES")
        print("=" * 80)
        
        for chain_name in self.web3_connections.keys():
            try:
                gas_data = self.fetch_gas_price(chain_name)
                stats = self.get_gas_statistics(chain_name)
                
                spike_indicator = "🔥 SPIKE" if gas_data.get('is_spike') else "✓ Normal"
                
                print(f"\n  {chain_name.upper()}")
                print(f"    Current: {format_gas_price(gas_data.get('gas_price_gwei', 0))} {spike_indicator}")
                print(f"    Baseline: {format_gas_price(gas_data.get('baseline_gwei', 0))}")
                print(f"    Average: {format_gas_price(stats.get('average_gwei', 0))}")
                print(f"    Range: {format_gas_price(stats.get('min_gwei', 0))} - {format_gas_price(stats.get('max_gwei', 0))}")
                print(f"    Source: {gas_data.get('source', 'unknown').upper()}")
                
            except Exception as e:
                print(f"\n  {chain_name.upper()}: Error - {e}")
        
        print("\n" + "=" * 80 + "\n")


# Example usage
if __name__ == "__main__":
    print("Initializing Gas Oracle Integration...")
    
    oracle = GasOracleIntegration(
        update_interval_seconds=12,
        spike_threshold_percent=150.0,
        history_window_blocks=20
    )
    
    # Print initial report
    oracle.print_gas_report()
    
    # Test validation if we have connected chains
    if oracle.web3_connections:
        print("\nTesting gas validation for arbitrage transaction...")
        chain_name = list(oracle.web3_connections.keys())[0]
        validation = oracle.validate_gas_for_transaction(
            estimated_gas_units=500000,
            max_gas_price_gwei=100.0,
            chain_name=chain_name,
            safety_multiplier=1.5
        )
        
        print(f"  Chain: {chain_name}")
        print(f"  Approved: {validation['approved']}")
        print(f"  Current Gas: {format_gas_price(validation.get('current_gas_gwei', 0))}")
        print(f"  Estimated Cost: {fmt_usd(validation.get('estimated_cost_usd', 0))}")
        print(f"  Reason: {validation['reason']}")
    else:
        print("\n⚠️  No RPC connections available. Please configure .env file with valid RPC endpoints.")
