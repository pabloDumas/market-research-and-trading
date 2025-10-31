# pip install pandas pandas_datareader
import pandas as pd
from pandas_datareader import data as pdr
from datetime import date

START = "1960-01-01"
END = None  # today
OUTFILE = f"yield_curve_spreads_1960_to_{date.today().isoformat()}.csv"

# FRED series (no API key needed with pandas_datareader):
# DGS10  = 10-Year Treasury Constant Maturity
# DGS2   = 2-Year Treasury Constant Maturity
# DGS3MO = 3-Month Treasury Bill
series = ["DGS10", "DGS2", "DGS3MO"]
df = pdr.DataReader(series, "fred", START, END)

# Ensure numeric and forward-fill non-trading days (weekends/holidays)
df = df.astype(float).ffill()

# Spreads (percentage points)
df["spr_10y_2y"] = df["DGS10"] - df["DGS2"]
df["spr_10y_3m"] = df["DGS10"] - df["DGS3MO"]

# Inversion flags (True if spread < 0); keep NaN where data is missing
df["inv_10y_2y"] = df["spr_10y_2y"].lt(0).where(df["spr_10y_2y"].notna())
df["inv_10y_3m"] = df["spr_10y_3m"].lt(0).where(df["spr_10y_3m"].notna())

# Save full history since 1960
df.to_csv(OUTFILE, index_label="date")
print(f"✅ Saved CSV with {len(df):,} rows → {OUTFILE}")
