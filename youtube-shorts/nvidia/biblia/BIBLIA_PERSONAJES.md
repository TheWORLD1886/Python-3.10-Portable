# Biblia de personajes — NVIDIA (NEON CINEMATIC STUDIO)

Representaciones estilizadas, **no retratos**. Todos los personajes salen del mismo rig (`episodio01/rig.py`), así que comparten proporciones y nunca se redibujan "a mano" en un plano.

Fichas visuales (frente · tres cuartos · perfil · expresiones): `ficha_jensen.png`, `ficha_alice.png`, `ficha_colette.png`, `ficha_agente.png`. Escala común: `escala_personajes.png`.

## Proporciones comunes (unidad u = altura del personaje / 8)

| Parte | Medida | Nota |
|---|---|---|
| Cabeza | círculo de radio 1u | blanca, no se escorza en 3/4 |
| Cuello | 0.25u | visible en todos (el pelo nunca lo tapa) |
| Torso | 2.45u (cadera → cuello) | hombros 0.86u del eje (mujeres 0.76u) |
| Brazo / antebrazo | 1.30u / 1.25u | IK: el codo nunca cambia de largo |
| Muslo / espinilla | 1.55u / 1.55u | rodilla siempre hacia adelante |
| Mano | círculo 0.31u | igual en frente, 3/4 y perfil |
| Pie | elipse 0.50 × 0.25u | apoyado = fijo al suelo |
| Cejas | a 0.45u sobre los ojos | ningún pelo, gorra o casco las tapa |

## Personajes

| Personaje | Altura | Elementos fijos | Expresiones |
|---|---|---|---|
| **Jensen Huang** | 1.00 | pelo gris peinado hacia atrás · chaqueta de cuero negra con cierre · camiseta negra | seguridad, preocupación, sorpresa, tensión, tristeza, desconcierto |
| **Alice Huang** | 0.94 | melena negra a la mandíbula · blazer crema · pantalón oscuro · silueta femenina | serenidad, misterio, desconfianza, concentración, preocupación |
| **Colette Kress** | 0.95 | melena rubia · traje azul marino · postura erguida | profesional, seguridad, atención, firmeza |
| **Agente** | 1.00 | traje y corbata negros · gafas oscuras · auricular con cable · carpeta o dispositivo | serio, alerta, informa, sorpresa contenida |
| Secundarios | 0.95–1.00 | portavoz chino (traje gris, corbata roja) · directiva (traje gris, cola) · legisladores | — |

## Articulaciones animables

Hombros (subir/bajar), codos e hombros por IK, manos, cadera (desplazamiento y altura), rodillas, tobillos, inclinación del torso, giro e inclinación de cabeza, mirada, parpadeo, cejas (fruncir, subir, asimetría) y boca (neutra, sonrisa, o, tensa, triste, habla con apertura continua).

## Limitaciones honestas del diseño

- Las manos son círculos (estilo de la serie): **no hay dedos ni rotación de muñeca visible**. Para sostener objetos, la mano se dibuja sobre el borde del objeto.
- El perfil y los 3/4 son dibujos distintos del mismo rig: el giro de perfil a 3/4 se resuelve con un fundido de 0.2 s (6 fotogramas), que el control de calidad marca como transición planificada.
