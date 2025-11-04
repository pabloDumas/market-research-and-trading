# pip install fredapi pandas
import os
import pandas as pd
from fredapi import Fred

# Set your key first: export FRED_API_KEY=YOUR_KEY
fred = Fred(api_key=os.getenv("FRED_API_KEY"))

# University of Michigan: Consumer Sentiment (proxy for "consumer confidence")
df = fred.get_series("UMCSENT").to_frame(name="umich_consumer_sentiment")
df.index.name = "date"

# (Optional) pre-1978 history is also available on FRED via UMCSENT1 notes
df.sort_index().to_csv("consumer_sentiment_umich_fred.csv")
print(df.tail())
