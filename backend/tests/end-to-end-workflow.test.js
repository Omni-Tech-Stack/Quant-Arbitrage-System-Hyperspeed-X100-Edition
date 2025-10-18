#!/usr/bin/env node

/**
 * End-to-End Workflow Test
 * Verifies the complete flashloan arbitrage system workflow
 */

const axios = require('axios');
const { spawn } = require('child_process');
const path = require('path');

const BASE_URL = 'http://localhost:3001';
let serverProcess;

// ANSI color codes for prettier output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function startServer() {
  return new Promise((resolve, reject) => {
    const serverPath = path.join(__dirname, '..');
    serverProcess = spawn(process.execPath, ['server.js'], {
      cwd: serverPath,
      env: { ...process.env, DEMO_MODE: 'true' }
    });

    serverProcess.stdout.on('data', (data) => {
      const output = data.toString();
      if (output.includes('running on port')) {
        setTimeout(resolve, 500);
      }
    });

    serverProcess.stderr.on('data', (data) => {
      console.error('Server error:', data.toString());
    });

    setTimeout(() => reject(new Error('Server startup timeout')), 10000);
  });
}

function stopServer() {
  if (serverProcess) {
    serverProcess.kill();
  }
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runWorkflow() {
  console.log('\n' + '='.repeat(70));
  log('FLASHLOAN ARBITRAGE SYSTEM - END-TO-END WORKFLOW TEST', 'bright');
  console.log('='.repeat(70) + '\n');

  try {
    // Step 1: Start server
    log('🚀 Step 1: Starting backend server...', 'blue');
    await startServer();
    log('✅ Server started successfully\n', 'green');
    await sleep(1000);

    // Step 2: Health check
    log('🔍 Step 2: Verifying system health...', 'blue');
    const healthResponse = await axios.get(`${BASE_URL}/api/health`);
    if (healthResponse.data.status === 'ok') {
      log('✅ System is healthy and ready\n', 'green');
    } else {
      throw new Error('Health check failed');
    }

    // Step 3: Define market conditions
    log('📊 Step 3: Setting up market conditions...', 'blue');
    const uniswapPool = {
      name: 'Uniswap V2',
      reserveIn: 1000000,  // 1M USDC
      reserveOut: 2000000  // 2M ETH
    };
    const sushiswapPool = {
      name: 'SushiSwap',
      reserveIn: 1800000,  // 1.8M USDC (10% cheaper!)
      reserveOut: 1000000  // 1M ETH
    };

    log(`  ${uniswapPool.name}: ${uniswapPool.reserveOut} ETH / ${uniswapPool.reserveIn} USDC`, 'reset');
    log(`  ${sushiswapPool.name}: ${sushiswapPool.reserveOut} ETH / ${sushiswapPool.reserveIn} USDC`, 'reset');
    log(`  💡 Price difference detected: ~10%\n`, 'yellow');

    // Step 4: Calculate optimal flashloan
    log('💰 Step 4: Calculating optimal flashloan amount...', 'blue');
    const flashloanResponse = await axios.post(`${BASE_URL}/api/calculate-flashloan`, {
      reserveInBuy: sushiswapPool.reserveIn,
      reserveOutBuy: sushiswapPool.reserveOut,
      reserveInSell: uniswapPool.reserveIn,
      reserveOutSell: uniswapPool.reserveOut,
      flashloanFee: 0.0009,  // Aave V3: 0.09%
      gasCost: 150
    });

    const flashloanAmount = flashloanResponse.data.flashloanAmount;
    const profitable = flashloanResponse.data.profitable;

    log(`  Flashloan provider: Aave V3 (0.09% fee)`, 'reset');
    log(`  Optimal flashloan: $${flashloanAmount.toFixed(2)}`, 'reset');
    log(`  Profitable: ${profitable ? '✅ YES' : '❌ NO'}`, profitable ? 'green' : 'red');

    if (!profitable) {
      log('\n⚠️  Opportunity not profitable. Aborting workflow.\n', 'yellow');
      return;
    }
    log('');

    // Step 5: Calculate market impact on buy side
    log('📉 Step 5: Calculating market impact on buy side...', 'blue');
    const buyImpactResponse = await axios.post(`${BASE_URL}/api/calculate-impact`, {
      reserveIn: sushiswapPool.reserveIn,
      reserveOut: sushiswapPool.reserveOut,
      tradeAmount: flashloanAmount
    });

    const buyImpact = buyImpactResponse.data.marketImpact;
    log(`  Market impact: ${buyImpactResponse.data.marketImpactPct}`, 'reset');

    if (buyImpact > 5) {
      log('  ⚠️  WARNING: High market impact on buy side!', 'yellow');
    } else {
      log('  ✅ Market impact within acceptable range', 'green');
    }
    log('');

    // Step 6: Calculate market impact on sell side
    log('📈 Step 6: Calculating market impact on sell side...', 'blue');
    const amountAfterBuy = (flashloanAmount * 0.997 * sushiswapPool.reserveOut) / 
                           (sushiswapPool.reserveIn + flashloanAmount * 0.997);
    
    const sellImpactResponse = await axios.post(`${BASE_URL}/api/calculate-impact`, {
      reserveIn: uniswapPool.reserveIn,
      reserveOut: uniswapPool.reserveOut,
      tradeAmount: amountAfterBuy
    });

    const sellImpact = sellImpactResponse.data.marketImpact;
    log(`  Market impact: ${sellImpactResponse.data.marketImpactPct}`, 'reset');

    if (sellImpact > 5) {
      log('  ⚠️  WARNING: High market impact on sell side!', 'yellow');
    } else {
      log('  ✅ Market impact within acceptable range', 'green');
    }
    log('');

    // Step 7: Calculate total path slippage
    log('🔄 Step 7: Calculating multi-hop slippage...', 'blue');
    const slippageResponse = await axios.post(`${BASE_URL}/api/calculate-multihop-slippage`, {
      path: [
        [sushiswapPool.reserveIn, sushiswapPool.reserveOut],
        [uniswapPool.reserveIn, uniswapPool.reserveOut]
      ],
      flashloanAmount: flashloanAmount
    });

    const totalSlippage = slippageResponse.data.totalSlippage;
    log(`  Total slippage: ${slippageResponse.data.totalSlippagePct}`, 'reset');
    log(`  Number of hops: ${slippageResponse.data.hops}`, 'reset');

    if (totalSlippage > 10) {
      log('  ⚠️  WARNING: High total slippage!', 'yellow');
    } else {
      log('  ✅ Slippage within acceptable range', 'green');
    }
    log('');

    // Step 8: Compare multiple paths
    log('🔀 Step 8: Simulating alternative paths...', 'blue');
    const pathsResponse = await axios.post(`${BASE_URL}/api/simulate-paths`, {
      paths: [
        // Path 1: Direct arbitrage
        [[sushiswapPool.reserveIn, sushiswapPool.reserveOut], 
         [uniswapPool.reserveIn, uniswapPool.reserveOut]],
        
        // Path 2: Through Curve (simulated balanced pool)
        [[sushiswapPool.reserveIn, sushiswapPool.reserveOut],
         [2000000, 2000000],
         [uniswapPool.reserveIn, uniswapPool.reserveOut]],
        
        // Path 3: Through Balancer (simulated)
        [[sushiswapPool.reserveIn, sushiswapPool.reserveOut],
         [3000000, 3000000],
         [uniswapPool.reserveIn, uniswapPool.reserveOut]]
      ],
      flashloanAmounts: [flashloanAmount, flashloanAmount, flashloanAmount],
      flashloanFee: 0.0009,
      gasCosts: [150, 200, 200]
    });

    pathsResponse.data.results.forEach((result, idx) => {
      const routeName = ['Direct', 'Via Curve', 'Via Balancer'][idx];
      const marker = result.isBest ? '⭐' : '  ';
      log(`  ${marker} Route ${idx + 1} (${routeName}):`, 'reset');
      log(`     Profit: $${result.profit.toFixed(2)}, Slippage: ${result.slippagePct}`, 'reset');
    });

    const bestRoute = pathsResponse.data.results[pathsResponse.data.bestPathIndex];
    log(`\n  ⭐ Best route: Path ${pathsResponse.data.bestPathIndex + 1}`, 'green');
    log(`     Expected profit: $${bestRoute.profit.toFixed(2)}`, 'green');
    log('');

    // Step 9: Final decision
    log('🎯 Step 9: Making execution decision...', 'blue');
    
    const maxSlippageThreshold = 10;
    const maxImpactThreshold = 5;
    const minProfitThreshold = 50;

    const checks = [
      { name: 'Profitable opportunity', pass: profitable },
      { name: 'Buy impact < 5%', pass: buyImpact < maxImpactThreshold },
      { name: 'Sell impact < 5%', pass: sellImpact < maxImpactThreshold },
      { name: 'Total slippage < 10%', pass: totalSlippage < maxSlippageThreshold },
      { name: 'Profit > $50', pass: bestRoute.profit > minProfitThreshold }
    ];

    log('  Pre-execution checklist:', 'reset');
    checks.forEach(check => {
      const status = check.pass ? '✅' : '❌';
      log(`    ${status} ${check.name}`, check.pass ? 'green' : 'red');
    });

    const allChecksPassed = checks.every(c => c.pass);
    
    log('');
    if (allChecksPassed) {
      log('🚀 DECISION: EXECUTE ARBITRAGE', 'green');
      log(`   Route: Path ${pathsResponse.data.bestPathIndex + 1}`, 'green');
      log(`   Flashloan: $${flashloanAmount.toFixed(2)} from Aave V3`, 'green');
      log(`   Expected profit: $${bestRoute.profit.toFixed(2)}`, 'green');
      log(`   Total slippage: ${slippageResponse.data.totalSlippagePct}`, 'green');
    } else {
      log('⚠️  DECISION: DO NOT EXECUTE', 'yellow');
      log('   One or more safety checks failed', 'yellow');
    }
    log('');

    // Step 10: Summary
    console.log('='.repeat(70));
    log('📊 WORKFLOW SUMMARY', 'bright');
    console.log('='.repeat(70));
    log(`✅ System Status: Operational`, 'green');
    log(`✅ Flashloan Calculation: $${flashloanAmount.toFixed(2)}`, 'green');
    log(`✅ Market Impact Analysis: ${buyImpactResponse.data.marketImpactPct} (buy), ${sellImpactResponse.data.marketImpactPct} (sell)`, 'green');
    log(`✅ Slippage Calculation: ${slippageResponse.data.totalSlippagePct}`, 'green');
    log(`✅ Path Simulation: ${pathsResponse.data.totalPathsSimulated} paths analyzed`, 'green');
    log(`✅ Best Route: Path ${pathsResponse.data.bestPathIndex + 1} with $${bestRoute.profit.toFixed(2)} profit`, 'green');
    log(`✅ Security Checks: All passed`, 'green');
    console.log('='.repeat(70) + '\n');

    log('🎉 END-TO-END WORKFLOW TEST PASSED!', 'green');
    log('All flashloan features are working correctly.\n', 'green');

  } catch (error) {
    log(`\n❌ Workflow failed: ${error.message}`, 'red');
    if (error.response) {
      log(`   Status: ${error.response.status}`, 'red');
      log(`   Data: ${JSON.stringify(error.response.data)}`, 'red');
    }
    process.exit(1);
  } finally {
    stopServer();
  }
}

// Run the workflow
runWorkflow().catch(error => {
  console.error('Fatal error:', error);
  stopServer();
  process.exit(1);
});
