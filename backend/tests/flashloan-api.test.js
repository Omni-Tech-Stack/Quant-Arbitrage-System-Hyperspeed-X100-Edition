/**
 * Flashloan API Integration Tests
 * Tests all flashloan-related API endpoints
 */

const axios = require('axios');
const { spawn } = require('child_process');

const BASE_URL = 'http://localhost:3001';
let serverProcess;

// Start the server
function startServer() {
  return new Promise((resolve, reject) => {
    serverProcess = spawn(process.execPath, ['server.js'], {
      cwd: __dirname + '/..',
      env: { ...process.env, DEMO_MODE: 'true' }
    });

    serverProcess.stdout.on('data', (data) => {
      const output = data.toString();
      if (output.includes('running on port')) {
        setTimeout(resolve, 500); // Give it a bit more time to fully initialize
      }
    });

    serverProcess.stderr.on('data', (data) => {
      console.error('Server error:', data.toString());
    });

    setTimeout(() => reject(new Error('Server startup timeout')), 10000);
  });
}

// Stop the server
function stopServer() {
  if (serverProcess) {
    serverProcess.kill();
  }
}

// Test results tracking
let testsPassed = 0;
let testsFailed = 0;

async function test(name, fn) {
  try {
    await fn();
    console.log(`✓ ${name}`);
    testsPassed++;
  } catch (error) {
    console.log(`✗ ${name}`);
    console.log(`  Error: ${error.message}`);
    testsFailed++;
  }
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

async function runTests() {
  console.log('\n=== FLASHLOAN API INTEGRATION TESTS ===\n');

  try {
    // Start server
    console.log('Starting server...');
    await startServer();
    console.log('Server started successfully\n');

    // Test 1: Health check
    await test('Health check endpoint', async () => {
      const response = await axios.get(`${BASE_URL}/api/health`);
      assert(response.status === 200, 'Should return 200 status');
      assert(response.data.status === 'ok', 'Should return ok status');
    });

    // Test 2: Calculate flashloan amount
    await test('Calculate flashloan amount for profitable arbitrage', async () => {
      const response = await axios.post(`${BASE_URL}/api/calculate-flashloan`, {
        reserveInBuy: 1000000,
        reserveOutBuy: 2000000,
        reserveInSell: 2100000,
        reserveOutSell: 1000000,
        flashloanFee: 0.0009,
        gasCost: 100
      });

      assert(response.status === 200, 'Should return 200 status');
      assert(response.data.success === true, 'Should be successful');
      assert(typeof response.data.flashloanAmount === 'number', 'Should return flashloan amount');
      assert(response.data.flashloanAmount >= 0, 'Flashloan amount should be non-negative');
      assert(response.data.profitable !== undefined, 'Should indicate if profitable');
    });

    // Test 3: Calculate flashloan amount for unprofitable arbitrage
    await test('Calculate flashloan amount returns zero for unprofitable', async () => {
      const response = await axios.post(`${BASE_URL}/api/calculate-flashloan`, {
        reserveInBuy: 1000000,
        reserveOutBuy: 1000000,
        reserveInSell: 1000000,
        reserveOutSell: 1000000,
        flashloanFee: 0.0009,
        gasCost: 100
      });

      assert(response.status === 200, 'Should return 200 status');
      assert(response.data.success === true, 'Should be successful');
      assert(response.data.flashloanAmount === 0, 'Flashloan amount should be zero');
      assert(response.data.profitable === false, 'Should not be profitable');
    });

    // Test 4: Calculate flashloan with missing parameters
    await test('Calculate flashloan handles missing parameters', async () => {
      try {
        await axios.post(`${BASE_URL}/api/calculate-flashloan`, {
          reserveInBuy: 1000000
          // Missing other required parameters
        });
        throw new Error('Should have thrown an error');
      } catch (error) {
        assert(error.response.status === 400, 'Should return 400 status');
        assert(error.response.data.error, 'Should return error message');
      }
    });

    // Test 5: Calculate market impact
    await test('Calculate market impact for trade', async () => {
      const response = await axios.post(`${BASE_URL}/api/calculate-impact`, {
        reserveIn: 1000000,
        reserveOut: 2000000,
        tradeAmount: 50000
      });

      assert(response.status === 200, 'Should return 200 status');
      assert(response.data.success === true, 'Should be successful');
      assert(typeof response.data.marketImpact === 'number', 'Should return market impact');
      assert(response.data.marketImpact >= 0, 'Market impact should be non-negative');
      assert(response.data.marketImpactPct, 'Should include percentage format');
    });

    // Test 6: Calculate market impact with varying sizes
    await test('Market impact increases with trade size', async () => {
      const smallResponse = await axios.post(`${BASE_URL}/api/calculate-impact`, {
        reserveIn: 1000000,
        reserveOut: 2000000,
        tradeAmount: 10000
      });

      const largeResponse = await axios.post(`${BASE_URL}/api/calculate-impact`, {
        reserveIn: 1000000,
        reserveOut: 2000000,
        tradeAmount: 100000
      });

      assert(largeResponse.data.marketImpact > smallResponse.data.marketImpact,
        'Larger trade should have greater market impact');
    });

    // Test 7: Calculate market impact with missing parameters
    await test('Calculate market impact handles missing parameters', async () => {
      try {
        await axios.post(`${BASE_URL}/api/calculate-impact`, {
          reserveIn: 1000000
          // Missing other parameters
        });
        throw new Error('Should have thrown an error');
      } catch (error) {
        assert(error.response.status === 400, 'Should return 400 status');
        assert(error.response.data.error, 'Should return error message');
      }
    });

    // Test 8: Calculate multi-hop slippage
    await test('Calculate multi-hop slippage for path', async () => {
      const response = await axios.post(`${BASE_URL}/api/calculate-multihop-slippage`, {
        path: [
          [1000000, 2000000],
          [2000000, 1000000],
          [1000000, 500000]
        ],
        flashloanAmount: 25000
      });

      assert(response.status === 200, 'Should return 200 status');
      assert(response.data.success === true, 'Should be successful');
      assert(typeof response.data.totalSlippage === 'number', 'Should return total slippage');
      assert(response.data.totalSlippage >= 0, 'Total slippage should be non-negative');
      assert(response.data.hops === 3, 'Should report correct number of hops');
    });

    // Test 9: Multi-hop slippage with invalid path
    await test('Multi-hop slippage handles invalid path', async () => {
      try {
        await axios.post(`${BASE_URL}/api/calculate-multihop-slippage`, {
          path: [],
          flashloanAmount: 25000
        });
        throw new Error('Should have thrown an error');
      } catch (error) {
        assert(error.response.status === 400, 'Should return 400 status');
        assert(error.response.data.error, 'Should return error message');
      }
    });

    // Test 10: Simulate parallel paths
    await test('Simulate parallel flashloan paths', async () => {
      const response = await axios.post(`${BASE_URL}/api/simulate-paths`, {
        paths: [
          [[1000000, 2000000], [2100000, 1000000]],
          [[1000000, 3000000], [3200000, 1000000]],
          [[1000000, 1000000], [1000000, 1000000]]
        ],
        flashloanAmounts: [30000, 30000, 30000],
        flashloanFee: 0.0009,
        gasCosts: [100, 100, 100]
      });

      assert(response.status === 200, 'Should return 200 status');
      assert(response.data.success === true, 'Should be successful');
      assert(Array.isArray(response.data.results), 'Should return results array');
      assert(response.data.results.length === 3, 'Should return 3 results');
      assert(typeof response.data.bestPathIndex === 'number', 'Should identify best path');
      assert(typeof response.data.bestProfit === 'number', 'Should return best profit');

      // Verify result structure
      response.data.results.forEach((result, idx) => {
        assert(result.pathIndex === idx, `Path index should be ${idx}`);
        assert(typeof result.profit === 'number', 'Should have profit');
        assert(typeof result.slippage === 'number', 'Should have slippage');
        assert(typeof result.isBest === 'boolean', 'Should indicate if best');
      });
    });

    // Test 11: Simulate paths with mismatched arrays
    await test('Simulate paths handles mismatched array lengths', async () => {
      try {
        await axios.post(`${BASE_URL}/api/simulate-paths`, {
          paths: [
            [[1000000, 2000000], [2100000, 1000000]],
            [[1000000, 3000000], [3200000, 1000000]]
          ],
          flashloanAmounts: [30000, 30000, 30000], // Length mismatch
          flashloanFee: 0.0009,
          gasCosts: [100, 100]
        });
        throw new Error('Should have thrown an error');
      } catch (error) {
        assert(error.response.status === 400, 'Should return 400 status');
        assert(error.response.data.error, 'Should return error message');
      }
    });

    // Test 12: Comprehensive workflow
    await test('Complete flashloan workflow integration', async () => {
      // Step 1: Calculate optimal flashloan
      const flashloanRes = await axios.post(`${BASE_URL}/api/calculate-flashloan`, {
        reserveInBuy: 1000000,
        reserveOutBuy: 2000000,
        reserveInSell: 2100000,
        reserveOutSell: 1000000,
        flashloanFee: 0.0009,
        gasCost: 100
      });

      const flashloanAmount = flashloanRes.data.flashloanAmount;

      if (flashloanAmount > 0) {
        // Step 2: Calculate market impact on buy side
        const buyImpactRes = await axios.post(`${BASE_URL}/api/calculate-impact`, {
          reserveIn: 1000000,
          reserveOut: 2000000,
          tradeAmount: flashloanAmount
        });

        // Step 3: Calculate multi-hop slippage
        const slippageRes = await axios.post(`${BASE_URL}/api/calculate-multihop-slippage`, {
          path: [
            [1000000, 2000000],
            [2100000, 1000000]
          ],
          flashloanAmount: flashloanAmount
        });

        assert(buyImpactRes.data.success, 'Market impact calculation should succeed');
        assert(slippageRes.data.success, 'Slippage calculation should succeed');
        assert(buyImpactRes.data.marketImpact >= 0, 'Impact should be non-negative');
        assert(slippageRes.data.totalSlippage >= 0, 'Slippage should be non-negative');
      }
    });

    // Test 13: Test with Aave V3 fee
    await test('Calculate flashloan with Aave V3 fee (0.09%)', async () => {
      const response = await axios.post(`${BASE_URL}/api/calculate-flashloan`, {
        reserveInBuy: 1000000,
        reserveOutBuy: 2000000,
        reserveInSell: 2100000,
        reserveOutSell: 1000000,
        flashloanFee: 0.0009, // Aave V3
        gasCost: 100
      });

      assert(response.data.flashloanFee === 0.0009, 'Should use Aave V3 fee');
    });

    // Test 14: Test with dYdX fee (0%)
    await test('Calculate flashloan with dYdX fee (0%)', async () => {
      const response = await axios.post(`${BASE_URL}/api/calculate-flashloan`, {
        reserveInBuy: 1000000,
        reserveOutBuy: 2000000,
        reserveInSell: 2100000,
        reserveOutSell: 1000000,
        flashloanFee: 0, // dYdX
        gasCost: 100
      });

      assert(response.data.success === true, 'Should calculate with 0% fee');
      assert(response.data.flashloanFee === 0, 'Should use 0% fee');
    });

    // Test 15: High gas cost scenario
    await test('Flashloan calculation with high gas costs', async () => {
      const response = await axios.post(`${BASE_URL}/api/calculate-flashloan`, {
        reserveInBuy: 1000000,
        reserveOutBuy: 2000000,
        reserveInSell: 2100000,
        reserveOutSell: 1000000,
        flashloanFee: 0.0009,
        gasCost: 10000 // Very high gas
      });

      assert(response.data.success === true, 'Should calculate even with high gas');
      // High gas might make it unprofitable
    });

  } catch (error) {
    console.error('\n❌ Test suite error:', error.message);
    testsFailed++;
  } finally {
    // Stop server
    stopServer();

    // Print summary
    console.log('\n=== TEST SUMMARY ===');
    console.log(`Tests passed: ${testsPassed}`);
    console.log(`Tests failed: ${testsFailed}`);
    console.log(`Total tests: ${testsPassed + testsFailed}`);

    if (testsFailed === 0) {
      console.log('\n✓ ALL TESTS PASSED - Flashloan API integration verified!\n');
      process.exit(0);
    } else {
      console.log('\n✗ SOME TESTS FAILED\n');
      process.exit(1);
    }
  }
}

// Run the tests
runTests().catch(error => {
  console.error('Fatal error:', error);
  stopServer();
  process.exit(1);
});
