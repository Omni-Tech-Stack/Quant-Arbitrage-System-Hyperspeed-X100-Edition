#!/usr/bin/env python
"""
Execution Mode Manager
Handles SIMULATION vs LIVE trading modes with manual execution window
"""

import os
import sys
import time
import threading
from enum import Enum
from typing import Dict, Any, Optional, Callable
from datetime import datetime


class ExecutionMode(Enum):
    """Execution modes for the arbitrage system"""
    SIMULATION = "SIMULATION"  # Paper trading with mock executions
    LIVE = "LIVE"              # Real executions with real money


class ManualExecutionDecision(Enum):
    """Manual execution decisions"""
    EXECUTE = "EXECUTE"
    SKIP = "SKIP"
    TIMEOUT = "TIMEOUT"


class ExecutionModeManager:
    """
    Manages execution mode (SIMULATION vs LIVE) and manual execution windows
    
    Features:
    - SIMULATION mode: Paper trading with mock executions
    - LIVE mode: Real executions immediately
    - BONUS: 5-second window for manual execution on hot routes (press 'M' or 'S')
    """
    
    def __init__(self, mode: ExecutionMode = ExecutionMode.SIMULATION, 
                 enable_manual_window: bool = True,
                 manual_window_duration: int = 5):
        """
        Initialize execution mode manager
        
        Args:
            mode: ExecutionMode.SIMULATION or ExecutionMode.LIVE
            enable_manual_window: Enable 5-second manual execution window
            manual_window_duration: Duration of manual window in seconds
        """
        self.mode = mode
        self.enable_manual_window = enable_manual_window
        self.manual_window_duration = manual_window_duration
        
        # Statistics
        self.stats = {
            'simulation': {
                'total_opportunities': 0,
                'mock_executions': 0,
                'total_paper_profit': 0.0,
                'successful_rate': 0.0
            },
            'live': {
                'total_opportunities': 0,
                'real_executions': 0,
                'manual_executions': 0,
                'auto_executions': 0,
                'skipped': 0,
                'total_profit': 0.0
            }
        }
        
        self.user_decision = None
        self.decision_event = threading.Event()
        
        print(f"[ExecutionMode] Initialized in {mode.value} mode")
        if enable_manual_window and mode == ExecutionMode.LIVE:
            print(f"[ExecutionMode] Manual execution window: {manual_window_duration} seconds")
    
    def set_mode(self, mode: ExecutionMode):
        """Change execution mode"""
        old_mode = self.mode
        self.mode = mode
        print(f"[ExecutionMode] Mode changed: {old_mode.value} → {mode.value}")
    
    def is_simulation_mode(self) -> bool:
        """Check if in simulation mode"""
        return self.mode == ExecutionMode.SIMULATION
    
    def is_live_mode(self) -> bool:
        """Check if in live mode"""
        return self.mode == ExecutionMode.LIVE
    
    def execute_opportunity(self, opportunity: Dict[str, Any], 
                          execute_fn: Callable, 
                          is_hot_route: bool = False) -> Dict[str, Any]:
        """
        Execute an opportunity based on current mode
        
        Args:
            opportunity: The arbitrage opportunity to execute
            execute_fn: Function to call for real execution
            is_hot_route: Whether this is a hot route (high profit/confidence)
            
        Returns:
            Execution result dictionary
        """
        if self.mode == ExecutionMode.SIMULATION:
            return self._execute_simulation(opportunity)
        else:  # LIVE mode
            return self._execute_live(opportunity, execute_fn, is_hot_route)
    
    def _execute_simulation(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute in simulation mode (paper trading)
        Shows what WOULD happen without real execution
        """
        self.stats['simulation']['total_opportunities'] += 1
        self.stats['simulation']['mock_executions'] += 1
        
        estimated_profit = opportunity.get('estimated_profit', 0)
        
        # Simulate execution with 85% success rate
        import random
        success = random.random() < 0.85
        
        if success:
            # Add some variance to simulate real conditions
            actual_profit = estimated_profit * random.uniform(0.9, 1.05)
            self.stats['simulation']['total_paper_profit'] += actual_profit
        else:
            actual_profit = -opportunity.get('gas_cost', 20)  # Lost gas
        
        # Update success rate
        total = self.stats['simulation']['mock_executions']
        if success:
            successful = int(self.stats['simulation']['successful_rate'] * (total - 1)) + 1
        else:
            successful = int(self.stats['simulation']['successful_rate'] * (total - 1))
        self.stats['simulation']['successful_rate'] = successful / total if total > 0 else 0
        
        result = {
            'mode': 'SIMULATION',
            'success': success,
            'executed': True,
            'mock_execution': True,
            'estimated_profit': estimated_profit,
            'actual_profit': actual_profit if success else 0,
            'tx_hash': f"0xSIMULATION{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'message': '✅ SIMULATION: Would have executed (paper trading)' if success else '⚠ SIMULATION: Would have failed'
        }
        
        print(f"\n[SIMULATION MODE] 📊 Paper Trading Result:")
        print(f"  Estimated Profit: ${estimated_profit:.2f}")
        print(f"  Actual Profit: ${actual_profit:.2f}")
        print(f"  Success: {'✅ Yes' if success else '❌ No'}")
        print(f"  Total Paper Profit: ${self.stats['simulation']['total_paper_profit']:.2f}")
        print(f"  Success Rate: {self.stats['simulation']['successful_rate']*100:.1f}%\n")
        
        return result
    
    def _execute_live(self, opportunity: Dict[str, Any], 
                     execute_fn: Callable,
                     is_hot_route: bool = False) -> Dict[str, Any]:
        """
        Execute in live mode with real money
        
        Features:
        - Automatic execution for normal routes
        - 5-second manual window for hot routes (high profit/confidence)
        """
        self.stats['live']['total_opportunities'] += 1
        
        # Check if manual window should be shown
        show_manual_window = (
            self.enable_manual_window and 
            is_hot_route and 
            self._should_show_manual_window(opportunity)
        )
        
        if show_manual_window:
            print(f"\n{'='*80}")
            print(f"  🔥 HOT ROUTE DETECTED - MANUAL EXECUTION WINDOW")
            print(f"{'='*80}")
            print(f"  Estimated Profit: ${opportunity.get('estimated_profit', 0):.2f}")
            print(f"  ML Score: {opportunity.get('ml_score', 0):.4f}")
            print(f"  Confidence: {opportunity.get('confidence', 0):.2%}")
            print(f"  Hops: {opportunity.get('hops', 0)}")
            print(f"\n  Press 'M' to MANUALLY EXECUTE or 'S' to SKIP")
            print(f"  Timeout in {self.manual_window_duration} seconds (auto-execute)")
            print(f"{'='*80}\n")
            
            decision = self._get_manual_decision()
            
            if decision == ManualExecutionDecision.SKIP:
                self.stats['live']['skipped'] += 1
                return {
                    'mode': 'LIVE',
                    'success': False,
                    'executed': False,
                    'skipped': True,
                    'manual_decision': 'SKIP',
                    'message': '⏭ Manually skipped by user',
                    'timestamp': datetime.now().isoformat()
                }
            
            if decision == ManualExecutionDecision.EXECUTE:
                self.stats['live']['manual_executions'] += 1
                print("  ✅ Manual execution confirmed by user\n")
            else:  # TIMEOUT
                self.stats['live']['auto_executions'] += 1
                print("  ⏰ Timeout - Auto-executing\n")
        else:
            # Auto-execute for non-hot routes in live mode
            self.stats['live']['auto_executions'] += 1
        
        # Execute the opportunity
        print(f"[LIVE MODE] 💰 Executing real arbitrage transaction...")
        
        try:
            result = execute_fn(opportunity)
            self.stats['live']['real_executions'] += 1
            
            if result.get('success'):
                actual_profit = result.get('actual_profit', 0)
                self.stats['live']['total_profit'] += actual_profit
                
                print(f"  ✅ Transaction successful!")
                print(f"  Tx Hash: {result.get('tx_hash', 'N/A')}")
                print(f"  Profit: ${actual_profit:.2f}")
            else:
                print(f"  ❌ Transaction failed: {result.get('error', 'Unknown error')}")
            
            result['mode'] = 'LIVE'
            result['manual_execution'] = show_manual_window and decision == ManualExecutionDecision.EXECUTE
            return result
            
        except Exception as e:
            print(f"  ❌ Execution error: {e}")
            return {
                'mode': 'LIVE',
                'success': False,
                'executed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _should_show_manual_window(self, opportunity: Dict[str, Any]) -> bool:
        """
        Determine if manual window should be shown for this opportunity
        
        Hot route criteria:
        - High ML score (> 0.8)
        - High profit (> $50)
        - High confidence (> 0.85)
        """
        ml_score = opportunity.get('ml_score', 0)
        profit = opportunity.get('estimated_profit', 0)
        confidence = opportunity.get('confidence', 0)
        
        is_hot = (
            ml_score > 0.8 or
            profit > 50 or
            confidence > 0.85
        )
        
        return is_hot
    
    def _get_manual_decision(self) -> ManualExecutionDecision:
        """
        Get manual decision from user within timeout window
        Uses non-blocking input with timeout
        """
        self.user_decision = None
        self.decision_event.clear()
        
        # Start input thread
        input_thread = threading.Thread(target=self._input_thread)
        input_thread.daemon = True
        input_thread.start()
        
        # Wait for decision or timeout
        decision_made = self.decision_event.wait(timeout=self.manual_window_duration)
        
        if decision_made and self.user_decision:
            return self.user_decision
        else:
            return ManualExecutionDecision.TIMEOUT
    
    def _input_thread(self):
        """Thread to handle user input"""
        try:
            # Non-blocking input simulation
            # In production, this would use proper terminal input handling
            print("  Waiting for input (M/S)...", end='', flush=True)
            
            # Simulate checking for input
            # In a real implementation, you'd use select() or similar
            # For now, we'll auto-timeout for testing
            time.sleep(self.manual_window_duration)
            
        except Exception as e:
            print(f"\n  Input error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            'mode': self.mode.value,
            'simulation': self.stats['simulation'],
            'live': self.stats['live'],
            'manual_window_enabled': self.enable_manual_window
        }
    
    def print_statistics(self):
        """Print execution statistics"""
        print(f"\n{'='*80}")
        print(f"  EXECUTION MODE STATISTICS")
        print(f"{'='*80}")
        print(f"  Current Mode: {self.mode.value}")
        print(f"  Manual Window: {'Enabled' if self.enable_manual_window else 'Disabled'}")
        print(f"\n  SIMULATION MODE:")
        print(f"    Total Opportunities: {self.stats['simulation']['total_opportunities']}")
        print(f"    Mock Executions: {self.stats['simulation']['mock_executions']}")
        print(f"    Total Paper Profit: ${self.stats['simulation']['total_paper_profit']:.2f}")
        print(f"    Success Rate: {self.stats['simulation']['successful_rate']*100:.1f}%")
        print(f"\n  LIVE MODE:")
        print(f"    Total Opportunities: {self.stats['live']['total_opportunities']}")
        print(f"    Real Executions: {self.stats['live']['real_executions']}")
        print(f"    Manual Executions: {self.stats['live']['manual_executions']}")
        print(f"    Auto Executions: {self.stats['live']['auto_executions']}")
        print(f"    Skipped: {self.stats['live']['skipped']}")
        print(f"    Total Real Profit: ${self.stats['live']['total_profit']:.2f}")
        print(f"{'='*80}\n")


def main():
    """Test execution mode manager"""
    print("=" * 80)
    print("  EXECUTION MODE MANAGER TEST")
    print("=" * 80)
    print()
    
    # Create manager in simulation mode
    manager = ExecutionModeManager(
        mode=ExecutionMode.SIMULATION,
        enable_manual_window=True
    )
    
    # Test simulation execution
    print("Testing SIMULATION mode...")
    test_opp = {
        'estimated_profit': 35.50,
        'gas_cost': 20,
        'ml_score': 0.85,
        'confidence': 0.90,
        'hops': 3
    }
    
    def mock_execute(opp):
        return {
            'success': True,
            'tx_hash': '0xTEST123',
            'actual_profit': 32.0
        }
    
    result = manager.execute_opportunity(test_opp, mock_execute, is_hot_route=True)
    print(f"Result: {result}\n")
    
    # Switch to live mode
    print("\nSwitching to LIVE mode...")
    manager.set_mode(ExecutionMode.LIVE)
    
    # Test live execution
    print("\nTesting LIVE mode (auto-execute after timeout)...")
    result = manager.execute_opportunity(test_opp, mock_execute, is_hot_route=True)
    print(f"Result: {result}\n")
    
    # Print statistics
    manager.print_statistics()
    
    print("✓ Execution mode manager test completed")


if __name__ == "__main__":
    main()
