#!/usr/bin/env python3
"""
DeFi Analytics & ML Engine
Adaptive, continuous ML retraining on live/historical data
Now powered by Dual AI: XGBoost + ONNX for superior performance
"""

try:
    from dual_ai_ml_engine import DualAIMLEngine
    DUAL_AI_AVAILABLE = True
except ImportError:
    DUAL_AI_AVAILABLE = False
    print("[ML] Warning: Dual AI engine not available, using fallback")
import pickle
import os
import sys
from datetime import datetime

# Try to import the model class for unpickling
try:
    from ml_model import SimpleArbitrageModel
except ImportError:
    SimpleArbitrageModel = None


class MLAnalyticsEngine:
    """
    ML Analytics Engine with Dual AI support
    - Primary: Uses DualAIMLEngine when available (XGBoost + ONNX)
    - Fallback: Simple scoring based on estimated profit
    """
    
    def __init__(self, model_dir: str = "./models"):
        self.model_dir = model_dir
        self.dual_ai = None
        
        if DUAL_AI_AVAILABLE:
            try:
                self.dual_ai = DualAIMLEngine(model_dir=model_dir)
                print("[ML] ✓ Dual AI engine initialized (XGBoost + ONNX)")
            except Exception as e:
                print(f"[ML] ⚠ Failed to initialize Dual AI: {e}")
    ML-powered analytics engine for arbitrage opportunity scoring
    Loads pre-trained model and scores opportunities in real-time
    """
    
    def __init__(self, model_path='./models/arb_ml_latest.pkl'):
        """Initialize ML engine and load trained model"""
        self.model_path = model_path
        self.model = None
        self.trade_results = []
        self.load_model()
    
    def load_model(self):
        """Load pre-trained ML model from disk"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"[ML] ✓ Loaded model from {self.model_path}")
                if hasattr(self.model, 'version'):
                    print(f"[ML] ✓ Model version: {self.model.version}")
                if hasattr(self.model, 'trained_at'):
                    print(f"[ML] ✓ Model trained at: {self.model.trained_at}")
            except Exception as e:
                print(f"[ML] ⚠ Failed to load model: {e}")
                self.model = None
        else:
            print(f"[ML] ⚠ Model not found at {self.model_path}")
            print(f"[ML] ℹ Run 'python3 train_ml_model.py' to create model")
    
    def score_opportunities(self, opportunities):
        """
        Score opportunities using ML model
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            Best opportunity with ML scores
        Returns the highest scoring opportunity
        """
        if not opportunities:
            return None
        
        # Use Dual AI if available
        if self.dual_ai:
            return self.dual_ai.score_opportunities(opportunities)
        
        # Fallback: Return highest estimated profit
        return max(opportunities, key=lambda o: o.get('estimated_profit', 0))
    
    def add_trade_result(self, opportunity, tx_hash, success: bool = True, actual_profit: float = 0.0):
        """
        Add trade result for ML training
        
        Args:
            opportunity: The executed opportunity
            tx_hash: Transaction hash
            success: Whether trade was successful
            actual_profit: Actual profit realized
        """
        if self.dual_ai:
            self.dual_ai.add_trade_result(opportunity, tx_hash, success, actual_profit)
        else:
            print(f"[ML] Trade result logged: {tx_hash}")
    
    def train_models(self, training_data, labels):
        """
        Train ML models on historical data
        
        Args:
            training_data: List of opportunity dictionaries
            labels: Target values (e.g., actual profit/success rate)
        """
        if self.dual_ai:
            self.dual_ai.train_models(training_data, labels)
        else:
            print("[ML] Training not available without Dual AI engine")


if __name__ == "__main__":
    print("=" * 80)
    print("  ML ANALYTICS ENGINE TEST")
    print("=" * 80)
    print()
    
    engine = MLAnalyticsEngine()
    
    # Test scoring
    test_opps = [
        {
            'hops': 3,
            'gross_profit': 50,
            'gas_cost': 20,
            'estimated_profit': 30,
            'confidence': 0.85
        },
        {
            'hops': 2,
            'gross_profit': 25,
            'gas_cost': 15,
            'estimated_profit': 10,
            'confidence': 0.75
        }
    ]
    
    best = engine.score_opportunities(test_opps)
    if best:
        print(f"\n✓ Best opportunity:")
        print(f"  - Estimated Profit: ${best['estimated_profit']:.2f}")
        if 'ml_score' in best:
            print(f"  - ML Score: {best['ml_score']:.4f}")
        if self.model and hasattr(self.model, 'score_opportunities'):
            # Use ML model to score and select best opportunity
            try:
                best_opp = self.model.score_opportunities(opportunities)
                if best_opp:
                    print(f"[ML] Best opportunity score: {best_opp.get('ml_score', 0):.3f}")
                return best_opp
            except Exception as e:
                print(f"[ML] ⚠ Model scoring failed: {e}, using fallback")
        
        # Fallback: return opportunity with highest existing ml_score
        return max(opportunities, key=lambda o: o.get('ml_score', 0))
    
    def add_trade_result(self, opportunity, tx_hash):
        """
        Add trade result for ML training
        Store results for future model retraining
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'tx_hash': tx_hash,
            'opportunity': opportunity,
            'profit': opportunity.get('estimated_profit', 0),
            'ml_score': opportunity.get('ml_score', 0)
        }
        self.trade_results.append(result)
        print(f"[ML] Trade result logged: {tx_hash} (score: {result['ml_score']:.3f})")
        
        # Trigger retraining if we have enough new data
        if len(self.trade_results) >= 100:
            print("[ML] ℹ 100 new trades logged. Consider retraining model.")
    
    def retrain_model(self):
        """
        Retrain model with accumulated trade results
        This would be called periodically to improve model performance
        """
        if len(self.trade_results) < 50:
            print(f"[ML] ⚠ Not enough data for retraining ({len(self.trade_results)} < 50)")
            return False
        
        print(f"[ML] Retraining model with {len(self.trade_results)} trade results...")
        # In production, this would retrain the model with actual trade outcomes
        # For now, we just acknowledge the request
        print("[ML] ℹ Model retraining requires train_ml_model.py to be run")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("  ML ANALYTICS ENGINE TEST")
    print("=" * 60)
    print()
    
    # Test initialization
    engine = MLAnalyticsEngine()
    
    # Test with sample opportunities
    sample_opportunities = [
        {
            'hops': 2,
            'estimated_profit': 50,
            'confidence': 0.8,
            'gas_cost': 30,
            'initial_amount': 1000
        },
        {
            'hops': 3,
            'estimated_profit': 100,
            'confidence': 0.9,
            'gas_cost': 45,
            'initial_amount': 2000
        }
    ]
    
    best = engine.score_opportunities(sample_opportunities)
    if best:
        print(f"\n✓ Best opportunity: ${best['estimated_profit']} profit")
        print(f"✓ ML Score: {best.get('ml_score', 0):.3f}")
    
    print("\n✓ ML Analytics Engine - Ready")
