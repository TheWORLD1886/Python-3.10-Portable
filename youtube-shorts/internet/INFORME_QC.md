# Control de calidad — ¿Qué pasaría si Internet desapareciera mañana?

Video `internet_desaparece.mp4` · 3360 fotogramas · 1080×1920 · 30 fps. Revisión automática de todos los fotogramas (articulaciones de cada personaje + diferencia de imagen) y revisión visual de hojas de contacto (`qc_contactos/`).

| # | Plano | Corp. | Extr. | Cam. | Visual | Labios | Objetos | Temporal | Estado |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Wake | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 2 | Apps | — | — | — | — | — | — | 10 | aprobado |
| 3 | Beginning | — | — | — | — | — | — | 10 | aprobado |
| 4 | Streets | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 5 | ATM | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 6 | Banks | — | — | — | — | — | — | 10 | aprobado |
| 7 | Lines | 10 | 10 | 10 | 10 | 10 | — | 10 | aprobado |
| 8 | Register | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 9 | HowLong | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 10 | Office | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 11 | Hospital | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 12 | Airport | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 13 | StillMoving | — | — | — | — | — | — | 10 | aprobado |
| 14 | Coordination | — | — | — | — | — | — | 10 | aprobado |
| 15 | Danger | — | — | — | — | — | — | 10 | aprobado |
| 16 | Rumors | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 17 | Unknown | — | — | — | — | — | — | 10 | aprobado |
| 18 | Government | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |
| 19 | Button | 10 | 10 | 10 | 10 | 10 | 9.5 | 10 | aprobado |
| 20 | NotOneMachine | — | — | — | — | — | — | 10 | aprobado |
| 21 | Infra | — | — | — | — | — | — | 10 | aprobado |
| 22 | Extreme | — | — | — | — | — | — | 10 | aprobado |
| 23 | SevenDays | — | — | — | — | — | — | 10 | aprobado |
| 24 | Friend | 10 | 10 | 10 | 10 | 10 | 10 | 10 | aprobado |

## Errores encontrados y corregidos

| Detectado por | Plano(s) | Error | Corrección |
|---|---|---|---|
| revisión visual | 5–6 | El plano del cajero duraba 1.8 s: no alcanzaba la acción | Cajero y terminal unidos en un plano; aviso «TERMINALES DE PAGO: ERROR» |
| revisión visual | 23 | Calendario encimado con los subtítulos | Calendario más arriba |
| QC | 4, 16, 24 | **Codos saltando 1–2u** en gestos que suben (celular arriba, susurro, manos a la cabeza) | Tres arreglos en el rig compartido: (1) el gesto parte exactamente de la pose libre del brazo; (2) la mano viaja en arco por delante del cuerpo (antes pasaba por el hombro y el brazo quedaba plegado); (3) un polo alternativo evita la inestabilidad cuando el brazo se alinea con la dirección del codo. Gestos más largos (0.9–1.2 s) |
| QC | 2, 12, 21 | Elementos que aparecían de golpe y cortes duros dentro de un plano | Entradas desde fuera del cuadro y fundidos de 0.3 s |
| QC | 3 | Parpadeo de luces en destellos | Pulso suave |
| QC | 19 | La mano se separaba del botón después de presionarlo | Posición de reposo corregida (quedan 2 fotogramas a 3–4 px: 9.5) |
| error de código | 12 | El plano del aeropuerto fallaba al renderizar | Corregido |

## Limitaciones

- Un 10 significa que no se encontró ninguno de los errores que el sistema mide. La naturalidad la juzgué a ojo.
- Voz en off: nadie habla en cámara. La categoría labial solo verifica bocas cerradas sin diálogo.
- Manos circulares por estilo: no hay dedos.
- El guion es un escenario hipotético. No contiene cifras y el video lo indica en pantalla.
