"""Bar-based backtester with conservative assumptions.

* Entry at the NEXT bar's open after the signal (no trading on the signal close).
* Costs: spread + slippage (USD/oz) charged on every round trip.
* If stop and target are both inside the same bar, the STOP is assumed first.
* Gaps through the stop fill at the bar open (worse than the stop).
* One position at a time; risk limits from nti.risk apply.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .risk import RiskConfig, RiskState, can_open
from .strategy.liquidity_sweep import Signal


@dataclass
class Costs:
    spread: float = 0.35     # USD/oz, assumption for XM GOLD - replace with measured value
    slippage: float = 0.10   # USD/oz per round trip

    @property
    def total(self) -> float:
        return self.spread + self.slippage


def run_backtest(df: pd.DataFrame, signals: list[Signal], costs: Costs = Costs(),
                 risk: RiskConfig = RiskConfig(), start_equity: float = 10_000.0,
                 max_hold: int = 24) -> pd.DataFrame:
    o, h, l, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    idx = df.index
    by_bar = {s.bar: s for s in signals}
    st = RiskState(start_equity, start_equity)
    equity = start_equity
    trades = []
    i, n = 0, len(df)
    while i < n - 1:
        s = by_bar.get(i)
        if s is None:
            i += 1
            continue
        ok, why = can_open(risk, st, equity, costs.spread, idx[i + 1].date())
        if not ok:
            i += 1
            continue
        e_bar = i + 1
        entry = o[e_bar]
        stop = s.stop
        risk_dist = (entry - stop) * s.direction
        if risk_dist <= 0:     # gapped beyond the stop before entry -> skip
            i += 1
            continue
        target = entry + s.direction * s.rr * risk_dist
        exit_px, exit_bar, reason = None, None, None
        for j in range(e_bar, min(e_bar + max_hold, n)):
            if s.direction == 1:
                if l[j] <= stop:
                    exit_px, reason = (min(o[j], stop) if j > e_bar else stop), "stop"
                elif h[j] >= target:
                    exit_px, reason = (max(o[j], target) if j > e_bar else target), "target"
            else:
                if h[j] >= stop:
                    exit_px, reason = (max(o[j], stop) if j > e_bar else stop), "stop"
                elif l[j] <= target:
                    exit_px, reason = (min(o[j], target) if j > e_bar else target), "target"
            if exit_px is not None:
                exit_bar = j
                break
        if exit_px is None:
            exit_bar = min(e_bar + max_hold, n) - 1
            exit_px, reason = c[exit_bar], "time"
        gross = (exit_px - entry) * s.direction
        net = gross - costs.total
        r_mult = net / risk_dist
        pnl = equity * risk.risk_per_trade * r_mult
        equity += pnl
        trades.append({"signal_time": idx[i], "entry_time": idx[e_bar], "exit_time": idx[exit_bar],
                       "direction": s.direction, "entry": entry, "stop": stop, "target": target,
                       "exit": exit_px, "reason": reason, "risk_usd_oz": risk_dist,
                       "r": r_mult, "pnl": pnl, "equity": equity})
        i = exit_bar + 1
    return pd.DataFrame(trades)
