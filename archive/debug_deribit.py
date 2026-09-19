import ccxt

exchange = ccxt.deribit()
markets = exchange.load_markets()

print("🔍 Fetching raw tickers...")
tickers = exchange.fetch_tickers(params={'currency': 'BTC'})

count = 0
for symbol, ticker in tickers.items():
    # Only look at BTC options
    if 'BTC' in symbol and 'OPTION' in symbol.upper():
        print(f"\n📌 Symbol: {symbol}")
        print(f"   Bid: {ticker.get('bid')}")
        print(f"   Ask: {ticker.get('ask')}")
        print(f"   Raw Info: {ticker.get('info')}")
        print("-" * 60)
        count += 1
        if count >= 3:  # Just show 3 examples
            break

if count == 0:
    print("❌ No BTC options found in the ticker response.")
    print("   This might mean Deribit is returning a different symbol format.")
    print("   Let's print the first 5 symbols from the entire response:")
    for i, (sym, _) in enumerate(list(tickers.items())[:5]):
        print(f"   {i+1}. {sym}")