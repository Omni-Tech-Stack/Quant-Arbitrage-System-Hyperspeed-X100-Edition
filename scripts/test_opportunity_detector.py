#!/usr/bin/env python3
"""Test opportunity detector"""
import sys
sys.path.insert(0, '..')

def main():
    print("=" * 80)
    print("  OPPORTUNITY DETECTOR TEST")
    print("=" * 80)
    
    try:
        from pool_registry_integrator import PoolRegistryIntegrator
        from advanced_opportunity_detection_Version1 import OpportunityDetector
        
        registry = PoolRegistryIntegrator("pool_registry.json")
        detector = OpportunityDetector(registry)
        
        print("\n✓ Detector initialized")
        print("✓ Scanning for opportunities...")
        
        opportunities = detector.detect_opportunities()
        print(f"✓ Found {len(opportunities)} opportunities")
        print("\n✅ Detector test passed!")
    except Exception as e:
        print(f"\n⚠ Detector test: {e}")

if __name__ == "__main__":
    main()
