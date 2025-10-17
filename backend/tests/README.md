# Backend API Testing Suite

Comprehensive unit and feature testing for the Quant Arbitrage System API with real data simulation.

## Overview

This testing suite provides complete coverage of all API endpoints with:
- **Unit Tests**: Individual endpoint validation with real-world data
- **Feature Tests**: End-to-end scenarios simulating actual arbitrage workflows
- **Automated Results**: JSON and Markdown reports with detailed metrics

## Test Structure

```
tests/
├── unit/
│   └── api.test.js                    # Unit tests for all API endpoints
├── feature/
│   └── arbitrage-scenarios.test.js    # Real-world arbitrage scenarios
├── run-all-tests.js                   # Comprehensive test runner
└── test-results/                      # Generated test results
    ├── unit-test-results-*.json
    ├── feature-test-results-*.json
    ├── comprehensive-report.json
    └── TEST-REPORT.md
```

## Running Tests

### Prerequisites

Install dependencies:
```bash
cd backend
npm install
```

The test runner will automatically start the server if it's not already running.

### Run All Tests

```bash
npm test
```

This runs both unit and feature tests, generates comprehensive reports, and displays results.

### Run Individual Test Suites

**Unit Tests Only:**
```bash
npm run test:unit
```

**Feature/Scenario Tests Only:**
```bash
npm run test:feature
```

**Manual Server Start (Optional):**
```bash
npm start
# In another terminal:
npm test
```

## Test Coverage

### Unit Tests (15 tests)

1. **Health Check** - Validates API health endpoint
2. **Get Opportunities** - Tests opportunity retrieval
3. **Get Trades** - Tests trade history retrieval
4. **Get Trades with Limit** - Tests pagination
5. **Get Statistics** - Tests stats endpoint
6. **Post Opportunity** - Creates arbitrage opportunities
7. **Post Trade** - Records trade executions
8. **Calculate Flashloan** - Tests flashloan calculation
9. **Calculate Market Impact** - Tests market impact calculation
10. **Simulate Parallel Paths** - Tests multi-path simulation
11. **Invalid Endpoint** - Tests 404 handling
12. **Missing Fields** - Tests partial data handling
13. **Concurrent Requests** - Tests parallel request handling
14. **Large Payload** - Tests large data handling
15. **Rapid Sequential Requests** - Tests high-frequency scenarios

### Feature/Scenario Tests (7 scenarios)

1. **Complete Profitable Arbitrage Workflow**
   - Detect opportunity
   - Calculate flashloan
   - Calculate market impact
   - Post opportunity
   - Execute trade
   - Verify stats

2. **Unprofitable Opportunity Detection**
   - Calculate with equal prices
   - Post unprofitable opportunity
   - Record failed trade

3. **Multi-Path Arbitrage Analysis**
   - Simulate multiple paths
   - Select best path
   - Execute multi-hop trade

4. **High-Frequency Trading Simulation**
   - Create 10 rapid opportunities
   - Execute 10 rapid trades
   - Verify all recorded

5. **Stablecoin Arbitrage (Low Slippage)**
   - Calculate stablecoin impact
   - Post low-slippage opportunity
   - Execute with minimal slippage

6. **MEV Bundle Submission Workflow**
   - Create bundle opportunities
   - Execute bundle trades
   - Verify bundle results

7. **Market Condition Change Response**
   - Detect favorable conditions
   - Recalculate after change
   - Cancel unprofitable trade

## Real Data Sources

Tests use realistic market data based on:
- **Uniswap V2**: ETH/USDT pools with ~$1.5-2.9M liquidity
- **SushiSwap**: ETH/USDT pools with comparable liquidity
- **Curve**: DAI/USDC stablecoin pools with $5M+ TVL
- **Balancer**: WBTC/ETH weighted pools

All values are representative of actual mainnet conditions.

## Test Results

### JSON Reports

Detailed JSON reports are saved to `test-results/`:

**Unit Test Results:**
```json
{
  "summary": {
    "total": 15,
    "passed": 15,
    "failed": 0,
    "successRate": "100.00%"
  },
  "tests": [
    {
      "name": "Health Check - GET /api/health",
      "success": true,
      "duration": 25,
      "timestamp": "2025-10-17T05:49:20.102Z"
    }
  ]
}
```

**Feature Test Results:**
```json
{
  "summary": {
    "total": 7,
    "passed": 7,
    "failed": 0,
    "successRate": "100.00%"
  },
  "scenarios": [
    {
      "name": "Complete Profitable Arbitrage Workflow",
      "steps": 6,
      "success": true,
      "duration": 1250
    }
  ]
}
```

### Markdown Report

A human-readable report is generated at `test-results/TEST-REPORT.md`:

```markdown
# Comprehensive API Test Report

**Generated:** 2025-10-17T05:49:20.102Z
**API Base URL:** http://localhost:3001
**Overall Status:** ✅ PASSED

## Test Suite Execution

| Suite Name | Status | Duration |
|------------|--------|----------|
| Unit Tests | ✅ PASS | 1250ms |
| Feature/Scenario Tests | ✅ PASS | 3500ms |

...
```

## Test Output Example

```
================================================================================
  API Comprehensive Test Suite Runner
================================================================================

Starting comprehensive API testing...
Target API: http://localhost:3001

Checking if server is already running...
✓ Server is already running

Running Test Suites
--------------------------------------------------------------------------------

Running Unit Tests...
✓ Health Check - GET /api/health (25ms)
✓ Get Opportunities - GET /api/opportunities (18ms)
✓ Get Trades - GET /api/trades (15ms)
...

================================================================================
API UNIT TEST RESULTS
================================================================================

Test Details:
--------------------------------------------------------------------------------
Test Name                                                Status  Duration
--------------------------------------------------------------------------------
Health Check - GET /api/health                           ✓ PASS  25ms
Get Opportunities - GET /api/opportunities               ✓ PASS  18ms
...

Summary:
  Total Tests:       15
  Passed:            15
  Failed:            0
  Success Rate:      100.00%
================================================================================

Running Feature/Scenario Tests...

Scenario 1: Complete Profitable Arbitrage Workflow
    ✓ Detect price difference between DEXs
    ✓ Calculate optimal flashloan amount
    ✓ Calculate market impact
    ✓ Create opportunity
    ✓ Execute trade
    ✓ Verify statistics updated
  ✓ Complete Profitable Arbitrage Workflow (1250ms)

...

================================================================================
COMPREHENSIVE TEST RESULTS
================================================================================

Test Suite Execution
Suite Name                               Status  Duration
--------------------------------------------------------------------------------
Unit Tests                               ✓ PASS  1250ms
Feature/Scenario Tests                   ✓ PASS  3500ms

Overall Summary
--------------------------------------------------------------------------------
  Total Tests & Scenarios: 22
  Total Passed:            22
  Total Failed:            0
  Overall Success Rate:    100.00%
================================================================================

✓ ALL TESTS PASSED - API is production-ready!
================================================================================

Comprehensive report saved to: test-results/comprehensive-report.json
Markdown report saved to: test-results/TEST-REPORT.md
```

## Environment Variables

- `API_BASE_URL`: Base URL for API (default: `http://localhost:3001`)
- `VERBOSE`: Show detailed server logs during tests (default: `false`)

Example:
```bash
API_BASE_URL=http://localhost:8080 npm test
```

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd backend && npm install
      - name: Run tests
        run: cd backend && npm test
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: backend/test-results/
```

## Adding New Tests

### Adding a Unit Test

Edit `tests/unit/api.test.js`:

```javascript
async function testYourNewEndpoint() {
  return runTest('Your Test Name', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/your-endpoint`);
    assert.strictEqual(response.status, 200);
    return { your: 'data' };
  });
}

// Add to runAllTests():
await testYourNewEndpoint();
```

### Adding a Feature Scenario

Edit `tests/feature/arbitrage-scenarios.test.js`:

```javascript
async function scenarioYourNewScenario(log) {
  // Step 1
  log('Step 1 description', { data: 'value' });
  const response = await axios.post(`${API_BASE_URL}/api/endpoint`, data);
  
  // Step 2
  log('Step 2 description', result);
  // ... more steps
}

// Add to runAllScenarios():
await runScenario('Your Scenario Name', scenarioYourNewScenario);
```

## Troubleshooting

### Server Won't Start
- Check if port 3001 is already in use
- Verify dependencies are installed
- Check server.js for errors

### Tests Timeout
- Increase `TEST_TIMEOUT` in test files
- Check network connectivity
- Verify server is responding

### Tests Fail with Connection Refused
- Ensure server is running on correct port
- Check `API_BASE_URL` environment variable
- Verify firewall settings

## Best Practices

1. **Run tests before committing**: Always run `npm test` before pushing code
2. **Review test reports**: Check generated reports for detailed insights
3. **Update tests with API changes**: Keep tests synchronized with API changes
4. **Add real data**: Use realistic values for new test scenarios
5. **Document failures**: Add comments explaining expected failures

## Support

For issues or questions about the testing suite:
1. Check test output for error messages
2. Review generated JSON reports in `test-results/`
3. Verify server logs if VERBOSE=true
4. Open an issue in the repository

## License

MIT - Same as parent project
