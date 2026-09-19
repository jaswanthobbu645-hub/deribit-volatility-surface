import pandas as pd
import numpy as np
import math

# Path definitions for data and charts
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
TRADES_DIR = os.path.join(DATA_DIR, "trades")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "charts")



def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def bs_call(S, K, T, r, sigma):
    if T <= 0: return max(S - K, 0)
    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
    return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d1 - sigma * math.sqrt(T))


def bs_put(S, K, T, r, sigma):
    if T <= 0: return max(K - S, 0)
    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
    return K * math.exp(-r * T) * norm_cdf(-(d1 - sigma * math.sqrt(T))) - S * norm_cdf(-d1)


def implied_vol(price, S, K, T, opt_type):
    if T <= 0 or price <= 0: return None
    intrinsic = max(S - K, 0) if opt_type == 'call' else max(K - S, 0)
    if price < intrinsic * 0.98: return None
    lo, hi = 0.01, 5.0
    for _ in range(50):
        mid = (lo + hi) / 2
        p = bs_call(S, K, T, 0, mid) if opt_type == 'call' else bs_put(S, K, T, 0, mid)
        if p < price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def calc_greeks(S, K, T, sigma, opt_type):
    if T <= 0 or sigma <= 0:
        return {'delta': 0, 'gamma': 0, 'vega': 0, 'theta': 0}
    d1 = (math.log(S / K) + (0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    delta = norm_cdf(d1) if opt_type == 'call' else norm_cdf(d1) - 1
    gamma = (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) / (S * sigma * math.sqrt(T))
    vega = S * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) * math.sqrt(T) / 100
    theta = -(S * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) * sigma) / (2 * math.sqrt(T)) / 365
    return {'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta}


def walk_forward(rr_file, asset_name):
    print(f"\n{'=' * 60}\nWALK-FORWARD: {asset_name}\n{'=' * 60}")
    df = pd.read_csv(rr_file)
    df['date'] = pd.to_datetime(df['date'])
    df['expiry_date'] = pd.to_datetime(df['expiry_date'])
    df = df.sort_values(['expiry_date', 'date']).reset_index(drop=True)

    unique_dates = sorted(df['date'].unique())
    TRAIN, TEST = 60, 20
    trades = []
    COST_RT = 0.02

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
            net = (gross - COST_RT) * 100

            dS = exit_row['underlying_close'] - entry['underlying_close']
            dIV = exit_row['implied_volatility_call'] - entry['implied_volatility_call']
            hold = (exit_row['date'] - entry['date']).days

            trades.append({
                'entry_date': entry['date'], 'exit_date': exit_row['date'],
                'expiry': entry['expiry_date'],
                'entry_rr': entry['rr'], 'exit_rr': exit_row['rr'],
                'hold_days': hold, 'net_return_pct': net,
                'delta_pnl': entry['delta'] * dS,
                'gamma_pnl': 0.5 * entry['gamma'] * dS ** 2,
                'vega_pnl': entry['vega'] * (dIV * 100),
                'theta_pnl': entry['theta'] * hold,
            })

    if len(trades) == 0:
        print(f"No trades for {asset_name}")
        return None

    tdf = pd.DataFrame(trades).sort_values('entry_date').reset_index(drop=True)
    wins = tdf[tdf['net_return_pct'] > 0]

    print(f"Total Trades: {len(tdf)}")
    print(f"Win Rate: {len(wins) / len(tdf) * 100:.2f}%")
    print(f"Total Net Return: {tdf['net_return_pct'].sum():.2f}%")
    print(
        f"PnL Attribution: Delta=${tdf['delta_pnl'].mean():.2f}, Gamma=${tdf['gamma_pnl'].mean():.2f}, Vega=${tdf['vega_pnl'].mean():.2f}, Theta=${tdf['theta_pnl'].mean():.2f}")

    tdf.to_csv(f'{asset_name}_walkforward_trades.csv', index=False)
    return tdf


if __name__ == "__main__":
    walk_forward('os.path.join(PROCESSED_DIR, 'BTC_rr_all_expiries.csv')', 'BTC')
    walk_forward('os.path.join(PROCESSED_DIR, 'ETH_rr_all_expiries.csv')', 'ETH')