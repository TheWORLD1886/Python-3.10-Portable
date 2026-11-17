"""Measure the futures-spot basis (GC=F minus spot XAU/USD) so charts can show spot prices,
which is what XM's GOLD tracks.

Why it is not trivial: Yahoo's GC=F is delayed ~10 min, Swissquote's public spot quote is live.
So each run (1) stores a live spot sample, (2) compares OLD samples with the GC=F 1-minute bar of the
same minute once Yahoo has published it, (3) saves the median of the latest aligned measurements.

Usage:  python tools/spot_basis.py          -> prints basis, writes data/raw/basis.json
Spot source: Swissquote public quotes (free, unofficial). XM's own price can still differ by a few
tenths (spread / feed); verify against the app.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data/raw/spot_samples.json"
BASIS = ROOT / "data/raw/basis.json"
GC1M = ROOT / "data/raw/GC=F_1m_1d.json"
SQ_URL = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"


def spot_now() -> tuple[float, float] | None:
    try:
        req = urllib.request.Request(SQ_URL, headers={"User-Agent": "NTI-research/0.2"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        p = d[0]["spreadProfilePrices"][0]
        return d[0]["ts"] / 1000, (p["bid"] + p["ask"]) / 2
    except Exception as e:  # noqa: BLE001
        print(f"spot quote failed: {e}", file=sys.stderr)
        return None


def main() -> int:
    samples = json.loads(SAMPLES.read_text()) if SAMPLES.exists() else []
    s = spot_now()
    if s:
        samples.append({"ts": s[0], "mid": s[1]})
    samples = [x for x in samples if x["ts"] > time.time() - 3 * 86400][-200:]
    SAMPLES.write_text(json.dumps(samples))

    subprocess.run([sys.executable, str(ROOT / "tools/download_yahoo.py"), "GC=F", str(GC1M),
                    "--interval", "1m", "--range", "1d"], capture_output=True)
    measured = []
    if GC1M.exists():
        r = json.loads(GC1M.read_text())["chart"]["result"][0]
        closes = {t // 60: c for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c}
        for x in samples:
            c = closes.get(int(x["ts"]) // 60)
            if c is not None:
                measured.append((x["ts"], c - x["mid"]))
    measured.sort()
    if measured:
        recent = [b for _, b in measured[-5:]]
        out = {"basis": round(statistics.median(recent), 2), "n": len(recent),
               "measured_at": measured[-1][0], "spot_now": s[1] if s else None}
        BASIS.write_text(json.dumps(out))
    elif BASIS.exists():
        out = json.loads(BASIS.read_text())
        out["note"] = "no new aligned sample yet (Yahoo delay); reusing previous basis"
    else:
        print("No aligned measurement yet: run again in ~12 minutes.", file=sys.stderr)
        return 1
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
