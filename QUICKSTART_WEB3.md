# Quick Start: Web3 & Wallet Integration

This guide will help you quickly get started with the Web3 and wallet integration.

## Installation

1. Install dependencies:
```bash
cd backend
npm install
```

Dependencies installed:
- `ethers@^6.9.0` - Ethereum library
- `web3@^4.3.0` - Web3 library
- `express@^4.18.2` - API server
- `cors@^2.8.5` - CORS support
- `ws@^8.14.0` - WebSocket support

## Starting the Server

```bash
cd backend
node server.js
```

The server will start on http://localhost:3001

## Quick Examples

### 1. Create a Wallet

```bash
curl -X POST http://localhost:3001/api/wallet/create \
  -H "Content-Type: application/json" \
  -d '{"label": "my-wallet"}'
```

Response:
```json
{
  "success": true,
  "address": "0x...",
  "mnemonic": "word1 word2 ...",
  "label": "my-wallet"
}
```

**⚠️ Important: Save the mnemonic phrase securely!**

### 2. Add a Blockchain Network

```bash
curl -X POST http://localhost:3001/api/blockchain/add-chain \
  -H "Content-Type: application/json" \
  -d '{
    "chainId": 1,
    "name": "Ethereum",
    "rpcUrl": "https://eth.llamarpc.com",
    "symbol": "ETH",
    "blockExplorer": "https://etherscan.io"
  }'
```

### 3. Check Wallet Balance

```bash
curl http://localhost:3001/api/wallet/0xYourAddress/balance?token=native
```

### 4. Sign a Message

```bash
curl -X POST http://localhost:3001/api/wallet/sign-message \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0xYourAddress",
    "message": "Hello, Blockchain!"
  }'
```

### 5. Get Gas Price

```bash
curl http://localhost:3001/api/blockchain/gas-price/1
```

### 6. Encode Function Call

```bash
curl -X POST http://localhost:3001/api/web3/encode-function \
  -H "Content-Type: application/json" \
  -d '{
    "abi": [{"type":"function","name":"transfer","inputs":[{"name":"to","type":"address"},{"name":"value","type":"uint256"}]}],
    "functionName": "transfer",
    "params": ["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0", "1000000000000000000"]
  }'
```

## JavaScript/Node.js Example

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:3001';

async function quickStart() {
  // 1. Create a wallet
  const wallet = await axios.post(`${API_BASE}/api/wallet/create`, {
    label: 'my-trading-wallet'
  });
  console.log('Wallet created:', wallet.data.address);
  console.log('Mnemonic:', wallet.data.mnemonic);

  // 2. Add Ethereum chain
  await axios.post(`${API_BASE}/api/blockchain/add-chain`, {
    chainId: 1,
    name: 'Ethereum',
    rpcUrl: 'https://eth.llamarpc.com',
    symbol: 'ETH'
  });

  // 3. Get balance
  const balance = await axios.get(
    `${API_BASE}/api/wallet/${wallet.data.address}/balance?token=native`
  );
  console.log('Balance:', balance.data.balanceFormatted, 'ETH');

  // 4. Sign a message
  const signature = await axios.post(`${API_BASE}/api/wallet/sign-message`, {
    address: wallet.data.address,
    message: 'Authentication message'
  });
  console.log('Signature:', signature.data.signature);

  // 5. Verify signature
  const verified = await axios.post(`${API_BASE}/api/wallet/verify-signature`, {
    message: 'Authentication message',
    signature: signature.data.signature
  });
  console.log('Recovered address:', verified.data.recoveredAddress);
  console.log('Match:', verified.data.recoveredAddress.toLowerCase() === wallet.data.address.toLowerCase());
}

quickStart().catch(console.error);
```

## Python Example

```python
import requests
import json

API_BASE = 'http://localhost:3001'

# 1. Create a wallet
response = requests.post(f'{API_BASE}/api/wallet/create', 
    json={'label': 'my-wallet'})
wallet = response.json()
print(f"Wallet: {wallet['address']}")

# 2. Add blockchain
requests.post(f'{API_BASE}/api/blockchain/add-chain', 
    json={
        'chainId': 1,
        'name': 'Ethereum',
        'rpcUrl': 'https://eth.llamarpc.com',
        'symbol': 'ETH'
    })

# 3. Get balance
response = requests.get(
    f"{API_BASE}/api/wallet/{wallet['address']}/balance",
    params={'token': 'native'})
balance = response.json()
print(f"Balance: {balance['balanceFormatted']} ETH")

# 4. Get gas price
response = requests.get(f'{API_BASE}/api/blockchain/gas-price/1')
gas = response.json()
print(f"Gas Price: {gas['gasPriceGwei']} Gwei")
```

## Available Endpoints

### Wallet Management
- `POST /api/wallet/create` - Create new wallet
- `POST /api/wallet/import-privatekey` - Import from private key
- `POST /api/wallet/import-mnemonic` - Import from mnemonic
- `POST /api/wallet/connect-external` - Connect external wallet
- `GET /api/wallets` - List all wallets
- `GET /api/wallet/:address` - Get wallet info
- `GET /api/wallet/:address/balance` - Get balance
- `POST /api/wallet/sign-message` - Sign message
- `POST /api/wallet/sign-transaction` - Sign transaction
- `POST /api/wallet/verify-signature` - Verify signature
- `POST /api/wallet/export` - Export wallet
- `DELETE /api/wallet/:address` - Remove wallet

### Blockchain Operations
- `POST /api/blockchain/add-chain` - Add network
- `GET /api/blockchain/chains` - List chains
- `GET /api/blockchain/chain-info/:chainId` - Chain info
- `GET /api/blockchain/block/:blockNumber` - Get block
- `GET /api/blockchain/transaction/:txHash` - Get transaction
- `GET /api/blockchain/receipt/:txHash` - Get receipt
- `POST /api/blockchain/send-transaction` - Send transaction
- `POST /api/blockchain/estimate-gas` - Estimate gas
- `GET /api/blockchain/gas-price/:chainId` - Gas price
- `GET /api/blockchain/token/:address` - Token info

### Web3 Utilities
- `POST /api/web3/encode-function` - Encode function
- `POST /api/web3/decode-function` - Decode function
- `POST /api/web3/keccak256` - Hash data
- `POST /api/web3/format-units` - Wei to Ether
- `POST /api/web3/parse-units` - Ether to Wei
- `POST /api/web3/is-address` - Validate address
- `POST /api/web3/checksum-address` - Checksum address
- `POST /api/web3/function-selector` - Get selector
- `POST /api/web3/abi-encode` - ABI encode
- `POST /api/web3/abi-decode` - ABI decode

## Running Tests

```bash
cd backend
node tests/web3-integration.test.js
```

Expected output:
```
================================================================================
  Wallet & Blockchain Integration Test Suite
================================================================================

✓ Server started successfully

Running Wallet Tests...
✓ Create new wallet (105ms)
✓ Import wallet from private key (5ms)
✓ Import wallet from mnemonic (19ms)
✓ Connect external wallet (2ms)
✓ List all wallets (2ms)
✓ Get wallet info (3ms)
✓ Get wallet count (1ms)
✓ Sign message with wallet (9ms)
✓ Verify message signature (10ms)
✓ Export wallet (4ms)

WALLET Tests: 10/10 passed ✅
```

## Common Use Cases

### Use Case 1: Trading Bot Wallet
```javascript
// Create a dedicated trading wallet
const tradingWallet = await axios.post(`${API_BASE}/api/wallet/create`, {
  label: 'trading-bot'
});

// Save encrypted backup
await axios.post(`${API_BASE}/api/wallet/save`, {
  address: tradingWallet.data.address,
  password: 'secure-password-123'
});
```

### Use Case 2: Multi-Chain Balance Checker
```javascript
const chains = [1, 137, 56]; // Ethereum, Polygon, BSC
const address = '0x...';

for (const chainId of chains) {
  const balance = await axios.get(
    `${API_BASE}/api/wallet/${address}/balance?token=native`,
    { headers: { 'X-Chain-ID': chainId } }
  );
  console.log(`Chain ${chainId}: ${balance.data.balanceFormatted}`);
}
```

### Use Case 3: Contract Interaction
```javascript
// Get ERC20 token info
const tokenInfo = await axios.get(
  `${API_BASE}/api/blockchain/token/0xdac17f958d2ee523a2206206994597c13d831ec7`
);
console.log('Token:', tokenInfo.data.token.name); // "Tether USD"

// Encode transfer
const encoded = await axios.post(`${API_BASE}/api/web3/encode-function`, {
  abi: [/* transfer function ABI */],
  functionName: 'transfer',
  params: [recipient, amount]
});

// Sign and send transaction
const signedTx = await axios.post(`${API_BASE}/api/wallet/sign-transaction`, {
  address: myWallet,
  transaction: {
    to: tokenAddress,
    data: encoded.data.encoded,
    gasLimit: '100000'
  }
});

const result = await axios.post(`${API_BASE}/api/blockchain/send-transaction`, {
  signedTx: signedTx.data.signedTransaction,
  chainId: 1
});
console.log('Transaction hash:', result.data.hash);
```

## Security Best Practices

1. **Never commit wallets or private keys**
   - Add `backend/wallets/` to `.gitignore`
   - Use environment variables for production keys

2. **Use encrypted wallet storage**
   ```javascript
   await axios.post(`${API_BASE}/api/wallet/save`, {
     address: wallet.address,
     password: process.env.WALLET_PASSWORD
   });
   ```

3. **Implement rate limiting**
   - Use a reverse proxy (nginx) with rate limits
   - Implement request throttling in production

4. **Use HTTPS in production**
   - Never use HTTP for sensitive operations
   - Implement SSL/TLS certificates

5. **Validate all inputs**
   - The API validates inputs, but add client-side validation too
   - Sanitize user inputs before sending to API

## Troubleshooting

### Issue: "No blockchain provider configured"
**Solution**: Add a blockchain network first:
```bash
curl -X POST http://localhost:3001/api/blockchain/add-chain \
  -H "Content-Type: application/json" \
  -d '{"chainId": 1, "name": "Ethereum", "rpcUrl": "https://eth.llamarpc.com", "symbol": "ETH"}'
```

### Issue: "Wallet not found or is external"
**Solution**: Ensure you're using an internal wallet (created or imported), not an external one:
```bash
curl -X POST http://localhost:3001/api/wallet/create \
  -H "Content-Type: application/json" \
  -d '{"label": "my-wallet"}'
```

### Issue: RPC errors or timeouts
**Solution**: Use a private RPC endpoint or alternative public endpoints:
- Ethereum: `https://eth.llamarpc.com`, `https://rpc.ankr.com/eth`
- Polygon: `https://polygon-rpc.com`, `https://rpc.ankr.com/polygon`
- BSC: `https://bsc-dataseed.binance.org`

## Next Steps

1. Read the full [WEB3_INTEGRATION.md](./WEB3_INTEGRATION.md) documentation
2. Explore the [wallet-manager.js](./backend/wallet-manager.js) source code
3. Check out [blockchain-connector.js](./backend/blockchain-connector.js) for advanced features
4. Review [web3-utilities.js](./backend/web3-utilities.js) for utility functions
5. Run the comprehensive test suite to see all features in action

## Support

For issues or questions:
1. Check the documentation
2. Review test cases in `backend/tests/web3-integration.test.js`
3. Open an issue on GitHub

Happy coding! 🚀
