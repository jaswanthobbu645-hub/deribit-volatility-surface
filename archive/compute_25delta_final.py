import ccxt
import pandas as pd
import numpy as np
from vollib.black_scholes.greeks.analytical import delta

print("🚀 Starting 25-delta skew computation...")

# 1. Connect and fetch live data to get underlying price
exchange = ccxt.deribit()
tickers = exchange.fetch_tickers(params={'currency': 'BTC'})

# Find underlying price from the first option's info
underlying_price = None
for symbol, ticker in tickers.items():
    if symbol.endswith('-C') or symbol.endswith('-P'):
        info = ticker.get('info', {})
        underlying_price = info.get('underlying_price')
        if underlying_price:
            break

if not underlying_price:
    # Fallback: Deribit spot is BTC/USDC
    spot_ticker = exchange.fetch_ticker('BTC/USDC')
    underlying_price = spot_ticker['last']

print(f"📍 Current BTC Underlying Price: ${underlying_price:,.0f}")

# 2. Load your saved options data
try:
    df = pd.read_csv('btc_options_snapshot.csv')
    print(f"📊 Loaded {len(df)} options.")
except FileNotFoundError:
    print("❌ File not found. Run fetch_deribit.py first.")
    exit()


# 3. Function to compute Delta (time_to_expiry = 0.1 years ≈ 36 days)
def compute_delta(strike, iv, spot, t=0.1):
    if pd.isna(iv) or iv == 0:
        return None
    try:
        # 'c' for Call delta
        return delta('c', spot, strike, t, iv / 100, 0.0)
    except:
        return None


# Compute Delta for all options
df['delta'] = df.apply(
    lambda row: compute_delta(row['strike'], row['mark_iv'], underlying_price),
    axis=1
)

# Drop rows where delta calculation failed
df = df[df['delta'].notna()].copy()

# Separate Calls and Puts
calls = df[df['kind'] == 'Call']
puts = df[df['kind'] == 'Put']

# Find the strike closest to 0.25 delta for Calls
call_25 = calls.iloc[(calls['delta'] - 0.25).abs().argsort()[:1]]

# For Puts, we want delta near -0.25, so we compare abs(delta + 0.25)
put_25 = puts.iloc[(puts['delta'] + 0.25).abs().argsort()[:1]]

if not call_25.empty and not put_25.empty:
    call_strike = call_25.iloc[0]['strike']
    call_delta = call_25.iloc[0]['delta']
    call_iv = call_25.iloc[0]['mark_iv']

    put_strike = put_25.iloc[0]['strike']
    put_delta = put_25.iloc[0]['delta']
    put_iv = put_25.iloc[0]['mark_iv']

    risk_reversal = call_iv - put_iv

    print("\n✅ 25-delta Call:")
    print(f"   Strike: {call_strike:.0f}, Delta: {call_delta:.3f}, IV: {call_iv:.2f}%")

    print("\n✅ 25-delta Put:")
    print(f"   Strike: {put_strike:.0f}, Delta: {put_delta:.3f}, IV: {put_iv:.2f}%")

    print(f"\n📊 25-delta Risk Reversal: {risk_reversal:.2f}%")
    print("   (Negative = Puts are more expensive than Calls)")

else:
    print("❌ Could not find 25-delta strikes. Try widening the time_to_expiry.")