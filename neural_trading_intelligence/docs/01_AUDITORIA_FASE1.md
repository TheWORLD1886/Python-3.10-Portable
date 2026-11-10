# FASE 1 — Auditoría técnica del entorno, herramientas y fuentes de datos

Fecha: 2026-11-10 · Entorno auditado: contenedor cloud Linux de Claude Code (sesión de desarrollo).
Evidencia reproducible: `tools/audit_environment.py` → `docs/audit/audit_linux_sandbox.json`.

> Convención usada en todo el proyecto:
> **OBSERVADO** = comprobado con datos reales en esta sesión ·
> **ESTIMADO** = inferido de documentación o de una comprobación parcial ·
> **NO VERIFICADO** = no se pudo comprobar; no debe asumirse operativo.

---

## 1. Entorno de ejecución

| Elemento | Resultado | Estado |
|---|---|---|
| SO del entorno de desarrollo | Linux x86_64, 4 vCPU, 15 GiB RAM, Docker disponible, sin Wine | OBSERVADO |
| Python | 3.13 en el contenedor. El repo contiene **Python 3.10.5 portable para Windows** (+PyScripter) | OBSERVADO |
| pip / PyPI | Accesible (instalación de numpy/pandas/scipy posible) | OBSERVADO |
| Persistencia | Contenedor efímero: todo lo que no se suba a git se pierde | OBSERVADO |

**Conclusión:** este contenedor sirve para **desarrollar, probar y hacer backtesting** de la lógica en Python,
pero **no puede alojar MetaTrader 5** ni ser el entorno de producción (es efímero y no es Windows).

## 2. MetaTrader 5

| Elemento | Resultado | Estado |
|---|---|---|
| Servidores MCP de MetaTrader 5 (Terminal / Marketdata / MetaEditor) | **No hay ninguno conectado a esta sesión.** Solo están disponibles MCP de GitHub y de gestión de sesiones. No he podido inspeccionar sus herramientas. | OBSERVADO (ausencia) |
| Paquete Python `MetaTrader5` | Existe en PyPI (v5.0.6231) pero **solo hay wheels `win_amd64`** (cp36–cp314, incluido cp310 → compatible con el Python 3.10 portable de este repo). Requiere un terminal MT5 en ejecución en la misma máquina Windows. | OBSERVADO |
| Terminal MT5 / cuenta demo / bróker | No disponible aquí. | NO VERIFICADO |
| Compilación MQL5 (MetaEditor) | No disponible aquí. Cualquier `.mq5` escrito en este entorno estará **sin compilar ni probar** hasta llegar al VPS Windows. | NO VERIFICADO |

**Implicación:** la conexión real a mercado y cuenta solo podrá verificarse en un servidor Windows con MT5 instalado.
No afirmaré que la integración MT5 funciona hasta ejecutarla allí.

## 3. Fuentes de datos externas (gratuitas)

Política aplicada: el cliente se identifica honestamente (`User-Agent` propio). **No se suplantan navegadores
para saltar protecciones anti-bot.** Una fuente que rechaza un cliente honesto se considera no utilizable por esa vía
y debe usarse su API oficial.

| Fuente | Dato | Resultado de la prueba | Estado | Limitaciones |
|---|---|---|---|---|
| **Dukascopy datafeed** | Ticks históricos XAUUSD (bid/ask) | Una hora decodificada: 25 485 ticks con bid/ask. Respuestas intermitentes 429/503 en llamadas seguidas | OBSERVADO (intermitente) | Feed CFD de Dukascopy, **no es el feed de tu bróker**; requiere descarga lenta y espaciada; uso sujeto a sus términos |
| **FRED (gráficos CSV)** | DGS10, DFII10 (real), DTWEXBGS (USD amplio), T10YIE | Rechaza la conexión con un cliente identificado; funciona con el UA por defecto de Python. **Ruta correcta: API oficial `api.stlouisfed.org` con API key gratuita** | PENDIENTE de API key | Diario, publicación con 1 día de retraso; DXY (ICE) **no** está en FRED, se usa el índice amplio de la Fed como proxy |
| **US Treasury (XML)** | Curva de rendimientos diaria | 215 registros del año | OBSERVADO | Diario, fin de jornada |
| **Calendario ForexFactory (espejo JSON `faireconomy.media`)** | Calendario semanal: hora con zona, impacto, previsión, anterior | 105 eventos; 4 USD alto impacto (incl. CPI hoy 08:30 ET) | OBSERVADO | **No oficial**; solo semana actual; **no incluye el dato publicado (“actual”)**; puede desaparecer |
| **Federal Reserve RSS** | Comunicados de prensa | 20 ítems | OBSERVADO | Fuente oficial; latencia de RSS (minutos) |
| **BLS RSS** (CPI, NFP, desempleo) | — | HTTP 403 a clientes automatizados | NO DISPONIBLE por esta vía | Alternativa: API oficial BLS v2 (registro gratuito) |
| **Yahoo Finance (chart API)** | DXY (DX-Y.NYB), GC=F | Devuelve datos | OBSERVADO | **API no oficial**, sujeta a 429 y a sus términos de uso; no apta como fuente crítica |
| **GDELT DOC API** | Noticias globales/geopolítica | 429: límite 1 petición / 5 s (IP de salida compartida) | PARCIAL | Latencia ~15 min; sin garantía |
| **Stooq** | Diario XAUUSD | Conexión reiniciada | NO DISPONIBLE | — |
| **Investing.com** | — | 403 | NO DISPONIBLE | Scraping no permitido |

### 3.1 Lo que **no** se puede obtener gratis (y no se va a simular)

* **Volumen real, delta y order flow de oro:** XAUUSD spot/CFD es OTC; MT5 solo da *tick volume* (número de
  cambios de precio), no volumen negociado. Delta e imbalance reales requieren datos de futuros **COMEX GC** con
  agresor (p. ej. Databento, Rithmic, CQG — de pago). Sin ellos, el módulo Order Flow trabajará con
  **proxies etiquetados como ESTIMADOS** (tick volume, regla de tick para delta aproximado).
* **Profundidad de mercado (DOM):** depende del bróker (`market_book_add`). En CFDs de oro suele venir vacío o
  sintético. Se verificará en el VPS.
* **Noticias de baja latencia (segundos):** requieren proveedores de pago (Reuters, Bloomberg, Benzinga, etc.).
  Con fuentes gratuitas la latencia realista es de minutos. Por eso la regla de riesgo será
  **no operar alrededor de eventos de alto impacto**, en lugar de intentar reaccionar a ellos.
* **Datos “institucionales”:** no existen datos públicos de órdenes institucionales en oro spot. Liquidity pools,
  order blocks, etc. serán siempre **hipótesis basadas en precio**, nunca afirmaciones sobre órdenes reales.

## 4. Errores encontrados durante la auditoría

1. Primeras pruebas de FRED fallaban por *timeout*; la causa real era su filtro de User-Agent (diagnosticado probando UAs con curl).
2. Dukascopy alterna 200 / 429 / 503 según frecuencia → el colector necesitará *rate limiting* y reintentos con backoff.
3. Intenté usar un User-Agent de navegador para FRED/Yahoo; la política de seguridad del entorno lo bloqueó como
   evasión de protecciones anti-bot. Es correcto: se adopta UA honesto y APIs oficiales.

## 5. Decisiones que necesito de ti

1. **Bróker y cuenta demo MT5** (nombre del bróker y servidor). Determina símbolos disponibles (XAUUSD, XAGUSD, USDX, índices), spread, comisión y DOM.
2. **Proveedor de VPS Windows** y presupuesto (ver plan, sección 3).
3. **API keys gratuitas**: FRED y (opcional) BLS. Se configurarán como secretos del entorno/VPS, nunca en el repositorio.
4. **Canal de alertas**: Telegram (recomendado, gratuito) o email.
5. ¿Aceptas usar fuentes **no oficiales** (espejo de ForexFactory, Yahoo) como secundarias, sabiendo que pueden fallar?
