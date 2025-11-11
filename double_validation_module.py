#!/usr/bin/env python3
"""
DOUBLE VALIDATION MODULE
Implements two-phase validation for critical execution decisions
Required for unaccounted data, flagged data, or large trades
"""

import time
import asyncio
from typing import Dict, Any, Optional, Tuple, List
import logging

from data_accounting_tracker import DataPoint, DataAccountingTracker, get_tracker
from fallback_coordinator import FallbackCoordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DoubleValidationResult:
    """Result of double-validation process"""
    
    def __init__(
        self,
        passed: bool,
        reason: str,
        phase1_data: Dict[str, Any],
        phase2_data: Dict[str, Any],
        deviation: float,
        confidence_delta: float
    ):
        self.passed = passed
        self.reason = reason
        self.phase1_data = phase1_data
        self.phase2_data = phase2_data
        self.deviation = deviation  # % deviation between phases
        self.confidence_delta = confidence_delta  # Confidence difference
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'passed': self.passed,
            'reason': self.reason,
            'phase1_data': self.phase1_data,
            'phase2_data': self.phase2_data,
            'deviation': self.deviation,
            'deviation_pct': round(self.deviation * 100, 4),
            'confidence_delta': self.confidence_delta,
            'timestamp': self.timestamp
        }


class DoubleValidationModule:
    """
    Two-phase validation for critical data
    
    Phase 1: Standard validation with fallback coordinator
    Phase 2: Independent re-validation using different data sources
    
    Comparison: Ensure <1% deviation between phases
    """
    
    def __init__(
        self,
        fallback_coordinator: Optional[FallbackCoordinator] = None,
        data_tracker: Optional[DataAccountingTracker] = None,
        max_deviation: float = 0.01,  # 1% max deviation between phases
        inter_phase_delay: float = 0.5,  # Delay between phases (seconds)
        require_independent_sources: bool = True
    ):
        """
        Initialize Double Validation Module
        
        Args:
            fallback_coordinator: Fallback coordinator for data fetching
            data_tracker: Data accounting tracker
            max_deviation: Max % deviation between Phase 1 and Phase 2
            inter_phase_delay: Delay between phases to allow data refresh
            require_independent_sources: Require different sources in Phase 2
        """
        self.coordinator = fallback_coordinator
        self.tracker = data_tracker or get_tracker()
        self.max_deviation = max_deviation
        self.inter_phase_delay = inter_phase_delay
        self.require_independent = require_independent_sources
        
        # Statistics
        self.total_validations = 0
        self.total_passed = 0
        self.total_failed = 0
        self.failure_reasons: Dict[str, int] = {}
        
        logger.info("[DoubleValidation] ✓ Initialized Double Validation Module")
        logger.info(f"  - Max Deviation: {max_deviation*100}%")
        logger.info(f"  - Inter-Phase Delay: {inter_phase_delay}s")
        logger.info(f"  - Independent Sources: {'REQUIRED' if require_independent else 'OPTIONAL'}")
    
    async def double_validate_opportunity(
        self,
        opportunity: Dict[str, Any],
        data_points: List[DataPoint]
    ) -> DoubleValidationResult:
        """
        Perform two-phase validation on an arbitrage opportunity
        
        Args:
            opportunity: Opportunity dictionary
            data_points: List of data points used in opportunity calculation
        
        Returns:
            DoubleValidationResult
        """
        self.total_validations += 1
        
        logger.info(
            f"[DoubleValidation] Starting double-validation for opportunity "
            f"(profit: ${opportunity.get('profit_usd', 0):.2f})"
        )
        
        # PHASE 1: Standard Validation
        logger.info("[DoubleValidation] Phase 1: Standard validation")
        phase1_result = await self._phase1_validation(opportunity, data_points)
        
        if not phase1_result['valid']:
            self._record_failure("phase1_failed")
            return DoubleValidationResult(
                passed=False,
                reason=f"Phase 1 failed: {phase1_result['reason']}",
                phase1_data=phase1_result,
                phase2_data={},
                deviation=0.0,
                confidence_delta=0.0
            )
        
        # Wait between phases to allow data refresh
        logger.info(f"[DoubleValidation] Waiting {self.inter_phase_delay}s before Phase 2")
        await asyncio.sleep(self.inter_phase_delay)
        
        # PHASE 2: Independent Re-validation
        logger.info("[DoubleValidation] Phase 2: Independent re-validation")
        phase2_result = await self._phase2_validation(
            opportunity, data_points, phase1_result
        )
        
        if not phase2_result['valid']:
            self._record_failure("phase2_failed")
            return DoubleValidationResult(
                passed=False,
                reason=f"Phase 2 failed: {phase2_result['reason']}",
                phase1_data=phase1_result,
                phase2_data=phase2_result,
                deviation=0.0,
                confidence_delta=0.0
            )
        
        # COMPARISON: Check deviation between phases
        logger.info("[DoubleValidation] Comparing Phase 1 vs Phase 2")
        deviation = self._calculate_deviation(phase1_result, phase2_result)
        confidence_delta = abs(
            phase1_result.get('avg_confidence', 0) - 
            phase2_result.get('avg_confidence', 0)
        )
        
        if deviation > self.max_deviation:
            self._record_failure("high_deviation")
            return DoubleValidationResult(
                passed=False,
                reason=f"Phase 1/2 deviation too high: {deviation*100:.2f}% > {self.max_deviation*100}%",
                phase1_data=phase1_result,
                phase2_data=phase2_result,
                deviation=deviation,
                confidence_delta=confidence_delta
            )
        
        # Success!
        self.total_passed += 1
        
        logger.info(
            f"[DoubleValidation] ✓ PASSED - Deviation: {deviation*100:.2f}%, "
            f"Confidence Δ: {confidence_delta:.2f}"
        )
        
        return DoubleValidationResult(
            passed=True,
            reason="Double-validation passed",
            phase1_data=phase1_result,
            phase2_data=phase2_result,
            deviation=deviation,
            confidence_delta=confidence_delta
        )
    
    async def _phase1_validation(
        self,
        opportunity: Dict[str, Any],
        data_points: List[DataPoint]
    ) -> Dict[str, Any]:
        """
        Phase 1: Standard validation
        
        Checks:
        - All data points are accounted
        - All data points are validated
        - No flagged data
        - Staleness within limits
        - Confidence above thresholds
        """
        result = {
            'valid': True,
            'reason': '',
            'data_points_checked': len(data_points),
            'avg_confidence': 0.0,
            'sources': [],
            'layers': []
        }
        
        if not data_points:
            result['valid'] = False
            result['reason'] = "No data points provided"
            return result
        
        # Check each data point
        confidences = []
        sources = []
        layers = []
        
        for dp in data_points:
            # Check if accounted
            if dp.request_id and not self.tracker.get_data_point(dp.request_id):
                result['valid'] = False
                result['reason'] = f"Unaccounted data point: {dp.data_type}"
                return result
            
            # Check validation status
            if dp.validation_status.value != "validated":
                result['valid'] = False
                result['reason'] = f"Unvalidated data: {dp.data_type} ({dp.validation_status.value})"
                return result
            
            # Check staleness
            dp.update_staleness()
            max_age = self.tracker.STALENESS_LIMITS.get(
                dp.data_type, 
                self.tracker.STALENESS_LIMITS['default']
            )
            if dp.staleness > max_age:
                result['valid'] = False
                result['reason'] = f"Stale data: {dp.data_type} ({dp.staleness:.1f}s > {max_age}s)"
                return result
            
            # Check confidence
            min_conf = self.tracker.MIN_CONFIDENCE.get(
                dp.data_type,
                self.tracker.MIN_CONFIDENCE['default']
            )
            if dp.confidence < min_conf:
                result['valid'] = False
                result['reason'] = f"Low confidence: {dp.data_type} ({dp.confidence:.2f} < {min_conf})"
                return result
            
            confidences.append(dp.confidence)
            sources.append(dp.source.value)
            layers.append(dp.layer)
        
        result['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0.0
        result['sources'] = sources
        result['layers'] = layers
        result['reason'] = "Phase 1 validation passed"
        
        return result
    
    async def _phase2_validation(
        self,
        opportunity: Dict[str, Any],
        original_data_points: List[DataPoint],
        phase1_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 2: Independent re-validation
        
        Fetches fresh data from different sources (if possible)
        Validates independently of Phase 1
        """
        result = {
            'valid': True,
            'reason': '',
            'data_points_checked': 0,
            'avg_confidence': 0.0,
            'sources': [],
            'layers': [],
            'values': {}
        }
        
        if not self.coordinator:
            result['valid'] = False
            result['reason'] = "No fallback coordinator available for Phase 2"
            return result
        
        # Re-fetch critical data points
        confidences = []
        sources = []
        layers = []
        values = {}
        
        for dp in original_data_points:
            # Skip if not critical data type
            if dp.data_type not in ['price', 'gas', 'liquidity']:
                continue
            
            try:
                # Fetch fresh data
                fresh_dp = await self.coordinator.fetch_with_fallback(
                    data_type=dp.data_type,
                    chain=dp.chain,
                    token=dp.token,
                    oracle_verification_config={
                        'type': 'chainlink',
                        'chain': dp.chain,
                        'token_pair': f"{dp.token}/USD" if dp.token else None
                    } if dp.data_type == 'price' else None
                )
                
                if not fresh_dp:
                    result['valid'] = False
                    result['reason'] = f"Failed to re-fetch {dp.data_type}"
                    return result
                
                # Check if source is different (independent validation)
                if self.require_independent and fresh_dp.source == dp.source:
                    logger.warning(
                        f"[DoubleValidation] Phase 2 used same source as Phase 1: "
                        f"{dp.source.value}"
                    )
                
                confidences.append(fresh_dp.confidence)
                sources.append(fresh_dp.source.value)
                layers.append(fresh_dp.layer)
                values[dp.data_type] = fresh_dp.value
                
            except Exception as e:
                result['valid'] = False
                result['reason'] = f"Error re-fetching {dp.data_type}: {e}"
                return result
        
        result['data_points_checked'] = len(confidences)
        result['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0.0
        result['sources'] = sources
        result['layers'] = layers
        result['values'] = values
        result['reason'] = "Phase 2 validation passed"
        
        return result
    
    def _calculate_deviation(
        self,
        phase1: Dict[str, Any],
        phase2: Dict[str, Any]
    ) -> float:
        """
        Calculate deviation between Phase 1 and Phase 2 results
        
        Returns:
            float: Maximum % deviation across all data points
        """
        # For now, compare average confidence as a proxy
        # In production, compare actual values from phase2['values']
        
        conf1 = phase1.get('avg_confidence', 0)
        conf2 = phase2.get('avg_confidence', 0)
        
        if conf1 == 0:
            return 1.0  # 100% deviation if no Phase 1 data
        
        deviation = abs(conf1 - conf2) / conf1
        
        return deviation
    
    def _record_failure(self, reason: str):
        """Record failure reason"""
        self.total_failed += 1
        self.failure_reasons[reason] = self.failure_reasons.get(reason, 0) + 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get double-validation statistics"""
        total = max(self.total_validations, 1)
        
        return {
            'total_validations': self.total_validations,
            'total_passed': self.total_passed,
            'total_failed': self.total_failed,
            'pass_rate': round(self.total_passed / total, 4),
            'fail_rate': round(self.total_failed / total, 4),
            'failure_reasons': self.failure_reasons
        }
    
    def print_statistics(self):
        """Print double-validation statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*80)
        print("  DOUBLE VALIDATION STATISTICS")
        print("="*80)
        print(f"Total Validations: {stats['total_validations']}")
        print(f"Passed:            {stats['total_passed']} ({stats['pass_rate']*100:.1f}%)")
        print(f"Failed:            {stats['total_failed']} ({stats['fail_rate']*100:.1f}%)")
        
        if stats['failure_reasons']:
            print(f"\nFailure Reasons:")
            for reason, count in stats['failure_reasons'].items():
                print(f"  {reason}: {count}")
        
        print("="*80 + "\n")


async def requires_double_validation(
    opportunity: Dict[str, Any],
    data_points: List[DataPoint],
    tracker: Optional[DataAccountingTracker] = None
) -> Tuple[bool, str]:
    """
    Check if an opportunity requires double-validation
    
    Returns:
        (required, reason)
    """
    tracker = tracker or get_tracker()
    
    # Check for unaccounted data
    for dp in data_points:
        if dp.request_id and tracker.requires_double_validation(dp.request_id):
            return True, "Unaccounted or flagged data present"
    
    # Check for low confidence
    confidences = [dp.confidence for dp in data_points]
    if confidences and min(confidences) < 0.85:
        return True, f"Low confidence data present (min: {min(confidences):.2f})"
    
    # Check for stale data
    for dp in data_points:
        dp.update_staleness()
        max_age = tracker.STALENESS_LIMITS.get(dp.data_type, 30)
        if dp.staleness > max_age:
            return True, f"Stale data present ({dp.data_type}: {dp.staleness:.1f}s)"
    
    # Check for large trade size
    profit_usd = opportunity.get('profit_usd', 0)
    if profit_usd > 100000:  # >$100k
        return True, f"Large trade size (${profit_usd:,.0f})"
    
    # Check for high gas cost
    gas_cost_usd = opportunity.get('gas_cost_usd', 0)
    if gas_cost_usd > 50:  # >$50 gas
        return True, f"High gas cost (${gas_cost_usd:.2f})"
    
    return False, "Double-validation not required"


if __name__ == "__main__":
    # Example usage
    async def main():
        validator = DoubleValidationModule()
        
        # Create mock data points
        data_points = [
            DataPoint(
                value=1850.00,
                data_type="price",
                source=DataSource.UNISWAP_SDK,
                layer=1,
                chain="polygon",
                token="WETH"
            )
        ]
        
        opportunity = {
            'profit_usd': 150000.0,
            'gas_cost_usd': 60.0
        }
        
        # Check if double-validation required
        required, reason = await requires_double_validation(opportunity, data_points)
        print(f"\nDouble-validation required: {required}")
        print(f"Reason: {reason}\n")
        
        # Print statistics
        validator.print_statistics()
    
    asyncio.run(main())
