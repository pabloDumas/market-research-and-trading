import pandas as pd

# If your text is already a CSV file, do this:
df = pd.read_csv("fred_indpro_business_investment_1919-01-01_to_2025-08-01.csv", parse_dates=["date"])

# If it's already a DataFrame named df, skip the read and start here.
# Expect columns: date, series_id, label, value, yoy_pct

# 1) Pivot values and YoY side-by-side
val_wide = df.pivot_table(index="date", columns="label", values="value")
yoy_wide = df.pivot_table(index="date", columns="label", values="yoy_pct")

# 2) Make column names tidy
val_wide = val_wide.rename(columns={
    "INDPRO (Industrial Production, M)": "INDPRO_value",
    "PNFI (Biz Investment, Nominal, Q)": "PNFI_value",
    "PNFIC96 (Biz Investment, Real, Q)": "PNFIC96_value",
})
yoy_wide = yoy_wide.rename(columns={
    "INDPRO (Industrial Production, M)": "INDPRO_yoy_pct",
    "PNFI (Biz Investment, Nominal, Q)": "PNFI_yoy_pct",
    "PNFIC96 (Biz Investment, Real, Q)": "PNFIC96_yoy_pct",
})

# 3) Merge into one wide table
wide = (
    val_wide.join(yoy_wide, how="outer")
             .reset_index()
             .sort_values("date")
)

# 4) Reorder final columns exactly as requested
wide = wide[[
    "date",
    "PNFI_value", "PNFIC96_value", "INDPRO_value",
    "PNFI_yoy_pct", "PNFIC96_yoy_pct", "INDPRO_yoy_pct",
]]

# 5) Save
wide.to_csv("industrial_production_business_investment_wide.csv", index=False)
try:
    with pd.ExcelWriter("industrial_production_business_investment_wide.xlsx", engine="openpyxl") as xw:
        wide.to_excel(xw, index=False, sheet_name="wide")
except Exception:
    pass  # openpyxl optional

wide.head()
