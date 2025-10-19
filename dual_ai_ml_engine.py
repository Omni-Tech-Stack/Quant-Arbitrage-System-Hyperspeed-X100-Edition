#!/usr/bin/env python
"""
Dual AI ML Engine - Superior Models with ONNX Integration
Combines traditional ML (XGBoost/Random Forest) with ONNX-optimized inference
for high-performance, production-ready arbitrage opportunity scoring
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import xgboost as xgb
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[DualAI] Warning: scikit-learn/xgboost not available")

try:
    import onnx
    import onnxruntime as ort
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("[DualAI] Warning: ONNX not available")


class DualAIMLEngine:
    """
    Dual AI Engine combining:
    1. Primary Model: XGBoost for high accuracy and complex patterns
    2. ONNX Model: Optimized inference for ultra-low latency
    
    Features:
    - Ensemble prediction combining both models
    - Feature engineering for arbitrage opportunities
    - Model versioning and persistence
    - Real-time scoring with sub-millisecond latency
    """
    
    def __init__(self, model_dir: str = "./models"):
        self.model_dir = model_dir
        self.primary_model = None
        self.onnx_session = None
        self.scaler = None
        self.feature_names = [
            'hops',
            'gross_profit',
            'gas_cost',
            'estimated_profit',
            'liquidity_score',
            'price_impact',
            'slippage_estimate',
            'confidence',
            'time_of_day',
            'volatility_indicator'
        ]
        
        os.makedirs(model_dir, exist_ok=True)
        self._load_or_initialize_models()
    
    def _load_or_initialize_models(self):
        """Load existing models or initialize new ones"""
        primary_path = os.path.join(self.model_dir, "xgboost_primary.pkl")
        onnx_path = os.path.join(self.model_dir, "onnx_model.onnx")
        scaler_path = os.path.join(self.model_dir, "scaler.pkl")
        
        # Load or create scaler
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
            print(f"[DualAI] ✓ Loaded scaler from {scaler_path}")
        elif SKLEARN_AVAILABLE:
            self.scaler = StandardScaler()
            print("[DualAI] ✓ Initialized new scaler")
        
        # Load or create primary model
        if os.path.exists(primary_path):
            self.primary_model = joblib.load(primary_path)
            print(f"[DualAI] ✓ Loaded primary XGBoost model from {primary_path}")
        elif SKLEARN_AVAILABLE:
            self.primary_model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                objective='reg:squarederror'
            )
            print("[DualAI] ✓ Initialized new XGBoost model")
        
        # Load ONNX model
        if os.path.exists(onnx_path) and ONNX_AVAILABLE:
            self.onnx_session = ort.InferenceSession(
                onnx_path,
                providers=['CPUExecutionProvider']
            )
            print(f"[DualAI] ✓ Loaded ONNX model from {onnx_path}")
        else:
            print("[DualAI] ⚠ ONNX model not found - will create on training")
    
    def extract_features(self, opportunities: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract and engineer features from opportunities
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            Feature matrix (n_samples, n_features)
        """
        features = []
        
        for opp in opportunities:
            # Basic features
            hops = opp.get('hops', 3)
            gross_profit = opp.get('gross_profit', 0)
            gas_cost = opp.get('gas_cost', 0)
            estimated_profit = opp.get('estimated_profit', 0)
            confidence = opp.get('confidence', 0.5)
            
            # Engineered features
            liquidity_score = self._calculate_liquidity_score(opp)
            price_impact = self._estimate_price_impact(opp)
            slippage_estimate = self._estimate_slippage(opp)
            time_of_day = (datetime.now().hour / 24.0)  # Normalized hour
            volatility_indicator = self._calculate_volatility_indicator(opp)
            
            feature_vector = [
                hops,
                gross_profit,
                gas_cost,
                estimated_profit,
                liquidity_score,
                price_impact,
                slippage_estimate,
                confidence,
                time_of_day,
                volatility_indicator
            ]
            
            features.append(feature_vector)
        
        return np.array(features, dtype=np.float32)
    
    def _calculate_liquidity_score(self, opp: Dict[str, Any]) -> float:
        """Calculate liquidity score based on path pools"""
        path = opp.get('path', [])
        if not path:
            return 0.5
        
        # Mock liquidity calculation - in production, use real TVL data
        avg_tvl = sum(pool.get('tvl', 1000000) for pool in path) / len(path)
        # Normalize to 0-1 range (assuming max TVL of 100M)
        return min(avg_tvl / 100_000_000, 1.0)
    
    def _estimate_price_impact(self, opp: Dict[str, Any]) -> float:
        """Estimate price impact of the trade"""
        initial_amount = opp.get('initial_amount', 1000)
        path = opp.get('path', [])
        
        if not path:
            return 0.01
        
        # Simple price impact model: impact increases with trade size and hops
        impact = (initial_amount / 10000) * (len(path) * 0.001)
        return min(impact, 0.1)  # Cap at 10%
    
    def _estimate_slippage(self, opp: Dict[str, Any]) -> float:
        """Estimate slippage for the opportunity"""
        hops = opp.get('hops', 3)
        # Slippage increases with number of hops
        base_slippage = 0.001  # 0.1% base
        return base_slippage * (1 + hops * 0.5)
    
    def _calculate_volatility_indicator(self, opp: Dict[str, Any]) -> float:
        """Calculate volatility indicator using historical price data (standard deviation of log returns)"""
        prices = opp.get('historical_prices', None)
        if prices is not None and isinstance(prices, (list, np.ndarray)) and len(prices) > 1:
            prices = np.array(prices)
            log_returns = np.diff(np.log(prices))
            volatility = np.std(log_returns)
            # Normalize volatility to 0-1 range (assuming max reasonable volatility of 0.1)
            return min(volatility / 0.1, 1.0)
        else:
            # If no price history, return 0.0 (no volatility info)
            return 0.0
    
    def score_opportunities(self, opportunities: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Score opportunities using dual AI system
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            Best opportunity with ML scores, or None if no valid opportunities
        """
        if not opportunities:
            return None
        
        # Extract features
        X = self.extract_features(opportunities)
        
        # Scale features
        if self.scaler is not None and hasattr(self.scaler, 'mean_'):
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # Get predictions from both models
        primary_scores = self._predict_primary(X_scaled)
        onnx_scores = self._predict_onnx(X_scaled)
        
        # Ensemble: weighted average of both models
        # Primary model: 60%, ONNX model: 40%
        if onnx_scores is not None:
            ensemble_scores = 0.6 * primary_scores + 0.4 * onnx_scores
            print(f"[DualAI] Using ensemble prediction (Primary + ONNX)")
        else:
            ensemble_scores = primary_scores
            print(f"[DualAI] Using primary model only")
        
        # Find best opportunity
        best_idx = np.argmax(ensemble_scores)
        best_opp = opportunities[best_idx].copy()
        
        # Add scoring information
        best_opp['ml_score'] = float(ensemble_scores[best_idx])
        best_opp['primary_score'] = float(primary_scores[best_idx])
        if onnx_scores is not None:
            best_opp['onnx_score'] = float(onnx_scores[best_idx])
        best_opp['feature_vector'] = X[best_idx].tolist()
        
        return best_opp
    
    def _predict_primary(self, X: np.ndarray) -> np.ndarray:
        """Predict using primary XGBoost model"""
        if self.primary_model is None or not hasattr(self.primary_model, 'predict'):
            # Return confidence scores as fallback
            return np.array([0.5] * len(X))
        
        try:
            predictions = self.primary_model.predict(X)
            # Normalize to 0-1 range
            return np.clip(predictions, 0, 1)
        except Exception as e:
            print(f"[DualAI] Primary model prediction error: {e}")
            return np.array([0.5] * len(X))
    
    def _predict_onnx(self, X: np.ndarray) -> Optional[np.ndarray]:
        """Predict using ONNX model for optimized inference"""
        if self.onnx_session is None:
            return None
        
        try:
            # Get input name
            input_name = self.onnx_session.get_inputs()[0].name
            
            # Run inference
            result = self.onnx_session.run(None, {input_name: X.astype(np.float32)})
            predictions = result[0].flatten()
            
            # Normalize to 0-1 range
            return np.clip(predictions, 0, 1)
        except Exception as e:
            print(f"[DualAI] ONNX model prediction error: {e}")
            return None
    
    def train_models(self, training_data: List[Dict[str, Any]], labels: List[float]):
        """
        Train both primary and ONNX models
        
        Args:
            training_data: List of opportunity dictionaries with features
            labels: Target values (e.g., actual profit/success rate)
        """
        if not SKLEARN_AVAILABLE:
            print("[DualAI] Cannot train - scikit-learn not available")
            return
        
        print(f"[DualAI] Training models on {len(training_data)} samples...")
        
        # Extract features
        X = self.extract_features(training_data)
        y = np.array(labels)
        
        # Fit scaler
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train primary XGBoost model
        print("[DualAI] Training XGBoost model...")
        self.primary_model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.primary_model.score(X_train, y_train)
        test_score = self.primary_model.score(X_test, y_test)
        print(f"[DualAI] XGBoost - Train R²: {train_score:.4f}, Test R²: {test_score:.4f}")
        
        # Save primary model
        primary_path = os.path.join(self.model_dir, "xgboost_primary.pkl")
        joblib.dump(self.primary_model, primary_path)
        print(f"[DualAI] ✓ Saved primary model to {primary_path}")
        
        # Save scaler
        scaler_path = os.path.join(self.model_dir, "scaler.pkl")
        joblib.dump(self.scaler, scaler_path)
        print(f"[DualAI] ✓ Saved scaler to {scaler_path}")
        
        # Convert to ONNX
        if ONNX_AVAILABLE:
            self._convert_to_onnx(X_train)
        
        # Save metadata
        self._save_training_metadata(train_score, test_score, len(training_data))
    
    def _convert_to_onnx(self, X_sample: np.ndarray):
        """Convert primary model to ONNX format"""
        print("[DualAI] Converting model to ONNX...")
        
        try:
            # Create a simpler Random Forest model for ONNX conversion
            # (XGBoost to ONNX can be complex, so we use RF as secondary model)
            rf_model = RandomForestRegressor(
                n_estimators=50,
                max_depth=6,
                random_state=42
            )
            
            # Train RF on the same data that primary model saw
            # For simplicity, we'll create synthetic data matching our features
            n_samples = min(len(X_sample), 100)
            X_train = X_sample[:n_samples]
            y_train = self.primary_model.predict(X_train)  # Use primary model predictions as labels
            
            rf_model.fit(X_train, y_train)
            
            # Convert to ONNX
            initial_type = [('float_input', FloatTensorType([None, len(self.feature_names)]))]
            onnx_model = convert_sklearn(
                rf_model,
                initial_types=initial_type,
                target_opset=12
            )
            
            # Save ONNX model
            onnx_path = os.path.join(self.model_dir, "onnx_model.onnx")
            with open(onnx_path, "wb") as f:
                f.write(onnx_model.SerializeToString())
            
            print(f"[DualAI] ✓ Saved ONNX model to {onnx_path}")
            
            # Load ONNX model for inference
            self.onnx_session = ort.InferenceSession(
                onnx_path,
                providers=['CPUExecutionProvider']
            )
            print("[DualAI] ✓ ONNX model ready for inference")
            
        except Exception as e:
            print(f"[DualAI] ⚠ ONNX conversion failed: {e}")
    
    def _save_training_metadata(self, train_score: float, test_score: float, n_samples: int):
        """Save training metadata for tracking"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'train_r2_score': train_score,
            'test_r2_score': test_score,
            'n_samples': n_samples,
            'feature_names': self.feature_names,
            'model_type': 'XGBoost + ONNX Dual AI'
        }
        
        metadata_path = os.path.join(self.model_dir, "training_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"[DualAI] ✓ Saved training metadata to {metadata_path}")
    
    def add_trade_result(self, opportunity: Dict[str, Any], tx_hash: str, success: bool = True, actual_profit: float = 0.0):
        """
        Log trade result for future model retraining
        
        Args:
            opportunity: The executed opportunity
            tx_hash: Transaction hash
            success: Whether trade was successful
            actual_profit: Actual profit realized
        """
        trade_log = {
            'timestamp': datetime.now().isoformat(),
            'tx_hash': tx_hash,
            'success': success,
            'estimated_profit': opportunity.get('estimated_profit', 0),
            'actual_profit': actual_profit,
            'ml_score': opportunity.get('ml_score', 0),
            'primary_score': opportunity.get('primary_score', 0),
            'onnx_score': opportunity.get('onnx_score', 0),
            'features': opportunity.get('feature_vector', [])
        }
        
        # Append to trade log file
        log_path = os.path.join(self.model_dir, "trade_log.jsonl")
        with open(log_path, 'a') as f:
            f.write(json.dumps(trade_log) + '\n')
        
        print(f"[DualAI] ✓ Trade result logged: {tx_hash}")


def main():
    """Test and demonstrate dual AI engine"""
    print("=" * 80)
    print("  DUAL AI ML ENGINE - SUPERIOR MODELS TEST")
    print("=" * 80)
    print()
    
    # Initialize engine
    engine = DualAIMLEngine()
    
    # Generate synthetic training data
    print("[DualAI] Generating synthetic training data...")
    training_data = []
    labels = []
    
    for i in range(200):
        opp = {
            'hops': np.random.randint(2, 5),
            'gross_profit': np.random.uniform(5, 100),
            'gas_cost': np.random.uniform(10, 40),
            'estimated_profit': np.random.uniform(-10, 60),
            'confidence': np.random.uniform(0.6, 0.95),
            'initial_amount': 1000,
            'path': [{'tvl': np.random.uniform(100000, 10000000)} for _ in range(3)]
        }
        training_data.append(opp)
        
        # Label: higher profit and confidence = higher score
        label = (opp['estimated_profit'] / 100) * opp['confidence']
        labels.append(max(0, min(label, 1)))
    
    # Train models
    engine.train_models(training_data, labels)
    
    print("\n" + "=" * 80)
    print("  TESTING INFERENCE")
    print("=" * 80)
    print()
    
    # Test scoring
    test_opportunities = [
        {
            'hops': 3,
            'gross_profit': 50,
            'gas_cost': 20,
            'estimated_profit': 30,
            'confidence': 0.85,
            'initial_amount': 1000,
            'path': [{'tvl': 5000000}, {'tvl': 3000000}, {'tvl': 4000000}]
        },
        {
            'hops': 2,
            'gross_profit': 25,
            'gas_cost': 15,
            'estimated_profit': 10,
            'confidence': 0.75,
            'initial_amount': 1000,
            'path': [{'tvl': 2000000}, {'tvl': 1500000}]
        },
        {
            'hops': 4,
            'gross_profit': 80,
            'gas_cost': 35,
            'estimated_profit': 45,
            'confidence': 0.90,
            'initial_amount': 1000,
            'path': [{'tvl': 8000000}, {'tvl': 6000000}, {'tvl': 7000000}, {'tvl': 5000000}]
        }
    ]
    
    best_opp = engine.score_opportunities(test_opportunities)
    
    if best_opp:
        print(f"\n✓ Best opportunity selected:")
        print(f"  - Estimated Profit: ${best_opp['estimated_profit']:.2f}")
        print(f"  - ML Score: {best_opp['ml_score']:.4f}")
        print(f"  - Primary Score: {best_opp['primary_score']:.4f}")
        if 'onnx_score' in best_opp:
            print(f"  - ONNX Score: {best_opp['onnx_score']:.4f}")
        print(f"  - Hops: {best_opp['hops']}")
        print(f"  - Confidence: {best_opp['confidence']:.2f}")
    
    print("\n✓ Dual AI ML Engine test completed successfully")


if __name__ == "__main__":
    main()
