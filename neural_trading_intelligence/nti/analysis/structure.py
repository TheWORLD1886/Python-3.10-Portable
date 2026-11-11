"""Market structure: swing points, BOS and CHoCH.

Swing high at bar j: high[j] is the strict max of high[j-k .. j+k]. It is only
*known* at bar j+k, so we report it there (confirmed_at). Using it earlier
would be look-ahead bias.

Trend state: +1 after a bullish break of structure, -1 after a bearish one.
  BOS   = break in the direction of the current trend (continuation)
  CHoCH = break against the current trend (change of character)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Swing:
    kind: str          # "high" | "low"
    price: float
    bar: int           # where the extreme happened
    confirmed_at: int  # first bar where it is knowable


def find_swings(df: pd.DataFrame, k: int = 3) -> list[Swing]:
    h, l = df["high"].to_numpy(), df["low"].to_numpy()
    out: list[Swing] = []
    for j in range(k, len(df) - k):
        win_h, win_l = h[j - k:j + k + 1], l[j - k:j + k + 1]
        if h[j] == win_h.max() and (win_h == h[j]).sum() == 1:
            out.append(Swing("high", float(h[j]), j, j + k))
        if l[j] == win_l.min() and (win_l == l[j]).sum() == 1:
            out.append(Swing("low", float(l[j]), j, j + k))
    out.sort(key=lambda s: (s.confirmed_at, s.bar))
    return out


def structure_events(df: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    """Per-bar columns: trend (+1/-1/0), event ('BOS_up','BOS_down','CHoCH_up','CHoCH_down',''),
    last_swing_high, last_swing_low (confirmed values only). Breaks use the bar close."""
    n = len(df)
    close = df["close"].to_numpy()
    swings = find_swings(df, k)
    by_conf: dict[int, list[Swing]] = {}
    for s in swings:
        by_conf.setdefault(s.confirmed_at, []).append(s)

    trend = np.zeros(n, dtype=int)
    event = np.array([""] * n, dtype=object)
    lsh = np.full(n, np.nan)
    lsl = np.full(n, np.nan)
    cur_t, sh, sl = 0, np.nan, np.nan
    sh_used = sl_used = True
    for i in range(n):
        for s in by_conf.get(i, []):
            if s.kind == "high":
                sh, sh_used = s.price, False
            else:
                sl, sl_used = s.price, False
        if not sh_used and close[i] > sh:
            event[i] = "BOS_up" if cur_t == 1 else "CHoCH_up"
            cur_t, sh_used = 1, True
        elif not sl_used and close[i] < sl:
            event[i] = "BOS_down" if cur_t == -1 else "CHoCH_down"
            cur_t, sl_used = -1, True
        trend[i], lsh[i], lsl[i] = cur_t, sh, sl
    return pd.DataFrame({"trend": trend, "event": event, "last_swing_high": lsh,
                         "last_swing_low": lsl}, index=df.index)
