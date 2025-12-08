import pandas as pd

def fetch_shiller_cape() -> pd.DataFrame:
    """
    Fetch Shiller CAPE / PE10 using a reliable HTTPS mirror + correct date parsing.
    """

    # HTTPS mirror (reliable for modern environments)
    url = "https://raw.githubusercontent.com/0x0f0f0f/shiller-data/main/ie_data.xls"

    # Read raw to locate header
    raw = pd.read_excel(url, sheet_name="Data", header=None)

    # Locate row containing the word 'Date' in column 0
    header_row_candidates = raw.index[raw.iloc[:, 0] == "Date"]
    if len(header_row_candidates) == 0:
        raise RuntimeError("Could not find header row with 'Date'")
    header_row = header_row_candidates[0]

    # Now read again with that header
    df = pd.read_excel(url, sheet_name="Data", header=header_row)

    # Keep Date + CAPE
    if "CAPE" not in df.columns:
        raise RuntimeError("CAPE column not found")
    df = df[["Date", "CAPE"]]

    # Convert CAPE to number
    df["CAPE"] = pd.to_numeric(df["CAPE"], errors="coerce")
    df = df.dropna(subset=["CAPE"])

    # --- FIX DATE PARSING ---
    # Shiller uses YYYY.MM (e.g., 1881.01 = January 1881)
    date_str = df["Date"].astype(str)

    # Extract year and month safely
    year = date_str.str.extract(r"^(\d{4})")[0]
    month = date_str.str.extract(r"\.(\d{2})")[0]

    df["Date"] = pd.to_datetime(year + "-" + month + "-01", errors="coerce")
    df = df.dropna(subset=["Date"])

    # Set index
    df = df.set_index("Date").sort_index()

    # Rename
    df = df.rename(columns={"CAPE": "cape_shiller_pe"})

    return df


if __name__ == "__main__":
    df_cape = fetch_shiller_cape()

    print(df_cape.head())
    print(df_cape.tail())

    out_path = "cape_shiller_pe_full_history.csv"
    df_cape.to_csv(out_path)
    print(f"\nSaved Shiller CAPE to {out_path}")
