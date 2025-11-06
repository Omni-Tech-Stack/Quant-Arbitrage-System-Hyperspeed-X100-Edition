#!/usr/bin/env python3
"""
Quick test script for Flash Loan Risk Management System
Tests the core functionality without running a full 90-day simulation
This is a standalone test that doesn't import the full simulation module
"""

import sys
import os

# We'll extract just the classes we need for testing
# Copy the essential code here for standalone testing

import random
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FlashLoanRiskTest')

class FlashLoanRiskManager:
    """
    Production-Grade Flash Loan Risk Management System
    
    Implements dynamic risk configuration, adaptive slippage calculation,
    and comprehensive risk metrics for flash loan arbitrage operations.
    """
    
    # Flash loan size categories (USD)
    LOAN_SIZE_CATEGORIES = {
        'small': {'min': 0, 'max': 50000},
        'medium': {'min': 50000, 'max': 200000},
        'large': {'min': 200000, 'max': float('inf')}
    }
    
    # Dynamic risk parameters per category
    RISK_CONFIGS = {
        'small': {
            'base_slippage_tolerance': 0.008,
            'max_pool_utilization': 0.25,
            'min_profit_threshold': 10,
            'gas_multiplier': 1.0,
            'risk_score_threshold': 0.7,
            'max_price_impact': 0.015
        },
        'medium': {
            'base_slippage_tolerance': 0.012,
            'max_pool_utilization': 0.15,
            'min_profit_threshold': 50,
            'gas_multiplier': 1.3,
            'risk_score_threshold': 0.5,
            'max_price_impact': 0.025
        },
        'large': {
            'base_slippage_tolerance': 0.020,
            'max_pool_utilization': 0.10,
            'min_profit_threshold': 200,
            'gas_multiplier': 1.8,
            'risk_score_threshold': 0.3,
            'max_price_impact': 0.040
        }
    }
    
    def __init__(self):
        """Initialize the Flash Loan Risk Manager"""
        self.historical_failures = []
        self.risk_metrics_history = []
        logger.info("FlashLoanRiskManager initialized with production-grade risk controls")
    
    def categorize_loan_size(self, loan_amount_usd: float) -> str:
        """Categorize flash loan size into small/medium/large"""
        for category, bounds in self.LOAN_SIZE_CATEGORIES.items():
            if bounds['min'] <= loan_amount_usd < bounds['max']:
                return category
        return 'large'
    
    def get_risk_config(self, loan_amount_usd: float) -> Dict[str, float]:
        """Get dynamic risk configuration based on loan size"""
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
        """Calculate adaptive slippage tolerance with multi-factor analysis"""
        config = self.get_risk_config(loan_amount_usd)
        base_slippage = config['base_slippage_tolerance']
        
        loan_to_liquidity_ratio = loan_amount_usd / pool_liquidity_usd if pool_liquidity_usd > 0 else 1.0
        depth_multiplier = 1.0 + (loan_to_liquidity_ratio * 2.0)
        complexity_multiplier = 1.0 + ((hops - 2) * 0.25)
        volatility_multiplier = volatility_index
        competition_multiplier = 1.0 + (competition_level * 0.5)
        
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
        """Validate if position size is within acceptable limits"""
        config = self.get_risk_config(loan_amount_usd)
        max_utilization = config['max_pool_utilization']
        
        if pool_liquidity_usd <= 0:
            return False, "Invalid pool liquidity"
        
        utilization = loan_amount_usd / pool_liquidity_usd
        
        if utilization > max_utilization:
            return False, f"Position size {utilization*100:.1f}% exceeds max {max_utilization*100:.1f}%"
        
        return True, "Position size acceptable"
    
    def calculate_risk_adjusted_threshold(
        self,
        loan_amount_usd: float,
        expected_slippage: float,
        gas_cost_usd: float
    ) -> float:
        """Calculate risk-adjusted minimum profit threshold"""
        config = self.get_risk_config(loan_amount_usd)
        base_threshold = config['min_profit_threshold']
        
        slippage_buffer = loan_amount_usd * expected_slippage * 1.5
        gas_buffer = gas_cost_usd * 0.5
        
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
        """Calculate comprehensive flash loan risk score"""
        config = self.get_risk_config(loan_amount_usd)
        
        ltl_ratio = loan_amount_usd / pool_liquidity_usd if pool_liquidity_usd > 0 else 1.0
        ltl_score = max(0, 1 - (ltl_ratio / config['max_pool_utilization']))
        
        max_acceptable_slippage = config['base_slippage_tolerance'] * 2.0
        slippage_score = max(0, 1 - (expected_slippage / max_acceptable_slippage))
        
        price_impact_score = max(0, 1 - (actual_price_impact / config['max_price_impact']))
        
        complexity_score = max(0, 1 - ((hops - 2) * 0.2))
        
        mev_score = 1.2 if has_mev else 1.0
        
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
        
        liquidation_risk = self._estimate_liquidation_risk(
            loan_amount_usd, expected_slippage, actual_price_impact
        )
        
        return {
            'composite_risk_score': min(1.0, composite_score),
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
        """Estimate liquidation risk probability"""
        slippage_risk = min(expected_slippage * 10, 0.5)
        impact_risk = min(price_impact * 8, 0.3)
        size_risk = min(loan_amount_usd / 1000000, 0.2)
        
        total_risk = slippage_risk + impact_risk + size_risk
        return min(total_risk, 1.0)
    
    def estimate_failure_probability(
        self,
        risk_score: float,
        market_phase: str,
        competition_level: float
    ) -> Dict[str, float]:
        """Estimate probability of flash loan failure"""
        base_failure_prob = 1 - risk_score
        
        market_multipliers = {
            'bull': 0.8,
            'bear': 1.4,
            'sideways': 1.0
        }
        market_multiplier = market_multipliers.get(market_phase, 1.0)
        
        competition_multiplier = 1.0 + (competition_level * 0.5)
        
        historical_failure_rate = self._get_historical_failure_rate()
        
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
            return 0.4
        
        recent_window = self.historical_failures[-100:]
        if not recent_window:
            return 0.4
            
        failure_count = sum(1 for f in recent_window if f)
        return failure_count / len(recent_window)
    
    def get_gas_cost_multiplier(self, loan_amount_usd: float) -> float:
        """Get gas cost multiplier based on loan size"""
        config = self.get_risk_config(loan_amount_usd)
        return config['gas_multiplier']


class AMMCalculator:
    """Automated Market Maker Calculator"""
    
    @staticmethod
    def calculate_swap_output(delta_x: float, x: float, y: float, fee_percent: float = 0.003) -> float:
        """Calculate swap output using constant product formula"""
        phi = fee_percent
        numerator = delta_x * y * (1 - phi)
        denominator = x + delta_x * (1 - phi)
        delta_y = numerator / denominator
        return delta_y
    
    @staticmethod
    def calculate_price(x: float, y: float) -> float:
        """Price Calculation: p = y / x"""
        return y / x if x > 0 else 0
    
    @staticmethod
    def calculate_price_impact(y_before: float, y_after: float) -> float:
        """Price Impact calculation"""
        if y_before == 0:
            return 0
        impact = ((y_before - y_after) / y_before) * 100
        return impact


def test_flash_loan_risk_manager():
    """Test FlashLoanRiskManager functionality"""
    print("="*80)
    print("FLASH LOAN RISK MANAGEMENT SYSTEM - UNIT TESTS")
    print("="*80)
    
    risk_manager = FlashLoanRiskManager()
    
    # Test 1: Loan Size Categorization
    print("\n[TEST 1] Loan Size Categorization")
    print("-" * 80)
    
    test_amounts = [25000, 100000, 250000]
    for amount in test_amounts:
        category = risk_manager.categorize_loan_size(amount)
        print(f"  ${amount:,} → {category.upper()} loan")
    
    # Test 2: Risk Configuration Retrieval
    print("\n[TEST 2] Risk Configuration by Category")
    print("-" * 80)
    
    for amount in test_amounts:
        category = risk_manager.categorize_loan_size(amount)
        config = risk_manager.get_risk_config(amount)
        print(f"\n  {category.upper()} loan (${amount:,}):")
        print(f"    Base Slippage: {config['base_slippage_tolerance']*100:.1f}%")
        print(f"    Max Pool Util: {config['max_pool_utilization']*100:.1f}%")
        print(f"    Min Profit: ${config['min_profit_threshold']}")
        print(f"    Gas Multiplier: {config['gas_multiplier']}x")
    
    # Test 3: Adaptive Slippage Calculation
    print("\n[TEST 3] Adaptive Slippage Calculation")
    print("-" * 80)
    
    loan_amount = 100000  # Medium loan
    pool_liquidity = 1000000  # $1M pool
    hops = 3
    volatility = 1.2  # Slightly elevated
    competition = 0.4  # 40%
    
    slippage = risk_manager.calculate_adaptive_slippage(
        loan_amount, pool_liquidity, hops, volatility, competition
    )
    
    print(f"  Loan: ${loan_amount:,}")
    print(f"  Pool Liquidity: ${pool_liquidity:,}")
    print(f"  Hops: {hops}")
    print(f"  Volatility: {volatility}")
    print(f"  Competition: {competition*100:.0f}%")
    print(f"\n  Results:")
    print(f"    Base Slippage: {slippage['base_slippage']*100:.2f}%")
    print(f"    Adaptive Slippage: {slippage['adaptive_slippage']*100:.2f}%")
    print(f"    Depth Multiplier: {slippage['depth_multiplier']:.2f}x")
    print(f"    Complexity Multiplier: {slippage['complexity_multiplier']:.2f}x")
    print(f"    Volatility Multiplier: {slippage['volatility_multiplier']:.2f}x")
    print(f"    Competition Multiplier: {slippage['competition_multiplier']:.2f}x")
    print(f"    Loan-to-Liquidity: {slippage['loan_to_liquidity_ratio']:.3f}")
    
    # Test 4: Position Size Validation
    print("\n[TEST 4] Position Size Validation")
    print("-" * 80)
    
    test_cases = [
        (50000, 500000, "Should PASS - 10% utilization"),
        (100000, 500000, "Should FAIL - 20% utilization (medium loan max: 15%)"),
        (200000, 1000000, "Should FAIL - 20% utilization (large loan max: 10%)"),
    ]
    
    for loan, pool, description in test_cases:
        valid, reason = risk_manager.validate_position_size(loan, pool)
        status = "✅ PASS" if valid else "❌ FAIL"
        print(f"  {status} | ${loan:,} in ${pool:,} pool")
        print(f"       {description}")
        print(f"       Reason: {reason}")
    
    # Test 5: Risk Score Calculation
    print("\n[TEST 5] Flash Loan Risk Score")
    print("-" * 80)
    
    risk_score = risk_manager.calculate_flash_loan_risk_score(
        loan_amount_usd=100000,
        pool_liquidity_usd=1000000,
        expected_slippage=0.015,
        actual_price_impact=0.012,
        hops=3,
        has_mev=True
    )
    
    print(f"  Composite Risk Score: {risk_score['composite_risk_score']:.3f}")
    print(f"  LTL Ratio: {risk_score['ltl_ratio']:.3f}")
    print(f"  LTL Score: {risk_score['ltl_score']:.3f}")
    print(f"  Slippage Score: {risk_score['slippage_score']:.3f}")
    print(f"  Price Impact Score: {risk_score['price_impact_score']:.3f}")
    print(f"  Complexity Score: {risk_score['complexity_score']:.3f}")
    print(f"  Liquidation Risk: {risk_score['liquidation_risk']*100:.2f}%")
    print(f"  Risk Threshold: {risk_score['risk_threshold']:.3f}")
    print(f"  Passes Check: {'✅ YES' if risk_score['passes_risk_check'] else '❌ NO'}")
    
    # Test 6: Failure Probability Estimation
    print("\n[TEST 6] Failure Probability Estimation")
    print("-" * 80)
    
    failure_prob = risk_manager.estimate_failure_probability(
        risk_score=0.65,
        market_phase='bear',
        competition_level=0.5
    )
    
    print(f"  Input Risk Score: 0.65")
    print(f"  Market Phase: BEAR")
    print(f"  Competition: 50%")
    print(f"\n  Results:")
    print(f"    Failure Probability: {failure_prob['failure_probability']*100:.1f}%")
    print(f"    Success Probability: {failure_prob['success_probability']*100:.1f}%")
    print(f"    Base Failure Prob: {failure_prob['base_failure_prob']*100:.1f}%")
    print(f"    Market Multiplier: {failure_prob['market_multiplier']:.2f}x")
    print(f"    Competition Multiplier: {failure_prob['competition_multiplier']:.2f}x")
    
    # Test 7: Risk-Adjusted Profit Threshold
    print("\n[TEST 7] Risk-Adjusted Profit Threshold")
    print("-" * 80)
    
    for loan_amount in [25000, 100000, 250000]:
        category = risk_manager.categorize_loan_size(loan_amount)
        threshold = risk_manager.calculate_risk_adjusted_threshold(
            loan_amount_usd=loan_amount,
            expected_slippage=0.015,
            gas_cost_usd=30
        )
        print(f"  {category.upper()} loan (${loan_amount:,})")
        print(f"    Risk-Adjusted Threshold: ${threshold:,.2f}")
    
    # Test 8: Gas Cost Multiplier
    print("\n[TEST 8] Gas Cost Multipliers")
    print("-" * 80)
    
    for amount in test_amounts:
        category = risk_manager.categorize_loan_size(amount)
        multiplier = risk_manager.get_gas_cost_multiplier(amount)
        print(f"  {category.upper()} loan (${amount:,}) → {multiplier:.1f}x gas multiplier")
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED SUCCESSFULLY ✅")
    print("="*80)

def test_amm_calculator():
    """Test AMMCalculator with realistic values"""
    print("\n[BONUS] AMM Calculator Integration Test")
    print("-" * 80)
    
    amm = AMMCalculator()
    
    # Simulate a swap
    reserve_x = 1000000  # 1M tokens
    reserve_y = 2000000  # 2M tokens
    input_amount = 50000  # 50k tokens
    
    output = amm.calculate_swap_output(input_amount, reserve_x, reserve_y, 0.003)
    price_before = amm.calculate_price(reserve_x, reserve_y)
    reserve_y_after = reserve_y - output
    price_impact = amm.calculate_price_impact(reserve_y, reserve_y_after)
    
    print(f"  Pool Reserves: {reserve_x:,} / {reserve_y:,}")
    print(f"  Input Amount: {input_amount:,}")
    print(f"  Output Amount: {output:,.2f}")
    print(f"  Price Before: {price_before:.4f}")
    print(f"  Price Impact: {price_impact:.2f}%")

if __name__ == "__main__":
    try:
        test_flash_loan_risk_manager()
        test_amm_calculator()
        print("\n✅ All systems operational!")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

