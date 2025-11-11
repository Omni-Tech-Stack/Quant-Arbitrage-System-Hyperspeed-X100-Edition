# Real Data Fetching System - Quick Start Guide

## Overview

The Quant Arbitrage System now uses **real on-chain and API data** instead of mock/random data. This guide will help you get started quickly.

## What Changed?

### Before (Mock Data)
```python
# Generated random fake pools
mock_pools = [
    {"tvl": random.randint(1000000, 20000000)}
    for i in range(8)
]
```

### After (Real Data)
```python
# Fetches real pools from The Graph subgraph
data = fetcher.fetch_tvl()
# Returns actual on-chain liquidity data
```

## Quick Start

### 1. Python TVL Fetchers

**Install dependencies** (already in requirements.txt):
```bash
pip install requests web3
```

**Basic usage**:
```python
from uniswapv3_tvl_fetcher import UniswapV3TVLFetcher
from balancer_tvl_fetcher import BalancerTVLFetcher
from src.curve_tvl_fetcher import CurveTVLFetcher

# Fetch Uniswap V3 pools
uniswap = UniswapV3TVLFetcher(chain="ethereum", min_tvl_usd=100000)
data = uniswap.fetch_tvl()
print(f"Total TVL: ${data['total_tvl']:,.2f}")
print(f"Pools: {len(data['pools'])}")

# Fetch Balancer pools
balancer = BalancerTVLFetcher(chain="polygon")
data = balancer.fetch_tvl()

# Fetch Curve pools
curve = CurveTVLFetcher(chain="ethereum")
data = curve.fetch_tvl()
```

### 2. JavaScript SDK Pool Loader

**Install dependencies** (already in package.json):
```bash
npm install axios
```

**Basic usage**:
```javascript
const SDKPoolLoader = require('./sdk_pool_loader');

const loader = new SDKPoolLoader();

// Load all pools from multiple protocols
await loader.loadAllPools();

// Get top pools by TVL
const topPools = loader.getTopPools(10);

// Find specific token pair
const wethUsdc = loader.getPoolsForPair('WETH', 'USDC');
```

## Testing

### Test Python Fetchers
```bash
python test_real_data_fetchers.py
```

Expected output:
```
✅ Uniswap V3 test PASSED
✅ Balancer test PASSED
✅ Curve test PASSED
🎉 All tests passed!
```

### Test JavaScript Loader
```bash
node test_sdk_pool_loader.js
```

Expected output:
```
✓ Loaded 150+ pools
✓ Total TVL: $1,500,000,000+
✅ All tests PASSED!
```

## Data Sources

### Uniswap V3
- **Source**: The Graph Subgraph (decentralized)
- **Update frequency**: ~15 seconds (new blocks)
- **Coverage**: All pools with >$50k TVL
- **Reliability**: ⭐⭐⭐⭐⭐

### Balancer
- **Primary**: Official Balancer API
- **Fallback**: The Graph Subgraph
- **Update frequency**: ~1 minute
- **Coverage**: Main pools + factory pools
- **Reliability**: ⭐⭐⭐⭐⭐

### Curve
- **Source**: Official Curve API
- **Update frequency**: ~5 minutes
- **Coverage**: Main + factory pools
- **Reliability**: ⭐⭐⭐⭐⭐

### DeFiLlama (SDK Loader)
- **Source**: Aggregated yields data
- **Update frequency**: ~10 minutes
- **Coverage**: 100+ protocols
- **Reliability**: ⭐⭐⭐⭐

## Configuration

### Minimum TVL Filter

Adjust to focus on high-liquidity pools:

**Python**:
```python
fetcher = UniswapV3TVLFetcher(
    chain="ethereum",
    min_tvl_usd=500000  # Only pools with >$500k TVL
)
```

**JavaScript**:
```javascript
const loader = new SDKPoolLoader();
loader.minLiquidity = 500000; // $500k minimum
```

### Chain Selection

**Supported chains**:
- `ethereum` - Ethereum mainnet
- `polygon` - Polygon (Matic)
- `arbitrum` - Arbitrum One
- `optimism` - Optimism
- `base` - Base (Curve only)

**Python**:
```python
fetcher = UniswapV3TVLFetcher(chain="polygon")
```

**JavaScript**:
```javascript
loader.chains = ['ethereum', 'polygon', 'arbitrum'];
```

### Cache TTL

Adjust cache duration:

**Python**:
```python
fetcher = UniswapV3TVLFetcher(chain="ethereum")
fetcher.cache_ttl = 600  # 10 minutes
```

**JavaScript**:
```javascript
loader.cacheTTL = 600000; // 10 minutes (in ms)
```

## Advanced Usage

### Find Specific Pool

**Python (Uniswap V3)**:
```python
pool = fetcher.get_pool_by_tokens("WETH", "USDC", fee_tier=0.003)
if pool:
    print(f"Pool address: {pool['address']}")
    print(f"TVL: ${pool['tvl']:,.2f}")
    print(f"24h volume: ${pool['volume_usd']:,.2f}")
```

**Python (Balancer)**:
```python
pool = fetcher.get_pool_by_id("0x06df3b2bbb68adc...")
if pool:
    print(f"Pool type: {pool['pool_type']}")
    print(f"Tokens: {[t['symbol'] for t in pool['tokens']]}")
```

**Python (Curve)**:
```python
# Get all stablecoin pools
stablecoin_pools = fetcher.get_stablecoin_pools()
for pool in stablecoin_pools:
    print(f"{pool['name']}: ${pool['tvl']:,.2f}")
```

**JavaScript**:
```javascript
// Filter by protocol
const uniswapPools = loader.getPoolsByProtocol('uniswap-v3');

// Filter by chain
const polygonPools = loader.getPoolsByChain('polygon');

// Get statistics
const stats = loader.getStatistics();
console.log(`Total TVL: $${stats.totalTVL.toLocaleString()}`);
```

### Async/Await Pattern

**Python**:
```python
import asyncio

async def fetch_multiple_protocols():
    uniswap = UniswapV3TVLFetcher()
    balancer = BalancerTVLFetcher()
    
    # Fetch concurrently
    results = await asyncio.gather(
        uniswap.fetch_all_pools(),
        balancer.fetch_all_pools()
    )
    
    return results

# Run
results = asyncio.run(fetch_multiple_protocols())
```

**JavaScript**:
```javascript
async function loadAllData() {
    const loader = new SDKPoolLoader();
    
    // Load pools
    await loader.loadAllPools();
    
    // Process results
    const stats = loader.getStatistics();
    return stats;
}

loadAllData().then(stats => {
    console.log('Total TVL:', stats.totalTVL);
});
```

## Error Handling

### Network Errors

**Automatic retry** with exponential backoff:
- 1st attempt: immediate
- 2nd attempt: 1 second delay
- 3rd attempt: 2 second delay
- Final: returns empty result with error flag

### API Rate Limits

**Built-in rate limiting**:
- The Graph: 1 request/second
- Curve API: 1 request/1.5 seconds
- DeFiLlama: 1 request/second

If rate-limited:
1. Increase `min_request_interval`
2. Use caching more aggressively
3. Implement request queue

### Validation Errors

**Data validation**:
- TVL must be numeric
- Pool addresses must be valid
- Required fields must exist

If validation fails:
- Pool is skipped (logged as warning)
- Continues processing other pools
- Returns partial results

## Performance Tips

### 1. Use Caching
```python
# First call: 3-5 seconds (API request)
data1 = fetcher.fetch_tvl()

# Second call within 5 min: <10ms (cached)
data2 = fetcher.fetch_tvl()
```

### 2. Filter Aggressively
```python
# Fewer pools = faster processing
fetcher = UniswapV3TVLFetcher(min_tvl_usd=1000000)  # Only >$1M pools
```

### 3. Choose Right Data Source
- **Fastest**: DeFiLlama (aggregated)
- **Most accurate**: The Graph (direct indexing)
- **Most reliable**: Multi-source fallback

## Monitoring

### Check Data Freshness
```python
data = fetcher.fetch_tvl()
age_seconds = time.time() - data['timestamp']
if age_seconds > 600:  # 10 minutes
    print("⚠️  Data is stale, consider refresh")
```

### Monitor API Success Rate
```python
import logging
logging.basicConfig(level=logging.INFO)

# Will log all API requests and errors
fetcher = UniswapV3TVLFetcher(chain="ethereum")
data = fetcher.fetch_tvl()
```

### Track Pool Count Changes
```python
previous_count = 150
current_count = len(data['pools'])

if current_count < previous_count * 0.8:  # 20% drop
    print("⚠️  Significant drop in pool count - API issue?")
```

## Integration with Existing System

The real data fetchers are **backward compatible** with the mock data system:

```python
# Old code still works!
from uniswapv3_tvl_fetcher import UniswapV3TVLFetcher

fetcher = UniswapV3TVLFetcher(chain="ethereum")
data = fetcher.fetch_tvl()  # Same interface

# Same structure:
# - data['protocol']
# - data['chain']
# - data['total_tvl']
# - data['pools']
# - data['timestamp']
```

## Troubleshooting

### "No pools returned"

**Possible causes**:
1. API endpoint down
2. Network connectivity issue
3. Min TVL too high

**Solutions**:
```python
# Lower min TVL
fetcher = UniswapV3TVLFetcher(min_tvl_usd=10000)

# Check API manually
import requests
response = requests.get('https://api.thegraph.com/...')
print(response.status_code)
```

### "Request timeout"

**Possible causes**:
1. Slow network
2. API overloaded
3. Firewall blocking

**Solutions**:
```python
# Increase timeout
import requests
response = requests.post(url, json=data, timeout=60)  # 60 seconds
```

### "Rate limit exceeded"

**Solutions**:
```python
# Increase delay between requests
fetcher.min_request_interval = 2.0  # 2 seconds
```

## Next Steps

1. ✅ Replace mock data with real fetchers
2. ✅ Test with small TVL filter ($100k)
3. ✅ Monitor for 1 hour
4. ✅ Increase TVL filter if needed ($500k+)
5. ✅ Deploy to production
6. ⬜ Set up monitoring alerts
7. ⬜ Implement WebSocket updates (future)

## Support

For issues or questions:
1. Check logs: `tail -f logs/*.log`
2. Run tests: `python test_real_data_fetchers.py`
3. Review docs: `REAL_DATA_INTEGRATION_GUIDE.md`
4. Check API status: https://thegraph.com/hosted-service

## Summary

✅ **Real data** from trusted sources  
✅ **No authentication** required  
✅ **Automatic retry** on failures  
✅ **Built-in caching** for performance  
✅ **Rate limiting** to prevent bans  
✅ **Backward compatible** with existing code  
✅ **Production ready** for live trading  

**You're all set! Start fetching real pool data now.** 🚀
