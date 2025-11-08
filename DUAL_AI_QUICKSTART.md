# Dual AI System - Quick Reference

## Overview
The Dual AI system combines a high-accuracy XGBoost model with an ultra-fast ONNX-optimized model for arbitrage opportunity scoring.

## Required Dependencies

**Critical ML packages:**
```bash
pip3 install scikit-learn xgboost onnx onnxruntime skl2onnx
```

Or use the complete requirements file:
```bash
pip3 install -r requirements.txt
```

## Verify Installation

```bash
# Check all dependencies
python3 scripts/verify_dependencies.py

# Should show all ML/ONNX packages installed
```

## Train Models

```bash
# Train with synthetic data (1000 samples)
PYTHONPATH=. python3 train_dual_ai_models.py --model-dir ./models --data-source synthetic --samples 1000 --validate

# Train with historical data (if available)
PYTHONPATH=. python3 train_dual_ai_models.py --model-dir ./models --data-source historical --validate
```

## Use in Code

### Using DualAIMLEngine (Recommended)
```python
from dual_ai_ml_engine import DualAIMLEngine

# Initialize
engine = DualAIMLEngine(model_dir="./models")

# Score opportunities
opportunities = [
    {
        'hops': 2,
        'gross_profit': 50,
        'gas_cost': 15,
        'estimated_profit': 35,
        'confidence': 0.9,
        'initial_amount': 1000,
        'path': [{'tvl': 5_000_000}, {'tvl': 4_000_000}]
    }
]

best = engine.score_opportunities(opportunities)
print(f"Best opportunity score: {best['ml_score']}")
print(f"Primary model score: {best['primary_score']}")
print(f"ONNX model score: {best.get('onnx_score', 'N/A')}")
```

### Using DualModel (Legacy + ONNX Pairing)
```python
from models.dual_model import DualModel

# Initialize with custom weights
dual = DualModel(model_dir="./models", legacy_weight=0.5, onnx_weight=0.5)

# Get predictions
scores = dual.predict(opportunities)

# Get best opportunity
best = dual.score_opportunities(opportunities)
```

## Demo Scripts

```bash
# Run the Dual AI demo
PYTHONPATH=. python3 scripts/demo_dual_ai.py
```

## Files

- `dual_ai_ml_engine.py` - Main dual AI engine (XGBoost + ONNX)
- `models/dual_model.py` - DualModel wrapper (legacy + ONNX pairing)
- `models/onnx_wrapper.py` - ONNX inference helper
- `train_dual_ai_models.py` - Training script
- `scripts/demo_dual_ai.py` - Simple demo
- `scripts/verify_dependencies.py` - Dependency checker

## Troubleshooting

### Dependencies not installed
```bash
# Run verification
python3 scripts/verify_dependencies.py

# Install missing packages
pip3 install xgboost onnx onnxruntime skl2onnx
```

### Models not found
```bash
# Train models
PYTHONPATH=. python3 train_dual_ai_models.py --model-dir ./models --validate

# Check models directory
ls -lh models/
# Should see: xgboost_primary.pkl, onnx_model.onnx, scaler.pkl, training_metadata.json
```

### Import errors
```bash
# Ensure PYTHONPATH is set when running scripts
PYTHONPATH=. python3 your_script.py

# Or run from repository root
cd /path/to/repo
python3 -m your_module
```

## Performance

- **XGBoost Primary Model**: High accuracy (R² 0.79+), ~15-20ms inference
- **ONNX Model**: 6-7x faster (~2-3ms), optimized for production
- **Ensemble**: Best of both worlds - accuracy + speed

## Next Steps

1. ✅ Install dependencies: `pip3 install -r requirements.txt`
2. ✅ Verify: `python3 scripts/verify_dependencies.py`
3. ✅ Train: `PYTHONPATH=. python3 train_dual_ai_models.py --validate`
4. ✅ Test: `PYTHONPATH=. python3 scripts/demo_dual_ai.py`
5. ✅ Integrate: Use `DualAIMLEngine` or `DualModel` in your orchestrator

## Documentation

- Full guide: `models/DUAL_AI_README.md`
- Installation: `INSTALL.md`
- Main README: `README.md`
