import os
import ssl
import smtplib
import pickle
import json
import requests
import pandas as pd
from datetime import datetime
from email.message import EmailMessage
from openpyxl.utils import get_column_letter

# === Secure configuration ===
SMTP_USER = os.environ["SMTP_USER"]                      # sender email
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]              # Gmail App Password
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")     # Gmail SMTP host
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))           # TLS port
SMTP_USER_TO = os.getenv("SMTP_USER_TO", SMTP_USER)      # recipient (default = sender)
ALPHA_VANTAGE_API_KEY = os.environ["ALPHA_VANTAGE_API_KEY"]

# === Constants ===
BASE_URL = "https://www.alphavantage.co/query?"
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

# In-repo output dirs
SAVE_DIR_DATA = os.path.join("data", TODAY_DATE)
SAVE_DIR_OUT = os.path.join("outputs")                  # root-level "outputs"
os.makedirs(SAVE_DIR_DATA, exist_ok=True)
os.makedirs(SAVE_DIR_OUT, exist_ok=True)

# === API calls ===
api_calls = [{"function": "TOP_GAINERS_LOSERS"}]

# === Helpers ===
def fetch_data(params):
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"❌ Request failed: {response.status_code}")
    return None

def save_excel_auto(df: pd.DataFrame, path: str, sheet_name: str = "Sheet1"):
    """Save DataFrame to Excel and auto-fit column widths (openpyxl)."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]
        for i, col in enumerate(df.columns, 1):
            # Max length among header and cells (as string)
            max_len = len(str(col))
            for val in df[col].astype(str).values:
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[get_column_letter(i)].width = min(max_len + 2, 80)  # cap width

def expand_top_gainers_from_df(concat_df: pd.DataFrame) -> pd.DataFrame:
    """Flatten 'top_gainers' column (list/JSON per row) into a normalized table."""
    if "top_gainers" not in concat_df.columns:
        return pd.DataFrame()

    records = []
    for cell in concat_df["top_gainers"].dropna():
        if isinstance(cell, list):
            records.extend(cell)
        elif isinstance(cell, str):
            try:
                parsed = json.loads(cell)
                if isinstance(parsed, list):
                    records.extend(parsed)
            except Exception:
                continue

    if not records:
        return pd.DataFrame()

    tg = pd.json_normalize(records)

    # Optional: clean percentage fields if present (e.g., "+12.34%")
    for col in tg.columns:
        if "percentage" in col.lower():
            tg[col] = (
                tg[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.replace("+", "", regex=False)
                .str.strip()
            )
            # Convert to float, coerce errors
            tg[col] = pd.to_numeric(tg[col], errors="coerce")

    return tg

def send_mail(to, subject, body, attachments=None):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    attachments = attachments or []
    for attachment_path in attachments:
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename=os.path.basename(attachment_path),
                )
            print(f"📎 Attached file: {os.path.basename(attachment_path)}")

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls(context=context)
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)
    print(f"✅ Email sent successfully to {to}")

# === Main flow ===
if __name__ == "__main__":
    all_data = []

    # Pull data
    for call in api_calls:
        print(f"Fetching data for {call['function']}")
        params = {**call, "apikey": ALPHA_VANTAGE_API_KEY}
        data = fetch_data(params)
        if not data:
            continue

        # Save raw pickle under data/YYYY-MM-DD
        pkl_name = f"{call['function']}.pkl"
        with open(os.path.join(SAVE_DIR_DATA, pkl_name), "wb") as f:
            pickle.dump(data, f)

        # Store as a 1-row DF with object columns (including JSON lists)
        df = pd.DataFrame(data, index=[0]) if isinstance(data, dict) else pd.DataFrame(data)
        df["source_query"] = call["function"]
        all_data.append(df)

    if not all_data:
        raise RuntimeError("No data retrieved from Alpha Vantage.")

    # Concatenate and save the main Excel(s)
    concatenated_df = pd.concat(all_data, ignore_index=True)

    # Paths for main file
    excel_name_main = f"financial_data_{TODAY_DATE}.xlsx"
    excel_path_data = os.path.join(SAVE_DIR_DATA, excel_name_main)
    excel_path_out = os.path.join(SAVE_DIR_OUT, excel_name_main)

    save_excel_auto(concatenated_df, excel_path_data, sheet_name="AlphaVantageRaw")
    save_excel_auto(concatenated_df, excel_path_out, sheet_name="AlphaVantageRaw")
    print(f"✅ Excel saved: {excel_path_data}")
    print(f"✅ Excel saved: {excel_path_out}")

    # Expand top_gainers into its own tidy table and save as second Excel
    top_gainers_df = expand_top_gainers_from_df(concatenated_df)
    excel_name_tg = f"top_gainers_{TODAY_DATE}.xlsx"
    tg_path_data = os.path.join(SAVE_DIR_DATA, excel_name_tg)
    tg_path_out = os.path.join(SAVE_DIR_OUT, excel_name_tg)

    if not top_gainers_df.empty:
        save_excel_auto(top_gainers_df, tg_path_data, sheet_name="TopGainers")
        save_excel_auto(top_gainers_df, tg_path_out, sheet_name="TopGainers")
        print(f"✅ Top gainers Excel saved: {tg_path_data}")
        print(f"✅ Top gainers Excel saved: {tg_path_out}")
    else:
        print("⚠️ No 'top_gainers' data found to expand.")

    # Email both Excel files (main + top gainers) from the outputs/ location
    attachments = [excel_path_out]
    if os.path.exists(tg_path_out):
        attachments.append(tg_path_out)

    send_mail(
        SMTP_USER_TO,
        f"Alpha Vantage Report – {TODAY_DATE}",
        f"Attached: main report + expanded Top Gainers for {TODAY_DATE}.",
        attachments=attachments,
    )
