# Plan de implementación — Neural Trading Intelligence (XAUUSD)

Estado: **propuesta para aprobación**. Modo inicial: **observación + cuenta demo**. Ninguna orden real sin autorización explícita.

---

## 1. Principios de diseño

1. **Defensa en profundidad:** el riesgo se controla en dos capas independientes — Python (supervisor) y el EA en MQL5
   (guardia final). Si Python falla o se equivoca, el EA sigue aplicando límites duros.
2. **Claude supervisa, no reacciona a ticks.** La ejecución de baja latencia vive en MQL5. Claude investiga, revisa
   escenarios, audita métricas y propone cambios; no está en la ruta crítica de una orden.
3. **Cada dato lleva etiqueta de procedencia:** `OBSERVED` (bróker/fuente oficial), `ESTIMATED` (proxy calculado),
   `HYPOTHESIS` (interpretación, p. ej. “posible liquidity pool”).
4. **Ninguna estrategia se declara rentable** sin: muestra suficiente, walk-forward fuera de muestra, costes reales
   (spread+comisión+slippage), comparación con benchmark y corrección por pruebas múltiples.
5. **Prohibido:** martingala, grid, aumentar lote tras pérdidas, operar sin SL.

## 2. Arquitectura lógica

```
                 ┌──────────────────── VPS Windows (producción) ─────────────────────┐
                 │                                                                    │
 Bróker MT5 ◄───►│  MT5 Terminal ── EA "NTI_Executor" (MQL5)                          │
                 │       │           • lee intents de señal (cola en Common\Files)    │
                 │       │           • límites duros: riesgo/op, pérdida diaria, DD,  │
                 │       │             nº posiciones, spread máx., ventana de noticias│
                 │       │           • kill switch (archivo + GlobalVariable + input) │
                 │       │                                                            │
                 │  Python (servicios Windows, NSSM):                                 │
                 │   collector ─► storage (DuckDB/Parquet) ◄─ news_intel              │
                 │        │               │                       │                   │
                 │        └──► analysis (structure, liquidity, smc, orderflow*,       │
                 │                       volatility, sessions, correlation)           │
                 │                         │                                          │
                 │                    signal_engine (3 escenarios) ─► risk_manager ─► intents
                 │                         │                                          │
                 │                    monitor: heartbeat, logs JSON, alertas Telegram │
                 └──────────────────────────┬─────────────────────────────────────────┘
                                            │ informes / MCP MT5 (cuando estén instalados)
                                       Claude (supervisor e investigador)
   Desarrollo y backtesting: este repo + contenedor Linux (datos Dukascopy/FRED/Treasury)
   * order flow = proxies ESTIMADOS salvo que se contraten datos de futuros GC
```

Separación pedida → módulos:

| Capa | Paquete | Ejecuta en |
|---|---|---|
| Recolección de datos | `nti/collectors/` (mt5, dukascopy, fred, treasury, calendar, rss) | VPS (MT5) / cualquier host (resto) |
| Almacenamiento | `nti/storage/` (Parquet particionado + DuckDB; SQLite para estado/logs de decisiones) | VPS + backup a almacenamiento de objetos |
| Procesamiento | `nti/features/` (barras multi-TF, sesiones, ATR, retornos) | idem |
| Inteligencia de noticias | `nti/news/` (normalización: fuente, hora+zona, impacto, activos, escenarios, reacción de mercado) | idem |
| Análisis | `nti/analysis/` (structure, liquidity, smc, orderflow, volatility, sessions, correlation) | idem |
| Cuantitativo | `nti/quant/` (backtester orientado a eventos, walk-forward, métricas, régimen, benchmark) | dev / VPS |
| Señales | `nti/signals/` (motor de decisión 8 pasos → 3 escenarios) | VPS |
| Riesgo | `nti/risk/` (Python) + `mql5/Include/NTI/Risk.mqh` (EA) | VPS |
| Ejecución | `mql5/Experts/NTI_Executor.mq5` | VPS (MT5) |
| Monitoreo | `nti/monitor/` (heartbeat, watchdog, alertas) | VPS |

## 3. Despliegue en la nube (recomendación preliminar, a confirmar en Fase 2)

* **VPS Windows Server** cercano al servidor del bróker (latencia típica objetivo < 20 ms). 2–4 vCPU, 4–8 GB RAM,
  60+ GB SSD. Opciones a comparar en Fase 2: proveedores de “Forex VPS”, AWS Lightsail/EC2 Windows, Azure, Contabo.
  El **VPS integrado de MetaQuotes** es barato pero **solo ejecuta EAs**, no Python ni servicios propios →
  útil como respaldo del EA, no como plataforma completa.
* Python 3.10 (el portable de este repo es compatible con el paquete `MetaTrader5`) ejecutado como servicios
  Windows con reinicio automático (NSSM) y Programador de tareas para el arranque del terminal.
* **Credenciales:** Windows Credential Manager / variables de entorno protegidas; nunca en git. Cuenta demo primero.
* **Recuperación ante fallos:** watchdog que reinicia terminal y servicios; EA con estado persistente;
  reconciliación de posiciones al reiniciar; alerta si el heartbeat cae > N minutos.
* **Backups:** Parquet/DuckDB y logs de decisiones a almacenamiento de objetos diario.

## 4. Fases, entregables y qué puede verificarse dónde

| Fase | Entregables | Verificable en este contenedor | Requiere VPS/MT5 |
|---|---|---|---|
| **1. Auditoría** ✅ | `tools/audit_environment.py`, `docs/01_AUDITORIA_FASE1.md` | Sí | Repetir la auditoría en el VPS (bróker, símbolos, DOM) |
| **2. Arquitectura y proveedores** | ADRs: VPS, bróker, datos, almacenamiento, puente Python↔EA; matriz de proveedores con costes | Sí (documental) | Medir latencia al bróker |
| **3. Datos y almacenamiento** | Colectores con rate limit/backoff, esquema Parquet, control de calidad (huecos, ticks duplicados, timezones UTC), descarga histórica XAUUSD Dukascopy | Sí (Dukascopy, Treasury, calendario, Fed RSS, FRED con key) | Colector MT5 (ticks y barras del bróker, spread real) |
| **4. Módulos de análisis** | structure (BOS/CHoCH multi-TF), liquidity (EQH/EQL, sweeps), smc (FVG, OB, breaker, mitigación, desplazamiento), volatility (ATR, régimen), sessions, correlation, orderflow (proxies), news_intel. Tests unitarios con casos sintéticos + datos reales | Sí | Validar contra datos del bróker |
| **5. Cuantitativo y señales** | Backtester con costes, métricas (expectancy, PF, win rate, max DD, Sharpe/Sortino, distribución), walk-forward, benchmark (buy&hold, aleatorio con mismo nº de trades), detección de régimen, motor de decisión de 3 escenarios con confianza calibrada (fiabilidad histórica por bucket) | Sí | — |
| **6. Riesgo y ejecución demo** | `risk/` Python + EA MQL5 con límites duros y kill switch; cola de intents; modo `observe` → `demo` | Lógica Python sí; **EA no compilable aquí** | Compilar EA, pruebas en Strategy Tester y demo |
| **7. Validación** | Informe de backtest + walk-forward + forward demo (mín. varias semanas); análisis de overfitting (deflated Sharpe / PBO) | Backtest sí | Forward demo |
| **8. Nube y monitoreo** | Scripts de instalación del VPS, servicios, watchdog, alertas, runbook de apagado | Scripts sí | Despliegue real |

**Puerta de seguridad antes de cualquier ejecución automática:** se presentará arquitectura, pruebas, resultados
backtest/forward, riesgos conocidos, límites y mecanismo de apagado, y se esperará tu autorización explícita.

## 5. Límites de riesgo propuestos por defecto (configurables, conservadores)

| Control | Valor por defecto |
|---|---|
| Riesgo por operación | 0,25 % del equity |
| Pérdida diaria máxima | 1,0 % → bloquea nuevas entradas hasta el día siguiente |
| Drawdown máximo desde pico | 5 % → kill switch y revisión manual |
| Posiciones simultáneas | 1 en XAUUSD; exposición correlacionada (XAG, USD) contada conjuntamente |
| Spread máximo | percentil 95 del spread histórico de la sesión, o valor fijo |
| Noticias de alto impacto USD | sin nuevas entradas de −30 a +30 min |
| SL/TP | obligatorios, verificados tras el envío; si el bróker no los confirma → cerrar |
| Lote | calculado solo por riesgo y distancia al SL; nunca se incrementa tras pérdidas |

## 6. Próximo paso propuesto

Con tu aprobación, avanzo con **Fase 2 (documental) + Fase 3 (colectores y almacenamiento)** en este repositorio,
y empiezo la **Fase 4** con los módulos que no dependen del bróker (estructura, liquidez, SMC, volatilidad,
sesiones) probados sobre ticks reales de Dukascopy. En paralelo necesito las decisiones listadas en la sección 5
de la auditoría (bróker demo, VPS, API keys, canal de alertas).
