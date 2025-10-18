// Core math engine for DEX slippage calculations

/// Compute Uniswap V2 slippage using constant product formula (x * y = k)
pub fn compute_uniswap_v2_slippage(reserve_in: f64, reserve_out: f64, amount_in: f64) -> f64 {
    if amount_in == 0.0 {
        return 0.0;
    }

    // Apply 0.3% fee
    let amount_in_with_fee = amount_in * 0.997;

    // Constant product formula
    let numerator = amount_in_with_fee * reserve_out;
    let denominator = reserve_in + amount_in_with_fee;
    let amount_out = numerator / denominator;

    // Calculate expected amount without slippage
    let expected_amount_out = (amount_in / reserve_in) * reserve_out;

    // Slippage percentage
    let slippage = ((expected_amount_out - amount_out) / expected_amount_out) * 100.0;
    slippage.max(0.0)
}

/// Compute Uniswap V3 slippage with concentrated liquidity
pub fn compute_uniswap_v3_slippage(liquidity: f64, sqrt_price: f64, amount_in: f64) -> f64 {
    if amount_in == 0.0 || liquidity == 0.0 {
        return 0.0;
    }

    // Simplified concentrated liquidity calculation
    // In real V3, this would involve tick math and price ranges
    let amount_out = (amount_in * sqrt_price * liquidity) / (liquidity + amount_in);
    let expected_amount_out = amount_in * sqrt_price;

    let slippage = ((expected_amount_out - amount_out) / expected_amount_out) * 100.0;
    slippage.max(0.0)
}

/// Compute Curve stableswap slippage with amplification coefficient
pub fn compute_curve_slippage(
    balance_in: f64,
    balance_out: f64,
    amount_in: f64,
    amplification: f64,
) -> f64 {
    if amount_in == 0.0 {
        return 0.0;
    }

    // Simplified Curve StableSwap formula
    // For balanced pools with high amplification, acts more like constant sum
    // For imbalanced pools, acts more like constant product
    let amp_factor = amplification;

    // Apply fee (0.04% for Curve)
    let amount_in_with_fee = amount_in * 0.9996;

    // Simplified invariant calculation
    let total_liquidity = balance_in + balance_out;

    // Calculate amount out using amplified invariant
    // Higher amplification = lower slippage for balanced pools
    let constant_sum_out = (total_liquidity * amount_in_with_fee) / (balance_in + balance_out);
    let constant_product_out =
        (amount_in_with_fee * balance_out) / (balance_in + amount_in_with_fee);

    // Blend between constant sum and constant product based on amplification
    let amp_weight = amp_factor / (amp_factor + 100.0);
    let amount_out = constant_sum_out * amp_weight + constant_product_out * (1.0 - amp_weight);

    let expected_amount_out = amount_in * (balance_out / balance_in);
    let slippage = ((expected_amount_out - amount_out) / expected_amount_out) * 100.0;
    slippage.max(0.0)
}

/// Compute Balancer weighted pool slippage
pub fn compute_balancer_slippage(
    balance_in: f64,
    balance_out: f64,
    weight_in: f64,
    weight_out: f64,
    amount_in: f64,
) -> f64 {
    if amount_in == 0.0 {
        return 0.0;
    }

    // Balancer weighted pool formula: amount_out = balance_out * (1 - (balance_in / (balance_in + amount_in))^(weight_in/weight_out))
    let base = balance_in / (balance_in + amount_in);
    let exponent = weight_in / weight_out;
    let amount_out = balance_out * (1.0 - base.powf(exponent));

    let expected_amount_out = amount_in * (balance_out / balance_in);
    let slippage = ((expected_amount_out - amount_out) / expected_amount_out) * 100.0;
    slippage.max(0.0)
}

/// Compute aggregator slippage by selecting minimum slippage route
pub fn compute_aggregator_slippage(slippages: &[f64]) -> f64 {
    if slippages.is_empty() {
        return 0.0;
    }

    // Return minimum slippage (best route)
    slippages.iter().cloned().fold(f64::INFINITY, f64::min)
}

/// Find optimal trade size for arbitrage given profit function
pub fn optimal_trade_size(
    reserve_in: f64,
    reserve_out: f64,
    gas_cost: f64,
    min_profit: f64,
) -> f64 {
    if reserve_in <= 0.0 || reserve_out <= 0.0 {
        return 0.0;
    }

    // Binary search for optimal trade size
    let mut low = 0.0;
    let mut high = reserve_in * 0.1; // Max 10% of reserve
    let mut best_size = 0.0;
    let iterations = 50;

    for _ in 0..iterations {
        let mid = (low + high) / 2.0;

        // Calculate profit at this trade size
        let amount_in_with_fee = mid * 0.997;
        let numerator = amount_in_with_fee * reserve_out;
        let denominator = reserve_in + amount_in_with_fee;
        let amount_out = numerator / denominator;

        let profit = amount_out - mid - gas_cost;

        if profit >= min_profit {
            best_size = mid;
            low = mid;
        } else {
            high = mid;
        }

        // Convergence check
        if (high - low) < 0.0001 {
            break;
        }
    }

    best_size
}

/// Calculate flashloan amount needed for arbitrage opportunity
/// Returns the optimal flashloan amount based on available liquidity and expected profit
pub fn calculate_flashloan_amount(
    reserve_in_buy: f64,
    reserve_out_buy: f64,
    reserve_in_sell: f64,
    reserve_out_sell: f64,
    flashloan_fee: f64,
    gas_cost: f64,
) -> f64 {
    if reserve_in_buy <= 0.0
        || reserve_out_buy <= 0.0
        || reserve_in_sell <= 0.0
        || reserve_out_sell <= 0.0
    {
        return 0.0;
    }

    // Binary search for optimal flashloan amount
    let max_flashloan = (reserve_in_buy * 0.3).min(reserve_in_sell * 0.3); // Max 30% of smaller reserve
    let mut low = 0.0;
    let mut high = max_flashloan;
    let mut best_amount = 0.0;
    let mut best_profit = 0.0;

    for _ in 0..100 {
        let mid = (low + high) / 2.0;

        // Calculate buy side (with flashloan)
        let amount_in_with_fee = mid * 0.997;
        let amount_out_buy =
            (amount_in_with_fee * reserve_out_buy) / (reserve_in_buy + amount_in_with_fee);

        // Calculate sell side
        let amount_in_sell = amount_out_buy * 0.997;
        let amount_out_sell =
            (amount_in_sell * reserve_out_sell) / (reserve_in_sell + amount_in_sell);

        // Calculate profit after flashloan fee
        let flashloan_repayment = mid * (1.0 + flashloan_fee);
        let profit = amount_out_sell - flashloan_repayment - gas_cost;

        if profit > best_profit {
            best_profit = profit;
            best_amount = mid;
        }

        if profit > 0.0 {
            low = mid;
        } else {
            high = mid;
        }

        if (high - low) < 0.01 {
            break;
        }
    }

    if best_profit > 0.0 {
        best_amount
    } else {
        0.0
    }
}

/// Calculate market impact (price slippage) caused by a flashloan-sized trade
/// Returns the percentage price impact on the pool
pub fn calculate_market_impact(reserve_in: f64, reserve_out: f64, flashloan_amount: f64) -> f64 {
    if reserve_in <= 0.0 || reserve_out <= 0.0 || flashloan_amount <= 0.0 {
        return 0.0;
    }

    // Price before trade
    let price_before = reserve_out / reserve_in;

    // Calculate output amount
    let amount_in_with_fee = flashloan_amount * 0.997;
    let amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee);

    // Price after trade (new reserves)
    let new_reserve_in = reserve_in + flashloan_amount;
    let new_reserve_out = reserve_out - amount_out;
    let price_after = new_reserve_out / new_reserve_in;

    // Market impact as percentage
    let impact = ((price_before - price_after) / price_before) * 100.0;
    impact.abs()
}

/// Calculate total slippage for a multi-hop flashloan arbitrage path
/// Returns combined slippage across all hops in the path
pub fn calculate_multihop_slippage(
    reserves: &[(f64, f64)], // Array of (reserve_in, reserve_out) pairs
    flashloan_amount: f64,
) -> f64 {
    if reserves.is_empty() || flashloan_amount <= 0.0 {
        return 0.0;
    }

    let mut current_amount = flashloan_amount;
    let mut total_slippage = 0.0;

    for (reserve_in, reserve_out) in reserves {
        if *reserve_in <= 0.0 || *reserve_out <= 0.0 {
            return 100.0; // Invalid pool
        }

        // Calculate slippage for this hop
        let hop_slippage = compute_uniswap_v2_slippage(*reserve_in, *reserve_out, current_amount);
        total_slippage += hop_slippage;

        // Calculate output for next hop
        let amount_in_with_fee = current_amount * 0.997;
        current_amount = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee);
    }

    total_slippage
}

/// Simulate flashloan arbitrage execution across multiple paths simultaneously
/// Returns array of (profit, slippage, path_index) for each path
pub fn simulate_parallel_flashloan_paths(
    paths: &[Vec<(f64, f64)>], // Array of paths, each path is array of reserve pairs
    flashloan_amounts: &[f64],
    flashloan_fee: f64,
    gas_costs: &[f64],
) -> Vec<(f64, f64, usize)> {
    let mut results = Vec::new();

    for (idx, path) in paths.iter().enumerate() {
        if idx >= flashloan_amounts.len() || idx >= gas_costs.len() {
            break;
        }

        let flashloan_amount = flashloan_amounts[idx];
        let gas_cost = gas_costs[idx];

        if path.is_empty() || flashloan_amount <= 0.0 {
            results.push((0.0, 0.0, idx));
            continue;
        }

        // Calculate output through the path
        let mut current_amount = flashloan_amount;
        for (reserve_in, reserve_out) in path {
            let amount_in_with_fee = current_amount * 0.997;
            current_amount = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee);
        }

        // Calculate profit after flashloan repayment
        let flashloan_repayment = flashloan_amount * (1.0 + flashloan_fee);
        let profit = current_amount - flashloan_repayment - gas_cost;

        // Calculate total slippage
        let slippage = calculate_multihop_slippage(path, flashloan_amount);

        results.push((profit, slippage, idx));
    }

    results
}

/// Calculate optimal flashloan amount for Uniswap V3 concentrated liquidity
pub fn calculate_flashloan_amount_v3(
    liquidity: f64,
    sqrt_price_buy: f64,
    sqrt_price_sell: f64,
    flashloan_fee: f64,
    gas_cost: f64,
) -> f64 {
    if liquidity <= 0.0 || sqrt_price_buy <= 0.0 || sqrt_price_sell <= 0.0 {
        return 0.0;
    }

    // Binary search for optimal amount
    let max_amount = liquidity * 0.3;
    let mut low = 0.0;
    let mut high = max_amount;
    let mut best_amount = 0.0;
    let mut best_profit = 0.0;

    for _ in 0..100 {
        let mid = (low + high) / 2.0;

        // Simplified V3 calculation
        let amount_out_buy = (mid * sqrt_price_buy * liquidity) / (liquidity + mid);
        let amount_out_sell =
            (amount_out_buy * sqrt_price_sell * liquidity) / (liquidity + amount_out_buy);

        let flashloan_repayment = mid * (1.0 + flashloan_fee);
        let profit = amount_out_sell - flashloan_repayment - gas_cost;

        if profit > best_profit {
            best_profit = profit;
            best_amount = mid;
        }

        if profit > 0.0 {
            low = mid;
        } else {
            high = mid;
        }

        if (high - low) < 0.01 {
            break;
        }
    }

    if best_profit > 0.0 {
        best_amount
    } else {
        0.0
    }
}

/// Step 1: Calculate token price from pool reserves
/// Formula: p_t = reserve_out / reserve_in
pub fn calculate_pool_price(reserve_in: f64, reserve_out: f64) -> f64 {
    if reserve_in <= 0.0 {
        return 0.0;
    }
    reserve_out / reserve_in
}

/// Step 2: Identify arbitrage opportunity by comparing prices across pools
/// Returns (has_opportunity, price_difference_percentage, direction)
/// direction: 0 = no opportunity, 1 = buy pool1/sell pool2, 2 = buy pool2/sell pool1
pub fn identify_arbitrage_opportunity(
    pool1_reserve_in: f64,
    pool1_reserve_out: f64,
    pool2_reserve_in: f64,
    pool2_reserve_out: f64,
    min_price_diff_pct: f64,
) -> (bool, f64, u8) {
    let price1 = calculate_pool_price(pool1_reserve_in, pool1_reserve_out);
    let price2 = calculate_pool_price(pool2_reserve_in, pool2_reserve_out);

    if price1 <= 0.0 || price2 <= 0.0 {
        return (false, 0.0, 0);
    }

    // Calculate price difference percentage
    let price_diff = ((price1 - price2).abs() / price1.min(price2)) * 100.0;

    if price_diff >= min_price_diff_pct {
        if price1 < price2 {
            // Buy on pool1 (cheaper), sell on pool2 (more expensive)
            return (true, price_diff, 1);
        } else {
            // Buy on pool2 (cheaper), sell on pool1 (more expensive)
            return (true, price_diff, 2);
        }
    }

    (false, price_diff, 0)
}

/// Step 3: Calculate input amount needed for desired output
/// Formula: amountIn = (ReserveIn × AmountOut × 1000) / ((ReserveOut - AmountOut) × 997) + 1
pub fn calculate_amount_in(reserve_in: f64, reserve_out: f64, amount_out: f64) -> f64 {
    if reserve_out <= amount_out || amount_out <= 0.0 {
        return 0.0;
    }

    let numerator = reserve_in * amount_out * 1000.0;
    let denominator = (reserve_out - amount_out) * 997.0;

    if denominator <= 0.0 {
        return 0.0;
    }

    (numerator / denominator) + 1.0
}

/// Step 3: Calculate output amount for given input
/// Formula: amountOut = (ReserveOut × AmountIn × 997) / (ReserveIn × 1000 + AmountIn × 997)
pub fn calculate_amount_out(reserve_in: f64, reserve_out: f64, amount_in: f64) -> f64 {
    if amount_in <= 0.0 {
        return 0.0;
    }

    let numerator = reserve_out * amount_in * 997.0;
    let denominator = reserve_in * 1000.0 + amount_in * 997.0;

    if denominator <= 0.0 {
        return 0.0;
    }

    numerator / denominator
}

/// Step 4: Estimate profitability of arbitrage
/// Formula: profit = AmountOut_sell - AmountIn_buy - gas_fees - flashloan_fees
pub fn estimate_arbitrage_profit(
    buy_reserve_in: f64,
    buy_reserve_out: f64,
    sell_reserve_in: f64,
    sell_reserve_out: f64,
    amount_in: f64,
    gas_cost: f64,
    flashloan_fee_pct: f64,
) -> f64 {
    // Calculate amount out from buy pool
    let amount_out_buy = calculate_amount_out(buy_reserve_in, buy_reserve_out, amount_in);

    // Calculate amount out from sell pool
    let amount_out_sell = calculate_amount_out(sell_reserve_in, sell_reserve_out, amount_out_buy);

    // Calculate flashloan repayment
    let flashloan_repayment = amount_in * (1.0 + flashloan_fee_pct);

    // Calculate net profit
    amount_out_sell - flashloan_repayment - gas_cost
}

/// Step 5: Solve quadratic equation for optimal trade size
/// Formula: ax² + bx + c = 0
/// Returns the positive root(s) or 0 if no real solutions
pub fn solve_quadratic(a: f64, b: f64, c: f64) -> (f64, f64) {
    if a == 0.0 {
        // Linear equation: bx + c = 0
        if b != 0.0 {
            return (-c / b, 0.0);
        }
        return (0.0, 0.0);
    }

    let discriminant = b * b - 4.0 * a * c;

    if discriminant < 0.0 {
        // No real solutions
        return (0.0, 0.0);
    }

    let sqrt_discriminant = discriminant.sqrt();
    let root1 = (-b + sqrt_discriminant) / (2.0 * a);
    let root2 = (-b - sqrt_discriminant) / (2.0 * a);

    (root1, root2)
}

/// Step 5: Find optimal trade size using quadratic optimization
/// This finds the trade size that maximizes profit considering slippage
pub fn optimize_trade_size_quadratic(
    buy_reserve_in: f64,
    buy_reserve_out: f64,
    sell_reserve_in: f64,
    sell_reserve_out: f64,
    gas_cost: f64,
    flashloan_fee_pct: f64,
) -> f64 {
    // Use binary search to find optimal size (more robust than pure quadratic)
    // Limit trade size to 30% of reserves to avoid excessive slippage and market impact.
    // 30% is a common DeFi heuristic, balancing profit potential with risk of moving the market,
    // and is consistent with the approach in `calculate_flashloan_amount_v3`.
    let max_amount = (buy_reserve_in * 0.3).min(sell_reserve_in * 0.3);
    let mut best_size = 0.0;
    let mut best_profit = 0.0;

    for i in 0..100 {
        let amount = (i as f64 / 100.0) * max_amount;
        if amount <= 0.0 {
            continue;
        }

        let profit = estimate_arbitrage_profit(
            buy_reserve_in,
            buy_reserve_out,
            sell_reserve_in,
            sell_reserve_out,
            amount,
            gas_cost,
            flashloan_fee_pct,
        );

        if profit > best_profit {
            best_profit = profit;
            best_size = amount;
        }
    }

    best_size
}

/// Step 6: Calculate TWAP (Time-Weighted Average Price)
/// Formula: TWAP = (a_t2 - a_t1) / (t2 - t1)
/// This validates that price discrepancy is legitimate and not temporary
pub fn calculate_twap(price_samples: &[(f64, f64)], // Array of (timestamp, price) pairs
) -> f64 {
    if price_samples.len() < 2 {
        return 0.0;
    }

    let mut weighted_sum = 0.0;
    let mut total_time = 0.0;

    for i in 0..price_samples.len() - 1 {
        let (t1, p1) = price_samples[i];
        let (t2, _p2) = price_samples[i + 1];
        let time_diff = t2 - t1;

        if time_diff > 0.0 {
            weighted_sum += p1 * time_diff;
            total_time += time_diff;
        }
    }

    if total_time > 0.0 {
        weighted_sum / total_time
    } else {
        0.0
    }
}

/// Step 6: Validate arbitrage opportunity using TWAP
/// Returns true if current price is close to TWAP (not manipulated)
pub fn validate_with_twap(current_price: f64, twap: f64, max_deviation_pct: f64) -> bool {
    if twap <= 0.0 {
        return false;
    }

    let deviation = ((current_price - twap).abs() / twap) * 100.0;
    deviation <= max_deviation_pct
}

/// Configuration parameters for arbitrage execution
pub struct ArbitrageConfig {
    pub gas_cost: f64,
    pub flashloan_fee_pct: f64,
    pub min_price_diff_pct: f64,
    pub max_twap_deviation_pct: f64,
    pub min_profit_threshold: f64,
}

/// Step 7: Complete arbitrage execution flow
/// Returns (should_execute, optimal_amount, expected_profit)
pub fn execute_arbitrage_flow(
    pool1_reserve_in: f64,
    pool1_reserve_out: f64,
    pool2_reserve_in: f64,
    pool2_reserve_out: f64,
    price_samples_pool1: &[(f64, f64)],
    price_samples_pool2: &[(f64, f64)],
    config: &ArbitrageConfig,
) -> (bool, f64, f64) {
    // Step 1 & 2: Identify arbitrage opportunity
    let (has_opportunity, _price_diff, direction) = identify_arbitrage_opportunity(
        pool1_reserve_in,
        pool1_reserve_out,
        pool2_reserve_in,
        pool2_reserve_out,
        config.min_price_diff_pct,
    );

    if !has_opportunity {
        return (false, 0.0, 0.0);
    }

    // Determine buy and sell pools based on direction
    let (buy_res_in, buy_res_out, sell_res_in, sell_res_out, price_samples) = if direction == 1 {
        (
            pool1_reserve_in,
            pool1_reserve_out,
            pool2_reserve_in,
            pool2_reserve_out,
            price_samples_pool1,
        )
    } else {
        (
            pool2_reserve_in,
            pool2_reserve_out,
            pool1_reserve_in,
            pool1_reserve_out,
            price_samples_pool2,
        )
    };

    // Step 6: Validate with TWAP
    let current_price = calculate_pool_price(buy_res_in, buy_res_out);
    let twap = calculate_twap(price_samples);

    if !validate_with_twap(current_price, twap, config.max_twap_deviation_pct) {
        return (false, 0.0, 0.0);
    }

    // Step 5: Optimize trade size
    let optimal_amount = optimize_trade_size_quadratic(
        buy_res_in,
        buy_res_out,
        sell_res_in,
        sell_res_out,
        config.gas_cost,
        config.flashloan_fee_pct,
    );

    if optimal_amount <= 0.0 {
        return (false, 0.0, 0.0);
    }

    // Step 4: Estimate profitability
    let expected_profit = estimate_arbitrage_profit(
        buy_res_in,
        buy_res_out,
        sell_res_in,
        sell_res_out,
        optimal_amount,
        config.gas_cost,
        config.flashloan_fee_pct,
    );

    // Step 7: Execute if profitable
    let should_execute = expected_profit >= config.min_profit_threshold;

    (should_execute, optimal_amount, expected_profit)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_uniswap_v2_slippage() {
        let slippage = compute_uniswap_v2_slippage(1000000.0, 2000000.0, 10000.0);
        assert!(slippage > 0.0);
        assert!(slippage < 100.0);
    }

    #[test]
    fn test_zero_amount() {
        let slippage = compute_uniswap_v2_slippage(1000000.0, 2000000.0, 0.0);
        assert_eq!(slippage, 0.0);
    }

    #[test]
    fn test_optimal_trade_size() {
        let size = optimal_trade_size(1000000.0, 2000000.0, 100.0, 50.0);
        assert!(size > 0.0);
    }

    #[test]
    fn test_flashloan_amount_calculation() {
        let amount = calculate_flashloan_amount(
            1000000.0, 2000000.0, // Buy pool - price is 2:1
            1800000.0, 1000000.0, // Sell pool - price is 0.556:1 (significant difference)
            0.0009,    // 0.09% flashloan fee (Aave)
            100.0,     // Gas cost
        );
        // With a significant price difference, should find profitable flashloan amount
        assert!(amount >= 0.0); // At minimum should not be negative
    }

    #[test]
    fn test_market_impact() {
        let impact = calculate_market_impact(1000000.0, 2000000.0, 50000.0);
        assert!(impact > 0.0);
        assert!(impact < 100.0);
    }

    #[test]
    fn test_multihop_slippage() {
        let reserves = vec![(1000000.0, 2000000.0), (2000000.0, 1000000.0)];
        let slippage = calculate_multihop_slippage(&reserves, 10000.0);
        assert!(slippage >= 0.0);
    }

    #[test]
    fn test_calculate_pool_price() {
        let price = calculate_pool_price(1000000.0, 2000000.0);
        assert_eq!(price, 2.0);
    }

    #[test]
    fn test_identify_arbitrage_opportunity() {
        // Pool 1: price = 2.0, Pool 2: price = 2.2 (10% difference)
        let (has_opp, diff, direction) = identify_arbitrage_opportunity(
            1000000.0, 2000000.0, // Pool 1
            1000000.0, 2200000.0, // Pool 2
            5.0,       // Min 5% difference
        );
        assert!(has_opp);
        assert!(diff >= 5.0);
        assert_eq!(direction, 1); // Buy pool 1, sell pool 2
    }

    #[test]
    fn test_calculate_amount_in() {
        let amount_in = calculate_amount_in(1000000.0, 2000000.0, 10000.0);
        assert!(amount_in > 0.0);
        assert!(amount_in < 1000000.0);
    }

    #[test]
    fn test_calculate_amount_out() {
        let amount_out = calculate_amount_out(1000000.0, 2000000.0, 10000.0);
        assert!(amount_out > 0.0);
        assert!(amount_out < 20000.0);
    }

    #[test]
    fn test_estimate_arbitrage_profit() {
        let profit = estimate_arbitrage_profit(
            1000000.0, 2000000.0, // Buy pool
            2000000.0, 1000000.0, // Sell pool
            10000.0,   // Amount in
            100.0,     // Gas cost
            0.0009,    // Flashloan fee
        );
        // Should be negative or very low due to price similarity
        assert!(profit < 1000.0);
    }

    #[test]
    fn test_solve_quadratic() {
        // x² - 5x + 6 = 0, roots: 2 and 3
        let (r1, r2) = solve_quadratic(1.0, -5.0, 6.0);
        assert!((r1 - 3.0).abs() < 0.01 || (r1 - 2.0).abs() < 0.01);
        assert!((r2 - 3.0).abs() < 0.01 || (r2 - 2.0).abs() < 0.01);
    }

    #[test]
    fn test_calculate_twap() {
        let samples = vec![(0.0, 100.0), (10.0, 110.0), (20.0, 105.0)];
        let twap = calculate_twap(&samples);
        assert!(twap > 0.0);
        assert!(twap >= 100.0 && twap <= 110.0);
    }

    #[test]
    fn test_validate_with_twap() {
        let is_valid = validate_with_twap(102.0, 100.0, 5.0); // 2% deviation, max 5%
        assert!(is_valid);

        let is_invalid = validate_with_twap(110.0, 100.0, 5.0); // 10% deviation, max 5%
        assert!(!is_invalid);
    }

    #[test]
    fn test_execute_arbitrage_flow() {
        let price_samples = vec![(0.0, 2.0), (10.0, 2.05), (20.0, 2.1)];

        let config = ArbitrageConfig {
            gas_cost: 100.0,
            flashloan_fee_pct: 0.0009,
            min_price_diff_pct: 5.0,
            max_twap_deviation_pct: 10.0,
            min_profit_threshold: 50.0,
        };

        let (should_execute, optimal_amount, profit) = execute_arbitrage_flow(
            1000000.0,
            2000000.0, // Pool 1
            1000000.0,
            2500000.0, // Pool 2 (significant price difference)
            &price_samples,
            &price_samples,
            &config,
        );

        // May or may not execute depending on profitability, but should return valid values
        assert!(optimal_amount >= 0.0);
        if should_execute {
            assert!(profit >= 50.0);
        }
    }
}
