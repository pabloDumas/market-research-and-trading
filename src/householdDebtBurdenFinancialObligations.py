import os
import requests
import pandas as pd

FRED_API_KEY = os.getenv("FRED_API_KEY")

def fetch_fred_series(series_id: str,
                      start_date: str = "1900-01-01",
                      end_date: str = "9999-12-31") -> pd.DataFrame:
    if not FRED_API_KEY:
        raise RuntimeError("FRED_API_KEY environment variable not set")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    obs = data.get("observations", [])
    if not obs:
        raise RuntimeError(f"No observations for series {series_id}")

    df = pd.DataFrame(obs)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[["date", "value"]].sort_values("date").reset_index(drop=True)
    return df

if __name__ == "__main__":
    # Debt Service Ratio series
    SERIES_DSR = "TDSP"
    df_dsr = fetch_fred_series(series_id=SERIES_DSR,
                               start_date="1980-01-01",
                               end_date="9999-12-31")
    print(df_dsr.head(), df_dsr.tail())
    df_dsr.to_csv("fred_household_debt_service_ratio_TDSP.csv", index=False)

    # Financial Obligations Ratio series (discontinued beyond 2023-Q3)
    SERIES_FOR = "FODSP"
    df_for = fetch_fred_series(series_id=SERIES_FOR,
                               start_date="1980-01-01",
                               end_date="9999-12-31")
    print(df_for.head(), df_for.tail())
    df_for.to_csv("fred_household_financial_obligations_ratio_FODSP.csv", index=False)
