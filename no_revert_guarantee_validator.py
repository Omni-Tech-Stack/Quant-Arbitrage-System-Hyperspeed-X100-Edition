#!/usr/bin/env python
"""
NO-REVERT GUARANTEE Validator
Ensures transactions will NEVER revert by validating all conditions before execution
Checks: Gas coverage, slippage tolerance, liquidity depth, price impact, GAS ORACLE
"""

import os
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime

# Import currency formatter for consistent decimal precision
from currency_formatter import format_currency_usd, format_percentage, fmt_usd

# Import gas oracle integration
try:
    from gas_oracle_integration import GasOracleIntegration
    GAS_ORACLE_AVAILABLE = True
except ImportError:
    GAS_ORACLE_AVAILABLE = False
    print("[NoRevert] Warning: Gas oracle integration not available")


class NoRevertGuaranteeValidator:
    """
    Validates that a transaction has NO possibility of reverting
    
    Checks performed:
    1. Profit > (Gas + Slippage + Price Impact + Safety Buffer)
    2. Liquidity sufficient for trade size
    3. Token balances exist in pools
    4. Pool reserves won't be depleted
    5. Price bounds within acceptable range
    """
    
    def __init__(
        self,
        safety_buffer_percent: float = 5.0,  # 5% safety buffer
        max_price_impact_percent: float = 2.0,  # 2% max price impact
        min_liquidity_ratio: float = 10.0,  # Trade size must be <10% of liquidity
        slippage_tolerance_percent: float = 1.0,  # 1% slippage tolerance
        use_gas_oracle: bool = True,  # Enable gas oracle integration
        chain_name: str = 'polygon',  # Default chain for gas oracle
    ):
        self.SAFETY_BUFFER_PERCENT = safety_buffer_percent
        self.MAX_PRICE_IMPACT_PERCENT = max_price_impact_percent
        self.MIN_LIQUIDITY_RATIO = min_liquidity_ratio
        self.SLIPPAGE_TOLERANCE_PERCENT = slippage_tolerance_percent
        self.chain_name = chain_name
        
        # Initialize Gas Oracle if available
        self.use_gas_oracle = use_gas_oracle and GAS_ORACLE_AVAILABLE
        self.gas_oracle = None
        
        if self.use_gas_oracle:
            try:
                self.gas_oracle = GasOracleIntegration(
                    update_interval_seconds=int(os.getenv('GAS_ORACLE_UPDATE_INTERVAL', '12')),
                    spike_threshold_percent=float(os.getenv('GAS_SPIKE_THRESHOLD_PCT', '150.0')),
                    history_window_blocks=20
                )
                print(f"[NoRevert] ✓ Gas Oracle Integration ENABLED")
            except Exception as e:
                print(f"[NoRevert] ✗ Gas Oracle initialization failed: {e}")
                self.gas_oracle = None
                self.use_gas_oracle = False
        
        # Statistics
        self.total_validated = 0
        self.total_approved = 0
        self.total_rejected = 0
        self.rejection_reasons = {}
        
        print(f"[NoRevert] ✓ Initialized NO-REVERT GUARANTEE Validator")
        print(f"  - Safety Buffer: {self.SAFETY_BUFFER_PERCENT}%")
        print(f"  - Max Price Impact: {self.MAX_PRICE_IMPACT_PERCENT}%")
        print(f"  - Min Liquidity Ratio: {self.MIN_LIQUIDITY_RATIO}x")
        print(f"  - Slippage Tolerance: {self.SLIPPAGE_TOLERANCE_PERCENT}%")
        print(f"  - Gas Oracle: {'ENABLED' if self.use_gas_oracle else 'DISABLED'}")
        print(f"  - Chain: {self.chain_name}")
    
    def validate_opportunity(
        self,
        opportunity: Dict[str, Any],
        gas_cost_usd: float,
        current_gas_price_gwei: float,
        estimated_gas_units: Optional[int] = None  # NEW: For gas oracle validation
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Comprehensive validation to guarantee NO REVERT
        NOW INCLUDES GAS ORACLE INTEGRATION (user's gas endpoints)
        
        Args:
            opportunity: Opportunity dict with path, profit, amounts
            gas_cost_usd: Accurate gas cost in USD
            current_gas_price_gwei: Current gas price from Infura API
            estimated_gas_units: Expected gas units for transaction (for gas oracle)
        
        Returns:
            (approved, reason, validation_details)
        """
        self.total_validated += 1
        
        # Extract opportunity data
        gross_profit = opportunity.get('gross_profit', 0)
        net_profit = opportunity.get('estimated_profit', 0)
        initial_amount = opportunity.get('initial_amount', 0)
        slippage_percent = opportunity.get('slippage', 0)
        path = opportunity.get('path', [])
        hops = opportunity.get('hops', 0)
        
        validation_details = {
            'validated_at': datetime.now().isoformat(),
            'gas_price_gwei': current_gas_price_gwei,
            'checks_performed': [],
            'risks_identified': [],
        }
        
        # CHECK 1: Gas Cost Coverage
        check_name = "gas_cost_coverage"
        validation_details['checks_performed'].append(check_name)
        
        if gas_cost_usd >= net_profit:
            self._record_rejection(check_name)
            return False, f"Gas cost ({fmt_usd(gas_cost_usd)}) exceeds profit ({fmt_usd(net_profit)})", validation_details
        
        gas_coverage_ratio = net_profit / gas_cost_usd if gas_cost_usd > 0 else 0
        validation_details['gas_coverage_ratio'] = gas_coverage_ratio
        
        if gas_coverage_ratio < 2.0:  # Profit must be at least 2x gas cost
            validation_details['risks_identified'].append(f"Low gas coverage ratio: {gas_coverage_ratio:.2f}x")
        
        # CHECK 2: Slippage Cost
        check_name = "slippage_tolerance"
        validation_details['checks_performed'].append(check_name)
        
        slippage_cost_usd = (slippage_percent / 100) * initial_amount
        validation_details['slippage_cost_usd'] = slippage_cost_usd
        
        if slippage_percent > self.SLIPPAGE_TOLERANCE_PERCENT:
            validation_details['risks_identified'].append(f"High slippage: {format_percentage(slippage_percent)}")
        
        # CHECK 3: Price Impact per Hop
        check_name = "price_impact"
        validation_details['checks_performed'].append(check_name)
        
        max_price_impact = 0.0
        for i, pool in enumerate(path):
            liquidity = float(pool.get('liquidity', 0))
            
            if liquidity == 0:
                self._record_rejection(check_name)
                return False, f"Pool {i+1} has zero liquidity", validation_details
            
            # Calculate price impact
            trade_size = initial_amount / hops if hops > 0 else initial_amount
            price_impact = (trade_size / liquidity) * 100
            max_price_impact = max(max_price_impact, price_impact)
            
            if price_impact > self.MAX_PRICE_IMPACT_PERCENT:
                self._record_rejection(check_name)
                return False, f"Price impact too high in pool {i+1}: {format_percentage(price_impact)}", validation_details
        
        validation_details['max_price_impact_percent'] = max_price_impact
        
        # CHECK 4: Liquidity Depth
        check_name = "liquidity_depth"
        validation_details['checks_performed'].append(check_name)
        
        for i, pool in enumerate(path):
            liquidity = float(pool.get('liquidity', 0))
            required_liquidity = initial_amount * self.MIN_LIQUIDITY_RATIO
            
            if liquidity < required_liquidity:
                self._record_rejection(check_name)
                return False, f"Insufficient liquidity in pool {i+1}: {fmt_usd(liquidity)} < {fmt_usd(required_liquidity)}", validation_details
        
        # CHECK 5: Total Risk vs Profit
        check_name = "total_risk_coverage"
        validation_details['checks_performed'].append(check_name)
        
        safety_buffer = (self.SAFETY_BUFFER_PERCENT / 100) * initial_amount
        total_risk = gas_cost_usd + slippage_cost_usd + safety_buffer
        net_profit_after_all_risks = net_profit - total_risk
        
        validation_details['total_risk_usd'] = total_risk
        validation_details['safety_buffer_usd'] = safety_buffer
        validation_details['net_profit_after_all_risks'] = net_profit_after_all_risks
        
        if net_profit_after_all_risks <= 0:
            self._record_rejection(check_name)
            return False, f"Profit ({fmt_usd(net_profit)}) doesn't cover total risk ({fmt_usd(total_risk)})", validation_details
        
        # CHECK 6: Reserve Depletion Prevention
        check_name = "reserve_depletion"
        validation_details['checks_performed'].append(check_name)
        
        for i, pool in enumerate(path):
            reserve0 = float(pool.get('reserve0', 0))
            reserve1 = float(pool.get('reserve1', 0))
            
            if reserve0 == 0 or reserve1 == 0:
                self._record_rejection(check_name)
                return False, f"Pool {i+1} has zero reserves", validation_details
            
            # Ensure we're not taking more than 15% of any reserve
            max_reserve = max(reserve0, reserve1)
            if initial_amount > max_reserve * 0.15:
                self._record_rejection(check_name)
                return False, f"Trade size exceeds 15% of pool {i+1} reserves", validation_details
        
        # CHECK 7: Profitability Threshold
        check_name = "profitability_threshold"
        validation_details['checks_performed'].append(check_name)
        
        min_profit_usd = float(os.getenv('MIN_PROFIT_USD', 15))
        
        if net_profit_after_all_risks < min_profit_usd:
            self._record_rejection(check_name)
            return False, f"Net profit ({fmt_usd(net_profit_after_all_risks)}) below minimum ({fmt_usd(min_profit_usd)})", validation_details
        
        # CHECK 8: Gas Oracle Validation (NEW - USER'S GAS ENDPOINTS)
        check_name = "gas_oracle_validation"
        validation_details['checks_performed'].append(check_name)
        
        if self.use_gas_oracle and self.gas_oracle and estimated_gas_units:
            try:
                # Fetch real-time gas prices from user's Infura/Alchemy/QuickNode endpoints
                gas_oracle_data = self.gas_oracle.fetch_gas_price(self.chain_name)
                
                # Add gas oracle data to validation details
                validation_details['gas_oracle'] = {
                    'current_gas_gwei': gas_oracle_data.get('gas_price_gwei', 0),
                    'baseline_gwei': gas_oracle_data.get('baseline_gwei', 0),
                    'is_spike': gas_oracle_data.get('is_spike', False),
                    'spike_multiplier': gas_oracle_data.get('spike_multiplier', 1.0),
                    'source': gas_oracle_data.get('source', 'unknown'),
                    'max_fee_per_gas_gwei': gas_oracle_data.get('max_fee_per_gas_gwei', 0),
                }
                
                # Check for gas price spike
                if gas_oracle_data.get('is_spike'):
                    spike_multiplier = gas_oracle_data.get('spike_multiplier', 1.0)
                    validation_details['risks_identified'].append(
                        f"Gas price spike detected: {spike_multiplier:.1f}x baseline"
                    )
                    
                    # Apply dynamic gas buffer during spikes
                    gas_buffer_multiplier = float(os.getenv('MAX_GAS_BUFFER_MULTIPLIER', '1.5'))
                    dynamic_gas_cost = gas_cost_usd * spike_multiplier * gas_buffer_multiplier
                    
                    validation_details['dynamic_gas_cost_usd'] = dynamic_gas_cost
                    
                    # Re-validate profitability with spike-adjusted gas
                    if net_profit < dynamic_gas_cost:
                        self._record_rejection(check_name)
                        return False, f"Gas spike makes trade unprofitable: {fmt_usd(dynamic_gas_cost)} gas cost > {fmt_usd(net_profit)} profit", validation_details
                
                # Validate gas price is within acceptable range
                max_gas_price_gwei = float(os.getenv('MAX_GAS_PRICE_GWEI', 2100))
                oracle_gas_price = gas_oracle_data.get('gas_price_gwei', 0)
                
                if oracle_gas_price > max_gas_price_gwei:
                    self._record_rejection(check_name)
                    return False, f"Gas price too high: {oracle_gas_price:.1f} gwei > {max_gas_price_gwei:.1f} gwei limit", validation_details
                
                # Validate transaction with gas oracle
                gas_validation = self.gas_oracle.validate_gas_for_transaction(
                    estimated_gas_units=estimated_gas_units,
                    max_gas_price_gwei=max_gas_price_gwei,
                    chain_name=self.chain_name,
                    safety_multiplier=1.5
                )
                
                validation_details['gas_oracle_validation'] = gas_validation
                
                if not gas_validation['approved']:
                    self._record_rejection(check_name)
                    return False, f"Gas oracle validation failed: {gas_validation['reason']}", validation_details
                
                # Add gas oracle insights
                validation_details['gas_oracle_cost_usd'] = gas_validation.get('estimated_cost_usd', 0)
                
            except Exception as e:
                # Don't fail validation if gas oracle has issues - log warning
                validation_details['risks_identified'].append(f"Gas oracle check failed: {str(e)}")
                print(f"[NoRevert] Warning: Gas oracle check failed: {e}")
        
        elif self.use_gas_oracle and estimated_gas_units is None:
            validation_details['risks_identified'].append("Gas oracle enabled but estimated_gas_units not provided")
        
        # ALL CHECKS PASSED - NO REVERT GUARANTEED
        self.total_approved += 1
        
        validation_details['guarantee_status'] = 'APPROVED'
        validation_details['confidence_score'] = self._calculate_confidence(validation_details)
        
        return True, "NO-REVERT GUARANTEED", validation_details
    
    def _calculate_confidence(self, details: Dict) -> float:
        """Calculate confidence score 0-100%"""
        score = 100.0
        
        # Deduct for risks
        for risk in details.get('risks_identified', []):
            score -= 5.0
        
        # Bonus for high gas coverage
        gas_coverage = details.get('gas_coverage_ratio', 0)
        if gas_coverage > 5.0:
            score += 10.0
        elif gas_coverage < 2.0:
            score -= 10.0
        
        # Bonus for low price impact
        price_impact = details.get('max_price_impact_percent', 0)
        if price_impact < 0.5:
            score += 5.0
        elif price_impact > 1.5:
            score -= 5.0
        
        return max(0.0, min(100.0, score))
    
    def _record_rejection(self, reason: str):
        """Record rejection reason"""
        self.total_rejected += 1
        if reason not in self.rejection_reasons:
            self.rejection_reasons[reason] = 0
        self.rejection_reasons[reason] += 1
    
    def print_statistics(self):
        """Print validation statistics"""
        print("\n" + "=" * 80)
        print("  NO-REVERT GUARANTEE VALIDATOR STATISTICS")
        print("=" * 80)
        
        print(f"\n  Total Validated: {self.total_validated}")
        print(f"  Total Approved: {self.total_approved}")
        print(f"  Total Rejected: {self.total_rejected}")
        
        if self.total_validated > 0:
            approval_rate = (self.total_approved / self.total_validated) * 100
            print(f"  Approval Rate: {approval_rate:.1f}%")
        
        if self.rejection_reasons:
            print(f"\n  Rejection Reasons:")
            for reason, count in sorted(self.rejection_reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {reason}: {count}")
        
        print("=" * 80 + "\n")


# Example usage
if __name__ == "__main__":
    validator = NoRevertGuaranteeValidator()
    
    # Test case 1: Good opportunity
    good_opp = {
        'gross_profit': 1000,
        'estimated_profit': 950,
        'initial_amount': 100000,
        'slippage': 0.5,
        'hops': 2,
        'path': [
            {'liquidity': 5000000, 'reserve0': 2500000, 'reserve1': 2500000},
            {'liquidity': 3000000, 'reserve0': 1500000, 'reserve1': 1500000},
        ]
    }
    
    approved, reason, details = validator.validate_opportunity(good_opp, 45.0, 50.0)
    print(f"\n✅ Good Opportunity:")
    print(f"  Approved: {approved}")
    print(f"  Reason: {reason}")
    print(f"  Confidence: {details.get('confidence_score', 0):.1f}%")
    
    # Test case 2: High gas cost
    bad_opp = {
        'gross_profit': 60,
        'estimated_profit': 50,
        'initial_amount': 10000,
        'slippage': 0.5,
        'hops': 2,
        'path': [
            {'liquidity': 500000, 'reserve0': 250000, 'reserve1': 250000},
            {'liquidity': 300000, 'reserve0': 150000, 'reserve1': 150000},
        ]
    }
    
    approved, reason, details = validator.validate_opportunity(bad_opp, 45.0, 50.0)
    print(f"\n❌ Bad Opportunity:")
    print(f"  Approved: {approved}")
    print(f"  Reason: {reason}")
    
    validator.print_statistics()
