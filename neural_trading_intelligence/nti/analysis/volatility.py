"""Volatility: ATR, compression/expansion and regime classification (OBSERVED from price)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    prev = df["close"].shift(1)
    return pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(),
                      (df["low"] - prev).abs()], axis=1).max(axis=1)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Wilder ATR (causal)."""
    return true_range(df).ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def regime(df: pd.DataFrame, n: int = 14, lookback: int = 500) -> pd.Series:
    """'compression' / 'normal' / 'expansion' / 'abnormal' from ATR's rolling percentile."""
    a = atr(df, n)
    pct = a.rolling(lookback, min_periods=n * 5).rank(pct=True)
    labels = np.select([pct < 0.2, pct < 0.8, pct < 0.97], ["compression", "normal", "expansion"],
                       default="abnormal")
    out = pd.Series(labels, index=df.index)
    out[pct.isna()] = "unknown"
    return out
