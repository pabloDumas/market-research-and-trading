import pandas as pd

url = "https://www.econ.yale.edu/~shiller/data/ie_data.xls"

# 1. Read the Excel file (sheet "Data"), no header row
data = pd.read_excel(url, sheet_name="Data", header=None)

# 2. Drop the top text rows and some unused columns
data = data.drop(data.index[:7]).reset_index(drop=True)
data = data.drop(columns=[1, 14, 16])

# 3. Give the columns proper names (Shiller layout)
data.columns = [
    "Date", "S&P Comp", "Dividend", "Earnings", "Consumer Price CPI",
    "Date Fraction", "Long Interest Rate", "Real price", "Real Dividend",
    "Real Total Return Price", "Real Earnings", "Real TR Scaled Earnings",
    "CAPE", "TR CAPE", "Excess CAPE Yield", "Monthly Total Bond Returns",
    "Real Total Bond Returns", "10Y Stock Real Return",
    "10Y Bonds Real Return", "Real 10Y Excess Return"
]

# 4. Build proper monthly dates from Shiller's "YYYY.MM" format
date_str = data["Date"].astype(str)        # e.g. '1881.01'
year  = date_str.str.slice(0, 4)
month = date_str.str.slice(5, 7)
data["Date"] = pd.to_datetime(year + "-" + month + "-01", errors="coerce")

# 5. Keep only valid rows and the CAPE series
cape_df = data.loc[data["Date"].notna(), ["Date"]].copy()
cape_df["cape_shiller_pe"] = pd.to_numeric(data["CAPE"], errors="coerce")

# 6. Save to CSV
cape_df.to_csv("cape_shiller_pe_full_history.csv", index=False)
