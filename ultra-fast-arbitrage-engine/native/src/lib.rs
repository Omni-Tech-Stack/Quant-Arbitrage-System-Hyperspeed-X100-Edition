#![deny(clippy::all)]

mod math;

use napi_derive::napi;

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
pub fn calculate_market_impact(
    reserve_in: f64,
    reserve_out: f64,
    flashloan_amount: f64,
) -> f64 {
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
