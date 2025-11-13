import json
import pandas as pd

# Path to your uploaded JS/JSON file
filepath = "stocksUSEarningsRevisionIndex2025-11-12T15-57-07.js"

# 1. Load the JSON-like structure
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Some MacroMicro JS files wrap JSON in JS syntax.
# Safest: find the JSON portion after the "=" sign if present.
# If your file is pure JSON, this still works.
try:
    # Remove leading JS variable assignments if any
    json_start = content.find("{")
    json_data = json.loads(content[json_start:])
except Exception:
    raise ValueError("File is not valid JSON. Paste or inspect raw content.")

# 2. Navigate to the earnings-revision data
# Structure: data -> "c:55674" -> "series" -> [ list1 , list2 ]
series_list = json_data["data"]["c:55674"]["series"]

# You want the **second** list of pairs
earnings_revision_series = series_list[1]

# 3. Convert to DataFrame
df = pd.DataFrame(earnings_revision_series, columns=["date", "value"])

# Fix numeric dtype
df["value"] = pd.to_numeric(df["value"])

# 4. Output head
print(df.head())

# 5. Save to CSV
output_path = "earnings_revision_index.csv"
df.to_csv(output_path, index=False)

print("Saved to:", output_path)

