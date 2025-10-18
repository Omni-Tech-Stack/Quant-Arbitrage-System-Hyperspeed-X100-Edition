#!/usr/bin/env python3
"""
ML Model Training Script
Pre-trains an arbitrage opportunity scoring model using synthetic historical data
"""

import pickle
import os
import numpy as np
from ml_model import SimpleArbitrageModel


def generate_synthetic_training_data(n_samples=1000):
    """
    Generate synthetic historical arbitrage data for model training
    """
    print(f"[Training] Generating {n_samples} synthetic training samples...")
    
    training_data = []
    
    for i in range(n_samples):
        # Generate realistic opportunity features
        hops = np.random.randint(2, 5)
        initial_amount = np.random.uniform(500, 10000)
        
        # Profit correlates with initial amount and inversely with hops
        base_profit = initial_amount * 0.02 * (4 / hops)
        profit = base_profit + np.random.normal(0, 10)
        
        gas_cost = hops * np.random.uniform(10, 20)
        net_profit = profit - gas_cost
        
        confidence = np.random.uniform(0.6, 0.95)
        
        opportunity = {
            'hops': hops,
            'initial_amount': initial_amount,
            'estimated_profit': max(0, net_profit),
            'gas_cost': gas_cost,
            'confidence': confidence,
            'gross_profit': max(0, profit)
        }
        
        training_data.append(opportunity)
    
    print(f"[Training] Generated {len(training_data)} training samples")
    return training_data


def train_and_save_model(output_path='./models/arb_ml_latest.pkl'):
    """
    Train the ML model and save it to disk
    """
    print("=" * 80)
    print("  ML MODEL TRAINING - ARBITRAGE OPPORTUNITY SCORER")
    print("=" * 80)
    print()
    
    # Create models directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate training data
    training_data = generate_synthetic_training_data(n_samples=1000)
    
    # Initialize and train model
    model = SimpleArbitrageModel()
    model.fit(training_data)
    
    # Validate model
    print("\n[Validation] Testing model predictions...")
    test_opportunities = generate_synthetic_training_data(n_samples=10)
    scores = model.predict(test_opportunities)
    
    print(f"[Validation] Sample predictions (first 5):")
    for i, (opp, score) in enumerate(zip(test_opportunities[:5], scores[:5])):
        print(f"  {i+1}. Profit: ${opp['estimated_profit']:.2f}, "
              f"Confidence: {opp['confidence']:.2f}, Score: {score:.3f}")
    
    # Save model
    print(f"\n[Saving] Writing model to {output_path}...")
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Verify saved model
    file_size = os.path.getsize(output_path)
    print(f"[Saving] ✓ Model saved successfully ({file_size} bytes)")
    
    # Test loading
    print("[Validation] Testing model reload...")
    with open(output_path, 'rb') as f:
        loaded_model = pickle.load(f)
    
    print(f"[Validation] ✓ Model loaded successfully")
    print(f"[Validation] ✓ Model version: {loaded_model.version}")
    print(f"[Validation] ✓ Trained at: {loaded_model.trained_at}")
    
    print("\n" + "=" * 80)
    print("  ✓ ML MODEL TRAINING COMPLETE")
    print("=" * 80)
    
    return output_path


if __name__ == "__main__":
    output_path = train_and_save_model()
    print(f"\n✓ Pre-trained model ready at: {output_path}")
    print("✓ System is ready for one-click deployment")
