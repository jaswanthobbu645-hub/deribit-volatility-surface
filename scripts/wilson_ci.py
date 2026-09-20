import math

def wilson_confidence_interval(wins, n, z=1.96):
    """Wilson score interval for a binomial proportion. Accurate at small n."""
    if n == 0:
        return (0.0, 0.0)
    phat = wins / n
    denom = 1 + (z ** 2) / n
    centre = (phat + (z ** 2) / (2 * n)) / denom
    half_width = (z / denom) * math.sqrt((phat * (1 - phat) / n) + (z ** 2) / (4 * n ** 2))
    return (max(0.0, centre - half_width), min(1.0, centre + half_width))


if __name__ == '__main__':
    print("Confidence intervals for backtest win rates:")
    print()
    
    scenarios = [
        ('BTC in-sample (7 trades, 4 wins)', 4, 7),
        ('BTC walk-forward OOS (2 trades, 0 wins)', 0, 2),
        ('ETH in-sample (11 trades, 4 wins)', 4, 11),
        ('ETH walk-forward OOS (1 trade, 0 wins)', 0, 1),
    ]
    
    for name, wins, n in scenarios:
        lo, hi = wilson_confidence_interval(wins, n)
        print(f"  {name}")
        print(f"    Point estimate: {wins/n:.1%}  |  95% CI: [{lo:.1%}, {hi:.1%}]")
        print()
