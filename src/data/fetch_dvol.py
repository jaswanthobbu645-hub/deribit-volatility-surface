import requests
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Path definitions for data and charts
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
TRADES_DIR = os.path.join(DATA_DIR, "trades")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "charts")



# ============================================================
# STEP 1: FETCH DVOL DATA LOCALLY
# ============================================================
def fetch_dvol(currency, days=365):
    print(f"Fetching {days} days of DVOL for {currency}...")
    end_ts = int(pd.Timestamp.now().timestamp() * 1000)
    start_ts = int((pd.Timestamp.now() - pd.Timedelta(days=days)).timestamp() * 1000)

    url = "https://www.deribit.com/api/v2/public/get_volatility_index_data"
    params = {
        "currency": currency,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "resolution": "1D"
    }

    r = requests.get(url, params=params, timeout=30)
    data = r.json().get("result", {}).get("data", [])

    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.drop(columns=["timestamp"])[["date", "open", "high", "low", "close"]]
    df.to_csv(f"dvol_{currency}_1y.csv", index=False)
    print(f"  {currency}: {len(df)} rows, {df['date'].min()} to {df['date'].max()}")
    return df


btc_dvol = fetch_dvol("BTC")
eth_dvol = fetch_dvol("ETH")

# ============================================================
# STEP 2: FED MEETING ANALYSIS
# ============================================================
fed_dates = [
    '2025-10-29', '2025-12-17', '2026-01-28', '2026-03-18',
    '2026-04-29', '2026-06-17', '2026-07-29', '2026-09-16'
]

print("\n" + "=" * 60)
print("FED MEETING DVOL ANALYSIS")
print("=" * 60)

fed_changes = []
for d in fed_dates:
    fed_date = pd.to_datetime(d)
    window = btc_dvol[(btc_dvol['date'] >= fed_date - pd.Timedelta(days=5)) &
                      (btc_dvol['date'] <= fed_date + pd.Timedelta(days=5))]
    if len(window) < 5:
        continue
    pre = window[window['date'] < fed_date]['close'].mean()
    post = window[window['date'] >= fed_date]['close'].mean()
    change = post - pre
    fed_changes.append(change)
    print(f"  {d}: pre={pre:.2f}, post={post:.2f}, change={change:+.2f}")

print(f"\nMean change: {np.mean(fed_changes):.2f}")
print(f"Std change: {np.std(fed_changes):.2f}")
print(f"Up: {sum(1 for c in fed_changes if c > 0)}, Down: {sum(1 for c in fed_changes if c < 0)}")

# ============================================================
# STEP 3: FINAL 4-PANEL CHART
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Top-left: Full year DVOL
axes[0, 0].plot(btc_dvol['date'], btc_dvol['close'], label='BTC DVOL', color='orange', linewidth=2)
axes[0, 0].plot(eth_dvol['date'], eth_dvol['close'], label='ETH DVOL', color='purple', linewidth=2)
for d in fed_dates:
    axes[0, 0].axvline(pd.to_datetime(d), color='red', linestyle='--', alpha=0.3)
axes[0, 0].set_title('1-Year DVOL with Fed Meetings', fontsize=12)
axes[0, 0].set_ylabel('DVOL (%)')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Top-right: Distribution
axes[0, 1].hist(btc_dvol['close'], bins=30, alpha=0.6, color='orange', label='BTC')
axes[0, 1].hist(eth_dvol['close'], bins=30, alpha=0.6, color='purple', label='ETH')
axes[0, 1].set_title('DVOL Distribution (1 Year)', fontsize=12)
axes[0, 1].set_xlabel('DVOL (%)')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Bottom-left: Fed meeting windows
for d in fed_dates:
    fed_date = pd.to_datetime(d)
    window = btc_dvol[(btc_dvol['date'] >= fed_date - pd.Timedelta(days=5)) &
                      (btc_dvol['date'] <= fed_date + pd.Timedelta(days=5))].copy()
    if len(window) < 5:
        continue
    window['days_from'] = (window['date'] - fed_date).dt.days
    axes[1, 0].plot(window['days_from'], window['close'], marker='o', alpha=0.6, linewidth=1.5)
axes[1, 0].axvline(0, color='red', linestyle='--', alpha=0.7, label='Fed Day')
axes[1, 0].set_title('BTC DVOL Around 8 Fed Meetings', fontsize=12)
axes[1, 0].set_xlabel('Days from Fed')
axes[1, 0].set_ylabel('DVOL (%)')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Bottom-right: Fed changes
colors = ['green' if c > 0 else 'red' for c in fed_changes]
axes[1, 1].bar(range(len(fed_changes)), fed_changes, color=colors, alpha=0.7)
axes[1, 1].axhline(0, color='black')
axes[1, 1].set_xticks(range(len(fed_dates)))
axes[1, 1].set_xticklabels([d[5:] for d in fed_dates], rotation=45)
axes[1, 1].set_title(f'DVOL Change Around Fed (Mean={np.mean(fed_changes):.2f}, Std={np.std(fed_changes):.2f})',
                     fontsize=12)
axes[1, 1].set_ylabel('DVOL Change (%)')
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, 'event_study_final.png'), dpi=300)
print(f"\n✅ Saved {os.path.join(CHARTS_DIR, 'event_study_final.png')}")

# ============================================================
# STEP 4: SUMMARY STATS
# ============================================================
print("\n" + "=" * 60)
print("SUMMARY STATS")
print("=" * 60)
print(f"\nBTC DVOL: mean={btc_dvol['close'].mean():.2f}, std={btc_dvol['close'].std():.2f}")
print(f"ETH DVOL: mean={eth_dvol['close'].mean():.2f}, std={eth_dvol['close'].std():.2f}")
print(f"ETH/BTC vol ratio: {eth_dvol['close'].mean() / btc_dvol['close'].mean():.2f}x")
print(f"\nFed meetings analyzed: {len(fed_changes)}")
print(f"Up reactions: {sum(1 for c in fed_changes if c > 0)}")
print(f"Down reactions: {sum(1 for c in fed_changes if c < 0)}")
print(f"Mean absolute change: {np.mean(np.abs(fed_changes)):.2f}")
print(f"Max positive: {max(fed_changes):.2f}")
print(f"Max negative: {min(fed_changes):.2f}")