import os
import pandas as pd
from fredapi import Fred
from datetime import datetime
from dotenv import load_dotenv

# ============================================================
# 1) CONFIG
# ============================================================

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise RuntimeError("Set FRED_API_KEY in your environment or .env file.")

fred = Fred(api_key=FRED_API_KEY)

# Index series IDs (FRED)
# SP500: S&P 500 Index (price) – daily
# WILL5000INDFC: Wilshire 5000 Total Market Full Cap Index (value) – daily (may be removed; swap if needed)
SP500_SERIES = "SP500"
BROAD_SERIES = "DJSUPER"   # Broad U.S. total-market index (valid on FRED)

START_DATE = "1990-01-01"  # adjust as desired
END_DATE = None            # None = latest

# ============================================================
# 2) FETCH DATA FROM FRED
# ============================================================

print(f"Fetching {SP500_SERIES} from FRED...")
sp500 = fred.get_series(SP500_SERIES, observation_start=START_DATE, observation_end=END_DATE)

print(f"Fetching {BROAD_SERIES} from FRED...")
try:
    broad = fred.get_series(BROAD_SERIES, observation_start=START_DATE, observation_end=END_DATE)
except Exception as e:
    raise RuntimeError(
        f"Failed to fetch broad index series '{BROAD_SERIES}' from FRED. "
        f"Try replacing BROAD_SERIES with another broad US equity series ID. "
        f"Original error: {e}"
    )

# Put into one DataFrame and align dates
df = pd.concat([sp500, broad], axis=1)
df.columns = ["SP500", "BROAD"]
df = df.dropna()

if df.empty:
    raise RuntimeError("No overlapping data between SP500 and BROAD series after dropna().")

# ============================================================
# 3) NORMALIZE & COMPUTE BREADTH PROXY
# ============================================================

# Normalize to 100 at first common date
df["SP500_norm"] = df["SP500"] / df["SP500"].iloc[0] * 100.0
df["BROAD_norm"] = df["BROAD"] / df["BROAD"].iloc[0] * 100.0

# Breadth ratio: broad-market vs large-cap
# > 1  → broad market outperforming SP500 → stronger breadth
# < 1  → SP500 outperforming broad market → narrow / mega-cap driven
df["breadth_ratio"] = df["BROAD_norm"] / df["SP500_norm"]

# Rolling z-score of breadth_ratio (optional, for extremes)
window = 60  # ~3 months of trading days
df["breadth_ratio_z"] = (
    df["breadth_ratio"] - df["breadth_ratio"].rolling(window).mean()
) / df["breadth_ratio"].rolling(window).std()

df = df.dropna()

# ============================================================
# 4) SUMMARY & OUTPUT
# ============================================================

latest_date = df.index[-1].date()
latest = df.iloc[-1]

print("\n==================== FRED EQUITY BREADTH PROXY ====================")
print(f"As of {latest_date}:")
print(f"SP500_norm       : {latest['SP500_norm']:.2f}")
print(f"BROAD_norm       : {latest['BROAD_norm']:.2f}")
print(f"Breadth ratio    : {latest['breadth_ratio']:.4f}  (BROAD / SP500)")
print(f"Breadth z-score  : {latest['breadth_ratio_z']:.2f}  (60-day)")

if latest["breadth_ratio"] > 1.0:
    print("Interpretation    : Broad market has outperformed SP500 since start date → stronger breadth.")
else:
    print("Interpretation    : SP500 has outperformed the broad market → narrower, large-cap-led market.")

print("\nData sample (head):")
print(df[["SP500", "BROAD", "SP500_norm", "BROAD_norm", "breadth_ratio"]].head())

# Save to CSV
out_name = f"fred_equity_breadth_proxy_{latest_date}.csv"
df.to_csv(out_name, index_label="date")
print(f"\nSaved full breadth time series to: {out_name}")
