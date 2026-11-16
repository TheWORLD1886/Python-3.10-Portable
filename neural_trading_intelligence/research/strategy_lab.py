"""Strategy lab: test a few well-known, hypothesis-driven gold strategies honestly.

Protocol
  * Daily strategies: parameters chosen on 2000-2012 (in-sample) by Sharpe,
    then evaluated UNCHANGED on 2013-2026 (out-of-sample). All grid points are
    reported so the choice can't hide a lucky cherry-pick.
  * Daily mark-to-market equity, fixed fractional risk per trade (position =
    risk / initial stop distance), costs on entry+exit, next-open execution.
  * Benchmark: buy & hold over the same period.

Usage: python research/strategy_lab.py data/raw/GC=F_1d_max.json data/raw/GC=F_60m_730d.json
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nti.analysis.sessions import session_range  # noqa: E402
from nti.analysis.volatility import atr  # noqa: E402
from nti.backtest import Costs, run_backtest  # noqa: E402
from nti.data import load_yahoo_chart  # noqa: E402
from nti.metrics import summarize, verdict  # noqa: E402
from nti.risk import RiskConfig  # noqa: E402

# research: measure the raw edge, do not let the live kill switch truncate the sample
NO_KILL = RiskConfig(max_daily_loss=1.0, max_drawdown=1.0)
from nti.strategy.liquidity_sweep import Signal  # noqa: E402

COST_FRAC = 0.0002      # round-trip cost as fraction of price (~0.8 USD at 4000)
RISK = 0.005            # 0.5 % equity risk per trade (daily systems)
SPLIT = "2013-01-01"


# ----------------------------------------------------------------------------- daily engine
def simulate(df: pd.DataFrame, entries: pd.Series, exit_fn, stop_atr: float, trail_atr: float | None,
             start=10_000.0):
    """entries: +1/-1/0 decided on bar close i -> executed at open i+1.
    exit_fn(i, direction) -> True to exit at next open (signal-based exit).
    Initial stop = entry -/+ stop_atr*ATR ; optional chandelier trailing stop."""
    o, h, l, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    a = atr(df, 20).to_numpy()
    ent = entries.to_numpy()
    n = len(df)
    eq = np.full(n, np.nan)
    equity, pos, units, stop, entry_px, risk_px, ext = start, 0, 0.0, 0.0, 0.0, 0.0, 0.0
    trades = []
    pending_exit = False
    for i in range(1, n):
        # 1) execute pending orders at today's open
        if pos != 0 and pending_exit:
            px = o[i]
            equity -= units * px * COST_FRAC / 2
            trades.append((pos * (px - entry_px) - entry_px * COST_FRAC) / risk_px)
            pos, pending_exit = 0, False
        if pos == 0 and ent[i - 1] != 0 and not np.isnan(a[i - 1]):
            pos = int(ent[i - 1])
            entry_px = o[i]
            risk_px = stop_atr * a[i - 1]
            stop = entry_px - pos * risk_px
            units = equity * RISK / risk_px
            equity -= units * entry_px * COST_FRAC / 2
            ext = entry_px
            prev_c = entry_px
        elif pos != 0:
            prev_c = c[i - 1]
        # 2) intrabar stop
        if pos != 0:
            hit = (l[i] <= stop) if pos == 1 else (h[i] >= stop)
            if hit:
                px = min(o[i], stop) if pos == 1 else max(o[i], stop)
                equity += units * pos * (px - prev_c) - units * px * COST_FRAC / 2
                trades.append((pos * (px - entry_px) - entry_px * COST_FRAC) / risk_px)
                pos = 0
            else:
                equity += units * pos * (c[i] - prev_c)
                if trail_atr:
                    ext = max(ext, h[i]) if pos == 1 else min(ext, l[i])
                    cand = ext - pos * trail_atr * a[i]
                    stop = max(stop, cand) if pos == 1 else min(stop, cand)
                if exit_fn(i, pos):
                    pending_exit = True
        eq[i] = equity
    eq[0] = start
    return pd.Series(eq, index=df.index).ffill(), np.array(trades)


def stats(eq: pd.Series, trades: np.ndarray | None = None) -> dict:
    r = eq.pct_change().dropna()
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    dd = (eq / eq.cummax() - 1).min()
    out = {"cagr_pct": round(((eq.iloc[-1] / eq.iloc[0]) ** (1 / yrs) - 1) * 100, 2),
           "sharpe": round(float(r.mean() / r.std() * np.sqrt(252)), 2) if r.std() > 0 else 0.0,
           "max_dd_pct": round(float(dd * 100), 1),
           "return_pct": round(float((eq.iloc[-1] / eq.iloc[0] - 1) * 100), 1)}
    if trades is not None and len(trades):
        w, ls = trades[trades > 0], trades[trades <= 0]
        boot = np.random.default_rng(3).choice(trades, (4000, len(trades))).mean(1)
        out.update({"trades": int(len(trades)), "win_rate": round(len(w) / len(trades), 3),
                    "expectancy_r": round(float(trades.mean()), 3),
                    "expectancy_r_ci95": [round(float(np.percentile(boot, 2.5)), 3),
                                          round(float(np.percentile(boot, 97.5)), 3)],
                    "profit_factor": round(float(w.sum() / -ls.sum()), 2) if ls.sum() < 0 else None})
    return out


def donchian(df, n_entry, n_exit, long_only):
    hi = df["high"].rolling(n_entry).max().shift(1)
    lo = df["low"].rolling(n_entry).min().shift(1)
    ent = pd.Series(0, index=df.index)
    ent[df["close"] > hi] = 1
    if not long_only:
        ent[df["close"] < lo] = -1
    xhi = df["high"].rolling(n_exit).max().shift(1).to_numpy()
    xlo = df["low"].rolling(n_exit).min().shift(1).to_numpy()
    c = df["close"].to_numpy()
    return ent, (lambda i, p: (p == 1 and c[i] < xlo[i]) or (p == -1 and c[i] > xhi[i]))


def ma_trend(df, fast, slow, long_only):
    f, s = df["close"].rolling(fast).mean(), df["close"].rolling(slow).mean()
    up = (f > s) & (df["close"] > s)
    dn = (f < s) & (df["close"] < s)
    ent = pd.Series(0, index=df.index)
    ent[up] = 1
    if not long_only:
        ent[dn] = -1
    upn, dnn = up.to_numpy(), dn.to_numpy()
    return ent, (lambda i, p: (p == 1 and not upn[i]) or (p == -1 and not dnn[i]))


def run_daily(df):
    grids = {
        "donchian": [dict(n_entry=a, n_exit=b, long_only=lo) for a, b, lo in
                     itertools.product([20, 55, 100], [10, 20], [True, False]) if b < a],
        "ma_trend": [dict(fast=a, slow=b, long_only=lo) for a, b, lo in
                     itertools.product([20, 50], [100, 200], [True, False])],
    }
    builders = {"donchian": donchian, "ma_trend": ma_trend}
    stops = [dict(stop_atr=2.0, trail_atr=None), dict(stop_atr=3.0, trail_atr=3.0)]
    ins, oos = df[df.index < SPLIT], df[df.index >= pd.Timestamp(SPLIT, tz="UTC") - pd.Timedelta(days=400)]
    res = {}
    for name, grid in grids.items():
        rows = []
        for g, st in itertools.product(grid, stops):
            e_in, x_in = builders[name](ins, **g)
            eq_in, tr_in = simulate(ins, e_in, x_in, **st)
            e_o, x_o = builders[name](oos, **g)
            eq_o, tr_o = simulate(oos, e_o, x_o, **st)
            keep = eq_o.index >= pd.Timestamp(SPLIT, tz="UTC")   # warm-up excluded from OOS stats
            ntr_o = tr_o[-max(1, int(round(len(tr_o) * keep.mean()))):] if len(tr_o) else tr_o
            rows.append({"params": {**g, **st}, "in_sample": stats(eq_in, tr_in),
                         "out_of_sample": stats(eq_o[keep], ntr_o)})
        best = max(rows, key=lambda r: r["in_sample"]["sharpe"])
        oos_sharpes = [r["out_of_sample"]["sharpe"] for r in rows]
        res[name] = {"chosen_on_in_sample": best,
                     "all_configs_oos_sharpe": {"min": min(oos_sharpes), "median": float(np.median(oos_sharpes)),
                                                "max": max(oos_sharpes), "n": len(rows)}}
    bh = lambda d: stats(d["close"] / d["close"].iloc[0] * 10_000)
    res["buy_and_hold"] = {"in_sample": bh(ins), "out_of_sample": bh(df[df.index >= SPLIT])}
    return res


# ----------------------------------------------------------------------------- intraday: Asia range breakout
def asia_breakout(df_h1, rr=1.5, costs=Costs()):
    rng = session_range(df_h1, "asia")
    a = atr(df_h1).to_numpy()
    c = df_h1["close"].to_numpy()
    hours = df_h1.index.hour
    day = df_h1.index.floor("D")
    sigs, traded = [], set()
    for i in range(len(df_h1) - 1):
        if not (7 <= hours[i] < 12) or day[i] in traded:
            continue
        ah, al = rng.iloc[i]
        if np.isnan(ah) or np.isnan(a[i]):
            continue
        width = ah - al
        if not (0.5 * a[i] <= width <= 4 * a[i]):     # skip degenerate / huge ranges
            continue
        if c[i] > ah:
            sigs.append(Signal(i, df_h1.index[i], 1, ah, al, c[i] - al, rr)); traded.add(day[i])
        elif c[i] < al:
            sigs.append(Signal(i, df_h1.index[i], -1, al, ah, ah - c[i], rr)); traded.add(day[i])
    t = run_backtest(df_h1, sigs, costs, risk=NO_KILL, max_hold=10)
    s = summarize(t)
    s["verdict"] = verdict(s)
    half = df_h1.index[len(df_h1) // 2]
    s["first_half_expectancy_r"] = float(t[t.signal_time < half]["r"].mean()) if len(t) else None
    s["second_half_expectancy_r"] = float(t[t.signal_time >= half]["r"].mean()) if len(t) else None
    return s


def main():
    daily = load_yahoo_chart(sys.argv[1])
    daily = daily[(daily.index.minute == 0) & (daily.index.second == 0)]   # drop live partial bar
    out = {"daily_source": daily.attrs.get("source"), "daily_range": [str(daily.index[0]), str(daily.index[-1])],
           "split": SPLIT, "risk_per_trade": RISK, "cost_frac_round_trip": COST_FRAC,
           "daily": run_daily(daily)}
    if len(sys.argv) > 2:
        h1 = load_yahoo_chart(sys.argv[2])
        out["asia_breakout_h1"] = {f"rr_{rr}": asia_breakout(h1, rr) for rr in (1.0, 1.5, 2.0)}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/strategy_lab.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
