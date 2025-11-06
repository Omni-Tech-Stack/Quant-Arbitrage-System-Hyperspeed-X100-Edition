# Polygon Deployment and Simulation Guide

This guide explains how to deploy and test the Universal Flashloan Arbitrage system on Polygon with simulation capabilities.

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Copy the production environment template
cp .env.production .env

# Edit .env with your actual values:
# - POLYGON_RPC: Your Polygon RPC endpoint  
# - PRIVATE_KEY: Your deployment private key
# - POLYGONSCAN_API_KEY: For contract verification
```

### 2. Install Dependencies
```bash
npm install
cd contracts/
npm install
```

### 3. Compile Contracts
```bash
npx hardhat compile
```

### 4. Run Simulation Tests (Recommended)
```bash
# Test with Polygon fork - no real funds needed
SIMULATION_MODE=true npx hardhat test test/PolygonSimulation.test.js --network polygonFork
```

### 5. Deploy to Polygon Mainnet
```bash
# Deploy with simulation testing
npx hardhat run scripts/deploy-polygon-with-simulation.js --network polygon

# Or deploy traditional way
npx hardhat run scripts/deploy-flashloan-system.js --network polygon
```

## 🧪 Simulation Testing Features

The system includes advanced simulation capabilities:

### Fork-based Testing
- Forks Polygon mainnet at latest block
- Funds test accounts with MATIC
- Tests all contract functions without spending real funds

### Performance Testing  
- Gas estimation for different scenarios
- Payload encoding benchmarks
- Multi-provider comparisons

### Integration Testing
- Tests orchestrator integration patterns
- Simulates real arbitrage opportunities
- Validates cross-chain readiness

## 📋 Deployment Checklist

Before mainnet deployment:

- [ ] Environment variables configured
- [ ] Simulation tests passing
- [ ] Private key secured (use hardware wallet)
- [ ] Gas price acceptable
- [ ] Sufficient MATIC for deployment (~50 MATIC)
- [ ] Multisig configured (if using)

## 🔧 Configuration

### Polygon-Specific Settings
```javascript
// Automatically configured for Polygon:
const POLYGON_CONFIG = {
  chainId: 137,
  currency: "MATIC", 
  
  protocols: {
    aaveV3Pool: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    balancerVault: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    
    routers: {
      "QUICKSWAP": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
      "UNISWAP_V3": "0xE592427A0AEce92De3Edee1F18E0157C05861564", 
      "SUSHISWAP": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
      "1INCH": "0x1111111254EEB25477B68fb85Ed929f73A960582"
    }
  }
};
```

### Integration with Main Orchestrator
```python
# Integration example for main_quant_hybrid_orchestrator.py
from integration.polygon_flashloan_integration import PolygonFlashloanExecutor

executor = PolygonFlashloanExecutor(private_key=os.getenv('PRIVATE_KEY'))

# Execute arbitrage from orchestrator
result = executor.execute_simple_arbitrage(
    token_a=opportunity['token_a'],
    token_b=opportunity['token_b'], 
    amount=opportunity['amount'],
    min_profit=opportunity['min_profit']
)

print(f"Transaction: {result.transactionHash.hex()}")
```

## 🎯 Testing Commands

```bash
# Full simulation test suite
npm run test:simulation

# Deploy to local fork for testing  
npm run deploy:fork

# Deploy to Polygon testnet (Mumbai)
npm run deploy:mumbai  

# Deploy to Polygon mainnet
npm run deploy:polygon

# Verify contracts after deployment
npm run verify:polygon
```

## 📊 Post-Deployment

After successful deployment:

1. **Contract Verification**: Contracts are auto-verified on Polygonscan
2. **Integration Files**: Generated in `integration/` directory
3. **ABI Files**: Available in `abi/` directory
4. **Deployment Record**: Saved in `deployments/` directory

## 🛡️ Security Notes

- Use hardware wallet for mainnet deployments
- Test thoroughly on Mumbai testnet first
- Monitor gas prices during deployment
- Set up monitoring and alerts post-deployment
- Use multisig for admin functions

## 📞 Support

For deployment issues:
- Check simulation tests pass first
- Verify environment configuration
- Ensure sufficient MATIC balance
- Review hardhat console for errors