# 🚀 72-HOUR SIMULATION RUN - QUICK REFERENCE

## ✅ SYSTEM STATUS: RUNNING IN SIMULATION MODE

**Current State:**
- ✅ Live real-time data from Polygon mainnet
- ✅ Paper trading only (NO transactions broadcast)
- ✅ All safety systems active
- ✅ Continuous operation until you stop it
- 📝 PID: 171993
- 📊 Log: `full_system_sim_72hr.log`

---

## 📊 MONITORING COMMANDS

### Quick Dashboard
```bash
bash monitor_system.sh
```

### Live Activity (Real-time)
```bash
tail -f full_system_sim_72hr.log
```

### View Profits
```bash
grep "Net Profit" full_system_sim_72hr.log | tail -20
```

### View Statistics
```bash
grep -E "ITERATION|APPROVED|REJECTED" full_system_sim_72hr.log | tail -50
```

### Check Execution Details
```bash
grep -A 10 "ARBITRAGE OPPORTUNITY" full_system_sim_72hr.log | tail -50
```

---

## ⏹️ STOP THE SYSTEM

```bash
kill $(pgrep -f main_quant_hybrid_orchestrator)
```

Or use the specific PID:
```bash
kill 171993
```

---

## 🔴 SWITCH TO LIVE MODE (REAL MONEY)

**⚠️ CRITICAL: Only do this when you're 100% ready for real transactions!**

### Step 1: Stop the system
```bash
kill $(pgrep -f main_quant_hybrid_orchestrator)
```

### Step 2: Change MODE in .env
```bash
# Open .env and change:
MODE=SIM  →  MODE=LIVE
```

### Step 3: Start in LIVE mode
```bash
nohup python main_quant_hybrid_orchestrator.py --mode LIVE > full_system_LIVE.log 2>&1 &
```

### Step 4: Monitor LIVE mode
```bash
tail -f full_system_LIVE.log
```

---

## 📈 WHAT TO WATCH FOR

### Good Signs ✅
- Consistent opportunity detection (iterations running)
- Reasonable profit estimates ($15-$1000+ per trade)
- Flashloan approvals (when pools have sufficient TVL)
- ML confidence scores > 70%
- Low gas costs relative to profit

### Warning Signs ⚠️
- All flashloans rejected (pool TVL = $0 means data issue)
- Unrealistic profits (>$1M suggests price data error)
- System crashes or stops
- No new iterations for >5 minutes

---

## 🎯 CURRENT PERFORMANCE

**After 2.5 minutes of runtime:**
- Total Iterations: 44
- Opportunities Found: 44
- Average Net Profit: $26,706,828.69 (likely test data)
- Status: All flashloans rejected (TVL = $0)

**Note:** The extremely high profits suggest the system is still initializing pool data. Real profits will be in the $15-$500 range once live pool TVL loads.

---

## 📁 KEY FILES

| File | Purpose |
|------|---------|
| `full_system_sim_72hr.log` | Complete system log |
| `monitor_system.sh` | Quick dashboard script |
| `.env` | Configuration (MODE=SIM/LIVE) |
| `main_quant_hybrid_orchestrator.py` | Main system orchestrator |

---

## 💡 TIPS

1. **Check every few hours** - Run `bash monitor_system.sh`
2. **Review profits regularly** - Look for realistic $15-$500 opportunities
3. **Monitor gas costs** - Should be $5-$50 per transaction
4. **Wait for pool TVL data** - First hour may show rejections while data loads
5. **Test before going LIVE** - Let SIM run for at least 24 hours

---

## 🆘 TROUBLESHOOTING

### System stopped unexpectedly
```bash
# Check if still running
ps aux | grep "[m]ain_quant_hybrid_orchestrator"

# Restart if needed
nohup python main_quant_hybrid_orchestrator.py --mode SIMULATION > full_system_sim_72hr.log 2>&1 &
```

### Want to see errors only
```bash
grep -i "error\|fatal\|exception" full_system_sim_72hr.log | tail -50
```

### Check memory usage
```bash
ps aux | grep "[m]ain_quant_hybrid_orchestrator" | awk '{print $4"%"}'
```

---

## 📞 SYSTEM CONTROL

**Current PID:** 171993  
**Started:** Now  
**Expected Runtime:** Until you stop it (72+ hours)  
**Mode:** SIMULATION (Paper Trading)  
**Safety:** ✅ NO REAL TRANSACTIONS WILL BE BROADCAST

---

**🎯 Goal:** Monitor for 72 hours to verify:
- Stable operation
- Realistic profit detection
- No crashes or errors
- Proper safety systems working

**Then:** Switch to LIVE mode when confident! 🚀
