import os
import requests
import pandas as pd

def fetch_fred_series(series_id: str, api_key: str) -> pd.DataFrame:
    """
    Fetch a FRED time series and return as a pandas DataFrame with:
    - index: datetime
    - column: 'value' as float (NaNs where missing)
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        # Leave start_date/end_date off to get full history.
        # Alternatively: "start_date": "1900-01-01"
        "observation_start": "1900-01-01",
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    observations = data.get("observations", [])
    if not observations:
        raise RuntimeError(f"No observations returned for series {series_id}")

    df = pd.DataFrame(observations)[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    # FRED uses "." for missing values
    df["value"] = pd.to_numeric(df["value"].replace(".", pd.NA), errors="coerce")
    df = df.set_index("date").sort_index()

    return df

if __name__ == "__main__":
    # Expect your key in an env var, e.g. FRED_API_KEY
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set the FRED_API_KEY environment variable.")

    # VIX from FRED
    series_id = "VIXCLS"

    df_vix = fetch_fred_series(series_id, api_key)

    print("VIX head:")
    print(df_vix.head())
    print("\nVIX tail:")
    print(df_vix.tail())

    # Save to CSV
    out_path = "vix_fred_full_history.csv"
    df_vix.to_csv(out_path)
    print(f"\nSaved full VIX history to {out_path}")
