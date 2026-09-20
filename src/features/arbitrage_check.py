"""
Arbitrage violation checks for the implied volatility surface.

Two types checked:
1. Butterfly arbitrage: d^2(w)/dk^2 >= 0 for all k (Gatheral density condition)
   where w(k) = sigma_BS(k)^2 * T is total implied variance.

2. Calendar spread arbitrage: w(k, T2) >= w(k, T1) for T2 > T1 at same k.
   (Total variance must be non-decreasing in time to maturity.)
"""
import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import minimize

DATA = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed')
CHARTS = os.path.join(os.path.dirname(__file__), '..', '..', 'charts')


def svi(k, a, b, rho, m, sigma):
    return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma ** 2))


def fit_svi(k, w):
    def loss(p):
        a, b, rho, m, sigma = p
        if b < 0 or abs(rho) >= 1 or sigma <= 0:
            return 1e10
        return np.sum((svi(k, a, b, rho, m, sigma) - w) ** 2)
    res = minimize(loss, [np.mean(w), 0.1, -0.3, 0, 0.1],
                   bounds=[(-1, 1), (0, 5), (-0.99, 0.99), (-1, 1), (0.001, 1)],
                   method='L-BFGS-B')
    return res.x if res.success else None


def svi_second_derivative(k, a, b, rho, m, sigma):
    """Analytical second derivative of SVI total variance w.r.t. k."""
    num = sigma ** 2
    denom = ((k - m) ** 2 + sigma ** 2) ** 1.5
    return b * num / denom


def check_butterfly(df_expiry):
    """Butterfly arbitrage: check d^2w/dk^2 >= 0 for all k in range."""
    S = df_expiry['underlying_close'].iloc[0]
    T = df_expiry['days_to_expiry'].iloc[0] / 365.0
    k = np.log(df_expiry['strike'].values / S)
    w = (df_expiry['implied_volatility'].values ** 2) * T

    params = fit_svi(k, w)
    if params is None:
        return None

    a, b, rho, m, sigma = params
    k_test = np.linspace(k.min() - 0.1, k.max() + 0.1, 200)
    second_deriv = svi_second_derivative(k_test, a, b, rho, m, sigma)

    violations = (second_deriv < 0).sum()
    return {
        'params': params,
        'min_second_deriv': second_deriv.min(),
        'violations': violations,
        'is_arbitrage_free': violations == 0
    }


def check_calendar(df_surface):
    """Calendar arbitrage: w(k, T2) >= w(k, T1) for T2 > T1."""
    expiries = sorted(df_surface['expiry_datetime'].unique())
    if len(expiries) < 2:
        return None

    results = []
    for i in range(len(expiries) - 1):
        exp1 = df_surface[df_surface['expiry_datetime'] == expiries[i]].copy()
        exp2 = df_surface[df_surface['expiry_datetime'] == expiries[i+1]].copy()

        exp1 = exp1[(exp1['implied_volatility'] > 0) & (exp1['implied_volatility'] < 3.0)]
        exp2 = exp2[(exp2['implied_volatility'] > 0) & (exp2['implied_volatility'] < 3.0)]

        if len(exp1) < 5 or len(exp2) < 5:
            continue

        S1 = exp1['underlying_close'].iloc[0]
        S2 = exp2['underlying_close'].iloc[0]
        T1 = exp1['days_to_expiry'].iloc[0] / 365.0
        T2 = exp2['days_to_expiry'].iloc[0] / 365.0

        k1 = np.log(exp1['strike'].values / S1)
        k2 = np.log(exp2['strike'].values / S2)
        w1 = (exp1['implied_volatility'].values ** 2) * T1
        w2 = (exp2['implied_volatility'].values ** 2) * T2

        # Find common k range
        k_min = max(k1.min(), k2.min())
        k_max = min(k1.max(), k2.max())
        if k_min >= k_max:
            continue

        k_common = np.linspace(k_min, k_max, 50)
        w1_interp = np.interp(k_common, k1, w1)
        w2_interp = np.interp(k_common, k2, w2)

        violations = (w2_interp < w1_interp).sum()
        results.append({
            'T1': T1, 'T2': T2,
            'violations': violations,
            'is_arbitrage_free': violations == 0
        })

    return results


if __name__ == '__main__':
    df = pd.read_csv(os.path.join(DATA, 'BTC_surface_1y.csv'))
    df['date'] = pd.to_datetime(df['datetime']).dt.date
    recent = sorted(df['date'].unique())[-1]
    day = df[df['date'] == recent].copy()

    print("=" * 60)
    print(f"ARBITRAGE CHECK — {recent}")
    print("=" * 60)

    # Butterfly check per expiry
    print("\n[Butterfly Arbitrage]")
    expiries = sorted(day['expiry_datetime'].unique())[:5]
    for exp in expiries:
        exp_df = day[day['expiry_datetime'] == exp]
        exp_df = exp_df[(exp_df['implied_volatility'] > 0) & (exp_df['implied_volatility'] < 3.0)]
        if len(exp_df) < 5:
            continue
        result = check_butterfly(exp_df)
        if result:
            status = "FREE" if result['is_arbitrage_free'] else f"VIOLATED ({result['violations']})"
            print(f"  {str(exp)[:10]}: {status}, min(d2w/dk2)={result['min_second_deriv']:.6f}")

    # Calendar check
    print("\n[Calendar Spread Arbitrage]")
    cal_results = check_calendar(day)
    if cal_results:
        for r in cal_results:
            status = "FREE" if r['is_arbitrage_free'] else f"VIOLATED ({r['violations']})"
            print(f"  T1={r['T1']:.3f} -> T2={r['T2']:.3f}: {status}")
    else:
        print("  Insufficient expiries for calendar check")

    # Plot butterfly density for one expiry
    target_exp = expiries[1] if len(expiries) > 1 else expiries[0]
    exp_df = day[day['expiry_datetime'] == target_exp]
    exp_df = exp_df[(exp_df['implied_volatility'] > 0) & (exp_df['implied_volatility'] < 3.0)]

    if len(exp_df) >= 5:
        S = exp_df['underlying_close'].iloc[0]
        T = exp_df['days_to_expiry'].iloc[0] / 365.0
        k = np.log(exp_df['strike'].values / S)
        w = (exp_df['implied_volatility'].values ** 2) * T
        params = fit_svi(k, w)

        if params is not None:
            a, b, rho, m, sigma = params
            k_plot = np.linspace(k.min() - 0.1, k.max() + 0.1, 200)
            w_plot = svi(k_plot, a, b, rho, m, sigma)
            d2w = svi_second_derivative(k_plot, a, b, rho, m, sigma)

            fig, axes = plt.subplots(1, 2, figsize=(14, 5))

            axes[0].scatter(k, exp_df['implied_volatility'], c='blue', s=40,
                            label='Market', alpha=0.7)
            axes[0].plot(k_plot, np.sqrt(w_plot / T), 'r-', linewidth=2,
                         label='SVI fit')
            axes[0].set_xlabel('Log-Moneyness k')
            axes[0].set_ylabel('IV')
            axes[0].set_title(f'SVI Fit — {str(target_exp)[:10]}')
            axes[0].legend(); axes[0].grid(True, alpha=0.3)

            axes[1].plot(k_plot, d2w, 'g-', linewidth=2)
            axes[1].axhline(0, color='red', linestyle='--', alpha=0.7,
                            label='Butterfly boundary')
            axes[1].fill_between(k_plot, d2w, 0, where=(d2w < 0),
                                 color='red', alpha=0.4, label='Violation')
            axes[1].set_xlabel('Log-Moneyness k')
            axes[1].set_ylabel('d2w/dk2')
            axes[1].set_title('Butterfly Arbitrage Check')
            axes[1].legend(); axes[1].grid(True, alpha=0.3)

            plt.tight_layout()
            out = os.path.join(CHARTS, 'arbitrage_check.png')
            plt.savefig(out, dpi=300)
            print(f"\nSaved {out}")