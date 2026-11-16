# Instrucciones del proyecto (Neural Trading Intelligence)

Idioma: responder en español.

## Cuando el usuario pida "entradas" (de oro / XAUUSD)
Siempre, sin que lo vuelva a pedir:
1. Descargar datos frescos (desde `neural_trading_intelligence/`):
   ```
   python tools/download_yahoo.py GC=F data/raw/GC=F_60m_730d.json
   curl -s -A "NTI-research/0.2" -o data/raw/GC=F_1d_max.json "https://query2.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&period1=946684800&period2=1900000000"
   curl -s -A "NTI-research/0.2" -o data/raw/ff_calendar_thisweek.json https://nfs.faireconomy.media/ff_calendar_thisweek.json
   ```
2. Generar la gráfica de velas con las entradas LARGAS:
   `python tools/entry_chart.py --calendar data/raw/ff_calendar_thisweek.json`
3. Mirar la imagen (comprobar que no hay etiquetas solapadas) y enviarla al usuario con SendUserFile
   (status "normal", display "render"). El usuario la ve en iPhone.
4. Resumir en el chat: contexto (diario/H4/H1), cada compra C1/C2 con disparador, entrada, SL, TP, R:R,
   invalidación, y eventos de alto impacto cercanos.

Reglas que no cambian: los niveles de liquidez son hipótesis; las compras son condicionales al disparador;
avisar si van contra la tendencia diaria; precios de futuros GC=F (ajustar a GOLD de XM);
la estrategia no tiene ventaja estadística demostrada; solo cuenta demo; nunca prometer ganancias.
