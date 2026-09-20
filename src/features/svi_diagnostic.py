import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from features.svi import svi_total_variance, fit_svi

DATA = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed')
CHARTS = os.path.join(os.path.dirname(__file__), '..', '..', 'charts')

df = pd.read_csv(os.path.join(DATA, 'BTC_surface_1y.csv'))
df['date'] = pd.to_datetime(df['datetime']).dt.date
recent = sorted(df['date'].unique())[-1]
day = df[df['date'] == recent].copy()

exp_counts = day.groupby('expiry_datetime').size().sort_values(ascending=False)
top_expiries = exp_counts.head(3).index.tolist()

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for idx, expiry in enumerate(top_expiries):
    exp_df = day[day['expiry_datetime'] == expiry].copy()
    exp_df = exp_df[(exp_df['implied_volatility'] > 0) &
                    (exp_df['implied_volatility'] < 3.0)]
    if len(exp_df) < 5:
        continue
    S = exp_df['underlying_close'].iloc[0]
    T = exp_df['days_to_expiry'].iloc[0] / 365.0
    k = np.log(exp_df['strike'].values / S)
    w = (exp_df['implied_volatility'].values ** 2) * T

    params = fit_svi(k, w)
    if params is None:
        continue

    a, b, rho, m, sigma = (params['a'], params['b'], params['rho'],
                            params['m'], params['sigma'])
    k_plot = np.linspace(k.min(), k.max(), 100)
    w_plot = svi_total_variance(k_plot, a, b, rho, m, sigma)
    iv_plot = np.sqrt(np.maximum(w_plot, 0) / T)

    ax = axes[idx]
    ax.scatter(k, exp_df['implied_volatility'], c='blue', s=40,
               label='Market', alpha=0.7)
    ax.plot(k_plot, iv_plot, 'r-', linewidth=2, label='SVI Fit')
    ax.set_title(f'Expiry: {str(expiry)[:10]}\na={a:.3f}, b={b:.3f}, rho={rho:.3f}')
    ax.set_xlabel('Log-Moneyness k = ln(K/S)')
    ax.set_ylabel('Implied Volatility')
    ax.legend(); ax.grid(True, alpha=0.3)

plt.tight_layout()
out = os.path.join(CHARTS, 'svi_diagnostic.png')
plt.savefig(out, dpi=300)
print(f"Saved {out}")