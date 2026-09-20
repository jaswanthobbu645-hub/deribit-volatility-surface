import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

DATA = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed')
CHARTS = os.path.join(os.path.dirname(__file__), '..', '..', 'charts')

df = pd.read_csv(os.path.join(DATA, 'BTC_surface_1y.csv'))
df['date'] = pd.to_datetime(df['datetime']).dt.date
recent = sorted(df['date'].unique())[-1]
day = df[df['date'] == recent].copy()
day = day[(day['days_to_expiry'] > 0) & (day['days_to_expiry'] <= 90)]
day = day[(day['implied_volatility'] > 0) & (day['implied_volatility'] < 3.0)]

exp_counts = day.groupby('expiry_datetime').size()
if len(exp_counts) == 0:
    print("No data"); raise SystemExit

target_expiry = exp_counts.idxmax()
exp_df = day[day['expiry_datetime'] == target_expiry].sort_values('strike')

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0,0].plot(exp_df['strike'], exp_df['delta'], 'o-', color='blue')
axes[0,0].axhline(0, color='black', linestyle='--', alpha=0.5)
axes[0,0].set_title('Delta vs Strike'); axes[0,0].set_xlabel('Strike')
axes[0,0].set_ylabel('Delta'); axes[0,0].grid(True, alpha=0.3)

axes[0,1].plot(exp_df['strike'], exp_df['implied_volatility'], 'o-', color='purple')
axes[0,1].set_title('Implied Volatility Smile')
axes[0,1].set_xlabel('Strike'); axes[0,1].set_ylabel('IV')
axes[0,1].grid(True, alpha=0.3)

axes[1,0].scatter(exp_df['delta'], exp_df['implied_volatility'],
                  c=exp_df['strike'], cmap='viridis', s=30)
axes[1,0].set_title('IV vs Delta (color=strike)')
axes[1,0].set_xlabel('Delta'); axes[1,0].set_ylabel('IV')
axes[1,0].grid(True, alpha=0.3)

surface = day.groupby(['delta', 'days_to_expiry'])['implied_volatility'].mean().reset_index()
ax = fig.add_subplot(2, 2, 4, projection='3d')
ax.scatter(surface['delta'], surface['days_to_expiry'],
           surface['implied_volatility'], c=surface['implied_volatility'],
           cmap='viridis', s=15)
ax.set_xlabel('Delta'); ax.set_ylabel('Days to Expiry'); ax.set_zlabel('IV')
ax.set_title('IV Surface in Delta Space')

plt.tight_layout()
out = os.path.join(CHARTS, 'greeks_surface.png')
plt.savefig(out, dpi=300)
print(f"Saved {out}")