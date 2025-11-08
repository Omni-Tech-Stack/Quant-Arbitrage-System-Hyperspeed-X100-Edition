#!/usr/bin/env python
"""
Dual model integrator: pairs the existing `SimpleArbitrageModel` (legacy)
with an ONNX-optimized model for a Dual-AI scoring pipeline.

Behavior:
- Uses `ml_model.SimpleArbitrageModel` as the legacy/primary logic
- Uses `dual_ai_ml_engine.DualAIMLEngine` to extract features and load the ONNX session
- Ensembles legacy scores and ONNX predictions (configurable weights)

This file provides a small, easy-to-use API for existing orchestrators.
"""
from typing import List, Dict, Any, Optional
import numpy as np

from ml_model import SimpleArbitrageModel
from dual_ai_ml_engine import DualAIMLEngine


class DualModel:
    def __init__(self, model_dir: str = "./models", legacy_weight: float = 0.5, onnx_weight: float = 0.5):
        """
        Initialize the DualModel.

        Args:
            model_dir: folder where ONNX/scaler/models are stored (used by DualAIMLEngine)
            legacy_weight: weight for the legacy `SimpleArbitrageModel` in the ensemble (0-1)
            onnx_weight: weight for the ONNX model in the ensemble (0-1)
        """
        # Normalize weights
        total = max(1e-8, legacy_weight + onnx_weight)
        self.legacy_w = legacy_weight / total
        self.onnx_w = onnx_weight / total

        # Legacy model (simple, interpretable)
        self.legacy = SimpleArbitrageModel()

        # Engine used primarily for feature extraction and ONNX session
        self.engine = DualAIMLEngine(model_dir=model_dir)

    def predict(self, opportunities: List[Dict[str, Any]]) -> List[float]:
        """
        Return ensemble scores for a list of opportunities.

        The ensemble combines the legacy model's score and the ONNX model's
        prediction (if available). If ONNX isn't available, falls back to legacy.
        """
        if not opportunities:
            return []

        # Legacy predictions (uses internal scoring logic)
        legacy_scores = self.legacy.predict(opportunities)
        legacy_arr = np.array(legacy_scores, dtype=np.float32)

        # Extract features via engine (ensures feature ordering matches ONNX)
        X = self.engine.extract_features(opportunities)

        # Scale if scaler present
        if self.engine.scaler is not None and hasattr(self.engine.scaler, 'mean_'):
            try:
                X_scaled = self.engine.scaler.transform(X)
            except Exception:
                X_scaled = X
        else:
            X_scaled = X

        # ONNX predictions (may be None)
        onnx_preds = self.engine._predict_onnx(X_scaled)

        if onnx_preds is None:
            # No ONNX available -> return legacy scores
            return legacy_arr.tolist()

        # Ensemble: weighted sum of legacy and ONNX predictions
        ensemble = (self.legacy_w * legacy_arr) + (self.onnx_w * np.array(onnx_preds, dtype=np.float32))
        return np.clip(ensemble, 0.0, 1.0).tolist()

    def score_opportunities(self, opportunities: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Select and return the best opportunity with scoring metadata attached.
        """
        if not opportunities:
            return None

        scores = self.predict(opportunities)

        best_idx = int(np.argmax(scores))
        best = opportunities[best_idx].copy()
        best['ml_score'] = float(scores[best_idx])

        # Add component scores if available
        legacy_scores = self.legacy.predict(opportunities)
        best['legacy_score'] = float(legacy_scores[best_idx])

        # Try to annotate onnx score
        X = self.engine.extract_features(opportunities)
        if self.engine.scaler is not None and hasattr(self.engine.scaler, 'mean_'):
            try:
                X_scaled = self.engine.scaler.transform(X)
            except Exception:
                X_scaled = X
        else:
            X_scaled = X

        onnx_scores = self.engine._predict_onnx(X_scaled)
        if onnx_scores is not None:
            best['onnx_score'] = float(onnx_scores[best_idx])

        best['feature_vector'] = X[best_idx].tolist()
        return best
