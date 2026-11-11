# Neural Trading Intelligence (NTI)

Inteligencia de mercado y bot de liquidez para XAUUSD (XM: `GOLD`) en MetaTrader 5, desplegable en Linux.

**Estado (v0.2): análisis y backtesting operativos y probados; EA en modo observación, no compilado aún;
sin ventaja estadística demostrada. Solo cuentas demo.**

| Documento | Contenido |
|---|---|
| [docs/03_BOT_LIQUIDEZ_XM.md](docs/03_BOT_LIQUIDEZ_XM.md) | **Bot de liquidez: qué hace, resultados reales, cómo usarlo** |
| [docs/01_AUDITORIA_FASE1.md](docs/01_AUDITORIA_FASE1.md) | Auditoría del entorno y fuentes de datos |
| [docs/02_PLAN_IMPLEMENTACION.md](docs/02_PLAN_IMPLEMENTACION.md) | Arquitectura y fases |
| [reports/](reports/) | Resultados de backtest y walk-forward |

```
nti/            núcleo Python (estructura, liquidez, SMC, volatilidad, sesiones, riesgo, backtest)
research/       backtest + walk-forward + benchmark aleatorio
mql5/Experts/   Expert Advisor para MT5 (XM)
deploy/linux/   instalación MT5 + Wine + Xvfb + systemd en Ubuntu
tests/          tests unitarios (pytest)
tools/          auditoría de entorno, descarga de datos
```
