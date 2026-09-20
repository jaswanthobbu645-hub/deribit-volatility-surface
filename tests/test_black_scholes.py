import math
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features.black_scholes import norm_cdf, bs_call, bs_put, implied_vol


class TestNormCDF:
    def test_at_zero(self):
        assert abs(norm_cdf(0) - 0.5) < 1e-6
    
    def test_large_positive(self):
        assert norm_cdf(10) > 0.9999
    
    def test_large_negative(self):
        assert norm_cdf(-10) < 0.0001
    
    def test_symmetry(self):
        for x in [-2, -1, 0, 1, 2]:
            assert abs(norm_cdf(x) + norm_cdf(-x) - 1.0) < 1e-6


class TestBlackScholes:
    def test_call_intrinsic_at_expiry(self):
        assert bs_call(100, 90, 0, 0, 0.2) == 10
        assert bs_call(100, 110, 0, 0, 0.2) == 0
    
    def test_put_intrinsic_at_expiry(self):
        assert bs_put(100, 90, 0, 0, 0.2) == 0
        assert bs_put(100, 110, 0, 0, 0.2) == 10
    
    def test_put_call_parity(self):
        S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2
        c = bs_call(S, K, T, r, sigma)
        p = bs_put(S, K, T, r, sigma)
        expected = S - K * math.exp(-r * T)
        assert abs((c - p) - expected) < 1e-4
    
    def test_deep_itm_call(self):
        c = bs_call(200, 100, 0.1, 0.0, 0.2)
        assert c > 95
    
    def test_deep_otm_call(self):
        c = bs_call(50, 200, 0.1, 0.0, 0.2)
        assert c < 0.01


class TestImpliedVol:
    def test_roundtrip_recovery(self):
        S, K, T = 100, 100, 0.25
        true_sigma = 0.5
        price = bs_call(S, K, T, 0, true_sigma)
        recovered = implied_vol(price, S, K, T, 'call')
        assert abs(recovered - true_sigma) < 1e-3
    
    def test_below_intrinsic_returns_none(self):
        assert implied_vol(1.0, 100, 50, 0.1, 'call') is None
    
    def test_zero_price_returns_none(self):
        assert implied_vol(0, 100, 100, 0.1, 'call') is None
    
    def test_negative_T_returns_none(self):
        assert implied_vol(5, 100, 100, -0.1, 'call') is None
