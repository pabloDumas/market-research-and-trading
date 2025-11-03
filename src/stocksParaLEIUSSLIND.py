# pip install fredapi pandas
import os
import pandas as pd
from fredapi import Fred

# set your FRED API key in env first, e.g.:
#  export FRED_API_KEY=YOUR_KEY_HERE  (Linux/macOS)
#  setx FRED_API_KEY YOUR_KEY_HERE    (Windows)
fred = Fred(api_key=os.getenv("FRED_API_KEY"))

# Philadelphia Fed “Leading Index for the United States”
series_id = "USSLIND"
lei = fred.get_series(series_id)               # pandas Series (DateIndex)
lei = lei.to_frame(name=series_id)
print(lei.tail())

# Save to CSV
lei.to_csv("USSLIND_leading_index.csv", index_label="date")
