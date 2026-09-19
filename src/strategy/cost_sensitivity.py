import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def run_backtest_with_cost(rr_file, cost_rt):
    df = pd.read_csv(rr_file)
    df['date'] = pd.to_datetime(df['date'])
    df['expiry_date'] = pd.to_datetime(df['expiry_date'])
    df = df.sort_values(['expiry_date', 'date']).reset_index(drop=True)
    
    unique_dates = sorted(df['date'].unique())
    TRAIN, TEST = 60, 20
    trades = []
    
    for fold_start in range(TRAIN, len(unique_dates) - TEST + 1, TEST):
        train_end = unique_dates[fold_start - 1]
        test_start = unique_dates[fold_start]
        test_end = unique_dates[min(fold_start + TEST - 1, len(unique_dates) - 1)]
        
        p20 = df[df['date'] <= train_end]['rr'].quantile(0.20)
        test_df = df[(df['date'] >= test_start) & (df['date'] <= test_end)]
        entries = test_df[test_df['rr'] < p20].drop_duplicates(subset=['date', 'expiry_date'])
        
        for _, entry in entries.iterrows():
            future = df[(df['expiry_date'] == entry['expiry_date']) &
                        (df['date'] > entry['date'])].sort_values('date')
            if len(future) == 0: continue
            
            exit_row = None
            for _, f in future.iterrows():
                hold = (f['date'] - entry['date']).days
                if f['rr'] > entry['rr'] + 0.03 or hold >= 7:
                    exit_row = f
                    break
            if exit_row is None:
                exit_row = future.iloc[-1]
            
            gross = (exit_row['option_price_usd'] - entry['option_price_usd']) / entry['option_price_usd']
            net = (gross - cost_rt) * 100
            
            trades.append({'net_return_pct': net})
    
    if len(trades) == 0:
        return None
    
    tdf = pd.DataFrame(trades)
    return {
        'cost': cost_rt * 100,
        'trades': len(tdf),
        'total_return': tdf['net_return_pct'].sum(),
        'avg_return': tdf['net_return_pct'].mean(),
        'win_rate': (tdf['net_return_pct'] > 0).mean() * 100
    }

print("=" * 70)
print("TRANSACTION COST SENSITIVITY")
print("=" * 70)

for asset in ['BTC', 'ETH']:
    print(f"\n{asset}:")
    print(f"{'Cost (RT)':<12} {'Trades':<8} {'Total Ret':<12} {'Avg Ret':<12} {'Win Rate':<10}")
    print("-" * 60)
    
    for cost in [0.01, 0.02, 0.03, 0.04]:
        result = run_backtest_with_cost(
            f'data/processed/{asset}_rr_all_expiries.csv', cost
        )
        if result:
            print(f"{result['cost']:.2f}%{'':<7} {result['trades']:<8} {result['total_return']:>10.2f}%  {result['avg_return']:>10.4f}%  {result['win_rate']:>8.2f}%")
        else:
            print(f"{cost*100:.2f}%{'':<7} 0 trades")