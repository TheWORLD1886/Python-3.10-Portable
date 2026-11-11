"""Session intelligence (UTC). Hours are approximations: DST shifts London/NY by 1h.

Asia 00-07, London 07-13, New York 13-21, off-hours 21-24 (low liquidity, gold rollover).
"""
from __future__ import annotations

import pandas as pd

SESSIONS = {"asia": (0, 7), "london": (7, 13), "newyork": (13, 21), "off": (21, 24)}


def session_of(index: pd.DatetimeIndex) -> pd.Series:
    h = index.hour
    out = pd.Series("off", index=index)
    for name, (a, b) in SESSIONS.items():
        out[(h >= a) & (h < b)] = name
    return out


def session_range(df: pd.DataFrame, name: str = "asia") -> pd.DataFrame:
    """Running high/low of the given session for each UTC day, available only once the
    session has closed (causal). Columns: <name>_high, <name>_low."""
    a, b = SESSIONS[name]
    day = df.index.floor("D")
    in_sess = (df.index.hour >= a) & (df.index.hour < b)
    g = df[in_sess].groupby(day[in_sess])
    hi, lo = g["high"].max(), g["low"].min()
    out = pd.DataFrame(index=df.index, columns=[f"{name}_high", f"{name}_low"], dtype=float)
    closed = df.index.hour >= b
    out.loc[closed, f"{name}_high"] = day[closed].map(hi).values
    out.loc[closed, f"{name}_low"] = day[closed].map(lo).values
    return out


def previous_day_levels(df: pd.DataFrame) -> pd.DataFrame:
    """Previous UTC day's high/low (PDH/PDL), known from the first bar of the new day."""
    day = df.index.floor("D")
    daily = df.groupby(day).agg(high=("high", "max"), low=("low", "min"))
    prev = daily.shift(1)
    return pd.DataFrame({"pdh": day.map(prev["high"]).values, "pdl": day.map(prev["low"]).values},
                        index=df.index)
