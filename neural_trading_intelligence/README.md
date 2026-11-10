# Neural Trading Intelligence (NTI)

Sistema modular de inteligencia de mercado y trading algorítmico para MetaTrader 5, especializado inicialmente en XAUUSD.

**Estado actual: Fase 1 completada (auditoría). Modo: observación. Sin ejecución de órdenes.**

| Documento | Contenido |
|---|---|
| [docs/01_AUDITORIA_FASE1.md](docs/01_AUDITORIA_FASE1.md) | Auditoría del entorno, MT5 y fuentes de datos, con evidencias |
| [docs/02_PLAN_IMPLEMENTACION.md](docs/02_PLAN_IMPLEMENTACION.md) | Arquitectura propuesta, fases, límites de riesgo |
| [docs/audit/](docs/audit/) | Resultados JSON de cada ejecución de la auditoría |

Repetir la auditoría (stdlib, Python ≥ 3.10; en el VPS Windows también comprueba el puente MetaTrader5):

```
python tools/audit_environment.py --json docs/audit/audit_<host>.json
```
