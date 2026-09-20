import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
df = pd.read_csv(os.path.join(DATA, 'BTC_surface_1y.csv'))
df['date'] = pd.to_datetime(df['datetime']).dt.date

# Get the most recent date
recent_date = sorted(df['date'].unique(), reverse=True)[0]
df_recent = df[df['date'] == recent_date].copy()

# Create a simple plot: IV smile for the nearest expiry
expiries = sorted(df_recent['expiry_datetime'].unique())
if len(expiries) == 0:
    print("No expiries found")
    exit(1)

# Use the nearest expiry
nearest_expiry = expiries[0]
df_expiry = df_recent[df_recent['expiry_datetime'] == nearest_expiry].sort_values('strike')

# Plot
plt.figure(figsize=(10, 6))
plt.plot(df_expiry['strike'], df_expiry['implied_volatility'], 'o-', color='purple')
plt.title(f'Deribit BTC Volatility Smile\nDate: {recent_date}, Expiry: {nearest_expiry}')
plt.xlabel('Strike')
plt.ylabel('Implied Volatility')
plt.grid(True, alpha=0.3)

# Add some metrics as text
spot = df_expiry['underlying_close'].iloc[0]
atm_iv = df_expiry[df_expiry['delta'].abs() < 0.1]['implied_volatility'].mean()
plt.figtext(0.02, 0.02, f'Spot: ${spot:,.0f} | ATM IV: {atm_iv*100:.1f}%', fontsize=10)

# Save
CHARTS = os.path.join(os.path.dirname(__file__), '..', 'charts')
out = os.path.join(CHARTS, 'dashboard_preview.png')
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f"Saved {out}")