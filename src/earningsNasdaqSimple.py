import os, sys, time, shutil, subprocess, platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

URL = "https://www.nasdaq.com/market-activity/earnings"

def which_first(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None

def ensure_chromium_installed():
    """
    Ensures a Chromium/Chrome binary exists.
    - On Linux (Debian/Ubuntu/Codespaces): installs chromium if missing.
    - On macOS/Windows: prints guidance (don’t attempt package install).
    Returns the binary path or raises RuntimeError.
    """
    # 1) Check if any Chrome/Chromium binary already exists
    existing = which_first(
        "chromium", "chromium-browser", "google-chrome", "chrome"
    )
    if existing:
        return existing

    system = platform.system().lower()
    if system == "linux":
        # Best-effort install for Debian/Ubuntu-like envs (Codespaces)
        print("[info] Chromium not found. Attempting apt-get install...")
        try:
            # Make sure apt cache is fresh
            subprocess.run(
                ["sudo", "apt-get", "update"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Try common package names
            # (Some images use 'chromium', others 'chromium-browser')
            for pkg in ("chromium", "chromium-browser"):
                try:
                    subprocess.run(
                        ["sudo", "apt-get", "install", "-y", pkg],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    break
                except subprocess.CalledProcessError:
                    pass

            # Re-check after install
            recheck = which_first("chromium", "chromium-browser")
            if not recheck:
                raise RuntimeError(
                    "Tried to install Chromium, but binary not found. "
                    "You may need to install manually in this container."
                )
            return recheck

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to install Chromium via apt-get. Details:\n{e}"
            ) from e

    elif system == "darwin":
        raise RuntimeError(
            "Chromium/Chrome not found on macOS. Install with Homebrew:\n"
            "  brew install --cask google-chrome   # or: brew install chromium"
        )
    elif system == "windows":
        raise RuntimeError(
            "Chromium/Chrome not found on Windows. Install Chrome:\n"
            "  https://www.google.com/chrome/"
        )
    else:
        raise RuntimeError(f"Unsupported OS for auto-install: {system}")

def open_earnings_page():
    chrome_binary = ensure_chromium_installed()

    opts = Options()
    opts.binary_location = chrome_binary
    # In containers/Codespaces, headless is safer. Remove this line if you want a visible window locally.
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,1000")

    # Use a Chromium driver (matches Debian/Ubuntu chromium builds)
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=opts)

    print(f"[info] Opening {URL} ...")
    driver.get(URL)
    print("[info] Page title:", driver.title)

    # Example: save a screenshot so you can confirm headless rendering
    driver.get_screenshot_as_file("nasdaq_earnings.png")
    print("[info] Saved nasdaq_earnings.png")

    time.sleep(2)
    driver.quit()

if __name__ == "__main__":
    open_earnings_page()
