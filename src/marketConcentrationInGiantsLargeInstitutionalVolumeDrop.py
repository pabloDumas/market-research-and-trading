import os
import requests
import pandas as pd

FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fred_series_full_history(
    series_id: str,
    api_key: str | None = None,
    units: str = "lin",
) -> pd.DataFrame:
    """
    Fetch full-history data for a FRED series (native frequency).

    Parameters
    ----------
    series_id : str
        FRED series ID (e.g. 'DDAM01USA156NWDB').
    api_key : str, optional
        FRED API key. If None, will read from FRED_API_KEY env var.
    units : str, optional
        FRED 'units' transform (default 'lin' = linear / no transform).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['value'] and a DateTimeIndex named 'date'.
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
        "units": units,
        # no observation_start / observation_end => full history
    }

    resp = requests.get(FRED_API_BASE, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "observations" not in data:
        raise RuntimeError(
            f"Unexpected response for {series_id}: keys={list(data.keys())}"
        )

    df = pd.DataFrame(data["observations"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.set_index("date").sort_index()[["value"]]

    return df


if __name__ == "__main__":
    # 1) Market Concentration in Giants (Top 10 traded vs total)
    # Value Traded of Top 10 Traded Companies to Total Value Traded, U.S.
    giants_concentration_id = "DDAM01USA156NWDB"
    df_giants_conc = fetch_fred_series_full_history(giants_concentration_id)
    print("Top-10 traded concentration (head):")
    print(df_giants_conc.head())
    print("\nTop-10 traded concentration (tail):")
    print(df_giants_conc.tail())

    df_giants_conc.to_csv(
        f"{giants_concentration_id}_giants_market_concentration_full_history.csv"
    )

    # 2) Stock Market Turnover Ratio (proxy for volume intensity)
    # Stock Market Turnover Ratio (Value Traded / Capitalization), U.S.
    turnover_ratio_id = "DDEM01USA156NWDB"
    df_turnover = fetch_fred_series_full_history(turnover_ratio_id)
    print("\nStock market turnover ratio (head):")
    print(df_turnover.head())
    print("\nStock market turnover ratio (tail):")
    print(df_turnover.tail())

    df_turnover.to_csv(
        f"{turnover_ratio_id}_stock_market_turnover_full_history.csv"
    )
