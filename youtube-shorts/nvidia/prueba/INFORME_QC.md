# Informe de control de calidad — Plano de prueba (plano 18)

**Plano:** «La junta directiva abrió una investigación independiente para determinar si Jensen fue objetivo de una operación extranjera.»

**Formato:** 7.2 s · 216 fotogramas · 1080×1920 · 30 fps.

**Inspección:**
- **Automática** (`qc.py`), sobre los **216 fotogramas**, con las articulaciones de 3 personajes registradas en cada uno.
- **Visual**, a mano, con hojas de contacto (1 de cada 2 fotogramas) y primeros planos de los momentos clave.

## Errores detectados y corregidos (4 iteraciones)

| Iteración | Detectado por | Error | Fotogramas | Corrección | ¿Verificado tras re-render? |
|---|---|---|---|---|---|
| 0 (prueba de cuadros) | revisión visual | Encuadre demasiado abierto: personajes pequeños | todos | Cámara más cerrada (1.34 → 1.46) | sí |
| 0 | revisión visual | El expediente tapaba la boca de Jensen en la sorpresa | ~170–190 | Expediente más bajo y más corto; subida en la sorpresa de 26 a 12 px | sí |
| 0 | revisión visual | Segundo miembro de la junta cortado por el borde | todos | Junta reubicada (x 730 / 850) | sí |
| 0 | revisión visual | Piernas cruzadas al retroceder | ~165–175 | Paso atrás más corto (0.3u) y peso hacia atrás (cadera −0.14u) | sí |
| 1 | QC automático | **Pies flotando 4–10 px al caminar**: la pierna no alcanzaba el suelo con la cadera a altura completa | 93 fotogramas (0–70) | El rig baja la cadera lo justo para que el pie apoyado toque el suelo (las rodillas se flexionan) | sí: 0 flotando, 0 atravesando |
| 1 | QC automático | **El codo derecho saltaba de lado** durante 1 fotograma (salto IK de 1.7u) | 118–119, 153–154, 163–164 | Coherencia temporal en la IK: cada fotograma elige la solución más cercana al codo anterior | sí: 0 saltos |
| 1 | QC automático | La rodilla izquierda saltaba 0.50u al arrancar | 2 | Se corrigió con la cadera ajustada al suelo | sí |
| 1 | QC automático | Falló el recorte del audio (parámetro de fundido) | — | `d=0.3` | sí |
| 2 | revisión visual | **Codo en «ala de pollo»** al alcanzar el expediente | 96–110 | IK del brazo en 3D: el codo va hacia atrás en profundidad y el brazo se ve escorzado | sí (ver `out/rev.jpg`) |
| 2 | revisión visual | **Brazos inmóviles** en la junta y reacción casi invisible | todos | Respiración, cambio de peso y balanceo leve; reacción con mano al pecho y mano al mentón | sí |
| 3 | QC automático | Codo de un miembro de la junta saltaba 0.43–0.60u (gesto demasiado rápido) | 179–181 | Gesto de 0.35 s a 0.6 s | sí: 0 saltos |

## Resultado final (iteración 4)

| Criterio | Medida | Puntuación |
|---|---|---|
| Continuidad corporal | error máximo de largo de hueso (en 3D): 0.0 % | 10 |
| Movimiento de extremidades | saltos de articulación > 0.35u: 0 | 10 |
| Naturalidad de caminata | deslizamientos 0 · flotando 0 · atraviesa suelo 0 (72 fotogramas caminando) | 10 |
| Consistencia visual | radio de mano constante por personaje (17.3 / 18.2 / 24.8 px; uno por personaje) | 10 |
| Sincronización labial | bocas hablando sin diálogo: 0. Plano con voz en off, nadie habla en cámara | 10 |
| Interacción con objetos | 270 agarres medidos, 0 a más de 3 px del punto | 10 |
| Continuidad temporal | 0 picos de diferencia de imagen (máx 3.44 · mediana 2.06) | 10 |

**Aprobado por QC: sí.**

## Limitaciones (dichas con honestidad)

1. **Un 10 no significa «perfecto».** Significa que no se encontró ninguno de los errores **que el QC mide**. La naturalidad de una pose y la intención actoral las juzgo a ojo. Por eso las correcciones de la iteración 2 vinieron de la revisión visual y no del QC.
2. **El giro de perfil a 3/4** (fotogramas 72–77) es un fundido planificado de 0.2 s. Se excluye de la detección de saltos y se marca como transición.
3. **La sincronización labial no se pone a prueba en este plano** porque no hay diálogo. Solo se verifica que nadie mueva la boca sin hablar.
4. **No hay dedos ni rotación de muñeca.** Las manos son círculos por diseño de la serie.
