#!/usr/bin/env python3
"""
FALLBACK COORDINATOR
Orchestrates 4-layer fallback data fetching with oracle verification
Ensures data availability even when primary sources fail
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
import logging

from data_accounting_tracker import (
    DataPoint, DataSource, ValidationStatus,
    DataAccountingTracker, get_tracker
)
from oracle_verification_manager import OracleVerificationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Fallback strategy types"""
    FAIL_FAST = "fail_fast"          # Stop at first success
    CONSENSUS = "consensus"           # Try multiple, require agreement
    BEST_EFFORT = "best_effort"       # Try all, use best available
    PARALLEL = "parallel"             # Try all in parallel


class FallbackCoordinator:
    """
    Coordinates 4-layer fallback data fetching with validation
    
    Architecture:
    Layer 1: Primary SDK Sources (Uniswap SDK, Balancer SDK, etc.)
    Layer 2: RPC Endpoint Rotation (Alchemy, Infura, QuickNode)
    Layer 3: Cached + Aggregated Data
    Layer 4: Emergency Static Fallbacks
    """
    
    def __init__(
        self,
        oracle_manager: Optional[OracleVerificationManager] = None,
        data_tracker: Optional[DataAccountingTracker] = None,
        default_strategy: FallbackStrategy = FallbackStrategy.FAIL_FAST,
        require_oracle_verification: bool = True,
        min_confidence: float = 0.85
    ):
        """
        Initialize Fallback Coordinator
        
        Args:
            oracle_manager: Oracle verification manager instance
            data_tracker: Data accounting tracker instance
            default_strategy: Default fallback strategy
            require_oracle_verification: Whether to require oracle verification
            min_confidence: Minimum confidence score to accept data
        """
        self.oracle_manager = oracle_manager or OracleVerificationManager()
        self.data_tracker = data_tracker or get_tracker()
        self.default_strategy = default_strategy
        self.require_oracle_verification = require_oracle_verification
        self.min_confidence = min_confidence
        
        # Fallback function registry
        self.layer_1_fetchers: List[Callable] = []
        self.layer_2_fetchers: List[Callable] = []
        self.layer_3_fetchers: List[Callable] = []
        self.layer_4_fetchers: List[Callable] = []
        
        # Statistics
        self.total_requests = 0
        self.layer_successes = {1: 0, 2: 0, 3: 0, 4: 0}
        self.layer_attempts = {1: 0, 2: 0, 3: 0, 4: 0}
        self.total_fallbacks = 0
        self.total_failures = 0
        
        logger.info("[FallbackCoordinator] ✓ Initialized Fallback Coordinator")
        logger.info(f"  - Default Strategy: {default_strategy.value}")
        logger.info(f"  - Oracle Verification: {'REQUIRED' if require_oracle_verification else 'OPTIONAL'}")
        logger.info(f"  - Min Confidence: {min_confidence}")
    
    def register_layer_1_fetcher(self, fetcher: Callable):
        """Register a Layer 1 (SDK) data fetcher"""
        self.layer_1_fetchers.append(fetcher)
        logger.debug(f"[FallbackCoordinator] Registered Layer 1 fetcher: {fetcher.__name__}")
    
    def register_layer_2_fetcher(self, fetcher: Callable):
        """Register a Layer 2 (RPC) data fetcher"""
        self.layer_2_fetchers.append(fetcher)
        logger.debug(f"[FallbackCoordinator] Registered Layer 2 fetcher: {fetcher.__name__}")
    
    def register_layer_3_fetcher(self, fetcher: Callable):
        """Register a Layer 3 (Aggregated/Cache) data fetcher"""
        self.layer_3_fetchers.append(fetcher)
        logger.debug(f"[FallbackCoordinator] Registered Layer 3 fetcher: {fetcher.__name__}")
    
    def register_layer_4_fetcher(self, fetcher: Callable):
        """Register a Layer 4 (Emergency Fallback) data fetcher"""
        self.layer_4_fetchers.append(fetcher)
        logger.debug(f"[FallbackCoordinator] Registered Layer 4 fetcher: {fetcher.__name__}")
    
    async def fetch_with_fallback(
        self,
        data_type: str,
        strategy: Optional[FallbackStrategy] = None,
        oracle_verification_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[DataPoint]:
        """
        Fetch data with 4-layer fallback and oracle verification
        
        Args:
            data_type: Type of data to fetch ("price", "gas", "liquidity", etc.)
            strategy: Fallback strategy (uses default if None)
            oracle_verification_config: Config for oracle verification
            **kwargs: Additional parameters for fetchers
        
        Returns:
            DataPoint: Validated data point or None if all layers fail
        """
        self.total_requests += 1
        strategy = strategy or self.default_strategy
        
        logger.info(f"[FallbackCoordinator] Fetching {data_type} with strategy {strategy.value}")
        
        # Try each layer in sequence
        for layer_num, fetchers in [
            (1, self.layer_1_fetchers),
            (2, self.layer_2_fetchers),
            (3, self.layer_3_fetchers),
            (4, self.layer_4_fetchers)
        ]:
            if not fetchers:
                logger.debug(f"[FallbackCoordinator] No fetchers registered for Layer {layer_num}")
                continue
            
            self.layer_attempts[layer_num] += 1
            
            logger.debug(f"[FallbackCoordinator] Trying Layer {layer_num} ({len(fetchers)} fetchers)")
            
            # Try fetchers in this layer
            results = await self._try_layer_fetchers(
                fetchers, layer_num, data_type, strategy, kwargs
            )
            
            if not results:
                logger.debug(f"[FallbackCoordinator] Layer {layer_num} failed - falling back")
                self.total_fallbacks += 1
                continue
            
            # Verify with oracles if required
            if self.require_oracle_verification and oracle_verification_config:
                verified_result = await self._verify_with_oracle(
                    results[0], oracle_verification_config
                )
                if verified_result:
                    results = [verified_result]
                else:
                    logger.warning(
                        f"[FallbackCoordinator] Layer {layer_num} oracle verification failed"
                    )
                    continue
            
            # Check confidence threshold
            best_result = self._select_best_result(results, strategy)
            
            if best_result and best_result.confidence >= self.min_confidence:
                logger.info(
                    f"[FallbackCoordinator] ✓ Success from Layer {layer_num} "
                    f"(confidence: {best_result.confidence:.2f})"
                )
                self.layer_successes[layer_num] += 1
                
                # Record in data tracker
                request_id = self.data_tracker.record(best_result)
                
                # Mark as validated if oracle verified or high confidence
                if best_result.oracle_verified or best_result.confidence >= 0.95:
                    self.data_tracker.validate(
                        request_id,
                        oracle_verified=best_result.oracle_verified,
                        oracle_source=best_result.oracle_source,
                        oracle_deviation=best_result.oracle_deviation
                    )
                
                return best_result
            else:
                logger.debug(
                    f"[FallbackCoordinator] Layer {layer_num} result below confidence threshold"
                )
        
        # All layers failed
        logger.error(f"[FallbackCoordinator] ✗ All 4 layers failed for {data_type}")
        self.total_failures += 1
        return None
    
    async def _try_layer_fetchers(
        self,
        fetchers: List[Callable],
        layer_num: int,
        data_type: str,
        strategy: FallbackStrategy,
        kwargs: Dict[str, Any]
    ) -> List[DataPoint]:
        """
        Try all fetchers in a layer
        
        Returns:
            List[DataPoint]: Successful results
        """
        results = []
        
        if strategy == FallbackStrategy.PARALLEL:
            # Try all fetchers in parallel
            tasks = [self._call_fetcher(f, layer_num, data_type, kwargs) for f in fetchers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [r for r in results if isinstance(r, DataPoint)]
        
        else:
            # Try fetchers sequentially
            for fetcher in fetchers:
                try:
                    result = await self._call_fetcher(fetcher, layer_num, data_type, kwargs)
                    if result:
                        results.append(result)
                        
                        if strategy == FallbackStrategy.FAIL_FAST:
                            # Stop at first success
                            break
                
                except Exception as e:
                    logger.debug(f"[FallbackCoordinator] Fetcher {fetcher.__name__} failed: {e}")
                    continue
        
        return results
    
    async def _call_fetcher(
        self,
        fetcher: Callable,
        layer_num: int,
        data_type: str,
        kwargs: Dict[str, Any]
    ) -> Optional[DataPoint]:
        """
        Call a data fetcher and wrap result in DataPoint
        
        Returns:
            DataPoint or None
        """
        try:
            # Call fetcher (may be async or sync)
            if asyncio.iscoroutinefunction(fetcher):
                result = await fetcher(**kwargs)
            else:
                result = fetcher(**kwargs)
            
            if result is None:
                return None
            
            # If already a DataPoint, return it
            if isinstance(result, DataPoint):
                return result
            
            # Otherwise, wrap in DataPoint
            data_point = DataPoint(
                value=result.get('value') if isinstance(result, dict) else result,
                data_type=data_type,
                source=self._infer_data_source(fetcher.__name__, layer_num),
                layer=layer_num,
                chain=kwargs.get('chain'),
                token=kwargs.get('token'),
                metadata={'fetcher': fetcher.__name__}
            )
            
            return data_point
        
        except Exception as e:
            logger.debug(f"[FallbackCoordinator] Error calling {fetcher.__name__}: {e}")
            return None
    
    def _infer_data_source(self, fetcher_name: str, layer: int) -> DataSource:
        """Infer DataSource from fetcher name and layer"""
        fetcher_lower = fetcher_name.lower()
        
        # Layer 1 sources
        if 'uniswap' in fetcher_lower or 'sdk' in fetcher_lower:
            return DataSource.UNISWAP_SDK
        elif 'balancer' in fetcher_lower:
            return DataSource.BALANCER_SDK
        elif 'curve' in fetcher_lower:
            return DataSource.CURVE_SDK
        elif 'subgraph' in fetcher_lower:
            return DataSource.SUBGRAPH
        elif 'contract' in fetcher_lower:
            return DataSource.DIRECT_CONTRACT
        
        # Layer 2 sources
        elif 'alchemy' in fetcher_lower:
            return DataSource.ALCHEMY_RPC
        elif 'infura' in fetcher_lower:
            return DataSource.INFURA_RPC
        elif 'quicknode' in fetcher_lower:
            return DataSource.QUICKNODE_RPC
        elif 'rpc' in fetcher_lower:
            return DataSource.PUBLIC_RPC
        
        # Layer 3 sources
        elif 'cache' in fetcher_lower:
            return DataSource.LOCAL_CACHE
        elif 'aggregat' in fetcher_lower:
            return DataSource.AGGREGATED
        elif 'historical' in fetcher_lower or 'baseline' in fetcher_lower:
            return DataSource.HISTORICAL_BASELINE
        
        # Layer 4 sources
        elif 'fallback' in fetcher_lower or 'emergency' in fetcher_lower:
            return DataSource.LAST_KNOWN_GOOD
        elif 'conservative' in fetcher_lower:
            return DataSource.CONSERVATIVE_ESTIMATE
        elif 'default' in fetcher_lower:
            return DataSource.SAFE_DEFAULT
        
        # Default based on layer
        layer_defaults = {
            1: DataSource.DIRECT_CONTRACT,
            2: DataSource.PUBLIC_RPC,
            3: DataSource.LOCAL_CACHE,
            4: DataSource.SAFE_DEFAULT
        }
        return layer_defaults.get(layer, DataSource.UNKNOWN)
    
    async def _verify_with_oracle(
        self,
        data_point: DataPoint,
        oracle_config: Dict[str, Any]
    ) -> Optional[DataPoint]:
        """
        Verify data point with oracle
        
        Args:
            data_point: Data point to verify
            oracle_config: Oracle configuration
        
        Returns:
            Updated DataPoint or None if verification fails
        """
        try:
            oracle_type = oracle_config.get('type', 'chainlink')
            
            if oracle_type == 'chainlink' and data_point.data_type == 'price':
                verified, deviation, oracle_data = self.oracle_manager.verify_price_with_chainlink(
                    token_pair=oracle_config.get('token_pair'),
                    price=float(data_point.value),
                    chain=oracle_config.get('chain', 'polygon')
                )
                
                if verified:
                    data_point.oracle_verified = True
                    data_point.oracle_source = 'chainlink'
                    data_point.oracle_deviation = deviation
                    data_point.confidence = data_point._calculate_confidence()
                    return data_point
            
            elif oracle_type == 'uniswap_twap':
                verified, deviation, oracle_data = self.oracle_manager.verify_price_with_uniswap_twap(
                    pool_address=oracle_config.get('pool_address'),
                    current_price=float(data_point.value),
                    chain=oracle_config.get('chain', 'polygon')
                )
                
                if verified:
                    data_point.oracle_verified = True
                    data_point.oracle_source = 'uniswap_twap'
                    data_point.oracle_deviation = deviation
                    data_point.confidence = data_point._calculate_confidence()
                    return data_point
            
            return None
        
        except Exception as e:
            logger.error(f"[FallbackCoordinator] Oracle verification error: {e}")
            return None
    
    def _select_best_result(
        self,
        results: List[DataPoint],
        strategy: FallbackStrategy
    ) -> Optional[DataPoint]:
        """
        Select best result from multiple results
        
        Args:
            results: List of DataPoint results
            strategy: Strategy for selection
        
        Returns:
            Best DataPoint or None
        """
        if not results:
            return None
        
        if strategy == FallbackStrategy.FAIL_FAST:
            return results[0]
        
        elif strategy == FallbackStrategy.BEST_EFFORT:
            # Return highest confidence
            return max(results, key=lambda dp: dp.confidence)
        
        elif strategy == FallbackStrategy.CONSENSUS:
            # Check if results agree within threshold
            values = [float(dp.value) for dp in results]
            avg_value = sum(values) / len(values)
            
            # Keep results within 1% of average
            consensus_results = [
                dp for dp in results
                if abs(float(dp.value) - avg_value) / avg_value < 0.01
            ]
            
            if consensus_results:
                # Return highest confidence from consensus
                return max(consensus_results, key=lambda dp: dp.confidence)
            else:
                return None
        
        else:
            return results[0]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fallback statistics"""
        total = max(self.total_requests, 1)
        
        stats = {
            'total_requests': self.total_requests,
            'total_fallbacks': self.total_fallbacks,
            'total_failures': self.total_failures,
            'success_rate': round((self.total_requests - self.total_failures) / total, 4),
            'failure_rate': round(self.total_failures / total, 4),
            'layer_usage': {}
        }
        
        for layer in [1, 2, 3, 4]:
            attempts = self.layer_attempts.get(layer, 0)
            successes = self.layer_successes.get(layer, 0)
            stats['layer_usage'][f'layer_{layer}'] = {
                'attempts': attempts,
                'successes': successes,
                'success_rate': round(successes / attempts, 4) if attempts > 0 else 0.0
            }
        
        return stats
    
    def print_statistics(self):
        """Print fallback statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*80)
        print("  FALLBACK COORDINATOR STATISTICS")
        print("="*80)
        print(f"Total Requests:    {stats['total_requests']}")
        print(f"Total Fallbacks:   {stats['total_fallbacks']}")
        print(f"Total Failures:    {stats['total_failures']}")
        print(f"Success Rate:      {stats['success_rate']*100:.1f}%")
        print(f"\nLayer Usage:")
        for layer in [1, 2, 3, 4]:
            layer_stats = stats['layer_usage'][f'layer_{layer}']
            print(f"  Layer {layer}: {layer_stats['successes']}/{layer_stats['attempts']} "
                  f"({layer_stats['success_rate']*100:.1f}% success)")
        print("="*80 + "\n")


if __name__ == "__main__":
    # Example usage
    async def example_sdk_fetcher(**kwargs):
        """Example Layer 1 SDK fetcher"""
        await asyncio.sleep(0.1)
        return {'value': 1850.00}
    
    async def example_rpc_fetcher(**kwargs):
        """Example Layer 2 RPC fetcher"""
        await asyncio.sleep(0.1)
        return {'value': 1851.00}
    
    async def example_cache_fetcher(**kwargs):
        """Example Layer 3 cache fetcher"""
        return {'value': 1849.00}
    
    async def example_fallback_fetcher(**kwargs):
        """Example Layer 4 fallback fetcher"""
        return {'value': 1850.00}
    
    async def main():
        coordinator = FallbackCoordinator(require_oracle_verification=False)
        
        # Register fetchers
        coordinator.register_layer_1_fetcher(example_sdk_fetcher)
        coordinator.register_layer_2_fetcher(example_rpc_fetcher)
        coordinator.register_layer_3_fetcher(example_cache_fetcher)
        coordinator.register_layer_4_fetcher(example_fallback_fetcher)
        
        # Fetch with fallback
        result = await coordinator.fetch_with_fallback(
            data_type="price",
            chain="polygon",
            token="WETH"
        )
        
        if result:
            print(f"\n✓ Fetched price: ${result.value}")
            print(f"  Source: {result.source.value}")
            print(f"  Layer: {result.layer}")
            print(f"  Confidence: {result.confidence:.2f}")
        
        # Print statistics
        coordinator.print_statistics()
    
    asyncio.run(main())
