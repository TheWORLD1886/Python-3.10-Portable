"""Liquidity-sweep reversal strategy for XAUUSD.

Hypothesis (to be TESTED, not assumed): when price runs an obvious liquidity
pool (swing extreme, equal highs/lows, Asia range, previous day H/L) during an
active session and immediately closes back inside, the stop-run often exhausts
and price rotates back. Entry on the next bar open, stop beyond the sweep wick,
target a fixed multiple of risk.

Every signal carries its evidence for and against so it can be audited.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from ..analysis.liquidity import LiquidityMap
from ..analysis.sessions import session_of
from ..analysis.structure import structure_events
from ..analysis.volatility import atr, regime
from ..data import resample


@dataclass
class Params:
    sessions: tuple[str, ...] = ("london", "newyork")
    min_pen_atr: float = 0.05       # sweep must go at least this far past the level
    max_pen_atr: float = 1.5        # deeper than this = breakout, not a sweep
    sl_buffer_atr: float = 0.15     # stop placed beyond the sweep wick
    max_sl_atr: float = 2.5         # skip if the stop would be too wide
    rr: float = 2.0                 # take-profit in multiples of risk
    max_hold_bars: int = 24
    htf_rule: str = "4h"            # higher timeframe for trend context
    trend_filter: str = "none"      # "none" | "with" (trade only with HTF trend)
    min_touches: int = 1            # 2 => only equal highs/lows
    skip_regimes: tuple[str, ...] = ("abnormal",)
    swing_k: int = 3


@dataclass
class Signal:
    bar: int
    time: pd.Timestamp
    direction: int          # +1 long, -1 short
    sweep_level: float
    stop: float             # absolute price; entry price is decided by the executor (next open)
    risk_ref: float         # reference risk distance (from sweep-bar close to stop)
    rr: float
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["time"] = str(self.time)
        return d


def htf_trend(df: pd.DataFrame, rule: str, k: int = 3) -> pd.Series:
    """Higher-timeframe structure trend mapped to the base timeframe using only CLOSED HTF bars."""
    htf = resample(df, rule)
    t = structure_events(htf, k)["trend"]
    # an HTF bar labelled T is only complete at T + rule
    t.index = t.index + pd.Timedelta(rule)
    return t.reindex(df.index, method="ffill").fillna(0).astype(int)


def generate_signals(df: pd.DataFrame, p: Params = Params()) -> list[Signal]:
    a = atr(df).to_numpy()
    sess = session_of(df.index).to_numpy()
    reg = regime(df).to_numpy()
    trend = htf_trend(df, p.htf_rule, p.swing_k).to_numpy()
    sweeps, _ = LiquidityMap(df, swing_k=p.swing_k).run(p.min_pen_atr, p.max_pen_atr)
    close = df["close"].to_numpy()
    out: list[Signal] = []
    for s in sweeps:
        i = s.bar
        if i + 1 >= len(df):
            continue
        d = -1 if s.direction == "bearish" else 1
        if sess[i] not in p.sessions or reg[i] in p.skip_regimes or s.touches < p.min_touches:
            continue
        if p.trend_filter == "with" and trend[i] != d:
            continue
        stop = s.extreme + d * -1 * p.sl_buffer_atr * a[i]
        risk = abs(close[i] - stop)
        if risk <= 0 or risk > p.max_sl_atr * a[i]:
            continue
        ev_for = [f"swept {'/'.join(s.sources)} at {s.level:.2f} and closed back inside",
                  f"penetration {s.penetration_atr:.2f} ATR (stop-run, not breakout)",
                  f"session={sess[i]}"]
        if s.touches > 1:
            ev_for.append(f"equal-level cluster ({s.touches} touches)")
        ev_against = []
        if trend[i] == -d:
            ev_against.append(f"counter to {p.htf_rule} structure trend")
        if reg[i] == "expansion":
            ev_against.append("volatility expansion regime")
        out.append(Signal(i, df.index[i], d, s.level, float(stop), float(risk), p.rr, ev_for, ev_against))
    return out
