# Bot de liquidez XAUUSD para XM en Linux — versión 0.2

Fecha: 2026-11-11 · Estado: **investigación + EA en modo observación. Sin ventaja estadística demostrada.**

## 0. Aviso que no se puede quitar

No existe un bot "sin pérdidas y de pura ganancia". Cada operación puede perder, y en esta
estrategia **la mayoría pierden** (ganan ~31 %). El objetivo es que las ganadoras (más grandes)
compensen a las perdedoras (pequeñas, cortadas por el Stop Loss). Hoy **eso no está demostrado**.

## 1. Qué hace

1. **Detecta liquidez** (hipótesis, porque las órdenes stop no son observables en oro OTC):
   máximos/mínimos de swing confirmados, máximos/mínimos iguales (clusters), rango de Asia,
   máximo/mínimo del día anterior (PDH/PDL).
2. **Detecta barridos** (observado): el precio atraviesa el nivel entre 0,05 y 1,5 ATR y **cierra
   de vuelta** dentro. Si cierra fuera, es ruptura, no barrido, y no opera.
3. **Filtra**: solo Londres (07–13 UTC) y Nueva York (13–21 UTC); evita volatilidad anormal;
   opcional: solo a favor de la estructura de H4; bloquea noticias USD de alto impacto
   (calendario económico integrado de MT5).
4. **Opera** a la apertura de la vela siguiente: SL al otro lado de la mecha + 0,15 ATR,
   TP = 2 × riesgo, cierre por tiempo a las 24 velas.
5. **Gestiona riesgo** (Python y EA): 0,25 % por operación, pérdida diaria 1 %, drawdown 5 %
   → kill switch, 1 posición, spread máximo, SL/TP verificados tras abrir (si faltan, cierra).

## 2. Resultados reales (datos horarios GC=F, 2024-06-21 → 2026-11-11, 13 709 velas)

Costes supuestos: spread 0,35 + slippage 0,10 USD/oz por operación (**sin medir en XM**).
Supuesto pesimista: si SL y TP caen en la misma vela, cuenta como pérdida.

| Prueba | Ops | Win rate | Expectativa (R) | IC 95 % | PF | Max DD | Veredicto |
|---|---|---|---|---|---|---|---|
| Parámetros por defecto, muestra completa | 90* | 31 % | **−0,19** | [−0,47, +0,11] | 0,75 | −5,0 % | negativa, no significativa |
| Mismo sin costes | 90 | — | −0,13 | — | — | — | la señal en sí no tiene ventaja |
| **Walk-forward fuera de muestra** (7 ventanas, 24 configs) | 149 | 32 % | **+0,03** | [−0,23, +0,31] | 1,04 | −4,1 % | **no distinguible de cero** |
| Entradas aleatorias (300 simulaciones) | 90 | — | −0,06 media | p95 = +0,21 | — | — | la estrategia por defecto queda en el percentil 22 |

\* El backtest por defecto **se detuvo al tocar el 5 % de drawdown**: el kill switch funcionó.

**Interpretación honesta:**
- Con parámetros por defecto la estrategia perdió dinero y fue **peor que la mediana de entradas aleatorias**.
- Optimizando en ventanas pasadas y probando en las siguientes, el resultado fuera de muestra es ~0.
  Las últimas 4 ventanas (dic 2025 → nov 2026) son positivas (+0,34, +0,04, +0,05, +0,23 R), pero 149 operaciones no bastan para
  separar ventaja de suerte.
- Limitación de datos: son **futuros** (GC=F), no el **spot de XM**; hay saltos al cambiar de
  contrato y el horario difiere. Con velas H1 no se puede confirmar en M5/M15.

**Conclusión: no hay base para operar con dinero real. Sí la hay para observar y probar en demo.**

## 3. Archivos

| Archivo | Qué es | Verificado |
|---|---|---|
| `nti/analysis/structure.py` | Swings confirmados sin look-ahead, BOS/CHoCH | 11 tests ✅ (incluye test de no look-ahead) |
| `nti/analysis/liquidity.py` | Pools de liquidez, EQH/EQL, barridos | ✅ |
| `nti/analysis/volatility.py`, `sessions.py`, `smc.py` | ATR/régimen, sesiones/PDH/Asia, FVG/desplazamiento | ✅ (smc sin usar aún en la estrategia) |
| `nti/strategy/liquidity_sweep.py` | Señales con evidencias a favor/en contra | ✅ |
| `nti/risk.py`, `nti/backtest.py`, `nti/metrics.py` | Riesgo, backtester conservador, métricas con IC | ✅ |
| `research/run_research.py` | Backtest + walk-forward + benchmark aleatorio | ✅ ejecutado, `reports/` |
| `mql5/Experts/NTI_LiquiditySweep.mq5` | EA para MT5 de XM | ❌ **NO COMPILADO** (ver §4) |
| `deploy/linux/install_mt5_xm.sh`, `nti-mt5.service` | Instalación MT5 + Wine + Xvfb + systemd en Ubuntu | ❌ **NO PROBADO** (solo sintaxis bash) |

## 4. Lo que NO pude verificar

- Instalé Wine 9.0 y descargué el instalador oficial de MT5 en el entorno de desarrollo, pero la
  política de seguridad del entorno **bloqueó ejecutar el `.exe`**. Por eso el EA no se ha
  compilado con MetaEditor ni probado en el Strategy Tester. Puede tener errores de compilación.
- Nombre exacto del símbolo de oro y del servidor de XM en tu cuenta (normalmente `GOLD`; el EA
  avisa si el símbolo no contiene GOLD/XAU).
- Spread y comisión reales de XM en oro (dependen del tipo de cuenta).
- La paridad exacta EA ↔ Python: la lógica es la misma, pero el agrupado de niveles iguales es
  una aproximación en el EA.

## 5. Cómo usarlo (demo)

```bash
# 1. Investigación en Linux
pip install -r requirements.txt
python tools/download_yahoo.py GC=F data/raw/GC=F_60m_730d.json
python -m pytest -q tests
python research/run_research.py data/raw/GC=F_60m_730d.json --spread 0.35 --slippage 0.10

# 2. Servidor Ubuntu con MT5 de XM (cuenta DEMO)
mkdir -p ~/.nti && cp deploy/linux/xm_demo.env.example ~/.nti/xm_demo.env && chmod 600 ~/.nti/xm_demo.env
nano ~/.nti/xm_demo.env          # login, contraseña y servidor DEMO de XM
bash deploy/linux/install_mt5_xm.sh
```

- El EA arranca en **`InpMode = OBSERVE`**: dibuja los niveles de liquidez, registra cada barrido
  en `Common/Files/NTI/signals.csv` y **no envía órdenes**.
- `NTI_DEMO_TRADE` envía órdenes **solo si la cuenta es demo**; en real el EA se desactiva.
- **Apagado de emergencia**: crear el archivo `Common/Files/NTI/KILL` o la variable global
  `NTI_KILL = 1` → cierra las posiciones del EA y bloquea nuevas entradas.

## 6. Siguiente paso recomendado

1. Compilar el EA en tu servidor (el script lo intenta y muestra el log) y pasarme los errores si los hay.
2. **Exportar desde MT5 de XM el histórico real de GOLD en M5/M15/H1** (spread incluido) y repetir
   la investigación con esos datos: `python research/run_research.py export.csv`.
3. Dejar el EA en OBSERVE / demo **varias semanas** y comparar sus señales con el backtest.
4. Solo si la expectativa fuera de muestra es positiva con IC > 0 en datos de XM, discutir dinero real.
