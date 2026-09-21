import pandas as pd
import numpy as np
import os

DATA = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'trades')
trades = pd.read_csv(os.path.join(DATA, 'BTC_walkforward_trades.csv'))

print("=" * 70)
print("BOOTSTRAP SIMULATION")
print("=" * 70)

returns = trades['net_return_pct'].values
n_observed = len(returns)

print(f"\nObserved: {n_observed} trades, mean={returns.mean():.4f}%, std={returns.std():.4f}%")

np.random.seed(42)
bootstrap_means = []
bootstrap_sharpes = []

for _ in range(10000):
    sample = np.random.choice(returns, size=100, replace=True)
    bootstrap_means.append(sample.mean())
    if sample.std() > 0:
        bootstrap_sharpes.append(sample.mean() / sample.std() * np.sqrt(50))

bootstrap_means = np.array(bootstrap_means)
bootstrap_sharpes = np.array(bootstrap_sharpes)

print(f"\nBootstrap 10,000 sims of 100-trade samples:")
print(f"  Expected mean return:    {bootstrap_means.mean():.4f}%")
print(f"  95% CI mean return:      [{np.percentile(bootstrap_means, 2.5):.4f}%, {np.percentile(bootstrap_means, 97.5):.4f}%]")
print(f"  P(positive mean return): {(bootstrap_means > 0).mean()*100:.2f}%")

if len(bootstrap_sharpes) > 0:
    print(f"  Expected Sharpe:         {bootstrap_sharpes.mean():.4f}")
    print(f"  95% CI Sharpe:           [{np.percentile(bootstrap_sharpes, 2.5):.4f}, {np.percentile(bootstrap_sharpes, 97.5):.4f}]")

days_span = 84
trades_per_year = n_observed * (365 / days_span)
print(f"\n  Trades/year estimate:    {trades_per_year:.1f}")
print(f"  Days to reach 50 trades: {50 / (trades_per_year/365):.0f}")