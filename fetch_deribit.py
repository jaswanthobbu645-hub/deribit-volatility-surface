import ccxt
import pandas as pd
import time

print("🚀 Starting Deribit Data Fetcher...")

# 1. Connect
exchange = ccxt.deribit()
markets = exchange.load_markets()
print("✅ Connected to Deribit.")

# 2. Fetch tickers for BTC options
print("🔄 Fetching live BTC option data (this takes 5-10 seconds)...")
tickers = exchange.fetch_tickers(params={'currency': 'BTC'})

# 3. Parse the data
data = []
for symbol, ticker in tickers.items():
    # Skip non-BTC and non-options
    if 'BTC' not in symbol:
        continue

    info = ticker.get('info', {})

    # Extract fields directly from Deribit's raw info (NO STRING PARSING)
    strike = info.get('strike')
    if not strike:
        continue

    kind_raw = info.get('kind', '')  # Deribit returns 'call' or 'put'
    if kind_raw == 'call':
        kind = 'Call'
    elif kind_raw == 'put':
        kind = 'Put'
    else:
        continue  # skip if unknown

    mark_iv = info.get('mark_iv')
    open_interest = info.get('open_interest', 0)
    bid = ticker.get('bid')
    ask = ticker.get('ask')

    # Filter out illiquid options (zero OI, no bid/ask, no IV)
    if not bid or not ask or mark_iv is None or open_interest < 5:
        continue

    data.append({
        'strike': float(strike),
        'kind': kind,
        'bid': float(bid),
        'ask': float(ask),
        'mid': (float(bid) + float(ask)) / 2,
        'mark_iv': float(mark_iv),
        'open_interest': float(open_interest)
    })

# 4. Convert to DataFrame and Save
df = pd.DataFrame(data)
df.to_csv('btc_options_snapshot.csv', index=False)

print(f"\n✅ SUCCESS! Saved {len(df)} liquid BTC options to 'btc_options_snapshot.csv'")

# 5. Preview
if len(df) > 0:
    print("\n📊 Preview (First 5 rows):")
    print(df[['strike', 'kind', 'bid', 'ask', 'mark_iv', 'open_interest']].head())
else:
    print("❌ No data retrieved. Check your internet or Deribit status.")