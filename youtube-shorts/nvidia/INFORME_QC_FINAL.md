# Informe final de control de calidad — NVIDIA v2

Video: `nvidia_espia_v2.mp4` · 4890 fotogramas · 1080×1920 · 30 fps · 2:43.
Inspección automática de **todos** los fotogramas: articulaciones registradas por el rig en cada uno; diferencia de imagen en 4889 de 4890 (el primero no tiene anterior).
Además, revisión visual de hojas de contacto de cada plano (`out2/contactos/`, 1 de cada 3 fotogramas) y de fotogramas del video final.

## Resultado por plano (puntuación 0–10; «—» = no aplica en ese plano)

| # | Plano | Corp. | Extr. | Cam. | Visual | Labios | Objetos | Temporal | Medidas clave | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Scandal | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 2 | Relation | 10 | 10 | 10 | 10 | 10 | — | 10 | 398 poses · 0 agarres · 51 f caminando · error hueso 0.01% | aprobado |
| 3 | Secrets | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 4 | JensenIntro | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 159 poses · 28 agarres · 44 f caminando · error hueso 0.009% | aprobado |
| 5 | ChipsAI | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 6 | AliceIntro | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 187 poses · 28 agarres · 47 f caminando · error hueso 0.011% | aprobado |
| 7 | DataCenter | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 8 | Buyer | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 111 poses · 222 agarres · 0 f caminando · error hueso 0.01% | aprobado |
| 9 | Suspicion | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 174 poses · 296 agarres · 0 f caminando · error hueso 0.012% | aprobado |
| 10 | Surveil | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 845 poses · 75 agarres · 0 f caminando · error hueso 0.034% | aprobado |
| 11 | Intercept | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 12 | FBIWarn | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 600 poses · 497 agarres · 0 f caminando · error hueso 0.011% | aprobado |
| 13 | Photos | 10 | 10 | 10 | 10 | 10 | — | 10 | 732 poses · 0 agarres · 0 f caminando · error hueso 0.025% | aprobado |
| 14 | NatSec | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 15 | Classified | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 16 | Problem | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 17 | ExportWall | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 18 | Board | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 528 poses · 220 agarres · 39 f caminando · error hueso 0.016% | aprobado |
| 19 | Statement | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 240 poses · 480 agarres · 0 f caminando · error hueso 0.01% | aprobado |
| 20 | Investors | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 360 poses · 113 agarres · 0 f caminando · error hueso 0.015% | aprobado |
| 21 | Capitol | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 22 | Questions | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 23 | Lawmakers | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 416 poses · 383 agarres · 0 f caminando · error hueso 0.018% | aprobado |
| 24 | Beijing | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 130 poses · 52 agarres · 0 f caminando · error hueso 0.011% | aprobado |
| 25 | Resign | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 410 poses · 135 agarres · 160 f caminando · error hueso 0.012% | aprobado |
| 26 | Infidelity | — | — | — | — | — | — | 10 | sin personajes | aprobado |
| 27 | Close | 10 | 10 | 10 | 10 | 10 | — | 10 | 810 poses · 0 agarres · 0 f caminando · error hueso 0.009% | aprobado |

## Errores detectados y corregidos durante la producción

| Ronda | Detectado por | Plano(s) | Error | Corrección | Verificado |
|---|---|---|---|---|---|
| Voz | Whisper | 0:21, 0:39, 2:06, 2:34 | «Envidia» ambigua (o contexto «de NVIDIA») | Regrabación de 4 frases y empalme; tiempos por palabra desplazados | 27/30 transcripciones «envidia» (ver `voz_segmentos/verificacion_whisper.json`) |
| 1 | QC | 4, 6, 18, 25 | Tobillos y manos saltando al entrar caminando | Caminata a velocidad natural: el personaje ya viene caminando antes del corte | sí |
| 1 | QC | 12 | Manos a 5–20 px de la carpeta (fuera de alcance) | Personajes reubicados a distancia de alcance; carpeta más angosta | sí |
| 1 | QC | 25 | Mano a 15–63 px del gafete (mesa fuera de alcance) | Mesa reubicada | sí |
| 1 | QC | 10 | Mano a 4.8u del monitor (inalcanzable); figuras de los monitores deslizándose | Gesto de señalar dentro del alcance; figuras quietas | sí |
| 1 | QC | 13 | Figuras de las fotos con arranque brusco | Entrada suave de las fotos | sí |
| 1 | QC | 15 | Expediente que aparecía de golpe en el cuadro | Entra desde fuera del cuadro | sí |
| 1–2 | QC | 4, 10, 12, 20 | Codos saltando en gestos hacia la cabeza (saludo, oreja, mentón, frente) | Gestos más lentos y con la mano por delante del cuerpo | sí |
| 2 | QC (falso positivo) | 15 | La métrica marcaba como «salto» un movimiento continuo y suave | Métrica de imagen cambiada a «pico respecto a los vecinos»; el error real de la ronda 1 (44.7 seguido de 12) sigue siendo detectado | sí |
| 3 | revisión visual | 25 | Colette quedaba encimada sobre Jensen | Colette se detiene más lejos; Jensen sale a ritmo constante | sí |
| 3 | revisión visual | 18 | Título cortado arriba por la cámara cerrada | Título dentro del encuadre | sí (fotograma del video final) |

## Limitaciones

- Un 10 significa que no se encontró ninguno de los errores **que el QC mide**. La naturalidad y la intención actoral se juzgaron a ojo, y por eso dos errores (planos 18 y 25) los encontró la revisión visual.
- Nadie habla en cámara (es voz en off). La categoría labial solo verifica que nadie mueva la boca sin diálogo.
- Las manos son círculos por estilo: no hay dedos ni giro de muñeca.
- Los giros de perfil a 3/4 son fundidos planificados de 0.2 s y se excluyen de la detección de saltos.
- Whisper no distingue matices finos de pronunciación. Conviene escuchar la voz final.
