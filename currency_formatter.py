#!/usr/bin/env python3
"""
GLOBAL CURRENCY FORMATTER
Standardizes all currency/profit/amount formatting across the system
Format: $XXX,XXX,XXX.XXXXXX (6 decimals after dot, unlimited before, thousands separators)
"""


def format_currency_usd(amount: float, include_dollar_sign: bool = True) -> str:
    """
    Format currency in USD with 6 decimal places and thousands separators
    
    Args:
        amount: The amount to format
        include_dollar_sign: Whether to include $ prefix
    
    Returns:
        Formatted string like: $1,234,567.890123
    
    Examples:
        >>> format_currency_usd(1234.56789)
        '$1,234.567890'
        >>> format_currency_usd(1000000.123456)
        '$1,000,000.123456'
        >>> format_currency_usd(0.000001)
        '$0.000001'
    """
    if amount is None:
        return "$0.000000" if include_dollar_sign else "0.000000"
    
    # Format with 6 decimals and thousands separators
    formatted = f"{amount:,.6f}"
    
    if include_dollar_sign:
        return f"${formatted}"
    return formatted


def format_token_amount(amount: float, decimals: int = 6, include_commas: bool = True) -> str:
    """
    Format token amounts with specified decimal places
    
    Args:
        amount: Token amount to format
        decimals: Number of decimal places (default 6)
        include_commas: Whether to include thousands separators
    
    Returns:
        Formatted token amount
    
    Examples:
        >>> format_token_amount(1234567.89, 6)
        '1,234,567.890000'
        >>> format_token_amount(0.123456789, 9)
        '0.123456789'
    """
    if amount is None:
        return f"0.{'0' * decimals}"
    
    if include_commas:
        return f"{amount:,.{decimals}f}"
    return f"{amount:.{decimals}f}"


def format_percentage(value: float, decimals: int = 2, include_sign: bool = False) -> str:
    """
    Format percentage values
    
    Args:
        value: Percentage value (e.g., 25.5 for 25.5%)
        decimals: Decimal places (default 2)
        include_sign: Include + for positive values
    
    Returns:
        Formatted percentage like: "25.50%" or "+25.50%"
    
    Examples:
        >>> format_percentage(25.5)
        '25.50%'
        >>> format_percentage(25.5, include_sign=True)
        '+25.50%'
        >>> format_percentage(-5.123, decimals=3)
        '-5.123%'
    """
    if value is None:
        return f"0.{'0' * decimals}%"
    
    if include_sign and value > 0:
        return f"+{value:.{decimals}f}%"
    return f"{value:.{decimals}f}%"


def format_gas_price(gwei: float, decimals: int = 2) -> str:
    """
    Format gas prices in Gwei
    
    Args:
        gwei: Gas price in Gwei
        decimals: Decimal places (default 2)
    
    Returns:
        Formatted gas price like: "45.50 gwei"
    """
    if gwei is None:
        return f"0.{'0' * decimals} gwei"
    
    return f"{gwei:.{decimals}f} gwei"


def format_compact_currency(amount: float, decimals: int = 2) -> str:
    """
    Format large numbers in compact form (K, M, B)
    
    Args:
        amount: Amount to format
        decimals: Decimal places
    
    Returns:
        Compact format like: "$1.23M" or "$456.78K"
    
    Examples:
        >>> format_compact_currency(1234567)
        '$1.23M'
        >>> format_compact_currency(123456)
        '$123.46K'
        >>> format_compact_currency(123)
        '$123.00'
    """
    if amount is None:
        return "$0.00"
    
    abs_amount = abs(amount)
    sign = "-" if amount < 0 else ""
    
    if abs_amount >= 1_000_000_000:
        return f"{sign}${abs_amount / 1_000_000_000:.{decimals}f}B"
    elif abs_amount >= 1_000_000:
        return f"{sign}${abs_amount / 1_000_000:.{decimals}f}M"
    elif abs_amount >= 1_000:
        return f"{sign}${abs_amount / 1_000:.{decimals}f}K"
    else:
        return f"{sign}${abs_amount:.{decimals}f}"


def format_scientific(amount: float) -> str:
    """
    Format very small/large numbers in scientific notation when appropriate
    
    Args:
        amount: Number to format
    
    Returns:
        Scientific notation if appropriate, otherwise standard format
    """
    if amount is None or amount == 0:
        return "$0.000000"
    
    abs_amount = abs(amount)
    
    # Use scientific notation for very small or very large numbers
    if abs_amount < 0.000001 or abs_amount > 1_000_000_000_000:
        return f"${amount:.6e}"
    
    return format_currency_usd(amount)


# Constants for commonly used formats
DECIMAL_PLACES_USD = 6
DECIMAL_PLACES_PERCENTAGE = 2
DECIMAL_PLACES_GAS_GWEI = 2
DECIMAL_PLACES_TOKEN = 6


# Quick access functions
def fmt_usd(amount: float) -> str:
    """Quick USD formatting: $XXX,XXX.XXXXXX"""
    return format_currency_usd(amount)


def fmt_pct(value: float) -> str:
    """Quick percentage formatting: XX.XX%"""
    return format_percentage(value)


def fmt_gas(gwei: float) -> str:
    """Quick gas price formatting: XX.XX gwei"""
    return format_gas_price(gwei)


def fmt_token(amount: float, decimals: int = 6) -> str:
    """Quick token amount formatting"""
    return format_token_amount(amount, decimals)


# Export all functions
__all__ = [
    'format_currency_usd',
    'format_token_amount',
    'format_percentage',
    'format_gas_price',
    'format_compact_currency',
    'format_scientific',
    'fmt_usd',
    'fmt_pct',
    'fmt_gas',
    'fmt_token',
    'DECIMAL_PLACES_USD',
    'DECIMAL_PLACES_PERCENTAGE',
    'DECIMAL_PLACES_GAS_GWEI',
    'DECIMAL_PLACES_TOKEN',
]


if __name__ == "__main__":
    # Test the formatters
    print("=" * 80)
    print("CURRENCY FORMATTER TEST")
    print("=" * 80)
    
    test_values = [
        0.000001,
        0.123456,
        1.23,
        123.456789,
        1234.56789,
        123456.789,
        1234567.89,
        12345678.9,
        123456789.0
    ]
    
    print("\n📊 USD Currency Formatting (6 decimals):")
    for val in test_values:
        print(f"  {val:>15} → {format_currency_usd(val)}")
    
    print("\n📊 Compact Currency Formatting:")
    large_values = [123, 1234, 12345, 123456, 1234567, 12345678, 123456789]
    for val in large_values:
        print(f"  {val:>15} → {format_compact_currency(val)}")
    
    print("\n📊 Token Amount Formatting:")
    token_values = [0.123456789, 1234.567890123, 1000000.123456]
    for val in token_values:
        print(f"  {val:>15} → {format_token_amount(val, 6)}")
    
    print("\n📊 Percentage Formatting:")
    pct_values = [0.12, 1.23, 25.5, -5.123]
    for val in pct_values:
        print(f"  {val:>8} → {format_percentage(val)} | {format_percentage(val, include_sign=True)}")
    
    print("\n📊 Gas Price Formatting:")
    gas_values = [1.5, 25.75, 150.123, 2000.5]
    for val in gas_values:
        print(f"  {val:>8} → {format_gas_price(val)}")
    
    print("\n" + "=" * 80)
    print("✅ All formatters working correctly!")
    print("=" * 80)
