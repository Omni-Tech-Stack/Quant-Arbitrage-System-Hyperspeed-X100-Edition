#!/usr/bin/env node
/**
 * SDK Pool Loader - Real Data Implementation
 * Fetches real pool data from DeFiLlama, The Graph, and protocol APIs
 * Prioritizes deep pools and aggregates data from multiple sources
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

class SDKPoolLoader {
  constructor() {
    this.pools = [];
    this.deepPools = [];
    this.minLiquidity = 100000; // $100k minimum
    this.chains = ['ethereum', 'polygon'];
    
    // API endpoints
    this.defiLlamaBaseUrl = 'https://api.llama.fi';
    this.defiLlamaPoolsUrl = 'https://yields.llama.fi/pools';
    
    // The Graph subgraph endpoints
    this.subgraphs = {
      ethereum: {
        'uniswap-v3': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
        'balancer': 'https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2',
        'curve': 'https://api.thegraph.com/subgraphs/name/convex-community/curve-pools'
      },
      polygon: {
        'uniswap-v3': 'https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon',
        'quickswap': 'https://api.thegraph.com/subgraphs/name/sameepsi/quickswap-v3',
        'balancer': 'https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-polygon-v2',
        'curve': 'https://api.thegraph.com/subgraphs/name/convex-community/curve-pools-polygon'
      }
    };
    
    // Rate limiting
    this.lastRequestTime = 0;
    this.minRequestInterval = 1000; // 1 second between requests
    
    // Cache
    this.cache = null;
    this.cacheTimestamp = 0;
    this.cacheTTL = 300000; // 5 minutes
  }

  /**
   * Rate limiting helper
   */
  async rateLimit() {
    const now = Date.now();
    const elapsed = now - this.lastRequestTime;
    if (elapsed < this.minRequestInterval) {
      await new Promise(resolve => setTimeout(resolve, this.minRequestInterval - elapsed));
    }
    this.lastRequestTime = Date.now();
  }

  /**
   * Fetch pools from DeFiLlama (aggregated multi-protocol data)
   */
  async fetchFromDeFiLlama(retries = 3) {
    await this.rateLimit();
    
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await axios.get(this.defiLlamaPoolsUrl, {
          timeout: 30000,
          headers: { 'Accept': 'application/json' }
        });
        
        if (!response.data || !response.data.data) {
          throw new Error('Invalid response from DeFiLlama');
        }
        
        const pools = response.data.data
          .filter(pool => {
            // Filter by chains
            const chainMatch = this.chains.includes(pool.chain?.toLowerCase());
            // Filter by minimum TVL
            const tvlMatch = pool.tvlUsd >= this.minLiquidity;
            return chainMatch && tvlMatch;
          })
          .map(pool => ({
            id: pool.pool || pool.poolId || `${pool.project}-${pool.symbol}`,
            address: pool.poolMeta || pool.pool || null,
            protocol: pool.project?.toLowerCase() || 'unknown',
            chain: pool.chain?.toLowerCase() || 'ethereum',
            symbol: pool.symbol,
            tokens: this._parseTokensFromSymbol(pool.symbol),
            liquidity: pool.tvlUsd.toFixed(2),
            tvl: pool.tvlUsd,
            apy: pool.apy || 0,
            apyBase: pool.apyBase || 0,
            apyReward: pool.apyReward || 0,
            volume24h: pool.volumeUsd1d || 0,
            lastUpdate: Date.now(),
            source: 'defillama'
          }));
        
        console.log(`[DeFiLlama] ✓ Fetched ${pools.length} pools`);
        return pools;
        
      } catch (error) {
        console.warn(`[DeFiLlama] Attempt ${attempt + 1}/${retries} failed: ${error.message}`);
        if (attempt < retries - 1) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        } else {
          console.error('[DeFiLlama] All retry attempts failed');
          return [];
        }
      }
    }
    
    return [];
  }

  /**
   * Parse token information from pool symbol
   */
  _parseTokensFromSymbol(symbol) {
    if (!symbol) return [];
    
    // Common patterns: "WETH-USDC", "3pool", "stETH/ETH"
    const separators = ['-', '/', '_'];
    let tokens = [symbol];
    
    for (const sep of separators) {
      if (symbol.includes(sep)) {
        tokens = symbol.split(sep).map(t => t.trim());
        break;
      }
    }
    
    return tokens.map(t => ({
      symbol: t.toUpperCase(),
      decimals: 18 // Default, would need token contract lookup for real decimals
    }));
  }

  /**
   * Fetch pools from The Graph subgraph
   */
  async fetchFromSubgraph(chain, protocol, retries = 3) {
    const subgraphUrl = this.subgraphs[chain]?.[protocol];
    
    if (!subgraphUrl) {
      console.log(`[Subgraph] No subgraph URL for ${chain}/${protocol}`);
      return [];
    }
    
    await this.rateLimit();
    
    // GraphQL query for top pools
    const query = `
      query TopPools($minLiquidity: String!) {
        pools(
          first: 50
          orderBy: totalValueLockedUSD
          orderDirection: desc
          where: { totalValueLockedUSD_gte: $minLiquidity }
        ) {
          id
          ${protocol === 'uniswap-v3' || protocol === 'quickswap' ? `
            token0 { id symbol name decimals }
            token1 { id symbol name decimals }
            feeTier
            liquidity
            totalValueLockedUSD
            volumeUSD
          ` : protocol === 'balancer' ? `
            address
            name
            tokens { address symbol name decimals }
            totalLiquidity
            totalSwapVolume
          ` : protocol === 'curve' ? `
            address
            name
            coins { address symbol decimals }
            totalValueLockedUSD
          ` : ''}
        }
      }
    `;
    
    const variables = {
      minLiquidity: this.minLiquidity.toString()
    };
    
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await axios.post(
          subgraphUrl,
          { query, variables },
          {
            timeout: 30000,
            headers: { 'Content-Type': 'application/json' }
          }
        );
        
        if (response.data.errors) {
          throw new Error(`GraphQL errors: ${JSON.stringify(response.data.errors)}`);
        }
        
        const pools = response.data.data?.pools || [];
        const parsed = pools.map(pool => this._parseSubgraphPool(pool, chain, protocol));
        
        console.log(`[Subgraph] ✓ ${chain}/${protocol}: ${parsed.length} pools`);
        return parsed;
        
      } catch (error) {
        console.warn(`[Subgraph] ${chain}/${protocol} attempt ${attempt + 1}/${retries} failed: ${error.message}`);
        if (attempt < retries - 1) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        } else {
          console.error(`[Subgraph] ${chain}/${protocol} all retry attempts failed`);
          return [];
        }
      }
    }
    
    return [];
  }

  /**
   * Parse pool data from subgraph response
   */
  _parseSubgraphPool(pool, chain, protocol) {
    try {
      let tokens = [];
      let liquidity = 0;
      let volume24h = 0;
      
      if (protocol === 'uniswap-v3' || protocol === 'quickswap') {
        tokens = [
          {
            address: pool.token0?.id,
            symbol: pool.token0?.symbol,
            name: pool.token0?.name,
            decimals: parseInt(pool.token0?.decimals || 18)
          },
          {
            address: pool.token1?.id,
            symbol: pool.token1?.symbol,
            name: pool.token1?.name,
            decimals: parseInt(pool.token1?.decimals || 18)
          }
        ];
        liquidity = parseFloat(pool.totalValueLockedUSD || 0);
        volume24h = parseFloat(pool.volumeUSD || 0);
      } else if (protocol === 'balancer') {
        tokens = (pool.tokens || []).map(t => ({
          address: t.address,
          symbol: t.symbol,
          name: t.name,
          decimals: parseInt(t.decimals || 18)
        }));
        liquidity = parseFloat(pool.totalLiquidity || 0);
        volume24h = parseFloat(pool.totalSwapVolume || 0);
      } else if (protocol === 'curve') {
        tokens = (pool.coins || []).map(c => ({
          address: c.address,
          symbol: c.symbol,
          decimals: parseInt(c.decimals || 18)
        }));
        liquidity = parseFloat(pool.totalValueLockedUSD || 0);
      }
      
      return {
        id: pool.id,
        address: pool.address || pool.id,
        protocol,
        chain,
        name: pool.name || `${tokens.map(t => t.symbol).join('/')}`,
        tokens,
        liquidity: liquidity.toFixed(2),
        tvl: liquidity,
        volume24h: volume24h.toFixed(2),
        fee: protocol === 'uniswap-v3' ? parseInt(pool.feeTier || 3000) / 1000000 : 0.003,
        lastUpdate: Date.now(),
        source: 'subgraph'
      };
    } catch (error) {
      console.warn(`[Parse] Error parsing pool: ${error.message}`);
      return null;
    }
  }

  /**
   * Load pools using protocol SDKs and APIs (real implementation)
   */
  async loadPoolsFromSDK(chain, protocol) {
    console.log(`[SDK] Loading ${protocol} pools on ${chain}...`);
    
    try {
      // First try subgraph (most reliable)
      const pools = await this.fetchFromSubgraph(chain, protocol);
      
      if (pools.length > 0) {
        return pools;
      }
      
      // If subgraph fails, return empty array
      console.warn(`[SDK] No pools loaded for ${chain}/${protocol}`);
      return [];
      
    } catch (error) {
      console.error(`[SDK] Error loading ${chain}/${protocol}: ${error.message}`);
      return [];
    }
  }

  /**
   * Filter pools by liquidity threshold
   */
  filterDeepPools(pools) {
    return pools.filter(pool => {
      const liquidity = parseFloat(pool.liquidity);
      return liquidity >= this.minLiquidity;
    });
  }

  /**
   * Load all pools from multiple sources
   */
  async loadAllPools() {
    console.log('\n' + '='.repeat(80));
    console.log('  SDK POOL LOADER - Real Data from DeFiLlama & The Graph');
    console.log('='.repeat(80));
    console.log(`\nLoading deep pools (min liquidity: $${this.minLiquidity.toLocaleString()})...`);
    
    // Check cache first
    const now = Date.now();
    if (this.cache && (now - this.cacheTimestamp) < this.cacheTTL) {
      console.log('[Cache] Using cached data');
      this.deepPools = this.cache;
      return this.deepPools;
    }
    
    const startTime = Date.now();
    let allPools = [];
    
    // Method 1: Try DeFiLlama first (fastest, aggregated data)
    console.log('\n[DeFiLlama] Fetching aggregated pool data...');
    try {
      const defiLlamaPools = await this.fetchFromDeFiLlama();
      if (defiLlamaPools.length > 0) {
        allPools = defiLlamaPools;
        console.log(`[DeFiLlama] ✓ Loaded ${allPools.length} pools`);
      }
    } catch (error) {
      console.warn(`[DeFiLlama] Failed: ${error.message}`);
    }
    
    // Method 2: If DeFiLlama fails or returns few results, use subgraphs
    if (allPools.length < 50) {
      console.log('\n[Subgraph] Fetching from The Graph as primary/fallback...');
      
      const protocols = {
        ethereum: ['uniswap-v3', 'balancer', 'curve'],
        polygon: ['uniswap-v3', 'quickswap', 'balancer', 'curve']
      };
      
      for (const chain of this.chains) {
        console.log(`\n[Subgraph] Processing ${chain}...`);
        
        for (const protocol of protocols[chain]) {
          try {
            const pools = await this.loadPoolsFromSDK(chain, protocol);
            allPools.push(...pools);
            console.log(`[Subgraph] ✓ ${chain}/${protocol}: ${pools.length} pools`);
          } catch (error) {
            console.error(`[Subgraph] ✗ ${chain}/${protocol}: ${error.message}`);
          }
        }
      }
    }
    
    // Remove duplicates based on pool ID
    const uniquePools = [];
    const seenIds = new Set();
    
    for (const pool of allPools) {
      const poolId = pool.id || pool.address;
      if (!seenIds.has(poolId)) {
        seenIds.add(poolId);
        uniquePools.push(pool);
      }
    }
    
    // Filter for deep pools and sort by liquidity
    this.pools = uniquePools;
    this.deepPools = this.filterDeepPools(uniquePools);
    this.deepPools.sort((a, b) => parseFloat(b.liquidity) - parseFloat(a.liquidity));
    
    // Update cache
    this.cache = this.deepPools;
    this.cacheTimestamp = now;
    
    const elapsed = Date.now() - startTime;
    
    console.log('\n' + '='.repeat(80));
    console.log('  SDK LOAD SUMMARY');
    console.log('='.repeat(80));
    console.log(`Total Pools:     ${uniquePools.length}`);
    console.log(`Deep Pools:      ${this.deepPools.length}`);
    console.log(`Avg Liquidity:   $${this.calculateAvgLiquidity().toLocaleString()}`);
    console.log(`Load Time:       ${elapsed}ms`);
    console.log(`Data Sources:    ${allPools[0]?.source || 'mixed'}`);
    console.log('='.repeat(80));
    
    return this.deepPools;
  }

  /**
   * Calculate average liquidity
   */
  calculateAvgLiquidity() {
    if (this.deepPools.length === 0) return 0;
    
    const totalLiquidity = this.deepPools.reduce((sum, pool) => {
      return sum + parseFloat(pool.liquidity);
    }, 0);
    
    return Math.round(totalLiquidity / this.deepPools.length);
  }

  /**
   * Get pools sorted by liquidity
   */
  getTopPools(limit = 10) {
    return [...this.deepPools]
      .sort((a, b) => parseFloat(b.liquidity) - parseFloat(a.liquidity))
      .slice(0, limit);
  }

  /**
   * Get pools for a specific token pair
   */
  getPoolsForPair(token0, token1) {
    return this.deepPools.filter(pool => {
      const tokens = pool.tokens || [pool.token0, pool.token1];
      const symbols = tokens.map(t => t?.symbol?.toUpperCase());
      
      const hasToken0 = symbols.includes(token0.toUpperCase());
      const hasToken1 = symbols.includes(token1.toUpperCase());
      
      return hasToken0 && hasToken1;
    });
  }

  /**
   * Get pools for a specific protocol
   */
  getPoolsByProtocol(protocol) {
    return this.deepPools.filter(pool => 
      pool.protocol?.toLowerCase() === protocol.toLowerCase()
    );
  }

  /**
   * Get pools for a specific chain
   */
  getPoolsByChain(chain) {
    return this.deepPools.filter(pool => 
      pool.chain?.toLowerCase() === chain.toLowerCase()
    );
  }

  /**
   * Save pools to file
   */
  savePools(filename = 'sdk_pools.json') {
    const filepath = path.join(__dirname, filename);
    
    try {
      const data = JSON.stringify({
        pools: this.deepPools,
        metadata: {
          count: this.deepPools.length,
          minLiquidity: this.minLiquidity,
          avgLiquidity: this.calculateAvgLiquidity(),
          chains: this.chains,
          timestamp: Date.now(),
          cacheTTL: this.cacheTTL
        }
      }, null, 2);
      
      fs.writeFileSync(filepath, data, 'utf8');
      console.log(`\n[SDK] ✓ Saved ${this.deepPools.length} pools to ${filename}`);
    } catch (error) {
      console.error(`[SDK] ✗ Error saving pools: ${error.message}`);
    }
  }

  /**
   * Display top pools
   */
  displayTopPools(limit = 5) {
    const topPools = this.getTopPools(limit);
    
    if (topPools.length === 0) {
      console.log('\n⚠️  No pools to display');
      return;
    }
    
    console.log(`\n📊 Top ${limit} Pools by Liquidity:`);
    console.log('-'.repeat(80));
    
    topPools.forEach((pool, index) => {
      const tokens = pool.tokens || [pool.token0, pool.token1];
      const tokenSymbols = tokens.map(t => t?.symbol).filter(Boolean).join('/');
      
      console.log(`${index + 1}. ${tokenSymbols || pool.symbol} on ${pool.chain}`);
      console.log(`   Protocol: ${pool.protocol}`);
      console.log(`   Liquidity: $${parseFloat(pool.liquidity).toLocaleString()}`);
      console.log(`   24h Volume: $${parseFloat(pool.volume24h || 0).toLocaleString()}`);
      if (pool.apy) {
        console.log(`   APY: ${pool.apy.toFixed(2)}%`);
      }
      console.log();
    });
  }

  /**
   * Get pool statistics
   */
  getStatistics() {
    const stats = {
      totalPools: this.deepPools.length,
      totalTVL: this.deepPools.reduce((sum, p) => sum + parseFloat(p.liquidity), 0),
      avgTVL: this.calculateAvgLiquidity(),
      byProtocol: {},
      byChain: {},
      topPool: this.deepPools[0]
    };
    
    // Count by protocol
    this.deepPools.forEach(pool => {
      stats.byProtocol[pool.protocol] = (stats.byProtocol[pool.protocol] || 0) + 1;
      stats.byChain[pool.chain] = (stats.byChain[pool.chain] || 0) + 1;
    });
    
    return stats;
  }
}

// Main execution
async function main() {
  const loader = new SDKPoolLoader();
  
  try {
    // Load all pools
    await loader.loadAllPools();
    
    // Display statistics
    const stats = loader.getStatistics();
    console.log('\n📈 Pool Statistics:');
    console.log(`   Total TVL: $${stats.totalTVL.toLocaleString()}`);
    console.log(`   By Protocol:`, stats.byProtocol);
    console.log(`   By Chain:`, stats.byChain);
    
    // Display top pools
    loader.displayTopPools(5);
    
    // Save to file
    loader.savePools();
    
    // Example: Find WETH/USDC pools
    const wethUsdcPools = loader.getPoolsForPair('WETH', 'USDC');
    console.log(`\n🔍 Found ${wethUsdcPools.length} WETH/USDC pools`);
    
    if (wethUsdcPools.length > 0) {
      console.log('   Top WETH/USDC pool:');
      const top = wethUsdcPools[0];
      console.log(`   - ${top.protocol} on ${top.chain}`);
      console.log(`   - Liquidity: $${parseFloat(top.liquidity).toLocaleString()}`);
    }
  } catch (error) {
    console.error('[SDK] ✗ Error:', error);
    throw error;
  }
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('[SDK] ✗ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = SDKPoolLoader;
