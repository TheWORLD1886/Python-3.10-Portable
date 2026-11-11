"""Risk management. Identical rules are implemented in the MQL5 EA (the final guard).

Hard rules (not configurable away): stop-loss mandatory, lot size never increases
after a loss, no martingale, no grid, no averaging down.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class RiskConfig:
    risk_per_trade: float = 0.0025     # 0.25 % of equity
    max_daily_loss: float = 0.01       # 1 % -> no new trades until next day
    max_drawdown: float = 0.05         # 5 % from peak -> kill switch
    max_positions: int = 1
    max_spread: float = 0.60           # USD per oz; above this, no entries
    news_blackout_min: int = 30        # minutes before/after high-impact USD events


def position_size(equity: float, risk_frac: float, entry: float, stop: float,
                  contract_size: float = 100.0, lot_step: float = 0.01,
                  min_lot: float = 0.01, max_lot: float = 50.0) -> float:
    """Lots such that hitting the stop loses <= risk_frac * equity.

    XM GOLD: 1 lot = 100 oz (read the real value from SymbolInfo in the EA).
    Rounds DOWN; returns 0 if even the minimum lot would exceed the risk budget.
    """
    dist = abs(entry - stop)
    if dist <= 0 or equity <= 0:
        return 0.0
    raw = (equity * risk_frac) / (dist * contract_size)
    lots = math.floor(raw / lot_step + 1e-9) * lot_step
    if lots < min_lot:
        return 0.0
    return round(min(lots, max_lot), 2)


@dataclass
class RiskState:
    peak_equity: float
    day_start_equity: float
    day: object = None
    open_positions: int = 0
    killed: bool = False
    reason: str = ""


def can_open(cfg: RiskConfig, st: RiskState, equity: float, spread: float, today,
             news_blocked: bool = False) -> tuple[bool, str]:
    if st.day != today:
        st.day, st.day_start_equity = today, equity
    st.peak_equity = max(st.peak_equity, equity)
    if st.killed:
        return False, f"kill switch: {st.reason}"
    if equity <= st.peak_equity * (1 - cfg.max_drawdown):
        st.killed, st.reason = True, f"drawdown >= {cfg.max_drawdown:.1%}"
        return False, st.reason
    if equity <= st.day_start_equity * (1 - cfg.max_daily_loss):
        return False, "daily loss limit"
    if st.open_positions >= cfg.max_positions:
        return False, "max positions"
    if spread > cfg.max_spread:
        return False, f"spread {spread:.2f} > {cfg.max_spread:.2f}"
    if news_blocked:
        return False, "high-impact news blackout"
    return True, "ok"
