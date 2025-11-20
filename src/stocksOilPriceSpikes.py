import os
import requests
import pandas as pd


FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fred_series_full_history(series_id: str,
                                   api_key: str | None = None,
                                   units: str = "lin",
                                   frequency: str = "d") -> pd.DataFrame:
    """
    Fetch full-history data for a FRED series (e.g., DCOILWTICO for WTI crude).

    Parameters
    ----------
    series_id : str
        FRED series ID (e.g. 'DCOILWTICO', 'DCOILBRENTEU').
    api_key : str, optional
        FRED API key. If None, will read from FRED_API_KEY env var.
    units : str, optional
        FRED units parameter (default 'lin').
    frequency : str, optional
        FRED frequency parameter (default 'd' for daily).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: ['date', 'value'] and a DateTimeIndex.
    """
    if api_key is None:
        api_key = os.environ.get("FRED_API_KEY")

    if not api_key:
        raise RuntimeError(
            "FRED API key not found. "
            "Set FRED_API_KEY environment variable or pass api_key explicitly."
        )

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        # No observation_start / observation_end => full history
        "units": units,
        "frequency": frequency,
    }

    resp = requests.get(FRED_API_BASE, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "observations" not in data:
        raise RuntimeError(
            f"Unexpected response for {series_id}: keys={list(data.keys())}"
        )

    obs = data["observations"]
    df = pd.DataFrame(obs)

    # FRED returns 'date' and 'value' as strings
    df["date"] = pd.to_datetime(df["date"])
    # Some series use '.' for missing values; coerce to NaN then float
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.set_index("date").sort_index()

    return df


if __name__ == "__main__":
    # Example 1: WTI crude (Cushing, OK)
    wti_series_id = "DCOILWTICO"

    df_wti = fetch_fred_series_full_history(wti_series_id)
    print("WTI crude head():")
    print(df_wti.head())
    print("\nWTI crude tail():")
    print(df_wti.tail())

    # Save to CSV (full-history)
    df_wti.to_csv("DCOILWTICO_full_history.csv")

    # Example 2: Brent crude
    brent_series_id = "DCOILBRENTEU"
    df_brent = fetch_fred_series_full_history(brent_series_id)
    print("\nBrent crude head():")
    print(df_brent.head())
    df_brent.to_csv("DCOILBRENTEU_full_history.csv")
