import os
import pandas as pd
from fredapi import Fred

# 1️⃣ Set your API key (use your own from https://fred.stlouisfed.org/docs/api/api_key.html)
fred = Fred(api_key=os.environ.get("FRED_API_KEY"))

# 2️⃣ Fetch M2 Money Stock (Seasonally Adjusted, billions USD)
series_id = "M2SL"  # M2 Money Stock
data = fred.get_series(series_id)

# 3️⃣ Convert to DataFrame
df = pd.DataFrame(data, columns=["M2"])
df.index.name = "date"
df.reset_index(inplace=True)

# 4️⃣ Compute YoY % Growth
df["yoy_pct"] = df["M2"].pct_change(periods=12) * 100

# 5️⃣ Add metadata
df["series_id"] = series_id
df["label"] = "M2 Money Stock (Seasonally Adjusted, billions USD)"

# 6️⃣ Save to CSV
csv_path = "M2_Money_Supply_Growth.csv"
df.to_csv(csv_path, index=False)
print(f"Saved {csv_path}")

# 7️⃣ Show recent data
print(df.tail(10))
