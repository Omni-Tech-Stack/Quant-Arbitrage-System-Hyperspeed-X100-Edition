/**
 * Main Configuration Module Index
 * Central export point for all configuration modules
 */

// Export environment configuration
const { envConfig, EnvironmentConfig } = require('./env-config');

// Export multi-chain provider
const { multiChainProvider, MultiChainProvider } = require('./multi-chain-provider');

// Export DEX protocol integration
const { dexProtocolIntegration, DEXProtocolIntegration } = require('./dex-protocol-integration');

// Export MEV integration
const { mevIntegration, MEVIntegration } = require('./mev-integration');

// Export notification integration
const { notificationIntegration, NotificationIntegration } = require('./notification-integration');

/**
 * Initialize all modules at once
 */
function initializeAll() {
  console.log('Initializing all configuration modules...\n');
  
  const results = {
    env: envConfig.load(),
    multiChain: multiChainProvider.initialize(),
    dex: dexProtocolIntegration.initialize(),
    mev: mevIntegration.initialize(),
    notifications: notificationIntegration.initialize()
  };

  const allSuccess = Object.values(results).every(r => r.success);

  return {
    success: allSuccess,
    results,
    message: allSuccess ? 'All modules initialized successfully' : 'Some modules failed to initialize'
  };
}

/**
 * Print comprehensive system summary
 */
function printSystemSummary() {
  console.log('\n╔═══════════════════════════════════════════════════════════════╗');
  console.log('║        QUANT ARBITRAGE SYSTEM - CONFIGURATION STATUS         ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');
  
  envConfig.printSummary();
  multiChainProvider.printSummary();
  dexProtocolIntegration.printSummary();
  mevIntegration.printSummary();
  notificationIntegration.printSummary();
}

/**
 * Get comprehensive system status
 */
function getSystemStatus() {
  return {
    environment: {
      loaded: envConfig.loaded,
      config: envConfig.getAllConfig(),
      validation: envConfig.validate()
    },
    multiChain: {
      initialized: multiChainProvider.initialized,
      availableChains: multiChainProvider.getAvailableChains(),
      chainCount: multiChainProvider.getAvailableChains().length
    },
    dex: {
      initialized: dexProtocolIntegration.initialized,
      availableProtocols: dexProtocolIntegration.getAvailableProtocols(),
      protocolCount: dexProtocolIntegration.protocols.size
    },
    mev: {
      initialized: mevIntegration.initialized,
      availableRelays: mevIntegration.getAvailableRelays(),
      relayCount: mevIntegration.relays.size,
      mevShareEnabled: mevIntegration.isMEVShareEnabled()
    },
    notifications: {
      initialized: notificationIntegration.initialized,
      availableChannels: notificationIntegration.getAvailableChannels(),
      channelCount: notificationIntegration.channels.size
    }
  };
}

module.exports = {
  // Singleton instances
  envConfig,
  multiChainProvider,
  dexProtocolIntegration,
  mevIntegration,
  notificationIntegration,
  
  // Classes for creating new instances
  EnvironmentConfig,
  MultiChainProvider,
  DEXProtocolIntegration,
  MEVIntegration,
  NotificationIntegration,
  
  // Utility functions
  initializeAll,
  printSystemSummary,
  getSystemStatus
};
