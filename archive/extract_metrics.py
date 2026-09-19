import ccxt
import pandas as pd

# Load data
df = pd.read_csv('btc_options_snapshot.csv')

# ATM Strike (highest OI)
atm_strike = df.groupby('strike')['open_interest'].sum().idxmax()
atm_call_iv = df[(df['strike'] == atm_strike) & (df['kind'] == 'Call')]['mark_iv'].mean()
atm_put_iv = df[(df['strike'] == atm_strike) & (df['kind'] == 'Put')]['mark_iv'].mean()

print(f"📍 ATM Strike: {atm_strike}")
print(f"📊 ATM Call IV: {atm_call_iv:.2f}%")
print(f"📊 ATM Put IV: {atm_put_iv:.2f}%")
print(f"📊 ATM Avg IV: {(atm_call_iv + atm_put_iv) / 2:.2f}%")

# --- NEW: Fetch Greeks directly from Deribit ---
exchange = ccxt.deribit()
tickers = exchange.fetch_tickers(params={'currency': 'BTC'})

# Find strikes where Delta ≈ 0.25 for Calls and -0.25 for Puts
call_25delta_iv = None
put_25delta_iv = None
delta_tolerance = 0.03  # Allow ±0.03

for symbol, ticker in tickers.items():
    if not symbol.endswith('-C') and not symbol.endswith('-P'):
        continue

    info = ticker.get('info', {})
    delta = info.get('delta')
    mark_iv = info.get('mark_iv')

    if delta is None or mark_iv is None:
        continue

    if symbol.endswith('-C') and abs(delta - 0.25) < delta_tolerance:
        call_25delta_iv = mark_iv
    elif symbol.endswith('-P') and abs(delta + 0.25) < delta_tolerance:
        put_25delta_iv = mark_iv

if call_25delta_iv and put_25delta_iv:
    risk_reversal = call_25delta_iv - put_25delta_iv
    print(f"\n✅ 25-delta Call IV: {call_25delta_iv:.2f}%")
    print(f"✅ 25-delta Put IV: {put_25delta_iv:.2f}%")
    print(f"✅ 25-delta Risk Reversal: {risk_reversal:.2f}%")
else:
    print("\n⚠️ Could not find exact 25-delta strikes. This is normal if options are thinly traded.")