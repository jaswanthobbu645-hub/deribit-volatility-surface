import pandas as pd
import numpy as np
import math
import os
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy import stats

# Path definitions for data and charts
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
TRADES_DIR = os.path.join(DATA_DIR, "trades")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "charts")



# ============================================================
# BLACK-SCHOLES HELPERS
# ============================================================
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
        return {'delta': 0, 'gamma': 0, 'vega': 0, 'theta': 0}
    d1 = (math.log(S / K) + (0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    delta = norm_cdf(d1) if opt_type == 'call' else norm_cdf(d1) - 1
    gamma = (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) / (S * sigma * math.sqrt(T))
    vega = S * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) * math.sqrt(T) / 100
    theta = -(S * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) * sigma) / (2 * math.sqrt(T)) / 365
    return {'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta}


# ============================================================
# LOAD AND RECOMPUTE
# ============================================================
def load_and_recompute(surface_file):
    print(f"\nLoading {surface_file}...")
    df = pd.read_csv(surface_file)
    df['option_price_usd'] = df['option_close'] * df['underlying_close']
    df = df[df['option_price_usd'] > 0].copy()
    print(f"  Rows after >0 filter: {len(df)}")

    print(f"  Recomputing IVs and greeks...")
    ivs, deltas, gammas, vegas, thetas = [], [], [], [], []
    for _, row in df.iterrows():
        S = row['underlying_close']
        K = row['strike']
        T = row['days_to_expiry'] / 365.0
        opt = row['option_type']
        iv = implied_vol(row['option_price_usd'], S, K, T, opt)
        if iv is None or iv < 0.05 or iv > 3.0:
            ivs.append(None);
            deltas.append(None);
            gammas.append(None);
            vegas.append(None);
            thetas.append(None)
        else:
            g = calc_greeks(S, K, T, iv, opt)
            ivs.append(iv);
            deltas.append(g['delta']);
            gammas.append(g['gamma'])
            vegas.append(g['vega']);
            thetas.append(g['theta'])

    df['iv_new'] = ivs
    df['delta_new'] = deltas
    df['gamma_new'] = gammas
    df['vega_new'] = vegas
    df['theta_new'] = thetas
    df = df[df['iv_new'].notna()].copy()
    print(f"  Rows after IV filter: {len(df)}")

    df['date'] = pd.to_datetime(df['datetime']).dt.date
    df['expiry_date'] = pd.to_datetime(df['expiry_datetime']).dt.date
    return df


# ============================================================
# BUILD RR PER EXPIRY
# ============================================================
def build_rr(df, asset_name):
    print(f"\n[{asset_name}] Building RR per expiry...")
    calls = df[df['option_type'] == 'call'].copy()
    puts = df[df['option_type'] == 'put'].copy()

    calls['dist'] = (calls['delta_new'] - 0.25).abs()
    puts['dist'] = (puts['delta_new'] + 0.25).abs()

    bc = calls.loc[calls.groupby(['date', 'expiry_date'])['dist'].idxmin()]
    bp = puts.loc[puts.groupby(['date', 'expiry_date'])['dist'].idxmin()]

    merged = pd.merge(
        bc[['date', 'expiry_date', 'days_to_expiry', 'underlying_close',
            'strike', 'iv_new', 'option_price_usd',
            'delta_new', 'gamma_new', 'vega_new', 'theta_new']],
        bp[['date', 'expiry_date', 'iv_new']],
        on=['date', 'expiry_date'],
        how='outer',
        suffixes=('_call', '_put')
    )
    merged['rr'] = merged['iv_new_call'] - merged['iv_new_put']
    merged = merged[(merged['days_to_expiry'] >= 7) & (merged['days_to_expiry'] <= 90)]
    merged = merged.dropna(subset=['rr'])

    merged.to_csv(f'{asset_name}_rr_all_expiries.csv', index=False)
    print(f"  Total rows: {len(merged)}")
    print(f"  Unique expiries: {merged['expiry_date'].nunique()}")
    print(f"  Unique dates: {merged['date'].nunique()}")
    print(f"  Expiries per day: {merged.groupby('date')['expiry_date'].nunique().mean():.1f}")
    print(f"  RR range: {merged['rr'].min():.4f} to {merged['rr'].max():.4f}")
    print(f"  Saved to {asset_name}_rr_all_expiries.csv")
    return merged


# ============================================================
# WALK-FORWARD BACKTEST
# ============================================================
def walk_forward(rr_file, asset_name):
    print(f"\n{'=' * 60}\nWALK-FORWARD: {asset_name}\n{'=' * 60}")
    df = pd.read_csv(rr_file)
    df['date'] = pd.to_datetime(df['date'])
    df['expiry_date'] = pd.to_datetime(df['expiry_date'])
    df = df.sort_values(['expiry_date', 'date']).reset_index(drop=True)

    unique_dates = sorted(df['date'].unique())
    TRAIN, TEST = 60, 20
    all_trades = []
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
            dIV = exit_row['iv_new_call'] - entry['iv_new_call']
            hold = (exit_row['date'] - entry['date']).days

            all_trades.append({
                'fold': fold_start,
                'entry_date': entry['date'],
                'exit_date': exit_row['date'],
                'expiry': entry['expiry_date'],
                'dte_at_entry': entry['days_to_expiry'],
                'entry_price': entry['option_price_usd'],
                'exit_price': exit_row['option_price_usd'],
                'entry_rr': entry['rr'],
                'exit_rr': exit_row['rr'],
                'hold_days': hold,
                'net_return_pct': net,
                'delta_pnl': entry['delta_new'] * dS,
                'gamma_pnl': 0.5 * entry['gamma_new'] * dS ** 2,
                'vega_pnl': entry['vega_new'] * (dIV * 100),
                'theta_pnl': entry['theta_new'] * hold,
            })

    if len(all_trades) == 0:
        print(f"❌ No trades for {asset_name}")
        return None

    tdf = pd.DataFrame(all_trades).sort_values('entry_date').reset_index(drop=True)
    wins = tdf[tdf['net_return_pct'] > 0]
    tdf['cum_return'] = tdf['net_return_pct'].cumsum()
    tdf['peak'] = tdf['cum_return'].cummax()
    tdf['dd'] = tdf['cum_return'] - tdf['peak']

    days = (tdf['exit_date'].max() - tdf['entry_date'].min()).days
    tpy = len(tdf) * (365 / days) if days > 0 else 0
    sharpe = (tdf['net_return_pct'].mean() / tdf['net_return_pct'].std()) * np.sqrt(tpy) if tdf[
                                                                                                'net_return_pct'].std() > 0 else 0

    print(f"Total Trades: {len(tdf)}")
    print(f"Win Rate: {len(wins) / len(tdf) * 100:.2f}%")
    print(f"Total Net Return: {tdf['net_return_pct'].sum():.2f}%")
    print(f"Avg Return: {tdf['net_return_pct'].mean():.2f}%")
    print(f"Max DD: {tdf['dd'].min():.2f}%")
    print(f"Trades/Year: {tpy:.1f}")
    print(f"Sharpe: {sharpe:.2f}")
    print(f"Avg Hold Days: {tdf['hold_days'].mean():.1f}")
    print(f"\nPnL Attribution (avg/trade):")
    print(f"  Delta: ${tdf['delta_pnl'].mean():.2f}")
    print(f"  Gamma: ${tdf['gamma_pnl'].mean():.2f}")
    print(f"  Vega:  ${tdf['vega_pnl'].mean():.2f}")
    print(f"  Theta: ${tdf['theta_pnl'].mean():.2f}")

    tdf.to_csv(f'{asset_name}_walkforward_trades.csv', index=False)
    return tdf


# ============================================================
# EVENT STUDY
# ============================================================
def event_study(rr_file, asset_name):
    print(f"\n{'=' * 60}\nEVENT STUDY: {asset_name}\n{'=' * 60}")
    df = pd.read_csv(rr_file, parse_dates=['date'])
    daily = df.groupby('date')['rr'].mean().reset_index()
    daily.columns = ['date', 'rr']

    data_min, data_max = daily['date'].min(), daily['date'].max()
    print(f"Data range: {data_min} to {data_max}")

    events = {
        'BTC Halving': '2024-04-20',
        'ETF Approval': '2024-01-10',
        'Fed Sep 2025': '2025-09-17',
        'Fed Dec 2025': '2025-12-17',
        'Fed Mar 2026': '2026-03-18',
        'Fed Jun 2026': '2026-06-17',
    }
    valid = {k: v for k, v in events.items()
             if pd.to_datetime(v) >= data_min and pd.to_datetime(v) <= data_max}
    print(f"Valid events in range: {len(valid)}")

    if len(valid) == 0:
        print("No events in data range — skipping chart")
        return

    all_windows = []
    for label, date_str in valid.items():
        ed = pd.to_datetime(date_str)
        w = daily[(daily['date'] >= ed - pd.Timedelta(days=7)) &
                  (daily['date'] <= ed + pd.Timedelta(days=7))].copy()
        if len(w) < 5: continue
        w['days_from_event'] = (w['date'] - ed).dt.days
        w['event'] = label
        all_windows.append(w)

    if not all_windows:
        print("No event windows with enough data")
        return

    edf = pd.concat(all_windows)
    fig, ax = plt.subplots(figsize=(12, 7))
    for label in edf['event'].unique():
        d = edf[edf['event'] == label].sort_values('days_from_event')
        ax.plot(d['days_from_event'], d['rr'], marker='o', label=label, alpha=0.7, linewidth=2)
    ax.axvline(0, color='red', linestyle='--', alpha=0.7, linewidth=2)
    ax.set_title(f'{asset_name} 25Δ RR Around Events', fontsize=14)
    ax.set_xlabel('Days from Event')
    ax.set_ylabel('25Δ RR')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{asset_name}_event_study.png', dpi=300)
    print(f"Saved {asset_name}_event_study.png")

    summary = []
    for label in edf['event'].unique():
        d = edf[edf['event'] == label]
        pre = d[d['days_from_event'] < 0]['rr'].mean()
        post = d[d['days_from_event'] >= 0]['rr'].mean()
        summary.append({'event': label, 'pre_rr': pre, 'post_rr': post, 'change': post - pre})
    sdf = pd.DataFrame(summary)
    print("\nEvent Study Summary:")
    print(sdf.to_string())
    sdf.to_csv(f'{asset_name}_event_study_summary.csv', index=False)


# ============================================================
# TEARSHEET
# ============================================================
def tearsheet(asset_name):
    trades = pd.read_csv(f'{asset_name}_walkforward_trades.csv', parse_dates=['entry_date', 'exit_date'])
    trades = trades.sort_values('entry_date').reset_index(drop=True)
    trades['cum'] = trades['net_return_pct'].cumsum()
    trades['peak'] = trades['cum'].cummax()
    trades['dd'] = trades['cum'] - trades['peak']

    total = trades['net_return_pct'].sum()
    wr = (trades['net_return_pct'] > 0).mean() * 100
    max_dd = trades['dd'].min()

    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    axes[0].plot(trades['entry_date'], trades['cum'], marker='o', color='green', linewidth=2)
    axes[0].fill_between(trades['entry_date'], trades['cum'], 0, alpha=0.3, color='green')
    axes[0].set_title(f'{asset_name} Equity Curve — Total {total:.2f}%', fontsize=14)
    axes[0].grid(True, alpha=0.3)

    axes[1].fill_between(trades['entry_date'], trades['dd'], 0, color='red', alpha=0.5)
    axes[1].set_title(f'{asset_name} Drawdown — Max {max_dd:.2f}%', fontsize=14)
    axes[1].grid(True, alpha=0.3)

    comps = ['Delta', 'Gamma', 'Vega', 'Theta']
    vals = [trades[f'{c.lower()}_pnl'].sum() for c in comps]
    axes[2].bar(comps, vals, color=['green' if v > 0 else 'red' for v in vals])
    axes[2].axhline(0, color='black')
    axes[2].set_title(f'{asset_name} PnL Attribution', fontsize=14)
    axes[2].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(f'{asset_name}_tearsheet.png', dpi=300)
    print(f"Saved {asset_name}_tearsheet.png")
    print(f"{asset_name}: {len(trades)} trades, {wr:.1f}% win, {total:.2f}% return, DD {max_dd:.2f}%")


# ============================================================
# CRYPTO vs EQUITY
# ============================================================
def crypto_vs_equity():
    print(f"\n{'=' * 60}\nCRYPTO vs EQUITY COMPARISON\n{'=' * 60}")
    btc = pd.read_csv('os.path.join(PROCESSED_DIR, 'BTC_rr_all_expiries.csv')', parse_dates=['date'])
    eth = pd.read_csv('os.path.join(PROCESSED_DIR, 'ETH_rr_all_expiries.csv')', parse_dates=['date'])
    btc_d = btc.groupby('date')['rr'].mean()
    eth_d = eth.groupby('date')['rr'].mean()
    spx_mean, spx_std = -0.0075, 0.015

    for name, s in [('BTC', btc_d), ('ETH', eth_d)]:
        print(f"\n{name} 25Δ RR:")
        print(f"  Mean: {s.mean():.4f}")
        print(f"  Std:  {s.std():.4f}")
        print(f"  Skew: {s.skew():.4f}")
        print(f"  Kurtosis: {s.kurtosis():.4f}")
        print(f"  Min: {s.min():.4f}")
        print(f"  Max: {s.max():.4f}")
        print(f"  % negative: {(s < 0).mean() * 100:.1f}%")

    print(f"\nSPX benchmark: mean={spx_mean}, std={spx_std}")
    print(f"BTC mean diff vs SPX: {btc_d.mean() - spx_mean:.4f}")
    print(f"Vol ratio BTC/SPX: {btc_d.std() / spx_std:.2f}x")

    t, p = stats.ttest_1samp(btc_d, spx_mean)
    print(f"T-test BTC vs SPX: t={t:.3f}, p={p:.4f}")


# ============================================================
# SVI FIT
# ============================================================
def svi_fit():
    print(f"\n{'=' * 60}\nSVI FIT\n{'=' * 60}")

    def svi(k, a, b, rho, m, sigma):
        return a + b * (rho * (k - m) + np.sqrt((k - m) ** 2 + sigma ** 2))

    df = pd.read_csv('os.path.join(PROCESSED_DIR, 'BTC_surface_1y.csv')')
    df['date'] = pd.to_datetime(df['datetime']).dt.date
    df['expiry_date'] = pd.to_datetime(df['expiry_datetime']).dt.date

    recent = sorted(df['date'].unique())[-10:]
    target_date = recent[0]
    day = df[(df['date'] == target_date) & (df['days_to_expiry'].between(20, 40))]
    if len(day) == 0:
        print("No data for SVI fit");
        return

    target_exp = day['expiry_date'].iloc[0]
    exp_df = day[day['expiry_date'] == target_exp].copy()
    exp_df = exp_df[exp_df['implied_volatility'] > 0]

    if len(exp_df) < 5:
        print("Not enough strikes");
        return

    S = exp_df['underlying_close'].iloc[0]
    T = exp_df['days_to_expiry'].iloc[0] / 365.0
    k = np.log(exp_df['strike'].values / S)
    w = (exp_df['implied_volatility'].values ** 2) * T

    def loss(p):
        a, b, rho, m, sigma = p
        if b < 0 or abs(rho) >= 1 or sigma <= 0: return 1e10
        return np.sum((svi(k, a, b, rho, m, sigma) - w) ** 2)

    res = minimize(loss, [w.mean(), 0.1, -0.3, 0, 0.1],
                   bounds=[(-1, 1), (0, 5), (-0.99, 0.99), (-1, 1), (0.001, 1)],
                   method='L-BFGS-B')

    if res.success:
        a, b, rho, m, sigma = res.x
        print(f"SVI Parameters (BTC {target_exp}):")
        print(f"  a={a:.6f}")
        print(f"  b={b:.6f}")
        print(f"  rho={rho:.6f}")
        print(f"  m={m:.6f}")
        print(f"  sigma={sigma:.6f}")

        k_plot = np.linspace(-0.5, 0.5, 100)
        w_plot = svi(k_plot, a, b, rho, m, sigma)
        iv_plot = np.sqrt(np.maximum(w_plot, 0) / T)

        plt.figure(figsize=(10, 6))
        plt.scatter(k, exp_df['implied_volatility'], c='blue', s=30, label='Raw Data')
        plt.plot(k_plot, iv_plot, 'r-', linewidth=2, label='SVI Fit')
        plt.xlabel('Log-Moneyness k')
        plt.ylabel('Implied Volatility')
        plt.title(f'SVI Fit — BTC {target_exp}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('svi_fit_diagnostic.png', dpi=300)
        print("Saved svi_fit_diagnostic.png")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("DERIBIT OPTIONS MASTER ANALYSIS")
    print("=" * 60)

    # Step 1: Load and recompute for BTC
    btc_df = load_and_recompute('os.path.join(PROCESSED_DIR, 'BTC_surface_1y.csv')')
    btc_rr = build_rr(btc_df, 'BTC')

    # Step 2: Load and recompute for ETH
    eth_df = load_and_recompute('os.path.join(PROCESSED_DIR, 'ETH_surface_1y.csv')')
    eth_rr = build_rr(eth_df, 'ETH')

    # Step 3: Walk-forward
    walk_forward('os.path.join(PROCESSED_DIR, 'BTC_rr_all_expiries.csv')', 'BTC')
    walk_forward('os.path.join(PROCESSED_DIR, 'ETH_rr_all_expiries.csv')', 'ETH')

    # Step 4: Event study
    event_study('os.path.join(PROCESSED_DIR, 'BTC_rr_all_expiries.csv')', 'BTC')

    # Step 5: Tearsheets
    tearsheet('BTC')
    tearsheet('ETH')

    # Step 6: Crypto vs equity
    crypto_vs_equity()

    # Step 7: SVI fit
    svi_fit()

    print(f"\n{'=' * 60}")
    print("MASTER ANALYSIS COMPLETE")
    print(f"{'=' * 60}")
    print("\nGenerated files:")
    print("  os.path.join(PROCESSED_DIR, 'BTC_rr_all_expiries.csv')")
    print("  os.path.join(PROCESSED_DIR, 'ETH_rr_all_expiries.csv')")
    print("  os.path.join(TRADES_DIR, 'BTC_walkforward_trades.csv')")
    print("  os.path.join(TRADES_DIR, 'ETH_walkforward_trades.csv')")
    print("  BTC_event_study.png")
    print("  BTC_event_study_summary.csv")
    print("  os.path.join(CHARTS_DIR, 'BTC_tearsheet.png')")
    print("  os.path.join(CHARTS_DIR, 'ETH_tearsheet.png')")
    print("  svi_fit_diagnostic.png")