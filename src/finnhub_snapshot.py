# ./src/finnhub_snapshot.py
"""
Append Finnhub spot prices for AAPL and GOOG to a running CSV.

CSV columns: date_time_utc, ticker, value

Designed for GitHub Actions:
- Workflow can run frequently (e.g., every 5–10 minutes)
- Script will ONLY write at these NYSE-session boundary instants (America/New_York):
    1) premarket_open  = 04:00 ET
    2) premarket_close = 09:30 ET (regular session opens)
    3) regular_close   = 16:00 ET
    4) postmarket_close= 20:00 ET
It also deduplicates so you get at most 4 writes per trading day.
"""

from __future__ import annotations

import csv
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, time
from zoneinfo import ZoneInfo

import requests

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
if not FINNHUB_API_KEY:
    print("ERROR: FINNHUB_API_KEY env var not set.", file=sys.stderr)
    sys.exit(2)

TICKERS = ["AAPL", "GOOG"]
OUT_CSV = os.getenv("OUT_CSV", "./outputs/finnhub_quotes.csv")

ET = ZoneInfo("America/New_York")

# Write window: if the workflow runs more than once around the boundary,
# we only allow writes within N minutes after the target time.
WINDOW_MINUTES = int(os.getenv("WINDOW_MINUTES", "3"))


@dataclass(frozen=True)
class Target:
    name: str
    et_time: time


TARGETS = [
    Target("premarket_open", time(4, 0)),
    Target("premarket_close", time(9, 30)),
    Target("regular_close", time(16, 0)),
    Target("postmarket_close", time(20, 0)),
]


def finnhub_quote(symbol: str) -> float:
    url = "https://finnhub.io/api/v1/quote"
    r = requests.get(url, params={"symbol": symbol, "token": FINNHUB_API_KEY}, timeout=15)
    r.raise_for_status()
    data = r.json()
    # "c" = current price
    c = data.get("c")
    if c in (None, 0):
        raise ValueError(f"Finnhub quote missing/zero for {symbol}: {data}")
    return float(c)


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def already_logged(date_et: str, target_name: str, ticker: str) -> bool:
    """
    Deduplicate by (ET trading-date, target_name, ticker).
    We store target_name in the CSV as an extra hidden tag by encoding it in datetime string:
        date_time_utc includes suffix "|<target_name>" in the file.
    This keeps the user's requested columns while remaining dedupe-capable.
    """
    if not os.path.exists(OUT_CSV):
        return False

    needle_suffix = f"|{target_name}"
    with open(OUT_CSV, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = (row.get("date_time_utc") or "").strip()
            if not dt.endswith(needle_suffix):
                continue
            if (row.get("ticker") or "").strip() != ticker:
                continue
            # Compare ET date for safety
            try:
                # dt is ISO UTC with suffix; strip suffix then parse
                dt_iso = dt.split("|", 1)[0]
                dt_utc = datetime.fromisoformat(dt_iso.replace("Z", "+00:00"))
                dt_et = dt_utc.astimezone(ET)
                if dt_et.date().isoformat() == date_et:
                    return True
            except Exception:
                continue
    return False


def current_target(now_et: datetime) -> Target | None:
    # Skip weekends
    if now_et.weekday() >= 5:
        return None

    for t in TARGETS:
        target_dt = now_et.replace(
            hour=t.et_time.hour,
            minute=t.et_time.minute,
            second=0,
            microsecond=0,
        )
        delta_min = (now_et - target_dt).total_seconds() / 60.0
        if 0 <= delta_min <= WINDOW_MINUTES:
            return t
    return None


def append_rows(rows: list[dict]) -> None:
    ensure_parent_dir(OUT_CSV)
    file_exists = os.path.exists(OUT_CSV)

    with open(OUT_CSV, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["date_time_utc", "ticker", "value"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for row in rows:
            writer.writerow(row)


def main() -> int:
    now_utc = datetime.now(timezone.utc)
    now_et = now_utc.astimezone(ET)

    tgt = current_target(now_et)
    if tgt is None:
        print("Not within a target window; nothing to write.")
        return 0

    date_et = now_et.date().isoformat()
    rows = []

    for ticker in TICKERS:
        if already_logged(date_et, tgt.name, ticker):
            print(f"Already logged {ticker} for {date_et} {tgt.name}; skipping.")
            continue

        price = finnhub_quote(ticker)

        # Store UTC timestamp, and append a suffix tag for internal dedupe.
        # Example: 2025-12-23T21:30:01Z|regular_close
        dt_tagged = now_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z") + f"|{tgt.name}"

        rows.append(
            {
                "date_time_utc": dt_tagged,
                "ticker": ticker,
                "value": f"{price:.4f}",
            }
        )

    if not rows:
        print("Nothing new to append.")
        return 0

    append_rows(rows)
    print(f"Appended {len(rows)} row(s) for target={tgt.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
