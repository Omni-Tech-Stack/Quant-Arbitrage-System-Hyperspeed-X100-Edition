/**
 * Unit Tests for Backend API Endpoints
 * Tests each API endpoint individually with real-world data scenarios
 */

const axios = require('axios');
const assert = require('assert');

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3001';
const TEST_TIMEOUT = 10000;

// Test utilities
class TestResults {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.tests = [];
  }

  addResult(testName, success, duration, error = null, details = {}) {
    this.tests.push({
      name: testName,
      success,
      duration,
      error,
      details,
      timestamp: new Date().toISOString()
    });
    if (success) {
      this.passed++;
    } else {
      this.failed++;
    }
  }

  getSummary() {
    return {
      total: this.tests.length,
      passed: this.passed,
      failed: this.failed,
      successRate: ((this.passed / this.tests.length) * 100).toFixed(2) + '%'
    };
  }
}

const results = new TestResults();

// Helper function to run a test
async function runTest(name, testFn, timeout = TEST_TIMEOUT) {
  const startTime = Date.now();
  try {
    const details = await Promise.race([
      testFn(),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Test timeout')), timeout)
      )
    ]);
    const duration = Date.now() - startTime;
    results.addResult(name, true, duration, null, details);
    console.log(`✓ ${name} (${duration}ms)`);
    return true;
  } catch (error) {
    const duration = Date.now() - startTime;
    results.addResult(name, false, duration, error.message);
    console.log(`✗ ${name} (${duration}ms)`);
    console.log(`  Error: ${error.message}`);
    return false;
  }
}

// Test 1: Health Check Endpoint
async function testHealthCheck() {
  return runTest('Health Check - GET /api/health', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/health`);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.strictEqual(response.data.status, 'ok', 'Status should be ok');
    assert.ok(response.data.timestamp, 'Should have timestamp');
    assert.ok(typeof response.data.uptime === 'number', 'Uptime should be a number');
    
    return {
      status: response.data.status,
      uptime: response.data.uptime,
      timestamp: response.data.timestamp
    };
  });
}

// Test 2: Get Opportunities Endpoint
async function testGetOpportunities() {
  return runTest('Get Opportunities - GET /api/opportunities', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/opportunities`);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.ok(Array.isArray(response.data), 'Response should be an array');
    
    // Validate structure if opportunities exist
    if (response.data.length > 0) {
      const opp = response.data[0];
      assert.ok(opp.id, 'Opportunity should have id');
      assert.ok(opp.timestamp, 'Opportunity should have timestamp');
      assert.ok(opp.expectedProfit, 'Opportunity should have expectedProfit');
    }
    
    return {
      count: response.data.length,
      sample: response.data[0] || 'No opportunities'
    };
  });
}

// Test 3: Get Trades Endpoint
async function testGetTrades() {
  return runTest('Get Trades - GET /api/trades', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/trades`);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.ok(Array.isArray(response.data), 'Response should be an array');
    
    return {
      count: response.data.length
    };
  });
}

// Test 4: Get Trades with Limit
async function testGetTradesWithLimit() {
  return runTest('Get Trades with Limit - GET /api/trades?limit=10', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/trades?limit=10`);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.ok(Array.isArray(response.data), 'Response should be an array');
    assert.ok(response.data.length <= 10, 'Should return at most 10 trades');
    
    return {
      count: response.data.length,
      requestedLimit: 10
    };
  });
}

// Test 5: Get Statistics Endpoint
async function testGetStats() {
  return runTest('Get Statistics - GET /api/stats', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/stats`);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.ok(typeof response.data.totalTrades === 'number', 'totalTrades should be a number');
    assert.ok(typeof response.data.successfulTrades === 'number', 'successfulTrades should be a number');
    assert.ok(typeof response.data.totalProfit === 'number', 'totalProfit should be a number');
    assert.ok(typeof response.data.avgSlippage === 'number', 'avgSlippage should be a number');
    
    return response.data;
  });
}

// Test 6: Post Opportunity
async function testPostOpportunity() {
  return runTest('Post Opportunity - POST /api/opportunities', async () => {
    const opportunityData = {
      pool1: 'UniswapV2',
      pool2: 'SushiSwap',
      pair: 'ETH/USDT',
      expectedProfit: 125.50,
      slippage: 0.0045,
      confidence: 85.5,
      flashloanAmount: 50000,
      flashloanFee: '0.0009',
      marketImpact: 2.3,
      estimatedGas: 180000
    };
    
    const response = await axios.post(`${API_BASE_URL}/api/opportunities`, opportunityData);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.strictEqual(response.data.success, true, 'Should return success: true');
    assert.ok(response.data.id, 'Should return an id');
    
    return {
      id: response.data.id,
      opportunityData
    };
  });
}

// Test 7: Post Trade
async function testPostTrade() {
  return runTest('Post Trade - POST /api/trades', async () => {
    const tradeData = {
      opportunityId: Date.now() - 1000,
      pool1: 'UniswapV3',
      pool2: 'Curve',
      pair: 'DAI/USDC',
      success: true,
      profit: 87.25,
      actualSlippage: 0.0032,
      gasUsed: 165000,
      flashloanAmount: 45000,
      flashloanFee: '0.0009',
      marketImpact: 1.8,
      executionTime: '1250ms'
    };
    
    const response = await axios.post(`${API_BASE_URL}/api/trades`, tradeData);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.strictEqual(response.data.success, true, 'Should return success: true');
    assert.ok(response.data.id, 'Should return an id');
    
    return {
      id: response.data.id,
      tradeData
    };
  });
}

// Test 8: Calculate Flashloan Endpoint
async function testCalculateFlashloan() {
  return runTest('Calculate Flashloan - POST /api/calculate-flashloan', async () => {
    const requestData = {
      reserveInBuy: 1000000,
      reserveOutBuy: 2000000,
      reserveInSell: 2100000,
      reserveOutSell: 1000000,
      flashloanFee: 0.0009,
      gasCost: 100
    };
    
    const response = await axios.post(`${API_BASE_URL}/api/calculate-flashloan`, requestData);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.ok(typeof response.data.flashloanAmount === 'number', 'flashloanAmount should be a number');
    assert.ok(response.data.timestamp, 'Should have timestamp');
    assert.strictEqual(response.data.flashloanFee, 0.0009, 'Should return flashloan fee');
    
    return response.data;
  });
}

// Test 9: Calculate Market Impact Endpoint
async function testCalculateImpact() {
  return runTest('Calculate Market Impact - POST /api/calculate-impact', async () => {
    const requestData = {
      reserveIn: 1000000,
      reserveOut: 2000000,
      tradeAmount: 50000
    };
    
    const response = await axios.post(`${API_BASE_URL}/api/calculate-impact`, requestData);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.ok(typeof response.data.marketImpact === 'number', 'marketImpact should be a number');
    assert.ok(response.data.timestamp, 'Should have timestamp');
    assert.strictEqual(response.data.reserveIn, requestData.reserveIn, 'Should echo reserveIn');
    
    return response.data;
  });
}

// Test 10: Simulate Parallel Paths Endpoint
async function testSimulatePaths() {
  return runTest('Simulate Parallel Paths - POST /api/simulate-paths', async () => {
    const requestData = {
      paths: [
        [[1000000, 2000000], [2100000, 1000000]],
        [[1000000, 1500000], [1550000, 1000000]],
        [[1000000, 3000000], [3200000, 1000000]]
      ],
      flashloanAmounts: [30000, 30000, 30000],
      flashloanFee: 0.0009,
      gasCosts: [100, 100, 100]
    };
    
    const response = await axios.post(`${API_BASE_URL}/api/simulate-paths`, requestData);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.ok(Array.isArray(response.data.results), 'results should be an array');
    assert.ok(typeof response.data.bestPathIndex === 'number', 'bestPathIndex should be a number');
    assert.ok(response.data.timestamp, 'Should have timestamp');
    
    return response.data;
  });
}

// Test 11: Invalid Endpoint (404)
async function testInvalidEndpoint() {
  return runTest('Invalid Endpoint - GET /api/invalid', async () => {
    try {
      await axios.get(`${API_BASE_URL}/api/invalid`);
      throw new Error('Should have returned 404');
    } catch (error) {
      assert.strictEqual(error.response.status, 404, 'Status should be 404');
      return {
        status: 404,
        message: 'Endpoint not found (expected)'
      };
    }
  });
}

// Test 12: POST with Missing Required Fields
async function testPostOpportunityMissingFields() {
  return runTest('Post Opportunity with Missing Fields - POST /api/opportunities', async () => {
    const incompleteData = {
      pool1: 'UniswapV2'
      // Missing other required fields
    };
    
    const response = await axios.post(`${API_BASE_URL}/api/opportunities`, incompleteData);
    
    // Even with missing fields, API should accept it (based on current implementation)
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.strictEqual(response.data.success, true, 'Should return success: true');
    
    return {
      accepted: true,
      message: 'API accepts partial data'
    };
  });
}

// Test 13: Concurrent Requests
async function testConcurrentRequests() {
  return runTest('Concurrent Requests - Multiple GET /api/health', async () => {
    const promises = Array(10).fill(null).map(() => 
      axios.get(`${API_BASE_URL}/api/health`)
    );
    
    const responses = await Promise.all(promises);
    
    responses.forEach(response => {
      assert.strictEqual(response.status, 200, 'All responses should be 200');
      assert.strictEqual(response.data.status, 'ok', 'All should return ok status');
    });
    
    return {
      requestCount: 10,
      successCount: responses.length
    };
  });
}

// Test 14: Large Payload
async function testLargePayload() {
  return runTest('Large Payload - POST /api/opportunities', async () => {
    // Create a large opportunity with extensive data
    const largeOpportunity = {
      pool1: 'UniswapV2',
      pool2: 'SushiSwap',
      pair: 'ETH/USDT',
      expectedProfit: 1250.50,
      slippage: 0.0045,
      confidence: 85.5,
      flashloanAmount: 500000,
      flashloanFee: '0.0009',
      marketImpact: 2.3,
      estimatedGas: 180000,
      metadata: {
        pools: Array(100).fill(null).map((_, i) => ({
          id: `pool-${i}`,
          tvl: Math.random() * 1000000,
          volume24h: Math.random() * 500000
        }))
      }
    };
    
    const response = await axios.post(`${API_BASE_URL}/api/opportunities`, largeOpportunity);
    
    assert.strictEqual(response.status, 200, 'Status should be 200');
    assert.strictEqual(response.data.success, true, 'Should handle large payload');
    
    return {
      payloadSize: JSON.stringify(largeOpportunity).length,
      accepted: true
    };
  });
}

// Test 15: Rapid Sequential Requests
async function testRapidSequentialRequests() {
  return runTest('Rapid Sequential Requests - POST opportunities', async () => {
    const startTime = Date.now();
    const count = 20;
    
    for (let i = 0; i < count; i++) {
      const opportunity = {
        pool1: 'UniswapV2',
        pool2: 'SushiSwap',
        pair: 'ETH/USDT',
        expectedProfit: Math.random() * 100,
        slippage: Math.random() * 0.01,
        confidence: 70 + Math.random() * 30,
        flashloanAmount: 10000 + Math.random() * 50000,
        flashloanFee: '0.0009',
        marketImpact: Math.random() * 5,
        estimatedGas: 150000 + Math.random() * 50000
      };
      
      await axios.post(`${API_BASE_URL}/api/opportunities`, opportunity);
    }
    
    const duration = Date.now() - startTime;
    
    return {
      requestCount: count,
      totalDuration: duration,
      avgPerRequest: (duration / count).toFixed(2) + 'ms'
    };
  });
}

// Display results in a formatted table
function displayResults() {
  console.log('\n' + '='.repeat(80));
  console.log('API UNIT TEST RESULTS');
  console.log('='.repeat(80));
  console.log('\nTest Details:');
  console.log('-'.repeat(80));
  console.log('Test Name'.padEnd(55), 'Status', 'Duration');
  console.log('-'.repeat(80));
  
  results.tests.forEach(test => {
    const status = test.success ? '✓ PASS' : '✗ FAIL';
    const statusColor = test.success ? '\x1b[32m' : '\x1b[31m';
    const resetColor = '\x1b[0m';
    
    console.log(
      test.name.padEnd(55),
      `${statusColor}${status}${resetColor}`,
      `${test.duration}ms`
    );
    
    if (!test.success) {
      console.log(`  Error: ${test.error}`);
    }
  });
  
  const summary = results.getSummary();
  console.log('-'.repeat(80));
  console.log('\nSummary:');
  console.log(`  Total Tests:       ${summary.total}`);
  console.log(`  Passed:            \x1b[32m${summary.passed}\x1b[0m`);
  console.log(`  Failed:            \x1b[31m${summary.failed}\x1b[0m`);
  console.log(`  Success Rate:      ${summary.successRate}`);
  console.log('='.repeat(80));
  
  return summary;
}

// Main test runner
async function runAllTests() {
  console.log('\nStarting API Unit Tests...');
  console.log(`API Base URL: ${API_BASE_URL}\n`);
  
  try {
    // Run all tests
    await testHealthCheck();
    await testGetOpportunities();
    await testGetTrades();
    await testGetTradesWithLimit();
    await testGetStats();
    await testPostOpportunity();
    await testPostTrade();
    await testCalculateFlashloan();
    await testCalculateImpact();
    await testSimulatePaths();
    await testInvalidEndpoint();
    await testPostOpportunityMissingFields();
    await testConcurrentRequests();
    await testLargePayload();
    await testRapidSequentialRequests();
    
    // Display results
    const summary = displayResults();
    
    // Export results as JSON
    const fs = require('fs');
    const path = require('path');
    const resultsDir = path.join(__dirname, '../../test-results');
    if (!fs.existsSync(resultsDir)) {
      fs.mkdirSync(resultsDir, { recursive: true });
    }
    
    const resultsFile = path.join(resultsDir, `unit-test-results-${Date.now()}.json`);
    fs.writeFileSync(resultsFile, JSON.stringify({
      summary,
      tests: results.tests,
      timestamp: new Date().toISOString(),
      apiBaseUrl: API_BASE_URL
    }, null, 2));
    console.log(`\nResults saved to: ${resultsFile}`);
    
    // Exit with appropriate code
    process.exit(summary.failed > 0 ? 1 : 0);
    
  } catch (error) {
    console.error('\nFatal error during test execution:', error.message);
    process.exit(1);
  }
}

// Export for use in other test files
module.exports = {
  runAllTests,
  testHealthCheck,
  testGetOpportunities,
  testGetTrades,
  testGetStats,
  results
};

// Run tests if this file is executed directly
if (require.main === module) {
  runAllTests();
}
