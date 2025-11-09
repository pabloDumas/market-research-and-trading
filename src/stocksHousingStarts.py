#!/usr/bin/env python3
import os, sys, requests
from datetime import date
try:
    import pandas as pd
except Exception:
    pd = None

API_KEY = os.getenv("FRED_API_KEY")
SERIES_ID = "HOUST"  # Housing Starts: Total, SAAR

if not API_KEY:
    print("Set FRED_API_KEY env var first.", file=sys.stderr)
    sys.exit(1)

url = "https://api.stlouisfed.org/fred/series/observations"
params = {
    "series_id": SERIES_ID,
    "api_key": API_KEY,
    "file_type": "json",
    "observation_start": "1990-01-01"  # adjust as you like
}

r = requests.get(url, params=params, timeout=30)
r.raise_for_status()
data = r.json()

# Save raw JSON
json_out = f"housing_starts_{date.today()}.json"
with open(json_out, "w", encoding="utf-8") as f:
    import json
    json.dump(data, f, ensure_ascii=False, indent=2)

# Minimal printout
obs = data.get("observations", [])
if not obs:
    print("No data returned.")
    sys.exit(0)

last = obs[-1]
print(f"Series: {SERIES_ID} (Housing Starts, SAAR)")
print(f"Last date: {last['date']}  value: {last['value']} (thous. units, annual rate)")

# Optional: quick CSV & simple YoY / 3m avg using pandas
if pd:
    df = pd.DataFrame(obs)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df.to_csv(f"housing_starts_{date.today()}.csv", index=False)

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    df["3m_ma"] = df["value"].rolling(3).mean()
    df["yoy_pct"] = df["value"].pct_change(12) * 100

    tail = df[["value", "3m_ma", "yoy_pct"]].tail(3).round(2)
    print("\nRecent (value, 3m MA, YoY%):")
    print(tail.to_string())
else:
    print("\nTip: install pandas to save CSV and compute YoY/3m MA.")
print(f"\nSaved raw JSON to {json_out}")
