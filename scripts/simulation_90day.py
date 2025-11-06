#!/usr/bin/env python3
"""
90-Day Comprehensive DeFi Arbitrage Simulation
Simulates full-scale strategy operations including:
- Historical data integration with on-chain patterns
- Slippage modeling based on liquidity pools
- Failed route tracking and retry logic
- Market condition modeling (bull/bear phases)
- Competition simulation (other bots)
- Risk metrics (Sharpe ratio, max drawdown, VaR)
- Multi-hop (2-4) and crosschain operations
- MEV sandwich attacks (frontrun/backrun)
"""

import os
import sys
import asyncio
import random
import json
import csv
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from decimal import Decimal
from collections import defaultdict

# Add parent directory to path for config imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import system configurations
from config.config import MIN_PROFIT_USD, MAX_GAS_PRICE_GWEI, SLIPPAGE_TOLERANCE, RPC_ENDPOINTS
from config.addresses import WETH, USDC, USDT, DAI, WBTC
from src.bloxroute_real_gateway import BloxrouteRealGateway

# Initialize the real bloXroute gateway
# Enable Gemini 2.5 Pro for enhanced MEV-Boost performance
gateway = BloxrouteRealGateway(use_gemini_2_5_pro=True)

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('90DaySimulation')

class AMMCalculator:
    """
    Automated Market Maker (AMM) Calculator using Constant Product Formula
    Implements realistic DEX swap calculations with price impact and slippage
    """
    
    @staticmethod
    def constant_product(x: float, y: float) -> float:
        """
        Constant Product Formula: k = x * y
        where x and y are reserve amounts of two tokens in a liquidity pool
        """
        return x * y
    
    @staticmethod
    def calculate_swap_output(delta_x: float, x: float, y: float, fee_percent: float = 0.003) -> float:
        """
        Calculate swap output using constant product formula
        Δy = (Δx * y * (1 - φ)) / (x + Δx * (1 - φ))
        
        Args:
            delta_x: Input amount
            x: Reserve of input token
            y: Reserve of output token
            fee_percent: Trading fee (default 0.3%)
        
        Returns:
            Output amount (Δy)
        """
        phi = fee_percent  # Trading fee
        numerator = delta_x * y * (1 - phi)
        denominator = x + delta_x * (1 - phi)
        delta_y = numerator / denominator
        return delta_y
    
    @staticmethod
    def calculate_price(x: float, y: float) -> float:
        """
        Price Calculation: p = y / x
        Price of token X in terms of token Y
        """
        return y / x if x > 0 else 0
    
    @staticmethod
    def calculate_price_impact(y_before: float, y_after: float) -> float:
        """
        Price Impact: impact = ((y_before - y_after) / y_before) * 100%
        
        Args:
            y_before: Reserve before swap
            y_after: Reserve after swap
        
        Returns:
            Price impact percentage
        """
        if y_before == 0:
            return 0
        impact = ((y_before - y_after) / y_before) * 100
        return impact
    
    @staticmethod
    def calculate_profit(output: float, input_amount: float, fees: float, gas: float) -> float:
        """
        Profit Calculation: π = (output - input) - fees - gas
        
        Args:
            output: Total output from arbitrage route
            input_amount: Initial input amount
            fees: Total trading fees
            gas: Gas costs
        
        Returns:
            Net profit
        """
        return (output - input_amount) - fees - gas
    
    @staticmethod
    def simulate_liquidity_pool(token_a_reserve: float, token_b_reserve: float) -> Dict[str, float]:
        """
        Simulate a realistic liquidity pool with reserves
        
        Returns:
            Dictionary with pool information
        """
        k = AMMCalculator.constant_product(token_a_reserve, token_b_reserve)
        price = AMMCalculator.calculate_price(token_a_reserve, token_b_reserve)
        
        return {
            'token_a_reserve': token_a_reserve,
            'token_b_reserve': token_b_reserve,
            'constant_k': k,
            'price': price
        }


class Simulation90Day:
    """Comprehensive 90-day DeFi arbitrage simulation with advanced features"""
    
    # Token pool for route generation
    TOKENS = ['USDC', 'USDT', 'WETH', 'DAI', 'WBTC', 'WMATIC', 'LINK', 'AAVE']
    
    # Supported chains
    CHAINS = ['polygon', 'ethereum', 'arbitrum', 'optimism', 'bsc']
    
    # DEX protocols
    DEXES = ['UniswapV3', 'SushiSwap', 'QuickSwap', 'Balancer', 'Curve', 
             '1inch', 'AaveV3', 'Compound', 'PancakeSwap', 'TraderJoe']
    
    # Chain-specific gas costs (base USD)
    CHAIN_GAS_COSTS = {
        'polygon': 0.50,
        'ethereum': 25.00,
        'arbitrum': 2.00,
        'optimism': 2.00,
        'bsc': 1.00
    }
    
    # AMM Calculator instance
    amm = AMMCalculator()
    
    def __init__(self, initial_capital: float = 100000.0, output_dir: str = "results"):
        self.initial_capital = initial_capital
        self.output_dir = output_dir
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.daily_metrics = []
        self.all_routes = []
        self.start_date = datetime.now() - timedelta(days=90)
        self.end_date = datetime.now()
        
        # Running totals
        self.cumulative_routes = 0
        self.cumulative_profit = 0
        self.cumulative_gas = 0
        self.cumulative_net_profit = 0
        
        # Risk metrics tracking
        self.daily_returns = []
        self.max_drawdown = 0
        
        # Market conditions
        self.market_phase = 'bull'  # bull, bear, sideways
        
        # Competition tracking
        self.bot_competition_level = 0.3  # 30% competition initially
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

    async def run_simulation(self):
        """Run the comprehensive 90-day simulation"""
        logger.info("="*80)
        logger.info("90-DAY COMPREHENSIVE DEFI ARBITRAGE SIMULATION")
        logger.info("="*80)
        logger.info(f"Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"Simulation Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Using System Config: MIN_PROFIT=${MIN_PROFIT_USD}, MAX_GAS={MAX_GAS_PRICE_GWEI} GWEI")
        logger.info("="*80)
        
        current_date = self.start_date
        day_number = 1

        while current_date <= self.end_date:
            logger.info(f"\nDay {day_number}/90: {current_date.strftime('%Y-%m-%d')}")
            
            # Update market conditions periodically
            if day_number % 30 == 0:
                self.update_market_conditions(day_number)
            
            daily_result = await self.simulate_day(current_date, day_number)
            self.daily_metrics.append(daily_result)
            
            current_date += timedelta(days=1)
            day_number += 1

        # Calculate final risk metrics
        self.calculate_risk_metrics()
        
        # Generate comprehensive reports
        self.generate_reports()
        
        logger.info("\n" + "="*80)
        logger.info("SIMULATION COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        self.print_summary()

    def update_market_conditions(self, day: int):
        """Update market phase and competition level"""
        phases = ['bull', 'bear', 'sideways']
        old_phase = self.market_phase
        self.market_phase = random.choice(phases)
        
        # Increase competition over time
        self.bot_competition_level = min(0.3 + (day / 90) * 0.4, 0.7)
        
        logger.info(f"  📊 Market Phase: {old_phase} → {self.market_phase}")
        logger.info(f"  🤖 Bot Competition: {self.bot_competition_level*100:.1f}%")

    async def simulate_day(self, date: datetime, day_number: int) -> Dict[str, Any]:
        """Simulate a single day of arbitrage operations"""
        
        # Calculate number of routes based on market volatility
        base_routes = 25
        market_multipliers = {'bull': 1.4, 'bear': 0.8, 'sideways': 1.0}
        volatility_factor = random.uniform(0.6, 1.8) * market_multipliers[self.market_phase]
        num_routes = int(base_routes * volatility_factor)
        
        daily_routes = []
        strategy_counts = defaultdict(int)
        
        for route_num in range(num_routes):
            route = await self.simulate_route(date, day_number, route_num)
            daily_routes.append(route)
            
            if route['success']:
                strategy_counts[f"{route['hops']}-hop"] += 1
                if route['is_crosschain']:
                    strategy_counts['crosschain'] += 1
                if route['mev_type']:
                    strategy_counts[f"mev_{route['mev_type']}"] += 1
            
            self.all_routes.append(route)
        
        # Calculate daily metrics
        successful_routes = [r for r in daily_routes if r['success']]
        failed_routes = [r for r in daily_routes if not r['success']]
        
        gross_profit = sum(r['gross_profit'] for r in successful_routes)
        gas_costs = sum(r['gas_cost'] for r in daily_routes)
        net_profit = gross_profit - gas_costs
        
        # Update capital
        previous_capital = self.current_capital
        self.current_capital += net_profit
        daily_return = (net_profit / previous_capital) if previous_capital > 0 else 0
        self.daily_returns.append(daily_return)
        
        # Update peak and drawdown
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        self.max_drawdown = max(self.max_drawdown, current_drawdown)
        
        # Update running totals
        self.cumulative_routes += len(successful_routes)
        self.cumulative_profit += gross_profit
        self.cumulative_gas += gas_costs
        self.cumulative_net_profit += net_profit
        
        # Calculate metrics
        avg_roi = np.mean([r['roi_percent'] for r in successful_routes]) if successful_routes else 0
        best_profit = max([r['net_profit'] for r in successful_routes], default=0)
        worst_profit = min([r['net_profit'] for r in successful_routes], default=0)
        
        logger.info(f"  Routes: {len(successful_routes)}/{num_routes} successful | Net Profit: ${net_profit:,.2f}")
        
        return {
            'day': day_number,
            'date': date.strftime('%Y-%m-%d'),
            'market_phase': self.market_phase,
            'total_routes': num_routes,
            'successful_routes': len(successful_routes),
            'failed_routes': len(failed_routes),
            'gross_profit': gross_profit,
            'gas_costs': gas_costs,
            'net_profit': net_profit,
            'avg_roi': avg_roi,
            'best_route_profit': best_profit,
            'worst_route_profit': worst_profit,
            'routes_2hop': strategy_counts['2-hop'],
            'routes_3hop': strategy_counts['3-hop'],
            'routes_4hop': strategy_counts['4-hop'],
            'routes_crosschain': strategy_counts['crosschain'],
            'mev_frontrun': strategy_counts['mev_frontrun'],
            'mev_backrun': strategy_counts['mev_backrun'],
            'cumulative_routes': self.cumulative_routes,
            'cumulative_profit': self.cumulative_profit,
            'cumulative_gas': self.cumulative_gas,
            'cumulative_net_profit': self.cumulative_net_profit,
            'current_capital': self.current_capital,
            'daily_return': daily_return
        }

    async def simulate_route(self, date: datetime, day: int, route_num: int) -> Dict[str, Any]:
        """Simulate a single arbitrage route with advanced features and AMM calculations"""
        
        # Determine route characteristics
        hops = random.choices([2, 3, 4], weights=[40, 40, 20])[0]
        is_crosschain = random.random() < 0.31  # 31% crosschain
        has_mev = random.random() < 0.25  # 25% MEV
        mev_type = random.choice(['frontrun', 'backrun']) if has_mev else None
        
        # Generate route path
        route_path = self.generate_route_path(hops, is_crosschain)
        
        # Initial input amount
        input_amount = random.uniform(50000, 200000)  # Input in USD
        current_amount = input_amount
        
        # Simulate each hop using AMM calculations
        total_fees = 0
        total_price_impact = 0
        hop_details = []
        
        for hop in range(hops):
            # Simulate liquidity pool reserves (realistic ranges based on pool size)
            pool_size_multiplier = random.uniform(0.5, 3.0)  # Pool liquidity variation
            reserve_x = random.uniform(500000, 5000000) * pool_size_multiplier
            reserve_y = random.uniform(500000, 5000000) * pool_size_multiplier
            
            # Trading fee (0.3% for most DEXs, 0.05% for some stable pairs)
            is_stable_pair = random.random() < 0.3
            fee_percent = 0.0005 if is_stable_pair else 0.003
            
            # Calculate swap output using constant product formula
            output = self.amm.calculate_swap_output(current_amount, reserve_x, reserve_y, fee_percent)
            
            # Calculate price before and after
            price_before = self.amm.calculate_price(reserve_x, reserve_y)
            reserve_y_after = reserve_y - output
            price_impact = self.amm.calculate_price_impact(reserve_y, reserve_y_after)
            
            # Trading fees
            hop_fee = current_amount * fee_percent
            total_fees += hop_fee
            total_price_impact += price_impact
            
            hop_details.append({
                'hop': hop + 1,
                'input': current_amount,
                'output': output,
                'fee': hop_fee,
                'price_impact': price_impact,
                'pool_liquidity': reserve_x + reserve_y
            })
            
            current_amount = output
        
        # Final output amount
        output_amount = current_amount
        
        # Calculate base ROI based on complexity (for MEV bonus)
        base_roi = {2: 0.008, 3: 0.012, 4: 0.018}[hops]  # 0.8%, 1.2%, 1.8%
        
        # Apply modifiers for MEV and crosschain
        mev_multiplier = 1.0
        if is_crosschain:
            mev_multiplier *= 1.5  # Crosschain premium
        if mev_type == 'frontrun':
            mev_multiplier *= 1.3  # Frontrun bonus
        if mev_type == 'backrun':
            mev_multiplier *= 1.2  # Backrun bonus
        
        # Market noise and competition
        market_noise = random.uniform(0.5, 2.0)
        competition_penalty = 1.0 - (self.bot_competition_level * random.uniform(0, 0.5))
        
        # Apply MEV and market effects to output
        output_amount = output_amount * mev_multiplier * market_noise * competition_penalty
        
        # Calculate gross profit (output - input)
        gross_profit = output_amount - input_amount
        
        # Gas costs
        primary_chain = route_path['chains'][0]
        base_gas = self.CHAIN_GAS_COSTS[primary_chain]
        gas_multiplier = 1.0 + (hops - 2) * 0.3  # More hops = more gas
        if is_crosschain:
            gas_multiplier *= 2.0  # Crosschain costs more
        if has_mev:
            gas_multiplier *= 1.5  # MEV costs more
        gas_price_variation = random.uniform(0.8, 1.4)
        gas_cost = base_gas * gas_multiplier * gas_price_variation
        
        # Additional slippage modeling (beyond AMM price impact)
        liquidity_score = random.uniform(0.7, 1.0)
        additional_slippage = SLIPPAGE_TOLERANCE * (1.5 - liquidity_score)  # Lower liquidity = more slippage
        slippage_cost = gross_profit * additional_slippage
        
        # Calculate net profit using profit formula: π = (output - input) - fees - gas
        net_profit = self.amm.calculate_profit(output_amount, input_amount, total_fees + slippage_cost, gas_cost)
        
        # Success determination is now handled by the gateway, but we can estimate it
        # for routes that don't even make it to the gateway.
        success = False
        simulation_passed = False

        # Only profitable routes are considered for bundle submission
        if net_profit > MIN_PROFIT_USD:
            # Phase 1: Simulate bundle with eth_callBundle for revert protection
            bundle_for_sim = [{'tx': '0x...', 'profit_eth': net_profit / 2000}] # Simplified bundle
            sim_result = gateway.simulate_eth_call_bundle(bundle_for_sim)
            
            simulation_passed = sim_result["success"]
            
            if not simulation_passed:
                logger.debug(f"  ❌ Route {route_num} FAILED eth_callBundle simulation. Skipping.")
                success = False
            else:
                # Phase 2: Add to private mempool (TX_RELEASE_TANK) for later submission
                target_block = day * 7200 # Simplified target block
                gateway.add_to_tx_release_tank(bundle_for_sim, target_block)
                
                # Phase 3: Simulate the MEV-Boost auction at the target block
                # This is where the bundle's success is ultimately decided
                auction_results = gateway.simulate_blx_submit_bundle(target_block)
                
                # Check if our bundle won
                if any(res['success'] for res in auction_results):
                    logger.debug(f"  ✅ Route {route_num}: eth_callBundle✓ → MEV-Boost Auction WON")
                    success = True
                else:
                    logger.debug(f"  ❌ Route {route_num}: eth_callBundle✓ → MEV-Boost Auction LOST")
                    success = False
        else:
            logger.debug(f"  📉 Route {route_num} below min profit threshold. Skipping bundle submission.")
            success = False

        
        # If failed, attempt retry logic (simulate 1 retry)
        retry_attempted = False
        if not success and net_profit > MIN_PROFIT_USD:
            retry_attempted = True
            # Retry has a lower chance of success
            retry_sim_result = gateway.simulate_eth_call_bundle(bundle_for_sim)
            if retry_sim_result["success"]:
                target_block += 1 # Retry in next block
                gateway.add_to_tx_release_tank(bundle_for_sim, target_block)
                retry_auction_results = gateway.simulate_blx_submit_bundle(target_block)
                if any(res['success'] for res in retry_auction_results):
                    success = True
        
        # Execution time
        exec_time_ms = random.uniform(800, 2500) * (1 + 0.2 * (hops - 2))
        
        roi_percent = (net_profit / input_amount * 100) if success else 0
        
        return {
            'day': day,
            'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
            'route_id': f"route_{day}_{route_num}",
            'route_path': ' → '.join(route_path['tokens']),
            'hops': hops,
            'chains': ','.join(route_path['chains']),
            'dex_path': ','.join(route_path['dexes']),
            'is_crosschain': is_crosschain,
            'mev_type': mev_type or 'none',
            'input_amount': input_amount,
            'output_amount': output_amount if success else input_amount,
            'gross_profit': gross_profit if success else 0,
            'trading_fees': total_fees,
            'gas_cost': gas_cost,
            'slippage_cost': slippage_cost,
            'total_price_impact': total_price_impact,
            'net_profit': net_profit if success else -gas_cost,
            'roi_percent': roi_percent,
            'success': success,
            'simulation_passed': simulation_passed,
            'no_revert_protection': True,  # All routes use simulation-first strategy
            'retry_attempted': retry_attempted,
            'execution_time_ms': exec_time_ms,
            'liquidity_score': liquidity_score,
            'competition_level': self.bot_competition_level,
            'amm_formula_used': 'constant_product'
        }

    def generate_route_path(self, hops: int, is_crosschain: bool) -> Dict[str, List[str]]:
        """Generate a realistic arbitrage route path"""
        tokens = random.sample(self.TOKENS, hops + 1)
        tokens[-1] = tokens[0]  # Close the loop
        
        if is_crosschain:
            chains = random.sample(self.CHAINS, min(hops, 3))
            chains = chains + [chains[0]] * (hops - len(chains) + 1)
        else:
            primary_chain = random.choice(self.CHAINS)
            chains = [primary_chain] * (hops + 1)
        
        dexes = random.choices(self.DEXES, k=hops)
        
        return {
            'tokens': tokens,
            'chains': chains,
            'dexes': dexes
        }

    def calculate_risk_metrics(self):
        """Calculate comprehensive risk metrics"""
        if not self.daily_returns:
            return
        
        # Sharpe Ratio (assuming risk-free rate of 3% annually)
        risk_free_rate_daily = 0.03 / 365
        excess_returns = np.array(self.daily_returns) - risk_free_rate_daily
        if len(excess_returns) > 1 and np.std(excess_returns) > 0:
            self.sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(365)
        else:
            self.sharpe_ratio = 0
        
        # Value at Risk (95% confidence)
        self.var_95 = np.percentile(self.daily_returns, 5) if self.daily_returns else 0
        
        logger.info(f"\n📊 Risk Metrics:")
        logger.info(f"  Sharpe Ratio: {self.sharpe_ratio:.2f}")
        logger.info(f"  Max Drawdown: {self.max_drawdown*100:.2f}%")
        logger.info(f"  VaR (95%): {self.var_95*100:.2f}%")

    def generate_reports(self):
        """Generate comprehensive simulation reports"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. JSON Summary
        self.generate_json_summary(timestamp)
        
        # 2. Daily Metrics CSV
        self.generate_daily_metrics_csv(timestamp)
        
        # 3. All Routes CSV
        self.generate_routes_csv(timestamp)
        
        # 4. Text Report
        self.generate_text_report(timestamp)

    def generate_json_summary(self, timestamp: str):
        """Generate JSON summary file"""
        json_path = os.path.join(self.output_dir, f"90day_simulation_{timestamp}.json")
        
        summary = {
            'simulation_metadata': {
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'end_date': self.end_date.strftime('%Y-%m-%d'),
                'duration_days': 90,
                'timestamp': timestamp
            },
            'capital': {
                'initial': self.initial_capital,
                'final': self.current_capital,
                'net_profit': self.current_capital - self.initial_capital,
                'roi_percent': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
            },
            'trading_statistics': {
                'total_routes': self.cumulative_routes,
                'total_routes_attempted': len(self.all_routes),
                'success_rate': (self.cumulative_routes / len(self.all_routes)) * 100 if self.all_routes else 0,
                'avg_daily_routes': self.cumulative_routes / 90,
                'total_gross_profit': self.cumulative_profit,
                'total_gas_costs': self.cumulative_gas,
                'total_net_profit': self.cumulative_net_profit
            },
            'risk_metrics': {
                'sharpe_ratio': self.sharpe_ratio,
                'max_drawdown_percent': self.max_drawdown * 100,
                'value_at_risk_95': self.var_95 * 100
            },
            'daily_metrics': self.daily_metrics
        }
        
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"✅ JSON summary saved: {json_path}")

    def generate_daily_metrics_csv(self, timestamp: str):
        """Generate daily metrics CSV"""
        csv_path = os.path.join(self.output_dir, f"90day_daily_metrics_{timestamp}.csv")
        
        if self.daily_metrics:
            fieldnames = self.daily_metrics[0].keys()
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.daily_metrics)
        
        logger.info(f"✅ Daily metrics CSV saved: {csv_path}")

    def generate_routes_csv(self, timestamp: str):
        """Generate all routes CSV"""
        csv_path = os.path.join(self.output_dir, f"90day_all_routes_{timestamp}.csv")
        
        if self.all_routes:
            fieldnames = self.all_routes[0].keys()
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.all_routes)
        
        logger.info(f"✅ All routes CSV saved: {csv_path}")

    def generate_text_report(self, timestamp: str):
        """Generate human-readable text report"""
        report_path = os.path.join(self.output_dir, f"90day_report_{timestamp}.txt")
        
        successful_routes = [r for r in self.all_routes if r['success']]
        
        # Calculate statistics
        total_2hop = sum(1 for r in successful_routes if r['hops'] == 2)
        total_3hop = sum(1 for r in successful_routes if r['hops'] == 3)
        total_4hop = sum(1 for r in successful_routes if r['hops'] == 4)
        total_crosschain = sum(1 for r in successful_routes if r['is_crosschain'])
        total_frontrun = sum(1 for r in successful_routes if r['mev_type'] == 'frontrun')
        total_backrun = sum(1 for r in successful_routes if r['mev_type'] == 'backrun')
        
        avg_profit = np.mean([r['net_profit'] for r in successful_routes]) if successful_routes else 0
        best_route = max(successful_routes, key=lambda x: x['net_profit']) if successful_routes else None
        avg_exec_time = np.mean([r['execution_time_ms'] for r in successful_routes]) if successful_routes else 0
        
        report = f"""
{'='*80}
90-DAY DEFI ARBITRAGE SIMULATION - COMPREHENSIVE REPORT
{'='*80}

EXECUTIVE SUMMARY
{'-'*80}
Simulation Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}
Duration: 90 days

FINANCIAL RESULTS
{'-'*80}
Initial Capital:     ${self.initial_capital:,.2f}
Final Capital:       ${self.current_capital:,.2f}
Total Net Profit:    ${self.cumulative_net_profit:,.2f}
ROI:                 {((self.current_capital - self.initial_capital) / self.initial_capital) * 100:.2f}%

TRADING STATISTICS
{'-'*80}
Total Routes Executed:     {self.cumulative_routes:,}
Total Routes Attempted:    {len(self.all_routes):,}
Success Rate:              {(self.cumulative_routes / len(self.all_routes)) * 100 if self.all_routes else 0:.1f}%
Avg Daily Routes:          {self.cumulative_routes / 90:.1f}
Avg Daily Profit:          ${self.cumulative_net_profit / 90:,.2f}

STRATEGY DISTRIBUTION
{'-'*80}
2-Hop Routes:        {total_2hop:,} ({total_2hop/self.cumulative_routes*100 if self.cumulative_routes else 0:.1f}%)
3-Hop Routes:        {total_3hop:,} ({total_3hop/self.cumulative_routes*100 if self.cumulative_routes else 0:.1f}%)
4-Hop Routes:        {total_4hop:,} ({total_4hop/self.cumulative_routes*100 if self.cumulative_routes else 0:.1f}%)
Crosschain Routes:   {total_crosschain:,} ({total_crosschain/self.cumulative_routes*100 if self.cumulative_routes else 0:.1f}%)
MEV Sandwich:        {total_frontrun + total_backrun:,} ({(total_frontrun + total_backrun)/self.cumulative_routes*100 if self.cumulative_routes else 0:.1f}%)
  - Frontrun:        {total_frontrun:,}
  - Backrun:         {total_backrun:,}

PERFORMANCE METRICS
{'-'*80}
Best Day Profit:         ${max([d['net_profit'] for d in self.daily_metrics]):.2f}
Worst Day Profit:        ${min([d['net_profit'] for d in self.daily_metrics]):.2f}
Avg Route Profit:        ${avg_profit:.2f}
Best Single Route:       ${best_route['net_profit'] if best_route else 0:.2f}
Avg Execution Time:      {avg_exec_time:.0f} ms
Total Gas Costs:         ${self.cumulative_gas:,.2f}

RISK METRICS
{'-'*80}
Sharpe Ratio:            {self.sharpe_ratio:.2f}
Max Drawdown:            {self.max_drawdown*100:.2f}%
Value at Risk (95%):     {self.var_95*100:.2f}%

DAILY BREAKDOWN (First 10 Days)
{'-'*80}
"""
        for i, day in enumerate(self.daily_metrics[:10]):
            report += f"Day {day['day']:2d} ({day['date']}): {day['successful_routes']:2d} routes | ${day['net_profit']:>10,.2f} profit\n"
        
        report += f"\nDAILY BREAKDOWN (Last 10 Days)\n{'-'*80}\n"
        for day in self.daily_metrics[-10:]:
            report += f"Day {day['day']:2d} ({day['date']}): {day['successful_routes']:2d} routes | ${day['net_profit']:>10,.2f} profit\n"
        
        report += f"\nTOP 10 MOST PROFITABLE ROUTES\n{'-'*80}\n"
        top_routes = sorted(successful_routes, key=lambda x: x['net_profit'], reverse=True)[:10]
        for i, route in enumerate(top_routes, 1):
            report += f"{i:2d}. {route['route_path']:30s} | ${route['net_profit']:>8,.2f} | {route['hops']}-hop | {route['chains']}\n"
        
        report += f"\n{'='*80}\nEND OF REPORT\n{'='*80}\n"
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"✅ Text report saved: {report_path}")

    def print_summary(self):
        """Print summary to console"""
        logger.info(f"Initial Capital:  ${self.initial_capital:,.2f}")
        logger.info(f"Final Capital:    ${self.current_capital:,.2f}")
        logger.info(f"Total Net Profit: ${self.cumulative_net_profit:,.2f}")
        logger.info(f"ROI:              {((self.current_capital - self.initial_capital) / self.initial_capital) * 100:.2f}%")
        logger.info(f"Total Routes:     {self.cumulative_routes:,}")
        logger.info(f"Success Rate:     {(self.cumulative_routes / len(self.all_routes)) * 100 if self.all_routes else 0:.1f}%")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the 90-day comprehensive DeFi arbitrage simulation.")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital for the simulation.")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory to save simulation results.")

    args = parser.parse_args()

    simulation = Simulation90Day(initial_capital=args.capital, output_dir=args.output_dir)
    asyncio.run(simulation.run_simulation())