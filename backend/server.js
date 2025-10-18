const express = require('express');
const cors = require('cors');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const WalletManager = require('./wallet-manager');
const BlockchainConnector = require('./blockchain-connector');
const Web3Utilities = require('./web3-utilities');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Initialize blockchain services
const walletManager = new WalletManager();
const blockchainConnector = new BlockchainConnector();
let web3Utils = null;

// Middleware - CORS configured to allow only specified origins via environment variable
const allowedOrigins = process.env.CORS_ORIGIN
  ? process.env.CORS_ORIGIN.split(',').map(origin => origin.trim())
  : [];

app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (like mobile apps, curl, etc.)
    if (!origin) return callback(null, true);
    if (allowedOrigins.length === 0) {
      // No origins allowed if env var is not set
      return callback(new Error('CORS not allowed from this origin'), false);
    }
    if (allowedOrigins.indexOf(origin) !== -1) {
      return callback(null, true);
    } else {
      return callback(new Error('CORS not allowed from this origin'), false);
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
  credentials: true, // Set to true if you want to allow cookies/credentials
  optionsSuccessStatus: 200
}));
app.use(express.json());

// Store for arbitrage data
const arbitrageData = {
  opportunities: [],
  trades: [],
  stats: {
    totalTrades: 0,
    successfulTrades: 0,
    totalProfit: 0,
    avgSlippage: 0
  }
};

// WebSocket connection handler
wss.on('connection', (ws) => {
  console.log('New WebSocket client connected');
  
  // Send initial data
  ws.send(JSON.stringify({
    type: 'initial',
    data: arbitrageData
  }));
  
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

// Broadcast updates to all connected clients
function broadcastUpdate(type, data) {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ type, data }));
    }
  });
}

// REST API Endpoints

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Get current arbitrage opportunities
app.get('/api/opportunities', (req, res) => {
  res.json(arbitrageData.opportunities);
});

// Get trade history
app.get('/api/trades', (req, res) => {
  const limit = parseInt(req.query.limit) || 100;
  res.json(arbitrageData.trades.slice(-limit));
});

// Get statistics
app.get('/api/stats', (req, res) => {
  res.json(arbitrageData.stats);
});

// Calculate flashloan amount for arbitrage opportunity
app.post('/api/calculate-flashloan', (req, res) => {
  try {
    const {
      reserveInBuy,
      reserveOutBuy,
      reserveInSell,
      reserveOutSell,
      flashloanFee = 0.0009, // Default to Aave fee
      gasCost = 100
    } = req.body;

    // Import the engine functions (assuming it's available)
    // In production, this would be properly imported at the top
    const flashloanAmount = 0; // Placeholder - would use real calculation
    
    res.json({
      flashloanAmount,
      flashloanFee,
      gasCost,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Calculate market impact for a trade
app.post('/api/calculate-impact', (req, res) => {
  try {
    const {
      reserveIn,
      reserveOut,
      tradeAmount
    } = req.body;

    // Placeholder for actual calculation
    const impact = 0;
    
    res.json({
      marketImpact: impact,
      reserveIn,
      reserveOut,
      tradeAmount,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Simulate parallel flashloan paths
app.post('/api/simulate-paths', (req, res) => {
  try {
    const {
      paths,
      flashloanAmounts,
      flashloanFee = 0.0009,
      gasCosts
    } = req.body;

    // Placeholder for actual calculation
    const results = [];
    
    res.json({
      results,
      bestPathIndex: 0,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Post new opportunity (from arbitrage engine)
app.post('/api/opportunities', (req, res) => {
  const opportunity = {
    ...req.body,
    timestamp: new Date().toISOString(),
    id: Date.now()
  };
  
  arbitrageData.opportunities.push(opportunity);
  // Keep only last 50 opportunities
  if (arbitrageData.opportunities.length > 50) {
    arbitrageData.opportunities.shift();
  }
  
  broadcastUpdate('opportunity', opportunity);
  res.json({ success: true, id: opportunity.id });
});

// Post trade execution result
app.post('/api/trades', (req, res) => {
  const trade = {
    ...req.body,
    timestamp: new Date().toISOString(),
    id: Date.now()
  };
  
  arbitrageData.trades.push(trade);
  // Keep only last 1000 trades
  if (arbitrageData.trades.length > 1000) {
    arbitrageData.trades.shift();
  }
  
  // Update statistics
  arbitrageData.stats.totalTrades++;
  if (trade.success) {
    arbitrageData.stats.successfulTrades++;
    arbitrageData.stats.totalProfit += trade.profit || 0;
  }
  
  broadcastUpdate('trade', trade);
  broadcastUpdate('stats', arbitrageData.stats);
  res.json({ success: true, id: trade.id });
});

// ============================================================================
// WALLET MANAGEMENT API ENDPOINTS
// ============================================================================

// Initialize wallet provider
app.post('/api/wallet/init-provider', async (req, res) => {
  try {
    const { rpcUrl } = req.body;
    const result = walletManager.initializeProvider(rpcUrl);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Create new wallet
app.post('/api/wallet/create', (req, res) => {
  try {
    const { label } = req.body;
    const result = walletManager.createWallet(label);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Import wallet from private key
app.post('/api/wallet/import-privatekey', (req, res) => {
  try {
    const { privateKey, label } = req.body;
    const result = walletManager.importFromPrivateKey(privateKey, label);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Import wallet from mnemonic
app.post('/api/wallet/import-mnemonic', (req, res) => {
  try {
    const { mnemonic, label, index } = req.body;
    const result = walletManager.importFromMnemonic(mnemonic, label, index);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Connect external wallet
app.post('/api/wallet/connect-external', (req, res) => {
  try {
    const { address, label } = req.body;
    const result = walletManager.connectExternalWallet(address, label);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get wallet info
app.get('/api/wallet/:address', (req, res) => {
  try {
    const { address } = req.params;
    const result = walletManager.getWallet(address);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// List all wallets
app.get('/api/wallets', (req, res) => {
  try {
    const result = walletManager.listWallets();
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get wallet balance
app.get('/api/wallet/:address/balance', async (req, res) => {
  try {
    const { address } = req.params;
    const { token } = req.query;
    const result = await walletManager.getBalance(address, token);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Sign message
app.post('/api/wallet/sign-message', async (req, res) => {
  try {
    const { address, message } = req.body;
    const result = await walletManager.signMessage(address, message);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Sign transaction
app.post('/api/wallet/sign-transaction', async (req, res) => {
  try {
    const { address, transaction } = req.body;
    const result = await walletManager.signTransaction(address, transaction);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Export wallet
app.post('/api/wallet/export', (req, res) => {
  try {
    const { address, includePrivateKey } = req.body;
    const result = walletManager.exportWallet(address, includePrivateKey);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Save wallet to file
app.post('/api/wallet/save', async (req, res) => {
  try {
    const { address, password } = req.body;
    const result = await walletManager.saveWalletToFile(address, password);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Load wallet from file
app.post('/api/wallet/load', async (req, res) => {
  try {
    const { filepath, password, label } = req.body;
    
    // Security: Validate input types to prevent type confusion
    if (typeof filepath !== 'string') {
      return res.status(400).json({ success: false, error: 'filepath must be a string' });
    }
    if (typeof password !== 'string') {
      return res.status(400).json({ success: false, error: 'password must be a string' });
    }
    
    const result = await walletManager.loadWalletFromFile(filepath, password, label);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Remove wallet
app.delete('/api/wallet/:address', (req, res) => {
  try {
    const { address } = req.params;
    const result = walletManager.removeWallet(address);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get wallet count
app.get('/api/wallets/count', (req, res) => {
  try {
    const result = walletManager.getWalletCount();
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Verify signature
app.post('/api/wallet/verify-signature', (req, res) => {
  try {
    const { message, signature } = req.body;
    const result = walletManager.verifySignature(message, signature);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ============================================================================
// BLOCKCHAIN CONNECTIVITY API ENDPOINTS
// ============================================================================

// Add chain
app.post('/api/blockchain/add-chain', (req, res) => {
  try {
    const { chainId, name, rpcUrl, symbol, blockExplorer } = req.body;
    const result = blockchainConnector.addChain(chainId, {
      name,
      rpcUrl,
      symbol,
      blockExplorer
    });
    
    // Initialize web3 utilities with the new provider if it's the first chain
    if (result.success && !web3Utils) {
      const providerResult = blockchainConnector.getProvider(chainId);
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      }
    }
    
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Set default chain
app.post('/api/blockchain/set-default-chain', (req, res) => {
  try {
    const { chainId } = req.body;
    const result = blockchainConnector.setDefaultChain(chainId);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get chain info
app.get('/api/blockchain/chain-info/:chainId?', async (req, res) => {
  try {
    const { chainId } = req.params;
    const result = await blockchainConnector.getChainInfo(chainId ? parseInt(chainId) : null);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get block
app.get('/api/blockchain/block/:blockNumber?', async (req, res) => {
  try {
    const { blockNumber } = req.params;
    const { chainId } = req.query;
    const result = await blockchainConnector.getBlock(
      blockNumber || 'latest',
      chainId ? parseInt(chainId) : null
    );
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get transaction
app.get('/api/blockchain/transaction/:txHash', async (req, res) => {
  try {
    const { txHash } = req.params;
    const { chainId } = req.query;
    const result = await blockchainConnector.getTransaction(txHash, chainId ? parseInt(chainId) : null);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get transaction receipt
app.get('/api/blockchain/receipt/:txHash', async (req, res) => {
  try {
    const { txHash } = req.params;
    const { chainId } = req.query;
    const result = await blockchainConnector.getTransactionReceipt(txHash, chainId ? parseInt(chainId) : null);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Send transaction
app.post('/api/blockchain/send-transaction', async (req, res) => {
  try {
    const { signedTx, chainId } = req.body;
    const result = await blockchainConnector.sendTransaction(signedTx, chainId);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Wait for transaction
app.post('/api/blockchain/wait-transaction', async (req, res) => {
  try {
    const { txHash, confirmations, chainId } = req.body;
    const result = await blockchainConnector.waitForTransaction(
      txHash,
      confirmations || 1,
      chainId
    );
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Estimate gas
app.post('/api/blockchain/estimate-gas', async (req, res) => {
  try {
    const { transaction, chainId } = req.body;
    const result = await blockchainConnector.estimateGas(transaction, chainId);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Call contract function
app.post('/api/blockchain/call', async (req, res) => {
  try {
    const { transaction, chainId } = req.body;
    const result = await blockchainConnector.call(transaction, chainId);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get token info
app.get('/api/blockchain/token/:address', async (req, res) => {
  try {
    const { address } = req.params;
    const { chainId } = req.query;
    const result = await blockchainConnector.getTokenInfo(address, chainId ? parseInt(chainId) : null);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get contract code
app.get('/api/blockchain/code/:address', async (req, res) => {
  try {
    const { address } = req.params;
    const { chainId } = req.query;
    const result = await blockchainConnector.getCode(address, chainId ? parseInt(chainId) : null);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get storage at position
app.post('/api/blockchain/storage', async (req, res) => {
  try {
    const { address, position, chainId } = req.body;
    const result = await blockchainConnector.getStorageAt(address, position, chainId);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// List chains
app.get('/api/blockchain/chains', (req, res) => {
  try {
    const result = blockchainConnector.listChains();
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get gas price
app.get('/api/blockchain/gas-price/:chainId?', async (req, res) => {
  try {
    const { chainId } = req.params;
    const result = await blockchainConnector.getGasPrice(chainId ? parseInt(chainId) : null);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ============================================================================
// WEB3 UTILITIES API ENDPOINTS
// ============================================================================

// Encode function call
app.post('/api/web3/encode-function', (req, res) => {
  try {
    if (!web3Utils) {
      // Initialize with a default provider if not already initialized
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { abi, functionName, params } = req.body;
    const result = web3Utils.encodeFunctionCall(abi, functionName, params);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Decode function result
app.post('/api/web3/decode-function', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { abi, functionName, data } = req.body;
    const result = web3Utils.decodeFunctionResult(abi, functionName, data);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Parse event log
app.post('/api/web3/parse-event', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { abi, log } = req.body;
    const result = web3Utils.parseEventLog(abi, log);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Calculate contract address
app.post('/api/web3/contract-address', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { deployerAddress, nonce } = req.body;
    const result = web3Utils.getContractAddress(deployerAddress, nonce);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Calculate CREATE2 address
app.post('/api/web3/create2-address', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { deployer, salt, bytecode } = req.body;
    const result = web3Utils.getCreate2Address(deployer, salt, bytecode);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Format units
app.post('/api/web3/format-units', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { value, decimals } = req.body;
    const result = web3Utils.formatUnits(value, decimals);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Parse units
app.post('/api/web3/parse-units', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { value, decimals } = req.body;
    const result = web3Utils.parseUnits(value, decimals);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Keccak256 hash
app.post('/api/web3/keccak256', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { data } = req.body;
    const result = web3Utils.keccak256(data);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Solidity packed encoding
app.post('/api/web3/solidity-packed', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { types, values } = req.body;
    const result = web3Utils.solidityPacked(types, values);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ABI encode
app.post('/api/web3/abi-encode', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { types, values } = req.body;
    const result = web3Utils.abiEncode(types, values);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// ABI decode
app.post('/api/web3/abi-decode', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { types, data } = req.body;
    const result = web3Utils.abiDecode(types, data);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Check if address is valid
app.post('/api/web3/is-address', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { address } = req.body;
    const result = web3Utils.isAddress(address);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get function selector
app.post('/api/web3/function-selector', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { signature } = req.body;
    const result = web3Utils.getFunctionSelector(signature);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Get event topic
app.post('/api/web3/event-topic', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { signature } = req.body;
    const result = web3Utils.getEventTopic(signature);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Convert to checksum address
app.post('/api/web3/checksum-address', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { address } = req.body;
    const result = web3Utils.toChecksumAddress(address);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Generate random bytes
app.post('/api/web3/random-bytes', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { length } = req.body;
    const result = web3Utils.randomBytes(length);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Hex to UTF8
app.post('/api/web3/hex-to-utf8', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { hex } = req.body;
    const result = web3Utils.hexToUtf8(hex);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// UTF8 to hex
app.post('/api/web3/utf8-to-hex', (req, res) => {
  try {
    if (!web3Utils) {
      const providerResult = blockchainConnector.getProvider();
      if (providerResult.success) {
        web3Utils = new Web3Utilities(providerResult.provider);
      } else {
        return res.status(400).json({ success: false, error: 'No blockchain provider configured. Add a chain first.' });
      }
    }
    const { text } = req.body;
    const result = web3Utils.utf8ToHex(text);
    res.json(result);
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Simulate some data for demo purposes
function simulateData() {
  const pools = ['UniswapV2', 'UniswapV3', 'Curve', 'Balancer', 'SushiSwap'];
  const tokens = ['ETH/USDT', 'DAI/USDC', 'WBTC/ETH', 'LINK/ETH'];
  
  // Simulate opportunity every 5 seconds
  setInterval(() => {
    const opportunity = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      pool1: pools[Math.floor(Math.random() * pools.length)],
      pool2: pools[Math.floor(Math.random() * pools.length)],
      pair: tokens[Math.floor(Math.random() * tokens.length)],
      expectedProfit: (Math.random() * 100 + 10).toFixed(2),
      slippage: (Math.random() * 2).toFixed(4),
      confidence: (Math.random() * 30 + 70).toFixed(2),
      flashloanAmount: (Math.random() * 50000 + 10000).toFixed(2),
      flashloanFee: '0.0009',
      marketImpact: (Math.random() * 5).toFixed(4),
      estimatedGas: Math.floor(Math.random() * 200000 + 150000)
    };
    
    arbitrageData.opportunities.push(opportunity);
    if (arbitrageData.opportunities.length > 50) {
      arbitrageData.opportunities.shift();
    }
    
    broadcastUpdate('opportunity', opportunity);
  }, 5000);
  
  // Simulate trade execution every 10 seconds
  setInterval(() => {
    if (arbitrageData.opportunities.length > 0) {
      const opp = arbitrageData.opportunities[Math.floor(Math.random() * arbitrageData.opportunities.length)];
      const success = Math.random() > 0.2; // 80% success rate
      
      const trade = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        opportunityId: opp.id,
        pool1: opp.pool1,
        pool2: opp.pool2,
        pair: opp.pair,
        success: success,
        profit: success ? parseFloat(opp.expectedProfit) * (0.8 + Math.random() * 0.4) : 0,
        actualSlippage: parseFloat(opp.slippage) * (0.9 + Math.random() * 0.2),
        gasUsed: (Math.random() * 200000 + 100000).toFixed(0),
        flashloanAmount: opp.flashloanAmount,
        flashloanFee: opp.flashloanFee,
        marketImpact: opp.marketImpact,
        executionTime: (Math.random() * 3000 + 500).toFixed(0) + 'ms'
      };
      
      arbitrageData.trades.push(trade);
      if (arbitrageData.trades.length > 1000) {
        arbitrageData.trades.shift();
      }
      
      // Update statistics
      arbitrageData.stats.totalTrades++;
      if (trade.success) {
        arbitrageData.stats.successfulTrades++;
        arbitrageData.stats.totalProfit += trade.profit;
      }
      arbitrageData.stats.avgSlippage = 
        arbitrageData.trades.reduce((sum, t) => sum + (t.actualSlippage || 0), 0) / 
        arbitrageData.trades.length;
      
      broadcastUpdate('trade', trade);
      broadcastUpdate('stats', arbitrageData.stats);
    }
  }, 10000);
}

// Start simulation in demo mode
if (process.env.DEMO_MODE === 'true') {
  console.log('Starting in DEMO mode with simulated data');
  simulateData();
}

const PORT = process.env.PORT || 3001;
const HOST = process.env.HOST || '0.0.0.0'; // Bind to all network interfaces

server.listen(PORT, HOST, () => {
  console.log(`Backend API server running on ${HOST}:${PORT}`);
  console.log(`WebSocket server ready for real-time updates`);
  console.log(`CORS: Accepting requests from all origins (no firewall restrictions)`);
});
