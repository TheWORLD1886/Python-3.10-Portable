# Instrucciones del proyecto (Neural Trading Intelligence)

Idioma: responder en español. El usuario está en Tijuana (America/Tijuana): dar las horas también en hora de Tijuana con a. m./p. m.

## Cuando el usuario pida "entradas" (de oro / XAUUSD)
Siempre, sin que lo vuelva a pedir:
1. Descargar datos frescos (desde `neural_trading_intelligence/`):
   ```
   python tools/download_yahoo.py GC=F data/raw/GC=F_60m_730d.json
   python tools/download_yahoo.py GC=F data/raw/GC=F_1d_max.json --interval 1d --since 946684800
   curl -s -A "NTI-research/0.2" -o data/raw/ff_calendar_thisweek.json https://nfs.faireconomy.media/ff_calendar_thisweek.json
   (download_yahoo.py valida la respuesta y no sobrescribe un archivo bueno si Yahoo da 429)
   ```
2. Medir la diferencia futuro−spot y el precio spot EN VIVO (XM GOLD es spot; Yahoo va ~10-15 min atrasado):
   `python tools/spot_basis.py`  (si dice "run again", usar el basis.json previo)
   Generar la gráfica de velas en precio SPOT con COMPRA (C1, C2) y VENTA (V1, V2) y la marca "AHORA":
   `python tools/entry_chart.py --spot --calendar data/raw/ff_calendar_thisweek.json`
   Si pide 5 minutos (M5): `python tools/download_yahoo.py GC=F data/raw/GC=F_5m_5d.json --interval 5m --range 5d` y usar
   `python tools/entry_chart.py --h1 data/raw/GC=F_5m_5d.json --tf M5 --spot --calendar data/raw/ff_calendar_thisweek.json`
   Recordar al usuario: las velas de XM en MT5 van en hora del servidor (UTC+2 = Tijuana +10 h).
3. Mirar la imagen (comprobar que no hay etiquetas solapadas) y enviarla al usuario con SendUserFile
   (status "normal", display "render"). El usuario la ve en iPhone.
4. Resumir en el chat: contexto (diario/H4/H1), cada entrada C/V con disparador, si va a favor o contra tendencia, entrada, SL, TP, R:R,
   invalidación, y eventos de alto impacto cercanos.

Reglas que no cambian: los niveles de liquidez son hipótesis; las compras son condicionales al disparador;
avisar si van contra la tendencia diaria; revisar si un disparador se activó desde el último análisis; precios spot estimados (GC=F − basis; pueden diferir décimas de XM);
la estrategia no tiene ventaja estadística demostrada; solo cuenta demo; nunca prometer ganancias.
