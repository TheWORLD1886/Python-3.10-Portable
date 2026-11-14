# Propuesta de animación y control de calidad — NVIDIA

## 1. Voz

- Antes de enviar texto a ElevenLabs, `para_voz()` sustituye la palabra completa **NVIDIA → Envidia** y falla si queda alguna sin corregir. En pantalla sigue escrito NVIDIA.
- Verificación automática: cada segmento se transcribe con Whisper (reconocimiento de voz local) y se comprueba que se oiga «envidia».
  - Prueba: las 3 apariciones se transcribieron «envidia».
  - En el video anterior, Whisper oyó «Nvidia» en el segundo 0:20 (el error que reportaste).
- Se generan archivos de voz por bloque en `voz_segmentos/` para poder regrabar solo lo afectado.

## 2. Actuación (qué cambia frente al video anterior)

Antes, la mayoría de planos eran personajes quietos con gráficos encima. Ahora cada plano con personaje tiene una **acción con principio, desarrollo y final**:

- **Caminar**: los pies salen de la posición real (fase atada a la distancia), el pie apoyado queda fijo y la cadera baja lo necesario para que las rodillas flexionen.
  - Los brazos se balancean en oposición a las piernas.
  - Al frenar, el balanceo y la inclinación se apagan.
- **Girar**: de perfil a 3/4 con fundido corto. La cabeza voltea antes que el cuerpo.
- **Tomar objetos**: IK de dos manos a puntos concretos del objeto. El objeto sigue a las manos y no al revés.
- **Reaccionar**: anticipación (baja un poco), acción (retrocede medio paso, hombros arriba, cejas arriba) y asentamiento.
  - Los secundarios reaccionan 0.25 s después (acción superpuesta).
- **Mirar**: cabeza, ojos y torso se orientan al objetivo. La cabeza llega 3 fotogramas después del cuerpo y los brazos 2 (follow-through).
- **Bocas**: los personajes no hablan en cámara (es voz en off), así que tienen la boca cerrada salvo una expresión (sorpresa, tristeza). Si un plano lleva diálogo, la apertura de la boca sale del volumen de la voz.
- **Cámara**: solo empujes lentos. La acción la hacen los personajes.

## 3. Control de calidad por fotograma (automático, sobre TODOS los fotogramas)

El rig registra, en cada fotograma y para cada personaje, la posición de todas las articulaciones, la boca, los agarres y los pies planeados. `prueba/qc.py` mide:

| Categoría | Qué se mide | Fórmula de puntuación |
|---|---|---|
| Continuidad corporal | error de largo de cada hueso | 10 − 50 × (error máx − 0.5 %) |
| Movimiento de extremidades | saltos: aceleración de una articulación > 0.35u entre fotogramas (fuera de transiciones planificadas) | 10 − 1 por salto |
| Naturalidad de caminata | pie apoyado que se desliza > 0.5 px, pies que flotan o atraviesan el suelo | 10 − 0.5 por fotograma con error |
| Consistencia visual | tamaño de manos y cabeza constante en todas las vistas | 10 si es constante |
| Sincronización labial | boca "hablando" sin diálogo | 10 − 0.5 por fotograma |
| Interacción con objetos | distancia mano–punto de agarre | 10 − 0.25 por fotograma > 3 px |
| Continuidad temporal | diferencia de imagen entre fotogramas consecutivos (picos > 4 × mediana) | 10 − 1 por pico |

Además, reviso a ojo hojas de contacto (1 de cada 2 fotogramas) y un mapa de trayectorias de las articulaciones.

**Lo que el QC automático NO puede juzgar** (lo reviso a ojo y lo digo): si una pose "se siente" natural, la intención actoral, la legibilidad de la composición.
