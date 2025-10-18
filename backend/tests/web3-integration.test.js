/**
 * Comprehensive Wallet and Blockchain Integration Tests
 */

const axios = require('axios');
const { spawn } = require('child_process');
const path = require('path');

const API_BASE = 'http://localhost:3001';
let serverProcess = null;

// Test results
const results = {
  wallet: [],
  blockchain: [],
  web3: []
};

// Helper functions
function pass(category, name, duration) {
  results[category].push({ name, status: 'PASS', duration });
  console.log(`✓ ${name} (${duration}ms)`);
}

function fail(category, name, error, duration) {
  results[category].push({ name, status: 'FAIL', error, duration });
  console.log(`✗ ${name} - ${error} (${duration}ms)`);
}

async function test(category, name, fn) {
  const start = Date.now();
  try {
    await fn();
    pass(category, name, Date.now() - start);
  } catch (error) {
    fail(category, name, error.message, Date.now() - start);
  }
}

// Start server
async function startServer() {
  console.log('Starting server for testing...');
  
  return new Promise((resolve, reject) => {
    serverProcess = spawn('node', ['server.js'], {
      cwd: path.join(__dirname, '..'),
      stdio: 'pipe'
    });

    serverProcess.stdout.on('data', (data) => {
      if (data.toString().includes('running on port')) {
        setTimeout(resolve, 1000); // Give it a second to fully initialize
      }
    });

    serverProcess.stderr.on('data', (data) => {
      console.error('Server error:', data.toString());
    });

    setTimeout(() => reject(new Error('Server startup timeout')), 10000);
  });
}

// Stop server
function stopServer() {
  if (serverProcess) {
    // Send SIGTERM first, then SIGKILL after timeout if still running
    let killed = false;
    const proc = serverProcess;
    const killTimeout = setTimeout(() => {
      if (!killed && proc.exitCode === null) {
        try {
          proc.kill('SIGKILL');
        } catch (e) {
          // Ignore if already dead
        }
      }
    }, 5000);
    proc.once('exit', () => {
      killed = true;
      clearTimeout(killTimeout);
    });
    try {
      proc.kill('SIGTERM');
    } catch (e) {
      // Ignore if already dead
    }
    serverProcess = null;
  }
}

// ============================================================================
// WALLET TESTS
// ============================================================================

async function testWalletCreation() {
  await test('wallet', 'Create new wallet', async () => {
    const response = await axios.post(`${API_BASE}/api/wallet/create`, {
      label: 'test-wallet'
    });
    
    if (!response.data.success) throw new Error('Failed to create wallet');
    if (!response.data.address) throw new Error('No address returned');
    if (!response.data.mnemonic) throw new Error('No mnemonic returned');
  });
}

async function testWalletImportPrivateKey() {
  await test('wallet', 'Import wallet from private key', async () => {
    // Use a test private key (DO NOT use in production)
    const testPk = '0x0123456789012345678901234567890123456789012345678901234567890123';
    const response = await axios.post(`${API_BASE}/api/wallet/import-privatekey`, {
      privateKey: testPk,
      label: 'imported-wallet'
    });
    
    if (!response.data.success) throw new Error('Failed to import wallet');
    if (!response.data.address) throw new Error('No address returned');
  });
}

async function testWalletImportMnemonic() {
  await test('wallet', 'Import wallet from mnemonic', async () => {
    const testMnemonic = 'test test test test test test test test test test test junk';
    const response = await axios.post(`${API_BASE}/api/wallet/import-mnemonic`, {
      mnemonic: testMnemonic,
      label: 'mnemonic-wallet',
      index: 0
    });
    
    if (!response.data.success) throw new Error('Failed to import from mnemonic');
    if (!response.data.address) throw new Error('No address returned');
  });
}

async function testExternalWalletConnection() {
  await test('wallet', 'Connect external wallet', async () => {
    const response = await axios.post(`${API_BASE}/api/wallet/connect-external`, {
      address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0',
      label: 'external-test'
    });
    
    if (!response.data.success) throw new Error('Failed to connect external wallet');
    if (response.data.type !== 'external') throw new Error('Wrong wallet type');
  });
}

async function testListWallets() {
  await test('wallet', 'List all wallets', async () => {
    const response = await axios.get(`${API_BASE}/api/wallets`);
    
    if (!response.data.success) throw new Error('Failed to list wallets');
    if (!Array.isArray(response.data.wallets)) throw new Error('Invalid wallet list');
    if (response.data.wallets.length < 3) throw new Error('Expected at least 3 wallets');
  });
}

async function testGetWallet() {
  await test('wallet', 'Get wallet info', async () => {
    const listResponse = await axios.get(`${API_BASE}/api/wallets`);
    const firstWallet = listResponse.data.wallets[0];
    
    const response = await axios.get(`${API_BASE}/api/wallet/${firstWallet.address}`);
    
    if (!response.data.success) throw new Error('Failed to get wallet');
    if (response.data.wallet.address !== firstWallet.address) throw new Error('Address mismatch');
  });
}

async function testWalletCount() {
  await test('wallet', 'Get wallet count', async () => {
    const response = await axios.get(`${API_BASE}/api/wallets/count`);
    
    if (!response.data.success) throw new Error('Failed to get count');
    if (typeof response.data.count !== 'number') throw new Error('Invalid count');
    if (response.data.count < 1) throw new Error('Expected at least 1 wallet');
  });
}

async function testSignMessage() {
  await test('wallet', 'Sign message with wallet', async () => {
    const listResponse = await axios.get(`${API_BASE}/api/wallets`);
    const internalWallet = listResponse.data.wallets.find(w => w.type !== 'external');
    
    if (!internalWallet) {
      console.log('  ⚠ Skipping sign message test - no internal wallets available');
      return;
    }
    
    const response = await axios.post(`${API_BASE}/api/wallet/sign-message`, {
      address: internalWallet.address,
      message: 'Test message for signing'
    });
    
    if (!response.data.success) throw new Error('Failed to sign message');
    if (!response.data.signature) throw new Error('No signature returned');
  });
}

async function testVerifySignature() {
  await test('wallet', 'Verify message signature', async () => {
    const listResponse = await axios.get(`${API_BASE}/api/wallets`);
    const internalWallet = listResponse.data.wallets.find(w => w.type !== 'external');
    
    if (!internalWallet) {
      console.log('  ⚠ Skipping verify signature test - no internal wallets available');
      return;
    }
    
    const message = 'Test verification message';
    const signResponse = await axios.post(`${API_BASE}/api/wallet/sign-message`, {
      address: internalWallet.address,
      message
    });
    
    const response = await axios.post(`${API_BASE}/api/wallet/verify-signature`, {
      message,
      signature: signResponse.data.signature
    });
    
    if (!response.data.success) throw new Error('Failed to verify signature');
    if (response.data.recoveredAddress.toLowerCase() !== internalWallet.address.toLowerCase()) {
      throw new Error('Address mismatch in verification');
    }
  });
}

async function testExportWallet() {
  await test('wallet', 'Export wallet', async () => {
    const listResponse = await axios.get(`${API_BASE}/api/wallets`);
    const wallet = listResponse.data.wallets[0];
    
    const response = await axios.post(`${API_BASE}/api/wallet/export`, {
      address: wallet.address,
      includePrivateKey: false
    });
    
    if (!response.data.success) throw new Error('Failed to export wallet');
    if (!response.data.wallet) throw new Error('No wallet data returned');
  });
}

// ============================================================================
// BLOCKCHAIN TESTS
// ============================================================================

async function testAddChain() {
  await test('blockchain', 'Add blockchain chain', async () => {
    const response = await axios.post(`${API_BASE}/api/blockchain/add-chain`, {
      chainId: 1,
      name: 'Ethereum Mainnet',
      rpcUrl: 'https://eth.llamarpc.com',
      symbol: 'ETH',
      blockExplorer: 'https://etherscan.io'
    });
    
    if (!response.data.success) throw new Error('Failed to add chain');
    if (response.data.chainId !== 1) throw new Error('Chain ID mismatch');
  });
}

async function testAddPolygonChain() {
  await test('blockchain', 'Add Polygon chain', async () => {
    const response = await axios.post(`${API_BASE}/api/blockchain/add-chain`, {
      chainId: 137,
      name: 'Polygon',
      rpcUrl: 'https://polygon-rpc.com',
      symbol: 'MATIC',
      blockExplorer: 'https://polygonscan.com'
    });
    
    if (!response.data.success) throw new Error('Failed to add Polygon chain');
  });
}

async function testListChains() {
  await test('blockchain', 'List all chains', async () => {
    const response = await axios.get(`${API_BASE}/api/blockchain/chains`);
    
    if (!response.data.success) throw new Error('Failed to list chains');
    if (!Array.isArray(response.data.chains)) throw new Error('Invalid chains list');
    if (response.data.chains.length < 1) throw new Error('Expected at least 1 chain');
  });
}

async function testSetDefaultChain() {
  await test('blockchain', 'Set default chain', async () => {
    const response = await axios.post(`${API_BASE}/api/blockchain/set-default-chain`, {
      chainId: 1
    });
    
    if (!response.data.success) throw new Error('Failed to set default chain');
  });
}

async function testGetChainInfo() {
  await test('blockchain', 'Get chain info', async () => {
    const response = await axios.get(`${API_BASE}/api/blockchain/chain-info/1`);
    
    if (!response.data.success) throw new Error('Failed to get chain info');
    if (!response.data.blockNumber) throw new Error('No block number returned');
  });
}

async function testGetBlock() {
  await test('blockchain', 'Get latest block', async () => {
    const response = await axios.get(`${API_BASE}/api/blockchain/block/latest?chainId=1`);
    
    if (!response.data.success) throw new Error('Failed to get block');
    if (!response.data.block) throw new Error('No block data returned');
    if (!response.data.block.number) throw new Error('No block number in response');
  });
}

async function testGetGasPrice() {
  await test('blockchain', 'Get gas price', async () => {
    const response = await axios.get(`${API_BASE}/api/blockchain/gas-price/1`);
    
    if (!response.data.success) throw new Error('Failed to get gas price');
    if (!response.data.gasPrice && !response.data.maxFeePerGas) {
      throw new Error('No gas price data returned');
    }
  });
}

async function testGetTokenInfo() {
  await test('blockchain', 'Get ERC20 token info', async () => {
    // USDT on Ethereum
    const usdtAddress = '0xdac17f958d2ee523a2206206994597c13d831ec7';
    const response = await axios.get(
      `${API_BASE}/api/blockchain/token/${usdtAddress}?chainId=1`
    );
    
    if (!response.data.success) throw new Error('Failed to get token info');
    if (!response.data.token) throw new Error('No token data returned');
    if (response.data.token.symbol !== 'USDT') throw new Error('Wrong token symbol');
  });
}

async function testGetContractCode() {
  await test('blockchain', 'Get contract code', async () => {
    // USDT on Ethereum
    const usdtAddress = '0xdac17f958d2ee523a2206206994597c13d831ec7';
    const response = await axios.get(
      `${API_BASE}/api/blockchain/code/${usdtAddress}?chainId=1`
    );
    
    if (!response.data.success) throw new Error('Failed to get code');
    if (!response.data.isContract) throw new Error('Should be a contract');
  });
}

async function testEstimateGas() {
  await test('blockchain', 'Estimate gas for transaction', async () => {
    const response = await axios.post(`${API_BASE}/api/blockchain/estimate-gas`, {
      transaction: {
        to: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0',
        value: '1000000000000000' // 0.001 ETH
      },
      chainId: 1
    });
    
    if (!response.data.success) throw new Error('Failed to estimate gas');
    if (!response.data.gasEstimate) throw new Error('No gas estimate returned');
  });
}

// ============================================================================
// WEB3 UTILITIES TESTS
// ============================================================================

async function testIsAddress() {
  await test('web3', 'Check if address is valid', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/is-address`, {
      address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0'
    });
    
    if (!response.data.success) throw new Error('Failed to check address');
    if (!response.data.isValid) throw new Error('Valid address marked as invalid');
    if (!response.data.checksummed) throw new Error('No checksummed address returned');
  });
}

async function testChecksumAddress() {
  await test('web3', 'Convert to checksum address', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/checksum-address`, {
      address: '0x742d35cc6634c0532925a3b844bc9e7595f0beb0'
    });
    
    if (!response.data.success) throw new Error('Failed to checksum address');
    if (!response.data.address) throw new Error('No checksummed address returned');
  });
}

async function testKeccak256() {
  await test('web3', 'Calculate keccak256 hash', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/keccak256`, {
      data: 'test data'
    });
    
    if (!response.data.success) throw new Error('Failed to hash');
    if (!response.data.hash) throw new Error('No hash returned');
    if (!response.data.hash.startsWith('0x')) throw new Error('Invalid hash format');
  });
}

async function testFormatUnits() {
  await test('web3', 'Format units (wei to ether)', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/format-units`, {
      value: '1000000000000000000', // 1 ETH in wei
      decimals: 18
    });
    
    if (!response.data.success) throw new Error('Failed to format units');
    if (response.data.formatted !== '1.0') throw new Error('Wrong formatted value');
  });
}

async function testParseUnits() {
  await test('web3', 'Parse units (ether to wei)', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/parse-units`, {
      value: '1.0',
      decimals: 18
    });
    
    if (!response.data.success) throw new Error('Failed to parse units');
    if (response.data.parsed !== '1000000000000000000') throw new Error('Wrong parsed value');
  });
}

async function testFunctionSelector() {
  await test('web3', 'Get function selector', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/function-selector`, {
      signature: 'transfer(address,uint256)'
    });
    
    if (!response.data.success) throw new Error('Failed to get selector');
    if (!response.data.selector) throw new Error('No selector returned');
    if (response.data.selector !== '0xa9059cbb') throw new Error('Wrong selector');
  });
}

async function testEventTopic() {
  await test('web3', 'Get event topic', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/event-topic`, {
      signature: 'Transfer(address,address,uint256)'
    });
    
    if (!response.data.success) throw new Error('Failed to get event topic');
    if (!response.data.topic) throw new Error('No topic returned');
  });
}

async function testRandomBytes() {
  await test('web3', 'Generate random bytes', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/random-bytes`, {
      length: 32
    });
    
    if (!response.data.success) throw new Error('Failed to generate random bytes');
    if (!response.data.bytes) throw new Error('No bytes returned');
  });
}

async function testUtf8ToHex() {
  await test('web3', 'Convert UTF8 to hex', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/utf8-to-hex`, {
      text: 'Hello, World!'
    });
    
    if (!response.data.success) throw new Error('Failed to convert to hex');
    if (!response.data.hex) throw new Error('No hex returned');
  });
}

async function testHexToUtf8() {
  await test('web3', 'Convert hex to UTF8', async () => {
    const hexResponse = await axios.post(`${API_BASE}/api/web3/utf8-to-hex`, {
      text: 'Hello, World!'
    });
    
    const response = await axios.post(`${API_BASE}/api/web3/hex-to-utf8`, {
      hex: hexResponse.data.hex
    });
    
    if (!response.data.success) throw new Error('Failed to convert to UTF8');
    if (response.data.utf8 !== 'Hello, World!') throw new Error('Wrong UTF8 value');
  });
}

async function testAbiEncode() {
  await test('web3', 'ABI encode', async () => {
    const response = await axios.post(`${API_BASE}/api/web3/abi-encode`, {
      types: ['address', 'uint256'],
      values: ['0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0', '1000000000000000000']
    });
    
    if (!response.data.success) throw new Error('Failed to ABI encode');
    if (!response.data.encoded) throw new Error('No encoded data returned');
  });
}

async function testAbiDecode() {
  await test('web3', 'ABI decode', async () => {
    const encodeResponse = await axios.post(`${API_BASE}/api/web3/abi-encode`, {
      types: ['address', 'uint256'],
      values: ['0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0', '1000000000000000000']
    });
    
    const response = await axios.post(`${API_BASE}/api/web3/abi-decode`, {
      types: ['address', 'uint256'],
      data: encodeResponse.data.encoded
    });
    
    if (!response.data.success) throw new Error('Failed to ABI decode');
    if (!Array.isArray(response.data.decoded)) throw new Error('Invalid decoded data');
  });
}

// ============================================================================
// RUN ALL TESTS
// ============================================================================

async function runAllTests() {
  console.log('\n================================================================================');
  console.log('  Wallet & Blockchain Integration Test Suite');
  console.log('================================================================================\n');

  try {
    await startServer();
    console.log('✓ Server started successfully\n');

    console.log('Running Wallet Tests...\n');
    await testWalletCreation();
    await testWalletImportPrivateKey();
    await testWalletImportMnemonic();
    await testExternalWalletConnection();
    await testListWallets();
    await testGetWallet();
    await testWalletCount();
    await testSignMessage();
    await testVerifySignature();
    await testExportWallet();

    console.log('\nRunning Blockchain Tests...\n');
    await testAddChain(); // This initializes the blockchain connector
    await testAddPolygonChain();
    await testListChains();
    await testSetDefaultChain();
    await testGetChainInfo();
    await testGetBlock();
    await testGetGasPrice();
    await testGetTokenInfo();
    await testGetContractCode();
    await testEstimateGas();

    console.log('\nRunning Web3 Utilities Tests...\n');
    // Web3 utils should work now that blockchain is initialized
    await testIsAddress();
    await testChecksumAddress();
    await testKeccak256();
    await testFormatUnits();
    await testParseUnits();
    await testFunctionSelector();
    await testEventTopic();
    await testRandomBytes();
    await testUtf8ToHex();
    await testHexToUtf8();
    await testAbiEncode();
    await testAbiDecode();

    // Print summary
    console.log('\n================================================================================');
    console.log('  TEST SUMMARY');
    console.log('================================================================================\n');

    const categories = ['wallet', 'blockchain', 'web3'];
    let totalTests = 0;
    let passedTests = 0;
    let failedTests = 0;

    categories.forEach(category => {
      const categoryResults = results[category];
      const passed = categoryResults.filter(r => r.status === 'PASS').length;
      const failed = categoryResults.filter(r => r.status === 'FAIL').length;
      
      totalTests += categoryResults.length;
      passedTests += passed;
      failedTests += failed;

      console.log(`${category.toUpperCase()} Tests: ${passed}/${categoryResults.length} passed`);
      
      if (failed > 0) {
        categoryResults.filter(r => r.status === 'FAIL').forEach(r => {
          console.log(`  ✗ ${r.name}: ${r.error}`);
        });
      }
    });

    console.log(`\nTotal: ${passedTests}/${totalTests} tests passed`);
    
    const successRate = ((passedTests / totalTests) * 100).toFixed(1);
    console.log(`Success Rate: ${successRate}%\n`);

    if (failedTests === 0) {
      console.log('✓ All tests passed!');
    } else {
      console.log(`✗ ${failedTests} test(s) failed`);
    }

  } catch (error) {
    console.error('Test suite error:', error.message);
  } finally {
    stopServer();
    console.log('\n✓ Server stopped\n');
  }
}

// Run tests
runAllTests().catch(error => {
  console.error('Fatal error:', error);
  stopServer();
  process.exit(1);
});
