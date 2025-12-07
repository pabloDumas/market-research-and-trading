import pandas as pd


def fetch_shiller_cape() -> pd.DataFrame:
    """
    Fetch Shiller CAPE / PE10 from Robert Shiller's Yale data file.

    Returns:
        DataFrame indexed by datetime with one column:
        - 'cape_shiller_pe' (float)
    """
    # Official Shiller data file (includes monthly S&P, earnings, CAPE, etc.)
    url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"

    # Read once without header to locate the real header row dynamically
    raw = pd.read_excel(url, sheet_name="Data", header=None)

    # Find the row that contains the column name 'Date' in the first column
    header_row_candidates = raw.index[raw.iloc[:, 0] == "Date"]
    if len(header_row_candidates) == 0:
        raise RuntimeError("Could not find header row with 'Date' in Shiller file.")
    header_row = header_row_candidates[0]

    # Re-read using that row as the header
    df = pd.read_excel(url, sheet_name="Data", header=header_row)

    # Keep only the Date and CAPE columns (Shiller labels the column 'CAPE')
    if "CAPE" not in df.columns:
        raise RuntimeError("Could not find 'CAPE' column in Shiller file.")
    df = df[["Date", "CAPE"]]

    # Drop rows with missing or non-numeric CAPE values
    df["CAPE"] = pd.to_numeric(df["CAPE"], errors="coerce")
    df = df.dropna(subset=["CAPE"])

    # Parse dates, set index, sort
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()

    # Rename to something friendlier
    df = df.rename(columns={"CAPE": "cape_shiller_pe"})

    return df


if __name__ == "__main__":
    df_cape = fetch_shiller_cape()

    print("Shiller CAPE head:")
    print(df_cape.head())
    print("\nShiller CAPE tail:")
    print(df_cape.tail())

    out_path = "cape_shiller_pe_full_history.csv"
    df_cape.to_csv(out_path)
    print(f"\nSaved full Shiller CAPE history to {out_path}")
