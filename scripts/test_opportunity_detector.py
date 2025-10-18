#!/usr/bin/env python3
"""Test opportunity detector"""
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 80)
    print("  OPPORTUNITY DETECTOR TEST")
    print("=" * 80)
    
    try:
        from pool_registry_integrator import PoolRegistryIntegrator
        from advanced_opportunity_detection_Version1 import OpportunityDetector
        
        registry = PoolRegistryIntegrator("pool_registry.json", "token_equivalence.json")
        detector = OpportunityDetector(registry)
        
        print("\n✓ Detector initialized")
        print("✓ Scanning for opportunities...")
        
        opportunities = detector.detect_opportunities()
        print(f"✓ Found {len(opportunities)} opportunities")
        
        if opportunities:
            print(f"\nSample opportunity:")
            opp = opportunities[0]
            print(f"  - Estimated Profit: ${opp['estimated_profit']:.2f}")
            print(f"  - ML Score: {opp['ml_score']:.2f}")
            print(f"  - Hops: {opp['hops']}")
        
        print("\n✅ Detector test passed!")
        return 0
    except Exception as e:
        print(f"\n⚠ Detector test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

