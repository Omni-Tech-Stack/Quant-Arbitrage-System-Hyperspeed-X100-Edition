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
