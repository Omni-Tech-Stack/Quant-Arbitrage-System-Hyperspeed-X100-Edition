# Security Considerations for Web3 Integration

## Overview

This document outlines important security considerations when deploying the Web3 and wallet integration in production environments.

## 🔐 Critical Security Measures

### 1. Rate Limiting (Required for Production)

The API endpoints are **NOT rate-limited by default**. You MUST implement rate limiting in production to prevent:
- Denial of Service (DoS) attacks
- Brute force attacks on wallet operations
- Resource exhaustion

**Recommended Solution - Using Express Rate Limit:**

```javascript
// Install: npm install express-rate-limit
const rateLimit = require('express-rate-limit');

// Apply to all requests
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

app.use(limiter);

// Stricter limit for sensitive wallet operations
const walletLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10, // Only 10 wallet operations per 15 minutes
  message: 'Too many wallet operations, please try again later.'
});

app.use('/api/wallet', walletLimiter);
```

**Alternative: Nginx Rate Limiting**

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://localhost:3001;
        }
    }
}
```

### 2. Wallet File Storage

**Default Behavior:**
- Wallets are stored in `backend/wallets/` directory
- Files are encrypted with user-provided passwords
- Directory is in `.gitignore` to prevent accidental commits

**Production Recommendations:**
1. Store wallet files in a secure, encrypted volume
2. Use hardware security modules (HSM) for production keys
3. Implement file permission restrictions (chmod 600)
4. Regular backup of encrypted wallet files to secure storage

```bash
# Set restrictive permissions on wallets directory
chmod 700 backend/wallets
chmod 600 backend/wallets/*.json
```

### 3. Private Key Handling

**NEVER:**
- ❌ Log private keys or mnemonics
- ❌ Return private keys in API responses without explicit request
- ❌ Store private keys in plaintext
- ❌ Commit wallet files to version control
- ❌ Send private keys over unencrypted connections

**ALWAYS:**
- ✅ Use HTTPS in production
- ✅ Encrypt wallet files with strong passwords
- ✅ Use environment variables for production keys
- ✅ Implement password strength requirements
- ✅ Use separate wallets for different environments

### 4. HTTPS/TLS

**Development:**
```javascript
// Development only (HTTP is acceptable)
const PORT = 3001;
server.listen(PORT);
```

**Production:**
```javascript
const https = require('https');
const fs = require('fs');

const options = {
  key: fs.readFileSync('/path/to/private-key.pem'),
  cert: fs.readFileSync('/path/to/certificate.pem')
};

https.createServer(options, app).listen(443);
```

Or use a reverse proxy (recommended):
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:3001;
    }
}
```

### 5. Input Validation

The API includes input validation for:
- Address format validation (checksummed addresses)
- Path traversal prevention in file operations
- Type checking for critical parameters

**Additional Recommendations:**
```javascript
// Validate all user inputs
const { body, validationResult } = require('express-validator');

app.post('/api/wallet/create', 
  body('label').isString().trim().escape(),
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }
    // Continue with wallet creation
  }
);
```

### 6. Password Security

**Minimum Requirements:**
- Length: At least 12 characters
- Complexity: Mix of uppercase, lowercase, numbers, and symbols
- No dictionary words or common patterns

**Example Validation:**
```javascript
function validatePassword(password) {
  const minLength = 12;
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumbers = /\d/.test(password);
  const hasSpecialChar = /[!@#$%^&*]/.test(password);
  
  return password.length >= minLength && 
         hasUpperCase && 
         hasLowerCase && 
         hasNumbers && 
         hasSpecialChar;
}
```

### 7. Environment Variables

Use environment variables for sensitive configuration:

```bash
# .env file (DO NOT COMMIT!)
WALLET_PASSWORD=your-secure-password
RPC_ETHEREUM=https://your-private-rpc-url
API_KEY_INFURA=your-infura-api-key
```

```javascript
require('dotenv').config();

const config = {
  walletPassword: process.env.WALLET_PASSWORD,
  rpcUrl: process.env.RPC_ETHEREUM
};
```

### 8. RPC Endpoint Security

**Public RPCs (Development Only):**
- Rate limited
- May log requests
- Potential privacy concerns

**Production Recommendations:**
- Use private RPC providers (Infura, Alchemy, QuickNode)
- Implement API key rotation
- Monitor usage and set alerts
- Use multiple RPC endpoints for redundancy

```javascript
const rpcEndpoints = [
  process.env.RPC_PRIMARY,
  process.env.RPC_FALLBACK_1,
  process.env.RPC_FALLBACK_2
];

// Implement fallback logic
async function getProvider() {
  for (const rpcUrl of rpcEndpoints) {
    try {
      const provider = new ethers.JsonRpcProvider(rpcUrl);
      await provider.getBlockNumber(); // Test connection
      return provider;
    } catch (error) {
      console.log(`RPC ${rpcUrl} failed, trying next...`);
    }
  }
  throw new Error('All RPC endpoints failed');
}
```

### 9. Transaction Signing Security

**Best Practices:**
1. Always verify transaction parameters before signing
2. Implement transaction simulation before execution
3. Use gas limit caps to prevent excessive fees
4. Implement approval workflows for high-value transactions

```javascript
// Example: Pre-flight checks before signing
async function safeSignTransaction(address, transaction) {
  // 1. Validate transaction parameters
  if (!ethers.isAddress(transaction.to)) {
    throw new Error('Invalid recipient address');
  }
  
  // 2. Check gas price
  const gasPrice = await provider.getFeeData();
  if (transaction.gasPrice > gasPrice.maxFeePerGas * 1.5) {
    throw new Error('Gas price too high');
  }
  
  // 3. Simulate transaction
  try {
    await provider.estimateGas(transaction);
  } catch (error) {
    throw new Error('Transaction simulation failed');
  }
  
  // 4. Sign transaction
  return walletManager.signTransaction(address, transaction);
}
```

### 10. Audit Logging

Implement comprehensive logging for security audits:

```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'audit.log' })
  ]
});

// Log all sensitive operations
app.post('/api/wallet/create', async (req, res) => {
  logger.info({
    action: 'wallet_create',
    timestamp: new Date().toISOString(),
    ip: req.ip,
    userAgent: req.headers['user-agent']
  });
  
  // Continue with wallet creation
});
```

### 11. Multi-Signature Wallets

For high-value operations, consider implementing multi-signature requirements:

```javascript
// Example: Require multiple signatures for transactions over threshold
const MULTISIG_THRESHOLD = ethers.parseEther('10'); // 10 ETH

async function executeTransaction(tx) {
  if (tx.value > MULTISIG_THRESHOLD) {
    // Require multiple approvals
    const approvals = await getApprovals(tx);
    if (approvals.length < REQUIRED_APPROVALS) {
      throw new Error('Insufficient approvals for high-value transaction');
    }
  }
  
  // Execute transaction
  return sendTransaction(tx);
}
```

### 12. Access Control

Implement role-based access control (RBAC):

```javascript
const roles = {
  ADMIN: ['wallet:create', 'wallet:delete', 'wallet:export'],
  TRADER: ['wallet:sign', 'transaction:send'],
  VIEWER: ['wallet:view', 'balance:check']
};

function checkPermission(userRole, action) {
  return roles[userRole]?.includes(action) || false;
}

// Middleware
function requirePermission(action) {
  return (req, res, next) => {
    const userRole = req.user?.role; // From auth middleware
    if (!checkPermission(userRole, action)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    next();
  };
}

app.post('/api/wallet/create', 
  requirePermission('wallet:create'),
  async (req, res) => {
    // Create wallet
  }
);
```

## 🛡️ Security Checklist

Before deploying to production, ensure:

- [ ] Rate limiting is implemented
- [ ] HTTPS/TLS is configured
- [ ] Environment variables are used for secrets
- [ ] Wallet files are stored securely with restricted permissions
- [ ] Input validation is comprehensive
- [ ] Audit logging is enabled
- [ ] RPC endpoints are private/authenticated
- [ ] Password requirements are enforced
- [ ] Multi-signature is implemented for high-value operations
- [ ] Access control/RBAC is configured
- [ ] Regular security audits are scheduled
- [ ] Backup procedures are tested
- [ ] Incident response plan is documented
- [ ] Dependencies are regularly updated
- [ ] Security headers are configured
- [ ] CORS is properly restricted

## 📊 Monitoring & Alerts

Set up monitoring for:
- Failed authentication attempts
- Unusual transaction patterns
- API error rates
- Gas price spikes
- Wallet balance changes
- Suspicious IP addresses

Example with monitoring service:
```javascript
const Sentry = require('@sentry/node');

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0
});

// Track errors
app.use(Sentry.Handlers.errorHandler());

// Custom security alerts
function alertSecurityIncident(type, details) {
  Sentry.captureMessage(`Security Incident: ${type}`, {
    level: 'warning',
    extra: details
  });
}
```

## 🔄 Regular Maintenance

1. **Weekly:**
   - Review audit logs
   - Check for unusual activity
   - Verify backup integrity

2. **Monthly:**
   - Update dependencies
   - Review and rotate API keys
   - Test disaster recovery

3. **Quarterly:**
   - Security audit
   - Penetration testing
   - Review and update security policies

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Ethereum Smart Contract Security Best Practices](https://consensys.github.io/smart-contract-best-practices/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Express Security Best Practices](https://expressjs.com/en/advanced/best-practice-security.html)

## 🚨 Incident Response

If a security incident occurs:

1. **Immediately:**
   - Disable affected endpoints
   - Revoke compromised credentials
   - Notify stakeholders

2. **Within 1 hour:**
   - Assess the scope of the breach
   - Secure backups
   - Begin forensic analysis

3. **Within 24 hours:**
   - Implement fixes
   - Deploy patches
   - Update security measures

4. **Within 1 week:**
   - Complete incident report
   - Update security documentation
   - Conduct post-mortem review

## Contact

For security concerns or to report vulnerabilities, please contact the security team immediately.

**Remember: Security is not a one-time implementation but an ongoing process!**
