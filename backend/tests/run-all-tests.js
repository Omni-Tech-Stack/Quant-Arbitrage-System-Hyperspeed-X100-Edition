#!/usr/bin/env node
/**
 * Comprehensive Test Runner for Backend API
 * Runs all unit and feature tests, displays results in a formatted manner
 */

const axios = require('axios');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3001';
const SERVER_STARTUP_WAIT = 3000;
const COLORS = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

let serverProcess = null;
let serverStarted = false;

// Helper functions
function log(message, color = COLORS.reset) {
  console.log(`${color}${message}${COLORS.reset}`);
}

function printHeader(title) {
  console.log('\n' + '='.repeat(80));
  log(`  ${title}`, COLORS.bright + COLORS.cyan);
  console.log('='.repeat(80) + '\n');
}

function printSection(title) {
  log(`\n${title}`, COLORS.bright + COLORS.blue);
  console.log('-'.repeat(80));
}

// Check if server is running
async function checkServerHealth(maxRetries = 10, delay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/health`, { timeout: 2000 });
      if (response.data.status === 'ok') {
        return true;
      }
    } catch (error) {
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  return false;
}

// Start server if not running
async function ensureServerRunning() {
  log('Checking if server is already running...', COLORS.cyan);
  
  const isRunning = await checkServerHealth(2, 500);
  
  if (isRunning) {
    log('✓ Server is already running', COLORS.green);
    serverStarted = false;
    return true;
  }
  
  log('Server not detected. Starting server...', COLORS.yellow);
  
  // Start the server
  serverProcess = spawn('node', ['server.js'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'pipe',
    env: { ...process.env, DEMO_MODE: 'false' }
  });
  
  serverProcess.stdout.on('data', (data) => {
    // Show server logs in VERBOSE mode or in CI for debugging
    if (process.env.VERBOSE || process.env.CI) {
      console.log(`[Server] ${data.toString().trim()}`);
    }
  });
  
  serverProcess.stderr.on('data', (data) => {
    console.error(`[Server Error] ${data.toString().trim()}`);
  });
  
  log(`Waiting ${SERVER_STARTUP_WAIT}ms for server to start...`, COLORS.cyan);
  await new Promise(resolve => setTimeout(resolve, SERVER_STARTUP_WAIT));
  
  const isNowRunning = await checkServerHealth(5, 1000);
  
  if (isNowRunning) {
    log('✓ Server started successfully', COLORS.green);
    serverStarted = true;
    return true;
  } else {
    log('✗ Failed to start server', COLORS.red);
    return false;
  }
}

// Stop server if we started it
function stopServer() {
  if (serverStarted && serverProcess) {
    log('\nStopping server...', COLORS.cyan);
    serverProcess.kill();
    serverProcess = null;
    log('✓ Server stopped', COLORS.green);
  }
}

// Run a test suite
function runTestSuite(suiteName, scriptPath) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const testProcess = spawn('node', [scriptPath], {
      cwd: path.dirname(scriptPath),
      stdio: 'inherit',
      env: { ...process.env, API_BASE_URL }
    });
    
    testProcess.on('close', (code) => {
      const duration = Date.now() - startTime;
      resolve({ suiteName, success: code === 0, duration, code });
    });
    
    testProcess.on('error', (error) => {
      const duration = Date.now() - startTime;
      reject({ suiteName, success: false, duration, error: error.message });
    });
  });
}

// Load and aggregate results
function aggregateResults() {
  const resultsDir = path.join(__dirname, '../test-results');
  
  if (!fs.existsSync(resultsDir)) {
    return null;
  }
  
  const files = fs.readdirSync(resultsDir);
  const unitResults = files.filter(f => f.startsWith('unit-test-results')).sort().pop();
  const featureResults = files.filter(f => f.startsWith('feature-test-results')).sort().pop();
  
  const results = {
    unit: null,
    feature: null
  };
  
  if (unitResults) {
    const unitPath = path.join(resultsDir, unitResults);
    results.unit = JSON.parse(fs.readFileSync(unitPath, 'utf8'));
  }
  
  if (featureResults) {
    const featurePath = path.join(resultsDir, featureResults);
    results.feature = JSON.parse(fs.readFileSync(featurePath, 'utf8'));
  }
  
  return results;
}

// Display comprehensive results
function displayComprehensiveResults(suiteResults, aggregatedResults) {
  printHeader('COMPREHENSIVE TEST RESULTS');
  
  // Test Suite Execution Summary
  printSection('Test Suite Execution');
  console.log('Suite Name'.padEnd(40), 'Status', 'Duration');
  console.log('-'.repeat(80));
  
  let allPassed = true;
  suiteResults.forEach(result => {
    const status = result.success ? '✓ PASS' : '✗ FAIL';
    const statusColor = result.success ? COLORS.green : COLORS.red;
    
    console.log(
      result.suiteName.padEnd(40),
      `${statusColor}${status}${COLORS.reset}`,
      `${result.duration}ms`
    );
    
    if (!result.success) {
      allPassed = false;
    }
  });
  
  // Detailed Results
  if (aggregatedResults) {
    if (aggregatedResults.unit) {
      printSection('Unit Tests Summary');
      const unit = aggregatedResults.unit.summary;
      console.log(`  Total Tests:       ${unit.total}`);
      console.log(`  Passed:            ${COLORS.green}${unit.passed}${COLORS.reset}`);
      console.log(`  Failed:            ${COLORS.red}${unit.failed}${COLORS.reset}`);
      console.log(`  Success Rate:      ${unit.successRate}`);
    }
    
    if (aggregatedResults.feature) {
      printSection('Feature/Scenario Tests Summary');
      const feature = aggregatedResults.feature.summary;
      console.log(`  Total Scenarios:   ${feature.total}`);
      console.log(`  Passed:            ${COLORS.green}${feature.passed}${COLORS.reset}`);
      console.log(`  Failed:            ${COLORS.red}${feature.failed}${COLORS.reset}`);
      console.log(`  Success Rate:      ${feature.successRate}`);
    }
  }
  
  // Overall Summary
  printSection('Overall Summary');
  
  if (aggregatedResults && aggregatedResults.unit && aggregatedResults.feature) {
    const totalTests = aggregatedResults.unit.summary.total + aggregatedResults.feature.summary.total;
    const totalPassed = aggregatedResults.unit.summary.passed + aggregatedResults.feature.summary.passed;
    const totalFailed = aggregatedResults.unit.summary.failed + aggregatedResults.feature.summary.failed;
    const overallRate = ((totalPassed / totalTests) * 100).toFixed(2) + '%';
    
    console.log(`  Total Tests & Scenarios: ${totalTests}`);
    console.log(`  Total Passed:            ${COLORS.green}${totalPassed}${COLORS.reset}`);
    console.log(`  Total Failed:            ${COLORS.red}${totalFailed}${COLORS.reset}`);
    console.log(`  Overall Success Rate:    ${overallRate}`);
  }
  
  console.log('\n' + '='.repeat(80));
  
  if (allPassed) {
    log('\n✓ ALL TESTS PASSED - API is production-ready!', COLORS.bright + COLORS.green);
  } else {
    log('\n✗ SOME TESTS FAILED - Please review the errors above', COLORS.bright + COLORS.red);
  }
  
  console.log('='.repeat(80) + '\n');
  
  // Export comprehensive report
  const resultsDir = path.join(__dirname, '../test-results');
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true });
  }
  
  const reportPath = path.join(resultsDir, 'comprehensive-report.json');
  fs.writeFileSync(reportPath, JSON.stringify({
    suiteResults,
    aggregatedResults,
    timestamp: new Date().toISOString(),
    apiBaseUrl: API_BASE_URL,
    allPassed
  }, null, 2));
  
  log(`Comprehensive report saved to: ${reportPath}`, COLORS.cyan);
  
  // Also create a markdown report
  createMarkdownReport(suiteResults, aggregatedResults, allPassed);
  
  return allPassed;
}

// Create markdown report
function createMarkdownReport(suiteResults, aggregatedResults, allPassed) {
  const resultsDir = path.join(__dirname, '../test-results');
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true });
  }
  
  const reportPath = path.join(resultsDir, 'TEST-REPORT.md');
  
  let markdown = `# Comprehensive API Test Report\n\n`;
  markdown += `**Generated:** ${new Date().toISOString()}\n`;
  markdown += `**API Base URL:** ${API_BASE_URL}\n`;
  markdown += `**Overall Status:** ${allPassed ? '✅ PASSED' : '❌ FAILED'}\n\n`;
  
  markdown += `## Test Suite Execution\n\n`;
  markdown += `| Suite Name | Status | Duration |\n`;
  markdown += `|------------|--------|----------|\n`;
  
  suiteResults.forEach(result => {
    const status = result.success ? '✅ PASS' : '❌ FAIL';
    markdown += `| ${result.suiteName} | ${status} | ${result.duration}ms |\n`;
  });
  
  if (aggregatedResults && aggregatedResults.unit) {
    markdown += `\n## Unit Tests\n\n`;
    const unit = aggregatedResults.unit.summary;
    markdown += `- **Total Tests:** ${unit.total}\n`;
    markdown += `- **Passed:** ${unit.passed}\n`;
    markdown += `- **Failed:** ${unit.failed}\n`;
    markdown += `- **Success Rate:** ${unit.successRate}\n\n`;
    
    markdown += `### Unit Test Details\n\n`;
    markdown += `| Test Name | Status | Duration |\n`;
    markdown += `|-----------|--------|----------|\n`;
    
    aggregatedResults.unit.tests.forEach(test => {
      const status = test.success ? '✅' : '❌';
      markdown += `| ${test.name} | ${status} | ${test.duration}ms |\n`;
    });
  }
  
  if (aggregatedResults && aggregatedResults.feature) {
    markdown += `\n## Feature/Scenario Tests\n\n`;
    const feature = aggregatedResults.feature.summary;
    markdown += `- **Total Scenarios:** ${feature.total}\n`;
    markdown += `- **Passed:** ${feature.passed}\n`;
    markdown += `- **Failed:** ${feature.failed}\n`;
    markdown += `- **Success Rate:** ${feature.successRate}\n\n`;
    
    markdown += `### Scenario Details\n\n`;
    markdown += `| Scenario Name | Status | Steps | Duration |\n`;
    markdown += `|---------------|--------|-------|----------|\n`;
    
    aggregatedResults.feature.scenarios.forEach(scenario => {
      const status = scenario.success ? '✅' : '❌';
      markdown += `| ${scenario.name} | ${status} | ${scenario.steps.length} | ${scenario.duration}ms |\n`;
    });
  }
  
  if (aggregatedResults && aggregatedResults.unit && aggregatedResults.feature) {
    markdown += `\n## Overall Summary\n\n`;
    const totalTests = aggregatedResults.unit.summary.total + aggregatedResults.feature.summary.total;
    const totalPassed = aggregatedResults.unit.summary.passed + aggregatedResults.feature.summary.passed;
    const totalFailed = aggregatedResults.unit.summary.failed + aggregatedResults.feature.summary.failed;
    const overallRate = ((totalPassed / totalTests) * 100).toFixed(2) + '%';
    
    markdown += `- **Total Tests & Scenarios:** ${totalTests}\n`;
    markdown += `- **Total Passed:** ${totalPassed}\n`;
    markdown += `- **Total Failed:** ${totalFailed}\n`;
    markdown += `- **Overall Success Rate:** ${overallRate}\n\n`;
  }
  
  markdown += `## Conclusion\n\n`;
  if (allPassed) {
    markdown += `✅ **All tests passed!** The API is production-ready and all endpoints are functioning correctly.\n`;
  } else {
    markdown += `❌ **Some tests failed.** Please review the failures and fix any issues before deploying to production.\n`;
  }
  
  fs.writeFileSync(reportPath, markdown);
  log(`Markdown report saved to: ${reportPath}`, COLORS.cyan);
}

// Main execution
async function main() {
  printHeader('API Comprehensive Test Suite Runner');
  
  log('Starting comprehensive API testing...', COLORS.bright);
  log(`Target API: ${API_BASE_URL}\n`, COLORS.cyan);
  
  try {
    // Step 0: Ensure test-results directory exists
    const resultsDir = path.join(__dirname, '../test-results');
    if (!fs.existsSync(resultsDir)) {
      fs.mkdirSync(resultsDir, { recursive: true });
      log('Created test-results directory', COLORS.cyan);
    }
    
    // Step 1: Ensure server is running
    const serverReady = await ensureServerRunning();
    if (!serverReady) {
      log('\n✗ Cannot proceed without a running server', COLORS.red);
      process.exit(1);
    }
    
    // Step 2: Run test suites
    printSection('Running Test Suites');
    
    const suiteResults = [];
    
    log('\nRunning Unit Tests...', COLORS.cyan);
    const unitResult = await runTestSuite(
      'Unit Tests',
      path.join(__dirname, 'unit/api.test.js')
    );
    suiteResults.push(unitResult);
    
    log('\nRunning Feature/Scenario Tests...', COLORS.cyan);
    const featureResult = await runTestSuite(
      'Feature/Scenario Tests',
      path.join(__dirname, 'feature/arbitrage-scenarios.test.js')
    );
    suiteResults.push(featureResult);
    
    // Step 3: Aggregate and display results
    const aggregatedResults = aggregateResults();
    const allPassed = displayComprehensiveResults(suiteResults, aggregatedResults);
    
    // Step 4: Cleanup
    stopServer();
    
    // Exit with appropriate code
    process.exit(allPassed ? 0 : 1);
    
  } catch (error) {
    log(`\n✗ Fatal error: ${error.message}`, COLORS.red);
    if (error.stack) {
      console.error(error.stack);
    }
    stopServer();
    process.exit(1);
  }
}

// Handle cleanup on exit
process.on('SIGINT', () => {
  log('\n\nTest runner interrupted', COLORS.yellow);
  stopServer();
  process.exit(1);
});

process.on('SIGTERM', () => {
  log('\n\nTest runner terminated', COLORS.yellow);
  stopServer();
  process.exit(1);
});

// Run main function
if (require.main === module) {
  main();
}

module.exports = { main };
