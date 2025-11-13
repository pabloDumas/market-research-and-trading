import requests
import pandas as pd

# JSON endpoint you saw in DevTools
URL = "https://en.macromicro.me/charts/data/55674"

# Minimal headers; add Authorization/Cookie from DevTools if your request needs auth
headers = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
    "Referer": (
        "https://en.macromicro.me/collections/34/us-stock-relative/"
        "55674/us-citi-surprise-index-earnings-revision"
    ),
    # If DevTools shows these, uncomment and paste them:
    # "Authorization": "Bearer YOUR_TOKEN_HERE",
    # "Cookie": "mm_session=...; other_cookie=...",
}

# 1. Fetch JSON from MacroMicro
resp = requests.get(URL, headers=headers)
resp.raise_for_status()
json_data = resp.json()

# 2. Navigate to the chart data
# data -> "c:55674" (key may be 'c:55674', so grab the first key under "data")
chart_key = next(iter(json_data["data"].keys()))
chart_obj = json_data["data"][chart_key]

# "series" is a list of two lists: [0] surprise index, [1] earnings revision index
series_list = chart_obj["series"]

# 3. Take the second list = Citigroup Earnings Revision Index
earnings_revision_series = series_list[1]  # list of [date, value] pairs

# 4. Convert to DataFrame
df = pd.DataFrame(earnings_revision_series, columns=["date", "value"])
df["value"] = pd.to_numeric(df["value"])

# 5. Show head
print(df.head())

# 6. Save to CSV
output_path = "US_Citi_Earnings_Revision_Index.csv"
df.to_csv(output_path, index=False)
print("Saved CSV to:", output_path)
