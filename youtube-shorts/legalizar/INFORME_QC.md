# Informe de control de calidad · prueba sin audio

Archivo: `legalizar_prueba_sin_audio.mp4`. Comprobado con ffprobe y con una decodificación completa: H.264, 1080×1920, 30 fps, 4320 fotogramas, 144 s, sin pista de audio (a propósito, es la prueba).

El sistema de medición es el mismo de NVIDIA v2 e Internet: el rig registra cada personaje en cada fotograma, y la diferencia de imagen se mide entre fotogramas consecutivos.
Fórmulas fijas, mínimo 9 de 10. En los planos documentales y gráficos (sin personajes) solo se puede medir la continuidad temporal.

## Correcciones hechas (re-renderizadas y vueltas a medir)
1. Etiquetas «IMAGEN REAL» y «RECREACIÓN» cortadas por el zoom de cámara: ahora se dibujan después de la cámara.
2. Tres procesos de render murieron por falta de memoria (los videos se guardaban sin comprimir): ahora los fotogramas se guardan en JPEG en memoria y se vuelve a renderizar todo.
3. Manos que no alcanzaban su objetivo (capo con el dinero, funcionaria con el sello, gestos de «alto»): personajes y objetos se acercaron.
4. Gestos demasiado rápidos (doctora, vecina) y un salto del brazo del dependiente: ahora se animan con más tiempo.
5. Entrada del menor demasiado rápida: ahora arranca y frena de forma suave.
6. Un logotipo de hotel aparecía en la última foto: se cambió por otra vista aérea del mismo autor.
7. Una sola foto ocupaba 9 s: se dividió en dos planos (decomiso de metanfetamina y Guardia Nacional).

## Puntuación por plano

| # | Plano | Inicio | Fin | Puntuaciones | Errores |
|---|---|---|---|---|---|
| 1 | Hook | 0 | 3.72 | Continuidad temporal: 10.0 | 0 |
| 2 | Pills | 3.72 | 6.73 | Continuidad temporal: 10.0 | 0 |
| 3 | Boss | 6.73 | 9.77 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 4 | HealthCrisis | 9.77 | 14.02 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 5 | Dilemma | 14.02 | 18.02 | Continuidad temporal: 10.0 | 0 |
| 6 | License | 18.02 | 23.69 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 7 | Markets | 23.69 | 29.34 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 8 | Compete | 29.34 | 34.66 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 9 | Fight | 34.66 | 38.94 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 10 | Illegal | 38.94 | 41.48 | Continuidad temporal: 10.0 | 0 |
| 11 | Diversify | 41.48 | 48.38 | Continuidad temporal: 10.0 | 0 |
| 12 | OtherSide | 48.38 | 50.19 | Continuidad temporal: 10.0 | 0 |
| 13 | Minors | 50.19 | 59.58 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 14 | Risks | 59.58 | 62.2 | Continuidad temporal: 10.0 | 0 |
| 15 | Fentanyl | 62.2 | 65.87 | Continuidad temporal: 10.0 | 0 |
| 16 | Hospitals | 65.87 | 73.63 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 17 | Challenge | 73.63 | 76.32 | Continuidad temporal: 10.0 | 0 |
| 18 | Inspect | 76.32 | 83.23 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 19 | Corruption | 83.23 | 90.21 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 20 | USA | 90.21 | 92.28 | Continuidad temporal: 10.0 | 0 |
| 21 | Border | 92.28 | 96.44 | Continuidad temporal: 10.0 | 0 |
| 22 | Tensions | 96.44 | 102.09 | Continuidad temporal: 10.0 | 0 |
| 23 | NotSame | 102.09 | 106.4 | Continuidad temporal: 10.0 | 0 |
| 24 | Law | 106.4 | 113.62 | Continuidad temporal: 10.0 | 0 |
| 25 | NoSale | 113.62 | 117.83 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 26 | NoEvidence | 117.83 | 123.32 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 27 | WhatNow | 123.32 | 126.11 | Continuidad temporal: 10.0 | 0 |
| 28 | Debate | 126.11 | 133.33 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 29 | Friend | 133.33 | 138.31 | Continuidad temporal: 10.0, Continuidad corporal: 10.0, Movimiento de extremidades: 10.0, Naturalidad de caminata: 10.0, Consistencia visual: 10.0, Sincronización labial: 10.0, Interacción con objetos: 10.0 | 0 |
| 30 | Reality | 138.31 | 144 | Continuidad temporal: 10.0 | 0 |

Resultado: todos los planos aprobados. Medidos 4319 de 4320 fotogramas (el primero no tiene uno anterior con qué compararse).

## Revisión documental
- Cada imagen real corresponde a lo que dice la voz. Fecha y lugar salen de la ficha del archivo y se rotulan en pantalla.
- Material de otro año o de otro país se identifica como tal: decomisos de la CBP en Arizona y Texas (2017–2023), y la reunión de 2023 rotulada «Archivo».
- No se muestra ninguna cifra inventada. La tabla de dosis es la del art. 479 de la Ley General de Salud. El dato de potencia del fentanilo es de la OMS.
- Las fotos de fábricas farmacéuticas (Japón, Reino Unido) se descartaron porque no corresponden a México y podían inducir a error.

## Pendiente para la versión final
- Voz (ya generada: `voz.mp3`), música original y efectos.
- Hojas de contacto de cada plano: `qc_contactos/`.
