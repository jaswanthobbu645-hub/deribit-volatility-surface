import ccxt
import pandas as pd

print("🚀 Starting Deribit Data Fetcher...")

# Connect
exchange = ccxt.deribit()
exchange.load_markets()
print("✅ Connected to Deribit.")

# Fetch tickers
print("🔄 Fetching live BTC option data (this takes 5-10 seconds)...")
tickers = exchange.fetch_tickers(params={'currency': 'BTC'})

data = []

for symbol, ticker in tickers.items():
    # 1. Only standard options (ending with -C or -P)
    if not symbol.endswith('-C') and not symbol.endswith('-P'):
        continue

    info = ticker.get('info', {})
    instrument_name = info.get('instrument_name', '')

    # 2. Parse strike from instrument_name: BTC-25DEC26-95000-P
    parts = instrument_name.split('-')
    if len(parts) >= 3:
        try:
            strike = int(parts[2])  # The 3rd part is the strike
        except ValueError:
            continue
    else:
        continue

    # 3. Determine Call or Put
    kind = 'Call' if symbol.endswith('-C') else 'Put'

    # 4. Extract pricing data
    bid = ticker.get('bid')
    ask = ticker.get('ask')
    mark_iv = info.get('mark_iv')
    open_interest = info.get('open_interest', 0)

    # 5. Filter out illiquid garbage (no bid/ask, no IV, or zero OI)
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

# Save to CSV
df = pd.DataFrame(data)
df.to_csv('btc_options_snapshot.csv', index=False)

print(f"\n✅ SUCCESS! Saved {len(df)} liquid BTC options to 'btc_options_snapshot.csv'")
print("\n📊 Preview (First 5 rows):")
print(df[['strike', 'kind', 'bid', 'ask', 'mark_iv', 'open_interest']].head())