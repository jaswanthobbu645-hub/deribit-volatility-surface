import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features.svi import svi_total_variance, fit_svi


class TestSVI:
    def test_svi_recovers_known_params(self):
        """Fit SVI to data generated from known params; recover within tolerance."""
        true_params = dict(a=0.04, b=0.4, rho=-0.3, m=0.0, sigma=0.2)
        k = np.linspace(-0.5, 0.5, 25)
        w_true = svi_total_variance(k, **true_params)
        
        fitted = fit_svi(k, w_true)
        
        assert fitted is not None, "SVI fit failed to converge"
        for key in true_params:
            assert abs(fitted[key] - true_params[key]) < 0.05, (
                f"{key}: fitted={fitted[key]:.4f} true={true_params[key]:.4f}"
            )
    
    def test_svi_no_negative_variance(self):
        """SVI total variance must always be non-negative."""
        true_params = dict(a=0.04, b=0.4, rho=-0.3, m=0.0, sigma=0.2)
        k = np.linspace(-0.6, 0.6, 50)
        w = svi_total_variance(k, **true_params)
        assert (w >= 0).all()
    
    def test_svi_extreme_rho(self):
        """Fit should work when rho is near +0.8."""
        true_params = dict(a=0.05, b=0.3, rho=0.8, m=0.1, sigma=0.15)
        k = np.linspace(-0.4, 0.4, 20)
        w_true = svi_total_variance(k, **true_params)
        
        fitted = fit_svi(k, w_true)
        assert fitted is not None
        assert abs(fitted['rho'] - 0.8) < 0.1
