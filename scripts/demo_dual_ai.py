#!/usr/bin/env python
"""
Demo script to exercise the DualModel (legacy SimpleArbitrageModel + ONNX)

This script creates a small set of synthetic opportunities and prints the
legacy score, ONNX score (if available), and the ensemble score.
"""
from models.dual_model import DualModel


def main():
    engine = DualModel(model_dir="./models", legacy_weight=0.5, onnx_weight=0.5)

    opportunities = [
        {
            'hops': 2,
            'gross_profit': 50,
            'gas_cost': 15,
            'estimated_profit': 35,
            'confidence': 0.9,
            'initial_amount': 1000,
            'path': [{'tvl': 5_000_000}, {'tvl': 4_000_000}]
        },
        {
            'hops': 3,
            'gross_profit': 20,
            'gas_cost': 12,
            'estimated_profit': 8,
            'confidence': 0.75,
            'initial_amount': 500,
            'path': [{'tvl': 1_000_000}, {'tvl': 800_000}, {'tvl': 600_000}]
        }
    ]

    print("Running DualModel demo...")
    best = engine.score_opportunities(opportunities)

    if best is None:
        print("No opportunities")
        return

    print("Best opportunity selected:")
    print(f"  Estimated profit: {best.get('estimated_profit')}")
    print(f"  ML score: {best.get('ml_score')}")
    print(f"  Legacy score: {best.get('legacy_score')}")
    if 'onnx_score' in best:
        print(f"  ONNX score: {best.get('onnx_score')}")
    else:
        print("  ONNX score: (not available)")


if __name__ == '__main__':
    main()
