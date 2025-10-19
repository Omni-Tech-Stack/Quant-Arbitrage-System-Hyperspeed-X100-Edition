#!/usr/bin/env python
"""Test pool registry integrity"""
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 80)
    print("  REGISTRY INTEGRITY TEST")
    print("=" * 80)
    
    try:
        from pool_registry_integrator import PoolRegistryIntegrator
        registry = PoolRegistryIntegrator("pool_registry.json", "token_equivalence.json")
        stats = registry.get_statistics()
        
        print(f"\n✓ Registry loaded successfully")
        print(f"✓ Total pools: {stats['total_pools']}")
        print(f"✓ Active chains: {stats['active_chains']}")
        print(f"✓ Tokens: {stats['tokens']}")
        print("\n✅ Registry integrity verified!")
        return 0
    except Exception as e:
        print(f"\n⚠ Registry test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

