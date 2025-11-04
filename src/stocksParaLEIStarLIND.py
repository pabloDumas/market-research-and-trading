# pip install fredapi pandas
from fredapi import Fred
import pandas as pd
import os

fred = Fred(api_key=os.getenv("FRED_API_KEY"))

# State series are like 'PAsLIND', 'TXSLIND', etc. FRED also provides a master list.
# If you already know the tickers, list them; otherwise, quick manual subset example:
states = [
    "ALSLIND", "AKSLIND", "AZSLIND", "ARSLIND", "CASLIND",
    "COSLIND", "CTSLIND", "DESLIND", "DCSLIND", "FLSLIND",
    "GASLIND", "HISLIND", "IDSLIND", "ILSLIND", "INSLIND",
    "IASLIND", "KSSLIND", "KYSLIND", "LASLIND", "MESLIND",
    "MDESLIND", "MASLIND", "MISLIND", "MNESLIND", "MSSLIND",
    "MOSLIND", "MTSLIND", "NESLIND", "NVSLIND", "NHSLIND",
    "NJSLIND", "NMESLIND", "NYSLIND", "NCESLIND", "NDESLIND",
    "OHSLIND", "OKSLIND", "ORESLIND", "PASLIND", "RISLIND",
    "SCESLIND", "SDESLIND", "TNESLIND", "TXSLIND", "UTSLIND",
    "VTSLIND", "VASLIND", "WASLIND", "WVSLIND", "WISLIND", "WYSLIND"
]


df = pd.concat({sid: fred.get_series(sid) for sid in states}, axis=1)
df.to_csv("state_leading_indexes.csv", index_label="date")
print(df.tail())
