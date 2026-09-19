# Deribit BTC & ETH Volatility Surface Pipeline

A production-grade options analytics pipeline for Deribit BTC and ETH options, computing volatility surface metrics, fitting SVI curves, analyzing Fed events, and backtesting a skew mean-reversion strategy.

## Key Findings

1. **Crypto has no consistent Fed-meeting vol reaction.** Across 8 Fed meetings over 1 year, BTC DVOL rose 5 times and fell 3 times (mean +0.49%, std 2.28%). ETH: 4 up / 4 down. Different from equity markets where VIX reliably spikes.

2. **ETH is 1.43x more volatile than BTC.** Mean DVOL: ETH 62.59% vs BTC 43.72%.

3. **BTC skew is 2.23x more volatile than SPX.** 25Δ RR std 3.34% vs SPX 1.50%.

4. **Skew mean-reversion works on BTC.** +15.61% net return, 57% win rate, 7 trades over 3 months.

## Limitations

 - **Sample size:** The in-sample backtest has only 7 BTC trades. The 57% win rate has a 95% confidence interval of approximately ±30% — the true win rate could be anywhere from 27% to 87%. Walk-forward OOS has only 2 trades. This is not statistically significant.
 - **Data window:** Deribit's free API caps option history at ~90 days. Our 84-day window covers one regime (Jun-Sep 2026). Extrapolating to other regimes is not validated.
 - **Slippage assumption:** 1% per side is modeled. At 2x slippage (2% per side), the strategy's edge would be materially reduced. See sensitivity table in MEMO.md.
 - **No second-window validation:** A proper out-of-sample test on a different quarter/regime has not been performed due to data limits.
 

## Repository Structure
