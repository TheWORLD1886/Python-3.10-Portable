# YouTube Short — "¿Qué pasaría si el crimen organizado tomara oficialmente la Presidencia?"

Formato: 60 s · 1080x1920 (9:16) · Stickman 3D evolucionado (cabeza esférica blanca mate, articulaciones orgánicas sin esferas mecánicas).

| Archivo | Uso |
|---|---|
| `elevenlabs_voz.txt` | Texto listo para pegar en ElevenLabs (con pausas `<break>` para llenar los 60 s). |
| `prompts.json` | Prompts visuales por escena, negative prompt, ajustes de voz, cámara y SFX. |

## Ajustes ElevenLabs
- Voz: **Brian C. - Professional Latin Narrator** (`uCQe5kObQIjtylU0HL3m`).
- Modelo: `eleven_multilingual_v2` (soporta `<break time="x.xs" />`).
- Stability 0.45 · Similarity 0.80 · Style 0.35 · Speaker boost ON · Speed 0.95.
- El guion tiene ~103 palabras; a ritmo natural dura ~45 s. Las pausas lo llevan a ~58–60 s.
  Si queda corto/largo, ajusta los `break` de 1.2 s entre escenas.

## Guion y timing
| Escena | Tiempo | Voz / subtítulo | Cámara |
|---|---|---|---|
| 1 | 00:00–00:08 | De las sombras al Palacio Nacional. ¿Qué pasaría si el crimen organizado tomara oficialmente la Presidencia? | Zoom-in rápido |
| 2 | 00:08–00:20 | Primero: Un Narco-Estado oficial. Las instituciones públicas se fusionarían con los carteles, legalizando sus operaciones y cobrando impuestos directos. | Orbital |
| 3 | 00:20–00:35 | Segundo: Intervención extranjera. Para potencias como Estados Unidos, esto sería una amenaza de seguridad nacional. Habría bloqueos comerciales e invasión militar. | Travelling, contrapicado |
| 4 | 00:35–00:48 | Tercero: Guerra civil interna. La disputa por el control total de los estados entre carteles rivales desataría un conflicto sin precedentes. | Push-in lento |
| 5 | 00:48–01:00 | El colapso de la democracia sería total. ¿Crees que este escenario está lejos de la realidad? ¡Comenta abajo y suscríbete! | Zoom suave |

## Cambios respecto al prompt original
- Se añadió un **estilo global** y un **negative prompt** (sin esferas en articulaciones, sin rasgos faciales, sin texto mal escrito) para mantener el stickman consistente entre escenas.
- Escena 3 incluye un stickman con uniforme militar en primer plano para respetar el estándar de personaje en todas las escenas.
- Escena 4: se corrigió "smoking smoke columns" → "rising columns of smoke" y se detalló el equipo táctico.
- Los textos "LEGALIZADO / IMPUESTO" y "BLOQUEO INTERNACIONAL" se recomiendan **en edición**: los generadores de video suelen deformar texto.
- Resolución explícita 1080x1920 en cada prompt.
