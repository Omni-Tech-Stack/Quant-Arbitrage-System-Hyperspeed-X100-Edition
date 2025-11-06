## Operation summary: stages, functions, and files

This document maps the system flow (boot → data fetch → opportunity find → op scoring → flashloan execution) to concrete modules, functions, inputs/outputs and edge cases in this repository.

1) Boot / Start-up
- Entry point: `main_quant_hybrid_orchestrator.py` → `main()` and `arbitrage_main_loop()`
- Actions:
  - Run JavaScript pool fetcher: `dex_pool_fetcher.js` (invoked via `run_js_pool_fetcher()`)
  - Load SDK pools: `sdk_pool_loader.js` (invoked via `load_sdk_pool_info()`)
  - DEX/protocol precheck: `dex_protocol_precheck.DexProtocolPrecheck.run_full_precheck()` (invoked via `run_precheck()`)
- Success criteria: fetchers start, integrator and ML engines importable (or graceful fallback to mocks)

2) Pool discovery & TVL fetching
- Module: `orchestrator_tvl_hyperspeed.py` → `TVLOrchestrator`
- Key functions:
  - `fetch_all_chains()` — parallel fetch for configured chains
  - `fetch_chain_tvl(chain)` — fetch protocols for a chain
  - `aggregate_tvl(results)`, `get_statistics(results)`
- Protocol fetchers: `balancer_tvl_fetcher.py`, `curve_tvl_fetcher.py`, `uniswapv3_tvl_fetcher.py`, plus JS fetcher `dex_pool_fetcher.js`
- Outputs: per-chain JSON with `pools`, `total_tvl`, `pool_count`, timestamps
- Edge cases: network errors, rate limits — orchestrator returns empty/zeroed structures and logs warnings

3) Opportunity finding (route enumeration & simulation)
- Typical module referenced by orchestrator: `advanced_opportunity_detection_Version1` (import attempt in `arbitrage_main_loop()`) or other detector modules
- Expected behavior:
  - Enumerate candidate routes between pools discovered by TVL fetchers
  - For each route, simulate execution (swap math, amounts out) and compute estimated profit before fees
  - Call flashloan calculation / impact endpoints to compute an executable amount
- Inputs: pool reserves, exchange fees, token equivalence (`token_equivalence.json`), route definition
- Outputs: list of opportunity objects (route, expected profit, constraints)

4) Flashloan calculation & market-impact prediction
- Backend docs: `FLASHLOAN_API_DOCUMENTATION.md` and `FLASHLOAN_COMPLETE_GUIDE.md`
- Core engine: native Rust engine (exposed via backend REST API)
- API endpoints (backend):
  - `POST /api/calculate-flashloan` — returns optimal flashloan amount (binary search), profitability flag
  - `POST /api/calculate-impact` — returns market impact (price slippage) for a trade amount
  - `POST /api/calculate-multihop-slippage` — total slippage across hops
  - `POST /api/simulate-paths` — parallel simulation across multiple paths
- Inputs: reserves per pool, trade amount, flashloanFee, gasCost, path hops
- Outputs: `flashloanAmount`, `profitable`, `marketImpactPct`, ranked path results
- Edge cases: insufficient liquidity (cap to % of reserves), negative profit → returns `profitable: false`

5) Opportunity scoring (ML / analytics)
- Module: `defi_analytics_ml` (imported by orchestrator if available)
- Functions used in orchestrator:
  - `ml_engine.score_opportunities(opportunities)` → returns best opportunity
  - `ml_engine.add_trade_result(best_opp, tx_hash)` → feed execution outcome for retraining/analytics
- Inputs: list of opportunities with features (profit, slippage, impact, liquidity, gas)
- Outputs: ranked or scored opportunities, confidence metric
- Edge cases: ML engine missing → orchestrator uses fallback logic or skip

6) Encode & execute arbitrage (private submission)
- Encoding: `arb_request_encoder.encode_arbitrage_request(best_opp)`
- Private submission / gateway: `BillionaireBot_bloxroute_gateway_Version2.send_private_transaction(calldata)` (or other senders)
- Wallet & signing: `backend/wallet-manager.js` and `wallet-manager.py` equivalents manage keys and sign transactions
- Execution: high-priority private mempool or direct provider; flashloan provider covers temporary liquidity
- Outputs: `tx_hash`, on-chain receipts, revert detection
- Edge cases: tx revert, insufficient gas, frontrunning — orchestrator logs and (optionally) retries

7) Post-execution handling
- ML feedback: `ml_engine.add_trade_result(...)`
- Rewards distribution (optional): `BillionaireBot_merkle_sender_tree_Version2` → build/distribute Merkle rewards
- Dashboard updates: frontend receives events (WebSocket) and shows opportunities/trades (`frontend/app.js`)

Observability & safety checks
- Logging at each stage (fetch, detect, simulate, encode, send, result)
- Metric collection: fetch times, TVL, API latencies, success/failure rates
- Safety thresholds (documented in flashloan docs): maxPoolImpact (e.g., 30%), maxSlippage, minProfit

Quick contract (inputs/outputs, error modes)
- Inputs: pool lists, pair reserves, chain info, flashloan fees, gas estimates
- Outputs: opportunity list (route, profit, estimated gas), flashloan amount, tx calldata
- Error modes: missing modules (graceful fallback), network failures, unprofitable paths, execution revert

Files of interest (non-exhaustive)
- `main_quant_hybrid_orchestrator.py` — orchestrator main loop (boot, detection, execution flow)
- `orchestrator_tvl_hyperspeed.py` — TVL fetching and aggregation
- `dex_pool_fetcher.js`, `sdk_pool_loader.js` — initial pool discovery and SDK low-latency loader
- `FLASHLOAN_API_DOCUMENTATION.md`, `FLASHLOAN_COMPLETE_GUIDE.md` — flashloan engine docs and API
- `backend/` — server, blockchain connector, wallet manager, utilities
- `arb_request_encoder.py` / `arb_request_encoder.js` — encodes calldata for execution (referenced)
- `defi_analytics_ml` / `ml_model.py` — ML scoring and analytics

Recommendations and next steps
- Add a compact call graph for `OpportunityDetector` if/when the exact detector module is present in repo (I attempted to open `advanced_opportunity_detection_Version1.py` but it wasn't found).
- Instrument the TL;DR flow with exact function names for encoding and sending (there are references in `main_quant_hybrid_orchestrator.py` but some modules may be optional/missing and are imported dynamically).
- Add an E2E test harness that runs the orchestrator in `--test` mode and asserts that the lifecycle triggers the fetch → detect → encode flow (there are tests referenced in `README_VERIFICATION.md`).

If you want, I can:
- Generate a PNG/SVG from the Mermaid diagram (requires a renderer or external service), or
- Expand the summary into a sequence diagram showing async timing (fetch latency, path sim, flashloan calc, encode, send).
