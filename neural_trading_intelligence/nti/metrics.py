"""Performance statistics with uncertainty. A positive average is NOT evidence of an edge
unless the confidence interval excludes zero and it survives out-of-sample."""
from __future__ import annotations

import numpy as np
import pandas as pd


def summarize(trades: pd.DataFrame, start_equity: float = 10_000.0, n_boot: int = 5000,
              seed: int = 7) -> dict:
    if trades.empty:
        return {"trades": 0}
    r = trades["r"].to_numpy()
    wins, losses = r[r > 0], r[r <= 0]
    eq = np.concatenate([[start_equity], trades["equity"].to_numpy()])
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak
    rng = np.random.default_rng(seed)
    boot = rng.choice(r, size=(n_boot, len(r)), replace=True).mean(axis=1)
    t = r.mean() / (r.std(ddof=1) / np.sqrt(len(r))) if len(r) > 1 and r.std() > 0 else np.nan
    return {
        "trades": int(len(r)),
        "win_rate": float(len(wins) / len(r)),
        "avg_win_r": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss_r": float(losses.mean()) if len(losses) else 0.0,
        "expectancy_r": float(r.mean()),
        "expectancy_r_ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        "t_stat": float(t),
        "profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else float("inf"),
        "max_drawdown_pct": float(dd.min() * 100),
        "return_pct": float((eq[-1] / start_equity - 1) * 100),
        "max_consecutive_losses": int(max((len(x) for x in "".join("L" if v <= 0 else "W" for v in r).split("W")), default=0)),
        "exit_reasons": trades["reason"].value_counts().to_dict(),
    }


def verdict(stats: dict, min_trades: int = 100) -> str:
    if stats.get("trades", 0) < min_trades:
        return f"INSUFFICIENT SAMPLE ({stats.get('trades', 0)} < {min_trades} trades): no conclusion possible"
    lo, hi = stats["expectancy_r_ci95"]
    if lo > 0:
        return "POSITIVE EXPECTANCY (95% CI > 0) on this sample - still requires forward/demo confirmation"
    if hi < 0:
        return "NEGATIVE EXPECTANCY (95% CI < 0): do not trade"
    return "NOT DISTINGUISHABLE FROM ZERO: no demonstrated edge"
