#!/usr/bin/env python3
"""
Liquidity Provider Failover System
Handles graceful degradation when primary liquidity providers experience issues
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

class ProviderStatus(Enum):
    """Liquidity provider status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"

class ProviderType(Enum):
    """Types of liquidity providers"""
    FLASHLOAN = "flashloan"  # Aave, dYdX, Compound
    DEX = "dex"  # Uniswap, SushiSwap, Curve
    LENDING = "lending"  # Lending protocols

@dataclass
class ProviderConfig:
    """Configuration for a liquidity provider"""
    name: str
    provider_type: ProviderType
    priority: int  # 1 = highest priority
    contract_address: str
    max_loan_size_usd: float
    fee_percent: float
    avg_gas_cost: int
    check_endpoint: Optional[str] = None

class LiquidityProviderFailover:
    """
    Manages failover between liquidity providers
    Implements health checks and automatic failover
    """
    
    def __init__(self):
        # Provider configurations
        self.providers = self._initialize_providers()
        
        # Health status tracking
        self.provider_health = {
            name: {
                "status": ProviderStatus.HEALTHY,
                "last_check": 0,
                "consecutive_failures": 0,
                "success_count": 0,
                "failure_count": 0,
                "avg_response_time_ms": 0,
                "last_error": None
            }
            for name in self.providers.keys()
        }
        
        # Health check configuration
        self.health_check_interval = 60  # seconds
        self.failure_threshold = 3  # consecutive failures to mark unhealthy
        self.recovery_threshold = 5  # consecutive successes to mark healthy
        
        # Fallback strategy
        self.enable_fallback = True
        self.enable_graceful_degradation = True
        
        logger.info("LiquidityProviderFailover initialized")
    
    def _initialize_providers(self) -> Dict[str, ProviderConfig]:
        """Initialize liquidity provider configurations"""
        return {
            # Flashloan Providers
            "aave": ProviderConfig(
                name="aave",
                provider_type=ProviderType.FLASHLOAN,
                priority=1,
                contract_address="0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
                max_loan_size_usd=10_000_000,
                fee_percent=0.09,  # 0.09%
                avg_gas_cost=250_000
            ),
            "dydx": ProviderConfig(
                name="dydx",
                provider_type=ProviderType.FLASHLOAN,
                priority=2,
                contract_address="0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e",
                max_loan_size_usd=5_000_000,
                fee_percent=0.0,  # No fee
                avg_gas_cost=300_000
            ),
            "compound": ProviderConfig(
                name="compound",
                provider_type=ProviderType.FLASHLOAN,
                priority=3,
                contract_address="0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",
                max_loan_size_usd=3_000_000,
                fee_percent=0.08,
                avg_gas_cost=280_000
            ),
            
            # DEX Fallbacks
            "uniswap_v3": ProviderConfig(
                name="uniswap_v3",
                provider_type=ProviderType.DEX,
                priority=4,
                contract_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
                max_loan_size_usd=2_000_000,
                fee_percent=0.05,  # Via flashswap
                avg_gas_cost=200_000
            ),
            "balancer": ProviderConfig(
                name="balancer",
                provider_type=ProviderType.DEX,
                priority=5,
                contract_address="0xBA12222222228d8Ba445958a75a0704d566BF2C8",
                max_loan_size_usd=1_000_000,
                fee_percent=0.0,  # Balancer flash loans are free
                avg_gas_cost=220_000
            )
        }
    
    def get_best_provider(
        self,
        amount_usd: float,
        provider_type: Optional[ProviderType] = None
    ) -> Tuple[Optional[str], Optional[ProviderConfig]]:
        """
        Get the best available provider for a given amount
        
        Args:
            amount_usd: Loan amount in USD
            provider_type: Optional filter by provider type
            
        Returns:
            tuple: (provider_name, provider_config) or (None, None) if none available
        """
        # Filter providers
        candidates = []
        
        for name, config in self.providers.items():
            # Skip if wrong type
            if provider_type and config.provider_type != provider_type:
                continue
            
            # Skip if amount too large
            if amount_usd > config.max_loan_size_usd:
                continue
            
            # Skip if unhealthy or offline
            health = self.provider_health[name]
            if health["status"] in [ProviderStatus.OFFLINE, ProviderStatus.UNHEALTHY]:
                continue
            
            # Calculate score
            score = self._calculate_provider_score(name, config, health)
            candidates.append((score, name, config))
        
        if not candidates:
            logger.warning(f"No healthy providers found for amount ${amount_usd:,.2f}")
            
            # Try fallback providers if enabled
            if self.enable_fallback:
                return self._get_fallback_provider(amount_usd, provider_type)
            
            return None, None
        
        # Sort by score (highest first)
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        best_provider = candidates[0]
        logger.info(f"Selected provider: {best_provider[1]} (score: {best_provider[0]:.2f})")
        
        return best_provider[1], best_provider[2]
    
    def _calculate_provider_score(
        self,
        name: str,
        config: ProviderConfig,
        health: Dict
    ) -> float:
        """
        Calculate provider score based on multiple factors
        
        Higher score = better provider
        """
        score = 0.0
        
        # Priority (higher priority = higher score)
        priority_score = (10 - config.priority) * 10
        score += priority_score
        
        # Health status
        if health["status"] == ProviderStatus.HEALTHY:
            score += 50
        elif health["status"] == ProviderStatus.DEGRADED:
            score += 20
        
        # Success rate
        total_attempts = health["success_count"] + health["failure_count"]
        if total_attempts > 0:
            success_rate = health["success_count"] / total_attempts
            score += success_rate * 30
        
        # Lower fees = higher score
        fee_score = max(0, (1.0 - config.fee_percent) * 10)
        score += fee_score
        
        # Lower gas cost = higher score
        gas_score = max(0, (500_000 - config.avg_gas_cost) / 10_000)
        score += gas_score
        
        # Response time (lower = better)
        if health["avg_response_time_ms"] > 0:
            response_score = max(0, (1000 - health["avg_response_time_ms"]) / 100)
            score += response_score
        
        return score
    
    def _get_fallback_provider(
        self,
        amount_usd: float,
        provider_type: Optional[ProviderType]
    ) -> Tuple[Optional[str], Optional[ProviderConfig]]:
        """
        Get fallback provider even if health status is degraded
        """
        logger.warning("Attempting fallback provider selection...")
        
        candidates = []
        
        for name, config in self.providers.items():
            if provider_type and config.provider_type != provider_type:
                continue
            
            if amount_usd > config.max_loan_size_usd:
                continue
            
            # Allow degraded providers in fallback
            health = self.provider_health[name]
            if health["status"] == ProviderStatus.OFFLINE:
                continue
            
            score = self._calculate_provider_score(name, config, health)
            candidates.append((score, name, config))
        
        if not candidates:
            logger.error("No fallback providers available")
            return None, None
        
        candidates.sort(reverse=True, key=lambda x: x[0])
        fallback = candidates[0]
        
        logger.warning(f"Using fallback provider: {fallback[1]} (degraded)")
        return fallback[1], fallback[2]
    
    def record_provider_result(
        self,
        provider_name: str,
        success: bool,
        response_time_ms: float,
        error: Optional[str] = None
    ):
        """
        Record result of provider interaction
        
        Args:
            provider_name: Name of provider
            success: Whether operation was successful
            response_time_ms: Response time in milliseconds
            error: Error message if failed
        """
        if provider_name not in self.provider_health:
            logger.warning(f"Unknown provider: {provider_name}")
            return
        
        health = self.provider_health[provider_name]
        
        # Update counts
        if success:
            health["success_count"] += 1
            health["consecutive_failures"] = 0
        else:
            health["failure_count"] += 1
            health["consecutive_failures"] += 1
            health["last_error"] = error
        
        # Update response time (exponential moving average)
        alpha = 0.3
        if health["avg_response_time_ms"] == 0:
            health["avg_response_time_ms"] = response_time_ms
        else:
            health["avg_response_time_ms"] = (
                alpha * response_time_ms +
                (1 - alpha) * health["avg_response_time_ms"]
            )
        
        # Update status based on consecutive failures/successes
        if success:
            if health["status"] == ProviderStatus.UNHEALTHY:
                # Need multiple successes to recover
                if health["success_count"] >= self.recovery_threshold:
                    health["status"] = ProviderStatus.HEALTHY
                    logger.info(f"Provider {provider_name} recovered to HEALTHY")
        else:
            if health["consecutive_failures"] >= self.failure_threshold:
                old_status = health["status"]
                health["status"] = ProviderStatus.UNHEALTHY
                if old_status != ProviderStatus.UNHEALTHY:
                    logger.warning(
                        f"Provider {provider_name} marked UNHEALTHY "
                        f"after {health['consecutive_failures']} consecutive failures"
                    )
        
        health["last_check"] = time.time()
    
    def check_provider_health(self, provider_name: str) -> bool:
        """
        Perform health check on a specific provider
        
        Returns:
            bool: True if healthy, False otherwise
        """
        if provider_name not in self.providers:
            return False
        
        config = self.providers[provider_name]
        health = self.provider_health[provider_name]
        
        try:
            # In production, would check:
            # 1. Contract is callable
            # 2. Liquidity is available
            # 3. Response time is acceptable
            
            # For now, simulate health check
            start_time = time.time()
            
            # Check if provider has been failing recently
            if health["consecutive_failures"] >= self.failure_threshold:
                return False
            
            response_time = (time.time() - start_time) * 1000
            
            self.record_provider_result(
                provider_name,
                success=True,
                response_time_ms=response_time
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed for {provider_name}: {e}")
            self.record_provider_result(
                provider_name,
                success=False,
                response_time_ms=0,
                error=str(e)
            )
            return False
    
    def check_all_providers(self):
        """Perform health check on all providers"""
        logger.info("Running health checks on all providers...")
        
        for provider_name in self.providers.keys():
            self.check_provider_health(provider_name)
    
    def get_provider_status(self) -> Dict:
        """
        Get current status of all providers
        
        Returns:
            dict: Status information for all providers
        """
        status = {}
        
        for name, config in self.providers.items():
            health = self.provider_health[name]
            total_attempts = health["success_count"] + health["failure_count"]
            success_rate = (
                health["success_count"] / total_attempts if total_attempts > 0 else 0
            )
            
            status[name] = {
                "type": config.provider_type.value,
                "priority": config.priority,
                "status": health["status"].value,
                "success_rate": f"{success_rate*100:.1f}%",
                "consecutive_failures": health["consecutive_failures"],
                "avg_response_time_ms": f"{health['avg_response_time_ms']:.1f}",
                "max_loan_usd": config.max_loan_size_usd,
                "fee_percent": config.fee_percent,
                "last_error": health["last_error"]
            }
        
        return status
    
    def get_failover_recommendations(self, amount_usd: float) -> List[str]:
        """
        Get list of recommended providers in order of preference
        
        Args:
            amount_usd: Loan amount in USD
            
        Returns:
            list: Ordered list of provider names
        """
        candidates = []
        
        for name, config in self.providers.items():
            if amount_usd > config.max_loan_size_usd:
                continue
            
            health = self.provider_health[name]
            if health["status"] == ProviderStatus.OFFLINE:
                continue
            
            score = self._calculate_provider_score(name, config, health)
            candidates.append((score, name))
        
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        return [name for _, name in candidates]
    
    def enable_graceful_degradation(self, enable: bool = True):
        """Enable or disable graceful degradation mode"""
        self.enable_graceful_degradation = enable
        logger.info(f"Graceful degradation: {'enabled' if enable else 'disabled'}")
    
    def mark_provider_offline(self, provider_name: str, reason: str):
        """Manually mark a provider as offline"""
        if provider_name in self.provider_health:
            self.provider_health[provider_name]["status"] = ProviderStatus.OFFLINE
            self.provider_health[provider_name]["last_error"] = reason
            logger.warning(f"Provider {provider_name} manually marked OFFLINE: {reason}")
    
    def mark_provider_online(self, provider_name: str):
        """Manually mark a provider as online"""
        if provider_name in self.provider_health:
            self.provider_health[provider_name]["status"] = ProviderStatus.HEALTHY
            self.provider_health[provider_name]["consecutive_failures"] = 0
            logger.info(f"Provider {provider_name} manually marked ONLINE")

# Global failover instance
_global_failover = None

def get_failover():
    """Get global failover instance"""
    global _global_failover
    if _global_failover is None:
        _global_failover = LiquidityProviderFailover()
    return _global_failover

if __name__ == "__main__":
    import json
    
    # Test failover system
    print("Testing Liquidity Provider Failover System\n")
    print("=" * 80)
    
    failover = LiquidityProviderFailover()
    
    # Test 1: Get best provider for normal amount
    print("\nTest 1: Get best provider for $50,000 loan")
    provider_name, provider_config = failover.get_best_provider(50_000)
    if provider_config:
        print(f"  Selected: {provider_name}")
        print(f"  Fee: {provider_config.fee_percent}%")
        print(f"  Max Loan: ${provider_config.max_loan_size_usd:,.0f}")
    
    # Test 2: Simulate some failures
    print("\nTest 2: Simulate Aave failures")
    for i in range(5):
        failover.record_provider_result(
            "aave",
            success=False,
            response_time_ms=1000,
            error="Connection timeout"
        )
    
    # Test 3: Get provider after failures (should failover)
    print("\nTest 3: Get provider after Aave failures")
    provider_name, provider_config = failover.get_best_provider(50_000)
    if provider_config:
        print(f"  Selected: {provider_name} (failover)")
        print(f"  Fee: {provider_config.fee_percent}%")
    
    # Test 4: Get status
    print("\nTest 4: Provider Status")
    print("=" * 80)
    status = failover.get_provider_status()
    print(json.dumps(status, indent=2))
    
    # Test 5: Recommendations
    print("\nTest 5: Failover Recommendations for $100,000")
    recommendations = failover.get_failover_recommendations(100_000)
    print(f"  Recommended order: {', '.join(recommendations)}")
    
    print("\n" + "=" * 80)
    print("Failover system test complete")
