#!/usr/bin/env python
"""
Test script for real data fetchers
Validates that all TVL fetchers can successfully retrieve real data
"""

import sys
import asyncio
from uniswapv3_tvl_fetcher import UniswapV3TVLFetcher
from balancer_tvl_fetcher import BalancerTVLFetcher
from src.curve_tvl_fetcher import CurveTVLFetcher


def test_uniswap_v3():
    """Test Uniswap V3 TVL fetcher"""
    print("\n" + "="*80)
    print("Testing Uniswap V3 TVL Fetcher")
    print("="*80)
    
    try:
        fetcher = UniswapV3TVLFetcher(chain="ethereum", min_tvl_usd=1000000)
        data = fetcher.fetch_tvl()
        
        assert 'protocol' in data, "Missing protocol field"
        assert 'chain' in data, "Missing chain field"
        assert 'total_tvl' in data, "Missing total_tvl field"
        assert 'pools' in data, "Missing pools field"
        
        print(f"✓ Protocol: {data['protocol']}")
        print(f"✓ Chain: {data['chain']}")
        print(f"✓ Total TVL: ${data['total_tvl']:,.2f}")
        print(f"✓ Pool count: {len(data['pools'])}")
        
        if data['pools']:
            top_pool = data['pools'][0]
            print(f"\n  Top pool: {top_pool['token0']['symbol']}/{top_pool['token1']['symbol']}")
            print(f"  TVL: ${top_pool['tvl']:,.2f}")
            print(f"  Fee tier: {top_pool['fee_tier']*100}%")
        
        print("\n✅ Uniswap V3 test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Uniswap V3 test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_balancer():
    """Test Balancer TVL fetcher"""
    print("\n" + "="*80)
    print("Testing Balancer TVL Fetcher")
    print("="*80)
    
    try:
        fetcher = BalancerTVLFetcher(chain="ethereum", min_tvl_usd=500000)
        data = fetcher.fetch_tvl()
        
        assert 'protocol' in data, "Missing protocol field"
        assert 'chain' in data, "Missing chain field"
        assert 'total_tvl' in data, "Missing total_tvl field"
        assert 'pools' in data, "Missing pools field"
        
        print(f"✓ Protocol: {data['protocol']}")
        print(f"✓ Chain: {data['chain']}")
        print(f"✓ Total TVL: ${data['total_tvl']:,.2f}")
        print(f"✓ Pool count: {len(data['pools'])}")
        
        if data['pools']:
            top_pool = data['pools'][0]
            token_symbols = [t['symbol'] for t in top_pool['tokens']]
            print(f"\n  Top pool: {'/'.join(token_symbols)}")
            print(f"  TVL: ${top_pool['tvl']:,.2f}")
            print(f"  Pool type: {top_pool['pool_type']}")
        
        print("\n✅ Balancer test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Balancer test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_curve():
    """Test Curve TVL fetcher"""
    print("\n" + "="*80)
    print("Testing Curve TVL Fetcher")
    print("="*80)
    
    try:
        fetcher = CurveTVLFetcher(chain="ethereum", min_tvl_usd=500000)
        data = fetcher.fetch_tvl()
        
        assert 'protocol' in data, "Missing protocol field"
        assert 'chain' in data, "Missing chain field"
        assert 'total_tvl' in data, "Missing total_tvl field"
        assert 'pools' in data, "Missing pools field"
        
        print(f"✓ Protocol: {data['protocol']}")
        print(f"✓ Chain: {data['chain']}")
        print(f"✓ Total TVL: ${data['total_tvl']:,.2f}")
        print(f"✓ Pool count: {len(data['pools'])}")
        print(f"✓ Main pools: {data.get('main_pool_count', 0)}")
        print(f"✓ Factory pools: {data.get('factory_pool_count', 0)}")
        
        if data['pools']:
            top_pool = data['pools'][0]
            token_symbols = [t['symbol'] for t in top_pool['tokens']]
            print(f"\n  Top pool: {'/'.join(token_symbols)}")
            print(f"  TVL: ${top_pool['tvl']:,.2f}")
            print(f"  Pool type: {top_pool['pool_type']}")
        
        print("\n✅ Curve test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Curve test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("Real Data Fetcher Test Suite")
    print("="*80)
    print("\nThis will test all TVL fetchers with real API calls")
    print("Note: Tests may take 5-10 seconds due to rate limiting")
    print("="*80)
    
    results = {
        'Uniswap V3': test_uniswap_v3(),
        'Balancer': test_balancer(),
        'Curve': test_curve()
    }
    
    print("\n" + "="*80)
    print("Test Results Summary")
    print("="*80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:20s} {status}")
    
    print("="*80)
    print(f"Total: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n🎉 All tests passed! Real data fetching is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
