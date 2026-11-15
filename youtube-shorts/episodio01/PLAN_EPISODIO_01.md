# EL DÍA QUE TODO TERMINÓ · Episodio 01: «La última noche normal»

Plan de producción para aprobación. Formato vertical 1080×1920, 30 fps, MP4 H.264, español latino neutro.

---

## 1. Personajes (diseño definitivo)

Ver `diseno_personajes.png`. El rig nuevo es `rig.py`.

| | Daniel (32) | Laura (31) | Sofía (9) |
|---|---|---|---|
| Ropa | Camisa de franela azul a cuadros y jeans con bastilla | Suéter mostaza con cuello blusa y pantalón azul marino | Sudadera amarilla con capucha y cordones, mallas moradas |
| Pelo | Castaño corto, fleco de lado | Melena castaña hasta los hombros | Dos coletas con ligas rosas, fleco |
| Calzado | Botas cafés | Botines cafés | Tenis blancos con línea morada |
| Proporción | 100 % de estatura | 94 % | 62 %, cabeza 1.28× (rasgo de niña) |
| Personalidad | Protector y calmado. Saluda abierto | Observadora e intuitiva | Inquieta y alegre; mejillas rosadas |

- **Paleta fija:** cada personaje usa siempre los mismos 5 colores.
- **Expresiones base:** tranquilo, preocupado, sorpresa y miedo, más parpadeo, boca tensa y susurro.
- **Rig:** el código no permite cambiar proporciones ni ropa entre planos.
  - Articulaciones visibles: hombro, codo, muñeca, cadera, rodilla y tobillo.
  - Cadena cadera → torso → cuello → cabeza.
- **Vistas:** frente (lista en la hoja). Las vistas 3/4 y perfil se construyen en la prueba de caminata.

---

## 2. Duración: ajuste necesario

El guion tiene **273 palabras de narración**. Con voz natural eso son unos **110 s**, más 6–8 s de acciones sin voz (choque, carrera y golpes). El total quedaría en ~118 s y el objetivo es 80–90 s.

Propongo esta versión condensada, de unas 210 palabras y ~90 s. Mantiene todos los hechos y frases clave del guion:

> **E1.** 10:47 de la noche. En una pequeña ciudad de Estados Unidos, todo parece normal. Las familias cenan, los negocios siguen abiertos… Pero en el hospital, los médicos intentan contener algo que todavía no comprenden.
>
> **E2.** Daniel tiene 32 años. Vive con su esposa Laura y su hija Sofía, de nueve. Esta noche cenan con las noticias de fondo… hasta que aparece una alerta de última hora: personas atacando a desconocidos por toda la ciudad. Hospitales saturados. Las autoridades piden no salir de casa.
>
> **E3.** Suena el teléfono. Es Marcos, su hermano. Está desesperado: algo pasa en las calles, que cierre todas las puertas. Y la llamada… se corta. Daniel mira por la ventana.
>
> **E4.** Un auto se estrella contra una tienda. La gente corre. Una mujer cae… y alguien se abalanza sobre ella. *(acción sin voz: Daniel corre a la puerta, Laura carga a Sofía, sirenas, la TV pierde la señal)*
>
> **E5.** Y entonces… tres golpes sacuden la puerta. — **HOMBRE:** «¡Por favor! ¡Déjenme entrar!» — Daniel mira por la mirilla. Es un hombre cubierto de sangre. Pero algo no está bien: no deja de golpear. — **LAURA (susurro):** «Daniel… no lo dejes entrar.»
>
> **E6.** Su hija llora. El hombre suplica. Y algo se mueve detrás de él, en la oscuridad. ¿Qué debería hacer Daniel? *(silencio + opciones A/B)* Tú decides cómo empieza esta historia. Comenta A o B. Porque mañana… quizá ya no exista un lugar seguro.

**Decisión pendiente:** usar la versión condensada (~90 s) o el guion completo (~118 s).

---

## 3. Storyboard y plan de animación (26 planos · ~90 s)

### Convenciones (aplican a todos los planos)

- **Capas de cada plano:**
  1. Fondo desenfocado.
  2. Entorno.
  3. Personajes secundarios.
  4. Personajes principales.
  5. Primer plano desenfocado y bokeh.
- **Paralaje:** cada capa se mueve a una velocidad distinta, de 0.1× a 1.7×.
- **Método de animación:** rig 2D propio con poses clave por ángulos e interpolación *ease in/out*. Incluye:
  - IK de dos huesos con **pies fijos al suelo** (foot locking) en caminatas y apoyos.
  - Retraso de 2–4 fotogramas por articulación (follow through y overlapping).
  - Anticipación antes de cada acción y respiración constante.
  - Parpadeo con intervalos aleatorios de 2–5 s.
- **Clave de animación:** cada plano indica sus poses clave, que es lo que programo en el motor. No uso generadores de video por IA (ver sección 4).

### ESCENA 1: 10:47 PM (14 s)

| Plano | Dur. | Personajes | Acción y animación | Cámara | Luz | Audio |
|---|---|---|---|---|---|---|
| 1.1 | 4 s | 6 extras, 3 autos | Calle principal. Los autos circulan a velocidades distintas: las ruedas giran y la carrocería se balancea un poco. Árboles mecidos por el viento y letreros parpadeando. Texto «10:47 PM». | Grúa descendente lenta | Noche cálida: farolas ámbar y vitrinas | Música nostálgica (piano y pad), tráfico suave |
| 1.2 | 4 s | Pareja y 2 peatones | Peatones con ciclo de caminata completo y brazos opuestos a las piernas. La pareja se detiene: él abre la puerta de la tienda y ella entra primero; él la sigue con un giro de torso. | Travelling lateral | Vitrina iluminada | Campanita de la puerta y pasos |
| 1.3 | 3 s | — | Exterior del hospital: llega una ambulancia frenando con las luces girando. Paso al interior con barrido de luz. | Paneo hacia la entrada | Rojo y azul | Sirena breve; la música baja |
| 1.4 | 3 s | 2 médicos, 1 enfermera, paciente | Pasillo: empujan una camilla a paso rápido, con el torso inclinado hacia adelante. Un médico voltea hacia atrás con retraso de cabeza. La mano del paciente se crispa. | Cámara en mano sutil | Fluorescente frío y parpadeante | Ruedas de la camilla, pitido de monitor, grave tenue |

### ESCENA 2: La familia (18 s)

| Plano | Dur. | Personajes | Acción y animación | Cámara | Luz | Audio |
|---|---|---|---|---|---|---|
| 2.1 | 4 s | Daniel, Laura, Sofía | Cena. Daniel lleva el tenedor a la boca en arco y mastica. Laura le pasa el pan con un giro de torso. Sofía balancea las piernas en la silla. | Dolly in lento | Lámpara cálida sobre la mesa | Piano familiar, cubiertos, risa breve de Sofía |
| 2.2 | 2.5 s | — | TV: noticiero con cintillo rojo «ÚLTIMA HORA». | Inserto fijo con leve empuje | Luz azul de la TV | Tono de alerta; entran graves |
| 2.3 | 3 s | Daniel, Laura | Daniel deja los cubiertos (anticipación: se detiene a medio camino) y gira la cabeza, luego el torso, hacia la TV. Laura gira el torso y lo observa. | Plano medio | La TV ilumina sus caras con parpadeo | Voz del noticiero amortiguada |
| 2.4 | 2.5 s | Sofía | Se acomoda en la silla y mira a sus papás y luego a la TV. Las cejas suben y los hombros se encogen. | Primer plano | Reflejo de la TV | Grave sostenido |
| 2.5 | 3 s | Daniel, Laura | Daniel hace un gesto tranquilizador: palma abajo con movimiento suave y sonrisa leve. Laura frunce la frente, niega con la cabeza y cruza los brazos. | Dos personajes | Cálida contra fría | Respiración de Laura |
| 2.6 | 3 s | Los tres | Inserto de la TV: «PERMANEZCAN EN SUS CASAS». Contraplano de los tres en silencio, iluminados por la TV y parpadeando. | Dolly out lento | Azul dominante | La música se apaga a un pad |

### ESCENA 3: La advertencia (12 s)

| Plano | Dur. | Personajes | Acción y animación | Cámara | Luz | Audio |
|---|---|---|---|---|---|---|
| 3.1 | 3 s | Daniel | El teléfono vibra sobre la mesa. Daniel lo toma: el brazo hace un arco hasta la oreja con el codo flexionado. La otra mano se apoya en la mesa. | Plano medio | Pantalla del teléfono en su cara | Vibración y tono |
| 3.2 | 4 s | Daniel, Laura (desenfocada) | La expresión cambia de neutra a preocupada y a alarmada. Se inclina hacia adelante; la mano libre aprieta el borde de la mesa. Laura lo sigue con la mirada. | Primer plano, dolly in | Fría | Voz de Marcos lejana y filtrada (ininteligible), tensión |
| 3.3 | 2 s | Daniel | La llamada se corta. Aparta el teléfono y mira la pantalla «LLAMADA FINALIZADA». | Inserto y primer plano | — | Pitido de llamada cortada y silencio |
| 3.4 | 3 s | Daniel, Laura | Daniel se levanta y da 3 pasos hacia la ventana con transferencia de peso. Ilumina la ventana un resplandor rojo y azul. | Seguimiento lateral | Rojo y azul desde afuera | Sirenas muy lejanas |

### ESCENA 4: El comienzo del fin (15 s)

| Plano | Dur. | Personajes | Acción y animación | Cámara | Luz | Audio |
|---|---|---|---|---|---|---|
| 4.1 | 4 s | Extras | Por la ventana: un auto pierde el control, derrapa, gira y choca contra la fachada de la tienda. Salen cristales y chispas. Varias personas corren en direcciones distintas. | Plano general por la ventana | Fuego naranja | Derrape, choque, alarma de auto |
| 4.2 | 3 s | Mujer, figura | La mujer tropieza, pierde el equilibrio y cae apoyando las manos. Una figura en sombra avanza y se lanza. Corte antes del contacto; solo se ve la silueta. | Plano medio desde lejos | Contraluz | Grito lejano, latido |
| 4.3 | 3 s | Daniel | Carrera completa a la puerta: torso inclinado y brazos impulsando. Desacelera en 2 pasos, gira, estira el brazo y pone el seguro. | Paneo que lo acompaña | Interior oscuro | Pasos pesados y «clac» del seguro |
| 4.4 | 3 s | Laura, Sofía | Laura se levanta, se agacha y carga a Sofía. Sofía le rodea el cuello con los brazos. Laura compensa el peso inclinando la cadera. | Plano medio | Cálida tenue | Respiración agitada y sollozo |
| 4.5 | 2 s | — | La TV pierde la señal y queda en estática con «SIN SEÑAL». | Inserto | Estática blanca | Estática y sirenas por toda la ciudad |

### ESCENA 5: Los golpes (16 s)

| Plano | Dur. | Personajes | Acción y animación | Cámara | Luz | Audio |
|---|---|---|---|---|---|---|
| 5.1 | 3 s | Daniel | Tres golpes: la puerta vibra en cada uno y cae polvo. Daniel da un sobresalto rápido de todo el cuerpo y luego queda congelado. | Plano general del recibidor | Franja de luz bajo la puerta | 3 golpes secos y resonantes, sincronizados al fotograma |
| 5.2 | 3 s | Laura, Sofía | Laura retrocede dos pasos y gira el cuerpo para proteger a Sofía, que esconde la cara en el hombro de su madre. | Plano medio | — | «¡Por favor! ¡Déjenme entrar!» (voz del hombre) |
| 5.3 | 3 s | Daniel | Se acerca despacio a la mirilla: pasos cortos, hombros elevados, mano en la puerta y torso inclinado. | Dolly in lento | Casi a oscuras | Respiración contenida |
| 5.4 | 4 s | Hombre | Vista por la mirilla con lente ojo de pez: el hombre está manchado de sangre estilizada (rojo oscuro, sin heridas explícitas). Sus movimientos son espasmódicos y golpea sin parar. | Vista subjetiva con viñeta circular | Foco del porche verdoso | Golpes rítmicos y gemidos |
| 5.5 | 3 s | Laura | Laura susurra: «Daniel… no lo dejes entrar». Cejas tensas, cabeza hacia él y Sofía apretada contra ella. | Primer plano | Lateral tenue | Susurro y grave |

### ESCENA 6: La decisión (15 s)

| Plano | Dur. | Personajes | Acción y animación | Cámara | Luz | Audio |
|---|---|---|---|---|---|---|
| 6.1 | 3 s | Daniel y Sofía | Daniel duda: mira a la puerta, luego a su familia y otra vez a la puerta, con la mano en la manija. Sofía llora con los hombros temblando. | Plano y contraplano | — | Llanto suave y golpes |
| 6.2 | 3 s | Hombre y sombra | De nuevo por la mirilla: detrás del hombre, algo se mueve en la oscuridad (dos brillos y una silueta que se arrastra). | Vista subjetiva | Muy oscuro | Silencio musical repentino |
| 6.3 | 5 s | — | Pantalla dividida: **A — ABRIR LA PUERTA** (la manija brilla) / **B — ESCONDERSE** (escaleras al sótano). | Fija con paralaje | Neón rojo / neón azul | Silencio y un solo golpe |
| 6.4 | 4 s | — | «Tú decides… Comenta A o B». Cierre: «¿Mañana existirá un lugar seguro?» y «EPISODIO 02». | Empuje lento | — | Golpe grave final |

---

## 4. Herramientas y costo estimado

| Parte | Herramienta | Costo |
|---|---|---|
| Animación, escenarios, cámara y efectos | Motor 2.5D propio en Python (rig articulado nuevo + capas con paralaje + filtros de cine), el mismo de tus shorts | **$0** (corre en esta sesión) |
| Narrador | ElevenLabs, Brian C. (voz latina), ~1,300 caracteres × 2 tomas | ~2,600 créditos |
| Voces del hombre en la puerta y del susurro de Laura | ElevenLabs: 2 voces de la biblioteca, 3 tomas cada una | ~400 créditos |
| Música y efectos | Sintetizados en código: piano, pads, graves, sirenas, golpes, respiración, estática | **$0** |
| Gritos, choque y vidrios realistas (opcional) | ElevenLabs Sound Effects | ~1,000–2,000 créditos |

- **Total en créditos de ElevenLabs:** ~3,000 (sin efectos opcionales) o ~5,000 (con ellos).
  - Cabe en el plan **Starter** (~$5 USD/mes, 30,000 créditos), que además da la licencia para publicar en un canal monetizado.
  - El plan gratis no permite uso comercial.
  - Tu cuenta actual no tiene el formato de audio de 192 kbps (es del plan Creator). No afecta: uso el de 128 kbps.
- **Generadores de video con IA (Runway, Kling, Veo, etc.):** no los recomiendo para este estilo.
  - No mantienen idénticos a los personajes entre planos.
  - Cada intento cuesta créditos.
  - No tengo acceso a ellos desde esta sesión.
  - Con el rig propio, la continuidad está garantizada por código.

**Límite honesto:** es animación 2.5D procedural, no 3D de estudio. Puedo lograr:
- Ciclos de caminata y carrera con rodillas y pies fijos.
- Torso con inercia, anticipación y retrasos entre partes del cuerpo.
- Cargar a Sofía, agarrar la manija y tomar el teléfono.

La ropa no tendrá simulación de tela: solo un movimiento secundario sencillo.

---

## 5. Tiempos de producción

| Etapa | Tiempo |
|---|---|
| Prueba de Daniel (caminar, girar y levantar la mano), 5–6 s | ~1 h de trabajo + 2 min de render |
| Rig completo: vistas frente, 3/4 y perfil, ciclos y agarres | 2–3 h |
| Escenarios (calle, hospital, comedor, recibidor, mirilla, pantalla A/B) | 3–4 h |
| Animación de los 26 planos con revisión de cada uno | 5–7 h |
| Voces, música, efectos y mezcla | 1–2 h |
| Render final (~90 s) | ~35 min por pasada |

Entrego por escenas para que apruebes cada una antes de seguir.

---

## 6. Qué necesito que apruebes

1. Diseño de Daniel, Laura y Sofía (`diseno_personajes.png`).
2. Guion: versión condensada (~90 s) o completa (~118 s).
3. Storyboard de 26 planos.
4. Herramientas: rig propio + ElevenLabs (narrador y 2 voces). ¿Quieres los efectos opcionales de ElevenLabs?

Con tu aprobación hago **solo** el plano de prueba: Daniel camina, gira y levanta una mano.
