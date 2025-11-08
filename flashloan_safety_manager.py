#!/usr/bin/env python
"""
Flashloan Safety Manager
Enforces minimum/maximum flashloan limits based on real-time pool TVL
Maintains 240-minute snapshots per pool/vault to prevent over-borrowing
"""

import time
import json
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


class FlashloanSafetyManager:
    """
    Manages flashloan safety limits with TVL-based constraints
    
    Rules:
    - MIN_FLASHLOAN_USD: Minimum flashloan size ($50,000 default)
    - MAX_FLASHLOAN_PERCENT_TVL: Maximum % of pool TVL (15% default)
    - Snapshot refresh: Every 240 minutes per pool/vault
    - Explicit tracking: Separate variables for each pool/token
    """
    
    def __init__(
        self,
        min_flashloan_usd: float = 50000.0,
        max_flashloan_percent_tvl: float = 15.0,
        snapshot_refresh_minutes: int = 240,
        snapshot_file: str = "flashloan_snapshots.json"
    ):
        # Core safety limits
        self.MIN_FLASHLOAN_USD = min_flashloan_usd
        self.MAX_FLASHLOAN_PERCENT_TVL = max_flashloan_percent_tvl
        self.SNAPSHOT_REFRESH_MINUTES = snapshot_refresh_minutes
        self.SNAPSHOT_REFRESH_SECONDS = snapshot_refresh_minutes * 60
        
        # Snapshot storage
        self.snapshot_file = snapshot_file
        self.pool_snapshots = {}  # {pool_id: {token: {tvl, timestamp, ...}}}
        self.vault_snapshots = {}  # {vault_id: {token: {tvl, timestamp, ...}}}
        
        # Explicit tracking variables (separate storage)
        self.current_pool_tvl = {}  # {pool_id: {token: tvl_usd}}
        self.current_vault_tvl = {}  # {vault_id: {token: tvl_usd}}
        self.last_snapshot_time = {}  # {pool_id: timestamp}
        self.flashloan_limits = {}  # {pool_id: {token: max_amount_usd}}
        self.active_flashloans = {}  # {tx_id: {pool_id, token, amount, timestamp}}
        
        # Token price cache (for USD conversions)
        self.token_prices_usd = {}  # {token_address: price_usd}
        
        # Statistics
        self.total_flashloans_approved = 0
        self.total_flashloans_rejected = 0
        self.rejection_reasons = {}
        
        # Load existing snapshots
        self._load_snapshots()
        
        print(f"[FlashloanSafety] ✓ Initialized")
        print(f"  - MIN_FLASHLOAN_USD: ${self.MIN_FLASHLOAN_USD:,.2f}")
        print(f"  - MAX_FLASHLOAN_PERCENT_TVL: {self.MAX_FLASHLOAN_PERCENT_TVL}%")
        print(f"  - Snapshot Refresh: {self.SNAPSHOT_REFRESH_MINUTES} minutes")
    
    def _load_snapshots(self):
        """Load existing snapshots from disk"""
        try:
            if os.path.exists(self.snapshot_file):
                with open(self.snapshot_file, 'r') as f:
                    data = json.load(f)
                    self.pool_snapshots = data.get('pools', {})
                    self.vault_snapshots = data.get('vaults', {})
                    self.last_snapshot_time = data.get('last_snapshot_time', {})
                print(f"[FlashloanSafety] ✓ Loaded snapshots: {len(self.pool_snapshots)} pools, {len(self.vault_snapshots)} vaults")
        except Exception as e:
            print(f"[FlashloanSafety] ⚠ Could not load snapshots: {e}")
    
    def _save_snapshots(self):
        """Save snapshots to disk"""
        try:
            data = {
                'pools': self.pool_snapshots,
                'vaults': self.vault_snapshots,
                'last_snapshot_time': self.last_snapshot_time,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.snapshot_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[FlashloanSafety] ⚠ Could not save snapshots: {e}")
    
    def update_pool_tvl(
        self,
        pool_id: str,
        token_address: str,
        token_symbol: str,
        token_reserve: float,
        token_price_usd: float,
        pool_type: str = "pool"  # "pool" or "vault"
    ):
        """
        Update TVL for a specific pool/vault and token
        
        Args:
            pool_id: Unique pool/vault identifier
            token_address: Token contract address
            token_symbol: Token symbol (e.g., USDC, WETH)
            token_reserve: Token reserve in the pool (in token units)
            token_price_usd: Current token price in USD
            pool_type: "pool" or "vault"
        """
        # Calculate TVL in USD
        tvl_usd = token_reserve * token_price_usd
        
        # Store in appropriate structure
        if pool_type == "vault":
            if pool_id not in self.current_vault_tvl:
                self.current_vault_tvl[pool_id] = {}
            self.current_vault_tvl[pool_id][token_address] = tvl_usd
        else:
            if pool_id not in self.current_pool_tvl:
                self.current_pool_tvl[pool_id] = {}
            self.current_pool_tvl[pool_id][token_address] = tvl_usd
        
        # Update token price cache
        self.token_prices_usd[token_address] = token_price_usd
        
        # Check if snapshot needs refresh
        current_time = time.time()
        last_snapshot = self.last_snapshot_time.get(pool_id, 0)
        
        if current_time - last_snapshot >= self.SNAPSHOT_REFRESH_SECONDS:
            self._create_snapshot(pool_id, token_address, token_symbol, tvl_usd, pool_type)
            self.last_snapshot_time[pool_id] = current_time
    
    def _create_snapshot(
        self,
        pool_id: str,
        token_address: str,
        token_symbol: str,
        tvl_usd: float,
        pool_type: str
    ):
        """Create a 240-minute snapshot for a pool/token"""
        snapshot_data = {
            'token_address': token_address,
            'token_symbol': token_symbol,
            'tvl_usd': tvl_usd,
            'max_flashloan_usd': tvl_usd * (self.MAX_FLASHLOAN_PERCENT_TVL / 100),
            'timestamp': time.time(),
            'timestamp_human': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=self.SNAPSHOT_REFRESH_MINUTES)).isoformat()
        }
        
        # Store in appropriate snapshot dictionary
        if pool_type == "vault":
            if pool_id not in self.vault_snapshots:
                self.vault_snapshots[pool_id] = {}
            self.vault_snapshots[pool_id][token_address] = snapshot_data
        else:
            if pool_id not in self.pool_snapshots:
                self.pool_snapshots[pool_id] = {}
            self.pool_snapshots[pool_id][token_address] = snapshot_data
        
        # Calculate and store flashloan limit
        if pool_id not in self.flashloan_limits:
            self.flashloan_limits[pool_id] = {}
        self.flashloan_limits[pool_id][token_address] = snapshot_data['max_flashloan_usd']
        
        # Save to disk
        self._save_snapshots()
        
        print(f"[FlashloanSafety] 📸 Snapshot created: {pool_id}/{token_symbol}")
        print(f"  TVL: ${tvl_usd:,.2f} | Max Flashloan: ${snapshot_data['max_flashloan_usd']:,.2f}")
    
    def validate_flashloan(
        self,
        pool_id: str,
        token_address: str,
        flashloan_amount_tokens: float,
        pool_type: str = "pool"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate if a flashloan request meets safety requirements
        
        Args:
            pool_id: Pool/vault ID
            token_address: Token to borrow
            flashloan_amount_tokens: Amount to borrow (in token units)
            pool_type: "pool" or "vault"
        
        Returns:
            (approved, reason, details)
            - approved: bool (True if flashloan is safe)
            - reason: str (explanation)
            - details: dict (validation details)
        """
        # Get token price
        token_price_usd = self.token_prices_usd.get(token_address, 0)
        if token_price_usd == 0:
            self.total_flashloans_rejected += 1
            self._record_rejection("no_price_data")
            return False, "No price data for token", {}
        
        # Calculate flashloan size in USD
        flashloan_usd = flashloan_amount_tokens * token_price_usd
        
        # Check minimum flashloan size
        if flashloan_usd < self.MIN_FLASHLOAN_USD:
            self.total_flashloans_rejected += 1
            self._record_rejection("below_minimum")
            return False, f"Below minimum ${self.MIN_FLASHLOAN_USD:,.2f} (requested: ${flashloan_usd:,.2f})", {
                'flashloan_usd': flashloan_usd,
                'min_required': self.MIN_FLASHLOAN_USD
            }
        
        # Get current TVL
        tvl_dict = self.current_vault_tvl if pool_type == "vault" else self.current_pool_tvl
        if pool_id not in tvl_dict or token_address not in tvl_dict[pool_id]:
            self.total_flashloans_rejected += 1
            self._record_rejection("no_tvl_data")
            return False, "No TVL data for pool/token", {}
        
        pool_tvl_usd = tvl_dict[pool_id][token_address]
        
        # Calculate percentage of TVL
        percent_of_tvl = (flashloan_usd / pool_tvl_usd * 100) if pool_tvl_usd > 0 else 0
        
        # Check maximum TVL percentage
        if percent_of_tvl > self.MAX_FLASHLOAN_PERCENT_TVL:
            self.total_flashloans_rejected += 1
            self._record_rejection("exceeds_tvl_limit")
            return False, f"Exceeds {self.MAX_FLASHLOAN_PERCENT_TVL}% TVL limit ({percent_of_tvl:.1f}%)", {
                'flashloan_usd': flashloan_usd,
                'pool_tvl_usd': pool_tvl_usd,
                'percent_of_tvl': percent_of_tvl,
                'max_allowed_percent': self.MAX_FLASHLOAN_PERCENT_TVL
            }
        
        # Check snapshot exists and is not expired
        snapshot_dict = self.vault_snapshots if pool_type == "vault" else self.pool_snapshots
        if pool_id in snapshot_dict and token_address in snapshot_dict[pool_id]:
            snapshot = snapshot_dict[pool_id][token_address]
            snapshot_age = time.time() - snapshot['timestamp']
            
            if snapshot_age > self.SNAPSHOT_REFRESH_SECONDS:
                print(f"[FlashloanSafety] ⚠ Snapshot expired for {pool_id}/{token_address} (age: {snapshot_age/60:.1f}min)")
        
        # Approved!
        self.total_flashloans_approved += 1
        
        details = {
            'flashloan_amount_tokens': flashloan_amount_tokens,
            'flashloan_usd': flashloan_usd,
            'token_price_usd': token_price_usd,
            'pool_tvl_usd': pool_tvl_usd,
            'percent_of_tvl': percent_of_tvl,
            'max_allowed_percent': self.MAX_FLASHLOAN_PERCENT_TVL,
            'min_flashloan_usd': self.MIN_FLASHLOAN_USD,
            'pool_type': pool_type,
            'validated_at': datetime.now().isoformat()
        }
        
        return True, "Flashloan approved", details
    
    def _record_rejection(self, reason: str):
        """Record rejection reason for statistics"""
        if reason not in self.rejection_reasons:
            self.rejection_reasons[reason] = 0
        self.rejection_reasons[reason] += 1
    
    def register_active_flashloan(
        self,
        tx_id: str,
        pool_id: str,
        token_address: str,
        amount_tokens: float
    ):
        """Register an active flashloan for tracking"""
        self.active_flashloans[tx_id] = {
            'pool_id': pool_id,
            'token_address': token_address,
            'amount_tokens': amount_tokens,
            'timestamp': time.time(),
            'timestamp_human': datetime.now().isoformat()
        }
    
    def complete_flashloan(self, tx_id: str):
        """Mark flashloan as completed"""
        if tx_id in self.active_flashloans:
            del self.active_flashloans[tx_id]
    
    def get_max_flashloan_for_pool(
        self,
        pool_id: str,
        token_address: str,
        pool_type: str = "pool"
    ) -> float:
        """Get maximum flashloan size in USD for a pool/token"""
        tvl_dict = self.current_vault_tvl if pool_type == "vault" else self.current_pool_tvl
        
        if pool_id not in tvl_dict or token_address not in tvl_dict[pool_id]:
            return 0.0
        
        pool_tvl_usd = tvl_dict[pool_id][token_address]
        max_flashloan_usd = pool_tvl_usd * (self.MAX_FLASHLOAN_PERCENT_TVL / 100)
        
        return max(max_flashloan_usd, self.MIN_FLASHLOAN_USD)
    
    def print_statistics(self):
        """Print comprehensive statistics"""
        print("\n" + "=" * 80)
        print("  FLASHLOAN SAFETY MANAGER STATISTICS")
        print("=" * 80)
        print(f"  Total Approved: {self.total_flashloans_approved}")
        print(f"  Total Rejected: {self.total_flashloans_rejected}")
        
        if self.total_flashloans_approved + self.total_flashloans_rejected > 0:
            approval_rate = self.total_flashloans_approved / (self.total_flashloans_approved + self.total_flashloans_rejected) * 100
            print(f"  Approval Rate: {approval_rate:.1f}%")
        
        if self.rejection_reasons:
            print(f"\n  Rejection Reasons:")
            for reason, count in self.rejection_reasons.items():
                print(f"    - {reason}: {count}")
        
        print(f"\n  Active Flashloans: {len(self.active_flashloans)}")
        print(f"  Pool Snapshots: {len(self.pool_snapshots)}")
        print(f"  Vault Snapshots: {len(self.vault_snapshots)}")
        print("=" * 80 + "\n")
    
    def get_snapshot_info(self, pool_id: str, token_address: str, pool_type: str = "pool") -> Optional[Dict]:
        """Get snapshot information for a pool/token"""
        snapshot_dict = self.vault_snapshots if pool_type == "vault" else self.pool_snapshots
        
        if pool_id in snapshot_dict and token_address in snapshot_dict[pool_id]:
            return snapshot_dict[pool_id][token_address]
        
        return None


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = FlashloanSafetyManager(
        min_flashloan_usd=50000.0,
        max_flashloan_percent_tvl=15.0,
        snapshot_refresh_minutes=240
    )
    
    # Example: Update pool TVL
    # USDC pool on Uniswap V3
    manager.update_pool_tvl(
        pool_id="uniswap_v3_usdc_weth_0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        token_address="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC
        token_symbol="USDC",
        token_reserve=5000000.0,  # 5M USDC
        token_price_usd=1.0,
        pool_type="pool"
    )
    
    # Example: Validate flashloan
    approved, reason, details = manager.validate_flashloan(
        pool_id="uniswap_v3_usdc_weth_0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        token_address="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        flashloan_amount_tokens=500000.0,  # 500K USDC
        pool_type="pool"
    )
    
    print(f"\nFlashloan Validation Result:")
    print(f"  Approved: {approved}")
    print(f"  Reason: {reason}")
    if details:
        print(f"  Details: {json.dumps(details, indent=2)}")
    
    # Print statistics
    manager.print_statistics()
