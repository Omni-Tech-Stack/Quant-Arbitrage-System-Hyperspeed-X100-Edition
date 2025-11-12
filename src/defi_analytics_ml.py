#!/usr/bin/env python
"""
DeFi Analytics & ML Engine
Adaptive, continuous ML retraining on live/historical data
Now powered by Dual AI: XGBoost + ONNX for superior performance
"""

import time
from typing import List, Dict, Any


class MLAnalyticsEngine:
    """Analytics and ML engine for adaptive opportunity scoring"""
    
    def __init__(self):
        self.trade_history = []
        self.model_version = "v1.0"
        self.total_trades = 0
        self.successful_trades = 0
    
    def score_opportunities(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score opportunities using ML model and return best one"""
        if not opportunities:
            return None
        
        # Score each opportunity
        scored = []
        for opp in opportunities:
            # Calculate comprehensive score
            score = self._calculate_ml_score(opp)
            opp['ml_score'] = score
            scored.append(opp)
        
        # Return highest scoring opportunity
        return max(scored, key=lambda o: o.get('ml_score', 0))
    
    def _calculate_ml_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate ML score for an opportunity"""
        # Factors: profit, confidence, slippage, gas
        profit = opportunity.get('estimated_profit', 0)
        confidence = opportunity.get('confidence', 0.5)
        slippage = opportunity.get('slippage', 0)
        gas = opportunity.get('estimated_gas', 0)
        
        # Normalize and weight factors
        profit_score = min(profit / 100, 1.0) if profit > 0 else 0
        confidence_score = confidence
        slippage_penalty = max(0, 1.0 - slippage / 10.0)
        gas_penalty = max(0, 1.0 - gas / 100.0)
        
        # Weighted combination
        score = (profit_score * 0.4 + 
                confidence_score * 0.3 + 
                slippage_penalty * 0.2 + 
                gas_penalty * 0.1)
        
        return max(0.0, min(1.0, score))
    
    def add_trade_result(self, opportunity: Dict[str, Any], tx_hash: str):
        """Add trade result for ML training"""
        self.total_trades += 1
        
        trade_record = {
            'timestamp': time.time(),
            'tx_hash': tx_hash,
            'opportunity': opportunity,
            'profit': opportunity.get('net_profit', 0),
            'success': True  # Assume success for now
        }
        
        self.trade_history.append(trade_record)
        
        if trade_record['success']:
            self.successful_trades += 1
        
        print(f"[ML] Trade result logged: {tx_hash[:16]}... (Total: {self.total_trades})")
    
    def retrain_model(self) -> Dict[str, Any]:
        """Retrain ML model on collected data"""
        if len(self.trade_history) < 10:
            print(f"[ML] Insufficient data for retraining ({len(self.trade_history)} trades)")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        print(f"[ML] Retraining model on {len(self.trade_history)} trades...")
        
        # Simulate retraining
        self.model_version = f"v1.{len(self.trade_history)}"
        
        return {
            "status": "success",
            "model_version": self.model_version,
            "training_samples": len(self.trade_history),
            "accuracy": self.successful_trades / self.total_trades if self.total_trades > 0 else 0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analytics statistics"""
        win_rate = self.successful_trades / self.total_trades if self.total_trades > 0 else 0
        
        total_profit = sum(t['profit'] for t in self.trade_history)
        avg_profit = total_profit / len(self.trade_history) if self.trade_history else 0
        
        return {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit': avg_profit,
            'model_version': self.model_version
        }
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
            Best opportunity with ML scores (highest scoring opportunity)
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
