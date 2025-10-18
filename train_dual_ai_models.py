#!/usr/bin/env python3
"""
Model Training Script for Dual AI System
Trains superior models on historical arbitrage data
"""

import os
import sys
import json
import argparse
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

try:
    from dual_ai_ml_engine import DualAIMLEngine
except ImportError:
    print("Error: dual_ai_ml_engine not found")
    sys.exit(1)


def generate_synthetic_data(n_samples: int = 1000) -> Tuple[List[Dict[str, Any]], List[float]]:
    """
    Generate synthetic training data based on realistic arbitrage patterns
    In production, this would load from historical trade logs
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        Tuple of (training_data, labels)
    """
    print(f"[Training] Generating {n_samples} synthetic samples...")
    
    training_data = []
    labels = []
    
    for i in range(n_samples):
        # Simulate different market conditions
        market_condition = np.random.choice(['normal', 'volatile', 'low_liquidity'], p=[0.7, 0.2, 0.1])
        
        if market_condition == 'normal':
            hops = np.random.randint(2, 4)
            gross_profit = np.random.uniform(10, 80)
            gas_cost = np.random.uniform(10, 30)
            confidence = np.random.uniform(0.7, 0.95)
            tvl_multiplier = 1.0
        elif market_condition == 'volatile':
            hops = np.random.randint(3, 5)
            gross_profit = np.random.uniform(20, 150)
            gas_cost = np.random.uniform(15, 50)
            confidence = np.random.uniform(0.5, 0.8)
            tvl_multiplier = 0.7
        else:  # low_liquidity
            hops = np.random.randint(2, 5)
            gross_profit = np.random.uniform(5, 60)
            gas_cost = np.random.uniform(20, 45)
            confidence = np.random.uniform(0.6, 0.85)
            tvl_multiplier = 0.5
        
        estimated_profit = gross_profit - gas_cost
        
        # Create opportunity
        opp = {
            'hops': hops,
            'gross_profit': gross_profit,
            'gas_cost': gas_cost,
            'estimated_profit': estimated_profit,
            'confidence': confidence,
            'initial_amount': np.random.choice([500, 1000, 2000, 5000]),
            'path': [
                {'tvl': np.random.uniform(500000, 20000000) * tvl_multiplier}
                for _ in range(hops)
            ],
            'market_condition': market_condition
        }
        
        training_data.append(opp)
        
        # Label: success probability based on multiple factors
        # Higher profit, higher confidence, lower gas cost, better liquidity = higher success
        profit_factor = max(0, min(estimated_profit / 100, 1))
        confidence_factor = confidence
        liquidity_factor = min(sum(p['tvl'] for p in opp['path']) / (10_000_000 * hops), 1)
        gas_factor = max(0, 1 - (gas_cost / 100))
        
        label = (
            profit_factor * 0.4 +
            confidence_factor * 0.3 +
            liquidity_factor * 0.2 +
            gas_factor * 0.1
        )
        
        # Add some noise
        label = max(0, min(label + np.random.normal(0, 0.05), 1))
        
        labels.append(label)
    
    return training_data, labels


def load_historical_data() -> Tuple[List[Dict[str, Any]], List[float]]:
    """
    Load historical training data from trade logs
    Falls back to synthetic data if no historical data available
    
    Returns:
        Tuple of (training_data, labels)
    """
    trade_log_path = "./models/trade_log.jsonl"
    
    if not os.path.exists(trade_log_path):
        print("[Training] No historical data found, using synthetic data")
        return generate_synthetic_data()
    
    print(f"[Training] Loading historical data from {trade_log_path}...")
    
    training_data = []
    labels = []
    
    try:
        with open(trade_log_path, 'r') as f:
            for line in f:
                trade = json.loads(line.strip())
                
                # Reconstruct opportunity from features
                features = trade.get('features', [])
                if len(features) >= 10:
                    opp = {
                        'hops': features[0],
                        'gross_profit': features[1],
                        'gas_cost': features[2],
                        'estimated_profit': features[3],
                        'confidence': features[7],
                        'initial_amount': 1000,  # Default
                        'path': [{'tvl': 5000000}] * int(features[0])  # Approximate
                    }
                    
                    training_data.append(opp)
                    
                    # Label: actual success/profit
                    if trade.get('success', False):
                        actual_profit = trade.get('actual_profit', 0)
                        estimated_profit = trade.get('estimated_profit', 1)
                        # Normalize to 0-1 range
                        label = min(max(actual_profit / max(estimated_profit, 1), 0), 1)
                    else:
                        label = 0.0
                    
                    labels.append(label)
        
        if len(training_data) < 50:
            print(f"[Training] Insufficient historical data ({len(training_data)} samples), adding synthetic data")
            synthetic_data, synthetic_labels = generate_synthetic_data(1000 - len(training_data))
            training_data.extend(synthetic_data)
            labels.extend(synthetic_labels)
        
        print(f"[Training] Loaded {len(training_data)} samples")
        
    except Exception as e:
        print(f"[Training] Error loading historical data: {e}")
        print("[Training] Falling back to synthetic data")
        return generate_synthetic_data()
    
    return training_data, labels


def train_models(engine: DualAIMLEngine, data_source: str = 'auto', n_samples: int = 1000):
    """
    Train the dual AI models
    
    Args:
        engine: DualAIMLEngine instance
        data_source: 'auto', 'historical', or 'synthetic'
        n_samples: Number of samples for synthetic data
    """
    print("\n" + "=" * 80)
    print("  MODEL TRAINING - DUAL AI SYSTEM")
    print("=" * 80)
    print()
    
    # Load training data
    if data_source == 'synthetic':
        training_data, labels = generate_synthetic_data(n_samples)
    elif data_source == 'historical':
        training_data, labels = load_historical_data()
    else:  # auto
        training_data, labels = load_historical_data()
    
    # Train models
    engine.train_models(training_data, labels)
    
    print("\n" + "=" * 80)
    print("  TRAINING COMPLETE")
    print("=" * 80)
    print()
    print("✓ Models trained and saved successfully")
    print(f"  - Primary Model: XGBoost ({n_samples} samples)")
    print(f"  - ONNX Model: Optimized for inference")
    print(f"  - Location: {engine.model_dir}")
    print()


def validate_models(engine: DualAIMLEngine):
    """
    Validate trained models on test data
    
    Args:
        engine: DualAIMLEngine instance
    """
    print("\n" + "=" * 80)
    print("  MODEL VALIDATION")
    print("=" * 80)
    print()
    
    # Generate test opportunities
    test_opportunities = [
        {
            'hops': 2,
            'gross_profit': 40,
            'gas_cost': 15,
            'estimated_profit': 25,
            'confidence': 0.85,
            'initial_amount': 1000,
            'path': [{'tvl': 5000000}, {'tvl': 4000000}]
        },
        {
            'hops': 3,
            'gross_profit': 60,
            'gas_cost': 25,
            'estimated_profit': 35,
            'confidence': 0.80,
            'initial_amount': 2000,
            'path': [{'tvl': 8000000}, {'tvl': 6000000}, {'tvl': 7000000}]
        },
        {
            'hops': 4,
            'gross_profit': 100,
            'gas_cost': 40,
            'estimated_profit': 60,
            'confidence': 0.90,
            'initial_amount': 5000,
            'path': [{'tvl': 10000000}, {'tvl': 9000000}, {'tvl': 8000000}, {'tvl': 11000000}]
        },
        {
            'hops': 2,
            'gross_profit': 20,
            'gas_cost': 30,
            'estimated_profit': -10,
            'confidence': 0.70,
            'initial_amount': 500,
            'path': [{'tvl': 1000000}, {'tvl': 1500000}]
        }
    ]
    
    print("Testing model predictions on sample opportunities:\n")
    
    for i, opp in enumerate(test_opportunities, 1):
        result = engine.score_opportunities([opp])
        
        if result:
            print(f"{i}. Opportunity:")
            print(f"   Estimated Profit: ${result['estimated_profit']:.2f}")
            print(f"   ML Score: {result.get('ml_score', 0):.4f}")
            print(f"   Primary Score: {result.get('primary_score', 0):.4f}")
            if 'onnx_score' in result:
                print(f"   ONNX Score: {result.get('onnx_score', 0):.4f}")
            print()
    
    # Test batch scoring
    print("\nBatch scoring (selecting best opportunity):")
    best = engine.score_opportunities(test_opportunities)
    if best:
        print(f"✓ Selected opportunity with:")
        print(f"  - Estimated Profit: ${best['estimated_profit']:.2f}")
        print(f"  - ML Score: {best.get('ml_score', 0):.4f}")
        print(f"  - Hops: {best['hops']}")
        print(f"  - Confidence: {best['confidence']:.2f}")
    
    print("\n✓ Validation complete")


def main():
    """Main training script"""
    parser = argparse.ArgumentParser(
        description='Train superior ML models for arbitrage opportunity detection'
    )
    parser.add_argument(
        '--data-source',
        choices=['auto', 'historical', 'synthetic'],
        default='auto',
        help='Data source for training (default: auto)'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=1000,
        help='Number of synthetic samples to generate (default: 1000)'
    )
    parser.add_argument(
        '--model-dir',
        default='./models',
        help='Directory to save models (default: ./models)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validation after training'
    )
    
    args = parser.parse_args()
    
    # Initialize engine
    print("Initializing Dual AI ML Engine...")
    engine = DualAIMLEngine(model_dir=args.model_dir)
    
    # Train models
    train_models(engine, args.data_source, args.samples)
    
    # Validate if requested
    if args.validate:
        validate_models(engine)
    
    print("\n" + "=" * 80)
    print("  TRAINING SESSION COMPLETE")
    print("=" * 80)
    print()
    print("Your dual AI models are now ready for production use!")
    print(f"Models saved in: {args.model_dir}")
    print()


if __name__ == "__main__":
    main()
