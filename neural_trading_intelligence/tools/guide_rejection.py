"""Teaching figure: what a valid rejection (sweep + close back) looks like vs a breakout."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, MUTED, GRID, SURF = "#1f2328", "#6e7781", "#e6e8eb", "#ffffff"
UP, DOWN, LVL, ENTRY = "#2e9e6b", "#c94c4c", "#9a6700", "#2f6fdb"


def candles(ax, bars, x0=0):
    for i, (o, h, l, c) in enumerate(bars):
        col = UP if c >= o else DOWN
        ax.vlines(x0 + i, l, h, color=col, linewidth=1.6, zorder=2)
        ax.bar(x0 + i, max(abs(c - o), 0.25), bottom=min(o, c), color=col, width=0.6, zorder=3)


def panel(ax, title, verdict, ok, bars, level, lvl_label, notes, entry=None, sl=None, tp=None, key=None):
    ax.set_facecolor(SURF)
    candles(ax, bars)
    ax.axhline(level, color=LVL, linestyle=(0, (3, 3)), linewidth=1.2, zorder=1)
    ax.text(-0.6, level, lvl_label, fontsize=7.5, color=MUTED, va="bottom")
    if key is not None:
        o, h, l, c = bars[key]
        ax.add_patch(plt.Rectangle((key - 0.55, l - 0.6), 1.1, h - l + 1.2, fill=False,
                                   edgecolor=INK, linewidth=1, linestyle="--", zorder=4))
    for y, lab, colr in ((entry, "Entrada", ENTRY), (sl, "Stop Loss", DOWN), (tp, "Take Profit", UP)):
        if y is not None:
            ax.hlines(y, len(bars) - 0.5, len(bars) + 1.6, color=colr, linewidth=2)
            ax.text(len(bars) + 1.7, y, f"{lab} {y:.1f}", fontsize=7.2, color=INK, va="center")
    ax.set_title(title, fontsize=10, color=INK, loc="left", weight="bold", pad=22)
    ax.text(0.0, 1.015, verdict, transform=ax.transAxes, fontsize=8.5, weight="bold",
            color=UP if ok else DOWN, va="bottom")
    ax.text(0.0, -0.04, notes, transform=ax.transAxes, fontsize=7.4, color=INK, va="top", linespacing=1.5)
    ax.set_xlim(-1, len(bars) + 6)
    ax.set_xticks([]); ax.tick_params(axis="y", labelsize=7, colors=MUTED, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.6); ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_visible(False)


fig, axs = plt.subplots(1, 3, figsize=(13, 6.4), dpi=200)
fig.patch.set_facecolor(SURF)
L = 3868.0
# 1) valid bearish rejection at 3868
b1 = [(3856, 3860, 3855, 3859), (3859, 3864, 3858, 3863), (3863, 3866.5, 3861, 3865.5),
      (3865.5, 3871.5, 3864, 3864.8), (3864.8, 3865.5, 3858, 3859), (3859, 3860, 3852, 3853)]
panel(axs[0], "1 · RECHAZO (venta válida)", "✔ Se activa la VENTA", True, b1, L, "nivel 3868 (liquidez arriba)",
      "① La vela SUBE por encima de 3868 (mecha arriba):\n    barre los stops de los vendedores.\n"
      "② Pero CIERRA por DEBAJO de 3868.\n    → mecha larga arriba, cuerpo abajo.\n"
      "③ Entras en la apertura de la SIGUIENTE vela.\n"
      "    SL encima de la mecha (+ un poco).",
      entry=3864.8, sl=3872.6, tp=3841.6, key=3)
# 2) breakout - not a rejection
b2 = [(3856, 3860, 3855, 3859), (3859, 3864, 3858, 3863), (3863, 3866.5, 3861, 3865.5),
      (3865.5, 3873, 3865, 3872), (3872, 3876, 3870.5, 3875), (3875, 3879, 3873.5, 3878)]
panel(axs[1], "2 · RUPTURA (NO vender)", "✘ No hay entrada de venta", False, b2, L, "nivel 3868",
      "① La vela sube por encima de 3868…\n② …y CIERRA por ENCIMA (cuerpo arriba).\n"
      "    Eso no es rechazo: los compradores ganaron.\n"
      "③ La venta queda invalidada.\n"
      "    Siguiente zona de venta: 3881 (V2).", key=3)
# 3) valid bullish rejection at 3841.6
b3 = [(3852, 3853, 3847, 3848), (3848, 3849, 3844, 3845), (3845, 3846, 3842.5, 3843.5),
      (3843.5, 3845, 3837.8, 3844.6), (3844.6, 3850, 3844, 3849), (3849, 3854, 3848, 3853)]
panel(axs[2], "3 · RECHAZO alcista (compra C1)", "✔ Se activa la COMPRA (contra tendencia)", True, b3, 3841.6,
      "nivel 3841.6 (liquidez abajo)",
      "① La vela BAJA por debajo de 3841.6 (mecha abajo):\n    barre los stops de los compradores.\n"
      "② Pero CIERRA por ENCIMA de 3841.6.\n    → mecha larga abajo, cuerpo arriba.\n"
      "③ Entras en la siguiente vela.\n    SL debajo de la mecha (+ un poco).",
      entry=3844.6, sl=3836.5, tp=3868.0, key=3)
fig.suptitle("Cómo se ve un rechazo (barrido de liquidez) en velas de 5 minutos · ejemplo ilustrativo, no datos reales",
             fontsize=11.5, color=INK, x=0.01, ha="left", weight="bold")
fig.text(0.01, 0.015, "Regla de oro: lo que importa es dónde CIERRA la vela, no hasta dónde llega la mecha. "
         "Espera el cierre completo de la vela de 5 min antes de entrar. Si cierra al otro lado del nivel → ruptura, no entres.",
         fontsize=8, color=MUTED)
fig.subplots_adjust(left=0.04, right=0.97, top=0.83, bottom=0.30, wspace=0.35)
fig.savefig("docs/img/guia_rechazo.png", facecolor=SURF)
print("ok")
