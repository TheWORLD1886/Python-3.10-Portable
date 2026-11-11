"""Full research run: in-sample backtest, walk-forward out-of-sample, random benchmark.

Usage: python research/run_research.py data/raw/GC=F_60m_730d.json [--spread 0.35 --slippage 0.10]
Writes reports/research_<source>.json and reports/oos_trades.csv
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nti.analysis.sessions import session_of  # noqa: E402
from nti.analysis.volatility import atr  # noqa: E402
from nti.backtest import Costs, run_backtest  # noqa: E402
from nti.data import load_mt5_csv, load_yahoo_chart  # noqa: E402
from nti.metrics import summarize, verdict  # noqa: E402
from nti.strategy.liquidity_sweep import Params, Signal, generate_signals  # noqa: E402

GRID = {"rr": [1.5, 2.0, 3.0], "trend_filter": ["none", "with"], "min_touches": [1, 2],
        "max_pen_atr": [1.0, 1.5]}


def load(path: str) -> pd.DataFrame:
    return load_yahoo_chart(path) if path.endswith(".json") else load_mt5_csv(path)


def in_window(sigs, a, b):
    return [s for s in sigs if a <= s.time < b]


def walk_forward(df, costs, train_m=9, test_m=3):
    configs = [replace(Params(), **dict(zip(GRID, v))) for v in itertools.product(*GRID.values())]
    cache = {i: generate_signals(df, p) for i, p in enumerate(configs)}
    start, end = df.index[0], df.index[-1]
    oos, log = [], []
    t0 = start
    while True:
        tr_a, tr_b = t0, t0 + pd.DateOffset(months=train_m)
        te_b = tr_b + pd.DateOffset(months=test_m)
        if tr_b >= end:
            break
        best, best_score = None, -np.inf
        for i, p in enumerate(configs):
            t = run_backtest(df, in_window(cache[i], tr_a, tr_b), costs, max_hold=p.max_hold_bars)
            if len(t) >= 20 and t["r"].mean() > best_score:
                best, best_score = i, t["r"].mean()
        if best is not None:
            t = run_backtest(df, in_window(cache[best], tr_b, te_b), costs, max_hold=configs[best].max_hold_bars)
            oos.append(t)
            log.append({"train": [str(tr_a.date()), str(tr_b.date())], "test_end": str(min(te_b, end).date()),
                        "chosen": {k: getattr(configs[best], k) for k in GRID},
                        "train_expectancy_r": round(best_score, 3), "oos_trades": len(t),
                        "oos_expectancy_r": round(float(t["r"].mean()), 3) if len(t) else None})
        t0 = t0 + pd.DateOffset(months=test_m)
    allo = pd.concat(oos, ignore_index=True) if oos else pd.DataFrame()
    if not allo.empty:  # rebuild a single compounding equity curve across windows
        eq = 10_000.0 * np.cumprod(1 + 0.0025 * allo["r"].to_numpy())
        allo["equity"] = eq
    return allo, log, len(configs)


def random_benchmark(df, n_trades, rr, costs, sessions=("london", "newyork"), sims=300, seed=1):
    a = atr(df).to_numpy()
    sess = session_of(df.index).to_numpy()
    c = df["close"].to_numpy()
    eligible = np.where(np.isin(sess, sessions) & ~np.isnan(a))[0]
    eligible = eligible[eligible < len(df) - 2]
    rng = np.random.default_rng(seed)
    exps = []
    for _ in range(sims):
        bars_ = np.sort(rng.choice(eligible, size=min(n_trades, len(eligible)), replace=False))
        sigs = []
        for b in bars_:
            d = int(rng.choice([-1, 1]))
            sigs.append(Signal(int(b), df.index[b], d, c[b], c[b] - d * 1.0 * a[b], a[b], rr))
        t = run_backtest(df, sigs, costs)
        exps.append(t["r"].mean() if len(t) else np.nan)
    return np.array(exps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--spread", type=float, default=0.35)
    ap.add_argument("--slippage", type=float, default=0.10)
    args = ap.parse_args()
    df = load(args.data)
    costs = Costs(args.spread, args.slippage)
    out = {"source": df.attrs.get("source"), "bars": len(df), "from": str(df.index[0]), "to": str(df.index[-1]),
           "costs": asdict(costs), "default_params": asdict(Params())}

    sigs = generate_signals(df, Params())
    full = run_backtest(df, sigs, costs)
    out["full_sample_default"] = summarize(full)
    out["full_sample_default"]["verdict"] = verdict(out["full_sample_default"])
    gross = run_backtest(df, sigs, Costs(0, 0))
    out["full_sample_default_no_costs_expectancy_r"] = float(gross["r"].mean()) if len(gross) else None

    oos, log, n_cfg = walk_forward(df, costs)
    out["walk_forward"] = {"configs_tested_per_window": n_cfg, "windows": log, "oos": summarize(oos)}
    out["walk_forward"]["oos"]["verdict"] = verdict(out["walk_forward"]["oos"])

    if len(full):
        bench = random_benchmark(df, len(full), Params().rr, costs)
        out["random_benchmark"] = {
            "sims": len(bench), "mean_expectancy_r": float(np.nanmean(bench)),
            "p95_expectancy_r": float(np.nanpercentile(bench, 95)),
            "strategy_percentile": float((bench < full["r"].mean()).mean() * 100)}

    Path("reports").mkdir(exist_ok=True)
    tag = (df.attrs.get("source") or "data").replace(":", "_").replace("=", "")
    Path(f"reports/research_{tag}.json").write_text(json.dumps(out, indent=2, default=str))
    if not oos.empty:
        oos.to_csv(f"reports/oos_trades_{tag}.csv", index=False)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
