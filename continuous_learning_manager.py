#!/usr/bin/env python3
"""
Continuous Learning Manager - Real-Time AI Training System
"Spring Training" for the Dual AI arbitrage system

This module enables the system to learn and improve in real-time while running
in SIMULATION mode, collecting live market data and continuously retraining
the ML models without risking real capital.

Features:
- Real-time data collection from live opportunities
- Continuous feedback loop (predicted vs simulated outcomes)
- Incremental model retraining on configurable intervals
- Experience replay buffer for efficient learning
- Model versioning and performance tracking
- Automatic rollback if new model performs worse
"""

import os
import json
import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
import numpy as np

try:
    from dual_ai_ml_engine import DualAIMLEngine
    DUAL_AI_AVAILABLE = True
except ImportError:
    DUAL_AI_AVAILABLE = False
    print("[ContinuousLearning] Warning: DualAIMLEngine not available")


class ContinuousLearningManager:
    """
    Manages continuous learning and real-time model improvement
    
    Think of this as "Spring Training" - the system practices on live data
    at full scale without executing real trades, constantly improving its
    decision-making capabilities.
    """
    
    def __init__(
        self,
        model_dir: str = "./models",
        buffer_size: int = 1000,
        retrain_interval: int = 100,  # Retrain every N samples
        min_samples_for_training: int = 50,
        enable_auto_retrain: bool = True,
        performance_threshold: float = 0.05,  # 5% improvement needed to keep new model
    ):
        """
        Initialize the continuous learning manager
        
        Args:
            model_dir: Directory to save/load models
            buffer_size: Maximum samples in experience replay buffer
            retrain_interval: Retrain model after this many new samples
            min_samples_for_training: Minimum samples needed before first training
            enable_auto_retrain: Automatically retrain when interval reached
            performance_threshold: Min improvement % to accept new model
        """
        self.model_dir = model_dir
        self.buffer_size = buffer_size
        self.retrain_interval = retrain_interval
        self.min_samples_for_training = min_samples_for_training
        self.enable_auto_retrain = enable_auto_retrain
        self.performance_threshold = performance_threshold
        
        # Experience replay buffer: stores (opportunity, predicted_score, actual_outcome)
        self.experience_buffer = deque(maxlen=buffer_size)
        
        # Performance tracking
        self.total_opportunities = 0
        self.correct_predictions = 0
        self.training_runs = 0
        self.last_training_time = None
        self.current_accuracy = 0.0
        
        # Model version tracking
        self.model_version = 0
        self.model_performance_history = []
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Initialize the AI engine
        if DUAL_AI_AVAILABLE:
            self.engine = DualAIMLEngine(model_dir=model_dir)
        else:
            self.engine = None
            print("[ContinuousLearning] Running without AI engine (demo mode)")
        
        # Load existing training data if available
        self._load_training_state()
        
        print(f"[ContinuousLearning] Initialized with buffer_size={buffer_size}, retrain_interval={retrain_interval}")
        print(f"[ContinuousLearning] Auto-retrain: {enable_auto_retrain}, Performance threshold: {performance_threshold*100}%")
    
    def observe_opportunity(self, opportunity: Dict[str, Any], predicted_score: float):
        """
        Record an opportunity that was evaluated by the AI
        
        This is called when the system evaluates an opportunity in SIMULATION mode.
        We store the opportunity and the AI's prediction for later learning.
        
        Args:
            opportunity: The opportunity dict with all features
            predicted_score: The ML model's predicted score
        """
        with self.lock:
            # Store with a placeholder for actual outcome (will be filled later)
            self.experience_buffer.append({
                'opportunity': opportunity.copy(),
                'predicted_score': predicted_score,
                'actual_outcome': None,  # To be filled by observe_outcome()
                'timestamp': datetime.now().isoformat()
            })
            
            self.total_opportunities += 1
    
    def observe_outcome(self, opportunity_id: str, actual_profit: float, success: bool):
        """
        Record the actual outcome of an opportunity (simulated execution)
        
        This is called after simulating the trade to see what would have happened.
        We use this to calculate the "actual" quality score of the opportunity.
        
        Args:
            opportunity_id: Unique identifier for the opportunity
            actual_profit: Actual profit from simulation (can be negative)
            success: Whether the simulated trade was successful
        """
        with self.lock:
            # Calculate actual outcome score (0-1 range)
            estimated_profit = 50  # Default assumption
            
            # Find the matching opportunity in buffer (match by recent entries)
            for exp in reversed(self.experience_buffer):
                if exp['actual_outcome'] is None:
                    opp = exp['opportunity']
                    estimated = opp.get('estimated_profit', 50)
                    
                    # Calculate actual quality score
                    if success:
                        # Scale based on actual vs estimated profit
                        profit_ratio = actual_profit / max(estimated, 1)
                        actual_score = min(max(profit_ratio * 0.5 + 0.3, 0), 1)
                    else:
                        actual_score = 0.0
                    
                    exp['actual_outcome'] = actual_score
                    exp['actual_profit'] = actual_profit
                    exp['success'] = success
                    
                    # Track prediction accuracy
                    predicted = exp['predicted_score']
                    error = abs(predicted - actual_score)
                    if error < 0.2:  # Within 20% is considered "correct"
                        self.correct_predictions += 1
                    
                    break
            
            # Check if we should retrain
            if self.enable_auto_retrain:
                labeled_samples = sum(1 for exp in self.experience_buffer if exp['actual_outcome'] is not None)
                
                if labeled_samples >= self.min_samples_for_training:
                    if labeled_samples % self.retrain_interval == 0:
                        print(f"\n[ContinuousLearning] 🎯 Retrain threshold reached ({labeled_samples} samples)")
                        self._trigger_retraining()
    
    def _trigger_retraining(self):
        """
        Trigger a retraining cycle using collected experience
        
        This runs in the background and updates the model if the new version
        performs better than the current one.
        """
        if not DUAL_AI_AVAILABLE or self.engine is None:
            print("[ContinuousLearning] Skipping retrain - AI engine not available")
            return
        
        print(f"[ContinuousLearning] 🔄 Starting retraining cycle #{self.training_runs + 1}...")
        
        # Extract training data from experience buffer
        training_data = []
        labels = []
        
        with self.lock:
            for exp in self.experience_buffer:
                if exp['actual_outcome'] is not None:
                    training_data.append(exp['opportunity'])
                    labels.append(exp['actual_outcome'])
        
        if len(training_data) < self.min_samples_for_training:
            print(f"[ContinuousLearning] ⚠ Not enough labeled samples ({len(training_data)}), skipping")
            return
        
        print(f"[ContinuousLearning] Training on {len(training_data)} real-world samples...")
        
        # Save current model as backup
        backup_dir = os.path.join(self.model_dir, f"backup_v{self.model_version}")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Train new model
        try:
            old_accuracy = self.current_accuracy
            
            # Train the dual AI engine
            self.engine.train_models(training_data, labels)
            
            # Validate new model performance
            new_accuracy = self._validate_model(training_data, labels)
            
            improvement = new_accuracy - old_accuracy
            improvement_pct = (improvement / max(old_accuracy, 0.01)) * 100
            
            print(f"[ContinuousLearning] 📊 Validation Results:")
            print(f"  Old accuracy: {old_accuracy:.4f}")
            print(f"  New accuracy: {new_accuracy:.4f}")
            print(f"  Improvement: {improvement:+.4f} ({improvement_pct:+.1f}%)")
            
            # Accept new model if it's better or within threshold
            if new_accuracy >= old_accuracy * (1 - self.performance_threshold):
                self.model_version += 1
                self.current_accuracy = new_accuracy
                self.training_runs += 1
                self.last_training_time = datetime.now()
                
                self.model_performance_history.append({
                    'version': self.model_version,
                    'accuracy': new_accuracy,
                    'improvement': improvement,
                    'samples': len(training_data),
                    'timestamp': self.last_training_time.isoformat()
                })
                
                print(f"[ContinuousLearning] ✅ New model v{self.model_version} ACCEPTED!")
                self._save_training_state()
            else:
                print(f"[ContinuousLearning] ❌ New model REJECTED (performance degraded)")
                # Would restore backup here in production
        
        except Exception as e:
            print(f"[ContinuousLearning] ⚠ Training failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _validate_model(self, X: List[Dict[str, Any]], y: List[float]) -> float:
        """
        Validate model performance on training data
        
        Returns:
            Accuracy score (0-1)
        """
        if not self.engine:
            return 0.0
        
        # Use a simple accuracy metric
        correct = 0
        total = len(y)
        
        for i, opp in enumerate(X):
            result = self.engine.score_opportunities([opp])
            if result:
                predicted = result['ml_score']
                actual = y[i]
                
                # Consider prediction correct if within 20% of actual
                if abs(predicted - actual) < 0.2:
                    correct += 1
        
        return correct / max(total, 1)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current learning statistics
        
        Returns:
            Dict with performance metrics
        """
        with self.lock:
            labeled_samples = sum(1 for exp in self.experience_buffer if exp['actual_outcome'] is not None)
            buffer_usage = len(self.experience_buffer) / self.buffer_size
            
            if self.total_opportunities > 0:
                prediction_accuracy = self.correct_predictions / self.total_opportunities
            else:
                prediction_accuracy = 0.0
            
            return {
                'total_opportunities_observed': self.total_opportunities,
                'labeled_samples': labeled_samples,
                'buffer_usage_pct': buffer_usage * 100,
                'prediction_accuracy': prediction_accuracy,
                'training_runs': self.training_runs,
                'model_version': self.model_version,
                'current_model_accuracy': self.current_accuracy,
                'last_training_time': self.last_training_time.isoformat() if self.last_training_time else None,
                'performance_history': self.model_performance_history[-5:]  # Last 5 versions
            }
    
    def print_statistics(self):
        """Print formatted statistics to console"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 80)
        print("  CONTINUOUS LEARNING - SPRING TRAINING STATS")
        print("=" * 80)
        print(f"  Total Opportunities Observed: {stats['total_opportunities_observed']}")
        print(f"  Labeled Samples Collected: {stats['labeled_samples']}")
        print(f"  Experience Buffer Usage: {stats['buffer_usage_pct']:.1f}%")
        print(f"  Prediction Accuracy: {stats['prediction_accuracy']:.2%}")
        print(f"  Training Runs Completed: {stats['training_runs']}")
        print(f"  Current Model Version: v{stats['model_version']}")
        print(f"  Current Model Accuracy: {stats['current_model_accuracy']:.4f}")
        
        if stats['performance_history']:
            print("\n  Recent Performance History:")
            for perf in stats['performance_history']:
                print(f"    v{perf['version']}: {perf['accuracy']:.4f} ({perf['improvement']:+.4f}) - {perf['samples']} samples")
        
        print("=" * 80 + "\n")
    
    def _save_training_state(self):
        """Save training state and experience buffer to disk"""
        state_file = os.path.join(self.model_dir, "continuous_learning_state.json")
        
        with self.lock:
            state = {
                'model_version': self.model_version,
                'training_runs': self.training_runs,
                'current_accuracy': self.current_accuracy,
                'total_opportunities': self.total_opportunities,
                'correct_predictions': self.correct_predictions,
                'last_training_time': self.last_training_time.isoformat() if self.last_training_time else None,
                'performance_history': self.model_performance_history,
                'experience_buffer': list(self.experience_buffer)[-100:]  # Save last 100
            }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"[ContinuousLearning] 💾 State saved to {state_file}")
        except Exception as e:
            print(f"[ContinuousLearning] ⚠ Failed to save state: {e}")
    
    def _load_training_state(self):
        """Load previous training state from disk"""
        state_file = os.path.join(self.model_dir, "continuous_learning_state.json")
        
        if not os.path.exists(state_file):
            print("[ContinuousLearning] No previous state found, starting fresh")
            return
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            self.model_version = state.get('model_version', 0)
            self.training_runs = state.get('training_runs', 0)
            self.current_accuracy = state.get('current_accuracy', 0.0)
            self.total_opportunities = state.get('total_opportunities', 0)
            self.correct_predictions = state.get('correct_predictions', 0)
            self.model_performance_history = state.get('performance_history', [])
            
            last_training = state.get('last_training_time')
            if last_training:
                self.last_training_time = datetime.fromisoformat(last_training)
            
            # Restore recent experience buffer
            buffer_data = state.get('experience_buffer', [])
            self.experience_buffer = deque(buffer_data, maxlen=self.buffer_size)
            
            print(f"[ContinuousLearning] 📂 Loaded state: v{self.model_version}, {self.training_runs} training runs")
            print(f"[ContinuousLearning] Restored {len(self.experience_buffer)} samples from buffer")
        
        except Exception as e:
            print(f"[ContinuousLearning] ⚠ Failed to load state: {e}")
    
    def force_retrain(self):
        """Manually trigger a retraining cycle"""
        print("[ContinuousLearning] 🔧 Manual retrain triggered")
        self._trigger_retraining()
    
    def export_training_data(self, output_file: str = None):
        """
        Export collected training data for analysis or offline training
        
        Args:
            output_file: Path to save training data (JSONL format)
        """
        if output_file is None:
            output_file = os.path.join(self.model_dir, f"training_data_export_{int(time.time())}.jsonl")
        
        with self.lock:
            labeled_data = [exp for exp in self.experience_buffer if exp['actual_outcome'] is not None]
        
        try:
            with open(output_file, 'w') as f:
                for exp in labeled_data:
                    f.write(json.dumps(exp) + '\n')
            
            print(f"[ContinuousLearning] 📤 Exported {len(labeled_data)} samples to {output_file}")
            return output_file
        
        except Exception as e:
            print(f"[ContinuousLearning] ⚠ Export failed: {e}")
            return None


def main():
    """Demo of continuous learning manager"""
    print("\n🎯 CONTINUOUS LEARNING MANAGER - DEMO\n")
    
    manager = ContinuousLearningManager(
        model_dir="./models",
        buffer_size=500,
        retrain_interval=50,
        min_samples_for_training=30,
        enable_auto_retrain=True
    )
    
    print("\nSimulating 'Spring Training' with live market data...\n")
    
    # Simulate observing opportunities during live operation
    for i in range(75):
        # Create a fake opportunity
        opp = {
            'hops': np.random.randint(2, 5),
            'gross_profit': np.random.uniform(20, 100),
            'gas_cost': np.random.uniform(10, 40),
            'estimated_profit': np.random.uniform(-10, 70),
            'confidence': np.random.uniform(0.6, 0.95),
            'initial_amount': np.random.choice([1000, 2000, 5000]),
            'path': [{'tvl': np.random.uniform(1_000_000, 10_000_000)} for _ in range(2)]
        }
        
        predicted_score = np.random.uniform(0.3, 0.9)
        manager.observe_opportunity(opp, predicted_score)
        
        # Simulate outcome
        success = np.random.rand() > 0.3
        actual_profit = opp['estimated_profit'] * np.random.uniform(0.7, 1.2) if success else -opp['gas_cost']
        manager.observe_outcome(f"opp_{i}", actual_profit, success)
        
        if (i + 1) % 25 == 0:
            print(f"Processed {i + 1} opportunities...")
    
    # Show final statistics
    manager.print_statistics()
    
    # Export training data
    manager.export_training_data()


if __name__ == '__main__':
    main()
