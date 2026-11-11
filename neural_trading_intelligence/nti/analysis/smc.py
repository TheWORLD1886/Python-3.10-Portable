"""Smart-money-concept price patterns (pure price geometry - no claims about who traded).

FVG (fair value gap), bar i = third candle:
  bullish if low[i] > high[i-2], bearish if high[i] < low[i-2].
Displacement: candle body >= mult * ATR.
"""
from __future__ import annotations

import pandas as pd

from .volatility import atr


def fvg(df: pd.DataFrame, min_atr: float = 0.1) -> pd.DataFrame:
    a = atr(df)
    bull_gap = df["low"] - df["high"].shift(2)
    bear_gap = df["low"].shift(2) - df["high"]
    return pd.DataFrame({
        "fvg_bull": bull_gap > min_atr * a,
        "fvg_bull_top": df["low"].where(bull_gap > min_atr * a),
        "fvg_bull_bottom": df["high"].shift(2).where(bull_gap > min_atr * a),
        "fvg_bear": bear_gap > min_atr * a,
        "fvg_bear_top": df["low"].shift(2).where(bear_gap > min_atr * a),
        "fvg_bear_bottom": df["high"].where(bear_gap > min_atr * a),
    }, index=df.index)


def displacement(df: pd.DataFrame, mult: float = 1.2) -> pd.Series:
    body = (df["close"] - df["open"])
    a = atr(df)
    return pd.Series(0, index=df.index).mask(body >= mult * a, 1).mask(-body >= mult * a, -1)
