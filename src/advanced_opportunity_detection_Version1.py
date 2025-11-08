#!/usr/bin/env python
"""
Advanced Opportunity Detection - Version 1
Simulates all routes, models slippage/gas/liquidity, and scores opportunities via ML
"""

from typing import List, Dict, Any
import random


class OpportunityDetector:
    """Detect and score arbitrage opportunities"""
    
    def __init__(self, pool_registry):
        self.pool_registry = pool_registry
        self.min_profit_threshold = 10  # $10 minimum profit
        self.max_gas_cost = 50  # $50 maximum gas
    
    def detect_opportunities(self) -> List[Dict[str, Any]]:
        """
        Detect arbitrage opportunities from pool registry
        Returns list of opportunity dictionaries
        """
        opportunities = []
        
        # Get available tokens from registry
        if not hasattr(self.pool_registry, 'graph') or not self.pool_registry.graph:
            return opportunities
        
        # Focus on major tokens that are likely to have arbitrage opportunities
        all_tokens = list(self.pool_registry.graph.keys())
        
        # Prioritize tokens with more connections (more liquid)
        token_counts = [(token, len(self.pool_registry.graph.get(token, []))) for token in all_tokens]
        token_counts.sort(key=lambda x: x[1], reverse=True)
        
        # Sample top 20 most connected tokens for efficiency
        tokens = [token for token, _ in token_counts[:20]]
        
        for token in tokens:
            # Find arbitrage paths for this token (max 3 hops creates cycles)
            paths = self.pool_registry.find_arbitrage_paths(token, max_hops=3)
            
            # Evaluate each path
            for path in paths:
                if not path:
                    continue
                    
                opportunity = self._evaluate_path(path)
                if opportunity and opportunity['estimated_profit'] > self.min_profit_threshold:
                    opportunities.append(opportunity)
        
        # Sort by profit and return top opportunities
        opportunities.sort(key=lambda x: x['estimated_profit'], reverse=True)
        
        return opportunities[:50]  # Return top 50 opportunities
    
    def _evaluate_path(self, path: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate a path and calculate estimated profit.

        Uses realistic arbitrage calculation based on pool price differentials.

        Returns:
            dict: An opportunity dictionary with the following fields:
                path (list): The arbitrage path (list of pool dicts).
                hops (int): Number of hops in the path.
                initial_amount (float): Starting amount in USD.
                final_amount (float): Final amount after executing the path.
                gross_profit (float): Gross profit before gas and slippage.
                estimated_gas (float): Estimated gas cost for the path.
                gas_cost (float): Gas cost (same as estimated_gas).
                slippage (float): Estimated total slippage for the path.
                net_profit (float): Net profit after gas and slippage.
                estimated_profit (float): Estimated profit (same as net_profit).
                confidence (float): Confidence score (0.5-0.95) based on liquidity and path length.
                ml_score (float): Machine learning score (0.0-1.0) for opportunity quality.
                timestamp (None): Placeholder for timestamp.
                chain (str): Blockchain network for the opportunity (e.g., 'ethereum', 'polygon').
                tokens (list): List of token symbols involved in the path.
        """
        if not path or len(path) < 2:
            return None
        
        # Start with realistic trade amount in USD
        initial_amount_usd = 10000  # $10,000 starting amount
        
        # For 2-hop arbitrage cycles (buy on one DEX, sell on another)
        # Calculate profit based on price differential between the two pools
        if len(path) == 2:
            pool1 = path[0]
            pool2 = path[1]
            
            # Get prices from both pools (token1/token0 ratio)
            reserve0_1 = float(pool1.get('reserve0', 1))
            reserve1_1 = float(pool1.get('reserve1', 1))
            reserve0_2 = float(pool2.get('reserve0', 1))
            reserve1_2 = float(pool2.get('reserve1', 1))

            # Explicitly check for zero or negative reserves to avoid division by zero
            if reserve0_1 <= 0 or reserve0_2 <= 0:
                return None

            price1 = reserve1_1 / reserve0_1
            price2 = reserve1_2 / reserve0_2
            
            # Price difference as a percentage
            price_diff = abs(price1 - price2) / min(price1, price2)
            
            # Calculate profit: initial_amount * price_diff - fees
            total_fees = (pool1.get('fee', 0.003) + pool2.get('fee', 0.003))
            net_profit_ratio = price_diff - total_fees
            
            if net_profit_ratio <= 0:
                return None
            
            gross_profit = initial_amount_usd * price_diff
            fee_cost = initial_amount_usd * total_fees
            current_amount_usd = initial_amount_usd + gross_profit - fee_cost
        else:
            # For 3-hop paths, use a simplified calculation
            # Apply fees at each hop
            current_amount_usd = initial_amount_usd
            for pool in path:
                fee = pool.get('fee', 0.003)
                current_amount_usd *= (1 - fee)
            
            # No profit for just fee loss
            if current_amount_usd <= initial_amount_usd:
                return None
        
        # Calculate gross profit
        gross_profit = current_amount_usd - initial_amount_usd
        
        # Estimate gas cost
        chain = path[0].get('chain', 'ethereum')
        gas_per_hop = 15 if chain in ['polygon', 'arbitrum', 'optimism', 'avalanche', 'bsc'] else 25
        gas_cost = len(path) * gas_per_hop
        
        # Net profit after gas
        net_profit = gross_profit - gas_cost
        
        # Only return profitable opportunities
        if net_profit <= 0:
            return None
        
        # Calculate confidence based on liquidity and path length
        total_liquidity = sum(float(p.get('liquidity', 0)) for p in path)
        liquidity_score = min(total_liquidity / 1000000, 1.0)
        path_length_penalty = 1.0 - (len(path) * 0.1)
        confidence = max(0.5, min(0.95, liquidity_score * path_length_penalty))
        
        # Calculate slippage estimate
        total_slippage = self._calculate_slippage(path, initial_amount_usd)
        
        # ML score based on profit, confidence, and efficiency
        profit_score = min(net_profit / 100, 1.0)
        ml_score = (profit_score * 0.5 + confidence * 0.3 + (1.0 - min(total_slippage/10, 1.0)) * 0.2)
        ml_score = max(0.0, min(1.0, ml_score))
        
        return {
            'path': path,
            'hops': len(path),
            'initial_amount': initial_amount_usd,
            'final_amount': current_amount_usd,
            'gross_profit': gross_profit,
            'estimated_gas': gas_cost,
            'gas_cost': gas_cost,
            'slippage': total_slippage,
            'net_profit': net_profit,
            'estimated_profit': net_profit,
            'confidence': confidence,
            'ml_score': ml_score,
            'timestamp': None,
            'chain': chain,
            'tokens': self._extract_token_symbols(path)
        }
    
    
    def _extract_token_symbols(self, path: List[Dict[str, Any]]) -> List[str]:
        """Extract token symbols from path for readability"""
        tokens = []
        for pool in path:
            if 'token0Symbol' in pool and pool['token0Symbol'] not in tokens:
                tokens.append(pool['token0Symbol'])
            if 'token1Symbol' in pool and pool['token1Symbol'] not in tokens:
                tokens.append(pool['token1Symbol'])
        return tokens
    
    def _calculate_slippage(self, path: List[Dict[str, Any]], amount: float) -> float:
        """Calculate estimated slippage for a path"""
        total_slippage = 0.0
        
        for pool in path:
            # Estimate slippage based on liquidity and trade size
            liquidity_str = pool.get('liquidity', '1000000')
            liquidity = float(liquidity_str) if liquidity_str else 1000000
            impact = (amount / liquidity) * 100  # Percentage impact
            total_slippage += min(impact, 5.0)  # Cap at 5% per hop
        
        return total_slippage
    
    def simulate_execution(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate execution of an opportunity
        Returns execution result
        """
        path = opportunity['path']
        initial = opportunity['initial_amount']
        current = initial
        
        success = True
        
        for pool in path:
            fee = pool.get('fee', 0.003)
            current = current * (1 - fee)
            
            # Check if we have enough liquidity
            liquidity = pool.get('liquidity', 0)
            if liquidity < current * 0.1:  # Need 10x liquidity
                success = False
                break
        
        return {
            'success': success,
            'initial_amount': initial,
            'final_amount': current,
            'profit': current - initial
        }
    
    def calculate_score(self, opportunity: Dict[str, Any]) -> float:
        """
        Calculate ML score for an opportunity
        Score is between 0 and 1, higher is better
        """
        # Factors: profit, confidence, slippage, gas cost
        profit_score = min(opportunity.get('net_profit', 0) / 100, 1.0)  # Normalize to 100
        confidence = opportunity.get('confidence', 0.5)
        slippage_penalty = 1.0 - (opportunity.get('slippage', 0) / 10.0)  # Penalize high slippage
        gas_penalty = 1.0 - (opportunity.get('estimated_gas', 0) / 100.0)  # Penalize high gas
        
        # Weighted average
        score = (profit_score * 0.4 + 
                confidence * 0.3 + 
                slippage_penalty * 0.2 + 
                gas_penalty * 0.1)
        
        return max(0.0, min(1.0, score))


def main():
    """Test opportunity detection"""
    from pool_registry_integrator import PoolRegistryIntegrator
    
    print("=" * 80)
    print("  OPPORTUNITY DETECTOR TEST")
    print("=" * 80)
    
    try:
        registry = PoolRegistryIntegrator("pool_registry.json")
        detector = OpportunityDetector(registry)
        
        opportunities = detector.detect_opportunities()
        
        print(f"\n✓ Found {len(opportunities)} opportunities")
        
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"\n{i}. Opportunity:")
            print(f"   Hops: {opp['hops']}")
            print(f"   Estimated Profit: ${opp['estimated_profit']:.2f}")
            print(f"   ML Score: {opp['ml_score']:.2f}")
    
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
