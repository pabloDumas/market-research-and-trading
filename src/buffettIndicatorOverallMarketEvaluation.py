import os
import requests
import pandas as pd

FRED_API_KEY = os.getenv("FRED_API_KEY")


def fetch_fred_series(series_id: str,
                      start_date: str = "1900-01-01",
                      end_date: str | None = None) -> pd.DataFrame:
    """
    Generic FRED fetcher -> DataFrame[date, value]
    """
    if not FRED_API_KEY:
        raise RuntimeError("FRED_API_KEY environment variable is not set")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
    }
    if end_date is not None:
        params["observation_end"] = end_date

    resp = requests.get(url, params=params, timeout=20)
    # Helpful debug if FRED returns 400/404/etc.
    if not resp.ok:
        raise RuntimeError(
            f"FRED API error for {series_id}: {resp.status_code} {resp.reason}\n"
            f"URL: {resp.url}\n"
            f"Body: {resp.text}"
        )

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
    # === 1) Market cap proxy: Market Value of Equities Outstanding ===
    # Buffett's original style numerator (nonfinancial corporate business)
    SERIES_MCAP = "NCBEILQ027S"  # Millions of dollars, quarterly, NSA

    df_mcap = fetch_fred_series(
        series_id=SERIES_MCAP,
        start_date="1950-01-01"
    )
    df_mcap.rename(columns={"value": "mcap_millions"}, inplace=True)

    # === 2) Denominator: GNP (or GDP if you prefer) ===
    SERIES_GNP = "GNP"  # Billions of dollars, quarterly, SAAR

    df_gnp = fetch_fred_series(
        series_id=SERIES_GNP,
        start_date="1950-01-01"
    )
    df_gnp.rename(columns={"value": "gnp_billions"}, inplace=True)

    # === 3) Merge and compute Buffett Indicator ===
    df = (
        df_mcap.set_index("date")
        .join(df_gnp.set_index("date"), how="inner")
        .sort_index()
    )

    # Convert millions / billions to a unitless ratio
    # ratio = (millions) / (billions * 1000)
    df["buffett_ratio"] = df["mcap_millions"] / (df["gnp_billions"] * 1000.0)
    df["buffett_percent"] = df["buffett_ratio"] * 100.0

    # Optional: keep only the useful columns
    df_out = df[["mcap_millions", "gnp_billions", "buffett_ratio", "buffett_percent"]]
    df_out.reset_index(inplace=True)

    print(df_out.head())
    print(df_out.tail())

    df_out.to_csv("buffett_indicator_NCBEILQ027S_GNP.csv", index=False)
