import pandas as pd
import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

# Path definitions for data and charts
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
TRADES_DIR = os.path.join(DATA_DIR, "trades")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "charts")


# ==========================================================
# TASK 1: TERM STRUCTURE + BUTTERFLY
# ==========================================================
print("[1/4] Building daily metrics (RR, Butterfly, Term Slope)...")


def compute_daily_metrics(surface_file, asset_name):
    df = pd.read_csv(surface_file)
    df['option_price_usd'] = df['option_close'] * df['underlying_close']
    df = df[df['option_price_usd'] > 0].copy()
    df['date'] = pd.to_datetime(df['datetime']).dt.date
    df['expiry_date'] = pd.to_datetime(df['expiry_datetime']).dt.date
    df = df[(df['days_to_expiry'] >= 7) & (df['days_to_expiry'] <= 90)]

    calls = df[df['option_type'] == 'call'].copy()
    puts = df[df['option_type'] == 'put'].copy()

    calls['d25'] = (calls['delta'] - 0.25).abs()
    puts['d25'] = (puts['delta'] + 0.25).abs()
    calls['dATM'] = calls['delta'].abs()
    puts['dATM'] = puts['delta'].abs()

    bc25 = calls.loc[calls.groupby(['date', 'expiry_date'])['d25'].idxmin()]
    bp25 = puts.loc[puts.groupby(['date', 'expiry_date'])['d25'].idxmin()]
    bcA = calls.loc[calls.groupby(['date', 'expiry_date'])['dATM'].idxmin()]
    bpA = puts.loc[puts.groupby(['date', 'expiry_date'])['dATM'].idxmin()]

    m = pd.merge(bc25[['date', 'expiry_date', 'days_to_expiry', 'underlying_close', 'implied_volatility']],
                 bp25[['date', 'expiry_date', 'implied_volatility']],
                 on=['date', 'expiry_date'], suffixes=('_c25', '_p25'))
    atm = pd.merge(bcA[['date', 'expiry_date', 'implied_volatility']],
                   bpA[['date', 'expiry_date', 'implied_volatility']],
                   on=['date', 'expiry_date'], suffixes=('_cA', '_pA'))
    atm['atm_iv'] = (atm['implied_volatility_cA'] + atm['implied_volatility_pA']) / 2
    m = pd.merge(m, atm[['date', 'expiry_date', 'atm_iv']], on=['date', 'expiry_date'])

    m['rr'] = m['implied_volatility_c25'] - m['implied_volatility_p25']
    m['bf'] = (m['implied_volatility_c25'] + m['implied_volatility_p25']) / 2 - m['atm_iv']

    # Daily aggregation
    daily = []
    for d, g in m.groupby('date'):
        g = g.sort_values('days_to_expiry')
        if len(g) >= 2:
            term_slope = g.iloc[-1]['rr'] - g.iloc[0]['rr']
        else:
            term_slope = 0
        daily.append({
            'date': d,
            'rr_25d': g['rr'].mean(),
            'bf_25d': g['bf'].mean(),
            'atm_iv': g['atm_iv'].mean(),
            'term_slope': term_slope,
            'spot': g['underlying_close'].mean(),
            'n_expiries': len(g)
        })
    daily_df = pd.DataFrame(daily)
    daily_df.to_csv(f'{asset_name}_daily_metrics.csv', index=False)
    print(
        f"  {asset_name}: {len(daily_df)} rows, term_slope range {daily_df['term_slope'].min():.4f} to {daily_df['term_slope'].max():.4f}")
    return daily_df


btc_daily = compute_daily_metrics('os.path.join(PROCESSED_DIR, 'BTC_surface_1y.csv')', 'BTC')
eth_daily = compute_daily_metrics('os.path.join(PROCESSED_DIR, 'ETH_surface_1y.csv')', 'ETH')

# Chart
btc_daily['date'] = pd.to_datetime(btc_daily['date'])
fig, axes = plt.subplots(2, 1, figsize=(14, 10))
axes[0].plot(btc_daily['date'], btc_daily['term_slope'], marker='o', color='blue', linewidth=2)
axes[0].axhline(0, color='black', linestyle='--', alpha=0.5)
axes[0].fill_between(btc_daily['date'], btc_daily['term_slope'], 0, alpha=0.3)
axes[0].set_title('BTC Term Structure Slope (Far RR - Near RR)', fontsize=14)
axes[0].set_ylabel('Term Slope')
axes[0].grid(True, alpha=0.3)

axes[1].plot(btc_daily['date'], btc_daily['bf_25d'], marker='o', color='purple', linewidth=2)
axes[1].axhline(0, color='black', linestyle='--', alpha=0.5)
axes[1].fill_between(btc_daily['date'], btc_daily['bf_25d'], 0, alpha=0.3, color='purple')
axes[1].set_title('BTC 25Δ Butterfly (Wing Premium)', fontsize=14)
axes[1].set_ylabel('Butterfly')
axes[1].set_xlabel('Date')
axes[1].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('os.path.join(CHARTS_DIR, 'term_structure_butterfly.png')', dpi=300)
print("  ✅ Saved os.path.join(CHARTS_DIR, 'term_structure_butterfly.png')")

# ==========================================================
# TASK 2: 3D SURFACE
# ==========================================================
print("\n[2/4] Building 3D surface...")
df = pd.read_csv('os.path.join(PROCESSED_DIR, 'BTC_surface_1y.csv')')
df['date'] = pd.to_datetime(df['datetime']).dt.date
recent = sorted(df['date'].unique())[-1]
day = df[df['date'] == recent].copy()
day = day[(day['days_to_expiry'] > 0) & (day['days_to_expiry'] <= 90)]
day = day[day['implied_volatility'] > 0]
surface = day.groupby(['strike', 'days_to_expiry'])['implied_volatility'].mean().reset_index()

fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')
sc = ax.scatter(surface['days_to_expiry'], surface['strike'], surface['implied_volatility'],
                c=surface['implied_volatility'], cmap='viridis', s=25, alpha=0.8)
ax.set_xlabel('Days to Expiry')
ax.set_ylabel('Strike (USD)')
ax.set_zlabel('Implied Volatility')
ax.set_title(f'BTC Volatility Surface — {recent}')
plt.colorbar(sc, ax=ax, label='IV', shrink=0.6)
plt.tight_layout()
plt.savefig('os.path.join(CHARTS_DIR, 'surface_3d.png')', dpi=300)
print(f"  ✅ Saved os.path.join(CHARTS_DIR, 'surface_3d.png') ({len(surface)} points)")

# ==========================================================
# TASK 3: CRYPTO VS EQUITY CHART
# ==========================================================
print("\n[3/4] Building crypto vs equity chart...")
btc = pd.read_csv('os.path.join(PROCESSED_DIR, 'BTC_rr_all_expiries.csv')', parse_dates=['date'])
eth = pd.read_csv('os.path.join(PROCESSED_DIR, 'ETH_rr_all_expiries.csv')', parse_dates=['date'])
btc_d = btc.groupby('date')['rr'].mean()
eth_d = eth.groupby('date')['rr'].mean()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes[0, 0].plot(btc_d.index, btc_d.values, label='BTC', linewidth=2, color='orange')
axes[0, 0].plot(eth_d.index, eth_d.values, label='ETH', linewidth=2, color='purple')
axes[0, 0].axhline(-0.0075, color='blue', linestyle='--', label='SPX typical')
axes[0, 0].set_title('25Δ RR — Crypto vs SPX')
axes[0, 0].legend();
axes[0, 0].grid(True, alpha=0.3)

axes[0, 1].hist(btc_d, bins=20, alpha=0.5, color='orange', label='BTC', density=True)
axes[0, 1].hist(eth_d, bins=20, alpha=0.5, color='purple', label='ETH', density=True)
axes[0, 1].axvline(-0.0075, color='blue', linestyle='--', label='SPX')
axes[0, 1].set_title('25Δ RR Distribution')
axes[0, 1].legend();
axes[0, 1].grid(True, alpha=0.3)

stds = [btc_d.std(), eth_d.std(), 0.015]
axes[1, 0].bar(['BTC', 'ETH', 'SPX'], stds, color=['orange', 'purple', 'blue'], alpha=0.7)
for i, v in enumerate(stds):
    axes[1, 0].text(i, v, f'{v:.4f}', ha='center', va='bottom')
axes[1, 0].set_title('Skew Volatility (Std of 25Δ RR)')
axes[1, 0].grid(True, alpha=0.3, axis='y')

axes[1, 1].axis('off')
axes[1, 1].text(0.1, 0.5,
                f"BTC  Mean={btc_d.mean():.4f}  Std={btc_d.std():.4f}\nETH  Mean={eth_d.mean():.4f}  Std={eth_d.std():.4f}\nSPX  Mean=-0.0075  Std=0.0150",
                fontsize=12, family='monospace')
axes[1, 1].set_title('Summary Statistics')
plt.tight_layout()
plt.savefig('os.path.join(CHARTS_DIR, 'crypto_vs_equity.png')', dpi=300)
print("  ✅ Saved os.path.join(CHARTS_DIR, 'crypto_vs_equity.png')")

# ==========================================================
# TASK 4: ETH FED EVENT STUDY
# ==========================================================
print("\n[4/4] Building ETH Fed event study...")
eth_dvol = pd.read_csv('os.path.join(PROCESSED_DIR, 'dvol_ETH_1y.csv')', parse_dates=['date'])
fed_dates = ['2025-10-29', '2025-12-17', '2026-01-28', '2026-03-18',
             '2026-04-29', '2026-06-17', '2026-07-29', '2026-09-16']
changes = []
fig, ax = plt.subplots(figsize=(14, 7))
for d in fed_dates:
    fd = pd.to_datetime(d)
    w = eth_dvol[(eth_dvol['date'] >= fd - pd.Timedelta(days=5)) &
                 (eth_dvol['date'] <= fd + pd.Timedelta(days=5))].copy()
    if len(w) < 5: continue
    w['days_from'] = (w['date'] - fd).dt.days
    ax.plot(w['days_from'], w['close'], marker='o', alpha=0.6, linewidth=1.5, label=d[5:])
    pre = w[w['days_from'] < 0]['close'].mean()
    post = w[w['days_from'] >= 0]['close'].mean()
    changes.append(post - pre)
ax.axvline(0, color='red', linestyle='--', alpha=0.7)
ax.set_title('ETH DVOL Around 8 Fed Meetings', fontsize=14)
ax.set_xlabel('Days from Fed');
ax.set_ylabel('ETH DVOL (%)')
ax.legend(fontsize=8, loc='upper left', ncol=2);
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('os.path.join(CHARTS_DIR, 'eth_fed_study.png')', dpi=300)
print(f"  ✅ Saved os.path.join(CHARTS_DIR, 'eth_fed_study.png')")
print(f"  ETH Fed changes: {[round(c, 2) for c in changes]}")
print(
    f"  Mean={np.mean(changes):.2f}, Std={np.std(changes):.2f}, Up={sum(1 for c in changes if c > 0)}, Down={sum(1 for c in changes if c < 0)}")

print("\n" + "=" * 60)
print("ALL FILES GENERATED")
print("=" * 60)