"""
pip install fredapi pandas
Env: FRED_API_KEY
"""
from fredapi import Fred
import os

fred = Fred(api_key=os.environ["FRED_API_KEY"])

def get_spread(series_id="BAMLC0A4CBBB"):
    s = fred.get_series(series_id)  # pandas Series indexed by date
    s.name = series_id
    return s

if __name__ == "__main__":
    s1 = get_spread("BAMLC0A4CBBB")  # ICE BofA BBB OAS
    s2 = get_spread("BAA10Y")        # Moody's Baa - 10Y Treasury
    print(s1.tail())
    print(s2.tail())
    s1.to_csv("BAMLC0A4CBBB.csv", header=True)
    s2.to_csv("BAA10Y.csv", header=True)
