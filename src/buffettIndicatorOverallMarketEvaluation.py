import os
import requests
import pandas as pd

FRED_API_KEY = os.getenv("FRED_API_KEY")  # ensure set in environment

def fetch_fred_series(series_id: str,
                      start_date: str = "1900-01-01",
                      end_date: str = "9999-12-31") -> pd.DataFrame:
    """
    Generic FRED fetcher → returns DataFrame with [date, value]
    """
    if not FRED_API_KEY:
        raise RuntimeError("FRED_API_KEY environment variable not set.")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }

    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    obs = data.get("observations", [])
    if not obs:
        raise ValueError(f"No observations returned for series {series_id}")

    df = pd.DataFrame(obs)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[["date", "value"]].sort_values("date").reset_index(drop=True)
    return df


if __name__ == "__main__":
    # 1) Wilshire 5000 Total Market Index (proxy for Total Market Cap)
    SERIES_TMC = "WILL5000PRFC"  # working Wilshire 5000 series

    df_tmc = fetch_fred_series(
        series_id=SERIES_TMC,
        start_date="1970-01-01",
        end_date="2050-01-01"
    )
    df_tmc.to_csv("fred_total_market_cap_WILL5000INDFC.csv", index=False)
    print(df_tmc.head(), df_tmc.tail())


    # 2) Nominal GDP (SAAR)
    SERIES_GDP = "GDP"

    df_gdp = fetch_fred_series(
        series_id=SERIES_GDP,
        start_date="1947-01-01",
        end_date="9999-12-31"
    )
    df_gdp.to_csv("fred_nominal_gdp_GDP.csv", index=False)
    print(df_gdp.head(), df_gdp.tail())


    # 3) Optional — Compute the Buffett Indicator
    # Since GDP is QUARTERLY and Wilshire 5000 is MONTHLY, align by forward fill.
    df_combined = (df_tmc.set_index("date")
                          .join(df_gdp.set_index("date"), lsuffix="_tmc", rsuffix="_gdp")
                          .sort_index())

    df_combined["value_gdp"] = df_combined["value_gdp"].ffill()

    # Buffett Indicator = Total Market Cap / GDP
    df_combined["buffett_indicator"] = df_combined["value_tmc"] / df_combined["value_gdp"]

    df_combined.to_csv("buffett_indicator_history.csv")
    print(df_combined.tail())
