#!/usr/bin/env python
"""
RPC Rotation Manager
Rotates through all available RPC endpoints to avoid rate limits
Assigns specific endpoints to specific tasks for optimal performance
"""

import os
import time
import random
from typing import Dict, List, Optional
from web3 import Web3


class RPCRotationManager:
    """
    Manages rotation of RPC endpoints to avoid rate limits
    Assigns endpoints to specific tasks based on their strengths
    """
    
    def __init__(self):
        # Load all RPC endpoints from environment
        self.polygon_endpoints = {
            'alchemy_primary': os.getenv('ALCHEMY_RPC_URL', ''),
            'alchemy_http': os.getenv('INFURA_POLYGON_RPC_HTTP', ''),
            'quicknode': os.getenv('QUICKNODE_RPC_URL', ''),
            'polygon_main': os.getenv('POLYGON_RPC_URL', ''),
        }
        
        self.ethereum_endpoints = {
            'infura': os.getenv('ETHEREUM_RPC_URL', ''),
        }
        
        self.arbitrum_endpoints = {
            'quicknode': os.getenv('ARBITRUM_RPC_URL', ''),
        }
        
        self.optimism_endpoints = {
            'quicknode': os.getenv('OPTIMISM_RPC_URL', ''),
        }
        
        # Gas API endpoint
        self.gas_api_url = "https://gas.api.infura.io/v3/ed05b301f1a949f59bfbc1c128910937"
        
        # Task-specific endpoint assignments
        self.task_assignments = {
            'block_fetching': ['alchemy_primary', 'quicknode'],
            'transaction_data': ['alchemy_http', 'quicknode'],
            'pool_data': ['polygon_main', 'alchemy_primary'],
            'gas_estimation': ['quicknode', 'alchemy_primary'],
            'event_listening': ['alchemy_primary'],  # Best for websockets
        }
        
        # Rate limit tracking
        self.request_counts = {}
        self.last_request_time = {}
        self.rate_limits = {
            'alchemy_primary': 100,  # requests per second
            'alchemy_http': 100,
            'quicknode': 50,
            'polygon_main': 50,
            'infura': 10,
        }
        
        # Connection pool
        self.connections = {}
        self._initialize_connections()
        
        print(f"[RPCRotation] ✓ Initialized with {len(self.polygon_endpoints)} Polygon endpoints")
    
    def _initialize_connections(self):
        """Initialize Web3 connections for all endpoints"""
        for name, url in self.polygon_endpoints.items():
            if url:
                try:
                    self.connections[name] = Web3(Web3.HTTPProvider(url))
                    print(f"[RPCRotation] ✓ Connected to {name}")
                except Exception as e:
                    print(f"[RPCRotation] ⚠ Failed to connect to {name}: {e}")
    
    def get_endpoint_for_task(self, task: str, chain: str = 'polygon') -> tuple:
        """
        Get best endpoint for a specific task
        
        Args:
            task: Task type (block_fetching, transaction_data, pool_data, etc.)
            chain: Blockchain network
        
        Returns:
            (endpoint_name, web3_instance)
        """
        # Get assigned endpoints for this task
        assigned = self.task_assignments.get(task, list(self.polygon_endpoints.keys()))
        
        # Filter available endpoints
        available = [ep for ep in assigned if ep in self.connections and self._check_rate_limit(ep)]
        
        if not available:
            # Fallback to any available endpoint
            available = [ep for ep in self.connections.keys() if self._check_rate_limit(ep)]
        
        if not available:
            # Wait for rate limits to reset
            time.sleep(1)
            available = list(self.connections.keys())
        
        # Select endpoint (round-robin or random)
        endpoint = random.choice(available)
        
        # Track usage
        self._record_request(endpoint)
        
        return endpoint, self.connections[endpoint]
    
    def _check_rate_limit(self, endpoint: str) -> bool:
        """Check if endpoint is within rate limits"""
        current_time = time.time()
        
        if endpoint not in self.request_counts:
            self.request_counts[endpoint] = 0
            self.last_request_time[endpoint] = current_time
            return True
        
        # Reset counter if 1 second has passed
        if current_time - self.last_request_time[endpoint] >= 1.0:
            self.request_counts[endpoint] = 0
            self.last_request_time[endpoint] = current_time
            return True
        
        # Check if within limit
        return self.request_counts[endpoint] < self.rate_limits.get(endpoint, 10)
    
    def _record_request(self, endpoint: str):
        """Record a request to an endpoint"""
        if endpoint not in self.request_counts:
            self.request_counts[endpoint] = 0
        self.request_counts[endpoint] += 1
    
    def get_gas_price(self, chain: str = 'polygon') -> Dict:
        """
        Get accurate gas price from Infura Gas API
        
        Returns:
            dict with gas prices in gwei
        """
        import requests
        
        try:
            response = requests.get(self.gas_api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Polygon gas prices are in gwei
            if chain == 'polygon':
                return {
                    'slow': float(data.get('low', 30)),
                    'standard': float(data.get('medium', 50)),
                    'fast': float(data.get('high', 100)),
                    'instant': float(data.get('high', 100)) * 1.2,
                    'base_fee': float(data.get('baseFee', 30)),
                    'priority_fee': float(data.get('priorityFee', 20)),
                }
        except Exception as e:
            print(f"[RPCRotation] ⚠ Gas API error: {e}")
            
            # Fallback to on-chain gas price
            endpoint, w3 = self.get_endpoint_for_task('gas_estimation', chain)
            try:
                gas_price_wei = w3.eth.gas_price
                gas_price_gwei = w3.from_wei(gas_price_wei, 'gwei')
                
                return {
                    'slow': gas_price_gwei * 0.8,
                    'standard': gas_price_gwei,
                    'fast': gas_price_gwei * 1.2,
                    'instant': gas_price_gwei * 1.5,
                    'base_fee': gas_price_gwei,
                    'priority_fee': gas_price_gwei * 0.1,
                }
            except Exception as e2:
                print(f"[RPCRotation] ⚠ Fallback gas estimation error: {e2}")
                # Final fallback - typical Polygon values
                return {
                    'slow': 30.0,
                    'standard': 50.0,
                    'fast': 100.0,
                    'instant': 150.0,
                    'base_fee': 30.0,
                    'priority_fee': 20.0,
                }
    
    def calculate_gas_cost_usd(self, gas_units: int, speed: str = 'fast', chain: str = 'polygon') -> float:
        """
        Calculate gas cost in USD
        
        Args:
            gas_units: Gas units required
            speed: Gas speed (slow, standard, fast, instant)
            chain: Blockchain network
        
        Returns:
            Gas cost in USD
        """
        gas_prices = self.get_gas_price(chain)
        gas_price_gwei = gas_prices.get(speed, gas_prices['standard'])
        
        # Convert to wei
        gas_price_wei = gas_price_gwei * 1e9
        
        # Calculate total cost in wei
        total_cost_wei = gas_units * gas_price_wei
        
        # Convert to ETH/MATIC
        total_cost_native = total_cost_wei / 1e18
        
        # Convert to USD (approximate prices)
        native_prices_usd = {
            'polygon': 0.60,  # MATIC price
            'ethereum': 3500,  # ETH price
            'arbitrum': 3500,  # ETH on Arbitrum
            'optimism': 3500,  # ETH on Optimism
        }
        
        native_price = native_prices_usd.get(chain, 1.0)
        total_cost_usd = total_cost_native * native_price
        
        return total_cost_usd
    
    def print_statistics(self):
        """Print usage statistics"""
        print("\n" + "=" * 80)
        print("  RPC ROTATION MANAGER STATISTICS")
        print("=" * 80)
        
        print(f"\n  Active Endpoints:")
        for name, conn in self.connections.items():
            is_connected = conn.is_connected() if hasattr(conn, 'is_connected') else True
            status = "✓" if is_connected else "✗"
            requests = self.request_counts.get(name, 0)
            print(f"    {status} {name}: {requests} requests")
        
        print(f"\n  Gas Prices (Polygon):")
        gas_prices = self.get_gas_price('polygon')
        for speed, price in gas_prices.items():
            print(f"    {speed}: {price:.2f} gwei")
        
        print("=" * 80 + "\n")


# Example usage
if __name__ == "__main__":
    manager = RPCRotationManager()
    
    # Test gas price fetching
    print("\n🔥 Testing Gas Price API:")
    gas = manager.get_gas_price('polygon')
    print(f"  Standard: {gas['standard']:.2f} gwei")
    print(f"  Fast: {gas['fast']:.2f} gwei")
    
    # Test gas cost calculation
    gas_cost = manager.calculate_gas_cost_usd(500000, 'fast', 'polygon')
    print(f"\n💰 Gas Cost for 500K units (fast): ${gas_cost:.4f}")
    
    # Test endpoint rotation
    print("\n🔄 Testing Endpoint Rotation:")
    for i in range(5):
        endpoint, w3 = manager.get_endpoint_for_task('block_fetching')
        print(f"  Request {i+1}: Using {endpoint}")
    
    manager.print_statistics()
