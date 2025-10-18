# Secrets & Key Management Guide

## Overview

This guide outlines best practices for managing secrets, private keys, and sensitive credentials in the Quant Arbitrage System. **NEVER** commit secrets to version control.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Hardware Wallets & HSM](#hardware-wallets--hsm)
3. [Multi-Signature Requirements](#multi-signature-requirements)
4. [Key Rotation](#key-rotation)
5. [Production Deployment](#production-deployment)
6. [Emergency Procedures](#emergency-procedures)

## Environment Variables

### Setup

Create a `.env` file in the project root (already in `.gitignore`):

```bash
# .env - NEVER COMMIT THIS FILE

# Blockchain RPC Endpoints (use private/authenticated endpoints)
RPC_ETHEREUM=https://eth-mainnet.alchemyapi.io/v2/YOUR_API_KEY
RPC_POLYGON=https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY
RPC_BSC=https://bsc-dataseed.binance.org/
RPC_ARBITRUM=https://arb-mainnet.g.alchemy.com/v2/YOUR_API_KEY

# Private Keys (for automated trading wallets)
# WARNING: These should be dedicated wallets with LIMITED FUNDS
TRADING_WALLET_PRIVATE_KEY=0x...
EXECUTOR_WALLET_PRIVATE_KEY=0x...

# Flashloan Contract Addresses
FLASHLOAN_CONTRACT_ADDRESS=0x...
MULTIDEX_ARBITRAGE_CORE_ADDRESS=0x...

# API Keys for Price Feeds
CHAINLINK_API_KEY=your_chainlink_api_key
COINGECKO_API_KEY=your_coingecko_api_key

# MEV Protection - Private Relayers
FLASHBOTS_RELAY_URL=https://relay.flashbots.net
FLASHBOTS_AUTH_KEY=your_flashbots_auth_key
BLOXROUTE_API_KEY=your_bloxroute_api_key
EDEN_RELAY_URL=https://api.edennetwork.io/v1/rpc

# Monitoring & Alerting
PAGERDUTY_INTEGRATION_KEY=your_pagerduty_key
OPSGENIE_API_KEY=your_opsgenie_key
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Database (if using external DB for trade history)
DATABASE_URL=postgresql://user:password@host:5432/arbitrage_db

# Multi-Signature Wallet (for large operations)
MULTISIG_WALLET_ADDRESS=0x...
MULTISIG_REQUIRED_SIGNATURES=3
MULTISIG_SIGNERS=0x...,0x...,0x...

# Circuit Breaker & Safety
EMERGENCY_CONTACT_EMAIL=security@your-domain.com
EMERGENCY_PHONE=+1-555-0100

# Encryption Keys (for encrypted wallet storage)
WALLET_ENCRYPTION_PASSWORD=your_very_strong_password_here
```

### Loading Environment Variables

#### Python

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access variables
rpc_url = os.getenv('RPC_ETHEREUM')
private_key = os.getenv('TRADING_WALLET_PRIVATE_KEY')

# Validate required variables
required_vars = ['RPC_ETHEREUM', 'TRADING_WALLET_PRIVATE_KEY']
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")
```

#### Node.js

```javascript
require('dotenv').config();

const config = {
  rpcUrl: process.env.RPC_ETHEREUM,
  privateKey: process.env.TRADING_WALLET_PRIVATE_KEY
};

// Validate required variables
const requiredVars = ['RPC_ETHEREUM', 'TRADING_WALLET_PRIVATE_KEY'];
for (const varName of requiredVars) {
  if (!process.env[varName]) {
    throw new Error(`Missing required environment variable: ${varName}`);
  }
}
```

## Hardware Wallets & HSM

### Recommended Hardware Security Modules

For production deployments with significant capital:

1. **Ledger Nano X**
   - USB hardware wallet
   - Supports Ethereum and EVM chains
   - Can be integrated via `@ledgerhq/hw-app-eth`

2. **Trezor Model T**
   - Alternative hardware wallet
   - Good web3 integration

3. **AWS CloudHSM**
   - Enterprise-grade HSM
   - FIPS 140-2 Level 3 validated
   - Best for institutional deployments

4. **YubiHSM 2**
   - Affordable HSM option
   - Good for small-to-medium deployments

### Integration Example (Ledger)

```javascript
const TransportNodeHid = require("@ledgerhq/hw-transport-node-hid");
const AppEth = require("@ledgerhq/hw-app-eth").default;
const { ethers } = require("ethers");

async function signWithLedger(transaction) {
  // Connect to Ledger
  const transport = await TransportNodeHid.create();
  const eth = new AppEth(transport);
  
  // Get address (first account)
  const path = "44'/60'/0'/0/0";
  const { address } = await eth.getAddress(path);
  
  // Sign transaction
  const signature = await eth.signTransaction(
    path,
    transaction.serializeUnsigned().slice(2)
  );
  
  // Add signature to transaction
  const signedTx = ethers.Transaction.from({
    ...transaction,
    signature: {
      v: signature.v,
      r: "0x" + signature.r,
      s: "0x" + signature.s
    }
  });
  
  return signedTx;
}
```

### HSM Best Practices

1. **Separation of Duties**
   - Use different keys for different purposes
   - Trading key (hot, automated)
   - Treasury key (cold, manual approval)
   - Emergency key (cold, multi-sig)

2. **Key Hierarchy**
   ```
   Master Key (Cold Storage, Multi-sig)
   ├── Trading Key 1 (Hot, Max $10k)
   ├── Trading Key 2 (Hot, Max $10k)
   ├── Treasury Key (Warm, Manual approval)
   └── Emergency Key (Cold, 3-of-5 multi-sig)
   ```

3. **Access Control**
   - Limit who can access HSM
   - Require 2FA for HSM access
   - Audit all HSM operations
   - Regular key rotation

## Multi-Signature Requirements

### Recommended Multi-Sig Setup

Use Gnosis Safe for multi-signature operations:

1. **Deployment & Upgrades**: 3-of-5 signatures
2. **Large Withdrawals (>$50k)**: 2-of-3 signatures
3. **Emergency Actions**: 3-of-5 signatures

### Example Multi-Sig Contract Interaction

```solidity
// Safe multi-sig wallet interaction
contract SafeProxy {
    address public safeAddress;
    
    function executeWithMultiSig(
        address to,
        uint256 value,
        bytes memory data,
        bytes[] memory signatures
    ) external {
        require(signatures.length >= requiredSignatures, "Not enough signatures");
        
        // Verify signatures
        for (uint i = 0; i < signatures.length; i++) {
            address signer = recoverSigner(to, value, data, signatures[i]);
            require(isOwner(signer), "Invalid signer");
        }
        
        // Execute transaction
        (bool success, ) = to.call{value: value}(data);
        require(success, "Transaction failed");
    }
}
```

### Implementation in Python

```python
from eth_account import Account
from web3 import Web3

class MultiSigManager:
    def __init__(self, safe_address, required_sigs, owners):
        self.safe_address = safe_address
        self.required_sigs = required_sigs
        self.owners = owners
        self.pending_txs = {}
    
    def propose_transaction(self, to, value, data, proposer_key):
        """Propose a transaction for multi-sig approval"""
        tx_hash = Web3.keccak(text=f"{to}{value}{data}")
        
        # Sign with proposer
        signature = Account.sign_message(tx_hash, proposer_key)
        
        self.pending_txs[tx_hash] = {
            "to": to,
            "value": value,
            "data": data,
            "signatures": [signature],
            "signers": [Account.from_key(proposer_key).address]
        }
        
        return tx_hash
    
    def approve_transaction(self, tx_hash, approver_key):
        """Approve a pending transaction"""
        if tx_hash not in self.pending_txs:
            raise ValueError("Transaction not found")
        
        # Sign with approver
        signature = Account.sign_message(tx_hash, approver_key)
        approver_address = Account.from_key(approver_key).address
        
        if approver_address not in self.owners:
            raise ValueError("Not an owner")
        
        if approver_address in self.pending_txs[tx_hash]["signers"]:
            raise ValueError("Already signed")
        
        self.pending_txs[tx_hash]["signatures"].append(signature)
        self.pending_txs[tx_hash]["signers"].append(approver_address)
        
        # Check if we have enough signatures
        if len(self.pending_txs[tx_hash]["signatures"]) >= self.required_sigs:
            return self.execute_transaction(tx_hash)
        
        return None
    
    def execute_transaction(self, tx_hash):
        """Execute transaction once enough signatures collected"""
        tx = self.pending_txs[tx_hash]
        
        # Execute via Safe contract
        # (Implementation would interact with Gnosis Safe contract)
        
        return tx_hash
```

## Key Rotation

### Rotation Schedule

- **Hot Wallets (Trading)**: Every 30 days
- **Warm Wallets (Treasury)**: Every 90 days
- **Cold Wallets (Emergency)**: Every 180 days
- **API Keys**: Every 60 days

### Rotation Procedure

1. **Before Rotation**
   - Document current key usage
   - Prepare new keys
   - Test new keys in staging
   - Schedule downtime window

2. **During Rotation**
   ```bash
   # 1. Generate new key
   python3 << EOF
   from eth_account import Account
   account = Account.create()
   print(f"Address: {account.address}")
   print(f"Private Key: {account.key.hex()}")
   EOF
   
   # 2. Update .env file
   # OLD_TRADING_WALLET_PRIVATE_KEY=0x... (keep for rollback)
   # TRADING_WALLET_PRIVATE_KEY=0x... (new key)
   
   # 3. Fund new wallet
   # Transfer funds from old wallet to new wallet
   
   # 4. Update contract permissions if needed
   
   # 5. Restart services
   systemctl restart arbitrage-system
   
   # 6. Verify new key is working
   
   # 7. Withdraw remaining funds from old wallet
   
   # 8. Archive old key securely
   ```

3. **After Rotation**
   - Verify all systems using new key
   - Monitor for issues
   - Update documentation
   - Archive old key

### Automated Rotation Script

```python
#!/usr/bin/env python3
"""
Automated key rotation script
Run monthly via cron: 0 0 1 * * /path/to/rotate_keys.py
"""

import os
from eth_account import Account
from web3 import Web3
from datetime import datetime

def rotate_trading_wallet():
    """Rotate trading wallet key"""
    print(f"[{datetime.now()}] Starting key rotation...")
    
    # 1. Create new account
    new_account = Account.create()
    print(f"New wallet address: {new_account.address}")
    
    # 2. Get old key
    old_key = os.getenv('TRADING_WALLET_PRIVATE_KEY')
    old_account = Account.from_key(old_key)
    
    # 3. Transfer funds
    w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_ETHEREUM')))
    balance = w3.eth.get_balance(old_account.address)
    
    if balance > 0:
        # Reserve some for gas
        transfer_amount = balance - w3.to_wei(0.01, 'ether')
        
        tx = {
            'from': old_account.address,
            'to': new_account.address,
            'value': transfer_amount,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(old_account.address)
        }
        
        signed = old_account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        
        print(f"Transfer tx: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transfer confirmed in block {receipt['blockNumber']}")
    
    # 4. Update .env file
    env_file = '.env'
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    with open(env_file, 'w') as f:
        for line in lines:
            if line.startswith('TRADING_WALLET_PRIVATE_KEY='):
                f.write(f"# Rotated on {datetime.now()}\n")
                f.write(f"# OLD_TRADING_WALLET_PRIVATE_KEY={old_key}\n")
                f.write(f"TRADING_WALLET_PRIVATE_KEY={new_account.key.hex()}\n")
            else:
                f.write(line)
    
    # 5. Archive old key
    with open(f"keys_archive/{datetime.now().strftime('%Y%m%d')}_old.key", 'w') as f:
        f.write(old_key)
    
    print("[✓] Key rotation complete")
    print("    Please restart the arbitrage system")
    
    return new_account.address

if __name__ == "__main__":
    rotate_trading_wallet()
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] All secrets stored in environment variables
- [ ] No hardcoded credentials in code
- [ ] `.env` file in `.gitignore`
- [ ] Hardware wallet configured for large operations
- [ ] Multi-sig wallet set up with proper threshold
- [ ] Key rotation schedule documented
- [ ] Emergency procedures documented
- [ ] Access control lists updated
- [ ] Monitoring and alerting configured
- [ ] Backup keys stored in secure offline location

### Production Environment Variables

```bash
# Production .env template
NODE_ENV=production

# Use private RPC endpoints
RPC_ETHEREUM=https://private-rpc.production.example.com
RPC_POLYGON=https://private-rpc-polygon.production.example.com

# Production keys (should be from HSM or hardware wallet)
TRADING_WALLET_PRIVATE_KEY=USE_HSM_OR_HARDWARE_WALLET
TREASURY_WALLET_ADDRESS=0x... # Read-only, funded via multi-sig

# Production API keys (rate-limited)
CHAINLINK_API_KEY=prod_key_...
COINGECKO_API_KEY=pro_api_key_...

# Enable all monitoring
ENABLE_PROMETHEUS=true
ENABLE_GRAFANA=true
ENABLE_PAGERDUTY=true
ENABLE_CIRCUIT_BREAKER=true

# Production safety limits
MAX_LOSS_PER_TRADE_USD=500
MAX_LOSS_PER_DAY_USD=5000
MAX_POSITION_SIZE_USD=50000
```

## Emergency Procedures

### Compromised Key Response

If a key is compromised:

1. **Immediate Actions** (within 5 minutes)
   ```bash
   # Activate emergency shutdown
   python3 << EOF
   from circuit_breaker import get_circuit_breaker
   cb = get_circuit_breaker()
   cb.emergency_stop("KEY_COMPROMISED")
   EOF
   
   # Pause all trading
   # Stop all services
   systemctl stop arbitrage-system
   ```

2. **Within 15 minutes**
   - Transfer all funds to secure backup wallet
   - Revoke compromised key permissions
   - Generate new keys
   - Update all services with new keys

3. **Within 1 hour**
   - Complete forensic analysis
   - Identify breach source
   - Patch vulnerabilities
   - Notify relevant parties

4. **Within 24 hours**
   - Complete incident report
   - Rotate all potentially affected keys
   - Review and update security procedures

### Emergency Contact List

Maintain an up-to-date contact list:

```yaml
# emergency_contacts.yaml
contacts:
  - role: "System Administrator"
    name: "John Doe"
    phone: "+1-555-0100"
    email: "john@example.com"
    
  - role: "Security Lead"
    name: "Jane Smith"
    phone: "+1-555-0101"
    email: "jane@example.com"
    
  - role: "On-Call Engineer"
    phone: "+1-555-0102"
    pagerduty: "engineer@example.pagerduty.com"

procedures:
  key_compromise:
    severity: "CRITICAL"
    response_time: "5 minutes"
    escalation: ["System Administrator", "Security Lead"]
    
  circuit_breaker_trigger:
    severity: "HIGH"
    response_time: "15 minutes"
    escalation: ["On-Call Engineer"]
```

## Security Audit Checklist

Regular security audits should verify:

- [ ] No secrets in version control (git history scan)
- [ ] All keys rotated on schedule
- [ ] Access logs reviewed
- [ ] Multi-sig wallet functioning correctly
- [ ] Hardware wallet firmware up-to-date
- [ ] Emergency procedures tested
- [ ] Backup keys verified and accessible
- [ ] Dependencies scanned for vulnerabilities
- [ ] Encrypted storage verified
- [ ] Monitoring and alerting functional

## Additional Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [Gnosis Safe Documentation](https://docs.gnosis-safe.io/)
- [Hardware Wallet Integration Guide](https://docs.ethers.io/v5/api/signer/#Wallet)

## Support

For security concerns, contact:
- Email: security@example.com
- Emergency Hotline: +1-555-0100
- PagerDuty: security@example.pagerduty.com
