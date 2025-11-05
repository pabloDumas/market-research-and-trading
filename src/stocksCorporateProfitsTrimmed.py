import os
import pandas as pd
from fredapi import Fred

fred = Fred(api_key=os.environ["FRED_API_KEY"])

# Your original list (example)
series_ids = [
    # replace with yours
    "CPATAX",   # Corporate Profits After Tax (w/o IVA & CCAdj) – quarterly
    "A053RC1Q027SBEA",  # Corp profits with IVA & CCAdj – quarterly
    # "CPROFIT"  # ← example of a likely invalid code
]

# normalize
series_ids = [sid.strip().upper() for sid in series_ids]

valid = {}
invalid = []

for sid in series_ids:
    try:
        s = fred.get_series(sid)  # you can also pass observation_start=...
        if s is None or s.empty:
            invalid.append((sid, "exists but returned empty series"))
        else:
            valid[sid] = s
    except Exception as e:
        invalid.append((sid, str(e)))

if invalid:
    print("These series failed:")
    for sid, msg in invalid:
        print(f"  - {sid}: {msg}")

if valid:
    df = pd.concat(valid, axis=1)  # columns are series IDs
    df.index.name = "DATE"
    print("Combined shape:", df.shape)
    # After combining the series into df
    output_path = "corporate_profits_data.csv"
    df.to_csv(output_path, index=True)
    print(f"✅ Data saved to {output_path} ({len(df)} rows).")
