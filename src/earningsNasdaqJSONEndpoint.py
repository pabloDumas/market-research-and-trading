#!/usr/bin/env python3
import os, sys, json, time, argparse
from pathlib import Path
from datetime import date, datetime, timedelta

import requests
import pandas as pd
from requests.adapters import HTTPAdapter, Retry

DEFAULT_ENDPOINT = "https://api.nasdaq.com/api/calendar/earnings"

# ---------- HTTP session ----------
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nasdaq.com/market-activity/earnings",
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
    s = make_session()
    r = s.get(endpoint, params={"date": date_str}, timeout=30)
    if r.status_code in (403, 429):
        time.sleep(1.5)
        r = s.get(endpoint, params={"date": date_str}, timeout=30)
    r.raise_for_status()
    return r.json()

# ---------- Parsing ----------
def rows_to_dataframe(payload: dict) -> pd.DataFrame:
    data = payload.get("data") or {}
    rows = data.get("rows") or []
    df = pd.DataFrame(rows)

    # Numeric helpers
    def to_num(series):
        return (
            series.astype(str)
                  .str.replace("$", "", regex=False)
                  .str.replace(",", "", regex=False)
                  .str.replace("%", "", regex=False)
                  .str.strip()
                  .replace({"": None, "N/A": None, "—": None, "NaN": None})
                  .pipe(pd.to_numeric, errors="coerce")
        )

    # Create numeric companions if present
    if "epsForecast" in df.columns:
        df["epsForecast_num"] = to_num(df["epsForecast"])
    if "lastYearEPS" in df.columns:
        df["lastYearEPS_num"] = to_num(df["lastYearEPS"])
    if "noOfEsts" in df.columns:
        df["noOfEsts_num"] = to_num(df["noOfEsts"])

    return df

# ---------- Date utilities ----------
def business_days(start_dt: date, end_dt: date):
    # Inclusive business days (Mon–Fri)
    days = pd.bdate_range(start=start_dt, end=end_dt).date
    return [d.isoformat() for d in days]

def next_week_business_days(today: date | None = None):
    if today is None:
        today = date.today()
    # Find next Monday
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_monday = today + timedelta(days=days_ahead)
    next_friday = next_monday + timedelta(days=4)
    return business_days(next_monday, next_friday)

# ---------- Main workflow ----------
def main():
    # --- argparse ---
    ap = argparse.ArgumentParser(description="Nasdaq earnings -> CSV with EPS ratio and filters")
    g = ap.add_mutually_exclusive_group(required=False)  # <-- was True
    g.add_argument("--date", help="Single date YYYY-MM-DD")
    g.add_argument("--start", help="Start date YYYY-MM-DD (business days only)")
    ap.add_argument("--end", help="End date YYYY-MM-DD (required when --start is used)")
    ap.add_argument("--next-week", action="store_true",
                    help="Fetch next week's Mon–Fri business days automatically")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                    help="JSON endpoint (paste from DevTools if different)")
    ap.add_argument("--out-raw", default="nasdaq_earnings_all.csv",
                help="CSV path for the unfiltered concatenated DataFrame (before drops/sorts)")
    ap.add_argument("--out", default="nasdaq_earnings_processed.csv",
                    help="Output CSV filename")
    args = ap.parse_args()
    
    # --- resolve date list ---
    if args.next_week:
        dates = next_week_business_days()
    elif args.date:
        dates = [args.date]
    elif args.start:
        if not args.end:
            ap.error("--end is required when --start is provided")
        start_dt = date.fromisoformat(args.start)
        end_dt = date.fromisoformat(args.end)
        dates = business_days(start_dt, end_dt)
    else:
        ap.error("Provide --next-week OR --date YYYY-MM-DD OR --start YYYY-MM-DD --end YYYY-MM-DD")

    # Fetch & concat
    frames = []
    for d in dates:
        try:
            payload = fetch_json(args.endpoint, d)
        except Exception as e:
            print(f"[warn] {d}: fetch error: {e}", file=sys.stderr)
            continue
        df = rows_to_dataframe(payload)
        if not df.empty:
            df["queryDate"] = d  # keep the date we asked for
            frames.append(df)

    if not frames:
        print("No data found for requested dates.")
        sys.exit(0)

    df_all = pd.concat(frames, ignore_index=True)
    
    # ---- Make a copy and compute ratio
    out_df = df_all.copy()

    # Drop rows where # of estimates <= 5
    if "noOfEsts_num" in out_df.columns:
        out_df = out_df[out_df["noOfEsts_num"] > 5]

    # Compute ratio: epsForecast_num / lastYearEPS_num
    if {"epsForecast_num", "lastYearEPS_num"} <= set(out_df.columns):
        out_df["eps_ratio"] = out_df["epsForecast_num"] / out_df["lastYearEPS_num"]
    else:
        out_df["eps_ratio"] = pd.NA

    # Sort descending on eps_ratio (NaNs last)
    out_df = out_df.sort_values(by="eps_ratio", ascending=False, na_position="last")
    
    # Determine date range strings for filenames
    range_start = min(dates)
    range_end   = max(dates)
    range_tag   = f"{range_start}_to_{range_end}"
    
    # === Save the ORIGINAL, unfiltered DataFrame ===
    raw_path = Path(f"{Path(args.out_raw).stem}_{range_tag}{Path(args.out_raw).suffix}")
    df_all.to_csv(raw_path, index=False, encoding="utf-8")
    print(f"Saved raw/unfiltered CSV: {raw_path.resolve()}")
    
    # === Filtered, processed version ===
    out_path = Path(f"{Path(args.out).stem}_{range_tag}{Path(args.out).suffix}")
    out_df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Saved processed CSV     : {out_path.resolve()}")
    print(f"Rows (after filter)     : {len(out_df)}")


if __name__ == "__main__":
    main()
