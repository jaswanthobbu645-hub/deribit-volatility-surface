import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features.black_scholes import calc_greeks


class TestGreeks:
    def test_call_delta_range(self):
        for K in [50, 100, 150, 200]:
            g = calc_greeks(100, K, 0.25, 0.3, 'call')
            assert 0 <= g['delta'] <= 1
    
    def test_put_delta_range(self):
        for K in [50, 100, 150, 200]:
            g = calc_greeks(100, K, 0.25, 0.3, 'put')
            assert -1 <= g['delta'] <= 0
    
    def test_call_put_parity_delta(self):
        dc = calc_greeks(100, 100, 0.25, 0.3, 'call')['delta']
        dp = calc_greeks(100, 100, 0.25, 0.3, 'put')['delta']
        assert abs((dc - dp) - 1.0) < 1e-6
    
    def test_gamma_positive(self):
        g = calc_greeks(100, 100, 0.25, 0.3, 'call')
        assert g['gamma'] > 0
    
    def test_vega_positive(self):
        g = calc_greeks(100, 100, 0.25, 0.3, 'call')
        assert g['vega'] > 0
    
    def test_theta_negative(self):
        g = calc_greeks(100, 100, 0.25, 0.3, 'call')
        assert g['theta'] < 0
    
    def test_zero_T_returns_zeros(self):
        g = calc_greeks(100, 100, 0, 0.3, 'call')
        assert g['delta'] == 0 and g['gamma'] == 0
