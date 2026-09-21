import pandas as pd
import numpy as np
from scipy import stats
import os

DATA = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed')

btc = pd.read_csv(os.path.join(DATA, 'dvol_BTC_1y.csv'), parse_dates=['date'])
eth = pd.read_csv(os.path.join(DATA, 'dvol_ETH_1y.csv'), parse_dates=['date'])

fed_dates = [
    '2025-10-29', '2025-12-17', '2026-01-28', '2026-03-18',
    '2026-04-29', '2026-06-17', '2026-07-29', '2026-09-16'
]

print("=" * 70)
print("T-TEST: FED MEETING DVOL CHANGES")
print("=" * 70)

for name, df in [('BTC', btc), ('ETH', eth)]:
    changes = []
    for d in fed_dates:
        fed_date = pd.to_datetime(d)
        window = df[(df['date'] >= fed_date - pd.Timedelta(days=5)) &
                    (df['date'] <= fed_date + pd.Timedelta(days=5))]
        if len(window) < 5:
            continue
        pre = window[window['date'] < fed_date]['close'].mean()
        post = window[window['date'] >= fed_date]['close'].mean()
        changes.append(post - pre)

    changes = np.array(changes)
    t_stat, p_value = stats.ttest_1samp(changes, 0)

    print(f"\n{name}:")
    print(f"  N meetings:       {len(changes)}")
    print(f"  Mean change:      {changes.mean():.4f}")
    print(f"  Std change:       {changes.std():.4f}")
    print(f"  T-statistic:      {t_stat:.4f}")
    print(f"  P-value:          {p_value:.4f}")
    if p_value < 0.05:
        print(f"  Result:           SIGNIFICANT")
    else:
        print(f"  Result:           NOT SIGNIFICANT")