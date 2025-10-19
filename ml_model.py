#!/usr/bin/env python
"""
ML Model Definition
Arbitrage opportunity scoring model
"""

import numpy as np
from datetime import datetime


class SimpleArbitrageModel:
    """
    Simple arbitrage opportunity scoring model
    Uses weighted features to score opportunities
    """
    
    def __init__(self):
        self.version = "1.0.0"
        self.trained_at = None
        # Feature weights learned from historical data
        self.weights = {
            'profit_ratio': 0.35,
            'confidence': 0.25,
            'gas_efficiency': 0.20,
            'liquidity_score': 0.15,
            'hop_penalty': 0.05
        }
        self.min_score = 0.0
        self.max_score = 1.0
    
    def fit(self, X, y=None):
        """
        Train the model on historical data
        X: List of opportunity features
        y: Optional labels (not used in this simple model)
        """
        print("[Training] Fitting model on historical data...")
        
        # Simulate training by analyzing feature distributions
        if X and len(X) > 0:
            # Calculate statistics for normalization
            profits = [opp.get('estimated_profit', 0) for opp in X]
            confidences = [opp.get('confidence', 0.5) for opp in X]
            
            if profits:
                self.profit_mean = np.mean(profits)
                self.profit_std = np.std(profits) if len(profits) > 1 else 1.0
            
            if confidences:
                self.confidence_mean = np.mean(confidences)
        
        self.trained_at = datetime.now().isoformat()
        print(f"[Training] Model trained successfully at {self.trained_at}")
        return self
    
    def predict(self, opportunities):
        """
        Score arbitrage opportunities
        Returns scores between 0 and 1
        """
        if not opportunities:
            return []
        
        scores = []
        for opp in opportunities:
            score = self._score_opportunity(opp)
            scores.append(score)
        
        return scores
    
    def _score_opportunity(self, opp):
        """Calculate weighted score for a single opportunity"""
        # Extract features
        profit = opp.get('estimated_profit', 0)
        confidence = opp.get('confidence', 0.5)
        gas_cost = opp.get('gas_cost', 50)
        hops = opp.get('hops', 2)
        
        # Normalize and calculate component scores
        profit_score = min(1.0, profit / 100.0)  # Normalize to $100 profit
        confidence_score = confidence
        gas_efficiency = max(0, 1.0 - (gas_cost / 100.0))  # Lower gas is better
        liquidity_score = min(1.0, opp.get('initial_amount', 1000) / 10000.0)
        hop_penalty = max(0, 1.0 - (hops / 5.0))  # Fewer hops is better
        
        # Weighted combination
        final_score = (
            self.weights['profit_ratio'] * profit_score +
            self.weights['confidence'] * confidence_score +
            self.weights['gas_efficiency'] * gas_efficiency +
            self.weights['liquidity_score'] * liquidity_score +
            self.weights['hop_penalty'] * hop_penalty
        )
        
        return max(self.min_score, min(self.max_score, final_score))
    
    def score_opportunities(self, opportunities):
        """Score and return best opportunity"""
        if not opportunities:
            return None
        
        scores = self.predict(opportunities)
        
        # Add scores to opportunities
        scored_opps = []
        for opp, score in zip(opportunities, scores):
            opp_copy = opp.copy()
            opp_copy['ml_score'] = score
            scored_opps.append(opp_copy)
        
        # Return highest scoring opportunity
        return max(scored_opps, key=lambda x: x['ml_score'])
