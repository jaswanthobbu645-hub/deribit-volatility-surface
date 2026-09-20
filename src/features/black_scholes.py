import math

def norm_cdf(x):
    """Cumulative standard normal distribution."""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def bs_call(S, K, T, r, sigma):
    """Black-Scholes call price."""
    if T <= 0:
        return max(S - K, 0)
    d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)

def bs_put(S, K, T, r, sigma):
    """Black-Scholes put price."""
    if T <= 0:
        return max(K - S, 0)
    d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)

def implied_vol(price, S, K, T, option_type, max_iter=50):
    """Bisection method for implied volatility."""
    if T <= 0 or price <= 0:
        return None
    intrinsic = max(S - K, 0) if option_type == 'call' else max(K - S, 0)
    if price < intrinsic * 0.98:
        return None
    lo, hi = 0.01, 5.0
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        p = bs_call(S, K, T, 0, mid) if option_type == 'call' else bs_put(S, K, T, 0, mid)
        if p < price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def calc_greeks(S, K, T, sigma, option_type):
    """Compute Delta, Gamma, Vega, Theta."""
    if T <= 0 or sigma <= 0:
        return {'delta': 0, 'gamma': 0, 'vega': 0, 'theta': 0}
    d1 = (math.log(S / K) + (0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    delta = norm_cdf(d1) if option_type == 'call' else norm_cdf(d1) - 1
    gamma = (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1**2) / (S * sigma * math.sqrt(T))
    vega = S * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1**2) * math.sqrt(T) / 100
    theta = -(S * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1**2) * sigma) / (2 * math.sqrt(T)) / 365
    return {'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta}
