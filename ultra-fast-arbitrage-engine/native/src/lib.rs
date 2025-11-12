#![deny(clippy::all)]

mod math;

use napi_derive::napi;

/// Configuration parameters for arbitrage execution
#[napi(object)]
pub struct ArbitrageConfig {
    pub gas_cost: f64,
    pub flashloan_fee_pct: f64,
    pub min_price_diff_pct: f64,
    pub max_twap_deviation_pct: f64,
    pub min_profit_threshold: f64,
}

#[napi]
pub fn compute_uniswap_v2_slippage(reserve_in: f64, reserve_out: f64, amount_in: f64) -> f64 {
    math::compute_uniswap_v2_slippage(reserve_in, reserve_out, amount_in)
}

#[napi]
pub fn compute_uniswap_v3_slippage(liquidity: f64, sqrt_price: f64, amount_in: f64) -> f64 {
    math::compute_uniswap_v3_slippage(liquidity, sqrt_price, amount_in)
}

#[napi]
pub fn compute_curve_slippage(
    balance_in: f64,
    balance_out: f64,
    amount_in: f64,
    amplification: f64,
) -> f64 {
    math::compute_curve_slippage(balance_in, balance_out, amount_in, amplification)
}

#[napi]
pub fn compute_balancer_slippage(
    balance_in: f64,
    balance_out: f64,
    weight_in: f64,
    weight_out: f64,
    amount_in: f64,
) -> f64 {
    math::compute_balancer_slippage(balance_in, balance_out, weight_in, weight_out, amount_in)
}

#[napi]
pub fn compute_aggregator_slippage(slippages: Vec<f64>) -> f64 {
    math::compute_aggregator_slippage(&slippages)
}

#[napi]
pub fn optimal_trade_size(
    reserve_in: f64,
    reserve_out: f64,
    gas_cost: f64,
    min_profit: f64,
) -> f64 {
    math::optimal_trade_size(reserve_in, reserve_out, gas_cost, min_profit)
}

#[napi]
pub fn calculate_flashloan_amount(
    reserve_in_buy: f64,
    reserve_out_buy: f64,
    reserve_in_sell: f64,
    reserve_out_sell: f64,
    flashloan_fee: f64,
    gas_cost: f64,
) -> f64 {
    math::calculate_flashloan_amount(
        reserve_in_buy,
        reserve_out_buy,
        reserve_in_sell,
        reserve_out_sell,
        flashloan_fee,
        gas_cost,
    )
}

#[napi]
pub fn calculate_market_impact(reserve_in: f64, reserve_out: f64, flashloan_amount: f64) -> f64 {
    math::calculate_market_impact(reserve_in, reserve_out, flashloan_amount)
}

#[napi]
pub fn calculate_multihop_slippage(reserves: Vec<Vec<f64>>, flashloan_amount: f64) -> f64 {
    let reserve_pairs: Vec<(f64, f64)> = reserves
        .iter()
        .filter_map(|r| {
            if r.len() >= 2 {
                Some((r[0], r[1]))
            } else {
                None
            }
        })
        .collect();

    math::calculate_multihop_slippage(&reserve_pairs, flashloan_amount)
}

#[napi]
pub fn simulate_parallel_flashloan_paths(
    paths: Vec<Vec<Vec<f64>>>,
    flashloan_amounts: Vec<f64>,
    flashloan_fee: f64,
    gas_costs: Vec<f64>,
) -> Vec<Vec<f64>> {
    let path_tuples: Vec<Vec<(f64, f64)>> = paths
        .iter()
        .map(|path| {
            path.iter()
                .filter_map(|r| {
                    if r.len() >= 2 {
                        Some((r[0], r[1]))
                    } else {
                        None
                    }
                })
                .collect()
        })
        .collect();

    let results = math::simulate_parallel_flashloan_paths(
        &path_tuples,
        &flashloan_amounts,
        flashloan_fee,
        &gas_costs,
    );

    results
        .iter()
        .map(|(profit, slippage, idx)| vec![*profit, *slippage, *idx as f64])
        .collect()
}

#[napi]
pub fn calculate_flashloan_amount_v3(
    liquidity: f64,
    sqrt_price_buy: f64,
    sqrt_price_sell: f64,
    flashloan_fee: f64,
    gas_cost: f64,
) -> f64 {
    math::calculate_flashloan_amount_v3(
        liquidity,
        sqrt_price_buy,
        sqrt_price_sell,
        flashloan_fee,
        gas_cost,
    )
}

// New arbitrage flow functions

#[napi]
pub fn calculate_pool_price(reserve_in: f64, reserve_out: f64) -> f64 {
    math::calculate_pool_price(reserve_in, reserve_out)
}

#[napi]
pub fn identify_arbitrage_opportunity(
    pool1_reserve_in: f64,
    pool1_reserve_out: f64,
    pool2_reserve_in: f64,
    pool2_reserve_out: f64,
    min_price_diff_pct: f64,
) -> Vec<f64> {
    let (has_opportunity, price_diff, direction) = math::identify_arbitrage_opportunity(
        pool1_reserve_in,
        pool1_reserve_out,
        pool2_reserve_in,
        pool2_reserve_out,
        min_price_diff_pct,
    );

    vec![
        if has_opportunity { 1.0 } else { 0.0 },
        price_diff,
        direction as f64,
    ]
}

#[napi]
pub fn calculate_amount_in(reserve_in: f64, reserve_out: f64, amount_out: f64) -> f64 {
    math::calculate_amount_in(reserve_in, reserve_out, amount_out)
}

#[napi]
pub fn calculate_amount_out(reserve_in: f64, reserve_out: f64, amount_in: f64) -> f64 {
    math::calculate_amount_out(reserve_in, reserve_out, amount_in)
}

#[napi]
pub fn estimate_arbitrage_profit(
    buy_reserve_in: f64,
    buy_reserve_out: f64,
    sell_reserve_in: f64,
    sell_reserve_out: f64,
    amount_in: f64,
    gas_cost: f64,
    flashloan_fee_pct: f64,
) -> f64 {
    math::estimate_arbitrage_profit(
        buy_reserve_in,
        buy_reserve_out,
        sell_reserve_in,
        sell_reserve_out,
        amount_in,
        gas_cost,
        flashloan_fee_pct,
    )
}

#[napi]
pub fn solve_quadratic(a: f64, b: f64, c: f64) -> Vec<f64> {
    let (root1, root2) = math::solve_quadratic(a, b, c);
    vec![root1, root2]
}

#[napi]
pub fn optimize_trade_size_quadratic(
    buy_reserve_in: f64,
    buy_reserve_out: f64,
    sell_reserve_in: f64,
    sell_reserve_out: f64,
    gas_cost: f64,
    flashloan_fee_pct: f64,
) -> f64 {
    math::optimize_trade_size_quadratic(
        buy_reserve_in,
        buy_reserve_out,
        sell_reserve_in,
        sell_reserve_out,
        gas_cost,
        flashloan_fee_pct,
    )
}

#[napi]
pub fn calculate_twap(price_samples: Vec<Vec<f64>>) -> f64 {
    let samples: Vec<(f64, f64)> = price_samples
        .iter()
        .filter_map(|s| {
            if s.len() >= 2 {
                Some((s[0], s[1]))
            } else {
                None
            }
        })
        .collect();

    math::calculate_twap(&samples)
}

#[napi]
pub fn validate_with_twap(current_price: f64, twap: f64, max_deviation_pct: f64) -> bool {
    math::validate_with_twap(current_price, twap, max_deviation_pct)
}

#[napi]
pub fn execute_arbitrage_flow(
    pool1_reserve_in: f64,
    pool1_reserve_out: f64,
    pool2_reserve_in: f64,
    pool2_reserve_out: f64,
    price_samples_pool1: Vec<Vec<f64>>,
    price_samples_pool2: Vec<Vec<f64>>,
    config: ArbitrageConfig,
) -> Vec<f64> {
    let samples1: Vec<(f64, f64)> = price_samples_pool1
        .iter()
        .filter_map(|s| {
            if s.len() >= 2 {
                Some((s[0], s[1]))
            } else {
                None
            }
        })
        .collect();

    let samples2: Vec<(f64, f64)> = price_samples_pool2
        .iter()
        .filter_map(|s| {
            if s.len() >= 2 {
                Some((s[0], s[1]))
            } else {
                None
            }
        })
        .collect();

    let math_config = math::ArbitrageConfig {
        gas_cost: config.gas_cost,
        flashloan_fee_pct: config.flashloan_fee_pct,
        min_price_diff_pct: config.min_price_diff_pct,
        max_twap_deviation_pct: config.max_twap_deviation_pct,
        min_profit_threshold: config.min_profit_threshold,
    };

    let (should_execute, optimal_amount, expected_profit) = math::execute_arbitrage_flow(
        pool1_reserve_in,
        pool1_reserve_out,
        pool2_reserve_in,
        pool2_reserve_out,
        &samples1,
        &samples2,
        &math_config,
    );

    vec![
        if should_execute { 1.0 } else { 0.0 },
        optimal_amount,
        expected_profit,
    ]
}

#[napi]
pub fn batch_evaluate_opportunities(
    opportunities: Vec<Vec<f64>>,  // Each inner vec: [pool1_res_in, pool1_res_out, pool2_res_in, pool2_res_out]
    config: ArbitrageConfig,
) -> Vec<Vec<f64>> {
    let opp_tuples: Vec<(f64, f64, f64, f64)> = opportunities
        .iter()
        .filter_map(|opp| {
            if opp.len() >= 4 {
                Some((opp[0], opp[1], opp[2], opp[3]))
            } else {
                None
            }
        })
        .collect();

    let math_config = math::ArbitrageConfig {
        gas_cost: config.gas_cost,
        flashloan_fee_pct: config.flashloan_fee_pct,
        min_price_diff_pct: config.min_price_diff_pct,
        max_twap_deviation_pct: config.max_twap_deviation_pct,
        min_profit_threshold: config.min_profit_threshold,
    };

    let results = math::batch_evaluate_opportunities(&opp_tuples, &math_config);

    results
        .iter()
        .map(|(should_execute, optimal_amount, profit)| {
            vec![
                if *should_execute { 1.0 } else { 0.0 },
                *optimal_amount,
                *profit,
            ]
        })
        .collect()
}
