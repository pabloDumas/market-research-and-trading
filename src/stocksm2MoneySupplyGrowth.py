import os
import pandas as pd
from fredapi import Fred

# 1️⃣ Set your API key
fred = Fred(api_key=os.environ.get("FRED_API_KEY"))

# 2️⃣ Fetch M2 Money Stock (Seasonally Adjusted, billions USD)
series_id = "M2SL"
data = fred.get_series(series_id)

# 3️⃣ Convert to DataFrame
df = pd.DataFrame(data, columns=["M2"])
df.index.name = "date"
df.reset_index(inplace=True)

# 4️⃣ Compute YoY % Growth and rename column
df["year_over_year_percent_M2"] = df["M2"].pct_change(periods=12) * 100

# 5️⃣ Save to CSV
csv_path = "M2_Money_Supply_Growth_Simplified.csv"
df.to_csv(csv_path, index=False)
print(f"Saved {csv_path}")

# 6️⃣ Display last 10 rows
print(df.tail(10))
