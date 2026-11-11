"""Data loading and normalisation. Every frame is OHLCV indexed by UTC timestamps.

Supported sources:
  * Yahoo chart JSON (research only: unofficial API, futures GC=F != XM spot GOLD)
  * CSV exported from MetaTrader 5 (the reference source for XM: same feed you trade)
  * Dukascopy minute candles (.bi5)
"""
from __future__ import annotations

import json
import lzma
import struct
from pathlib import Path

import numpy as np
import pandas as pd

COLS = ["open", "high", "low", "close", "volume"]


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df[COLS].astype(float)
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df[~df.index.duplicated(keep="last")].sort_index()
    # Repair impossible bars rather than silently trusting them
    df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
    df["low"] = df[["open", "high", "low", "close"]].min(axis=1)
    return df


def load_yahoo_chart(path: str | Path) -> pd.DataFrame:
    res = json.loads(Path(path).read_text())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True)
    df = pd.DataFrame({c: q[c] for c in COLS}, index=idx)
    df.attrs["source"] = f"yahoo:{res['meta']['symbol']}"
    df = _clean(df)
    # Yahoo appends a partial "live" bar; drop bars not aligned to the interval
    step = df.index.to_series().diff().mode().iloc[0]
    df = df[df.index.floor(step) == df.index]
    return df


def load_mt5_csv(path: str | Path, tz_offset_hours: float = 0.0) -> pd.DataFrame:
    """CSV from MT5 (File > Save in History Center, or our EA exporter).

    MT5 server time is broker time (XM: GMT+2 / GMT+3 in DST). Pass the offset
    so the index is converted to UTC.
    """
    raw = pd.read_csv(path, sep=None, engine="python")
    raw.columns = [c.strip("<>").lower() for c in raw.columns]
    if "date" in raw.columns and "time" in raw.columns:
        ts = pd.to_datetime(raw["date"] + " " + raw["time"])
    else:
        ts = pd.to_datetime(raw[raw.columns[0]])
    ts = ts - pd.Timedelta(hours=tz_offset_hours)
    vol = raw["tickvol"] if "tickvol" in raw.columns else raw.get("volume", 0)
    df = pd.DataFrame({"open": raw["open"].values, "high": raw["high"].values,
                       "low": raw["low"].values, "close": raw["close"].values,
                       "volume": np.asarray(vol, dtype=float)},
                      index=pd.DatetimeIndex(ts).tz_localize("UTC"))
    df.attrs["source"] = f"mt5csv:{Path(path).name}"
    return _clean(df)


def decode_dukascopy_candles(blob: bytes, day: pd.Timestamp, point: float = 1e-3) -> pd.DataFrame:
    """Decode a Dukascopy *_candles_min_1.bi5 file (one UTC day of 1-minute bars)."""
    raw = lzma.decompress(blob)
    rows = [struct.unpack(">IIIIIf", raw[i:i + 24]) for i in range(0, len(raw), 24)]
    if not rows:
        return pd.DataFrame(columns=COLS)
    a = np.array(rows, dtype=float)
    idx = pd.Timestamp(day).tz_localize("UTC") if pd.Timestamp(day).tzinfo is None else pd.Timestamp(day)
    idx = idx + pd.to_timedelta(a[:, 0], unit="s")
    # Dukascopy order: time, open, close, low, high, volume
    df = pd.DataFrame({"open": a[:, 1] * point, "high": a[:, 4] * point, "low": a[:, 3] * point,
                       "close": a[:, 2] * point, "volume": a[:, 5]}, index=idx)
    return _clean(df)


def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Aggregate to a higher timeframe. Bars are labelled by their open time."""
    out = df.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    return out.dropna(subset=["open"])
