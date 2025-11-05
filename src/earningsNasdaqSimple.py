# earnings_open_page.py
import time, shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL = "https://www.nasdaq.com/market-activity/earnings"

def find_browser():
    # prefer Google Chrome stable if present
    for name in ("google-chrome", "chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p: return p
    raise RuntimeError("No Chrome/Chromium binary found. Install google-chrome-stable.")

def open_page():
    chrome_bin = find_browser()
    opts = Options()
    opts.binary_location = chrome_bin
    # container-safe flags
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,1000")

    # Selenium 4.6+ auto-downloads the correct driver (Selenium Manager)
    driver = webdriver.Chrome(options=opts)

    driver.get(URL)
    print("Title:", driver.title)
    driver.get_screenshot_as_file("nasdaq_earnings.png")
    print("Saved nasdaq_earnings.png")
    time.sleep(1)
    driver.quit()

if __name__ == "__main__":
    open_page()
