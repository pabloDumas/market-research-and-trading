import time, shutil
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.nasdaq.com/market-activity/earnings"

# --- Your provided XPaths (brittle but we’ll try them first) ---
DROPDOWN_XPATH_PRIMARY = r"/html/body/div[2]/div/main/div[2]/article/div/div[1]/div[2]/div/div[2]/div/div/div[1]/div/div/div[6]/div/div[1]/div"
TABLE_SCOPE_XPATH_PRIMARY = r"/html/body/div[2]/div/main/div[2]/article/div/div[1]/div[2]/div/div[2]/div/div/div[1]/div/div/div[5]/nsdq-table-sort//div"

# --- Safer fallbacks if the absolute paths shift a little ---
# 1) Rows-per-page dropdown button (custom select)
DROPDOWN_XPATH_FALLBACK = (
    "//div[contains(@class,'select') and .//button[contains(@aria-haspopup,'listbox')]]"
    "//button[contains(@aria-haspopup,'listbox')]"
)
# 2) Option '100' inside the popup listbox
OPTION_100_XPATH = "//div[@role='listbox' or @role='menu']//div[.//span[normalize-space()='100'] or normalize-space()='100']"
# 3) Actual data table
TABLE_XPATH_FALLBACK = "//table[.//thead]"

def find_browser():
    for name in ("google-chrome", "chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    raise RuntimeError("Chrome/Chromium not found. Install google-chrome-stable.")

def open_page():
    chrome_bin = find_browser()
    opts = Options()
    opts.binary_location = chrome_bin

    # Container-safe + HTTP/2 workaround + realistic UA
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,1000")
    opts.add_argument("--disable-http2")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(URL)
        print("Title:", driver.title)

        # 1) Click the rows-per-page dropdown
        try:
            dd = wait.until(EC.element_to_be_clickable((By.XPATH, DROPDOWN_XPATH_PRIMARY)))
        except Exception:
            dd = wait.until(EC.element_to_be_clickable((By.XPATH, DROPDOWN_XPATH_FALLBACK)))
        dd.click()

        # 2) Select '100'
        opt100 = wait.until(EC.element_to_be_clickable((By.XPATH, OPTION_100_XPATH)))
        opt100.click()

        # 3) Give the page time to re-render to 100 rows
        time.sleep(5)

        # 4) Locate the table element
        table_el = None
        try:
            # If the primary points to a wrapper, descend to the actual <table>
            scope = wait.until(EC.presence_of_element_located((By.XPATH, TABLE_SCOPE_XPATH_PRIMARY)))
            # try to find a table *inside* that scope
            try:
                table_el = scope.find_element(By.XPATH, ".//table[.//thead]")
            except Exception:
                pass
        except Exception:
            pass

        if table_el is None:
            table_el = wait.until(EC.presence_of_element_located((By.XPATH, TABLE_XPATH_FALLBACK)))

        # 5) Parse the table HTML with pandas
        html = table_el.get_attribute("outerHTML")
        dfs = pd.read_html(html)
        if not dfs:
            raise RuntimeError("No table parsed from the HTML block.")
        df = dfs[0]

        # Save + preview
        csv_name = "nasdaq_earnings_100.csv"
        df.to_csv(csv_name, index=False)
        print(f"\nSaved CSV: {csv_name}")
        print("\nTop 5 rows:")
        print(df.head(5).to_string(index=False))

        # optional: keep a raw HTML snapshot too
        with open("nasdaq_earnings_table.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved nasdaq_earnings_table.html")

        # optional screenshot for debugging
        driver.get_screenshot_as_file("nasdaq_earnings_after_100.png")

    finally:
        driver.quit()

if __name__ == "__main__":
    open_page()
