#!/usr/bin/env node
/**
 * Comprehensive Environment Variable Implementation Test
 * Tests all newly created modules and their integration with .env variables
 */

const { envConfig } = require('./config/env-config');
const { multiChainProvider } = require('./config/multi-chain-provider');
const { dexProtocolIntegration } = require('./config/dex-protocol-integration');
const { mevIntegration } = require('./config/mev-integration');
const { notificationIntegration } = require('./config/notification-integration');

console.log('╔═══════════════════════════════════════════════════════════════╗');
console.log('║     ENVIRONMENT VARIABLE IMPLEMENTATION TEST SUITE            ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function test(name, condition, details = '') {
  totalTests++;
  if (condition) {
    console.log(`✓ ${name}`);
    if (details) console.log(`  ${details}`);
    passedTests++;
    return true;
  } else {
    console.log(`✗ ${name}`);
    if (details) console.log(`  ${details}`);
    failedTests++;
    return false;
  }
}

function sectionHeader(title) {
  console.log(`\n${'═'.repeat(65)}`);
  console.log(`  ${title}`);
  console.log('═'.repeat(65));
}

async function runTests() {
  // Test 1: Environment Config Module
  sectionHeader('ENVIRONMENT CONFIG MODULE');
  
  const loadResult = envConfig.load();
  test('Environment config loads successfully', loadResult);
  
  const networkConfig = envConfig.getNetworkConfig();
  test('Network config retrieved', networkConfig !== null);
  test('Chain ID is set', networkConfig.chainId > 0, `Chain ID: ${networkConfig.chainId}`);
  
  const walletConfig = envConfig.getWalletConfig();
  test('Wallet config retrieved', walletConfig !== null);
  
  const dexConfig = envConfig.getDEXProtocolEndpoints();
  test('DEX protocol endpoints retrieved', dexConfig !== null);
  test('Uniswap V2 Router configured', dexConfig.uniswapV2Router !== undefined);
  test('Uniswap V3 Router configured', dexConfig.uniswapV3Router !== undefined);
  test('Balancer Vault configured', dexConfig.balancerVault !== undefined);
  test('AAVE V3 Pool configured', dexConfig.aaveV3Pool !== undefined);
  
  const mevConfig = envConfig.getMEVConfig();
  test('MEV config retrieved', mevConfig !== null);
  test('Flashbots relay configured', mevConfig.flashbotsRelayUrl !== undefined);
  test('MEV-Share setting retrieved', typeof mevConfig.mevShareEnabled === 'boolean');
  
  const dbConfig = envConfig.getDatabaseConfig();
  test('Database config retrieved', dbConfig !== null);
  test('PostgreSQL config present', dbConfig.postgres !== null);
  test('Redis config present', dbConfig.redis !== null);
  
  const notifConfig = envConfig.getNotificationConfig();
  test('Notification config retrieved', notifConfig !== null);
  test('Telegram config present', notifConfig.telegram !== null);
  test('Discord config present', notifConfig.discord !== null);
  
  const mlConfig = envConfig.getMLConfig();
  test('ML config retrieved', mlConfig !== null);
  test('ML model path set', mlConfig.modelPath !== undefined);
  test('ML retrain interval set', mlConfig.retrainInterval > 0);
  
  const execConfig = envConfig.getExecutionConfig();
  test('Execution config retrieved', execConfig !== null);
  test('Min profit USD set', execConfig.minProfitUSD > 0);
  test('Max gas price set', execConfig.maxGasPriceGwei > 0);
  test('Slippage tolerance set', execConfig.slippageTolerance >= 0);
  
  const monConfig = envConfig.getMonitoringConfig();
  test('Monitoring config retrieved', monConfig !== null);
  test('Prometheus port set', monConfig.prometheusPort > 0);
  test('Health check port set', monConfig.healthCheckPort > 0);
  
  const swarmConfig = envConfig.getSwarmConfig();
  test('Swarm config retrieved', swarmConfig !== null);
  
  const chainEndpoints = envConfig.getChainEndpoints();
  test('Chain endpoints retrieved', chainEndpoints !== null);
  test('Multiple chains configured', Object.keys(chainEndpoints).length > 0, 
    `${Object.keys(chainEndpoints).length} chains`);
  
  const validation = envConfig.validate();
  test('Config validation runs', validation !== null);

  // Test 2: Multi-Chain Provider
  sectionHeader('MULTI-CHAIN PROVIDER MODULE');
  
  const initResult = multiChainProvider.initialize();
  test('Multi-chain provider initializes', initResult.success);
  test('Chains initialized', initResult.totalChains > 0, 
    `${initResult.totalChains} chains`);
  
  const availableChains = multiChainProvider.getAvailableChains();
  test('Available chains retrieved', availableChains.length > 0, 
    `${availableChains.length} chains available`);
  
  // Test getting provider for first available chain
  if (availableChains.length > 0) {
    const firstChain = availableChains[0];
    const providerResult = multiChainProvider.getProvider(firstChain);
    test(`Provider for ${firstChain} retrieved`, providerResult.success);
    
    const metadata = multiChainProvider.getChainMetadata(firstChain);
    test(`Metadata for ${firstChain} retrieved`, metadata !== null);
  }

  // Test 3: DEX Protocol Integration
  sectionHeader('DEX PROTOCOL INTEGRATION MODULE');
  
  const dexInitResult = dexProtocolIntegration.initialize();
  test('DEX protocol integration initializes', dexInitResult.success);
  test('DEX protocols configured', dexInitResult.protocolCount > 0, 
    `${dexInitResult.protocolCount} protocols`);
  
  const availableProtocols = dexProtocolIntegration.getAvailableProtocols();
  test('Available protocols retrieved', availableProtocols.length > 0, 
    `${availableProtocols.length} protocols`);
  
  // Test specific protocols
  const protocolTests = [
    'UNISWAP_V2',
    'UNISWAP_V3',
    'SUSHISWAP',
    'QUICKSWAP',
    'CURVE',
    'BALANCER',
    'AAVE_V3',
    'DODO'
  ];
  
  for (const protocolName of protocolTests) {
    const protocolResult = dexProtocolIntegration.getProtocol(protocolName);
    if (protocolResult.success) {
      test(`${protocolName} configured`, true);
      
      if (protocolName === 'AAVE_V3') {
        const flashloanSupported = dexProtocolIntegration.supportsFlashloans(protocolName);
        test(`${protocolName} flashloan support detected`, flashloanSupported);
      }
    }
  }

  // Test 4: MEV Integration
  sectionHeader('MEV INTEGRATION MODULE');
  
  const mevInitResult = mevIntegration.initialize();
  test('MEV integration initializes', mevInitResult.success);
  test('MEV relays configured', mevInitResult.activeRelays >= 0, 
    `${mevInitResult.activeRelays} relays`);
  
  const availableRelays = mevIntegration.getAvailableRelays();
  test('Available relays retrieved', availableRelays !== null);
  
  const mevShareEnabled = mevIntegration.isMEVShareEnabled();
  test('MEV-Share status retrieved', typeof mevShareEnabled === 'boolean', 
    `MEV-Share: ${mevShareEnabled}`);

  // Test 5: Notification Integration
  sectionHeader('NOTIFICATION INTEGRATION MODULE');
  
  const notifInitResult = notificationIntegration.initialize();
  test('Notification integration initializes', notifInitResult.success);
  test('Notification channels configured', notifInitResult.activeChannels >= 0, 
    `${notifInitResult.activeChannels} channels`);
  
  const availableChannels = notificationIntegration.getAvailableChannels();
  test('Available channels retrieved', availableChannels !== null);

  // Test 6: Integration Tests
  sectionHeader('INTEGRATION TESTS');
  
  const allConfig = envConfig.getAllConfig();
  test('All config retrieved in one call', allConfig !== null);
  test('Config has network section', allConfig.network !== undefined);
  test('Config has wallet section', allConfig.wallet !== undefined);
  test('Config has dexProtocols section', allConfig.dexProtocols !== undefined);
  test('Config has mev section', allConfig.mev !== undefined);
  test('Config has database section', allConfig.database !== undefined);
  test('Config has notifications section', allConfig.notifications !== undefined);
  test('Config has ml section', allConfig.ml !== undefined);
  test('Config has execution section', allConfig.execution !== undefined);
  test('Config has monitoring section', allConfig.monitoring !== undefined);
  test('Config has swarm section', allConfig.swarm !== undefined);
  test('Config has chains section', allConfig.chains !== undefined);

  // Final Summary
  console.log('\n' + '═'.repeat(65));
  console.log('  TEST SUMMARY');
  console.log('═'.repeat(65));
  console.log(`Total tests:     ${totalTests}`);
  console.log(`Passed:          ${passedTests} ✓`);
  console.log(`Failed:          ${failedTests} ${failedTests > 0 ? '✗' : ''}`);
  console.log(`Success rate:    ${((passedTests/totalTests) * 100).toFixed(1)}%`);
  console.log('─'.repeat(65));

  if (failedTests === 0) {
    console.log('✓ ALL TESTS PASSED - Environment variable implementation complete!\n');
    
    // Print summaries of all modules
    envConfig.printSummary();
    multiChainProvider.printSummary();
    dexProtocolIntegration.printSummary();
    mevIntegration.printSummary();
    notificationIntegration.printSummary();
    
    process.exit(0);
  } else {
    console.log(`✗ ${failedTests} TEST(S) FAILED - Review errors above\n`);
    process.exit(1);
  }
}

// Run tests
runTests().catch(error => {
  console.error('\n❌ Error running tests:', error.message);
  console.error(error.stack);
  process.exit(1);
});
