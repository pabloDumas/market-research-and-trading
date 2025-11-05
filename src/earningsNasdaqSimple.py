import time, shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL = "https://www.nasdaq.com/market-activity/earnings"

def find_browser():
    for name in ("google-chrome", "chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p: return p
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

    # Selenium Manager auto-fetches the right driver
    driver = webdriver.Chrome(options=opts)

    driver.get(URL)
    print("Title:", driver.title)
    driver.get_screenshot_as_file("nasdaq_earnings.png")
    print("Saved nasdaq_earnings.png")
    time.sleep(1)
    driver.quit()

if __name__ == "__main__":
    open_page()
