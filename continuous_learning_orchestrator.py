#!/usr/bin/env python3
"""
Orchestrator Integration for Continuous Learning
Hooks the continuous learning system into the main orchestrator for real-time training
"""

from typing import Dict, Any, Optional
from continuous_learning_manager import ContinuousLearningManager


class ContinuousLearningOrchestrator:
    """
    Wrapper that integrates continuous learning with the main arbitrage orchestrator
    
    This enables "Spring Training" mode where the system runs at full scale in
    SIMULATION mode while continuously improving the AI models.
    """
    
    def __init__(
        self,
        enable_learning: bool = True,
        model_dir: str = "./models",
        retrain_interval: int = 100,
        verbose: bool = True
    ):
        """
        Initialize the learning orchestrator
        
        Args:
            enable_learning: Enable continuous learning
            model_dir: Directory for model storage
            retrain_interval: Retrain every N samples
            verbose: Print learning statistics periodically
        """
        self.enable_learning = enable_learning
        self.verbose = verbose
        self.learning_manager = None
        
        if enable_learning:
            self.learning_manager = ContinuousLearningManager(
                model_dir=model_dir,
                buffer_size=1000,
                retrain_interval=retrain_interval,
                min_samples_for_training=50,
                enable_auto_retrain=True,
                performance_threshold=0.05
            )
            print(f"[Orchestrator] 🎯 Continuous Learning ENABLED (Spring Training Mode)")
        else:
            print(f"[Orchestrator] Continuous Learning DISABLED")
    
    def on_opportunity_evaluated(
        self,
        opportunity: Dict[str, Any],
        ml_score: float,
        selected: bool = False
    ):
        """
        Called when an opportunity is evaluated by the ML system
        
        Args:
            opportunity: The opportunity dict
            ml_score: Score predicted by ML model
            selected: Whether this opportunity was selected for execution
        """
        if not self.learning_manager:
            return
        
        # Record the prediction
        self.learning_manager.observe_opportunity(opportunity, ml_score)
        
        # If opportunity was selected, we'll track its outcome
        if selected:
            opportunity['_tracked_for_learning'] = True
    
    def on_trade_simulated(
        self,
        opportunity: Dict[str, Any],
        simulation_result: Dict[str, Any]
    ):
        """
        Called after a trade is simulated (in SIMULATION mode)
        
        Args:
            opportunity: The original opportunity
            simulation_result: Result of simulation with actual_profit, success, etc.
        """
        if not self.learning_manager:
            return
        
        # Extract outcome
        actual_profit = simulation_result.get('actual_profit', 0)
        success = simulation_result.get('success', False)
        opp_id = simulation_result.get('opportunity_id', 'unknown')
        
        # Feed back to learning manager
        self.learning_manager.observe_outcome(opp_id, actual_profit, success)
    
    def on_trade_executed(
        self,
        opportunity: Dict[str, Any],
        execution_result: Dict[str, Any]
    ):
        """
        Called after a real trade is executed (in LIVE mode)
        
        In LIVE mode, we learn from actual blockchain execution results
        
        Args:
            opportunity: The original opportunity
            execution_result: Result with tx_hash, actual_profit, success, etc.
        """
        if not self.learning_manager:
            return
        
        # Extract outcome from real execution
        actual_profit = execution_result.get('actual_profit', 0)
        success = execution_result.get('success', False)
        tx_hash = execution_result.get('tx_hash', 'unknown')
        
        # Feed back to learning manager
        self.learning_manager.observe_outcome(tx_hash, actual_profit, success)
        
        # In LIVE mode, also log to the dual AI engine for permanent record
        if hasattr(self.learning_manager, 'engine') and self.learning_manager.engine:
            self.learning_manager.engine.add_trade_result(
                opportunity=opportunity,
                tx_hash=tx_hash,
                success=success,
                actual_profit=actual_profit
            )
    
    def print_learning_stats(self):
        """Print current learning statistics"""
        if self.learning_manager:
            self.learning_manager.print_statistics()
    
    def get_learning_stats(self) -> Optional[Dict[str, Any]]:
        """Get learning statistics as dict"""
        if self.learning_manager:
            return self.learning_manager.get_statistics()
        return None
    
    def force_retrain(self):
        """Manually trigger model retraining"""
        if self.learning_manager:
            self.learning_manager.force_retrain()
        else:
            print("[Orchestrator] Continuous learning not enabled")
    
    def export_training_data(self, output_file: str = None):
        """Export collected training data"""
        if self.learning_manager:
            return self.learning_manager.export_training_data(output_file)
        return None


# Example integration with main orchestrator
def integrate_with_orchestrator_example():
    """
    Example of how to integrate continuous learning with the main orchestrator
    """
    
    # Initialize continuous learning
    learning = ContinuousLearningOrchestrator(
        enable_learning=True,
        retrain_interval=50
    )
    
    # In your main orchestrator loop:
    # 
    # while True:
    #     opportunities = detect_opportunities()
    #     
    #     for opp in opportunities:
    #         # Score with AI
    #         result = ai_engine.score_opportunities([opp])
    #         ml_score = result['ml_score']
    #         
    #         # HOOK: Record prediction for learning
    #         learning.on_opportunity_evaluated(opp, ml_score, selected=True)
    #         
    #         # Simulate or execute
    #         if MODE == "SIMULATION":
    #             sim_result = simulate_trade(opp)
    #             
    #             # HOOK: Record simulation outcome
    #             learning.on_trade_simulated(opp, sim_result)
    #         
    #         elif MODE == "LIVE":
    #             exec_result = execute_trade(opp)
    #             
    #             # HOOK: Record real execution outcome
    #             learning.on_trade_executed(opp, exec_result)
    #     
    #     # Periodically show learning progress
    #     if iteration % 100 == 0:
    #         learning.print_learning_stats()
    
    print("Example integration complete - see code above")


if __name__ == '__main__':
    integrate_with_orchestrator_example()
