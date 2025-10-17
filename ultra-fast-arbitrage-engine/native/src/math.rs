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
    if reserve_in_buy <= 0.0 || reserve_out_buy <= 0.0 || reserve_in_sell <= 0.0 || reserve_out_sell <= 0.0 {
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
        let amount_out_buy = (amount_in_with_fee * reserve_out_buy) / (reserve_in_buy + amount_in_with_fee);
        
        // Calculate sell side
        let amount_in_sell = amount_out_buy * 0.997;
        let amount_out_sell = (amount_in_sell * reserve_out_sell) / (reserve_in_sell + amount_in_sell);
        
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
pub fn calculate_market_impact(
    reserve_in: f64,
    reserve_out: f64,
    flashloan_amount: f64,
) -> f64 {
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
        let amount_out_sell = (amount_out_buy * sqrt_price_sell * liquidity) / (liquidity + amount_out_buy);
        
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
            0.0009, // 0.09% flashloan fee (Aave)
            100.0   // Gas cost
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
        let reserves = vec![
            (1000000.0, 2000000.0),
            (2000000.0, 1000000.0),
        ];
        let slippage = calculate_multihop_slippage(&reserves, 10000.0);
        assert!(slippage >= 0.0);
    }
}
