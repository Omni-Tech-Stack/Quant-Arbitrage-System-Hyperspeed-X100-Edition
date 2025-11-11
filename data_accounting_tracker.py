#!/usr/bin/env python3
"""
DATA ACCOUNTING TRACKER
Tracks all data points with full provenance, validation status, and staleness
Ensures 100% data attribution before execution
"""

import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Data validation status"""
    UNVALIDATED = "unvalidated"
    VALIDATED = "validated"
    FLAGGED = "flagged"
    REJECTED = "rejected"


class DataSource(Enum):
    """Data source types"""
    # Layer 1: Primary SDK Sources
    UNISWAP_SDK = "uniswap_sdk"
    BALANCER_SDK = "balancer_sdk"
    CURVE_SDK = "curve_sdk"
    DIRECT_CONTRACT = "direct_contract"
    SUBGRAPH = "subgraph"
    
    # Layer 2: RPC Endpoints
    ALCHEMY_RPC = "alchemy_rpc"
    INFURA_RPC = "infura_rpc"
    QUICKNODE_RPC = "quicknode_rpc"
    PUBLIC_RPC = "public_rpc"
    
    # Layer 3: Aggregated/Cached
    LOCAL_CACHE = "local_cache"
    AGGREGATED = "aggregated"
    HISTORICAL_BASELINE = "historical_baseline"
    
    # Layer 4: Emergency Fallbacks
    LAST_KNOWN_GOOD = "last_known_good"
    CONSERVATIVE_ESTIMATE = "conservative_estimate"
    SAFE_DEFAULT = "safe_default"
    
    # Oracles
    CHAINLINK_ORACLE = "chainlink_oracle"
    UNISWAP_TWAP = "uniswap_twap"
    
    # Unknown
    UNKNOWN = "unknown"


@dataclass
class DataPoint:
    """
    Tracked data point with complete provenance
    Every piece of data used in execution must be a DataPoint
    """
    # Core data
    value: Any
    data_type: str  # "price", "gas", "liquidity", "pool_data"
    
    # Provenance
    source: DataSource
    layer: int  # 1-4 fallback layer
    timestamp: float = field(default_factory=time.time)
    
    # Validation
    validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    oracle_verified: bool = False
    oracle_source: Optional[str] = None
    oracle_deviation: Optional[float] = None  # % deviation from oracle
    
    # Quality metrics
    staleness: float = 0.0  # Seconds since data generation
    confidence: float = 0.0  # 0.0-1.0 calculated confidence score
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tracking
    request_id: Optional[str] = None
    chain: Optional[str] = None
    token: Optional[str] = None
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.staleness = time.time() - self.timestamp
        if self.confidence == 0.0:
            self.confidence = self._calculate_confidence()
    
    def _calculate_confidence(self) -> float:
        """
        Calculate confidence score based on source, freshness, and oracle verification
        
        Returns:
            float: Confidence score 0.0-1.0
        """
        # Source weights based on layer
        source_weights = {
            1: 1.0,   # Layer 1: SDK/Direct
            2: 0.95,  # Layer 2: RPC
            3: 0.85,  # Layer 3: Aggregated
            4: 0.60   # Layer 4: Cached/Fallback
        }
        source_weight = source_weights.get(self.layer, 0.5)
        
        # Freshness weight
        if self.staleness < 5:
            freshness_weight = 1.0
        elif self.staleness < 12:
            freshness_weight = 0.95
        elif self.staleness < 30:
            freshness_weight = 0.85
        elif self.staleness < 60:
            freshness_weight = 0.70
        else:
            freshness_weight = 0.50
        
        # Oracle verification weight
        if self.oracle_verified:
            if self.oracle_deviation is not None and self.oracle_deviation < 0.02:
                oracle_weight = 1.0
            elif self.oracle_deviation is not None and self.oracle_deviation < 0.05:
                oracle_weight = 0.85
            else:
                oracle_weight = 0.50
        else:
            oracle_weight = 0.80  # Not verified
        
        # Combined confidence
        confidence = source_weight * freshness_weight * oracle_weight
        
        return round(confidence, 4)
    
    def update_staleness(self):
        """Update staleness and recalculate confidence"""
        self.staleness = time.time() - self.timestamp
        self.confidence = self._calculate_confidence()
    
    def is_stale(self, max_age_seconds: float) -> bool:
        """Check if data is stale beyond threshold"""
        self.update_staleness()
        return self.staleness > max_age_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['source'] = self.source.value
        data['validation_status'] = self.validation_status.value
        return data


class DataAccountingTracker:
    """
    Tracks all data points used in the system
    Ensures 100% data attribution and accountability
    """
    
    # Staleness limits by data type (seconds)
    STALENESS_LIMITS = {
        'price': 12,      # 1 Polygon block
        'gas': 12,        # 1 block
        'liquidity': 60,  # 5 blocks
        'pool_data': 300, # 25 blocks
        'default': 30
    }
    
    # Minimum confidence by data type
    MIN_CONFIDENCE = {
        'price': 0.85,
        'gas': 0.85,
        'liquidity': 0.80,
        'pool_data': 0.75,
        'default': 0.75
    }
    
    def __init__(self):
        """Initialize data accounting tracker"""
        self.data_points: Dict[str, DataPoint] = {}  # request_id -> DataPoint
        self.unaccounted_data: List[str] = []  # request_ids of unaccounted data
        self.flagged_data: List[str] = []  # request_ids of flagged data
        
        # Statistics
        self.total_tracked = 0
        self.total_validated = 0
        self.total_rejected = 0
        self.total_unaccounted = 0
        
        # Layer usage stats
        self.layer_usage = {1: 0, 2: 0, 3: 0, 4: 0}
        
        logger.info("[DataAccounting] ✓ Initialized Data Accounting Tracker")
    
    def record(self, data_point: DataPoint) -> str:
        """
        Record a data point with full provenance
        
        Args:
            data_point: DataPoint to record
        
        Returns:
            str: Assigned request_id
        """
        # Generate request_id if not provided
        if not data_point.request_id:
            data_point.request_id = f"{data_point.data_type}_{int(time.time()*1000000)}"
        
        # Update staleness and confidence
        data_point.update_staleness()
        
        # Store
        self.data_points[data_point.request_id] = data_point
        
        # Update statistics
        self.total_tracked += 1
        self.layer_usage[data_point.layer] = self.layer_usage.get(data_point.layer, 0) + 1
        
        if data_point.validation_status == ValidationStatus.VALIDATED:
            self.total_validated += 1
        elif data_point.validation_status == ValidationStatus.UNVALIDATED:
            self.unaccounted_data.append(data_point.request_id)
            self.total_unaccounted += 1
        elif data_point.validation_status == ValidationStatus.FLAGGED:
            self.flagged_data.append(data_point.request_id)
        
        logger.debug(f"[DataAccounting] Recorded {data_point.data_type} from {data_point.source.value} "
                    f"(confidence: {data_point.confidence:.2f})")
        
        return data_point.request_id
    
    def validate(self, request_id: str, oracle_verified: bool = False, 
                 oracle_source: Optional[str] = None, 
                 oracle_deviation: Optional[float] = None) -> bool:
        """
        Mark data point as validated
        
        Args:
            request_id: Request ID to validate
            oracle_verified: Whether oracle verification was performed
            oracle_source: Oracle source used
            oracle_deviation: Deviation from oracle (%)
        
        Returns:
            bool: True if validation successful
        """
        if request_id not in self.data_points:
            logger.error(f"[DataAccounting] Cannot validate unknown request_id: {request_id}")
            return False
        
        data_point = self.data_points[request_id]
        
        # Update validation status
        data_point.validation_status = ValidationStatus.VALIDATED
        data_point.oracle_verified = oracle_verified
        data_point.oracle_source = oracle_source
        data_point.oracle_deviation = oracle_deviation
        
        # Recalculate confidence
        data_point.update_staleness()
        
        # Flag if oracle deviation is high
        if oracle_deviation is not None and oracle_deviation > 0.05:
            data_point.validation_status = ValidationStatus.FLAGGED
            if request_id not in self.flagged_data:
                self.flagged_data.append(request_id)
            logger.warning(f"[DataAccounting] Flagged {request_id}: oracle deviation {oracle_deviation*100:.2f}%")
        
        # Remove from unaccounted if present
        if request_id in self.unaccounted_data:
            self.unaccounted_data.remove(request_id)
            self.total_unaccounted -= 1
        
        self.total_validated += 1
        
        logger.debug(f"[DataAccounting] Validated {request_id} "
                    f"(oracle: {oracle_verified}, confidence: {data_point.confidence:.2f})")
        
        return True
    
    def reject(self, request_id: str, reason: str) -> bool:
        """
        Mark data point as rejected
        
        Args:
            request_id: Request ID to reject
            reason: Rejection reason
        
        Returns:
            bool: True if rejection successful
        """
        if request_id not in self.data_points:
            logger.error(f"[DataAccounting] Cannot reject unknown request_id: {request_id}")
            return False
        
        data_point = self.data_points[request_id]
        data_point.validation_status = ValidationStatus.REJECTED
        data_point.metadata['rejection_reason'] = reason
        
        self.total_rejected += 1
        
        logger.info(f"[DataAccounting] Rejected {request_id}: {reason}")
        
        return True
    
    def get_data_point(self, request_id: str) -> Optional[DataPoint]:
        """Get data point by request_id"""
        return self.data_points.get(request_id)
    
    def check_staleness(self, request_id: str) -> bool:
        """
        Check if data point is within staleness limits
        
        Returns:
            bool: True if fresh, False if stale
        """
        data_point = self.get_data_point(request_id)
        if not data_point:
            return False
        
        max_age = self.STALENESS_LIMITS.get(data_point.data_type, 
                                            self.STALENESS_LIMITS['default'])
        
        return not data_point.is_stale(max_age)
    
    def check_confidence(self, request_id: str) -> bool:
        """
        Check if data point meets minimum confidence threshold
        
        Returns:
            bool: True if confidence sufficient
        """
        data_point = self.get_data_point(request_id)
        if not data_point:
            return False
        
        min_conf = self.MIN_CONFIDENCE.get(data_point.data_type,
                                           self.MIN_CONFIDENCE['default'])
        
        return data_point.confidence >= min_conf
    
    def requires_double_validation(self, request_id: str) -> bool:
        """
        Check if data point requires double-validation
        
        Double-validation required for:
        - Unaccounted data
        - Flagged data
        - Stale data
        - Low confidence data
        
        Returns:
            bool: True if double-validation required
        """
        if request_id in self.unaccounted_data:
            return True
        
        if request_id in self.flagged_data:
            return True
        
        data_point = self.get_data_point(request_id)
        if not data_point:
            return True  # Unknown data always requires double-validation
        
        if not self.check_staleness(request_id):
            return True
        
        if not self.check_confidence(request_id):
            return True
        
        return False
    
    def get_unaccounted_data(self) -> List[DataPoint]:
        """Get all unaccounted data points"""
        return [self.data_points[rid] for rid in self.unaccounted_data 
                if rid in self.data_points]
    
    def get_flagged_data(self) -> List[DataPoint]:
        """Get all flagged data points"""
        return [self.data_points[rid] for rid in self.flagged_data 
                if rid in self.data_points]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get accounting statistics"""
        total = max(self.total_tracked, 1)  # Avoid division by zero
        
        return {
            'total_tracked': self.total_tracked,
            'total_validated': self.total_validated,
            'total_rejected': self.total_rejected,
            'total_unaccounted': self.total_unaccounted,
            'validation_rate': round(self.total_validated / total, 4),
            'rejection_rate': round(self.total_rejected / total, 4),
            'unaccounted_rate': round(self.total_unaccounted / total, 4),
            'layer_usage': self.layer_usage,
            'layer_1_pct': round(self.layer_usage.get(1, 0) / total * 100, 2),
            'layer_2_pct': round(self.layer_usage.get(2, 0) / total * 100, 2),
            'layer_3_pct': round(self.layer_usage.get(3, 0) / total * 100, 2),
            'layer_4_pct': round(self.layer_usage.get(4, 0) / total * 100, 2),
            'flagged_count': len(self.flagged_data)
        }
    
    def print_statistics(self):
        """Print accounting statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*80)
        print("  DATA ACCOUNTING STATISTICS")
        print("="*80)
        print(f"Total Tracked:    {stats['total_tracked']}")
        print(f"Validated:        {stats['total_validated']} ({stats['validation_rate']*100:.1f}%)")
        print(f"Rejected:         {stats['total_rejected']} ({stats['rejection_rate']*100:.1f}%)")
        print(f"Unaccounted:      {stats['total_unaccounted']} ({stats['unaccounted_rate']*100:.1f}%)")
        print(f"Flagged:          {stats['flagged_count']}")
        print(f"\nLayer Usage:")
        print(f"  Layer 1 (SDK):        {stats['layer_1_pct']}%")
        print(f"  Layer 2 (RPC):        {stats['layer_2_pct']}%")
        print(f"  Layer 3 (Aggregated): {stats['layer_3_pct']}%")
        print(f"  Layer 4 (Fallback):   {stats['layer_4_pct']}%")
        print("="*80 + "\n")
    
    def export_to_json(self, filepath: str):
        """Export all data points to JSON file"""
        data = {
            'statistics': self.get_statistics(),
            'data_points': [dp.to_dict() for dp in self.data_points.values()],
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"[DataAccounting] Exported {len(self.data_points)} data points to {filepath}")


# Singleton instance
_tracker_instance: Optional[DataAccountingTracker] = None

def get_tracker() -> DataAccountingTracker:
    """Get global data accounting tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = DataAccountingTracker()
    return _tracker_instance


if __name__ == "__main__":
    # Example usage
    tracker = DataAccountingTracker()
    
    # Record some data points
    price_data = DataPoint(
        value=1850.50,
        data_type="price",
        source=DataSource.UNISWAP_SDK,
        layer=1,
        chain="polygon",
        token="WETH",
        metadata={"pair": "WETH/USDC"}
    )
    
    request_id = tracker.record(price_data)
    tracker.validate(request_id, oracle_verified=True, 
                     oracle_source="chainlink", oracle_deviation=0.01)
    
    # Simulate some more data
    for i in range(10):
        data = DataPoint(
            value=100 + i,
            data_type="gas",
            source=DataSource.ALCHEMY_RPC if i % 2 == 0 else DataSource.INFURA_RPC,
            layer=2,
            chain="polygon"
        )
        rid = tracker.record(data)
        if i % 3 == 0:
            tracker.validate(rid)
    
    # Print statistics
    tracker.print_statistics()
