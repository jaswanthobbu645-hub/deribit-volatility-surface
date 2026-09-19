import requests
import time
import math
from datetime import datetime
import csv
import os

# Path definitions for data and charts
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
TRADES_DIR = os.path.join(DATA_DIR, "trades")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "charts")


# ==============================
# CONFIGURATION
# ==============================
BASE_URL = "https://www.deribit.com/api/v2/public"
RISK_FREE_RATE = 0.0
CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "historical_scrape")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, 'ETH_surface_1y.csv')
CHECKPOINT_FILE = os.path.join(CHECKPOINT_DIR, 'checkpoint_eth.csv')
CHECKPOINT_INTERVAL = 100
API_SLEEP = 0.1


# ==============================
# BLACK-SCHOLES FUNCTIONS
# ==============================
def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def black_scholes_price(S, K, T, r, sigma, option_type):
    if T <= 0:
        if option_type == 'call':
            return max(S - K, 0)
        else:
            return max(K - S, 0)
    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option_type == 'call':
        return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    else:
        return K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)


def black_scholes_delta(S, K, T, r, sigma, option_type):
    if T <= 0:
        if option_type == 'call':
            return 1.0 if S > K else 0.0
        else:
            return -1.0 if S < K else 0.0
    d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
    if option_type == 'call':
        return norm_cdf(d1)
    else:
        return norm_cdf(d1) - 1.0


def implied_volatility(market_price, S, K, T, r, option_type, tolerance=1e-5, max_iterations=100):
    sigma = 0.5
    for _ in range(max_iterations):
        price = black_scholes_price(S, K, T, r, sigma, option_type)
        d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
        vega = S * norm_cdf(d1) * math.sqrt(T)
        if vega == 0:
            break
        diff = price - market_price
        if abs(diff) < tolerance:
            return sigma
        sigma = sigma - diff / vega
        if sigma <= 0:
            sigma = 0.001
    return sigma


# ==============================
# DERIBIT API
# ==============================
def fetch_json(url, params=None):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def get_historical_volatility(currency="ETH"):
    url = f"{BASE_URL}/get_historical_volatility"
    data = fetch_json(url, params={"currency": currency})
    if data and "result" in data:
        return data["result"]
    return []


def get_instruments(currency="ETH", kind="option"):
    url = f"{BASE_URL}/get_instruments"
    data = fetch_json(url, params={"currency": currency, "kind": kind})
    if data and "result" in data:
        return data["result"]
    return []


def get_tradingview_chart_data(instrument_name, start_timestamp, end_timestamp, resolution="1D"):
    url = f"{BASE_URL}/get_tradingview_chart_data"
    params = {
        "instrument_name": instrument_name,
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "resolution": resolution
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and "result" in data:
            return data["result"]
        return {}
    except Exception as e:
        print(f"Error fetching chart data for {instrument_name}: {e}")
        return {}


# ==============================
# CHECKPOINT
# ==============================
FIELDNAMES = [
    "timestamp", "datetime", "instrument_name", "strike", "option_type",
    "expiry_timestamp", "expiry_datetime", "days_to_expiry",
    "underlying_close", "option_close", "implied_volatility", "delta"
]


def save_checkpoint(results, filepath):
    if not results:
        return
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)


def load_checkpoint(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ==============================
# MAIN
# ==============================
def main():
    print("=" * 60)
    print("Deribit ETH Options Surface Builder")
    print("=" * 60)

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    end_timestamp = int(time.time() * 1000)
    start_timestamp = end_timestamp - (365 * 24 * 3600 * 1000)
    print(f"Fetching data from {datetime.fromtimestamp(start_timestamp / 1000)}")
    print(f"                 to {datetime.fromtimestamp(end_timestamp / 1000)}")

    print("\n[1/4] Fetching historical volatility...")
    hist_vol = get_historical_volatility("ETH")
    print(f"      Retrieved {len(hist_vol)} HV data points.")

    print("\n[2/4] Fetching ETH option instruments...")
    instruments = get_instruments("ETH", "option")
    option_instruments = [i for i in instruments if i.get("kind") == "option"]
    print(f"      Found {len(option_instruments)} option instruments.")

    print("\n[3/4] Fetching ETH-PERPETUAL as underlying...")
    perp_data = get_tradingview_chart_data("ETH-PERPETUAL", start_timestamp, end_timestamp, "1D")
    if not perp_data or "ticks" not in perp_data:
        print("      ERROR: Could not fetch perpetual data. Exiting.")
        return

    perp_close_by_time = {}
    for i, ts in enumerate(perp_data["ticks"]):
        perp_close_by_time[ts] = perp_data["close"][i]
    print(f"      Fetched {len(perp_close_by_time)} underlying price points.")

    print("\n[4/4] Processing instruments...")
    results = load_checkpoint(CHECKPOINT_FILE)
    already_done = set(r["instrument_name"] for r in results)
    print(f"      Resuming with {len(results)} existing rows.")

    processed = 0
    for instr in option_instruments:
        instrument_name = instr["instrument_name"]
        if instrument_name in already_done:
            continue

        strike = instr["strike"]
        option_type = instr["option_type"]
        expiry_timestamp = instr["expiration_timestamp"]

        if expiry_timestamp < start_timestamp:
            processed += 1
            continue

        option_data = get_tradingview_chart_data(
            instrument_name, start_timestamp, end_timestamp, "1D"
        )

        if not option_data or "ticks" not in option_data:
            processed += 1
            continue

        for i, ts in enumerate(option_data["ticks"]):
            if ts not in perp_close_by_time:
                continue
            if ts >= expiry_timestamp:
                continue

            T = (expiry_timestamp - ts) / (365.0 * 24.0 * 3600.0 * 1000.0)
            if T <= 0:
                continue

            S = perp_close_by_time[ts]
            market_price = option_data["close"][i]

            if S <= 0 or market_price <= 0:
                continue

            try:
                iv = implied_volatility(market_price, S, strike, T, RISK_FREE_RATE, option_type)
                delta = black_scholes_delta(S, strike, T, RISK_FREE_RATE, iv, option_type)

                results.append({
                    "timestamp": ts,
                    "datetime": datetime.fromtimestamp(ts / 1000).isoformat(),
                    "instrument_name": instrument_name,
                    "strike": strike,
                    "option_type": option_type,
                    "expiry_timestamp": expiry_timestamp,
                    "expiry_datetime": datetime.fromtimestamp(expiry_timestamp / 1000).isoformat(),
                    "days_to_expiry": (expiry_timestamp - ts) / (24.0 * 3600.0 * 1000.0),
                    "underlying_close": S,
                    "option_close": market_price,
                    "implied_volatility": iv,
                    "delta": delta
                })
            except Exception:
                pass

        processed += 1

        if processed % CHECKPOINT_INTERVAL == 0:
            print(f"      Processed {processed} instruments | Rows: {len(results)}")
            save_checkpoint(results, CHECKPOINT_FILE)

        time.sleep(API_SLEEP)

    print(f"\n      Processed {processed} instruments. Total rows: {len(results)}")

    save_checkpoint(results, OUTPUT_FILE)
    print(f"\n✅ Saved to {OUTPUT_FILE}")

    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print("✅ Checkpoint removed.")


if __name__ == "__main__":
    main()