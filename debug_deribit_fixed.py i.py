import ccxt

exchange = ccxt.deribit()
markets = exchange.load_markets()

print("🔍 Fetching raw tickers...")
tickers = exchange.fetch_tickers(params={'currency': 'BTC'})

# Filter for standard options only (symbols ending with -C or -P)
option_symbols = []
for symbol in tickers.keys():
    if 'BTC' in symbol and (symbol.endswith('-C') or symbol.endswith('-P')):
        option_symbols.append(symbol)

print(f"✅ Found {len(option_symbols)} standard BTC options.")

if len(option_symbols) > 0:
    # Take the first 3 to inspect
    for sym in option_symbols[:3]:
        ticker = tickers[sym]
        print(f"\n📌 Symbol: {sym}")
        print(f"   Bid: {ticker.get('bid')}")
        print(f"   Ask: {ticker.get('ask')}")
        print(f"   Info: {ticker.get('info')}")
        print("-" * 60)
else:
    print("❌ No standard options found. Trying alternate filter...")
    # Fallback: search for option type in market data
    for sym, market in markets.items():
        if 'BTC' in sym and market.get('type') == 'option':
            print(f"   Market symbol: {sym}")
