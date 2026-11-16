"""Entry chart: H1 (or M5 with --tf M5) candles + liquidity + planned LONG and SHORT setups (entry / SL / TP).

Usage:
  python tools/entry_chart.py [--h1 data/raw/GC=F_60m_730d.json] [--d1 data/raw/GC=F_1d_max.json]
                              [--bars 120] [--out reports/charts]
Prints a JSON summary of the setups and writes a PNG (2x scale, phone friendly).

Epistemics shown on the chart:
  * candles, swings, sweeps = OBSERVED price
  * liquidity pools = HYPOTHESIS (stops not observable in OTC gold)
  * planned setups = CONDITIONAL plans, valid only if the trigger happens
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nti.analysis.liquidity import LiquidityMap  # noqa: E402
from nti.analysis.structure import structure_events  # noqa: E402
from nti.analysis.volatility import atr  # noqa: E402
from nti.data import load_yahoo_chart, resample  # noqa: E402
from nti.strategy.liquidity_sweep import Params, generate_signals  # noqa: E402

TF = "H1"  # timeframe label of the base data, set from --tf

# Palette: trading convention for candles (muted), one accent for entries, text in neutral ink
INK, MUTED, GRID, SURF = "#1f2328", "#6e7781", "#e6e8eb", "#ffffff"
UP, DOWN = "#2e9e6b", "#c94c4c"
ENTRY, SELLSIDE, BUYSIDE = "#2f6fdb", "#2f6fdb", "#9a6700"


def daily_trend_state(d1: pd.DataFrame) -> dict:
    c = d1["close"]
    s50, s100, s200 = (c.rolling(n).mean().iloc[-1] for n in (50, 100, 200))
    hi55 = d1["high"].rolling(55).max().iloc[-2]
    long_ok = bool(c.iloc[-1] > s100 and s50 > s100)
    short_ok = bool(c.iloc[-1] < s100 and s50 < s100)
    return {"close": float(c.iloc[-1]), "sma50": float(s50), "sma100": float(s100), "sma200": float(s200),
            "donchian55_high": float(hi55), "trend_system_long": long_ok, "trend_system_short": short_ok,
            "daily_label": "ALCISTA" if long_ok else ("BAJISTA" if short_ok else "neutral"),
            "trend_label": "ALCISTA (sistema de tendencia comprado)" if long_ok else
                           "NO ALCISTA (sistema de tendencia fuera: compras = contra tendencia)"}


def plan_setups(pools, a_h1: float, last: float, direction: int, max_setups: int = 2) -> list[dict]:
    """direction +1: buy after a sweep of sell-side liquidity below; -1: sell after a sweep of buy-side above."""
    if direction == 1:
        trig = sorted([p for p in pools if p.side == "sell_side" and p.price < last], key=lambda p: -p.price)
        tgt = sorted([p for p in pools if p.side == "buy_side" and p.price > last], key=lambda p: p.price)
    else:
        trig = sorted([p for p in pools if p.side == "buy_side" and p.price > last], key=lambda p: p.price)
        tgt = sorted([p for p in pools if p.side == "sell_side" and p.price < last], key=lambda p: -p.price)
    d = direction
    setups = []
    for k, p in enumerate(trig[:max_setups], 1):
        level = p.price
        entry = level + d * 0.1 * a_h1                     # estimated: close back inside the level
        stop = level - d * (0.6 + 0.15) * a_h1             # estimated sweep wick (~0.6 ATR) + buffer
        risk = abs(entry - stop)
        tps = [q.price for q in tgt if d * (q.price - entry) >= risk][:2] or [entry + d * 2 * risk]
        side_txt = (f"mecha bajo el nivel y CIERRE {TF} por encima" if d == 1
                    else f"mecha sobre el nivel y CIERRE {TF} por debajo")
        setups.append({
            "label": f"{'C' if d == 1 else 'V'}{k}", "direction": "COMPRA" if d == 1 else "VENTA",
            "level": round(level, 1), "sources": p.sources, "touches": p.touches,
            "trigger": f"vela {TF} barre {level:.1f}: {side_txt}",
            "entry_est": round(entry, 1), "stop_est": round(stop, 1),
            "tp1": round(tps[0], 1), "tp2": round(tps[1], 1) if len(tps) > 1 else None,
            "rr_tp1": round(abs(tps[0] - entry) / risk, 2),
            "invalidation": f"cierre {TF} {'bajo' if d == 1 else 'sobre'} {stop:.1f}",
        })
    return setups


def draw(df: pd.DataFrame, n_bars: int, pools, setups, past_sigs, trend: dict, h4_trend: int,
         h1_trend: int, out: Path, events: list[str], base_trend: int = 0) -> Path:
    v = df.iloc[-n_bars:]
    x = np.arange(len(v))
    fig = plt.figure(figsize=(11.5, 6.6), dpi=200)
    gs = fig.add_gridspec(1, 2, width_ratios=[3.0, 1], wspace=0.02)
    ax, side = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF); side.axis("off")
    o, h, l, c = (v[k].to_numpy() for k in ("open", "high", "low", "close"))
    col = np.where(c >= o, UP, DOWN)
    ax.vlines(x, l, h, color=col, linewidth=0.9, zorder=2)
    ax.bar(x, np.maximum(np.abs(c - o), 0.15), bottom=np.minimum(o, c), color=col, width=0.62,
           linewidth=0, zorder=3)

    lo_y, hi_y = l.min(), h.max()
    for st in setups:
        lo_y = min(lo_y, st["stop_est"], st["tp1"]); hi_y = max(hi_y, st["stop_est"], st["tp1"])
    pad = (hi_y - lo_y) * 0.05
    lo_y, hi_y = lo_y - pad, hi_y + pad
    width, gap = 5.0, 1.3
    x_end = len(v) + 1 + len(setups) * (width + gap) + 1

    # draw every pool line, but merge labels of levels that would overlap (< 2.5 % of the y-range apart)
    vis = sorted([p for p in pools if lo_y < p.price < hi_y], key=lambda p: p.price)
    groups: list[list] = []
    for p in vis:
        colr = SELLSIDE if p.side == "sell_side" else BUYSIDE
        ax.axhline(p.price, color=colr, linewidth=0.8, linestyle=(0, (2, 3)), alpha=0.75, zorder=1)
        if groups and p.price - groups[-1][-1].price < 0.025 * (hi_y - lo_y) and p.side == groups[-1][-1].side:
            groups[-1].append(p)
        else:
            groups.append([p])
    for g in groups:
        tag = "liq. abajo" if g[0].side == "sell_side" else "liq. arriba"
        ax.text(0.5, g[-1].price, f"{tag} " + " / ".join(f"{q.price:.1f}" for q in g),
                fontsize=6.3, color=MUTED, va="bottom", ha="left")

    # each setup in its own column right of the last candle: red = risk zone, green = reward zone
    for k, st in enumerate(setups):
        xa = len(v) + 1 + k * (width + gap); xb = xa + width
        ax.fill_between([xa, xb], st["stop_est"], st["entry_est"], color=DOWN, alpha=0.11, zorder=0, linewidth=0)
        ax.fill_between([xa, xb], st["entry_est"], st["tp1"], color=UP, alpha=0.11, zorder=0, linewidth=0)
        ax.hlines(st["entry_est"], xa, xb, color=ENTRY, linewidth=2, zorder=4)
        ax.hlines(st["stop_est"], xa, xb, color=DOWN, linewidth=1.2, zorder=4)
        ax.hlines(st["tp1"], xa, xb, color=UP, linewidth=1.2, zorder=4)
        va = "bottom" if st["direction"] == "COMPRA" else "top"
        ax.text((xa + xb) / 2, st["entry_est"], st["label"], fontsize=8, weight="bold", color=INK,
                ha="center", va=va, zorder=6)

    pos = {t: i for i, t in enumerate(v.index)}
    off = (hi_y - lo_y) * 0.02
    for sgn in past_sigs:
        if sgn.time in pos:
            i = pos[sgn.time]
            if sgn.direction == 1:
                ax.scatter(i, l[i] - off, marker="^", s=55, color=ENTRY, edgecolor=SURF, linewidth=1.5, zorder=5)
            else:
                ax.scatter(i, h[i] + off, marker="v", s=55, color=BUYSIDE, edgecolor=SURF, linewidth=1.5, zorder=5)

    if TF == "H1":
        ticks = [i for i, t in enumerate(v.index) if t.hour == 0]
        ax.set_xticks(ticks, [v.index[i].strftime("%d-%b") for i in ticks], fontsize=7, color=MUTED)
    else:
        ticks = [i for i, t in enumerate(v.index) if t.minute == 0 and t.hour % 2 == 0]
        ax.set_xticks(ticks, [v.index[i].strftime("%H:%M") for i in ticks], fontsize=7, color=MUTED)
    ax.tick_params(axis="y", labelsize=7, colors=MUTED, length=0)
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(-1, x_end)
    ax.set_ylim(lo_y, hi_y)
    ax.grid(axis="y", color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_visible(False)

    tr = {1: "alcista", -1: "bajista", 0: "neutral"}
    now = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC")
    fig.text(0.01, 0.965, f"Oro (GC=F) {TF} · entradas planificadas (compra y venta) · {now}", fontsize=11,
             color=INK, weight="bold")
    fig.text(0.01, 0.935, f"Última vela cerrada {v.index[-1]:%d-%b %H:%M} UTC · {v['close'].iloc[-1]:.1f}  ·  "
             f"Diario: {trend['daily_label']} (SMA100 {trend['sma100']:.0f})  ·  "
             f"H4 {tr[h4_trend]}  ·  H1 {tr[h1_trend]}" + (f"  ·  {TF} {tr[base_trend]}" if TF != "H1" else ""), fontsize=8, color=MUTED)

    y = 0.99
    def line(txt, size=7.3, color=INK, weight="normal", gap=0.034):
        nonlocal y
        side.text(0.02, y, txt, fontsize=size, color=color, weight=weight, va="top", transform=side.transAxes)
        y -= gap
    for st in setups:
        with_trend = (st["direction"] == "COMPRA" and trend["trend_system_long"]) or \
                     (st["direction"] == "VENTA" and trend["trend_system_short"])
        tag = "a favor de tendencia" if with_trend else "CONTRA tendencia"
        line(f"{st['label']} · {st['direction']} · liq. {st['level']:.1f}", 8.2, INK, "bold", 0.036)
        line(f"   {tag} · {st['touches']} toque{'s' if st['touches'] > 1 else ''}", 6.6,
             UP if with_trend else DOWN, gap=0.03)
        line("   " + (f"mecha bajo nivel + CIERRE {TF} encima" if st["direction"] == "COMPRA"
                      else f"mecha sobre nivel + CIERRE {TF} debajo"), 6.6, MUTED, gap=0.032)
        line(f"   Entrada ~{st['entry_est']:.1f} · SL ~{st['stop_est']:.1f}", 7.3, ENTRY, "bold", 0.032)
        tp2 = f" / {st['tp2']:.1f}" if st.get("tp2") else ""
        line(f"   TP {st['tp1']:.1f}{tp2} · R:R {st['rr_tp1']}", 7.3, INK, gap=0.05)
    line("Leyenda", 7.3, INK, "bold", 0.032)
    line("▲ / ▼ barrido alcista / bajista detectado", 6.4, MUTED, gap=0.028)
    line("··· azul: liquidez abajo · ocre: arriba (hipótesis)", 6.4, MUTED, gap=0.028)
    line("rojo = riesgo (hasta SL) · verde = objetivo", 6.4, MUTED, gap=0.028)

    foot = ("Entradas solo si se cumple el disparador. Entrada/SL estimados: recalcula con la mecha real. "
            "Precios de futuros: ajusta a GOLD de XM. Sin ventaja estadística demostrada · solo demo.")
    if events:
        foot = "Eventos USD alto impacto (no operar ±30 min): " + " | ".join(events) + "\n" + foot
    fig.text(0.01, 0.01, foot, fontsize=6.4, color=MUTED, va="bottom")
    fig.subplots_adjust(left=0.05, right=0.99, top=0.91, bottom=0.11)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"entradas_{TF}_{datetime.now(timezone.utc):%Y%m%d_%H%M}.png"
    fig.savefig(path, facecolor=SURF)
    plt.close(fig)
    return path


def upcoming_events(cal_path: str | None) -> list[str]:
    if not cal_path or not Path(cal_path).exists():
        return []
    now = pd.Timestamp.now(tz="UTC")
    out = []
    for e in json.loads(Path(cal_path).read_text()):
        t = pd.Timestamp(e["date"]).tz_convert("UTC")
        if e.get("country") == "USD" and e.get("impact") == "High" and now - pd.Timedelta("1h") <= t <= now + pd.Timedelta("72h"):
            out.append(f"{t:%a %H:%M} UTC {e['title']}")
    return out[:4]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h1", default="data/raw/GC=F_60m_730d.json")
    ap.add_argument("--d1", default="data/raw/GC=F_1d_max.json")
    ap.add_argument("--calendar", default=None)
    ap.add_argument("--bars", type=int, default=None, help="default 72 (H1) / 144 (M5)")
    ap.add_argument("--tf", default="H1", choices=["H1", "M5"], help="timeframe of --h1 data")
    ap.add_argument("--out", default="reports/charts")
    args = ap.parse_args()
    global TF
    TF = args.tf
    n_bars = args.bars or (72 if TF == "H1" else 144)

    h1 = load_yahoo_chart(args.h1)
    d1 = load_yahoo_chart(args.d1)
    d1 = d1[(d1.index.minute == 0) & (d1.index.second == 0)]
    trend = daily_trend_state(d1)
    h4_trend = int(structure_events(resample(h1, "4h"), 3)["trend"].iloc[-1])
    h1_trend = int(structure_events(resample(h1, "1h") if TF != "H1" else h1, 3)["trend"].iloc[-1])
    base_trend = int(structure_events(h1, 3)["trend"].iloc[-1])
    lm = LiquidityMap(h1)
    _, allp = lm.run()
    active = lm.snapshot(len(h1) - 1, allp)
    a = float(atr(h1).iloc[-1])
    last = float(h1["close"].iloc[-1])
    setups = plan_setups(active, a, last, 1) + plan_setups(active, a, last, -1)
    past_sigs = generate_signals(h1, Params())
    events = upcoming_events(args.calendar)
    path = draw(h1, n_bars, active, setups, past_sigs, trend, h4_trend, h1_trend, Path(args.out), events,
                base_trend)
    print(json.dumps({"chart": str(path), "last_bar": str(h1.index[-1]), "last": last, "atr_h1": round(a, 1),
                      "daily": trend, "tf": TF, "h4_trend": h4_trend, "h1_trend": h1_trend, "base_trend": base_trend, "events": events,
                      "setups": setups}, indent=2, default=str))


if __name__ == "__main__":
    main()
