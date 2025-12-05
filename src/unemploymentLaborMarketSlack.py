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
        "observation_start": "1900-01-01",  # effectively 'full history'
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
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set the FRED_API_KEY environment variable.")

    # Sahm Rule Recession Indicator – labor market slack trigger
    # Units: percentage points (3m avg U3 minus 12m low, monthly)
    series_id = "SAHMCURRENT"      # or "SAHMREALTIME" for real-time vintages

    df_sahm = fetch_fred_series(series_id, api_key)

    print("Sahm Rule (labor slack) head:")
    print(df_sahm.head())
    print("\nSahm Rule (labor slack) tail:")
    print(df_sahm.tail())

    out_path = "sahm_rule_labor_slack_full_history.csv"
    df_sahm.to_csv(out_path)
    print(f"\nSaved Sahm Rule / labor slack history to {out_path}")
