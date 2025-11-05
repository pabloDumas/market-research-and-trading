"""
Cross-platform Selenium script.
Automatically installs correct ChromeDriver and opens the Nasdaq Earnings Calendar page.
Works on Windows, macOS, and Linux.
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def open_earnings_page():
    # 1. Configure Chrome
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # open fullscreen
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")

    # 2. Auto-install matching ChromeDriver (version agnostic)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                              options=chrome_options)

    # 3. Go to Nasdaq Earnings Calendar
    url = "https://www.nasdaq.com/market-activity/earnings"
    print(f"Opening {url} ...")
    driver.get(url)

    # 4. Keep browser visible for a while before closing
    time.sleep(10)
    driver.quit()


if __name__ == "__main__":
    open_earnings_page()
