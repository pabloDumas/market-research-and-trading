#!/usr/bin/env python3
"""
Fetches both nominal (RSXFS) and real (RRSFS) U.S. retail sales
from FRED, computes MoM and YoY growth from inception to date,
and saves the merged dataset to CSV.

Env var required:
  export FRED_API_KEY="your_fred_api_key"
"""

import os, sys, requests
import pandas as pd
from datetime import date

API_KEY = os.getenv("FRED_API_KEY")
if not API_KEY:
    print("Set FRED_API_KEY env var first.", file=sys.stderr)
    sys.exit(1)

URL = "https://api.stlouisfed.org/fred/series/observations"
SERIES = {
    "RSXFS": "Nominal Retail Sales: Retail Trade and Food Services (SA, Mil USD)",
    "RRSFS": "Real Retail Sales: Retail and Food Services, 2017 Dollars (SA, Mil USD)"
}

def fetch_fred_series(series_id: str) -> pd.DataFrame:
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json"
    }
    r = requests.get(URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("observations", [])
    if not data:
        raise ValueError(f"No data returned for {series_id}")
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.set_index("date").sort_index()
    df.rename(columns={"value": series_id}, inplace=True)
    return df[[series_id]]

def compute_growth(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df[f"{col}_MoM_%"] = df[col].pct_change(1) * 100
    df[f"{col}_YoY_%"] = df[col].pct_change(12) * 100
    return df

def main():
    frames = []
    for sid, desc in SERIES.items():
        print(f"Fetching {sid}: {desc}")
        df = fetch_fred_series(sid)
        df = compute_growth(df, sid)
        frames.append(df)

    # merge by date
    merged = pd.concat(frames, axis=1)
    merged.index.name = "date"

    # Save CSV
    out_file = f"retail_sales_growth_dual_{date.today()}.csv"
    merged.to_csv(out_file, float_format="%.3f")
    print(f"\nSaved: {out_file}")
    print(f"From {merged.index[0].date()} → {merged.index[-1].date()}")
    print(merged.tail(5).round(3))

if __name__ == "__main__":
    main()
