#!/bin/bash
# System Monitoring Dashboard for 72hr SIM Run

echo "================================================================================"
echo "  🚀 QUANT ARBITRAGE SYSTEM - LIVE MONITOR"
echo "  MODE: SIMULATION (Paper Trading)"
echo "================================================================================"
echo ""

# Check if system is running
if pgrep -f "main_quant_hybrid_orchestrator" > /dev/null; then
    echo "✅ System Status: RUNNING"
    PID=$(pgrep -f "main_quant_hybrid_orchestrator")
    echo "   PID: $PID"
    echo "   Uptime: $(ps -p $PID -o etime= | tr -d ' ')"
else
    echo "❌ System Status: STOPPED"
    echo ""
    echo "To start: python main_quant_hybrid_orchestrator.py --mode SIMULATION"
    exit 1
fi

echo ""
echo "📊 RECENT ACTIVITY (Last 20 lines):"
echo "--------------------------------------------------------------------------------"
tail -20 full_system_sim_72hr.log | sed 's/^/   /'
echo "--------------------------------------------------------------------------------"

echo ""
echo "📈 STATISTICS:"
echo "   Total Iterations: $(grep -c "ITERATION" full_system_sim_72hr.log || echo "0")"
echo "   Opportunities Found: $(grep -c "ARBITRAGE OPPORTUNITY" full_system_sim_72hr.log || echo "0")"
echo "   Flashloans Approved: $(grep -c "Status: ✅ APPROVED" full_system_sim_72hr.log || echo "0")"
echo "   Flashloans Rejected: $(grep -c "Status: ❌ REJECTED" full_system_sim_72hr.log || echo "0")"
echo ""

echo "💰 PROFIT TRACKING:"
grep "Net Profit (after gas):" full_system_sim_72hr.log | tail -5 | sed 's/^/   /'
echo ""

echo "================================================================================"
echo "  COMMANDS:"
echo "================================================================================"
echo "  📝 Live tail:   tail -f full_system_sim_72hr.log"
echo "  📊 This dashboard: bash monitor_system.sh"
echo "  🔍 Search profits: grep 'Net Profit' full_system_sim_72hr.log"
echo "  ⏹️  Stop system:  kill $PID"
echo ""
echo "  🔴 To switch to LIVE mode:"
echo "     1. Stop: kill $PID"
echo "     2. Edit ..env: MODE=LIVE"
echo "     3. Start: python main_quant_hybrid_orchestrator.py --mode LIVE"
echo "================================================================================"
