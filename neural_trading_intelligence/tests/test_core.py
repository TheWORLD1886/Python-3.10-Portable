import numpy as np
import pandas as pd
import pytest

from nti.analysis.liquidity import LiquidityMap, equal_levels
from nti.analysis.sessions import previous_day_levels, session_of
from nti.analysis.structure import find_swings, structure_events
from nti.analysis.volatility import atr
from nti.backtest import Costs, run_backtest
from nti.metrics import summarize, verdict
from nti.risk import RiskConfig, RiskState, can_open, position_size
from nti.strategy.liquidity_sweep import Signal


def bars(closes, start="2025-01-06 00:00", freq="1h", wick=0.5):
    c = np.asarray(closes, dtype=float)
    prev = np.r_[c[0], c[:-1]]
    o = (prev + c) / 2  # open between prev close and close: avoids artificial equal highs
    idx = pd.date_range(start, periods=len(c), freq=freq, tz="UTC")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) + wick, "low": np.minimum(o, c) - wick,
                         "close": c, "volume": 1.0}, index=idx)


def test_swings_are_confirmed_k_bars_later():
    df = bars([1, 2, 3, 10, 3, 2, 1, 2, 3])
    sw = [s for s in find_swings(df, k=3) if s.kind == "high"]
    assert sw and sw[0].bar == 3 and sw[0].confirmed_at == 6


def test_no_lookahead_in_structure():
    """Appending future bars must not change past structure values."""
    rng = np.random.default_rng(0)
    path = 2000 + np.cumsum(rng.normal(0, 2, 400))
    full = structure_events(bars(path), k=3)
    part = structure_events(bars(path[:250]), k=3)
    pd.testing.assert_frame_equal(full.iloc[:250], part)


def test_choch_then_bos():
    up = list(range(100, 111)) + [108, 106, 104, 106, 108, 112, 114, 112, 110, 108, 106, 103, 100, 98]
    ev = structure_events(bars(up, wick=0.1), k=2)["event"]
    events = [e for e in ev if e]
    assert "CHoCH_up" in events or "BOS_up" in events
    assert any(e.endswith("down") for e in events)


def test_equal_levels_grouping():
    g = equal_levels([100.0, 100.1, 105.0, 99.95], tol=0.2)
    assert sorted(len(x) for x in g) == [1, 3]


def test_sweep_detected_and_not_on_breakout():
    # build a clear swing high at 110 then a wick through it that closes back below
    base = [100, 102, 104, 106, 110, 106, 104, 102, 101, 100, 101, 102, 103, 104, 105, 106]
    df = bars(base * 3, wick=0.3)
    i = len(df) - 1
    # sweep bar: high above every previous high, close back below
    df.iloc[i, df.columns.get_loc("high")] = df["high"].iloc[:i].max() + 0.5
    df.iloc[i, df.columns.get_loc("close")] = 104.0
    sweeps, _ = LiquidityMap(df, swing_k=2).run(min_pen_atr=0.0, max_pen_atr=10)
    assert any(s.bar == i and s.direction == "bearish" for s in sweeps)
    # same bar but closing ABOVE the level = breakout, not a sweep
    df.iloc[i, df.columns.get_loc("close")] = df["high"].iloc[:i].max() + 0.4
    sweeps, _ = LiquidityMap(df, swing_k=2).run(min_pen_atr=0.0, max_pen_atr=10)
    assert not any(s.bar == i and s.direction == "bearish" for s in sweeps)


def test_sessions_and_pdh():
    df = bars(np.arange(48) + 100.0)
    s = session_of(df.index)
    assert s.iloc[3] == "asia" and s.iloc[8] == "london" and s.iloc[15] == "newyork"
    p = previous_day_levels(df)
    assert np.isnan(p["pdh"].iloc[0]) and p["pdh"].iloc[24] == df["high"].iloc[:24].max()


def test_atr_positive():
    assert (atr(bars(np.arange(50) + 100.0)).dropna() > 0).all()


def test_position_size_respects_risk():
    lots = position_size(10_000, 0.0025, entry=2000.0, stop=1995.0, contract_size=100)
    assert lots == 0.05            # 25 USD risk / (5 USD * 100 oz) = 0.05 lots
    assert position_size(1_000, 0.0025, 2000.0, 1990.0) == 0.0  # below min lot -> no trade


def test_risk_gates():
    cfg = RiskConfig()
    st = RiskState(10_000, 10_000)
    assert can_open(cfg, st, 10_000, 0.3, "d1")[0]
    assert not can_open(cfg, st, 10_000, 5.0, "d1")[0]                 # spread
    assert can_open(cfg, st, 9_890, 0.3, "d1")[1] == "daily loss limit"
    ok, why = can_open(cfg, st, 9_400, 0.3, "d2")                       # 6% DD
    assert not ok and st.killed
    assert not can_open(cfg, st, 20_000, 0.3, "d3")[0]                  # kill switch latches


def test_backtest_pessimistic_same_bar_and_costs():
    df = bars([100] * 10, wick=0.0)
    # bar 2: huge range touching both stop and target -> must count as STOP
    df.iloc[2, df.columns.get_loc("high")] = 110
    df.iloc[2, df.columns.get_loc("low")] = 90
    sig = Signal(0, df.index[0], 1, 99, stop=99.0, risk_ref=1.0, rr=2.0)
    tr = run_backtest(df, [sig], Costs(spread=0.0, slippage=0.0))
    assert tr.iloc[0]["reason"] == "stop" and tr.iloc[0]["r"] == pytest.approx(-1.0)
    tr2 = run_backtest(df, [sig], Costs(spread=0.3, slippage=0.1))
    assert tr2.iloc[0]["r"] == pytest.approx(-1.4)


def test_verdict_requires_sample():
    tr = pd.DataFrame({"r": [2.0] * 10, "equity": np.linspace(10_050, 10_500, 10), "reason": "target"})
    assert verdict(summarize(tr)).startswith("INSUFFICIENT")
