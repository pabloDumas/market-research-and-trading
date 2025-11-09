#!/usr/bin/env python3
"""
Extract tables/tabular-like data from a Yahoo Finance page.
Tested target: https://finance.yahoo.com/quote/ARKW/performance/
Dependencies: requests, pandas, beautifulsoup4, lxml
"""
import re
import json
import uuid
import pathlib
from typing import Any, Dict, Iterable, List, Tuple

import requests
import pandas as pd
from bs4 import BeautifulSoup

HEADERS = {
    # A realistic UA helps bypass basic bot filters
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def try_read_html_tables(html: str) -> List[pd.DataFrame]:
    """Extract any literal <table> elements with pandas.read_html."""
    try:
        # pandas will parse all <table> tags it finds
        dfs = pd.read_html(html)  # requires lxml
        return dfs
    except ValueError:
        # no tables found
        return []
    except Exception as e:
        print(f"[read_html] warning: {e}")
        return []

def extract_root_app_json(html: str) -> Dict[str, Any]:
    """
    Yahoo Finance pages embed a big JSON blob under 'root.App.main'.
    This finds and returns it as a Python dict (or {} if not found).
    """
    # Common pattern on Yahoo Finance
    m = re.search(r"root\.App\.main\s*=\s*({.*?});\s*</script>", html, re.DOTALL)
    if not m:
        return {}
    raw = m.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Sometimes they wrap JSON with anti-XSS; try a lenient cleanup
        raw = raw.replace("\\x2F", "/")
        try:
            return json.loads(raw)
        except Exception:
            return {}

def looks_like_tabular(obj: Any) -> bool:
    """
    Heuristic: a list of dicts with consistent keys looks like a table.
    """
    if not isinstance(obj, list) or not obj:
        return False
    if not all(isinstance(x, dict) for x in obj):
        return False
    # Require some overlap of keys for first few rows
    keys0 = set(obj[0].keys())
    if not keys0:
        return False
    for x in obj[1: min(10, len(obj))]:
        if not keys0.intersection(x.keys()):
            return False
    return True

def dfs_from_json(obj: Any) -> List[pd.DataFrame]:
    """
    Walk an arbitrary JSON tree and collect DataFrames from any table-like lists.
    """
    out: List[pd.DataFrame] = []

    def walk(x: Any, path: Tuple[str, ...]):
        if looks_like_tabular(x):
            try:
                df = pd.DataFrame(x)
                # Keep path so the caller can name files descriptively
                df._origin_path = "/".join(path) if path else "root"
                out.append(df)
            except Exception:
                pass
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(v, path + (str(k),))
        elif isinstance(x, list):
            for idx, v in enumerate(x):
                walk(v, path + (f"[{idx}]",))
        # primitives ignored

    walk(obj, tuple())
    return out

def save_tables(dfs: Iterable[pd.DataFrame], prefix: str = "table") -> List[pathlib.Path]:
    paths = []
    outdir = pathlib.Path("tables_out")
    outdir.mkdir(exist_ok=True)
    for i, df in enumerate(dfs, start=1):
        # Build a descriptive filename when possible
        origin = getattr(df, "_origin_path", "")
        safe = re.sub(r"[^A-Za-z0-9_\-\.]+", "_", origin)[:80] or str(uuid.uuid4())[:8]
        path = outdir / f"{prefix}_{i:02d}_{safe}.csv"
        df.to_csv(path, index=False)
        paths.append(path)
    return paths

def extract_all_tables(url: str) -> List[pd.DataFrame]:
    html = fetch_html(url)

    # 1) Literal <table> elements
    dfs_html = try_read_html_tables(html)

    # 2) Yahoo embedded JSON tables (root.App.main)
    data = extract_root_app_json(html)
    dfs_json = dfs_from_json(data) if data else []

    # 3) Also scan any <script type="application/json"> blocks for tabular blobs
    soup = BeautifulSoup(html, "lxml")
    for sc in soup.find_all("script", attrs={"type": "application/json"}):
        try:
            blob = json.loads(sc.text)
            dfs_json.extend(dfs_from_json(blob))
        except Exception:
            continue

    # Combine, de-duplicate by content/columns when possible
    all_dfs: List[pd.DataFrame] = []
    seen_fingerprints = set()
    for df in dfs_html + dfs_json:
        # Simple fingerprint of columns + first 5 rows
        cols = tuple(df.columns.astype(str).tolist())
        head = tuple(df.head(5).fillna("").astype(str).itertuples(index=False, name=None))
        fp = (cols, head)
        if fp not in seen_fingerprints:
            seen_fingerprints.add(fp)
            all_dfs.append(df)

    return all_dfs

if __name__ == "__main__":
    url = "https://finance.yahoo.com/quote/ARKW/performance/"
    tables = extract_all_tables(url)
    if not tables:
        print("No tables found. The page may require JS rendering or tighter headers/cookies.")
    else:
        print(f"Found {len(tables)} tables/tabular-like blocks.")
        for i, df in enumerate(tables, start=1):
            origin = getattr(df, "_origin_path", "unknown")
            print(f"\nTable {i} — source path: {origin}")
            # Compact preview
            print(df.head(10).to_string(index=False))

        # Save to CSVs
        paths = save_tables(tables, prefix="yahoo_ARKW_performance")
        print("\nSaved CSVs:")
        for p in paths:
            print("-", p.as_posix())
