import os
import requests
import pandas as pd

def fetch_fred_series(series_id: str, api_key: str) -> pd.DataFrame:
    """
    Fetch a FRED time series and return as a pandas DataFrame with:
    - index: datetime
    - column: 'value' as float
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": "1900-01-01",   # inception
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    observations = data.get("observations", [])
    if not observations:
        raise RuntimeError(f"No observations returned for series {series_id}")

    df = pd.DataFrame(observations)[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"].replace(".", pd.NA), errors="coerce")
    df = df.set_index("date").sort_index()

    return df

if __name__ == "__main__":
    # your API key from environment variables
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set the FRED_API_KEY environment variable.")

    # AUTO SALES (TOTALSA)
    series_id = "TOTALSA"

    df_auto = fetch_fred_series(series_id, api_key)

    print("Auto Sales head:")
    print(df_auto.head())
    print("\nAuto Sales tail:")
    print(df_auto.tail())

    # Save to CSV
    out_path = "auto_sales_fred_full_history.csv"
    df_auto.to_csv(out_path)
    print(f"\nSaved full Auto Sales history to {out_path}")
