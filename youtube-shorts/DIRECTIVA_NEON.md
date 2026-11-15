# NEON CINEMATIC STUDIO — directiva maestra (vigente desde 2026-11-15)

Resumen operativo del prompt maestro del usuario. Se aplica a todos los shorts nuevos.

## Identidad
- Stickmans del rig compartido (`episodio01/rig.py`): cabeza esférica blanca, ojos ovalados negros, cuerpo negro,
  extremidades articuladas, manos circulares, pies ovalados, ropa según el personaje. Nunca personas realistas generadas por IA.
- El mismo personaje conserva su diseño en todas las escenas (ficha en la biblia de cada episodio).

## Investigación y material real
- Antes de producir: investigar el tema; prioridad: 1) fuentes oficiales, 2) agencias, 3) medios especializados, 4) archivos verificables.
- No inventar hechos, cifras, fechas, fotos ni declaraciones. Hipótesis = rotuladas como hipótesis.
- Registro de fuentes por afirmación (`fuentes.json`): URL, autor/institución, fecha de publicación, fecha del hecho, licencia, frase del guion.
- Material visual solo con licencia comprobable: Wikimedia Commons (licencia leída en la ficha del archivo), dominio público
  de gobiernos (p. ej. NASA, Biblioteca del Congreso de EE. UU.) u otras licencias compatibles. Sin licencia verificable = no se usa.
- Nada de marcas de agua, imágenes repetidas, material antiguo presentado como actual, ni recreaciones presentadas como reales
  (las escenas con stickmans son recreaciones y se distinguen del material documental). Pequeño crédito en pantalla cuando corresponda.

## Escenas
- Tres tipos alternados: documental (fotos/videos/mapas/documentos reales), narrativa (stickmans), combinada (stickmans sobre fondos reales).
- No repetir una misma fórmula; cada cambio de información = cambio de composición.
- Planos generales, medios, primeros planos y detalle; cámara suave; la cámara no sustituye la animación.
- Fotos reales con paneo, recorte, máscaras, capas y gráficos; nunca una foto fija sin aportar nada.

## Animación
- Brazos independientes, codos, piernas, transferencia de peso, cabeza, reacciones, entradas/salidas, anticipación y seguimiento.
- Sin pies deslizando ni flotando; sin movimiento robótico.

## Formato y audio
- 1080×1920, 30 fps, MP4 H.264 + AAC. Duración objetivo 60–90 s salvo que el guion diga otra cosa.
- Voz Brian (ElevenLabs), música original sin derechos de terceros, ambientes y efectos discretos; la música nunca compite con la voz.
- Subtítulos palabra por palabra, legibles y sincronizados.

## Control de calidad
- QC automático del rig (huesos, saltos, pies, agarres, bocas, picos de imagen) + revisión de hojas de contacto.
- Revisión documental: cada imagen corresponde a la narración, fuente y fecha verificadas, real vs. recreación diferenciado.
- Lo que falla se corrige y se vuelve a renderizar y medir. Nunca se declara corregido sin re-render.

## Flujo
1 guion → 2 investigación → 3 lista de escenas → 4 material → 5 continuidad de personajes → 6 animación →
7 voz y sonido → 8 montaje → 9 QC → 10 exportación.
**Antes del video completo: storyboard + muestra visual para aprobación.** Sin pagos ni suscripciones sin autorización.

## Entrega
MP4 final · guion de narración · storyboard · lista de fuentes · créditos del material · informe de QC.
Se comprueba que el archivo existe, se reproduce (ffprobe + decodificación completa) y cumple las especificaciones antes de declararlo terminado.
