import os
import sys
import time
import shutil
import subprocess
import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL = "https://www.nasdaq.com/market-activity/earnings"

def which_first(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None

def ensure_chromium_installed():
    """
    Ensure we have a Chrome/Chromium binary.
    - On Linux (e.g., GitHub Codespaces), try apt-get install if missing.
    - On macOS/Windows, just prompt user to install Chrome.
    Returns the path to the binary.
    """
    existing = which_first("chromium", "chromium-browser", "google-chrome", "chrome")
    if existing:
        return existing

    system = platform.system().lower()
    if system == "linux":
        print("[info] Chromium not found. Attempting apt-get install...")
        try:
            subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
            # try both package names (one of them exists depending on base image)
            try:
                subprocess.run(["sudo", "apt-get", "install", "-y", "chromium"], check=True)
            except subprocess.CalledProcessError:
                subprocess.run(["sudo", "apt-get", "install", "-y", "chromium-browser"], check=True)

            recheck = which_first("chromium", "chromium-browser")
            if not recheck:
                raise RuntimeError("Chromium install attempted but binary still not found.")
            return recheck
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install Chromium via apt-get: {e}") from e

    elif system == "darwin":
        raise RuntimeError(
            "Chrome/Chromium not found on macOS. Install:\n"
            "  brew install --cask google-chrome   # or: brew install chromium"
        )
    elif system == "windows":
        raise RuntimeError(
            "Chrome/Chromium not found on Windows. Install Chrome:\n"
            "  https://www.google.com/chrome/"
        )
    else:
        raise RuntimeError(f"Unsupported OS: {system}")

def open_page():
    chrome_binary = ensure_chromium_installed()

    opts = Options()
    opts.binary_location = chrome_binary
    # In containers, headless is more reliable. Remove for a visible window locally.
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,1000")

    # ✨ Selenium Manager (built into Selenium 4.6+) will auto-download the driver:
    driver = webdriver.Chrome(options=opts)

    print(f"[info] Opening {URL} ...")
    driver.get(URL)
    print("[info] Title:", driver.title)

    driver.get_screenshot_as_file("nasdaq_earnings.png")
    print("[info] Saved nasdaq_earnings.png")
    time.sleep(1)
    driver.quit()

if __name__ == "__main__":
    open_page()
