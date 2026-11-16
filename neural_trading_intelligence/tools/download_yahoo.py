"""Download research data from Yahoo's chart endpoint (honest User-Agent, retries, never
overwrites a good file with an error page).

Research only: unofficial API, rate-limited, futures (GC=F) differ from XM spot GOLD.

Usage:
  python tools/download_yahoo.py GC=F data/raw/GC=F_60m_730d.json                # H1, 730 days
  python tools/download_yahoo.py GC=F data/raw/GC=F_5m_5d.json --interval 5m --range 5d
  python tools/download_yahoo.py GC=F data/raw/GC=F_1d_max.json --interval 1d --since 946684800
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("symbol")
ap.add_argument("out")
ap.add_argument("--interval", default="60m")
ap.add_argument("--range", default="730d")
ap.add_argument("--since", type=int, help="unix start (uses period1/period2 instead of range)")
a = ap.parse_args()
q = (f"interval={a.interval}&period1={a.since}&period2={int(time.time()) + 86400}" if a.since
     else f"interval={a.interval}&range={a.range}")
url = f"https://query2.finance.yahoo.com/v8/finance/chart/{a.symbol}?{q}"
for attempt in range(5):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NTI-research/0.2"})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
        json.loads(body)["chart"]["result"][0]["timestamp"]   # validate before writing
        Path(a.out).write_bytes(body)
        print("saved", a.out)
        sys.exit(0)
    except (urllib.error.URLError, KeyError, TypeError, ValueError) as e:
        wait = 5 * (attempt + 1)
        print(f"attempt {attempt + 1} failed ({e}); retry in {wait}s", file=sys.stderr)
        time.sleep(wait)
print("FAILED - previous file kept", file=sys.stderr)
sys.exit(1)
