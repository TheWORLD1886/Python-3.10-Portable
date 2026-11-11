"""Neural Trading Intelligence - XAUUSD market intelligence core.

All analysis functions are causal: the value at bar i only uses data up to
and including bar i (swing points are reported at the bar where they become
*confirmed*, not where they occurred). This is what makes backtests honest.
"""
__version__ = "0.2.0"
