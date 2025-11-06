#!/usr/bin/env python3
import os
import sys
import json
import time
import argparse
from pathlib import Path

import requests
import pandas as pd
from requests.adapters import HTTPAdapter, Retry

# Default endpoint used by the page (paste your exact URL if different)
DEFAULT_ENDPOINT = "https://api.nasdaq.com/api/calendar/earnings"

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        # Realistic headers improve reliability with some CDNs
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nasdaq.com/market-activity/earnings",
        "Connection": "keep-alive",
    })
    retries = Retry(
        total=4,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

def fetch_json(endpoint: str, date_str: str) -> dict:
    """Fetch the JSON payload for a single date."""
    params = {"date": date_str}
    s = make_session()
    r = s.get(endpoint, params=params, timeout=30)
    # If blocked (403/429), slow down and retry once more explicitly
    if r.status_code in (403, 429):
        time.sleep(1.5)
        r = s.get(endpoint, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def rows_to_dataframe(payload: dict) -> pd.DataFrame:
    """
    Convert the nasdaq earnings JSON to a DataFrame.
    Expected shape: {"data": {"rows": [ ... ]}}
    """
    data = payload.get("data") or {}
    rows = data.get("rows") or []
    df = pd.DataFrame(rows)

    # Optional cleanup: strip $ and commas, convert to numeric for a few fields if present
    for col in ("marketCap", "epsForecast", "lastYearEPS"):
        if col in df.columns:
            # keep original columns too if you like; here we make numeric companions
            num_col = col + "_num"
            df[num_col] = (
                df[col]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
                .replace({"": None, "N/A": None, "—": None})
            )
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

    return df

def main():
    ap = argparse.ArgumentParser(description="Download Nasdaq earnings JSON and save CSV")
    ap.add_argument("--date", required=True, help="Date in YYYY-MM-DD (e.g., 2025-11-05)")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Full JSON endpoint (paste from DevTools if different)")
    ap.add_argument("--outbase", default="nasdaq_earnings", help="Base filename (without extension)")
    args = ap.parse_args()

    payload = fetch_json(args.endpoint, args.date)

    # Save raw JSON (audit trail)
    raw_path = Path(f"{args.outbase}_{args.date}.json")
    raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Parse into DataFrame
    df = rows_to_dataframe(payload)

    # Save CSV
    csv_path = Path(f"{args.outbase}_{args.date}.csv")
    df.to_csv(csv_path, index=False)

    # Small status print
    print(f"Saved raw JSON: {raw_path.resolve()}")
    print(f"Saved CSV     : {csv_path.resolve()}")
    print(f"Rows parsed   : {len(df)}")

if __name__ == "__main__":
    main()
