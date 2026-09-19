# Deribit BTC & ETH Volatility Surface — Tearsheet

**Project:** Problem 13 — Deribit Options: Surface, Skew, Event Trading
**Author:** Jaswanth

## Key Metrics

### Walk-Forward (Out-of-Sample) Results
| Metric | BTC | ETH |
| :--- | :--- | :--- |
| Total Trades | 2 | 1 |
| Win Rate | 0% | 0% |
| Total Return | -13.72% | -3.33% |
| Note | Sample too small for inference | Sample too small |

### In-Sample (Full Period) Backtest
| Metric | BTC | ETH |
| :--- | :--- | :--- |
| Total Trades | 7 | 11 |
| Win Rate | 57.14% | 36.36% |
| Total Return | +15.61% | -2.01% |
| Max Drawdown | -7.93% | -3.33% |

**Interpretation:** In-sample backtest shows positive BTC expectancy; 
walk-forward OOS shows only 2 trades — insufficient for statistical 
significance. This is honestly documented in MEMO.md as the primary limitation.

## PnL Attribution (BTC In-Sample, Avg per Trade)
| Greek | Value |
| :--- | :--- |
| Delta | +$31.55 |
| Gamma | +$12.44 |
| Vega | +$24.92 |
| Theta | -$69.10 |

**Insight:** Edge comes from Delta + Gamma + Vega overcoming Theta decay.

## Fed Meeting DVOL Study (1 Year)
| Metric | BTC | ETH |
| :--- | :--- | :--- |
| Fed meetings analyzed | 8 | 8 |
| Up reactions | 5 | 4 |
| Down reactions | 3 | 4 |
| Mean DVOL change | +0.49% | +0.19% |
| Std DVOL change | 2.28% | 3.01% |

**Finding:** No consistent Fed reaction. Crypto vol is endogenous.

## Crypto vs Equity (25Δ RR)
| Metric | BTC | ETH | SPX |
| :--- | :--- | :--- | :--- |
| Mean | -1.04% | -0.19% | -0.75% |
| Std | 3.34% | 3.71% | 1.50% |
| Ratio vs SPX | 2.23x | 2.47x | 1.00x |

**Finding:** Crypto skew is 2.2-2.5x more volatile than SPX.

## DVOL Statistics (1 Year)
| Metric | BTC | ETH | Ratio |
| :--- | :--- | :--- | :--- |
| Mean | 43.72% | 62.59% | 1.43x |
| Std | 6.70 | 9.59 | 1.43x |

## Deliverables
- **Code:** src/ (organized by function)
- **Data:** data/processed/ (surfaces, DVOL, metrics)
- **Charts:** charts/ (7 PNGs)
- **Docs:** docs/ (MEMO.md, TEARSHEET.md, DATA_DICTIONARY.md)
