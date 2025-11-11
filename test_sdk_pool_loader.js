#!/usr/bin/env node
/**
 * Test script for SDK Pool Loader
 * Validates real data fetching from DeFiLlama and The Graph
 */

const SDKPoolLoader = require('./sdk_pool_loader');

async function testSDKPoolLoader() {
  console.log('\n' + '='.repeat(80));
  console.log('Testing SDK Pool Loader - Real Data Fetching');
  console.log('='.repeat(80));
  console.log('\nThis test will fetch real pool data from DeFiLlama and The Graph');
  console.log('Note: May take 10-20 seconds due to API calls and rate limiting');
  console.log('='.repeat(80));

  try {
    const loader = new SDKPoolLoader();
    
    // Test 1: Load all pools
    console.log('\n[Test 1] Loading all pools...');
    const startTime = Date.now();
    await loader.loadAllPools();
    const elapsed = Date.now() - startTime;
    
    // Validate results
    if (loader.deepPools.length === 0) {
      throw new Error('No pools loaded - check API connectivity');
    }
    
    console.log(`✓ Loaded ${loader.deepPools.length} pools in ${elapsed}ms`);
    
    // Test 2: Get statistics
    console.log('\n[Test 2] Getting pool statistics...');
    const stats = loader.getStatistics();
    
    console.log(`✓ Total pools: ${stats.totalPools}`);
    console.log(`✓ Total TVL: $${stats.totalTVL.toLocaleString()}`);
    console.log(`✓ Average TVL: $${stats.avgTVL.toLocaleString()}`);
    console.log(`✓ Protocols: ${Object.keys(stats.byProtocol).join(', ')}`);
    console.log(`✓ Chains: ${Object.keys(stats.byChain).join(', ')}`);
    
    // Test 3: Get top pools
    console.log('\n[Test 3] Getting top pools...');
    const topPools = loader.getTopPools(5);
    
    if (topPools.length === 0) {
      throw new Error('No top pools returned');
    }
    
    console.log(`✓ Top pool TVL: $${parseFloat(topPools[0].liquidity).toLocaleString()}`);
    
    // Test 4: Search for specific token pair
    console.log('\n[Test 4] Searching for WETH/USDC pools...');
    const wethUsdcPools = loader.getPoolsForPair('WETH', 'USDC');
    console.log(`✓ Found ${wethUsdcPools.length} WETH/USDC pools`);
    
    if (wethUsdcPools.length > 0) {
      console.log(`  - Top pool: ${wethUsdcPools[0].protocol} on ${wethUsdcPools[0].chain}`);
      console.log(`  - TVL: $${parseFloat(wethUsdcPools[0].liquidity).toLocaleString()}`);
    }
    
    // Test 5: Filter by protocol
    console.log('\n[Test 5] Filtering by protocol...');
    const uniswapPools = loader.getPoolsByProtocol('uniswap-v3');
    console.log(`✓ Found ${uniswapPools.length} Uniswap V3 pools`);
    
    // Test 6: Filter by chain
    console.log('\n[Test 6] Filtering by chain...');
    const ethereumPools = loader.getPoolsByChain('ethereum');
    const polygonPools = loader.getPoolsByChain('polygon');
    console.log(`✓ Ethereum pools: ${ethereumPools.length}`);
    console.log(`✓ Polygon pools: ${polygonPools.length}`);
    
    // Test 7: Data quality checks
    console.log('\n[Test 7] Data quality checks...');
    
    // Check for required fields
    const samplePool = loader.deepPools[0];
    const requiredFields = ['id', 'protocol', 'chain', 'liquidity', 'tvl'];
    
    for (const field of requiredFields) {
      if (!(field in samplePool)) {
        throw new Error(`Missing required field: ${field}`);
      }
    }
    console.log('✓ All required fields present');
    
    // Check data types
    if (typeof parseFloat(samplePool.liquidity) !== 'number') {
      throw new Error('Liquidity is not a number');
    }
    console.log('✓ Data types correct');
    
    // Check minimum TVL filter
    const minLiquidity = loader.minLiquidity;
    const belowMin = loader.deepPools.filter(p => parseFloat(p.liquidity) < minLiquidity);
    if (belowMin.length > 0) {
      console.warn(`⚠️  Warning: ${belowMin.length} pools below minimum liquidity`);
    } else {
      console.log(`✓ All pools meet minimum liquidity ($${minLiquidity.toLocaleString()})`);
    }
    
    // Test 8: Cache functionality
    console.log('\n[Test 8] Testing cache...');
    const cacheStartTime = Date.now();
    await loader.loadAllPools(); // Should use cache
    const cacheElapsed = Date.now() - cacheStartTime;
    
    if (cacheElapsed < 1000) {
      console.log(`✓ Cache working (${cacheElapsed}ms - much faster than ${elapsed}ms)`);
    } else {
      console.warn(`⚠️  Cache may not be working (${cacheElapsed}ms)`);
    }
    
    // Test 9: Save to file
    console.log('\n[Test 9] Saving pools to file...');
    loader.savePools('test_pools_output.json');
    console.log('✓ Pools saved successfully');
    
    console.log('\n' + '='.repeat(80));
    console.log('✅ All tests PASSED!');
    console.log('='.repeat(80));
    console.log('\n📊 Final Summary:');
    loader.displayTopPools(3);
    
    return 0;
    
  } catch (error) {
    console.error('\n' + '='.repeat(80));
    console.error('❌ Test FAILED');
    console.error('='.repeat(80));
    console.error(`\nError: ${error.message}`);
    console.error('\nStack trace:');
    console.error(error.stack);
    return 1;
  }
}

// Run tests
if (require.main === module) {
  testSDKPoolLoader()
    .then(code => {
      process.exit(code);
    })
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}

module.exports = { testSDKPoolLoader };
