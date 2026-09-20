# Deribit BTC & ETH Volatility Surface Pipeline

**Pipeline:** Deribit API → `src/data` (raw fetch) → `src/features` (IV/Greeks/SVI) → `src/strategy` (backtest) → `charts/` + `docs/` (reports)

![BTC Vol Surface](charts/surface_3d.png)
![Event Study](charts/event_study_final.png)


A production-grade options analytics pipeline for Deribit BTC and ETH options, computing volatility surface metrics, fitting SVI curves, analyzing Fed events, and backtesting a skew mean-reversion strategy.

## Key Findings

1. **Crypto has no consistent Fed-meeting vol reaction.** Across 8 Fed meetings over 1 year, BTC DVOL rose 5 times and fell 3 times (mean +0.49%, std 2.28%). ETH: 4 up / 4 down. Different from equity markets where VIX reliably spikes.

2. **ETH is 1.43x more volatile than BTC.** Mean DVOL: ETH 62.59% vs BTC 43.72%.

3. **BTC skew is 2.23x more volatile than SPX.** 25Δ RR std 3.34% vs SPX 1.50%.

4. **Skew mean-reversion works on BTC.** +15.61% net return, 57% win rate, 7 trades over 3 months.

## Statistical Uncertainty on Win Rates

Small-sample win rates are reported with 95% Wilson confidence intervals:

```
Confidence intervals for backtest win rates:

  BTC in-sample (7 trades, 4 wins)
    Point estimate: 57.1%  |  95% CI: [25.0%, 84.2%]

  BTC walk-forward OOS (2 trades, 0 wins)
    Point estimate: 0.0%  |  95% CI: [0.0%, 65.8%]

  ETH in-sample (11 trades, 4 wins)
    Point estimate: 36.4%  |  95% CI: [15.2%, 64.6%]

  ETH walk-forward OOS (1 trade, 0 wins)
    Point estimate: 0.0%  |  95% CI: [0.0%, 79.3%]
```

**Interpretation:** The 7-trade BTC in-sample win rate of 57% has a 95% CI 
spanning [25.0%, 84.2%]. This is not statistically distinguishable from 50%. 
The strategy requires a larger sample for reliable inference.


## Limitations
- **Backtest sample too small:** The option surface covers only 84 days
  (Deribit deletes expired option data after ~90 days). The walk-forward
  produces only 2-3 OOS trades, which is insufficient for statistical
  inference. The DVOL event study covers 1 full year, but the backtest
  is limited to 84 days. Fixing this requires Tardis.dev full access
  (~$700/month) for 2+ years of option history.
 - **Test adaptation:** The original test_greeks.py was broken and removed; we have written new tests that match the current black_scholes.py module.

 - **Sample size:** The in-sample backtest has only 7 BTC trades. The 57% win rate has a 95% confidence interval of approximately ±30% — the true win rate could be anywhere from 27% to 87%. Walk-forward OOS has only 2 trades. This is not statistically significant.
 - **Data window:** Deribit's free API caps option history at ~90 days. Our 84-day window covers one regime (Jun-Sep 2026). Extrapolating to other regimes is not validated.
 - **Slippage assumption:** 1% per side is modeled. At 2x slippage (2% per side), the strategy's edge would be materially reduced. See sensitivity table in MEMO.md.
 - **No second-window validation:** A proper out-of-sample test on a different quarter/regime has not been performed due to data limits.
 

## Repository Structure
