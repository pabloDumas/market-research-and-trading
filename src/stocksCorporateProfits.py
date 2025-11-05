# pip install fredapi pandas python-dotenv
import os
import pandas as pd
from fredapi import Fred

# Set your key first:
# export FRED_API_KEY=YOUR_KEY
fred = Fred(api_key=os.getenv("FRED_API_KEY"))

series_ids = ["CP", "CPNACO", "CPATAX", "CPROFIT", "CPFI", "CPNFI"]

df = pd.concat({sid: fred.get_series(sid) for sid in series_ids}, axis=1)
df.index.name = "date"
df = df.sort_index()

df.to_csv("corporate_profits_fred.csv")
print(df.tail())
