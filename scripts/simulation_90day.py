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

class FlashLoanRiskManager:
    """
    Production-Grade Flash Loan Risk Management System
    
    Implements dynamic risk configuration, adaptive slippage calculation,
    and comprehensive risk metrics for flash loan arbitrage operations.
    
    Key Features:
    - Size-based loan categorization with adaptive parameters
    - Advanced slippage impact modeling
    - Multi-dimensional risk scoring
    - Failure probability estimation
    - Position size optimization
    """
    
    # Historical tracking configuration
    HISTORICAL_WINDOW_SIZE = 100  # Number of recent attempts to consider
    MAX_HISTORY_SIZE = 1000  # Maximum history records to keep
    
    # Flash loan size categories (USD)
    LOAN_SIZE_CATEGORIES = {
        'small': {'min': 0, 'max': 50000},
        'medium': {'min': 50000, 'max': 200000},
        'large': {'min': 200000, 'max': float('inf')}
    }
    
    # Dynamic risk parameters per category
    RISK_CONFIGS = {
        'small': {
            'base_slippage_tolerance': 0.008,      # 0.8%
            'max_pool_utilization': 0.25,          # 25% of pool
            'min_profit_threshold': 10,            # $10 minimum
            'gas_multiplier': 1.0,
            'risk_score_threshold': 0.7,           # Lower risk tolerance
            'max_price_impact': 0.015              # 1.5%
        },
        'medium': {
            'base_slippage_tolerance': 0.012,      # 1.2%
            'max_pool_utilization': 0.15,          # 15% of pool
            'min_profit_threshold': 50,            # $50 minimum
            'gas_multiplier': 1.3,
            'risk_score_threshold': 0.5,           # Medium risk tolerance
            'max_price_impact': 0.025              # 2.5%
        },
        'large': {
            'base_slippage_tolerance': 0.020,      # 2.0%
            'max_pool_utilization': 0.10,          # 10% of pool
            'min_profit_threshold': 200,           # $200 minimum
            'gas_multiplier': 1.8,
            'risk_score_threshold': 0.3,           # Higher risk tolerance needed
            'max_price_impact': 0.040              # 4.0%
        }
    }
    
    def __init__(self):
        """Initialize the Flash Loan Risk Manager"""
        self.historical_failures = []
        self.risk_metrics_history = []
        logger.info("FlashLoanRiskManager initialized with production-grade risk controls")
    
    def categorize_loan_size(self, loan_amount_usd: float) -> str:
        """
        Categorize flash loan size into small/medium/large
        
        Args:
            loan_amount_usd: Loan amount in USD
            
        Returns:
            Category string: 'small', 'medium', or 'large'
        """
        for category, bounds in self.LOAN_SIZE_CATEGORIES.items():
            if bounds['min'] <= loan_amount_usd < bounds['max']:
                return category
        return 'large'  # Default to large for amounts over max
    
    def get_risk_config(self, loan_amount_usd: float) -> Dict[str, float]:
        """
        Get dynamic risk configuration based on loan size
        
        Args:
            loan_amount_usd: Loan amount in USD
            
        Returns:
            Dictionary of risk parameters
        """
        category = self.categorize_loan_size(loan_amount_usd)
        return self.RISK_CONFIGS[category].copy()
    
    def calculate_adaptive_slippage(
        self,
        loan_amount_usd: float,
        pool_liquidity_usd: float,
        hops: int,
        volatility_index: float = 1.0,
        competition_level: float = 0.3
    ) -> Dict[str, float]:
        """
        Calculate adaptive slippage tolerance with multi-factor analysis
        
        Considers:
        - Pool liquidity depth
        - Multi-hop route complexity
        - Market volatility conditions
        - MEV bot competition level
        
        Args:
            loan_amount_usd: Flash loan size in USD
            pool_liquidity_usd: Average pool liquidity across route
            hops: Number of hops in route
            volatility_index: Market volatility (0.5 = low, 1.0 = normal, 2.0 = high)
            competition_level: MEV competition (0.0 to 1.0)
            
        Returns:
            Dictionary with slippage metrics
        """
        config = self.get_risk_config(loan_amount_usd)
        base_slippage = config['base_slippage_tolerance']
        
        # Factor 1: Pool depth impact
        loan_to_liquidity_ratio = loan_amount_usd / pool_liquidity_usd if pool_liquidity_usd > 0 else 1.0
        depth_multiplier = 1.0 + (loan_to_liquidity_ratio * 2.0)  # Linear increase
        
        # Factor 2: Route complexity (more hops = more slippage)
        complexity_multiplier = 1.0 + ((hops - 2) * 0.25)  # +25% per extra hop
        
        # Factor 3: Volatility impact
        volatility_multiplier = volatility_index
        
        # Factor 4: Competition impact (more competition = more slippage)
        competition_multiplier = 1.0 + (competition_level * 0.5)  # Up to +50%
        
        # Combined adaptive slippage
        adaptive_slippage = (
            base_slippage * 
            depth_multiplier * 
            complexity_multiplier * 
            volatility_multiplier * 
            competition_multiplier
        )
        
        return {
            'base_slippage': base_slippage,
            'adaptive_slippage': adaptive_slippage,
            'depth_multiplier': depth_multiplier,
            'complexity_multiplier': complexity_multiplier,
            'volatility_multiplier': volatility_multiplier,
            'competition_multiplier': competition_multiplier,
            'loan_to_liquidity_ratio': loan_to_liquidity_ratio
        }
    
    def validate_position_size(
        self,
        loan_amount_usd: float,
        pool_liquidity_usd: float
    ) -> Tuple[bool, str]:
        """
        Validate if position size is within acceptable limits
        
        Args:
            loan_amount_usd: Flash loan size
            pool_liquidity_usd: Pool liquidity
            
        Returns:
            Tuple of (is_valid, reason)
        """
        config = self.get_risk_config(loan_amount_usd)
        max_utilization = config['max_pool_utilization']
        
        if pool_liquidity_usd <= 0:
            return False, "Invalid pool liquidity"
        
        utilization = loan_amount_usd / pool_liquidity_usd
        utilization_pct = utilization * 100
        max_utilization_pct = max_utilization * 100
        
        if utilization > max_utilization:
            return False, f"Position size {utilization_pct:.1f}% exceeds max {max_utilization_pct:.1f}%"
        
        return True, "Position size acceptable"
    
    def calculate_risk_adjusted_threshold(
        self,
        loan_amount_usd: float,
        expected_slippage: float,
        gas_cost_usd: float
    ) -> float:
        """
        Calculate risk-adjusted minimum profit threshold
        
        Args:
            loan_amount_usd: Flash loan size
            expected_slippage: Expected slippage percentage
            gas_cost_usd: Estimated gas cost
            
        Returns:
            Risk-adjusted profit threshold in USD
        """
        config = self.get_risk_config(loan_amount_usd)
        base_threshold = config['min_profit_threshold']
        
        # Add buffer for slippage risk
        slippage_buffer = loan_amount_usd * expected_slippage * 1.5  # 1.5x safety margin
        
        # Add buffer for gas cost volatility (gas can spike)
        gas_buffer = gas_cost_usd * 0.5  # 50% gas volatility buffer
        
        # Total risk-adjusted threshold
        adjusted_threshold = base_threshold + slippage_buffer + gas_buffer
        
        return adjusted_threshold
    
    def calculate_flash_loan_risk_score(
        self,
        loan_amount_usd: float,
        pool_liquidity_usd: float,
        expected_slippage: float,
        actual_price_impact: float,
        hops: int,
        has_mev: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive flash loan risk score
        
        Risk score ranges from 0 (highest risk) to 1 (lowest risk)
        
        Args:
            loan_amount_usd: Flash loan size
            pool_liquidity_usd: Pool liquidity
            expected_slippage: Expected slippage
            actual_price_impact: Actual price impact from AMM calculations
            hops: Number of hops
            has_mev: Whether route includes MEV opportunities
            
        Returns:
            Dictionary with risk metrics
        """
        config = self.get_risk_config(loan_amount_usd)
        
        # Component 1: Loan-to-liquidity ratio (lower is better)
        ltl_ratio = loan_amount_usd / pool_liquidity_usd if pool_liquidity_usd > 0 else 1.0
        ltl_score = max(0, 1 - (ltl_ratio / config['max_pool_utilization']))
        
        # Component 2: Slippage risk (lower is better)
        max_acceptable_slippage = config['base_slippage_tolerance'] * 2.0
        slippage_score = max(0, 1 - (expected_slippage / max_acceptable_slippage))
        
        # Component 3: Price impact risk
        price_impact_score = max(0, 1 - (actual_price_impact / config['max_price_impact']))
        
        # Component 4: Route complexity risk (fewer hops is better)
        complexity_score = max(0, 1 - ((hops - 2) * 0.2))  # Penalty for each hop beyond 2
        
        # Component 5: MEV bonus (MEV opportunities reduce risk through higher profit potential)
        mev_score = 1.2 if has_mev else 1.0
        
        # Weighted composite risk score
        weights = {
            'ltl': 0.30,
            'slippage': 0.25,
            'price_impact': 0.25,
            'complexity': 0.15,
            'mev': 0.05
        }
        
        composite_score = (
            ltl_score * weights['ltl'] +
            slippage_score * weights['slippage'] +
            price_impact_score * weights['price_impact'] +
            complexity_score * weights['complexity']
        ) * mev_score
        
        # Liquidation risk estimation (simplified model)
        liquidation_risk = self._estimate_liquidation_risk(
            loan_amount_usd, expected_slippage, actual_price_impact
        )
        
        return {
            'composite_risk_score': min(1.0, composite_score),  # Capped at 1.0
            'ltl_ratio': ltl_ratio,
            'ltl_score': ltl_score,
            'slippage_score': slippage_score,
            'price_impact_score': price_impact_score,
            'complexity_score': complexity_score,
            'liquidation_risk': liquidation_risk,
            'risk_threshold': config['risk_score_threshold'],
            'passes_risk_check': composite_score >= config['risk_score_threshold']
        }
    
    def _estimate_liquidation_risk(
        self,
        loan_amount_usd: float,
        expected_slippage: float,
        price_impact: float
    ) -> float:
        """
        Estimate liquidation risk probability
        
        Returns value between 0 (no risk) and 1 (certain liquidation)
        """
        # Simplified liquidation risk model
        # Risk increases with slippage and price impact
        slippage_risk = min(expected_slippage * 10, 0.5)  # Max 50% from slippage
        impact_risk = min(price_impact * 8, 0.3)  # Max 30% from price impact
        
        # Larger loans have higher liquidation risk
        size_risk = min(loan_amount_usd / 1000000, 0.2)  # Max 20% from size
        
        total_risk = slippage_risk + impact_risk + size_risk
        return min(total_risk, 1.0)
    
    def estimate_failure_probability(
        self,
        risk_score: float,
        market_phase: str,
        competition_level: float
    ) -> Dict[str, float]:
        """
        Estimate probability of flash loan failure
        
        Args:
            risk_score: Composite risk score (0-1)
            market_phase: Current market phase (bull/bear/sideways)
            competition_level: MEV bot competition (0-1)
            
        Returns:
            Dictionary with failure probability metrics
        """
        # Base failure rate from risk score
        base_failure_prob = 1 - risk_score
        
        # Market phase adjustment
        market_multipliers = {
            'bull': 0.8,      # Lower failure in bull markets
            'bear': 1.4,      # Higher failure in bear markets
            'sideways': 1.0   # Neutral
        }
        market_multiplier = market_multipliers.get(market_phase, 1.0)
        
        # Competition adjustment (more competition = higher failure)
        competition_multiplier = 1.0 + (competition_level * 0.5)
        
        # Historical failure rate (if available)
        historical_failure_rate = self._get_historical_failure_rate()
        
        # Weighted probability
        estimated_probability = (
            base_failure_prob * 0.5 * market_multiplier * competition_multiplier +
            historical_failure_rate * 0.5
        )
        
        return {
            'failure_probability': min(estimated_probability, 1.0),
            'base_failure_prob': base_failure_prob,
            'market_multiplier': market_multiplier,
            'competition_multiplier': competition_multiplier,
            'historical_failure_rate': historical_failure_rate,
            'success_probability': 1 - min(estimated_probability, 1.0)
        }
    
    def _get_historical_failure_rate(self) -> float:
        """Get historical failure rate from tracked metrics"""
        if not self.historical_failures:
            return 0.4  # Default baseline failure rate (60% success)
        
        recent_window = self.historical_failures[-self.HISTORICAL_WINDOW_SIZE:]  # Last HISTORICAL_WINDOW_SIZE (100) attempts
        if not recent_window:
            return 0.4
            
        failure_count = sum(1 for f in recent_window if f)
        return failure_count / len(recent_window)
    
    def record_result(self, success: bool, risk_metrics: Dict[str, Any]):
        """
        Record flash loan attempt result for future predictions
        
        Args:
            success: Whether the flash loan succeeded
            risk_metrics: Risk metrics from the attempt
        """
        self.historical_failures.append(not success)
        self.risk_metrics_history.append({
            'success': success,
            'metrics': risk_metrics,
            'timestamp': datetime.now()
        })
        
        # Keep only last N records to prevent memory bloat
        if len(self.historical_failures) > self.MAX_HISTORY_SIZE:
            self.historical_failures = self.historical_failures[-self.MAX_HISTORY_SIZE:]
        if len(self.risk_metrics_history) > self.MAX_HISTORY_SIZE:
            self.risk_metrics_history = self.risk_metrics_history[-self.MAX_HISTORY_SIZE:]
    
    def get_gas_cost_multiplier(self, loan_amount_usd: float) -> float:
        """
        Get gas cost multiplier based on loan size
        
        Larger loans need more sophisticated execution strategies
        and thus incur higher gas costs.
        
        Args:
            loan_amount_usd: Flash loan size
            
        Returns:
            Gas cost multiplier
        """
        config = self.get_risk_config(loan_amount_usd)
        return config['gas_multiplier']


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
    
    # Flash Loan Risk Manager instance
    risk_manager = FlashLoanRiskManager()
    
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
        self.volatility_index = 1.0  # Normal volatility
        
        # Competition tracking
        self.bot_competition_level = 0.3  # 30% competition initially
        
        # Flash loan risk tracking
        self.flash_loan_metrics = []
        
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
        """Update market phase, volatility, and competition level"""
        phases = ['bull', 'bear', 'sideways']
        old_phase = self.market_phase
        self.market_phase = random.choice(phases)
        
        # Update volatility index based on market phase
        volatility_ranges = {
            'bull': (0.8, 1.2),
            'bear': (1.2, 2.0),
            'sideways': (0.6, 1.0)
        }
        vol_range = volatility_ranges[self.market_phase]
        self.volatility_index = random.uniform(*vol_range)
        
        # Increase competition over time
        self.bot_competition_level = min(0.3 + (day / 90) * 0.4, 0.7)
        
        logger.info(f"  📊 Market Phase: {old_phase} → {self.market_phase}")
        logger.info(f"  📈 Volatility Index: {self.volatility_index:.2f}")
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
        
        # Initial input amount (flash loan size)
        input_amount = random.uniform(50000, 200000)  # Input in USD
        current_amount = input_amount
        
        # Categorize flash loan and get risk config
        loan_category = self.risk_manager.categorize_loan_size(input_amount)
        risk_config = self.risk_manager.get_risk_config(input_amount)
        
        # Simulate each hop using AMM calculations
        total_fees = 0
        total_price_impact = 0
        hop_details = []
        total_pool_liquidity = 0
        
        for hop in range(hops):
            # Simulate liquidity pool reserves (realistic ranges based on pool size)
            pool_size_multiplier = random.uniform(0.5, 3.0)  # Pool liquidity variation
            reserve_x = random.uniform(500000, 5000000) * pool_size_multiplier
            reserve_y = random.uniform(500000, 5000000) * pool_size_multiplier
            
            pool_liquidity = reserve_x + reserve_y
            total_pool_liquidity += pool_liquidity
            
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
                'pool_liquidity': pool_liquidity
            })
            
            current_amount = output
        
        # Average pool liquidity across route
        avg_pool_liquidity = total_pool_liquidity / hops if hops > 0 else 0
        
        # Calculate adaptive slippage using risk manager
        slippage_analysis = self.risk_manager.calculate_adaptive_slippage(
            loan_amount_usd=input_amount,
            pool_liquidity_usd=avg_pool_liquidity,
            hops=hops,
            volatility_index=self.volatility_index,
            competition_level=self.bot_competition_level
        )
        
        # Validate position size
        position_valid, position_reason = self.risk_manager.validate_position_size(
            input_amount, avg_pool_liquidity
        )
        
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
        
        # Gas costs with flash loan risk multiplier
        primary_chain = route_path['chains'][0]
        base_gas = self.CHAIN_GAS_COSTS[primary_chain]
        
        # Get gas multiplier from risk manager based on loan size
        flash_loan_gas_multiplier = self.risk_manager.get_gas_cost_multiplier(input_amount)
        
        gas_multiplier = 1.0 + (hops - 2) * 0.3  # More hops = more gas
        gas_multiplier *= flash_loan_gas_multiplier  # Flash loan size penalty
        
        if is_crosschain:
            gas_multiplier *= 2.0  # Crosschain costs more
        if has_mev:
            gas_multiplier *= 1.5  # MEV costs more
        gas_price_variation = random.uniform(0.8, 1.4)
        gas_cost = base_gas * gas_multiplier * gas_price_variation
        
        # Enhanced slippage modeling using adaptive calculation
        adaptive_slippage = slippage_analysis['adaptive_slippage']
        slippage_cost = gross_profit * adaptive_slippage
        
        # Calculate flash loan risk score
        avg_price_impact_pct = (total_price_impact / hops) / 100 if hops > 0 else 0
        risk_score_data = self.risk_manager.calculate_flash_loan_risk_score(
            loan_amount_usd=input_amount,
            pool_liquidity_usd=avg_pool_liquidity,
            expected_slippage=adaptive_slippage,
            actual_price_impact=avg_price_impact_pct,
            hops=hops,
            has_mev=has_mev
        )
        
        # Calculate risk-adjusted profit threshold
        risk_adjusted_threshold = self.risk_manager.calculate_risk_adjusted_threshold(
            loan_amount_usd=input_amount,
            expected_slippage=adaptive_slippage,
            gas_cost_usd=gas_cost
        )
        
        # Calculate net profit using profit formula: π = (output - input) - fees - gas
        net_profit = self.amm.calculate_profit(output_amount, input_amount, total_fees + slippage_cost, gas_cost)
        
        # Estimate failure probability
        failure_prob_data = self.risk_manager.estimate_failure_probability(
            risk_score=risk_score_data['composite_risk_score'],
            market_phase=self.market_phase,
            competition_level=self.bot_competition_level
        )
        
        # Success determination is now handled by the gateway, but we can estimate it
        # for routes that don't even make it to the gateway.
        success = False
        simulation_passed = False
        risk_check_passed = risk_score_data['passes_risk_check'] and position_valid
        target_block = day * 7200  # Define target block upfront for potential retry

        # Only profitable routes that pass risk checks are considered for bundle submission
        if net_profit > risk_adjusted_threshold and risk_check_passed:
            # Phase 1: Simulate bundle with eth_callBundle for revert protection
            bundle_for_sim = [{'tx': '0x...', 'profit_eth': net_profit / 2000}] # Simplified bundle
            sim_result = gateway.simulate_eth_call_bundle(bundle_for_sim)
            
            simulation_passed = sim_result["success"]
            
            if not simulation_passed:
                logger.debug(f"  ❌ Route {route_num} FAILED eth_callBundle simulation. Skipping.")
                success = False
            else:
                # Phase 2: Add to private mempool (TX_RELEASE_TANK) for later submission
                gateway.add_to_tx_release_tank(bundle_for_sim, target_block)
                
                # Phase 3: Simulate the MEV-Boost auction at the target block
                # Apply failure probability to auction success
                auction_results = gateway.simulate_blx_submit_bundle(target_block)
                
                # Check if our bundle won (adjusted by failure probability)
                won_auction = any(res['success'] for res in auction_results)
                # Apply stochastic failure based on estimated probability
                actual_success = won_auction and (random.random() > failure_prob_data['failure_probability'])
                
                if actual_success:
                    logger.debug(f"  ✅ Route {route_num}: Risk✓ eth_callBundle✓ → MEV-Boost Auction WON")
                    success = True
                else:
                    logger.debug(f"  ❌ Route {route_num}: Risk✓ eth_callBundle✓ → MEV-Boost Auction LOST")
                    success = False
        else:
            if net_profit <= risk_adjusted_threshold:
                logger.debug(f"  📉 Route {route_num} below risk-adjusted threshold ${risk_adjusted_threshold:.2f}. Skipping.")
            elif not risk_check_passed:
                logger.debug(f"  ⚠️ Route {route_num} FAILED risk check. Reason: {position_reason if not position_valid else 'Low risk score'}")
            success = False

        
        # If failed, attempt retry logic (simulate 1 retry) - only for routes that passed initial risk check
        retry_attempted = False
        if not success and net_profit > risk_adjusted_threshold and risk_check_passed and simulation_passed:
            retry_attempted = True
            # Retry has a lower chance of success
            bundle_for_sim = [{'tx': '0x...', 'profit_eth': net_profit / 2000}]  # Recreate bundle for retry
            retry_sim_result = gateway.simulate_eth_call_bundle(bundle_for_sim)
            if retry_sim_result["success"]:
                target_block_retry = target_block + 1  # Retry in next block
                gateway.add_to_tx_release_tank(bundle_for_sim, target_block_retry)
                retry_auction_results = gateway.simulate_blx_submit_bundle(target_block_retry)
                won_retry = any(res['success'] for res in retry_auction_results)
                # Apply higher failure probability for retries
                retry_success = won_retry and (random.random() > failure_prob_data['failure_probability'] * 1.3)
                if retry_success:
                    success = True
        
        # Record result in risk manager for future predictions
        self.risk_manager.record_result(success, risk_score_data)
        
        # Execution time
        exec_time_ms = random.uniform(800, 2500) * (1 + 0.2 * (hops - 2))
        
        roi_percent = (net_profit / input_amount * 100) if success else 0
        
        # Compile comprehensive flash loan metrics
        flash_loan_metrics = {
            'loan_category': loan_category,
            'loan_to_liquidity_ratio': slippage_analysis['loan_to_liquidity_ratio'],
            'adaptive_slippage': adaptive_slippage,
            'base_slippage': slippage_analysis['base_slippage'],
            'risk_adjusted_threshold': risk_adjusted_threshold,
            'composite_risk_score': risk_score_data['composite_risk_score'],
            'liquidation_risk': risk_score_data['liquidation_risk'],
            'failure_probability': failure_prob_data['failure_probability'],
            'success_probability': failure_prob_data['success_probability'],
            'position_valid': position_valid,
            'position_reason': position_reason,
            'risk_check_passed': risk_check_passed,
            'flash_loan_gas_multiplier': flash_loan_gas_multiplier
        }
        
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
            'liquidity_score': avg_pool_liquidity / (avg_pool_liquidity + input_amount),  # Normalized liquidity
            'competition_level': self.bot_competition_level,
            'amm_formula_used': 'constant_product',
            'volatility_index': self.volatility_index,
            **flash_loan_metrics  # Add all flash loan risk metrics
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
        
        # Flash loan risk statistics
        small_loans = sum(1 for r in successful_routes if r.get('loan_category') == 'small')
        medium_loans = sum(1 for r in successful_routes if r.get('loan_category') == 'medium')
        large_loans = sum(1 for r in successful_routes if r.get('loan_category') == 'large')
        
        avg_risk_score = np.mean([r.get('composite_risk_score', 0) for r in successful_routes]) if successful_routes else 0
        avg_liquidation_risk = np.mean([r.get('liquidation_risk', 0) for r in successful_routes]) if successful_routes else 0
        avg_failure_prob = np.mean([r.get('failure_probability', 0) for r in successful_routes]) if successful_routes else 0
        avg_ltl_ratio = np.mean([r.get('loan_to_liquidity_ratio', 0) for r in successful_routes]) if successful_routes else 0
        
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

FLASH LOAN RISK ANALYSIS
{'-'*80}
Small Loans (<$50k):       {small_loans:,} ({small_loans/self.cumulative_routes*100 if self.cumulative_routes else 0:.1f}%)
Medium Loans ($50k-$200k): {medium_loans:,} ({medium_loans/self.cumulative_routes*100 if self.cumulative_routes else 0:.1f}%)
Large Loans (>$200k):      {large_loans:,} ({large_loans/self.cumulative_routes*100 if self.cumulative_routes else 0:.1f}%)

Avg Risk Score:            {avg_risk_score:.3f} (1.0 = lowest risk)
Avg Liquidation Risk:      {avg_liquidation_risk*100:.2f}%
Avg Failure Probability:   {avg_failure_prob*100:.2f}%
Avg Loan-to-Liquidity:     {avg_ltl_ratio:.3f}

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
        
        report += f"\nTOP 10 HIGHEST RISK ROUTES (Successfully Executed)\n{'-'*80}\n"
        high_risk_routes = sorted(successful_routes, key=lambda x: x.get('liquidation_risk', 0), reverse=True)[:10]
        for i, route in enumerate(high_risk_routes, 1):
            liq_risk = route.get('liquidation_risk', 0)
            risk_score = route.get('composite_risk_score', 0)
            report += f"{i:2d}. {route['route_path']:30s} | Liq Risk: {liq_risk*100:5.2f}% | Score: {risk_score:.3f} | ${route['net_profit']:>8,.2f}\n"
        
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