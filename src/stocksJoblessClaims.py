series_ids = [
    # --- Initial Claims ---
    "ICSA",    # Initial Claims, Seasonally Adjusted (main)
    "ICNSA",   # Initial Claims, Not Seasonally Adjusted
    "IC4WSA",  # 4-Week Moving Average of Initial Claims, SA

    # --- Continued Claims ---
    "CCSA",    # Continued Claims (Insured Unemployment), SA
    "CCNSA",   # Continued Claims, Not Seasonally Adjusted

    # --- Insured Unemployment Rate ---
    "IURSA",   # Insured Unemployment Rate, SA
    "IURNSA",  # Insured Unemployment Rate, NSA
]
# pip install fredapi pandas
import os
import pandas as pd
from fredapi import Fred

fred = Fred(api_key=os.getenv("FRED_API_KEY"))
df = pd.concat({sid: fred.get_series(sid) for sid in series_ids}, axis=1)
df.index.name = "date"
df = df.sort_index()
df.to_csv("jobless_claims_all_fred.csv")
print(df.tail())
