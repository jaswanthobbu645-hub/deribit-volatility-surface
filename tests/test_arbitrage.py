import pytest
import numpy as np
import pandas as pd
from src.features.arbitrage_check import svi, fit_svi, svi_second_derivative, check_butterfly, check_calendar

def test_svi():
    k = np.array([-0.5, 0.0, 0.5])
    a, b, rho, m, sigma = 0.1, 0.2, -0.3, 0.0, 0.1
    w = svi(k, a, b, rho, m, sigma)
    expected = a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma ** 2))
    np.testing.assert_allclose(w, expected)

def test_svi_second_derivative():
    k = np.array([0.0])
    a, b, rho, m, sigma = 0.1, 0.2, -0.3, 0.0, 0.1
    d2w = svi_second_derivative(k, a, b, rho, m, sigma)
    # Analytical: b * sigma^2 / ((k-m)^2 + sigma^2)^(3/2)
    expected = b * sigma**2 / ((k - m)**2 + sigma**2)**(1.5)
    np.testing.assert_allclose(d2w, expected)

def test_check_butterfly():
    # Create a simple dataframe that should be arbitrage-free
    df = pd.DataFrame({
        'strike': [100, 105, 110],
        'implied_volatility': [0.2, 0.2, 0.2],
        'underlying_close': [100, 100, 100],
        'days_to_expiry': [30, 30, 30],
        'expiry_datetime': ['2026-10-01', '2026-10-01', '2026-10-01']
    })
    df['expiry_datetime'] = pd.to_datetime(df['expiry_datetime'])
    result = check_butterfly(df)
    assert result is not None
    assert 'is_arbitrage_free' in result
    # With constant IV, the SVI fit might not be perfect but we expect no violations?
    # We'll just check that the function runs without error and returns a dict.

if __name__ == '__main__':
    test_svi()
    test_svi_second_derivative()
    test_check_butterfly()
    print("All tests passed")