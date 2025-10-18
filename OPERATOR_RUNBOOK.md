# Operator Runbook

## Overview

This runbook provides step-by-step procedures for operating the Quant Arbitrage System. It covers routine operations, troubleshooting, incident response, and emergency procedures.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Monitoring & Alerts](#monitoring--alerts)
3. [Troubleshooting](#troubleshooting)
4. [Incident Response](#incident-response)
5. [Emergency Procedures](#emergency-procedures)
6. [Maintenance](#maintenance)

## Daily Operations

### Morning Checklist (Start of Trading Day)

```bash
#!/bin/bash
# scripts/daily-startup.sh

echo "Daily Startup Checklist"
echo "======================="

# 1. Check system status
echo "1. Checking system status..."
curl http://localhost:3001/api/health

# 2. Verify wallet balances
echo "2. Verifying wallet balances..."
python3 << EOF
from circuit_breaker import get_circuit_breaker
cb = get_circuit_breaker()
status = cb.get_status()
print(f"Circuit Breaker: {status['circuit_open']}")
print(f"Emergency Shutdown: {status['emergency_shutdown']}")
EOF

# 3. Check recent trades
echo "3. Reviewing recent trades..."
python3 << EOF
from pnl_accounting import get_accounting
accounting = get_accounting()
summary = accounting.get_pnl_summary("today")
print(f"Today's P&L: ${summary['net_profit_usd']}")
print(f"Success Rate: {summary['success_rate']}")
EOF

# 4. Verify liquidity providers
echo "4. Checking liquidity providers..."
python3 << EOF
from liquidity_provider_failover import get_failover
failover = get_failover()
status = failover.get_provider_status()
for name, info in status.items():
    print(f"{name}: {info['status']} - Success: {info['success_rate']}")
EOF

# 5. Check gas prices
echo "5. Current gas prices..."
curl -s https://api.etherscan.io/api?module=gastracker&action=gasoracle | jq

# 6. Review logs for errors
echo "6. Checking for errors in logs..."
tail -n 100 logs/system.log | grep -i error | tail -n 10

echo ""
echo "Startup checks complete. Ready for trading."
```

Run the morning checklist:

```bash
chmod +x scripts/daily-startup.sh
./scripts/daily-startup.sh
```

### Evening Checklist (End of Trading Day)

```bash
#!/bin/bash
# scripts/daily-shutdown.sh

echo "Daily Shutdown Checklist"
echo "========================"

# 1. Generate daily P&L report
echo "1. Generating daily P&L report..."
python3 << EOF
from pnl_accounting import get_accounting
from datetime import datetime

accounting = get_accounting()
summary = accounting.get_pnl_summary("today")

print(f"\nDaily Summary - {datetime.now().strftime('%Y-%m-%d')}")
print("=" * 50)
print(f"Total Trades: {summary['total_trades']}")
print(f"Successful: {summary['successful_trades']}")
print(f"Failed: {summary['failed_trades']}")
print(f"Success Rate: {summary['success_rate']}")
print(f"Net Profit: ${summary['net_profit_usd']:.2f}")
print(f"Total Costs: ${summary['total_costs']['total_usd']:.2f}")
print("=" * 50)

# Export to CSV
today = datetime.now().strftime('%Y-%m-%d')
accounting.export_to_csv(f"reports/trades-{today}.csv", "today")
print(f"\nTrades exported to reports/trades-{today}.csv")
EOF

# 2. Check for anomalies
echo "2. Checking for anomalies..."
python3 << EOF
from observability import get_metrics
metrics = get_metrics()
summary = metrics.get_metrics_summary()

anomalies = summary.get('anomalies', {})
if anomalies.get('total', 0) > 0:
    print(f"⚠️  {anomalies['total']} anomalies detected today")
    for anomaly in anomalies.get('recent', [])[:5]:
        print(f"  - {anomaly['type']}: {anomaly.get('value', 'N/A')}")
else:
    print("✓ No anomalies detected")
EOF

# 3. Archive logs
echo "3. Archiving logs..."
TODAY=$(date +%Y-%m-%d)
mkdir -p logs/archive
cp logs/*.log logs/archive/${TODAY}_
gzip logs/archive/${TODAY}_*.log

# 4. Reconcile accounts
echo "4. Reconciling accounts..."
python3 << EOF
from pnl_accounting import get_accounting
accounting = get_accounting()
reconciliation = accounting.reconcile()
if reconciliation['reconciled']:
    print("✓ Accounts reconciled successfully")
else:
    print(f"⚠️  Reconciliation mismatch: ${reconciliation['difference']:.2f}")
EOF

echo ""
echo "Shutdown checks complete."
```

Run the evening checklist:

```bash
chmod +x scripts/daily-shutdown.sh
./scripts/daily-shutdown.sh
```

## Monitoring & Alerts

### Real-Time Dashboard

Access the monitoring dashboard:

```bash
# Start backend (if not already running)
cd backend && npm start

# Access dashboard
open http://localhost:3000
```

### Key Metrics to Monitor

| Metric | Normal Range | Alert Threshold | Action |
|--------|--------------|-----------------|--------|
| Success Rate | > 80% | < 70% | Investigate recent failures |
| Gas Price | < 100 gwei | > 150 gwei | Pause trading if unprofitable |
| P&L (Hourly) | > $0 | < -$100 | Activate circuit breaker |
| Response Time | < 500ms | > 2000ms | Check RPC endpoints |
| Failed Trades | < 5/hour | > 10/hour | Review execution logic |
| Circuit Breaker | Closed | Open | Investigate trigger reason |

### Alert Response Matrix

#### Critical Alerts (Immediate Response)

| Alert | Response Time | Action |
|-------|--------------|--------|
| Emergency Shutdown Activated | Immediate | Call emergency contact, investigate cause |
| Circuit Breaker Triggered | 5 minutes | Review logs, assess situation, manual override if false positive |
| Large Loss (>$500) | 5 minutes | Pause trading, investigate trade, review logs |
| Security Breach | Immediate | Activate incident response plan, notify security team |

#### High Priority Alerts (15-minute Response)

| Alert | Response Time | Action |
|-------|--------------|--------|
| High Error Rate (>10%) | 15 minutes | Check RPC endpoints, review error logs |
| Low Success Rate (<70%) | 15 minutes | Review market conditions, check gas prices |
| Provider Failure | 15 minutes | Verify failover working, check provider status |
| Unusual Slippage | 15 minutes | Review pool liquidity, adjust trade sizes |

#### Medium Priority Alerts (1-hour Response)

| Alert | Response Time | Action |
|-------|--------------|--------|
| Gas Price Spike | 1 hour | Monitor situation, adjust gas limits if needed |
| Anomaly Detected | 1 hour | Review anomaly details, determine if action needed |
| Rate Limit Hit | 1 hour | Review usage patterns, adjust limits if needed |

## Troubleshooting

### Common Issues

#### 1. Trades Failing

**Symptoms:**
- High failure rate
- Revert messages in logs
- Transactions not being mined

**Diagnosis:**
```bash
# Check recent failed trades
python3 << EOF
from pnl_accounting import get_accounting
accounting = get_accounting()

failed = [t for t in accounting.trades if not t.success][-10:]
for trade in failed:
    print(f"{trade.trade_id}: {trade.revert_reason}")
EOF
```

**Common Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Insufficient gas | Increase gas limit in config |
| Slippage too high | Reduce trade size or increase slippage tolerance |
| Price changed | Enable re-evaluation before submit |
| Insufficient liquidity | Adjust pool depth limits |
| Nonce issues | Restart transaction manager |

#### 2. High Gas Costs

**Symptoms:**
- Gas costs eating into profits
- Trades becoming unprofitable

**Diagnosis:**
```bash
# Check gas statistics
python3 << EOF
from pnl_accounting import get_accounting
accounting = get_accounting()

summary = accounting.get_pnl_summary("today")
total_gas = summary['total_costs']['gas_usd']
total_profit = summary['net_profit_usd']
gas_percentage = (total_gas / (total_profit + total_gas)) * 100

print(f"Total Gas Cost: ${total_gas:.2f}")
print(f"Gas as % of Revenue: {gas_percentage:.1f}%")
EOF
```

**Solutions:**
- Increase minimum profit threshold
- Optimize contract gas usage
- Wait for gas prices to decrease
- Use Layer 2 solutions

#### 3. RPC Endpoint Issues

**Symptoms:**
- Slow response times
- Timeout errors
- Connection failures

**Diagnosis:**
```bash
# Test RPC endpoints
python3 << EOF
from web3 import Web3
import time

endpoints = [
    "https://eth-mainnet.alchemyapi.io/v2/YOUR-KEY",
    "https://rpc.ankr.com/eth",
    "https://eth.llamarpc.com"
]

for endpoint in endpoints:
    try:
        w3 = Web3(Web3.HTTPProvider(endpoint))
        start = time.time()
        block = w3.eth.block_number
        latency = (time.time() - start) * 1000
        print(f"✓ {endpoint}: {latency:.0f}ms (block: {block})")
    except Exception as e:
        print(f"✗ {endpoint}: {e}")
EOF
```

**Solutions:**
- Switch to backup RPC endpoint
- Upgrade to premium RPC service
- Implement request retry logic
- Add connection pooling

#### 4. Liquidity Provider Failures

**Symptoms:**
- Flashloan failures
- Provider marked unhealthy
- Failover activating frequently

**Diagnosis:**
```bash
# Check provider health
python3 << EOF
from liquidity_provider_failover import get_failover
failover = get_failover()

status = failover.get_provider_status()
for name, info in status.items():
    if info['status'] != 'healthy':
        print(f"⚠️  {name}:")
        print(f"   Status: {info['status']}")
        print(f"   Failures: {info['consecutive_failures']}")
        print(f"   Last Error: {info['last_error']}")
EOF
```

**Solutions:**
- Wait for provider to recover
- Manually mark provider online if false positive
- Switch to alternative provider
- Report issue to provider

## Incident Response

### Incident Severity Levels

**P0 - Critical**
- Service completely down
- Security breach
- Large financial loss (>$10k)
- Data loss

**P1 - High**
- Partial service disruption
- Circuit breaker triggered
- Moderate financial loss ($1k-$10k)
- Performance degradation

**P2 - Medium**
- Minor service disruption
- High error rate
- Small financial loss (<$1k)
- Monitoring alerts

**P3 - Low**
- No service impact
- Documentation issues
- Configuration warnings

### Incident Response Procedure

#### 1. Detection & Alert (0-5 minutes)

```bash
# When alert received:
1. Acknowledge alert
2. Assess severity
3. Notify on-call engineer (P0/P1 only)
4. Open incident tracking ticket
```

#### 2. Triage & Assessment (5-15 minutes)

```bash
# Quick assessment:
1. Check system status
2. Review recent changes
3. Check logs for errors
4. Determine impact
5. Escalate if needed
```

#### 3. Mitigation (15-60 minutes)

```bash
# Immediate actions:
# For trading issues:
python3 << EOF
from circuit_breaker import get_circuit_breaker
cb = get_circuit_breaker()
cb.pause_trading("Incident response - [ticket-id]")
EOF

# For security issues:
# 1. Activate emergency shutdown
# 2. Secure affected systems
# 3. Preserve evidence
# 4. Notify security team
```

#### 4. Investigation (1-24 hours)

```bash
# Detailed investigation:
1. Collect all relevant logs
2. Review transaction history
3. Analyze error patterns
4. Identify root cause
5. Document findings
```

#### 5. Resolution (Varies)

```bash
# Implement fix:
1. Develop and test fix
2. Deploy to staging
3. Validate fix
4. Deploy to production
5. Monitor for recurrence
```

#### 6. Post-Mortem (Within 1 week)

```markdown
# Incident Post-Mortem Template

## Incident Summary
- **Date/Time**: [Timestamp]
- **Duration**: [Hours]
- **Severity**: [P0/P1/P2/P3]
- **Impact**: [Description]
- **Financial Loss**: [$X.XX]

## Timeline
- [Time]: Incident detected
- [Time]: Response initiated
- [Time]: Mitigation deployed
- [Time]: Service restored
- [Time]: Root cause identified

## Root Cause
[Detailed explanation]

## Resolution
[What was done to fix]

## Lessons Learned
1. [Lesson 1]
2. [Lesson 2]
3. [Lesson 3]

## Action Items
- [ ] [Action item with owner and due date]
- [ ] [Action item with owner and due date]
- [ ] [Action item with owner and due date]

## Prevention
[How to prevent in future]
```

## Emergency Procedures

### Emergency Shutdown

**When to Use:**
- Security breach detected
- Uncontrolled losses
- Smart contract vulnerability
- System compromise

**Procedure:**

```python
#!/usr/bin/env python3
# Emergency shutdown script

from circuit_breaker import get_circuit_breaker
from alerting import get_alerting
import sys

def emergency_shutdown(reason):
    """Execute emergency shutdown"""
    print("🚨 EXECUTING EMERGENCY SHUTDOWN 🚨")
    print(f"Reason: {reason}")
    
    # 1. Activate circuit breaker
    cb = get_circuit_breaker()
    cb.emergency_stop(reason)
    print("✓ Circuit breaker activated")
    
    # 2. Send alerts
    alerting = get_alerting()
    alerting.alert_emergency_shutdown(reason)
    print("✓ Alerts sent")
    
    # 3. Stop all services
    # (In production, would actually stop services)
    print("✓ Services stopped")
    
    # 4. Log incident
    with open("logs/emergency-shutdown.log", "a") as f:
        from datetime import datetime
        f.write(f"{datetime.now().isoformat()} - {reason}\n")
    print("✓ Incident logged")
    
    print("\n📞 CONTACT EMERGENCY RESPONSE TEAM")
    print("Phone: +1-555-0100")
    print("Email: emergency@example.com")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 emergency_shutdown.py 'reason'")
        sys.exit(1)
    
    reason = " ".join(sys.argv[1:])
    emergency_shutdown(reason)
```

Usage:

```bash
python3 scripts/emergency_shutdown.py "Security breach detected"
```

### Key Compromise Response

If private keys are compromised:

```bash
#!/bin/bash
# Key compromise response

echo "🚨 KEY COMPROMISE RESPONSE 🚨"

# 1. Immediate shutdown
python3 scripts/emergency_shutdown.py "Key compromise"

# 2. Transfer all funds to backup wallet
# (Manual execution required)
echo "Transfer all funds to backup wallet:"
echo "Backup Address: [SECURE_BACKUP_ADDRESS]"

# 3. Revoke compromised key permissions
echo "Revoke all permissions for compromised key"

# 4. Generate new keys
echo "Generating new keys..."
python3 << EOF
from eth_account import Account
new_account = Account.create()
print(f"New Address: {new_account.address}")
print(f"Store private key securely!")
# DO NOT PRINT PRIVATE KEY
EOF

# 5. Notify team
echo "Notifying security team..."
# Send notifications

echo ""
echo "Complete the following manually:"
echo "1. Update all systems with new keys"
echo "2. Test new keys in staging"
echo "3. Gradually resume operations"
echo "4. Conduct post-incident review"
```

## Maintenance

### Weekly Maintenance (Every Monday)

```bash
# Weekly maintenance checklist
- [ ] Review P&L for previous week
- [ ] Check system logs for warnings
- [ ] Review and rotate API keys if needed
- [ ] Test backup and restore procedures
- [ ] Update dependencies (security patches only)
- [ ] Review circuit breaker settings
- [ ] Check disk space and logs rotation
- [ ] Test monitoring and alerting
```

### Monthly Maintenance (First Monday of Month)

```bash
# Monthly maintenance checklist
- [ ] Full security scan
- [ ] Dependency updates (all)
- [ ] Review and optimize gas usage
- [ ] Analyze strategy performance
- [ ] Test disaster recovery
- [ ] Review access controls
- [ ] Update documentation
- [ ] Team security training
- [ ] Performance optimization review
- [ ] Generate monthly reports
```

### Quarterly Maintenance (First Monday of Quarter)

```bash
# Quarterly maintenance checklist
- [ ] External security audit (if applicable)
- [ ] Comprehensive system review
- [ ] Key rotation
- [ ] Infrastructure upgrades
- [ ] Contract upgrades (if needed)
- [ ] Disaster recovery drill
- [ ] Compliance review
- [ ] Insurance policy review
- [ ] Budget and resource planning
```

## Contact Information

### Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Primary On-Call | [Name] | +1-555-0100 | oncall@example.com |
| Secondary On-Call | [Name] | +1-555-0101 | oncall2@example.com |
| Security Lead | [Name] | +1-555-0102 | security@example.com |
| System Admin | [Name] | +1-555-0103 | admin@example.com |

### Escalation Path

1. **Incident Detected** → On-Call Engineer
2. **P0/P1 Incident** → Engineering Manager (within 15 min)
3. **Unresolved** → CTO (within 1 hour)
4. **Security Breach** → Security Lead (immediate)

## Additional Resources

- [SECURITY.md](./SECURITY.md) - Security best practices
- [MAINNET_FORK_TESTING.md](./MAINNET_FORK_TESTING.md) - Testing procedures
- [MEV_PROTECTION.md](./MEV_PROTECTION.md) - MEV protection strategies
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Detailed troubleshooting

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-15 | Initial runbook |
| 1.1 | [Date] | [Changes] |
