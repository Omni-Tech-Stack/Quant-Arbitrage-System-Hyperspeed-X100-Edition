# 🎯 ML Model Integration & Execution Modes

## Overview

The Quant Arbitrage System now features **two clear execution modes** with full ML model integration:

### ✅ Execution Modes

1. **SIMULATION Mode** 🎓
   - Paper trading with mock executions
   - Shows what WOULD happen
   - Safe learning environment
   - 100% risk-free testing

2. **LIVE Mode** 💰
   - 100% automation with real executions
   - Real money, real transactions
   - **BONUS**: 5-second manual execution window for hot routes
     - Press **'M'** to manually execute
     - Press **'S'** to skip
     - Auto-executes after timeout

## 🚀 Quick Start

### Run in SIMULATION Mode (Safe Practice)

```bash
# Test mode with simulation
python main_quant_hybrid_orchestrator.py --test --mode SIMULATION

# Production simulation mode
python main_quant_hybrid_orchestrator.py --mode SIMULATION
```

### Run in LIVE Mode (Real Money)

```bash
# Test mode with live settings
python main_quant_hybrid_orchestrator.py --test --mode LIVE

# Production live mode (CAUTION: Real executions!)
python main_quant_hybrid_orchestrator.py --mode LIVE
```

## 🧠 ML Model Integration

### Dual AI ML Engine

The system uses a **Dual AI architecture** for superior performance:

1. **Primary Model**: XGBoost
   - High accuracy
   - Complex pattern recognition
   - Trained on simulation metrics

2. **ONNX Model** (Optional)
   - Optimized for ultra-low latency
   - Sub-millisecond inference
   - Production-ready deployment

### Training Models

```bash
# Train on synthetic data (for testing)
python train_dual_ai_models.py --samples 1000

# Train on historical data
python train_dual_ai_models.py --data-source historical

# Validate models after training
python train_dual_ai_models.py --validate
```

### Model Features

The ML models score opportunities based on:

- **Hops**: Number of swaps in the arbitrage path
- **Gross Profit**: Expected profit before costs
- **Gas Cost**: Estimated transaction fees
- **Estimated Profit**: Net profit after all costs
- **Liquidity Score**: Pool liquidity assessment
- **Price Impact**: Expected price movement
- **Slippage Estimate**: Estimated slippage
- **Confidence**: Route reliability score
- **Time of Day**: Market timing factor
- **Volatility Indicator**: Historical price volatility

## 🔥 Hot Route Detection

The system automatically detects "hot routes" based on:

- **ML Score** > 0.8
- **Estimated Profit** > $50
- **Confidence** > 0.85

When a hot route is detected in LIVE mode:
1. System pauses execution
2. Displays opportunity details
3. Waits 5 seconds for manual decision
4. User can press 'M' to execute or 'S' to skip
5. Auto-executes after timeout

## 📊 Statistics & Monitoring

### Execution Statistics

The system tracks comprehensive statistics for both modes:

**SIMULATION Mode:**
- Total opportunities detected
- Mock executions performed
- Total paper profit
- Success rate

**LIVE Mode:**
- Total opportunities detected
- Real executions performed
- Manual vs auto executions
- Opportunities skipped
- Total real profit

### View Statistics

```python
from execution_mode_manager import ExecutionModeManager, ExecutionMode

manager = ExecutionModeManager(mode=ExecutionMode.SIMULATION)
# ... execute opportunities ...
manager.print_statistics()
```

## ⚙️ Configuration

Edit `config/config.py` to customize:

```python
# Execution Mode (SIMULATION or LIVE)
EXECUTION_MODE = "SIMULATION"  # Start in safe mode

# Manual Execution Window
ENABLE_MANUAL_WINDOW = True  # Enable 5-second window
MANUAL_WINDOW_DURATION = 5   # Seconds

# Hot Route Thresholds
HOT_ROUTE_ML_SCORE_THRESHOLD = 0.8
HOT_ROUTE_PROFIT_THRESHOLD = 50.0
HOT_ROUTE_CONFIDENCE_THRESHOLD = 0.85

# ML Model Configuration
USE_DUAL_AI_ENGINE = True     # Use Dual AI (XGBoost + ONNX)
ML_MODEL_DIR = "./models"     # Model directory
```

## 🧪 Testing

### Run Integration Tests

```bash
# Test ML integration with both modes
python test_ml_integration.py
```

This tests:
- ✅ SIMULATION mode execution
- ✅ LIVE mode execution
- ✅ Hot route detection
- ✅ ML scoring
- ✅ Trade result logging

### Test Individual Components

```bash
# Test execution mode manager
python execution_mode_manager.py

# Test dual AI ML engine
python dual_ai_ml_engine.py

# Test orchestrator in test mode
python main_quant_hybrid_orchestrator.py --test
```

## 📁 File Structure

```
.
├── execution_mode_manager.py      # Execution mode handling
├── dual_ai_ml_engine.py           # Dual AI ML engine (XGBoost + ONNX)
├── ml_model.py                    # Simple ML model (fallback)
├── train_dual_ai_models.py        # Model training script
├── main_quant_hybrid_orchestrator.py  # Main orchestrator
├── test_ml_integration.py         # Integration tests
├── config/
│   └── config.py                  # Configuration file
└── models/                        # ML model files
    ├── xgboost_primary.pkl        # Trained XGBoost model
    ├── scaler.pkl                 # Feature scaler
    ├── onnx_model.onnx           # ONNX optimized model (optional)
    ├── training_metadata.json     # Training info
    └── trade_log.jsonl           # Trade results log
```

## 🎓 Usage Examples

### Example 1: Test in Simulation Mode

```python
from execution_mode_manager import ExecutionModeManager, ExecutionMode
from dual_ai_ml_engine import DualAIMLEngine

# Initialize components
ml_engine = DualAIMLEngine()
manager = ExecutionModeManager(mode=ExecutionMode.SIMULATION)

# Score opportunities
opportunities = [...] # Your opportunities
best_opp = ml_engine.score_opportunities(opportunities)

# Execute in simulation
def execute_fn(opp):
    # Your execution logic
    return {'success': True, 'tx_hash': '0x...', 'actual_profit': 50.0}

result = manager.execute_opportunity(best_opp, execute_fn)
print(f"Paper profit: ${result['actual_profit']:.2f}")
```

### Example 2: Live Mode with Manual Window

```python
from execution_mode_manager import ExecutionModeManager, ExecutionMode
from dual_ai_ml_engine import DualAIMLEngine

# Initialize in LIVE mode
ml_engine = DualAIMLEngine()
manager = ExecutionModeManager(
    mode=ExecutionMode.LIVE,
    enable_manual_window=True,
    manual_window_duration=5
)

# Score and execute
best_opp = ml_engine.score_opportunities(opportunities)

# This will show manual window for hot routes
result = manager.execute_opportunity(
    best_opp, 
    execute_fn,
    is_hot_route=True  # Triggers manual window
)
```

## 🔐 Safety Features

1. **Defaults to SIMULATION** - Safe by default
2. **Manual Confirmation** - Review hot routes before execution
3. **Paper Trading** - Test strategies risk-free
4. **Statistics Tracking** - Monitor performance
5. **Trade Logging** - All trades logged for analysis

## 📈 Performance

- **ML Scoring**: Sub-millisecond with ONNX
- **Manual Window**: 5-second default (configurable)
- **Success Rate**: Tracked per mode
- **Profit Tracking**: Real-time statistics

## 🚨 Important Notes

### SIMULATION Mode
- ✅ 100% safe - no real transactions
- ✅ Perfect for testing and learning
- ✅ Shows realistic profit estimates
- ✅ Tracks paper trading performance

### LIVE Mode
- ⚠️ Uses real money
- ⚠️ Real blockchain transactions
- ⚠️ Gas fees apply
- ⚠️ Review hot routes carefully
- ✅ Manual control for important decisions

## 🎯 Best Practices

1. **Always test in SIMULATION first**
2. **Review hot route criteria** before LIVE mode
3. **Monitor statistics** regularly
4. **Retrain models** with real trade data
5. **Start with small amounts** in LIVE mode
6. **Use manual window** for high-value trades

## 🔄 Model Retraining

Models automatically log trade results for retraining:

```bash
# Retrain with accumulated trade data
python train_dual_ai_models.py --data-source historical

# This uses logged results from:
# models/trade_log.jsonl
```

## 📞 Support

For issues or questions:
1. Check configuration in `config/config.py`
2. Review test output from `test_ml_integration.py`
3. Check model files in `./models/`
4. Review trade logs in `./models/trade_log.jsonl`

## 🎉 Summary

✅ **2 Clear Modes**: SIMULATION (safe) and LIVE (real money)  
✅ **ML Integration**: Dual AI with XGBoost + ONNX  
✅ **Manual Control**: 5-second window for hot routes  
✅ **Safety First**: Defaults to simulation mode  
✅ **Full Monitoring**: Comprehensive statistics tracking  
✅ **Production Ready**: Tested and validated  

Start in **SIMULATION** mode to learn, then switch to **LIVE** when ready! 🚀
