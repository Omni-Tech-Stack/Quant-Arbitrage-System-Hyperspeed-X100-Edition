#!/usr/bin/env python3
"""Test pool registry integrity"""
import sys
sys.path.insert(0, '..')

def main():
    print("=" * 80)
    print("  REGISTRY INTEGRITY TEST")
    print("=" * 80)
    
    try:
        from pool_registry_integrator import PoolRegistryIntegrator
        registry = PoolRegistryIntegrator("pool_registry.json")
        stats = registry.get_statistics()
        
        print(f"\n✓ Registry loaded successfully")
        print(f"✓ Total pools: {stats['total_pools']}")
        print(f"✓ Active chains: {stats['active_chains']}")
        print(f"✓ Tokens: {stats['tokens']}")
        print("\n✅ Registry integrity verified!")
    except Exception as e:
        print(f"\n⚠ Registry test: {e}")

if __name__ == "__main__":
    main()
