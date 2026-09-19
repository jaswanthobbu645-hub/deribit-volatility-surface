import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm

# Path definitions for data and charts
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
TRADES_DIR = os.path.join(DATA_DIR, "trades")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "charts")


print("🚀 Computing 25-delta skew using Manual Black-Scholes...")

# 1. Connect and fetch live data
exchange = ccxt.deribit()
tickers = exchange.fetch_tickers(params={'currency': 'BTC'})

# Find the current BTC underlying price
underlying_price = None
for symbol, ticker in tickers.items():
    if symbol.endswith('-C') or symbol.endswith('-P'):
        info = ticker.get('info', {})
        underlying_price = info.get('underlying_price')
        if underlying_price:
            break

if not underlying_price:
    spot_ticker = exchange.fetch_ticker('BTC/USDC')
    underlying_price = spot_ticker['last']

print(f"📍 Current BTC Price: ${underlying_price:,.0f}")

# 2. Load your saved options data
df = pd.read_csv('btc_options_snapshot.csv')
print(f"📊 Loaded {len(df)} options.")


# 3. Manual Black-Scholes Delta function
def compute_delta(spot, strike, t, sigma, option_type):
    """
    spot: underlying price
    strike: option strike
    t: time to expiry in years (approx)
    sigma: implied volatility (as decimal, e.g., 0.41)
    option_type: 'call' or 'put'
    """
    if sigma == 0 or t == 0:
        return 0.0
    d1 = (np.log(spot / strike) + (0.05 + 0.5 * sigma ** 2) * t) / (sigma * np.sqrt(t))
    if option_type.lower() == 'call':
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1


# 4. Assume the front expiry is about 30 days out (accurate enough for 25-delta identification)
T = 30 / 365  # ~0.082 years

# Apply to all options
df['delta'] = df.apply(
    lambda row: compute_delta(
        underlying_price,
        row['strike'],
        T,
        row['mark_iv'] / 100,  # convert 41.04% -> 0.4104
        row['kind'].lower()
    ),
    axis=1
)

# 5. Find 25-delta strikes
calls = df[df['kind'] == 'Call']
puts = df[df['kind'] == 'Put']

# For Calls: find strike where delta is closest to +0.25
call_25 = calls.iloc[(calls['delta'] - 0.25).abs().argsort()[:1]]

# For Puts: find strike where delta is closest to -0.25
put_25 = puts.iloc[(puts['delta'] + 0.25).abs().argsort()[:1]]

# 6. Print results
if not call_25.empty and not put_25.empty:
    c_delta = call_25.iloc[0]['delta']
    c_iv = call_25.iloc[0]['mark_iv']
    c_strike = call_25.iloc[0]['strike']

    p_delta = put_25.iloc[0]['delta']
    p_iv = put_25.iloc[0]['mark_iv']
    p_strike = put_25.iloc[0]['strike']

    risk_reversal = c_iv - p_iv

    print("\n✅ 25-delta Call:")
    print(f"   Strike: {c_strike:.0f}, Delta: {c_delta:.3f}, IV: {c_iv:.2f}%")

    print("\n✅ 25-delta Put:")
    print(f"   Strike: {p_strike:.0f}, Delta: {p_delta:.3f}, IV: {p_iv:.2f}%")

    print(f"\n📊 25-delta Risk Reversal: {risk_reversal:.2f}%")
    print("   (Negative = Puts are more expensive than Calls)")
else:
    print("❌ Could not find 25-delta strikes.")