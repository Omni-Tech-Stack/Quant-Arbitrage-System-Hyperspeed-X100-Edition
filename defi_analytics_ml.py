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
    
    def score_opportunities(self, opportunities):
        """
        Score opportunities using ML model
        
        Args:
            opportunities: List of opportunity dictionaries
            
        Returns:
            Best opportunity with ML scores
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
    
    print("\n✓ ML Analytics Engine - Ready")
