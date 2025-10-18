# Models Directory

This directory contains ML models for the Quant Arbitrage System.

## Pre-Trained Model

### `arb_ml_latest.pkl` - Latest trained arbitrage ML model

**Status:** ✅ Pre-trained and ready for production

**Description:** 
- Weighted feature-based model for scoring arbitrage opportunities
- Trained on 1000+ synthetic historical arbitrage scenarios
- Scores opportunities based on: profit ratio, confidence, gas efficiency, liquidity, and hop count

**Version:** 1.0.0  
**Trained:** 2025-10-18  
**Size:** ~500 bytes  

**Usage:**
```python
from defi_analytics_ml import MLAnalyticsEngine

# Automatically loads the pre-trained model
ml_engine = MLAnalyticsEngine()

# Score opportunities
best = ml_engine.score_opportunities(opportunities)
print(f"Score: {best['ml_score']:.3f}")
```

## Retraining

To retrain the model with updated data:

```bash
python3 train_ml_model.py
```

This will:
1. Generate synthetic training data (1000 samples)
2. Train the model with weighted feature scoring
3. Validate predictions
4. Save the model to `./models/arb_ml_latest.pkl`
5. Verify the model can be loaded correctly

## Model Files

- `arb_ml_latest.pkl` - Pre-trained model (included)
- `../ml_model.py` - Model class definition
- `../train_ml_model.py` - Training script
- `../defi_analytics_ml.py` - ML analytics engine that loads and uses the model

Models are automatically included in the one-click deployment - no additional setup required!
