import os
import requests
import pandas as pd


FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fred_series_full_history(series_id: str,
                                   api_key: str | None = None,
                                   units: str = "lin",
                                   frequency: str = "q") -> pd.DataFrame:
    """
    Fetch full-history data for a FRED series (e.g., DRCCLACBS for credit card delinquencies).

    Parameters
    ----------
    series_id : str
        FRED series ID (e.g. 'DRCCLACBS').
    api_key : str, optional
        FRED API key. If None, will read from FRED_API_KEY env var.
    units : str, optional
        FRED units parameter (default 'lin').
    frequency : str, optional
        FRED frequency parameter. For delinquencies, native is 'q' (quarterly).

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
        # no observation_start / observation_end => full history
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
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.set_index("date").sort_index()

    return df


if __name__ == "__main__":
    # Credit Card Delinquency Rate, all commercial banks
    cc_delinquencies_series_id = "DRCCLACBS"

    df_cc = fetch_fred_series_full_history(cc_delinquencies_series_id)
    print("Credit card delinquency rate (head):")
    print(df_cc.head())
    print("\nCredit card delinquency rate (tail):")
    print(df_cc.tail())

    # Save full history to CSV
    df_cc.to_csv("DRCCLACBS_credit_card_delinquencies_full_history.csv")
