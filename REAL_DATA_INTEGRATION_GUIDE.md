# Real Data Integration Guide

## Overview

This guide explains the implementation of real on-chain and API data fetching for the Quant Arbitrage System, replacing the previous mock data generators with production-ready data sources.

## Architecture

### Data Sources Strategy

We use a **multi-tier fallback architecture** for maximum reliability:

1. **Primary**: Public APIs and official protocol endpoints (fastest, most reliable)
2. **Secondary**: The Graph subgraphs (decentralized, censorship-resistant)
3. **Tertiary**: Direct RPC contract calls (most accurate but slower)

### Implemented Data Fetchers

#### 1. Uniswap V3 TVL Fetcher (`uniswapv3_tvl_fetcher.py`)

**Data Source**: The Graph Subgraph API (public, no authentication required)

**Endpoints**:
- Ethereum: `https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3`
- Polygon: `https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon`
- Arbitrum: `https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-arbitrum-one`
- Optimism: `https://api.thegraph.com/subgraphs/name/ianlapham/optimism-post-regenesis`

**Features**:
- Real-time pool TVL and liquidity data
- Token pair information with decimals
- Fee tier information (0.01%, 0.05%, 0.3%, 1%)
- 24h volume and trading statistics
- Built-in rate limiting (1 second between requests)
- 5-minute cache with automatic refresh
- Exponential backoff retry logic (3 attempts)

**Usage**:
```python
from uniswapv3_tvl_fetcher import UniswapV3TVLFetcher

# Initialize for Polygon with minimum $50k TVL
fetcher = UniswapV3TVLFetcher(
    chain="polygon",
    min_tvl_usd=50000,
    rpc_url="https://polygon-rpc.com"  # Optional
)

# Fetch all pools
data = fetcher.fetch_tvl()
print(f"Total TVL: ${data['total_tvl']:,.2f}")
print(f"Pool count: {data['pool_count']}")

# Find specific pool
pool = fetcher.get_pool_by_tokens("WETH", "USDC", fee_tier=0.003)
if pool:
    print(f"WETH/USDC 0.3% pool TVL: ${pool['tvl']:,.2f}")
```

#### 2. Balancer TVL Fetcher (`balancer_tvl_fetcher.py`)

**Data Sources**:
- **Primary**: Balancer API (`https://api.balancer.fi/pools/{chainId}`)
- **Fallback**: The Graph Subgraph

**Endpoints**:
- Ethereum API: `https://api.balancer.fi/pools/1`
- Polygon API: `https://api.balancer.fi/pools/137`
- Arbitrum API: `https://api.balancer.fi/pools/42161`
- Optimism API: `https://api.balancer.fi/pools/10`

**Features**:
- Weighted pools and stable pools support
- Token composition with weights
- Pool type identification (weighted, stable, meta-stable)
- Swap fee information
- 24h volume and fee statistics
- Automatic API → Subgraph fallback
- Rate limiting and caching

**Usage**:
```python
from balancer_tvl_fetcher import BalancerTVLFetcher

# Initialize
fetcher = BalancerTVLFetcher(chain="ethereum", min_tvl_usd=100000)

# Fetch pools
data = fetcher.fetch_tvl()

# Find specific pool by ID
pool = fetcher.get_pool_by_id("0x06df3b2bbb68adc...")
if pool:
    print(f"Pool type: {pool['pool_type']}")
    print(f"Token weights: {pool['weights']}")
```

#### 3. Curve TVL Fetcher (`src/curve_tvl_fetcher.py`)

**Data Source**: Official Curve API (public, no authentication)

**Endpoints**:
- Ethereum Main: `https://api.curve.fi/api/getPools/ethereum/main`
- Ethereum Factory: `https://api.curve.fi/api/getPools/ethereum/factory`
- Polygon: `https://api.curve.fi/api/getPools/polygon/main`
- Arbitrum: `https://api.curve.fi/api/getPools/arbitrum/main`

**Features**:
- Main pools and factory pools aggregation
- StableSwap and CryptoSwap pool support
- Amplification coefficient (A parameter)
- Virtual price tracking
- Meta-pool identification
- Stablecoin pool filtering
- Duplicate removal across main/factory

**Usage**:
```python
from src.curve_tvl_fetcher import CurveTVLFetcher

# Initialize
fetcher = CurveTVLFetcher(chain="ethereum", min_tvl_usd=200000)

# Fetch all pools
data = fetcher.fetch_tvl()
print(f"Main pools: {data['main_pool_count']}")
print(f"Factory pools: {data['factory_pool_count']}")

# Get stablecoin pools only
stablecoin_pools = fetcher.get_stablecoin_pools()
for pool in stablecoin_pools[:5]:
    print(f"{pool['name']}: ${pool['tvl']:,.2f}")

# Find specific pool
pool = fetcher.get_pool_by_address("0x8096ac61db23291252574D49f036f0f9ed8ab390")
```

#### 4. SDK Pool Loader (`sdk_pool_loader.js`)

**Data Sources**:
- **Primary**: DeFiLlama Yields API (aggregated cross-protocol data)
- **Fallback**: The Graph Subgraphs (per-protocol)

**Endpoints**:
- DeFiLlama: `https://yields.llama.fi/pools`
- The Graph: Protocol-specific subgraphs

**Features**:
- Multi-protocol aggregation (Uniswap, Balancer, Curve, etc.)
- Cross-chain support (Ethereum, Polygon, Arbitrum, Optimism)
- APY/APR data included
- Intelligent fallback system
- Duplicate detection and removal
- 5-minute caching
- Export to JSON

**Usage**:
```javascript
const SDKPoolLoader = require('./sdk_pool_loader');

const loader = new SDKPoolLoader();

// Load all pools
await loader.loadAllPools();

// Get top pools by TVL
const topPools = loader.getTopPools(10);

// Find pools for token pair
const wethUsdcPools = loader.getPoolsForPair('WETH', 'USDC');

// Filter by protocol
const uniswapPools = loader.getPoolsByProtocol('uniswap-v3');

// Filter by chain
const polygonPools = loader.getPoolsByChain('polygon');

// Get statistics
const stats = loader.getStatistics();
console.log(`Total TVL: $${stats.totalTVL.toLocaleString()}`);

// Save to file
loader.savePools('my_pools.json');
```

## Security Considerations

### 1. API Security

**Rate Limiting**:
- All fetchers implement rate limiting (1-1.5 seconds between requests)
- Prevents API abuse and IP bans
- Configurable per fetcher

**Retry Logic**:
- Exponential backoff on failures (1s, 2s, 4s)
- Maximum 3 retry attempts per request
- Graceful degradation to fallback sources

**Timeout Protection**:
- 30-second timeout on all HTTP requests
- Prevents indefinite hanging
- Allows quick failover to alternatives

### 2. Data Validation

**TVL Filtering**:
- Minimum liquidity thresholds prevent dust pools
- Default: $50k-$100k minimum
- Configurable per deployment

**Duplicate Detection**:
- Pool address/ID uniqueness checks
- Cross-source deduplication
- Prevents double-counting TVL

**Error Handling**:
- Graceful failure modes
- Empty result sets instead of crashes
- Detailed error logging

### 3. Caching Strategy

**Cache TTL**: 5 minutes (300 seconds)
- Balances freshness vs. API load
- Reduces redundant API calls
- Prevents stale data in fast-moving markets

**Cache Invalidation**:
- Automatic on TTL expiry
- Manual refresh available
- Timestamp tracking

### 4. No Private Keys or Credentials

**Public APIs Only**:
- No authentication required
- No API keys stored in code
- No risk of credential leakage

**RPC URLs** (optional):
- Pass from environment variables
- Never hardcoded
- Used only for direct contract calls (future feature)

## Performance Optimizations

### 1. Async/Await Patterns

- Non-blocking I/O for JavaScript
- Compatible with async Python workflows
- Parallel request potential

### 2. Response Parsing

- Efficient JSON parsing
- Minimal memory footprint
- Lazy loading where possible

### 3. Network Efficiency

- Single-request batch queries (GraphQL)
- Compressed response handling
- Connection reuse

### 4. Caching

- In-memory caching reduces API calls
- Configurable TTL per use case
- LRU eviction (if needed for scale)

## Error Handling Patterns

### 1. Graceful Degradation

```python
# Try API, fall back to subgraph, fall back to empty
data = self._fetch_from_api()
if not data:
    data = self._fetch_from_subgraph()
if not data:
    return {"pools": [], "error": "All sources failed"}
```

### 2. Detailed Logging

- `INFO`: Successful operations
- `WARNING`: Retryable failures
- `ERROR`: Fatal errors

### 3. User Feedback

- Clear error messages
- Status indicators
- Progress reporting

## Testing Recommendations

### Unit Tests

```python
# Test with mock responses
def test_uniswap_fetcher_parsing():
    fetcher = UniswapV3TVLFetcher(chain="ethereum")
    # Mock response data
    result = fetcher._parse_pool_data(mock_data)
    assert result['tvl'] > 0
```

### Integration Tests

```python
# Test live API calls (rate-limited)
@pytest.mark.integration
def test_real_api_call():
    fetcher = UniswapV3TVLFetcher()
    data = fetcher.fetch_tvl()
    assert data['pool_count'] > 0
```

### Error Injection Tests

```python
# Test retry logic
def test_retry_mechanism():
    fetcher = UniswapV3TVLFetcher()
    with patch('requests.post', side_effect=ConnectionError):
        result = fetcher.fetch_tvl()
        assert 'error' in result
```

## Monitoring and Alerts

### Key Metrics to Track

1. **API Success Rate**: % of successful requests
2. **Average Response Time**: Latency per data source
3. **Cache Hit Rate**: % of requests served from cache
4. **Pool Count**: Number of pools fetched (detect API issues)
5. **Total TVL**: Sanity check for data accuracy

### Alert Conditions

- API failures > 50% over 5 minutes
- Response time > 10 seconds
- Pool count drops > 20% suddenly
- Total TVL changes > 30% (may indicate API issue)

## Rate Limiting Guidelines

### The Graph

- **Recommended**: 1 request per second
- **Burst**: Up to 5 requests
- **Daily limit**: ~100k queries (free tier)

### Curve API

- **Recommended**: 1 request per 1.5 seconds
- **No documented limits**: Be conservative

### DeFiLlama

- **Recommended**: 1 request per second
- **Generous limits**: Rarely enforced for reasonable use

### Balancer API

- **Recommended**: 1 request per second
- **Fallback to subgraph**: If rate-limited

## Future Enhancements

### 1. Direct Contract Calls

- Implement Web3 direct reads for critical pools
- Use as tertiary fallback
- Requires RPC endpoint reliability

### 2. WebSocket Subscriptions

- Real-time pool updates
- Lower latency than polling
- Complex state management

### 3. Multi-Source Aggregation

- Combine data from multiple sources
- Cross-validate TVL figures
- Detect anomalies

### 4. Historical Data

- Track TVL changes over time
- Identify trends and patterns
- Improve ML model training

### 5. Custom Pool Discovery

- Detect new pools automatically
- Factory contract monitoring
- Event-driven updates

## Troubleshooting

### Issue: No pools returned

**Causes**:
- API endpoint down
- Network connectivity issues
- Min TVL threshold too high

**Solutions**:
1. Check logs for specific error messages
2. Test API endpoint manually: `curl https://api.thegraph.com/...`
3. Lower `min_tvl_usd` parameter
4. Try different chain/protocol

### Issue: Stale data

**Causes**:
- Cache not expiring
- API returning old data
- Network proxy caching

**Solutions**:
1. Reduce `cache_ttl`
2. Clear cache manually
3. Add cache-busting headers: `Cache-Control: no-cache`

### Issue: Rate limiting errors

**Causes**:
- Too many requests
- Shared IP rate limits
- Burst traffic

**Solutions**:
1. Increase `min_request_interval`
2. Implement request queue
3. Use multiple data sources
4. Deploy across multiple IPs/proxies

### Issue: Parsing errors

**Causes**:
- API schema changes
- Malformed responses
- Missing fields

**Solutions**:
1. Update parsing logic
2. Add schema validation
3. Fallback to alternative sources
4. Report to API maintainers

## Example Integration

### Full System Integration

```python
# orchestrator_tvl_hyperspeed.py

from uniswapv3_tvl_fetcher import UniswapV3TVLFetcher
from balancer_tvl_fetcher import BalancerTVLFetcher
from src.curve_tvl_fetcher import CurveTVLFetcher
import asyncio

class TVLOrchestrator:
    def __init__(self, chain="ethereum"):
        self.chain = chain
        self.fetchers = {
            'uniswap-v3': UniswapV3TVLFetcher(chain=chain),
            'balancer': BalancerTVLFetcher(chain=chain),
            'curve': CurveTVLFetcher(chain=chain)
        }
    
    async def fetch_all_protocols(self):
        results = {}
        for protocol, fetcher in self.fetchers.items():
            try:
                data = await fetcher.fetch_all_pools()
                results[protocol] = data
                print(f"✓ {protocol}: {data['pool_count']} pools")
            except Exception as e:
                print(f"✗ {protocol}: {e}")
                results[protocol] = {"error": str(e)}
        return results
    
    def aggregate_tvl(self, results):
        total_tvl = 0
        for protocol, data in results.items():
            if 'total_tvl' in data:
                total_tvl += data['total_tvl']
        return total_tvl

# Usage
async def main():
    orchestrator = TVLOrchestrator(chain="polygon")
    results = await orchestrator.fetch_all_protocols()
    total_tvl = orchestrator.aggregate_tvl(results)
    print(f"\nTotal TVL across all protocols: ${total_tvl:,.2f}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Conclusion

This real data integration provides:

✅ **Production-ready** data fetching  
✅ **Multiple fallback sources** for reliability  
✅ **Built-in error handling** and retry logic  
✅ **Rate limiting** to prevent API abuse  
✅ **Caching** for performance  
✅ **No authentication** required (public APIs)  
✅ **Comprehensive logging** for debugging  
✅ **Type-safe** parsing and validation  

The system is now ready for live arbitrage scanning with real market data.
