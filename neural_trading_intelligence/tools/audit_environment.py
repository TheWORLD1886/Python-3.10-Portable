"""Phase 1 - Environment & data-source audit (stdlib only, Python >= 3.10).

Checks the runtime, the MetaTrader5 Python bridge and the reachability AND
content of candidate free data sources. A source is marked OK only if real
parseable data comes back, never on HTTP status alone.

Usage:  python tools/audit_environment.py [--json out.json]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import platform
import sys
import time
import urllib.error
import urllib.request

# Policy: always identify honestly. We never impersonate a browser to get past
# a site's bot protection. A source that refuses an honest client is reported
# as NOT usable from here and must be accessed through its official API.
UA = "NTI-audit/0.1 (market-data research; contact: repo owner)"
TIMEOUT = 45
RETRIES = 3


def fetch(url: str, ua: str = UA) -> tuple[int, bytes]:
    """GET with retries on network errors (not on HTTP errors). status 0 = network failure."""
    last: tuple[int, bytes] = (0, b"")
    for attempt in range(RETRIES):
        req = urllib.request.Request(url, headers={"User-Agent": ua})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception as e:  # network-level failure -> retry with backoff
            last = (0, str(e).encode())
            time.sleep(2 ** attempt)
    return last


def check_fred(series: str):
    code, body = fetch(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}")
    rows = [r for r in csv.reader(io.StringIO(body.decode(errors="ignore"))) if len(r) == 2]
    valid = [r for r in rows[1:] if r[1] not in ("", ".")]
    if code == 200 and valid:
        return True, f"last={valid[-1][0]} value={valid[-1][1]} rows={len(valid)}"
    return False, f"http={code}"


def check_ff_calendar():
    code, body = fetch("https://nfs.faireconomy.media/ff_calendar_thisweek.json")
    try:
        data = json.loads(body)
        high_usd = [e for e in data if e.get("impact") == "High" and e.get("country") == "USD"]
        return True, f"events={len(data)} high_usd={len(high_usd)} sample={high_usd[:1]}"
    except Exception:
        return False, f"http={code}"


def check_rss(url: str):
    code, body = fetch(url)
    n = body.count(b"<item")
    return (code == 200 and n > 0), f"http={code} items={n}"


def check_yahoo(symbol: str):
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"
    for attempt in range(3):
        code, body = fetch(url)
        if code == 200:
            try:
                meta = json.loads(body)["chart"]["result"][0]["meta"]
                return True, f"price={meta.get('regularMarketPrice')} tz={meta.get('exchangeTimezoneName')}"
            except Exception:
                return False, "unparseable"
        time.sleep(2 ** attempt)
    return False, f"http={code} (rate limited / unofficial API)"


def check_treasury():
    year = dt.date.today().year
    code, body = fetch(
        "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
        f"?data=daily_treasury_yield_curve&field_tdr_date_value={year}")
    n = body.count(b"<entry")
    return (code == 200 and n > 0), f"http={code} entries={n}"


def check_dukascopy():
    """Decode a real hour of XAUUSD ticks. Note: Dukascopy months are 0-based in the URL."""
    import lzma
    import struct
    # 2026-09-02 14:00 UTC -> month index 08
    code, body = fetch("https://datafeed.dukascopy.com/datafeed/XAUUSD/2026/08/02/14h_ticks.bi5")
    if code != 200 or not body:
        return False, f"http={code}"
    raw = lzma.decompress(body)
    n = len(raw) // 20
    ticks = [struct.unpack(">IIIff", raw[i * 20:(i + 1) * 20]) for i in range(n)]
    if not ticks:
        return False, "empty hour"
    ms, ask, bid, _, _ = ticks[0]
    # XAUUSD point scale is 1e3 on Dukascopy
    return True, f"ticks_in_hour={n} first: +{ms}ms ask={ask/1e3} bid={bid/1e3} (CFD feed, not broker feed)"


def check_stooq():
    code, body = fetch("https://stooq.com/q/d/l/?s=xauusd&i=d")
    ok = code == 200 and b"Close" in body
    return ok, f"http={code}" + ("" if ok else f" no CSV, body starts: {body[:60]!r}")


def check_gdelt():
    code, body = fetch("https://api.gdeltproject.org/api/v2/doc/doc?query=gold%20fed&format=json&maxrecords=2&mode=artlist")
    try:
        arts = json.loads(body).get("articles", [])
        return True, f"articles={len(arts)}"
    except Exception:
        return False, f"http={code} (rate limit 1 req/5s)"


def check_mt5():
    try:
        import MetaTrader5 as mt5  # type: ignore
    except ImportError:
        return False, "MetaTrader5 package not installed (only win_amd64 wheels exist on PyPI)"
    if not mt5.initialize():
        return False, f"initialize() failed: {mt5.last_error()}"
    info = mt5.terminal_info()
    acc = mt5.account_info()
    sym = mt5.symbol_info("XAUUSD")
    mt5.shutdown()
    return True, f"terminal={getattr(info,'name',None)} trade_mode={getattr(acc,'trade_mode',None)} xauusd={'yes' if sym else 'no'}"


CHECKS = {
    "runtime": lambda: (True, f"python={sys.version.split()[0]} os={platform.system()} {platform.release()} arch={platform.machine()}"),
    "mt5_python_bridge": check_mt5,
    "fred_DGS10_10y_yield": lambda: check_fred("DGS10"),
    "fred_DFII10_real_yield": lambda: check_fred("DFII10"),
    "fred_DTWEXBGS_broad_usd": lambda: check_fred("DTWEXBGS"),
    "fred_T10YIE_breakeven": lambda: check_fred("T10YIE"),
    "forexfactory_calendar_json": check_ff_calendar,
    "fed_press_rss": lambda: check_rss("https://www.federalreserve.gov/feeds/press_all.xml"),
    "bls_rss": lambda: check_rss("https://www.bls.gov/feed/bls_latest.rss"),
    "treasury_yield_curve_xml": check_treasury,
    "yahoo_DXY_DX-Y.NYB": lambda: check_yahoo("DX-Y.NYB"),
    "yahoo_gold_futures_GC=F": lambda: check_yahoo("GC=F"),
    "dukascopy_xauusd_ticks": check_dukascopy,
    "stooq_xauusd_daily": check_stooq,
    "gdelt_news_api": check_gdelt,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    args = ap.parse_args()
    results = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "checks": {}}
    for name, fn in CHECKS.items():
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f"exception: {e!r}"
        results["checks"][name] = {"ok": ok, "detail": detail}
        print(f"[{'OK ' if ok else 'NO '}] {name:30s} {detail}")
        time.sleep(1)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
