# Data Dictionary

## Surface Data (BTC_surface_1y.csv, ETH_surface_1y.csv)

| Column | Type | Description |
|--------|------|-------------|
| timestamp | int | Unix millisecond timestamp |
| datetime | str | ISO 8601 datetime |
| instrument_name | str | Deribit symbol (e.g., BTC-25DEC26-95000-C) |
| strike | int | Strike price in USD |
| option_type | str | "call" or "put" |
| expiry_timestamp | int | Expiry in Unix ms |
| expiry_datetime | str | Expiry ISO 8601 |
| days_to_expiry | float | DTE at observation |
| underlying_close | float | Underlying spot price (USD) |
| option_close | float | Option premium in BTC |
| option_price_usd | float | Option premium in USD (computed) |
| implied_volatility | float | IV from Black-Scholes (decimal) |
| delta | float | Black-Scholes delta |

## DVOL Data (dvol_BTC_1y.csv, dvol_ETH_1y.csv)

| Column | Description |
|--------|-------------|
| date | Trading date |
| open, high, low, close | OHLC of Deribit Volatility Index |

## Daily Metrics (BTC_daily_metrics.csv)

| Column | Description |
|--------|-------------|
| date | Trading date |
| rr_25d | 25-delta Risk Reversal |
| bf_25d | 25-delta Butterfly |
| atm_iv | ATM implied volatility |
| term_slope | Far RR - Near RR |
| spot | Spot price |
| n_expiries | Number of expiries contributing |
