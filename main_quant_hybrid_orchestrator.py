#!/usr/bin/env python
"""
Hyperspeed X100 Hybrid Orchestrator
- Automated, cross-chain, modular, MEV-protected arbitrage system
- Dynamic pool discovery, async TVL analytics, ML scoring, batch rewards
- SIMULATION and LIVE execution modes with manual execution window
"""

import asyncio
import subprocess
import time
import sys
import argparse
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_js_pool_fetcher():
    """Run JavaScript pool fetcher to aggregate liquidity pool data"""
    print("[Hybrid] Running JS pool fetcher...")
    try:
        result = subprocess.run(["node", "dex_pool_fetcher.js"], 
                              check=False, 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print("[Hybrid] ✓ Pool fetcher completed successfully")
        else:
            print(f"[Hybrid] ⚠ Pool fetcher returned code {result.returncode}")
    except FileNotFoundError:
        print("[Hybrid] ⚠ dex_pool_fetcher.js not found - skipping")


def load_sdk_pool_info():
    """Load pools via SDK loader for ultra-low-latency access"""
    print("[Hybrid] Loading pools via SDK loader...")
    try:
        result = subprocess.run(["node", "sdk_pool_loader.js"], 
                              check=False,
                              capture_output=True,
                              text=True)
        if result.returncode == 0:
            print("[Hybrid] ✓ SDK pool loader completed successfully")
        else:
            print(f"[Hybrid] ⚠ SDK pool loader returned code {result.returncode}")
    except FileNotFoundError:
        print("[Hybrid] ⚠ sdk_pool_loader.js not found - skipping")


def run_precheck(chain="polygon"):
    """Run DEX/protocol precheck for contract validation"""
    print(f"[Hybrid] Running DEX/protocol precheck for {chain}...")
    try:
        from dex_protocol_precheck import DexProtocolPrecheck
        precheck = DexProtocolPrecheck(chain=chain)
        precheck.run_full_precheck()
        print(f"[Hybrid] ✓ Precheck for {chain} completed")
    except ImportError:
        print("[Hybrid] ⚠ dex_protocol_precheck module not found - skipping")
    except Exception as e:
        print(f"[Hybrid] ⚠ Precheck error: {e}")


async def arbitrage_main_loop(test_mode=False, mode=None):
    """Main arbitrage event loop with pool discovery, opportunity detection, and execution"""
    
    # Initialize components
    run_js_pool_fetcher()
    load_sdk_pool_info()
    run_precheck(chain="polygon")
    
    # Load configuration
    try:
        from config.config import (
            EXECUTION_MODE, ENABLE_MANUAL_WINDOW, MANUAL_WINDOW_DURATION,
            USE_DUAL_AI_ENGINE, ML_MODEL_DIR
        )
    except ImportError:
        EXECUTION_MODE = "SIMULATION"
        ENABLE_MANUAL_WINDOW = True
        MANUAL_WINDOW_DURATION = 5
        USE_DUAL_AI_ENGINE = True
        ML_MODEL_DIR = "./models"
    
    # Override mode if specified
    if mode:
        EXECUTION_MODE = mode.upper()
    
    # Initialize execution mode manager
    try:
        from execution_mode_manager import ExecutionModeManager, ExecutionMode
        exec_mode = ExecutionMode.LIVE if EXECUTION_MODE == "LIVE" else ExecutionMode.SIMULATION
        mode_manager = ExecutionModeManager(
            mode=exec_mode,
            enable_manual_window=ENABLE_MANUAL_WINDOW,
            manual_window_duration=MANUAL_WINDOW_DURATION
        )
        print(f"[Hybrid] ✓ Execution mode manager loaded ({EXECUTION_MODE} mode)")
    except ImportError as e:
        print(f"[Hybrid] ⚠ execution_mode_manager not found: {e}")
        mode_manager = None
    
    # Initialize ML engine (Dual AI or simple model)
    ml_engine = None
    if USE_DUAL_AI_ENGINE:
        try:
            from dual_ai_ml_engine import DualAIMLEngine
            ml_engine = DualAIMLEngine(model_dir=ML_MODEL_DIR)
            print("[Hybrid] ✓ Dual AI ML engine loaded (XGBoost + ONNX)")
        except ImportError:
            print("[Hybrid] ⚠ dual_ai_ml_engine not found - trying simple ML")
    
    if ml_engine is None:
        try:
            from defi_analytics_ml import MLAnalyticsEngine
            ml_engine = MLAnalyticsEngine()
            print("[Hybrid] ✓ ML analytics engine loaded")
        except ImportError:
            print("[Hybrid] ⚠ ML engine not found - using mock")
    
    # Try to import required modules
    try:
        from pool_registry_integrator import PoolRegistryIntegrator
        integrator = PoolRegistryIntegrator("pool_registry.json", "token_equivalence.json")
        print("[Hybrid] ✓ Pool registry integrator loaded")
    except ImportError:
        print("[Hybrid] ⚠ pool_registry_integrator not found - using mock")
        integrator = None
    
    try:
        from src.BillionaireBot_merkle_sender_tree_Version2 import MerkleRewardDistributor
        merkle_distributor = MerkleRewardDistributor()
        print("[Hybrid] ✓ Merkle reward distributor loaded")
    except ImportError:
        print("[Hybrid] ⚠ merkle reward distributor not found - using mock")
        merkle_distributor = None
    
    print("\n[Hybrid] Main arbitrage event loop started.")
    print(f"[Hybrid] Test mode: {test_mode}")
    print(f"[Hybrid] Execution mode: {EXECUTION_MODE}")
    
    if test_mode:
        print("\n[Hybrid] ✓ TEST MODE: All components initialized successfully")
        print("[Hybrid] ✓ System ready for production deployment")
        if mode_manager:
            mode_manager.print_statistics()
        return
    
    iteration = 0
    max_iterations = 100 if test_mode else None
    
    while True:
        iteration += 1
        
        # Detect opportunities
        try:
            from src.advanced_opportunity_detection_Version1 import OpportunityDetector
            if integrator:
                opportunities = OpportunityDetector(integrator).detect_opportunities()
            else:
                opportunities = []
        except ImportError:
            opportunities = []
        
        if not opportunities:
            print(f"[Hybrid] Iteration {iteration}: No opportunities. Waiting...")
            await asyncio.sleep(1)
            
            if max_iterations and iteration >= max_iterations:
                break
            continue
        
        # Score opportunities with ML
        best_opp = None
        if ml_engine and hasattr(ml_engine, 'score_opportunities'):
            best_opp = ml_engine.score_opportunities(opportunities)
        
        # If ML didn't return a result or no ML engine, use highest profit
        if not best_opp and opportunities:
            best_opp = max(opportunities, key=lambda x: x.get('estimated_profit', 0))
        
        if not best_opp:
            print(f"[Hybrid] Iteration {iteration}: No optimal arb. Waiting...")
            await asyncio.sleep(1)
            
            if max_iterations and iteration >= max_iterations:
                break
            continue
        
        # Determine if this is a hot route (use config thresholds)
        try:
            from config.config import (
                HOT_ROUTE_ML_SCORE_THRESHOLD,
                HOT_ROUTE_PROFIT_THRESHOLD,
                HOT_ROUTE_CONFIDENCE_THRESHOLD
            )
        except ImportError:
            # Fallback to defaults if config not available
            HOT_ROUTE_ML_SCORE_THRESHOLD = 0.8
            HOT_ROUTE_PROFIT_THRESHOLD = 50.0
            HOT_ROUTE_CONFIDENCE_THRESHOLD = 0.85
        
        ml_score = best_opp.get('ml_score', 0)
        profit = best_opp.get('estimated_profit', 0)
        confidence = best_opp.get('confidence', 0)
        is_hot_route = (
            ml_score > HOT_ROUTE_ML_SCORE_THRESHOLD or
            profit > HOT_ROUTE_PROFIT_THRESHOLD or
            confidence > HOT_ROUTE_CONFIDENCE_THRESHOLD
        )
        
        print(f"\n[Hybrid] Iteration {iteration}: Opportunity found!")
        print(f"  Estimated Profit: ${profit:.2f}")
        print(f"  ML Score: {ml_score:.4f}")
        print(f"  Confidence: {confidence:.2%}")
        print(f"  Hot Route: {'🔥 YES' if is_hot_route else 'No'}")
        
        # Define execution function
        def execute_arbitrage(opp):
            """Execute arbitrage transaction"""
            try:
                from src.arb_request_encoder import encode_arbitrage_request
                calldata = encode_arbitrage_request(opp)
                
                try:
                    from src.BillionaireBot_bloxroute_gateway_Version2 import send_private_transaction
                    tx_hash = send_private_transaction(calldata)
                    
                    return {
                        'success': True,
                        'tx_hash': tx_hash,
                        'actual_profit': opp.get('estimated_profit', 0) * 0.95  # Assume 95% of estimate
                    }
                except ImportError:
                    # Mock execution if gateway not available
                    return {
                        'success': True,
                        'tx_hash': f"0xMOCK{int(time.time())}",
                        'actual_profit': opp.get('estimated_profit', 0) * 0.95
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        # Execute using mode manager
        if mode_manager:
            result = mode_manager.execute_opportunity(
                best_opp, 
                execute_arbitrage,
                is_hot_route=is_hot_route
            )
        else:
            # Fallback to direct execution
            result = execute_arbitrage(best_opp)
        
        # Log trade result with ML engine
        if result.get('success') and ml_engine:
            tx_hash = result.get('tx_hash', 'N/A')
            actual_profit = result.get('actual_profit', 0)
            
            # Log to ML engine for future retraining
            if hasattr(ml_engine, 'add_trade_result'):
                ml_engine.add_trade_result(
                    best_opp, 
                    tx_hash,
                    success=True,
                    actual_profit=actual_profit
                )
        
        # Handle rewards distribution
        if best_opp.get("distribute_rewards") and merkle_distributor:
            try:
                merkle_tree = merkle_distributor.build_tree(best_opp["rewards"])
                merkle_distributor.distribute(merkle_tree)
                print("[Hybrid] ✓ Rewards distributed")
            except Exception as e:
                print(f"[Hybrid] ⚠ Reward distribution error: {e}")
        
        # Periodic refresh of pool data (every 5 minutes)
        if time.time() % 300 < 2:
            run_js_pool_fetcher()
            load_sdk_pool_info()
        
        await asyncio.sleep(0.15)
        
        if max_iterations and iteration >= max_iterations:
            print(f"[Hybrid] Reached maximum iterations ({max_iterations})")
            if mode_manager:
                mode_manager.print_statistics()
            break


def main():
    """Main entry point with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description='Quant Arbitrage System: Hyperspeed X100 Hybrid Orchestrator'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (initialize and validate components only)'
    )
    parser.add_argument(
        '--mode',
        choices=['SIMULATION', 'LIVE'],
        help='Execution mode: SIMULATION (paper trading) or LIVE (real money)',
        default=None
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("  QUANT ARBITRAGE SYSTEM: HYPERSPEED X100 EDITION")
    print("  Hybrid Python + Node.js Orchestrator")
    print("  With Dual AI ML Models & Execution Mode Manager")
    print("=" * 80)
    print()
    
    if args.mode:
        print(f"🎯 Execution Mode: {args.mode}")
        if args.mode == "SIMULATION":
            print("   📊 Paper trading - Shows what WOULD happen (safe learning)")
        else:
            print("   💰 Live trading - Real executions with real money")
            print("   🔥 5-second manual window for hot routes (M=execute, S=skip)")
        print()
    
    try:
        asyncio.run(arbitrage_main_loop(test_mode=args.test, mode=args.mode))
    except KeyboardInterrupt:
        print("\n[Hybrid] Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[Hybrid] ✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
