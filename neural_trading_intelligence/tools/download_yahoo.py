"""Download research data (H1, ~730 days) from Yahoo's chart endpoint.

Research only: unofficial API, rate-limited, futures (GC=F) differ from XM spot GOLD
(basis + contract rolls). For decisions, export the real XM history from MT5 instead.

Usage: python tools/download_yahoo.py GC=F data/raw/GC=F_60m_730d.json
"""
import sys
import urllib.request

sym, out = sys.argv[1], sys.argv[2]
url = f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}?interval=60m&range=730d"
req = urllib.request.Request(url, headers={"User-Agent": "NTI-research/0.2"})
with urllib.request.urlopen(req, timeout=60) as r, open(out, "wb") as f:
    f.write(r.read())
print("saved", out)
