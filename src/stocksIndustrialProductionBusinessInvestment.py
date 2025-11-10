# pip install fredapi pandas openpyxl requests python-dateutil
import os, sys, math
from datetime import date
import pandas as pd

TODAY = date.today().isoformat()

# --- Config: pick which business investment you want (nominal vs real) ---
SERIES = {
    "INDPRO (Industrial Production, M)": "INDPRO",          # Monthly
    "PNFI (Biz Investment, Nominal, Q)": "PNFI",            # Quarterly, SAAR, current dollars
    "PNFIC96 (Biz Investment, Real, Q)": "PNFIC96",         # Quarterly, SAAR, chained 2017 dollars
}

# ---------- Fetch helpers (fredapi first, requests fallback) ----------
def fred_fetch(series_id, api_key=None):
    """
    Returns a pandas Series with a DatetimeIndex. Tries fredapi first, then requests fallback.
    """
    try:
        from fredapi import Fred
        fred = Fred(api_key=api_key or os.getenv("FRED_API_KEY"))
        s = fred.get_series(series_id)
        s.index = pd.to_datetime(s.index)
        s.name = series_id
        return s.sort_index()
    except Exception as e:
        # Minimal fallback using requests (JSON endpoint)
        import requests
        key = api_key or os.getenv("FRED_API_KEY")
        if not key:
            raise RuntimeError(
                f"No FRED_API_KEY set and fredapi failed for {series_id}. "
                "Set FRED_API_KEY or install/configure fredapi."
            ) from e
        url = (
            "https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series_id}&api_key={key}&file_type=json&observation_start=1776-01-01"
        )
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()["observations"]
        df = pd.DataFrame(data)
        # Clean
        df = df[df["value"] != "."].copy()
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"])
        s = df.set_index("date")["value"].sort_index()
        s.name = series_id
        return s

# ---------- Metrics ----------
def yoy(series: pd.Series):
    """Year-over-year % change (aligned by frequency)."""
    return series.pct_change(12) * 100 if series.index.inferred_freq == "M" else series.pct_change(4) * 100

def cagr(series: pd.Series):
    """
    CAGR from first non-NA to last non-NA, annualized.
    Uses frequency inference to annualize properly.
    """
    s = series.dropna()
    if s.empty or s.iloc[0] <= 0:
        return float("nan")
    # infer periods per year (M=12, Q=4, A=1)
    freq = pd.infer_freq(s.index)
    per_year = 12 if freq and freq.startswith("M") else 4 if freq and freq.startswith("Q") else 1
    n_years = (s.index[-1] - s.index[0]).days / 365.25
    if n_years <= 0:
        return float("nan")
    return (s.iloc[-1] / s.iloc[0]) ** (1 / n_years) - 1

# ---------- Run ----------
all_frames = []
summary_rows = []

for label, sid in SERIES.items():
    s = fred_fetch(sid)
    # Attach frequency so YoY picks the right lag
    # (Pandas may not infer; we’ll coerce based on observed spacing)
    s = s.asfreq("M") if s.index.to_period("M").to_timestamp().equals(s.index.normalize()) and s.index.freq is None and s.index.inferred_freq in (None, "M") and len(s) > 24 else s
    if s.index.inferred_freq is None:
        # Try to infer again; if still None, just leave as-is (YoY will default to 4 for Q below)
        pass

    # Compute YoY using monthly=12, quarterly=4 assumption
    # Decide monthly vs quarterly heuristic: if median gap ~30 days → monthly; ~90 days → quarterly
    gaps = s.index.to_series().diff().dt.days.dropna()
    median_gap = gaps.median() if len(gaps) else 30
    if median_gap < 60:
        yoy_vals = s.pct_change(12) * 100
        freq_tag = "Monthly"
    else:
        yoy_vals = s.pct_change(4) * 100
        freq_tag = "Quarterly"

    df = pd.DataFrame({
        "series_id": sid,
        "label": label,
        "value": s,
        "yoy_pct": yoy_vals
    })
    all_frames.append(df)

    # Summary stats
    cg = cagr(s)
    summary_rows.append({
        "label": label,
        "series_id": sid,
        "freq": freq_tag,
        "start_date": s.dropna().index.min().date(),
        "end_date": s.dropna().index.max().date(),
        "first_value": s.dropna().iloc[0],
        "last_value": s.dropna().iloc[-1],
        "CAGR_since_inception_%": cg * 100 if pd.notna(cg) else float("nan"),
        "avg_YoY_%": df["yoy_pct"].mean(skipna=True),
        "min_YoY_%": df["yoy_pct"].min(skipna=True),
        "max_YoY_%": df["yoy_pct"].max(skipna=True),
        "obs": int(s.dropna().shape[0]),
    })

out_df = pd.concat(all_frames).reset_index(names="date").sort_values(["label", "date"])
summary_df = pd.DataFrame(summary_rows)

# Save files (include start/end in filenames)
def span_tag(df):
    # one span per series, but we’ll use the union span
    sd = out_df["date"].min().strftime("%Y-%m-%d")
    ed = out_df["date"].max().strftime("%Y-%m-%d")
    return f"{sd}_to_{ed}"

span = span_tag(out_df)

csv_name = f"fred_indpro_business_investment_{span}.csv"
xlsx_name = f"fred_indpro_business_investment_{span}.xlsx"

out_df.to_csv(csv_name, index=False)
with pd.ExcelWriter(xlsx_name, engine="openpyxl") as xw:
    out_df.to_excel(xw, index=False, sheet_name="history")
    summary_df.to_excel(xw, index=False, sheet_name="summary")

print("Wrote:", csv_name, "and", xlsx_name)
print("\n=== Summary ===")
print(summary_df.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
