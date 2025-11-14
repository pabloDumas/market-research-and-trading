import os
import time
import requests
import pandas as pd
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

# 1) Alpha Vantage API key
# Option A: set as environment variable ALPHA_VANTAGE_API_KEY
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "YOUR_ALPHA_VANTAGE_API_KEY_HERE")

if API_KEY == "YOUR_ALPHA_VANTAGE_API_KEY_HERE":
    raise RuntimeError("Set your Alpha Vantage API key in API_KEY or ALPHA_VANTAGE_API_KEY env variable.")

# 2) Universe of tickers (small sample; expand as desired)
TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META",
    "GOOGL", "GOOG", "BRK.B", "JNJ", "XOM"
]

# NOTE on rate limits:
# Free tier is small. Keep TICKERS short, or add more sleep.
SLEEP_SECONDS_BETWEEN_CALLS = 15   # basic safety for free-tier limits

# ============================================================
# HELPER: Fetch daily adjusted data for one symbol
# ============================================================

def fetch_alpha_vantage_daily_adjusted(symbol: str) -> pd.DataFrame:
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "apikey": API_KEY,
        "outputsize": "full"
    }

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # ========= NEW FIXES HERE =========

    # Case 1 — Rate limit or usage message
    if "Information" in data:
        raise RuntimeError(
            f"Alpha Vantage rate limit or usage note for {symbol}: {data['Information']}"
        )

    # Case 2 — Hard API error
    if "Error Message" in data:
        raise RuntimeError(f"Alpha Vantage error for {symbol}: {data['Error Message']}")

    # Case 3 — Temporary overload message
    if "Note" in data:
        raise RuntimeError(f"Alpha Vantage temporary note (likely rate limit): {data['Note']}")

    # ==================================

    if "Time Series (Daily)" not in data:
        raise RuntimeError(f"Unexpected structure for {symbol}: {list(data.keys())}")

    ts = data["Time Series (Daily)"]

    df = pd.DataFrame.from_dict(ts, orient="index", dtype=float)
    df = df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. adjusted close": "adjusted_close",
        "6. volume": "volume",
        "7. dividend amount": "dividend",
        "8. split coefficient": "split"
    })
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    return df



# ============================================================
# MAIN: Compute breadth (% above 200DMA) + Adv/Dec
# ============================================================

rows = []
advancers = 0
decliners = 0
unchanged = 0

for i, ticker in enumerate(TICKERS, start=1):
    print(f"[{i}/{len(TICKERS)}] Fetching data for {ticker}...")
    df = fetch_alpha_vantage_daily_adjusted(ticker)

    # Ensure enough history for 200-day SMA
    if df.shape[0] < 200:
        print(f"  Skipping {ticker}: fewer than 200 data points.")
        time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)
        continue

    # Use adjusted_close for trend/breadth
    df["SMA_200"] = df["adjusted_close"].rolling(window=200).mean()

    # Drop rows without SMA_200
    df = df.dropna(subset=["SMA_200"])

    if df.empty:
        print(f"  Skipping {ticker}: no rows after SMA calc.")
        time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)
        continue

    # Latest row
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    latest_close = latest["adjusted_close"]
    latest_sma200 = latest["SMA_200"]
    above_200dma = latest_close > latest_sma200

    # Advance/decline vs previous day's close
    if latest_close > prev["adjusted_close"]:
        advancers += 1
    elif latest_close < prev["adjusted_close"]:
        decliners += 1
    else:
        unchanged += 1

    rows.append({
        "ticker": ticker,
        "date": latest.name,  # index is Timestamp
        "close": latest_close,
        "sma_200": latest_sma200,
        "above_200dma": above_200dma
    })

    # Respect rate limits
    time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)

# Build breadth DataFrame
breadth_df = pd.DataFrame(rows)

if breadth_df.empty:
    raise RuntimeError("No symbols produced valid 200-day SMA data; check TICKERS or API response.")

# All tickers should share the same latest date if they updated, but we'll just take mode/first
latest_date = breadth_df["date"].mode().iloc[0].date()

total = len(breadth_df)
num_above = breadth_df["above_200dma"].sum()
num_below = total - num_above
pct_above = 100 * num_above / total

print("\n==================== MARKET BREADTH ====================")
print(f"Date: {latest_date}")
print(f"Universe size: {total}")
print(f"Above 200DMA: {num_above} ({pct_above:.1f}%)")
print(f"Below 200DMA: {num_below} ({100 - pct_above:.1f}%)")

print("\nAdvance / Decline (vs previous close, same universe):")
print(f"Advancers: {advancers}")
print(f"Decliners: {decliners}")
print(f"Unchanged: {unchanged}")

print("\nSample breadth rows:")
print(breadth_df.head())

# Save detailed breadth snapshot to CSV
output_file = f"alpha_vantage_breadth_{latest_date}.csv"
breadth_df.to_csv(output_file, index=False)
print(f"\nSaved breadth snapshot to: {output_file}")
