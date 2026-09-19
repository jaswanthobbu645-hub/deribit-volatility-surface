# Verification of Deribit Volatility Surface Project

**Date (UTC):** 2026-09-20 02:50:00  
**Latest Git Commit:** 0c9dc73 chore: remove archive folder and duplicate docs  
**Verification Log:**  
The end-to-end pipeline was executed successfully via `python main.py all`. The following steps completed:

1. ✅ Fetched historical BTC options data (82860 rows)
2. ✅ Fetched historical ETH options data (68160 rows)
3. ✅ Generated DVOL data and Fed meeting analysis for BTC and ETH
4. ✅ Computed daily metrics (RR, Butterfly, Term Slope) and generated charts
5. ✅ Built 3D volatility surfaces
6. ✅ Created crypto vs equity chart
7. ✅ Built ETH Fed event study
8. ✅ Ran walk-forward backtest for BTC and ETH
9. ✅ Ran transaction cost sensitivity analysis

**Outputs Generated:**
- `data/processed/BTC_surface_1y.csv`
- `data/processed/ETH_surface_1y.csv`
- `charts/event_study_final.png`
- `charts/term_structure_butterfly.png`
- `charts/surface_3d.png`
- `charts/crypto_vs_equity.png`
- `charts/eth_fed_study.png`
- `BTC_walkforward_trades.csv`
- `ETH_walkforward_trades.csv`
- Updated `MEMO.md` with cost sensitivity table
- Updated `README.md` with limitations section

**Key Results:**
- BTC DVOL mean: 43.75%, std: 6.69%
- ETH DVOL mean: 62.59%, std: 9.60%
- ETH/BTC vol ratio: 1.43x
- Walk-forward BTC: 2 trades, 0.00% win rate, -13.72% net return
- Walk-forward ETH: 1 trade, 0.00% win rate, -3.33% net return
- Cost sensitivity shows negative returns at all tested transaction cost levels (1%-4% round-trip)

**Limitations Acknowledged:**
- Sample size: Only 7 BTC trades in-sample, 2 trades walk-forward OOS (not statistically significant)
- Data window: Limited to 84-day window (Jun-Sep 2026) due to Deribit API constraints
- Slippage assumption: 1% per side modeled; edge reduced at higher slippage
- No second-window validation due to data limits

All steps completed successfully. The repository is ready for submission.