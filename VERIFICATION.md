# Verification Log

**Verified by:** Jaswanth
**Date:** 2026-09-20
**Machine:** Windows 11, Python 3.11.15
**Commit:** [latest hash]

## Fresh-Clone Verification

The following sequence was run from a clean environment to verify reproducibility:

    git clone https://github.com/jaswanthobbu645-hub/deribit-volatility-surface.git
    cd deribit-volatility-surface
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    pytest tests/ -v

### Result

- **32 tests collected, 32 passed in 2.94 seconds**
- Zero import errors
- All dependencies resolved from pinned `requirements.txt`
- Test coverage:
  - 13 tests: Black-Scholes math (norm_cdf symmetry, put-call parity, deep ITM/OTM, IV roundtrip, invalid inputs)
  - 7 tests: Greeks (delta ranges, call-put parity, gamma/vega/theta signs, zero-T edge case)
  - 9 tests: Data integrity (files exist, IV range, no .orig/.rej, no conflict markers)
  - 3 tests: SVI (parameter recovery, no negative variance, extreme rho)

## Data Files Verified

- data/processed/BTC_surface_1y.csv (81,977 rows)
- data/processed/ETH_surface_1y.csv (67,640 rows)
- data/processed/dvol_BTC_1y.csv (366 rows)
- data/processed/dvol_ETH_1y.csv (366 rows)

## Charts Verified

7 PNGs in charts/: event_study_final, term_structure_butterfly, surface_3d, crypto_vs_equity, eth_fed_study, BTC_tearsheet, ETH_tearsheet

## Conclusion

The repository is fully reproducible. A clean clone with only `requirements.txt` produces 32 passing tests. All data and charts are version-controlled and available in the repo.
