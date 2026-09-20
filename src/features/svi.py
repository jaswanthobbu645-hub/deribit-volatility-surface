import numpy as np
from scipy.optimize import minimize


def svi_total_variance(k, a, b, rho, m, sigma):
    """
    Gatheral's raw SVI parameterization for total implied variance w(k).
    
    k: log-moneyness = ln(K/S)
    a, b, rho, m, sigma: SVI parameters
    Returns: array of total variances w = sigma_iv^2 * T
    """
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma ** 2))


def fit_svi(k, w):
    """
    Fit SVI parameters to observed total variances.
    
    k: array of log-moneyness
    w: array of total variances (IV^2 * T)
    Returns: dict with keys a, b, rho, m, sigma
    """
    def loss(params):
        a, b, rho, m, sigma = params
        if b < 0 or abs(rho) >= 1 or sigma <= 0:
            return 1e10
        w_pred = svi_total_variance(k, a, b, rho, m, sigma)
        return np.sum((w_pred - w) ** 2)
    
    x0 = [float(np.mean(w)), 0.1, -0.3, 0.0, 0.1]
    bounds = [(-1, 1), (0, 5), (-0.99, 0.99), (-1, 1), (0.001, 1)]
    
    result = minimize(loss, x0, bounds=bounds, method='L-BFGS-B')
    
    if not result.success:
        return None
    
    a, b, rho, m, sigma = result.x
    return {'a': a, 'b': b, 'rho': rho, 'm': m, 'sigma': sigma}
