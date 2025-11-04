# pip install tradingeconomics pandas
import os
import pandas as pd
import tradingeconomics as te

# Set API key in environment first or directly:
# os.environ["TE_API_KEY"] = "ae506d41ded8410:nnfhnxpqf5322ca"

te.login(os.getenv("TE_API_KEY"))

# Option 1: direct historical pull for the indicator
pmi = te.getHistoricalData(
    country='United States',
    indicator='ISM Manufacturing PMI',
    output_type='df'
)

# Clean and save
pmi = pmi[['DateTime', 'Value']].rename(columns={'DateTime': 'date', 'Value': 'pmi'}).sort_values('date')
print(pmi.head(), "\n", pmi.tail())

pmi.to_csv('ism_manufacturing_pmi_tradingeconomics.csv', index=False)
