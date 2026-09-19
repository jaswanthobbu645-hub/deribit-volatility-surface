# Deribit BTC & ETH Volatility Surface — Research Memo

**Author:** Jaswanth
**Problem:** Problem 13 — Deribit Options: Surface, Skew, Event Trading
**Date:** September 2026

## 1. Executive Summary

This project builds a production-grade Deribit options analytics pipeline that:
- Collects live BTC and ETH options data daily
- Reconstructs historical surfaces from Deribit's public API
- Computes 25-delta Risk Reversal, ATM IV, Butterfly, Term Structure Slope
- Fits SVI volatility surfaces with no-arbitrage constraints
- Runs walk-forward backtests of a skew mean-reversion strategy
- Analyzes 8 Fed meetings over 1 year of DVOL data

**Headline findings:**

1. **Crypto volatility has no consistent Fed-meeting reaction.** Across 8 Fed meetings, BTC DVOL rose 5 times and fell 3 times (mean +0.49%, std 2.28%). ETH: 4 up / 4 down.

2. **ETH is structurally 1.43x more volatile than BTC.** Mean DVOL: ETH 62.59% vs BTC 43.72%.

3. **BTC skew is 2.23x more volatile than SPX.** BTC 25-delta RR std: 3.34% vs SPX 1.50%.

4. **Skew mean-reversion shows positive in-sample expectancy on BTC.** +15.61% return, 57% win rate in-sample.

## 2. Data

### 2.1 Sources

| Source | Purpose | Coverage |
|--------|---------|----------|
| Deribit get_instruments, get_tradingview_chart_data | Historical options surfaces | 84 days |
| Deribit get_volatility_index_data | DVOL index | 366 days |
| Live pipeline | Paper-trading log | 24+ days |

### 2.2 Dataset Sizes

| Dataset | Rows | Instruments |
|---------|------|-------------|
| BTC_surface_1y.csv | 81,977 | 978 |
| ETH_surface_1y.csv | 67,640 | 892 |
| dvol_BTC_1y.csv | 366 | - |
| dvol_ETH_1y.csv | 366 | - |

### 2.3 Data Limitations

- Deribit free API caps option history at ~90 days
- DVOL index covers 1 full year
- No survivorship bias within API window

## 3. Methodology

### 3.1 Implied Volatility
Bisection method with bracket [1%, 500%], 50 iterations, IV filter [5%, 300%].

### 3.2 Greeks
Manual Black-Scholes. Delta = N(d1), Gamma = N'(d1)/(S*sigma*sqrt(T)), Vega = S*N'(d1)*sqrt(T)/100, Theta = -S*N'(d1)*sigma/(2*sqrt(T))/365.

### 3.3 25-Delta Risk Reversal
For each (date, expiry), find Call with |delta-0.25| minimized and Put with |delta+0.25| minimized. RR = Call_IV - Put_IV.

### 3.4 SVI Fit
w(k) = a + b*(rho*(k-m) + sqrt((k-m)^2 + sigma^2)). Constraints: b>=0, |rho|<1, sigma>0.

### 3.5 Strategy
- Entry: RR < 20th percentile of rolling 60-day window
- Exit: RR reverts +3% OR 7-day time exit
- Cost: 2% round-trip

### 3.6 Walk-Forward
Train 60 days, test 20 days, roll forward by 20.

## 4. Results

### 4.1 Event Study — Fed Meetings

| Fed Date | BTC Change | ETH Change |
|----------|------------|------------|
| 2025-10-29 | +1.46 | +0.11 |
| 2025-12-17 | +0.21 | -0.46 |
| 2026-01-28 | +4.80 | +5.76 |
| 2026-03-18 | +1.99 | +2.61 |
| 2026-04-29 | -1.10 | -4.32 |
| 2026-06-17 | +1.17 | +1.97 |
| 2026-07-29 | -1.69 | -1.21 |
| 2026-09-16 | -2.95 | -2.91 |

BTC: 5 up / 3 down, mean +0.49%, std 2.28%.
ETH: 4 up / 4 down, mean +0.19%, std 3.01%.
No consistent pattern.

### 4.2 Crypto vs Equity

| Metric | BTC | ETH | SPX |
|--------|-----|-----|-----|
| Mean RR | -1.04% | -0.19% | -0.75% |
| Std RR | 3.34% | 3.71% | 1.50% |
| % Negative | 69% | 54% | ~95% |

BTC skew vol is 2.23x SPX.

### 4.3 Strategy Backtest

In-Sample:
- BTC: 7 trades, 57.14% win, +15.61%, DD -7.93%
- ETH: 11 trades, 36.36% win, -2.01%, DD -3.33%

Walk-Forward OOS:
- BTC: 2 trades, -13.72%
- ETH: 1 trade, -3.33%

PnL Attribution (BTC in-sample avg):
- Delta: +$31.55
- Gamma: +$12.44
- Vega: +$24.92
- Theta: -$69.10
- Net: ~$0

### 4.4 DVOL Statistics (1 Year)

| Metric | BTC | ETH | Ratio |
|--------|-----|-----|-------|
| Mean | 43.72% | 62.59% | 1.43x |
| Std | 6.70 | 9.59 | 1.43x |

## 5. Limitations

1. Walk-forward OOS has only 2 BTC trades — insufficient for inference
2. In-sample vs OOS divergence (positive vs negative)
3. Deribit free API cap at 84 days
4. Slippage assumption: 1% per side
5. DVOL-Skew correlation only 23 overlapping days

## 6. Deliverables

- **Code:** src/data/, src/features/, src/strategy/
- **Data:** data/processed/, data/trades/
- **Charts:** charts/ (7 PNGs)
- **Reports:** README.md, MEMO.md, TEARSHEET.md, DATA_DICTIONARY.md

## 7. Next Steps

1. Extend historical data via Tardis.dev full access
2. Test 10-delta skew
3. Multi-asset expansion (SOL, DOGE)
4. Live delta-hedged strangle trade

## 8. Conclusion

Production-grade Deribit options pipeline processing 149,617 rows across BTC and ETH. The 1-year DVOL event study shows crypto volatility has no consistent Fed-meeting reaction — supporting the thesis that crypto vol is endogenous.