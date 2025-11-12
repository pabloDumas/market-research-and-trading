# pip install yfinance pandas requests bs4
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup

# -----------------------------
# 1) Get ticker lists
# -----------------------------
def get_sp500():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    html = requests.get(url).text
    df = pd.read_html(html)[0]
    return df["Symbol"].tolist()

def get_nasdaq100():
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    html = requests.get(url).text
    tables = pd.read_html(html)
    df = tables[4]  # holdings table
    return df["Ticker"].tolist()

# Choose your index:
INDEX = "sp500"  # or "nasdaq100"

if INDEX == "sp500":
    tickers = get_sp500()
elif INDEX == "nasdaq100":
    tickers = get_nasdaq100()
else:
    tickers = []

# -----------------------------
# 2) Compute earnings revisions ratio per ticker
# -----------------------------
def earnings_revision_ratio(symbol):
    try:
        tkr = yf.Ticker(symbol)
        trend = tkr.get_earnings_trend()

        if not trend or "trend" not in trend:
            return None, 0, 0

        latest = trend["trend"][0]
        rev = latest.get("epsRevisions", {})

        up = rev.get("upLast30days", 0) or 0
        down = rev.get("downLast30days", 0) or 0

        total = up + down
        if total == 0:
            return None, up, down

        ratio = (up - down) / total
        return ratio, up, down

    except Exception:
        return None, 0, 0


# -----------------------------
# 3) Loop through universe
# -----------------------------
rows = []
total_up = 0
total_down = 0

for sym in tickers:
    ratio, up, down = earnings_revision_ratio(sym)
    total_up += up
    total_down += down

    rows.append({
        "symbol": sym,
        "up_last_30d": up,
        "down_last_30d": down,
        "revision_ratio": ratio
    })

df = pd.DataFrame(rows)

# -----------------------------
# 4) Index-level aggregate revision ratio
# -----------------------------
if (total_up + total_down) > 0:
    index_ratio = (total_up - total_down) / (total_up + total_down)
else:
    index_ratio = None

print(f"\nIndex: {INDEX.upper()}")
print(f"Total Upgrades (30d): {total_up}")
print(f"Total Downgrades (30d): {total_down}")
print(f"Index-Level Earnings Revisions Ratio: {index_ratio}\n")

# -----------------------------
# 5) Export CSV
# -----------------------------
df.to_csv(f"{INDEX}_earnings_revisions.csv", index=False)
print("Saved:", f"{INDEX}_earnings_revisions.csv")
