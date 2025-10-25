import os
import ssl
import smtplib
import pickle
import requests
import pandas as pd
from datetime import datetime
from email.message import EmailMessage

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
SAVE_DIR = os.path.join("data", TODAY_DATE)
os.makedirs(SAVE_DIR, exist_ok=True)

# === API calls ===
api_calls = [{"function": "TOP_GAINERS_LOSERS"}]

# === Fetch Alpha Vantage data ===
def fetch_data(params):
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"❌ Request failed: {response.status_code}")
    return None

all_data = []
for call in api_calls:
    print(f"Fetching data for {call['function']}")
    params = {**call, "apikey": ALPHA_VANTAGE_API_KEY}
    data = fetch_data(params)
    if not data:
        continue
    file_name = f"{call['function']}.pkl"
    with open(os.path.join(SAVE_DIR, file_name), "wb") as f:
        pickle.dump(data, f)
    df = pd.DataFrame(data)
    df["source_query"] = call["function"]
    all_data.append(df)

if not all_data:
    raise RuntimeError("No data retrieved from Alpha Vantage.")

# === Process and save Excel ===
concatenated_df = pd.concat(all_data, ignore_index=True)
excel_path = os.path.join(SAVE_DIR, f"financial_data_{TODAY_DATE}.xlsx")
concatenated_df.to_excel(excel_path, index=False)
print(f"✅ Excel file saved: {excel_path}")

# === Email function ===
def send_mail(to, subject, body, attachment_path=None):
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

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

if __name__ == "__main__":
    send_mail(
        SMTP_USER_TO,
        f"Alpha Vantage Report – {TODAY_DATE}",
        f"Attached is the Alpha Vantage financial data for {TODAY_DATE}.",
        excel_path,
    )
