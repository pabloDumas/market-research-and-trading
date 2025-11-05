"""
Requirements:
  pip install selenium pandas lxml
Also install Chrome + the matching ChromeDriver on PATH, or use webdriver-manager.

Notes:
- This script tries TWO strategies to click "tomorrow":
  (A) the date ribbon at the top of the page
  (B) the popup date-picker (calendar icon)
- If Nasdaq tweaks the markup, use the "How to get the XPath" steps below
  to update the XPaths under the CONFIG section.
"""

import time
import sys
import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


# --------------------- CONFIG (adjust XPaths here if needed) ---------------------

URL = "https://www.nasdaq.com/market-activity/earnings"

# A. Ribbon day button (top row of days) — uses visible text like "TUE 04 Nov".
#    We dynamically format the text for tomorrow and find a button containing it.
#    If this fails on your machine, switch to method B below.
RIBBON_BUTTON_XPATH_TEMPLATE = (
    # Looks for something like:  TUE 04 Nov
    "//div[contains(., '{dow_upper} {day:02d} {mon_title}') and contains(@class,'calendar')]"
    "//button[not(@disabled)]"
)

# B. Calendar icon + date-picker — open the popover and click exact day cell.
#    You will likely need to confirm the aria-label once with DevTools.
CALENDAR_ICON_XPATH = "//button[contains(@aria-label, 'calendar') or contains(@class,'calendar')]"
# Example aria-label that many date-pickers use:
# aria-label="Choose Tuesday, November 4, 2025"
DATEPICKER_BUTTON_ARIA_TEMPLATE = "Choose {dow_full}, {mon_full} {day}, {year}"
DATEPICKER_DAYBTN_XPATH_TEMPLATE = "//button[@aria-label=\"{aria}\"]"

# Locator for the main table element once the page loads a date's results.
# (Nasdaq uses a single table per page of results.)
TABLE_XPATH = "//table[.//thead]"

# Optional: change the “Show” dropdown to 100 rows (Nasdaq uses a custom select).
# If your page already shows 100, you can set this to False to skip.
TRY_SET_SHOW_100 = True
SHOW_DROPDOWN_XPATH = "//div[contains(@class,'select')]//button[contains(@aria-haspopup,'listbox')]"
OPTION_100_XPATH = "//div[@role='listbox']//div[.//span[normalize-space()='100']]"

# Max wait seconds
WAIT = 20


# --------------------- HELPER: build tomorrow labels in US/Eastern ---------------------

def tomorrow_labels():
    # Nasdaq calendar is aligned to U.S. market days; Eastern time is safest.
    now_et = dt.datetime.now(ZoneInfo("America/New_York"))
    tomorrow = now_et + dt.timedelta(days=1)

    dow_upper = tomorrow.strftime("%a").upper()   # e.g., "TUE"
    dow_full = tomorrow.strftime("%A")            # e.g., "Tuesday"
    day_num = int(tomorrow.strftime("%d"))        # 04 -> 4 / 04
    mon_title = tomorrow.strftime("%b")           # "Nov"
    mon_full = tomorrow.strftime("%B")            # "November"
    year = tomorrow.year

    return {
        "dow_upper": dow_upper,
        "dow_full": dow_full,
        "day": day_num,
        "mon_title": mon_title,
        "mon_full": mon_full,
        "year": year,
    }


# --------------------- BROWSER SETUP ---------------------

chrome_opts = Options()
# comment out headless if you want to watch the browser
# chrome_opts.add_argument("--headless=new")
chrome_opts.add_argument("--window-size=1400,1000")

driver = webdriver.Chrome(options=chrome_opts)
wait = WebDriverWait(driver, WAIT)

try:
    driver.get(URL)

    # Accept any cookie banner if it appears (best effort; safe to ignore if missing)
    try:
        consent = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[normalize-space()='Accept' or contains(., 'Accept')]"
        )))
        consent.click()
        time.sleep(0.5)
    except Exception:
        pass  # no banner or different text

    # Wait for the table (or its container) to be present once for baseline load
    wait.until(EC.presence_of_element_located((By.XPATH, TABLE_XPATH)))

    # Optionally set "Show 100"
    if TRY_SET_SHOW_100:
        try:
            # open the custom dropdown
            dd_btn = wait.until(EC.element_to_be_clickable((By.XPATH, SHOW_DROPDOWN_XPATH)))
            dd_btn.click()
            # click "100"
            opt_100 = wait.until(EC.element_to_be_clickable((By.XPATH, OPTION_100_XPATH)))
            opt_100.click()
            # allow table to re-render
            time.sleep(1.0)
        except Exception:
            # harmless if dropdown markup differs; continue with defaults
            pass

    # --------------------- CLICK TOMORROW ---------------------
    labels = tomorrow_labels()

    # Strategy A: click the ribbon day button that contains "TUE 04 Nov" style text
    clicked = False
    try:
        ribbon_xpath = RIBBON_BUTTON_XPATH_TEMPLATE.format(**labels)
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, ribbon_xpath)))
        btn.click()
        clicked = True
    except Exception:
        # Fall back to Strategy B (calendar icon)
        pass

    if not clicked:
        # Strategy B: open calendar popover and click exact date via aria-label
        icon = wait.until(EC.element_to_be_clickable((By.XPATH, CALENDAR_ICON_XPATH)))
        icon.click()

        aria = DATEPICKER_BUTTON_ARIA_TEMPLATE.format(**labels)
        daybtn_xpath = DATEPICKER_DAYBTN_XPATH_TEMPLATE.format(aria=aria)
        day_btn = wait.until(EC.element_to_be_clickable((By.XPATH, daybtn_xpath)))
        day_btn.click()

    # Wait for the table to refresh — simplest is to wait a beat, then ensure rows exist
    time.sleep(1.2)
    table_el = wait.until(EC.presence_of_element_located((By.XPATH, TABLE_XPATH)))

    # Grab table HTML and parse with pandas.read_html
    table_html = table_el.get_attribute("outerHTML")
    dfs = pd.read_html(table_html)
    if not dfs:
        raise RuntimeError("No table parsed from the HTML block.")
    df = dfs[0]

    # Show top 5
    print("\nTOP 5 ROWS FOR TOMORROW:")
    print(df.head(5).to_string(index=False))

    # Save artifacts
    df.to_csv("nasdaq_earnings_tomorrow.csv", index=False)
    with open("nasdaq_earnings_table.html", "w", encoding="utf-8") as f:
        f.write(table_html)
    print("\nSaved: nasdaq_earnings_tomorrow.csv and nasdaq_earnings_table.html")

finally:
    # Close the browser after a short pause so you can see the result if not headless
    time.sleep(1)
    driver.quit()
