import os
import requests
import pandas as pd

FRED_API_KEY = os.getenv("FRED_API_KEY")  # make sure this is set in your env

def fetch_fred_series(series_id: str,
                      start_date: str = "1900-01-01",
                      end_date: str = "9999-12-31") -> pd.DataFrame:
    """
    Fetch a FRED series as a pandas DataFrame from start_date to end_date.
    Dates are strings in YYYY-MM-DD format.
    """
    if FRED_API_KEY is None:
        raise RuntimeError("FRED_API_KEY environment variable is not set")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    obs = data.get("observations", [])
    if not obs:
        raise RuntimeError(f"No observations returned for series {series_id}")

    df = pd.DataFrame(obs)

    # Clean types
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Optional: keep just what you care about
    df = df[["date", "value"]].sort_values("date").reset_index(drop=True)

    return df


if __name__ == "__main__":
    # Corporate layoffs: Total Nonfarm, level (thousands), SA
    SERIES_ID = "JTSLDL"    # use "JTSLDR" if you want the rate instead

    df_layoffs = fetch_fred_series(
        series_id=SERIES_ID,
        start_date="2000-01-01",  # earlier than first obs is fine
        end_date="9999-12-31"
    )

    print(df_layoffs.head())
    print(df_layoffs.tail())

    # Save out for your research pipeline
    df_layoffs.to_csv("fred_layoffs_total_nonfarm_JTSLDL.csv", index=False)
