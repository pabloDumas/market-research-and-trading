# pip install nasdaqdatalink pandas
import os
import pandas as pd
import nasdaqdatalink as ndl

# set once:  os.environ["NASDAQ_DATA_LINK_API_KEY"] = "YOUR_KEY"
ndl.read_key()  # reads env var automatically

df = ndl.get("ISM/MAN_PMI")  # ISM Manufacturing PMI (Composite)
df = df.rename(columns={"PMI": "ISM_Manufacturing_PMI"})
print(df.head(), df.tail())

# save full history
df.to_csv("ism_manufacturing_pmi.csv", index_label="date")
