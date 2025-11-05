import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

def find_chrome_binary():
    # Look for common binaries in Linux/Windows/macOS
    candidates = [
        "google-chrome", "chrome",             # common names
        "chromium", "chromium-browser",        # Debian/Ubuntu
        "/usr/bin/google-chrome", "/usr/bin/chromium",
        "/usr/bin/chromium-browser", "/snap/bin/chromium"
    ]
    for name in candidates:
        path = shutil.which(name) if not name.startswith("/") else (name if shutil.which(name.split('/')[-1]) or os.path.exists(name) else None)
        if path:
            return path
    return None

def open_earnings_page():
    chrome_binary = find_chrome_binary()
    if not chrome_binary:
        raise RuntimeError(
            "Chrome/Chromium not found. Install it first:\n"
            "  sudo apt-get update && sudo apt-get install -y chromium\n"
        )

    opts = Options()
    opts.binary_location = chrome_binary
    # Codespaces tip: run headless and add these flags for containers
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,1000")

    # Use a CHROMIUM driver (works with Chromium builds)
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=opts)

    url = "https://www.nasdaq.com/market-activity/earnings"
    print(f"Opening {url} ...")
    driver.get(url)

    # If you want to confirm content was loaded:
    print("Page title:", driver.title)
    time.sleep(5)
    driver.quit()

if __name__ == "__main__":
    open_earnings_page()
