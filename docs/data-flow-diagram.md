## Data flow diagram (boot → fetch → detect → score → execute)

This file contains a Mermaid diagram showing the system-level data flow from startup through to flashloan execution and reward distribution.

```mermaid
flowchart LR
  Start([Boot / Start-up]) --> Init[Initialize components]
  Init --> JSFetch[Run JS pool fetcher (dex_pool_fetcher.js)]
  Init --> SDKLoad[Load SDK pool info (sdk_pool_loader.js)]
  Init --> Precheck[Protocol precheck (dex_protocol_precheck)]
  Init --> TVLOrch[TVL Orchestrator (orchestrator_tvl_hyperspeed.py)]

  TVLOrch --> PoolRegistry[Pool Registry Integrator]
  JSFetch --> PoolRegistry
  SDKLoad --> PoolRegistry

  PoolRegistry --> Detector[Opportunity Detector]
  Detector --> RouteSim[Route simulation & path enumerator]
  RouteSim --> FlashloanCalc[Flashloan calc & market-impact (Rust engine via backend API)]
  RouteSim --> SlippageCalc[Multi-hop slippage calc]

  FlashloanCalc --> Scorer[ML / Analytics Scorer (defi_analytics_ml)]
  SlippageCalc --> Scorer

  Scorer --> BestOpp[Select best opportunity]
  BestOpp --> Encoder[Arbitrage request encoder (arb_request_encoder)]
  Encoder --> PrivateSend[Private send / gateway (Bloxroute / BillionaireBot_bloxroute_gateway)]
  PrivateSend --> OnChainExec[On-chain execution (flashloan provider -> DEX swaps)]

  OnChainExec --> TradeResultFeed[Execution result]
  TradeResultFeed --> ML[MLAnalyticsEngine.add_trade_result]
  TradeResultFeed --> Rewards[MerkleRewardDistributor (optional)]

  OnChainExec --> Frontend[Frontend dashboard / WebSocket updates]
  TVLOrch --> Frontend
  Scorer --> Frontend

  subgraph Observability
    Logs[Logging & Metrics]
    Monitoring[Monitoring & Alerts]
  end

  JSFetch --> Logs
  TVLOrch --> Logs
  Detector --> Logs
  OnChainExec --> Logs
  Logs --> Monitoring

  note right of FlashloanCalc: flashloan engine exposes REST API endpoints
  note right of OnChainExec: encodes calldata, signs (wallet-manager), sends via private mempool

```

Quick notes:
- The orchestrator (`main_quant_hybrid_orchestrator.py`) boots, initializes fetchers, runs prechecks, and enters the main event loop.
- TVL collection and pool discovery are handled by `orchestrator_tvl_hyperspeed.py` and protocol-specific fetchers (e.g., `balancer_tvl_fetcher.py`, `uniswapv3_tvl_fetcher.py`).
- Opportunity detection enumerates routes, then calls the flashloan calculation engine (native Rust via backend API) to compute optimal flashloan amounts and market impact.
- Opportunities are ML-scored (`defi_analytics_ml`) to pick the best candidate. The arbitrage request is encoded and dispatched to a private gateway for execution.
- On-chain execution triggers trade-result handling (ML feedback, optional reward distribution via Merkle tree), and all stages report metrics to logging/monitoring and the frontend dashboard.
