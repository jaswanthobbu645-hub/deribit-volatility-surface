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
    d2 = d1 - sigma * math.sqrt(T)
    return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)


def bs_put(S, K, T, r, sigma):
    if T <= 0: return max(K - S, 0)
    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)


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
        return {'delta': None, 'gamma': None, 'vega': None, 'theta': None}
    d1 = (math.log(S / K) + (0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    delta = norm_cdf(d1) if opt_type == 'call' else norm_cdf(d1) - 1
    gamma = (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) / (S * sigma * math.sqrt(T))
    vega = S * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) * math.sqrt(T) / 100
    theta = -(S * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) * sigma) / (2 * math.sqrt(T)) / 365
    return {'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta}


def load_and_recompute(path):
    print(f"Loading {path}...")
    df = pd.read_csv(path)
    df['option_price_usd'] = df['option_close'] * df['underlying_close']
    df = df[df['option_price_usd'] > 0].copy()

    print(f"   Recomputing IVs ({len(df)} rows)...")
    ivs = []
    for _, row in df.iterrows():
        iv = implied_vol(row['option_price_usd'], row['underlying_close'],
                         row['strike'], row['days_to_expiry'] / 365.0, row['option_type'])
        ivs.append(iv if iv and 0.05 < iv < 3.0 else None)
    df['iv'] = ivs
    df = df[df['iv'].notna()].copy()

    # Compute greeks per row
    greeks = df.apply(lambda r: calc_greeks(r['underlying_close'], r['strike'],
                                            r['days_to_expiry'] / 365.0, r['iv'], r['option_type']), axis=1)
    df['delta'] = [g['delta'] for g in greeks]
    df['gamma'] = [g['gamma'] for g in greeks]
    df['vega'] = [g['vega'] for g in greeks]
    df['theta'] = [g['theta'] for g in greeks]

    df['date'] = pd.to_datetime(df['datetime']).dt.date
    df['expiry_date'] = pd.to_datetime(df['expiry_datetime']).dt.date

    print(f"   Final rows: {len(df)}")
    return df


def build_multi_expiry_rr(df):
    """Build RR for ALL expiries, not just front."""
    calls = df[df['option_type'] == 'call'].copy()
    puts = df[df['option_type'] == 'put'].copy()

    # 25-delta
    calls['dist25'] = (calls['delta'] - 0.25).abs()
    puts['dist25'] = (puts['delta'] + 0.25).abs()
    # 10-delta
    calls['dist10'] = (calls['delta'] - 0.10).abs()
    puts['dist10'] = (puts['delta'] + 0.10).abs()

    # 25-delta call/put
    bc25 = calls.loc[calls.groupby(['date', 'expiry_date'])['dist25'].idxmin()]
    bp25 = puts.loc[puts.groupby(['date', 'expiry_date'])['dist25'].idxmin()]

    # 10-delta call/put
    bc10 = calls.loc[calls.groupby(['date', 'expiry_date'])['dist10'].idxmin()]
    bp10 = puts.loc[puts.groupby(['date', 'expiry_date'])['dist10'].idxmin()]

    m = pd.merge(
        bc25[['date', 'expiry_date', 'days_to_expiry', 'underlying_close', 'strike',
              'iv', 'option_price_usd', 'delta', 'gamma', 'vega', 'theta']],
        bp25[['date', 'expiry_date', 'iv']],
        on=['date', 'expiry_date'], suffixes=('_call', '_put')
    )
    m['rr_25'] = m['iv_call'] - m['iv_put']

    # Add 10-delta RR
    m10 = pd.merge(
        bc10[['date', 'expiry_date', 'iv']],
        bp10[['date', 'expiry_date', 'iv']],
        on=['date', 'expiry_date'], suffixes=('_c10', '_p10')
    )
    m10['rr_10'] = m10['iv_c10'] - m10['iv_p10']
    m = pd.merge(m, m10[['date', 'expiry_date', 'rr_10']], on=['date', 'expiry_date'], how='left')

    # Keep ALL expiries with DTE 7-90
    m = m[(m['days_to_expiry'] >= 7) & (m['days_to_expiry'] <= 90)]
    m = m.dropna(subset=['rr_25'])

    # Rolling percentile per expiry
    m = m.sort_values(['expiry_date', 'date'])
    m['rr_25_p20'] = m.groupby('expiry_date')['rr_25'].transform(
        lambda x: x.rolling(30, min_periods=10).quantile(0.20))
    m['rr_10_p20'] = m.groupby('expiry_date')['rr_10'].transform(
        lambda x: x.rolling(30, min_periods=10).quantile(0.20))

    return m.dropna(subset=['rr_25_p20'])


def backtest_multi(asset_name, asset_path):
    print(f"\n{'=' * 60}\nAGGRESSIVE BACKTEST — {asset_name}\n{'=' * 60}")
    df = load_and_recompute(asset_path)
    m = build_multi_expiry_rr(df)

    print(f"\n   Total trade-eligible rows: {len(m)}")
    print(f"   Unique expiries: {m['expiry_date'].nunique()}")
    print(f"   RR 25 range: {m['rr_25'].min():.4f} to {m['rr_25'].max():.4f}")

    # Entry: RR_25 in bottom 20% AND RR_10 also extreme
    entries = m[(m['rr_25'] < m['rr_25_p20']) & (m['rr_25_p20'] < -0.02)].copy()
    entries = entries.sort_values('date')

    print(f"   Raw entry signals: {len(entries)}")

    # Deduplicate: one entry per (date, expiry)
    entries = entries.drop_duplicates(subset=['date', 'expiry_date'])
    print(f"   After dedup: {len(entries)}")

    trades = []
    COST_RT = 0.02

    for _, entry in entries.iterrows():
        entry_date = entry['date']
        expiry_date = entry['expiry_date']

        # Find exit: same expiry, future dates
        future = m[(m['expiry_date'] == expiry_date) & (m['date'] > entry_date)].sort_values('date')
        if len(future) == 0:
            continue

        exit_row = None
        for _, f in future.iterrows():
            hold_days = (pd.to_datetime(f['date']) - pd.to_datetime(entry_date)).days
            if f['rr_25'] > entry['rr_25'] + 0.03 or hold_days >= 7:
                exit_row = f
                break

        if exit_row is None:
            exit_row = future.iloc[-1]

        exit_price = exit_row['option_price_usd']
        gross_ret = (exit_price - entry['option_price_usd']) / entry['option_price_usd']
        net_ret = gross_ret - COST_RT

        # PnL attribution
        dS = exit_row['underlying_close'] - entry['underlying_close']
        dIV = exit_row['iv_call'] - entry['iv_call']
        hold_days = (pd.to_datetime(exit_row['date']) - pd.to_datetime(entry_date)).days

        trades.append({
            'entry_date': entry_date, 'exit_date': exit_row['date'],
            'expiry': expiry_date, 'dte_at_entry': entry['days_to_expiry'],
            'entry_price': entry['option_price_usd'], 'exit_price': exit_price,
            'entry_rr_25': entry['rr_25'], 'exit_rr_25': exit_row['rr_25'],
            'hold_days': hold_days,
            'gross_return_pct': gross_ret * 100,
            'net_return_pct': net_ret * 100,
            'delta_pnl': entry['delta'] * dS,
            'gamma_pnl': 0.5 * entry['gamma'] * dS ** 2,
            'vega_pnl': entry['vega'] * (dIV * 100),
            'theta_pnl': entry['theta'] * hold_days,
        })

    if len(trades) == 0:
        print("❌ Still no trades.")
        return None

    tdf = pd.DataFrame(trades)
    wins = tdf[tdf['net_return_pct'] > 0]
    losses = tdf[tdf['net_return_pct'] <= 0]

    print(f"\n📊 RESULTS — {asset_name}")
    print(f"Total Trades:        {len(tdf)}")
    print(f"Win Rate:            {len(wins) / len(tdf) * 100:.2f}%")
    print(f"Avg Net Return:      {tdf['net_return_pct'].mean():.2f}%")
    print(f"Total Net Return:    {tdf['net_return_pct'].sum():.2f}%")
    print(f"Avg Hold Days:       {tdf['hold_days'].mean():.1f}")
    if len(wins) > 0: print(f"Avg Win:             {wins['net_return_pct'].mean():.2f}%")
    if len(losses) > 0: print(f"Avg Loss:            {losses['net_return_pct'].mean():.2f}%")
    print(f"\nTrades per Month:")
    tdf['month'] = pd.to_datetime(tdf['entry_date']).dt.to_period('M')
    print(tdf.groupby('month').size().to_string())
    print(f"\nPnL Attribution (avg per trade):")
    print(f"   Delta PnL:  ${tdf['delta_pnl'].mean():.4f}")
    print(f"   Gamma PnL:  ${tdf['gamma_pnl'].mean():.4f}")
    print(f"   Vega PnL:   ${tdf['vega_pnl'].mean():.4f}")
    print(f"   Theta PnL:  ${tdf['theta_pnl'].mean():.4f}")

    tdf.to_csv(f'{asset_name}_trades_aggressive.csv', index=False)
    print(f"\n✅ Saved to {asset_name}_trades_aggressive.csv")
    return tdf


if __name__ == "__main__":
    backtest_multi('BTC', 'os.path.join(PROCESSED_DIR, 'BTC_surface_1y.csv')')
    backtest_multi('ETH', 'os.path.join(PROCESSED_DIR, 'ETH_surface_1y.csv')')