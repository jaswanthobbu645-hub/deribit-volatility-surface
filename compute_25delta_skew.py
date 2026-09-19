import ccxt
import pandas as pd
import numpy as np
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import delta

# 1. Fetch current BTC spot price (underlying)
exchange = ccxt.deribit()
ticker = exchange.fetch_ticker('BTC/USD')
spot_price = ticker['last']
print(f"📍 Current BTC Spot: ${spot_price:,.0f}")

# 2. Load your options data
df = pd.read_csv('btc_options_snapshot.csv')
print(f"📊 Loaded {len(df)} options.")


# 3. Function to compute Delta using Black-Scholes
def compute_delta(strike, iv, spot, time_to_expiry=0.1):
    """
    time_to_expiry is an estimate. We use 0.1 years (~36 days) as average.
    For now, we just need to find the strikes closest to 0.25 delta.
    """
    if np.isnan(iv) or iv == 0:
        return None
    try:
        # Black-Scholes Delta for Call
        d = delta('c', spot, strike, time_to_expiry, iv / 100, 0.0)
        return d
    except:
        return None


# 4. Calculate Delta for every option
df['delta'] = df.apply(
    lambda row: compute_delta(row['strike'], row['mark_iv'], spot_price),
    axis=1
)

# 5. Filter out failed calculations
df = df[df['delta'].notna()]

# 6. Find the closest to 25-delta Call and Put
call_df = df[df['kind'] == 'Call']
put_df = df[df['kind'] == 'Put']

# Find strike with delta closest to 0.25
call_25 = call_df.iloc[(call_df['delta'] - 0.25).abs().argsort()[:1]]
put_25 = put_df.iloc[(put_df['delta'] + 0.25).abs().argsort()[:1]]

if not call_25.empty and not put_25.empty:
    call_iv = call_25.iloc[0]['mark_iv']
    put_iv = put_25.iloc[0]['mark_iv']
    risk_reversal = call_iv - put_iv

    print(f"\n✅ 25-delta Call:")
    print(f"   Strike: {call_25.iloc[0]['strike']:.0f}, Delta: {call_25.iloc[0]['delta']:.3f}, IV: {call_iv:.2f}%")

    print(f"\n✅ 25-delta Put:")
    print(f"   Strike: {put_25.iloc[0]['strike']:.0f}, Delta: {put_25.iloc[0]['delta']:.3f}, IV: {put_iv:.2f}%")

    print(f"\n📊 25-delta Risk Reversal: {risk_reversal:.2f}%")
    print(f"   (Negative = Puts are more expensive than Calls)")
else:
    print("❌ Could not find strikes near 25-delta. Try adjusting the time_to_expiry.")