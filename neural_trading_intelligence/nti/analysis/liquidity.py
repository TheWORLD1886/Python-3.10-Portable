"""Liquidity analysis.

IMPORTANT - epistemic status: we cannot observe stop orders in XAUUSD (OTC market).
A "liquidity pool" here is a HYPOTHESIS: a price level where stops are *likely*
resting because it is an obvious swing extreme, an equal-high/low cluster, a
session extreme or the previous day's high/low. A "sweep" is OBSERVED price
behaviour: price trades through the level and closes back on the original side.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .sessions import previous_day_levels, session_range
from .structure import find_swings
from .volatility import atr


@dataclass
class Pool:
    side: str            # "buy_side" (above price: buy stops) | "sell_side" (below: sell stops)
    price: float
    born: int            # bar index where the level became known
    sources: list[str] = field(default_factory=list)
    touches: int = 1     # >1 => equal highs/lows cluster
    swept_at: int | None = None


def equal_levels(prices: list[float], tol: float) -> list[list[float]]:
    """Group prices that lie within `tol` of each other (equal highs / equal lows)."""
    groups: list[list[float]] = []
    for p in sorted(prices):
        if groups and abs(p - np.mean(groups[-1])) <= tol:
            groups[-1].append(p)
        else:
            groups.append([p])
    return groups


@dataclass
class Sweep:
    bar: int
    direction: str       # "bearish" (swept buy-side, expect down) | "bullish"
    level: float
    extreme: float       # wick extreme of the sweep bar
    penetration_atr: float
    sources: list[str]
    touches: int


class LiquidityMap:
    """Maintains active pools bar by bar (causal) and detects sweeps."""

    def __init__(self, df: pd.DataFrame, swing_k: int = 3, eq_tol_atr: float = 0.15,
                 max_age_bars: int = 24 * 10, atr_n: int = 14):
        self.df = df
        self.atr = atr(df, atr_n).to_numpy()
        self.swings = find_swings(df, swing_k)
        self.eq_tol_atr = eq_tol_atr
        self.max_age = max_age_bars
        self.pdl = previous_day_levels(df)
        self.asia = session_range(df, "asia")

    def _new_levels(self, i: int, by_conf) -> list[Pool]:
        out = [Pool("buy_side" if s.kind == "high" else "sell_side", s.price, i, [f"swing_{s.kind}"])
               for s in by_conf.get(i, [])]
        idx = self.df.index
        if i == 0 or idx[i].floor("D") != idx[i - 1].floor("D"):
            pdh, pdl = self.pdl.iloc[i]
            if not np.isnan(pdh):
                out += [Pool("buy_side", float(pdh), i, ["PDH"]), Pool("sell_side", float(pdl), i, ["PDL"])]
        ah, al = self.asia.iloc[i]
        if not np.isnan(ah) and (i == 0 or np.isnan(self.asia.iloc[i - 1, 0])):
            out += [Pool("buy_side", float(ah), i, ["asia_high"]), Pool("sell_side", float(al), i, ["asia_low"])]
        return out

    def run(self, min_pen_atr: float = 0.05, max_pen_atr: float = 1.5) -> tuple[list[Sweep], list[Pool]]:
        """Walk forward through the data. Returns detected sweeps and all pools (with swept_at)."""
        h, l, c = (self.df[x].to_numpy() for x in ("high", "low", "close"))
        by_conf: dict[int, list] = {}
        for s in self.swings:
            by_conf.setdefault(s.confirmed_at, []).append(s)
        active: list[Pool] = []
        allp: list[Pool] = []
        sweeps: list[Sweep] = []
        for i in range(len(self.df)):
            a = self.atr[i]
            # 1) check sweeps against pools known BEFORE this bar
            if not np.isnan(a) and a > 0:
                for side, sign in (("buy_side", 1), ("sell_side", -1)):
                    hit = [p for p in active if p.side == side and
                           ((sign == 1 and h[i] > p.price) or (sign == -1 and l[i] < p.price))]
                    if not hit:
                        continue
                    for p in hit:
                        p.swept_at = i
                    # the deepest level taken decides the sweep
                    lvl = max(hit, key=lambda p: p.price) if sign == 1 else min(hit, key=lambda p: p.price)
                    extreme = h[i] if sign == 1 else l[i]
                    pen = abs(extreme - lvl.price) / a
                    closed_back = c[i] < lvl.price if sign == 1 else c[i] > lvl.price
                    if closed_back and min_pen_atr <= pen <= max_pen_atr:
                        srcs = sorted({s for p in hit for s in p.sources})
                        sweeps.append(Sweep(i, "bearish" if sign == 1 else "bullish", lvl.price,
                                            float(extreme), float(pen), srcs, max(p.touches for p in hit)))
                active = [p for p in active if p.swept_at is None]
            # 2) add levels that become known at the close of this bar
            for p in self._new_levels(i, by_conf):
                still_valid = (p.side == "buy_side" and p.price > c[i]) or (p.side == "sell_side" and p.price < c[i])
                if not still_valid:
                    continue
                tol = self.eq_tol_atr * (a if not np.isnan(a) else 0)
                twin = next((q for q in active if q.side == p.side and abs(q.price - p.price) <= tol), None)
                if twin:  # equal highs / lows: strengthen the existing pool
                    twin.touches += 1
                    twin.sources = sorted(set(twin.sources + p.sources + ["equal_level"]))
                    twin.price = max(twin.price, p.price) if p.side == "buy_side" else min(twin.price, p.price)
                else:
                    active.append(p)
                    allp.append(p)
            active = [p for p in active if i - p.born <= self.max_age]
        return sweeps, allp

    def snapshot(self, i: int, pools: list[Pool]) -> list[Pool]:
        """Pools that were active (known and not yet swept) at bar i."""
        return [p for p in pools if p.born <= i and (p.swept_at is None or p.swept_at > i)
                and i - p.born <= self.max_age]
