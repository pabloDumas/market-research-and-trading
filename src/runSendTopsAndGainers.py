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

import ast
import json
import pandas as pd

def expand_top_gainers_from_df(concat_df: pd.DataFrame) -> pd.DataFrame:
    if "top_gainers" not in concat_df.columns:
        return pd.DataFrame()

    records = []
    for cell in concat_df["top_gainers"].dropna():
        # dict directly
        if isinstance(cell, dict):
            records.append(cell); continue

        # list directly
        if isinstance(cell, list):
            records.extend([x for x in cell if isinstance(x, dict)]); continue

        # string → try JSON then Python literal
        if isinstance(cell, str):
            parsed = None
            try:
                parsed = json.loads(cell)
            except Exception:
                try:
                    parsed = ast.literal_eval(cell)
                except Exception:
                    parsed = None
            if isinstance(parsed, dict):
                records.append(parsed)
            elif isinstance(parsed, list):
                records.extend([x for x in parsed if isinstance(x, dict)])

    if not records:
        return pd.DataFrame()

    tg = pd.json_normalize(records, sep="_")

    # clean percentage-like columns
    for col in tg.columns:
        cl = col.lower()
        if "percentage" in cl or "pct" in cl or cl.endswith("_change"):
            tg[col] = (
                tg[col].astype(str)
                .str.replace("%", "", regex=False)
                .str.replace("+", "", regex=False)
                .str.strip()
            )
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

    # Save raw pickle
    with open(os.path.join(SAVE_DIR_DATA, f"{call['function']}.pkl"), "wb") as f:
        pickle.dump(data, f)
    
    # ✅ FIXED: make a single-row DataFrame; list values stay as objects
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = pd.DataFrame(data)
    
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











import base64
from pathlib import Path

API_URL = "https://api.github.com"

def _read_b64(local_path: str) -> str:
    with open(local_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def _get_existing_sha(owner, repo, branch, repo_path, token):
    url = f"{API_URL}/repos/{owner}/{repo}/contents/{repo_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    r = requests.get(url, headers=headers, params={"ref": branch})
    if r.status_code == 200:
        return r.json().get("sha")  # needed when updating an existing file
    elif r.status_code == 404:
        return None
    r.raise_for_status()

def upload_or_update_file(owner, repo, branch, repo_path, local_path, token, message):
    """Create or update a single file in the repo via the Contents API."""
    sha = _get_existing_sha(owner, repo, branch, repo_path, token)
    content_b64 = _read_b64(local_path)

    url = f"{API_URL}/repos/{owner}/{repo}/contents/{repo_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "message": message,
        "content": content_b64,
        "branch": branch,
        # include sha only when updating an existing path
        **({"sha": sha} if sha else {}),
        # optional committer block:
        # "committer": {"name": "Your Bot", "email": "bot@example.com"},
    }

    r = requests.put(url, headers=headers, data=json.dumps(payload))
    r.raise_for_status()
    data = r.json()
    print("✅ Uploaded:", data["content"]["path"], "→", data["content"]["html_url"])
    return data

# --- Use it for BOTH files from your script ---
# Assume these variables already exist from your code:
# tg_path_out and excel_path_out (local filesystem paths)
def upload_both(owner, repo, branch, token, tg_path_out, excel_path_out, date_str):
    # Make sure local files exist
    for p in [tg_path_out, excel_path_out]:
        if not Path(p).exists():
            raise FileNotFoundError(p)

    # Choose where they should live inside the repo
    repo_path_tg    = f"outputs/top_gainers_{date_str}.xlsx"
    repo_path_main  = f"outputs/financial_data_{date_str}.xlsx"

    msg = f"Add reports for {date_str}"

    upload_or_update_file(owner, repo, branch, repo_path_main, excel_path_out, token, msg)
    upload_or_update_file(owner, repo, branch, repo_path_tg,   tg_path_out,    token, msg)

token = os.environ["GITHUB_TOKEN"]  # in Actions (preferred)
upload_both("pabloDumas", "market-research-and-trading", "main", token, tg_path_out, excel_path_out, TODAY_DATE)
