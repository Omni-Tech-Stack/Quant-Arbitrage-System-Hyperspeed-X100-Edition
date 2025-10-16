// Core math engine for DEX slippage calculations

/// Compute Uniswap V2 slippage using constant product formula (x * y = k)
pub fn compute_uniswap_v2_slippage(
    reserve_in: f64,
    reserve_out: f64,
    amount_in: f64,
) -> f64 {
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
pub fn compute_uniswap_v3_slippage(
    liquidity: f64,
    sqrt_price: f64,
    amount_in: f64,
) -> f64 {
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
    let constant_product_out = (amount_in_with_fee * balance_out) / (balance_in + amount_in_with_fee);
    
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
}
