import os
import requests
import pandas as pd


TE_HISTORICAL_BASE = "https://api.tradingeconomics.com/historical"


def fetch_global_composite_pmi_full_history(
    api_key: str | None = None,
    country: str = "world",
    indicator: str = "composite pmi",
) -> pd.DataFrame:
    """
    Fetch full-history JPMorgan / S&P Global Global Composite PMI
    from TradingEconomics.

    Parameters
    ----------
    api_key : str, optional
        TradingEconomics API key. If None, will read from
        TRADING_ECONOMICS_API_KEY env var.
        (Format is usually 'user:password' or a single token.)
    country : str, optional
        Country parameter for TE. For global PMI, use 'world'.
    indicator : str, optional
        Indicator name. For global composite PMI, use 'composite pmi'.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: ['value'] and a DateTimeIndex.
        Frequency is typically monthly.
    """
    if api_key is None:
        api_key = os.environ.get("TRADING_ECONOMICS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "TradingEconomics API key not found. "
            "Set TRADING_ECONOMICS_API_KEY or pass api_key explicitly."
        )

    # Build URL like:
    # https://api.tradingeconomics.com/historical/country/world/indicator/composite%20pmi?c=YOUR_KEY
    url = (
        f"{TE_HISTORICAL_BASE}/country/"
        f"{country.lower().replace(' ', '%20')}/indicator/"
        f"{indicator.lower().replace(' ', '%20')}"
        f"?c={api_key}"
    )

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if not isinstance(data, list) or len(data) == 0:
        raise RuntimeError(
            f"Unexpected response for Global Composite PMI: {data!r}"
        )

    df = pd.DataFrame(data)

    # TE fields: 'DateTime' and 'Value' are the ones we care about
    if "DateTime" not in df or "Value" not in df:
        raise RuntimeError(
            f"Missing expected fields in response: {df.columns.tolist()}"
        )

    df["date"] = pd.to_datetime(df["DateTime"])
    df["value"] = pd.to_numeric(df["Value"], errors="coerce")

    df = df[["date", "value"]].set_index("date").sort_index()

    return df


if __name__ == "__main__":
    df_global_pmi = fetch_global_composite_pmi_full_history()
    print("Global Composite PMI head():")
    print(df_global_pmi.head())
    print("\nGlobal Composite PMI tail():")
    print(df_global_pmi.tail())

    # Save full history to CSV
    df_global_pmi.to_csv("global_composite_pmi_full_history.csv")
