#!/usr/bin/env python3
"""
Save server-rendered HTML of a page using requests + BeautifulSoup.

Note: This captures what the server returns. If the page is mostly
client-rendered (JavaScript), you'll need a browser driver (e.g., Selenium)
to get the fully rendered DOM.
"""

import os
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

URL = "https://www.nasdaq.com/market-activity/earnings"

def fetch_html(url: str, timeout: int = 20) -> requests.Response:
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    })

    retries = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))

    resp = s.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp

def save_html_files(resp: requests.Response, base_name: str = "nasdaq_earnings") -> tuple[str, str]:
    ts = time.strftime("%Y%m%d_%H%M%S")
    raw_path = Path(f"{base_name}_{ts}.html").resolve()
    pretty_path = Path(f"{base_name}_{ts}.pretty.html").resolve()

    # Save raw HTML bytes (exact server response)
    # requests will decode .text using apparent encoding; we keep bytes to be exact.
    raw_path.write_bytes(resp.content)

    # Optional: save a prettified version for human reading
    soup = BeautifulSoup(resp.text, "html.parser")
    # Warning: prettify() can reformat whitespace; keep raw file for exact copy.
    pretty_path.write_text(soup.prettify(), encoding="utf-8")

    return str(raw_path), str(pretty_path)

def main():
    try:
        resp = fetch_html(URL)
    except requests.HTTPError as e:
        print(f"[HTTP {e.response.status_code}] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[Error] {e}", file=sys.stderr)
        sys.exit(2)

    raw_file, pretty_file = save_html_files(resp)
    print("Saved files:")
    print(f" - Raw:      {raw_file}")
    print(f" - Prettied: {pretty_file}")

if __name__ == "__main__":
    main()
