#!/usr/bin/env python3
"""
GAS ORACLE INTEGRATION - Multi-Network Version
Uses Infura Gas API (ON_CHAIN_GAS_ENDPOINT from ..env line 68)
Falls back to eth_gasPrice RPC calls when Gas API unavailable
Provides real-time gas prices for no-revert validation
"""

import os
import time
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from statistics import mean
import logging
from dotenv import load_dotenv
from web3 import Web3

# Load environment from ..env (single global config file)
load_dotenv('..env')

# Import currency formatter for consistent decimal precision
from currency_formatter import format_gas_price, fmt_usd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GasOracleIntegration:
    """
    Multi-Network Gas Oracle using Infura Gas API + RPC Fallback
    Fetches real-time gas prices for 100+ networks
    """
    
    # Supported networks with their chain IDs (from Infura docs)
    NETWORKS = {
        'ethereum': {'chain_id': 1, 'rpc_var': 'ETHEREUM_RPC_URL', 'name': 'Ethereum'},
        'optimism': {'chain_id': 10, 'rpc_var': 'OPTIMISM_RPC_URL', 'name': 'Optimism'},
        'bsc': {'chain_id': 56, 'rpc_var': 'BSC_RPC_URL', 'name': 'BNB Smart Chain'},
        'polygon': {'chain_id': 137, 'rpc_var': 'POLYGON_RPC_URL', 'name': 'Polygon'},
        'base': {'chain_id': 8453, 'rpc_var': 'BASE_RPC_URL', 'name': 'Base'},
        'arbitrum': {'chain_id': 42161, 'rpc_var': 'ARBITRUM_RPC_URL', 'name': 'Arbitrum One'},
        'avalanche': {'chain_id': 43114, 'rpc_var': 'AVALANCHE_RPC', 'name': 'Avalanche C-Chain'},
        'blast': {'chain_id': 81457, 'rpc_var': 'BLAST_RPC_URL', 'name': 'Blast'},
        'zksync': {'chain_id': 324, 'rpc_var': 'ZKSYNC_RPC_URL', 'name': 'zkSync Era'},
        'linea': {'chain_id': 59144, 'rpc_var': 'LINEA_RPC_URL', 'name': 'Linea'},
    }
    
    def __init__(
        self,
        update_interval_seconds: int = 12,
        spike_threshold_percent: float = 150.0,
        max_gas_price_gwei: float = 150.0
    ):
        """
        Initialize Gas Oracle with Infura Gas API + RPC fallback
        
        Args:
            update_interval_seconds: Cache duration (12s = Polygon block time)
            spike_threshold_percent: % increase to consider a gas spike
            max_gas_price_gwei: Maximum acceptable gas price
        """
        self.gas_api_endpoint = os.getenv('ON_CHAIN_GAS_ENDPOINT')
        self.update_interval = update_interval_seconds
        self.spike_threshold = spike_threshold_percent
        self.max_gas_price = max_gas_price_gwei
        
        # Initialize Web3 connections for RPC fallback
        self.web3_connections = self._initialize_rpc_connections()
        
        # Cache: {network: {'price': float, 'timestamp': float, 'data': dict}}
        self.cache: Dict[str, Dict[str, Any]] = {}
        
        # Gas price history for baseline: {network: [prices...]}
        self.history: Dict[str, list] = {net: [] for net in self.NETWORKS.keys()}
        
        logger.info(f"[GasOracle] ✓ Initialized with Infura Gas API + RPC Fallback")
        if self.gas_api_endpoint:
            logger.info(f"  - Gas API: {self.gas_api_endpoint[:60]}...")
        logger.info(f"  - RPC Connections: {len(self.web3_connections)} networks")
        logger.info(f"  - Cache TTL: {self.update_interval}s")
        logger.info(f"  - Spike Threshold: {self.spike_threshold}%")
        logger.info(f"  - Max Gas Price: {self.max_gas_price} gwei")
    
    def _initialize_rpc_connections(self) -> Dict[str, Web3]:
        """Initialize Web3 RPC connections for fallback gas price fetching"""
        connections = {}
        
        for network, config in self.NETWORKS.items():
            rpc_url = os.getenv(config['rpc_var'])
            if rpc_url:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    if w3.is_connected():
                        connections[network] = w3
                        logger.debug(f"[GasOracle] ✓ {config['name']} RPC connected")
                except Exception as e:
                    logger.debug(f"[GasOracle] ✗ {config['name']} RPC failed: {e}")
        
        return connections
    
    
    def fetch_gas_price(self, network: str = 'polygon', force_update: bool = False) -> Dict[str, Any]:
        """
        Fetch current gas price from Infura Gas API with RPC fallback
        
        Args:
            network: Network name ('polygon', 'ethereum', 'arbitrum', etc.)
            force_update: Skip cache and force fresh fetch
            
        Returns:
            Dict with gas price data
        """
        if network not in self.NETWORKS:
            raise ValueError(f"Unsupported network: {network}. Supported: {list(self.NETWORKS.keys())}")
        
        # Check cache
        if not force_update and network in self.cache:
            cached = self.cache[network]
            age = time.time() - cached['timestamp']
            if age < self.update_interval:
                logger.debug(f"[GasOracle] Using cached {network} gas price (age: {age:.1f}s)")
                return cached
        
        # Try Infura Gas API first
        gas_data = self._fetch_from_gas_api(network)
        
        # Fallback to RPC if Gas API fails
        if not gas_data or gas_data.get('source') == 'fallback':
            gas_data = self._fetch_from_rpc(network)
        
        # Update cache and history
        if gas_data:
            self.cache[network] = gas_data
            gas_price_gwei = gas_data['price_gwei']
            self.history[network].append(gas_price_gwei)
            if len(self.history[network]) > 20:
                self.history[network].pop(0)
        
        return gas_data
    
    def _fetch_from_gas_api(self, network: str) -> Optional[Dict[str, Any]]:
        """Fetch gas price from Infura Gas API"""
        if not self.gas_api_endpoint:
            return None
        
        try:
            chain_id = self.NETWORKS[network]['chain_id']
            url = f"{self.gas_api_endpoint}/networks/{chain_id}/suggestedGasFees"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Parse Infura Gas API response
            medium_price = float(data.get('medium', {}).get('suggestedMaxFeePerGas', 0))
            high_price = float(data.get('high', {}).get('suggestedMaxFeePerGas', 0))
            low_price = float(data.get('low', {}).get('suggestedMaxFeePerGas', 0))
            
            # Use high estimate for reliability
            gas_price_gwei = high_price if high_price > 0 else medium_price
            
            result = {
                'network': network,
                'chain_id': chain_id,
                'price_gwei': gas_price_gwei,
                'low': low_price,
                'medium': medium_price,
                'high': high_price,
                'timestamp': time.time(),
                'source': 'infura_gas_api',
                'data': data
            }
            
            logger.info(f"[GasOracle] ✓ {network.upper()}: {format_gas_price(gas_price_gwei)} (Gas API)")
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug(f"[GasOracle] Gas API requires subscription (403) - using RPC fallback")
            else:
                logger.debug(f"[GasOracle] Gas API error {e.response.status_code}: {e}")
            return None
        except Exception as e:
            logger.debug(f"[GasOracle] Gas API fetch error for {network}: {e}")
            return None
    
    def _fetch_from_rpc(self, network: str) -> Dict[str, Any]:
        """Fetch gas price from RPC endpoint using eth_gasPrice"""
        if network not in self.web3_connections:
            return self._get_fallback_price(network)
        
        try:
            w3 = self.web3_connections[network]
            gas_price_wei = w3.eth.gas_price
            gas_price_gwei = float(Web3.from_wei(gas_price_wei, 'gwei'))
            
            result = {
                'network': network,
                'chain_id': self.NETWORKS[network]['chain_id'],
                'price_gwei': gas_price_gwei,
                'low': gas_price_gwei * 0.9,
                'medium': gas_price_gwei,
                'high': gas_price_gwei * 1.1,
                'timestamp': time.time(),
                'source': 'rpc_eth_gasPrice'
            }
            
            logger.info(f"[GasOracle] ✓ {network.upper()}: {format_gas_price(gas_price_gwei)} (RPC)")
            return result
            
        except Exception as e:
            logger.warning(f"[GasOracle] RPC fetch failed for {network}: {e}")
            return self._get_fallback_price(network)
    
    def _get_fallback_price(self, network: str) -> Dict[str, Any]:
        """Return safe fallback gas price if both API and RPC fail"""
        # Updated fallback prices based on typical network gas costs (as of 2025)
        fallback_prices = {
            'ethereum': 30.0,      # ETH: ~30 gwei typical
            'polygon': 80.0,       # MATIC: ~80 gwei typical
            'arbitrum': 0.1,       # ARB: ~0.1 gwei (L2)
            'optimism': 0.002,     # OP: ~0.002 gwei (L2)
            'base': 0.001,         # BASE: ~0.001 gwei (L2)
            'bsc': 5.0,            # BNB: ~5 gwei typical
            'avalanche': 25.0,     # AVAX: ~25 gwei typical
            'blast': 0.001,        # BLAST: ~0.001 gwei (L2)
            'zksync': 0.25,        # ZKSYNC: ~0.25 gwei (L2)
            'linea': 0.5,          # LINEA: ~0.5 gwei (L2)
        }
        
        price = fallback_prices.get(network, 50.0)
        logger.warning(f"[GasOracle] Using fallback price for {network}: {format_gas_price(price)}")
        
        return {
            'network': network,
            'chain_id': self.NETWORKS[network]['chain_id'],
            'price_gwei': price,
            'timestamp': time.time(),
            'source': 'fallback',
            'low': price * 0.8,
            'medium': price,
            'high': price * 1.2,
        }
    
    def detect_gas_spike(self, current_gwei: float, network: str = 'polygon') -> bool:
        """
        Detect if current gas price is abnormally high (spike)
        
        Args:
            current_gwei: Current gas price in gwei
            network: Network to check
            
        Returns:
            True if gas spike detected
        """
        if network not in self.history or len(self.history[network]) < 5:
            return False  # Not enough data
        
        baseline = mean(self.history[network])
        threshold = baseline * (self.spike_threshold / 100.0)
        
        is_spike = current_gwei > threshold
        
        if is_spike:
            logger.warning(
                f"[GasOracle] ⚠️  GAS SPIKE on {network.upper()}! "
                f"Current: {format_gas_price(current_gwei)} | "
                f"Baseline: {format_gas_price(baseline)} | "
                f"Threshold: {format_gas_price(threshold)}"
            )
        
        return is_spike
    
    def validate_gas_for_transaction(
        self,
        estimated_gas_units: int,
        max_gas_price_gwei: float,
        network: str = 'polygon',
        safety_multiplier: float = 1.5
    ) -> Dict[str, Any]:
        """
        Validate if current gas conditions are acceptable for transaction
        
        Args:
            estimated_gas_units: Estimated gas consumption
            max_gas_price_gwei: Maximum acceptable gas price
            network: Network for transaction
            safety_multiplier: Safety buffer for gas cost
            
        Returns:
            Dict with validation result and gas cost estimate
        """
        # Fetch current gas price
        gas_data = self.fetch_gas_price(network)
        current_gas_gwei = gas_data['price_gwei']
        
        # Check if gas price is acceptable
        if current_gas_gwei > max_gas_price_gwei:
            return {
                'approved': False,
                'reason': f"Gas price too high: {format_gas_price(current_gas_gwei)} > {format_gas_price(max_gas_price_gwei)}",
                'current_gas_gwei': current_gas_gwei,
                'max_gas_gwei': max_gas_price_gwei,
                'estimated_cost_usd': 0
            }
        
        # Check for gas spike
        is_spike = self.detect_gas_spike(current_gas_gwei, network)
        if is_spike:
            return {
                'approved': False,
                'reason': f"Gas spike detected on {network}",
                'current_gas_gwei': current_gas_gwei,
                'is_spike': True,
                'estimated_cost_usd': 0
            }
        
        # Estimate gas cost (use high estimate for safety)
        high_gas_gwei = gas_data.get('high', current_gas_gwei)
        gas_cost_eth = (estimated_gas_units * high_gas_gwei * safety_multiplier) / 1e9
        
        # Convert to USD (use approximate prices)
        eth_prices = {'polygon': 0.5, 'ethereum': 3000, 'arbitrum': 3000, 'optimism': 3000, 'base': 3000}
        eth_price_usd = eth_prices.get(network, 1000)
        gas_cost_usd = gas_cost_eth * eth_price_usd
        
        return {
            'approved': True,
            'reason': 'Gas price acceptable',
            'current_gas_gwei': current_gas_gwei,
            'high_gas_gwei': high_gas_gwei,
            'estimated_cost_usd': gas_cost_usd,
            'estimated_gas_units': estimated_gas_units,
            'safety_multiplier': safety_multiplier,
            'network': network
        }
    
    def print_gas_report(self):
        """Print gas prices for all supported networks"""
        print("\n" + "=" * 80)
        print("  GAS ORACLE REPORT - REAL-TIME NETWORK GAS PRICES")
        print("  Source: Infura Gas API")
        print("=" * 80 + "\n")
        
        for network in self.NETWORKS.keys():
            try:
                gas_data = self.fetch_gas_price(network, force_update=True)
                print(f"  {network.upper()}:")
                print(f"    Low:    {format_gas_price(gas_data.get('low', 0))}")
                print(f"    Medium: {format_gas_price(gas_data.get('medium', 0))}")
                print(f"    High:   {format_gas_price(gas_data.get('high', 0))}")
                print(f"    Source: {gas_data.get('source', 'unknown')}")
                print()
            except Exception as e:
                print(f"  {network.upper()}: Error - {e}\n")
        
        print("=" * 80 + "\n")


# Example usage
if __name__ == "__main__":
    print("Initializing Gas Oracle Integration...")
    
    oracle = GasOracleIntegration(
        update_interval_seconds=12,
        spike_threshold_percent=150.0,
        max_gas_price_gwei=150.0
    )
    
    # Print initial report
    oracle.print_gas_report()
    
    # Test validation for Polygon
    print("\nTesting gas validation for Polygon arbitrage transaction...")
    validation = oracle.validate_gas_for_transaction(
        estimated_gas_units=500000,
        max_gas_price_gwei=200.0,
        network='polygon',
        safety_multiplier=1.5
    )
    
    print(f"  Network: {validation.get('network', 'polygon').upper()}")
    print(f"  Approved: {validation['approved']}")
    print(f"  Current Gas: {format_gas_price(validation.get('current_gas_gwei', 0))}")
    print(f"  Estimated Cost: {fmt_usd(validation.get('estimated_cost_usd', 0))}")
    print(f"  Reason: {validation['reason']}")
