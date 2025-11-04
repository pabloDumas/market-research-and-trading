# pip install tradingeconomics pandas
import os
import pandas as pd
import tradingeconomics as te

# set once: os.environ["TE_API_KEY"] = "guest:guest"  # replace with your key:secret
te.login(os.getenv("TE_API_KEY"))

# Pull indicator -> returns DataFrame with historical values
pmi = te.getIndicatorData(country="United States",
                          indicator="ISM Manufacturing PMI",
                          output_type="df")

# keep just date/value, sort ascending
pmi = pmi[["DateTime", "Value"]].rename(columns={"DateTime":"date","Value":"pmi"}).sort_values("date")
print(pmi.head(), pmi.tail())
pmi.to_csv("ism_manufacturing_pmi_tradingeconomics.csv", index=False)
