import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime

# Path definitions for data and charts
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
TRADES_DIR = os.path.join(DATA_DIR, "trades")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "charts")


print("[RUN] Running Daily Deribit Metrics Update...")

# --- 1. FETCH DATA ---
exchange = ccxt.deribit()
tickers = exchange.fetch_tickers(params={'currency': 'BTC'})

# Extract underlying price
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

print(f"[PRICE] Current BTC Price: ${underlying_price:,.0f}")

# Parse raw data into DataFrame
data = []
for symbol, ticker in tickers.items():
    if not symbol.endswith('-C') and not symbol.endswith('-P'):
        continue

    info = ticker.get('info', {})
    instrument_name = info.get('instrument_name', '')

    parts = instrument_name.split('-')
    if len(parts) >= 3:
        try:
            strike = int(parts[2])
        except:
            continue
    else:
        continue

    kind = 'Call' if symbol.endswith('-C') else 'Put'
    bid = ticker.get('bid')
    ask = ticker.get('ask')
    mark_iv = info.get('mark_iv')
    open_interest = info.get('open_interest', 0)

    if bid is None or ask is None or mark_iv is None or open_interest < 5:
        continue

    data.append({
        'strike': strike,
        'kind': kind,
        'bid': bid,
        'ask': ask,
        'mid': (bid + ask) / 2,
        'mark_iv': mark_iv,
        'open_interest': open_interest
    })

df = pd.DataFrame(data)
df.to_csv(os.path.join(RAW_DIR, f'btc_options_{datetime.now().strftime("%Y%m%d")}.csv'), index=False)
print(f"[OK] Saved {len(df)} options to daily file.")


# --- 2. COMPUTE 25-DELTA SKEW (Manual Black-Scholes) ---
def compute_delta(spot, strike, t, sigma, option_type):
    if sigma == 0 or t == 0:
        return 0.0
    d1 = (np.log(spot / strike) + (0.05 + 0.5 * sigma ** 2) * t) / (sigma * np.sqrt(t))
    if option_type.lower() == 'call':
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1


T = 30 / 365  # Approx 30 days to expiry

df['delta'] = df.apply(
    lambda row: compute_delta(
        underlying_price,
        row['strike'],
        T,
        row['mark_iv'] / 100,
        row['kind'].lower()
    ),
    axis=1
)

calls = df[df['kind'] == 'Call']
puts = df[df['kind'] == 'Put']

call_25 = calls.iloc[(calls['delta'] - 0.25).abs().argsort()[:1]]
put_25 = puts.iloc[(puts['delta'] + 0.25).abs().argsort()[:1]]

if not call_25.empty and not put_25.empty:
    c_strike = call_25.iloc[0]['strike']
    c_delta = call_25.iloc[0]['delta']
    c_iv = call_25.iloc[0]['mark_iv']

    p_strike = put_25.iloc[0]['strike']
    p_delta = put_25.iloc[0]['delta']
    p_iv = put_25.iloc[0]['mark_iv']

    risk_reversal = c_iv - p_iv

    # --- 3. APPEND TO HISTORY CSV ---
    today = datetime.now().strftime("%Y-%m-%d")
    history_file = 'metrics_history.csv'

    new_row = pd.DataFrame([{
        'date': today,
        'btc_price': underlying_price,
        'atm_iv': (c_iv + p_iv) / 2,  # rough ATM approximation
        'risk_reversal': risk_reversal,
        'call_strike': c_strike,
        'call_iv': c_iv,
        'put_strike': p_strike,
        'put_iv': p_iv
    }])

    try:
        history = pd.read_csv(history_file)
        history = pd.concat([history, new_row], ignore_index=True)
    except FileNotFoundError:
        history = new_row

    history.to_csv(history_file, index=False)

    print(f"[METRICS] Metrics Summary:")
    print(f"   ATM IV: {(c_iv + p_iv) / 2:.2f}%")
    print(f"   Risk Reversal: {risk_reversal:.2f}%")
    print(f"   Call Strike: {c_strike}, Put Strike: {p_strike}")
    print(f"[OK] Appended to '{history_file}'")
else:
    print("[FAIL] Could not compute 25-delta skew today.")
