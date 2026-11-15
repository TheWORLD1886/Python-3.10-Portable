# BAIT DATA: monitor de datos BAIT para iPhone (Scriptable)

Widget de iOS hecho con [Scriptable](https://scriptable.app). Muestra el consumo **real** de una línea BAIT (Walmart, México): GB disponibles y consumidos, porcentaje, vigencia, días restantes, estado, historial diario y hora de la última sincronización.

No usa datos inventados ni captura manual, ni depende de servidores externos, de una Mac o de otras apps.

---

## 1. Investigación técnica

### 1.1 Qué ofrece BAIT públicamente

| Canal | Qué permite | ¿Sirve para automatizar? |
|---|---|---|
| App **Mi Bait** (iOS/Android) | Consultar saldo y consumo, recargar | No. Es una app cerrada y Scriptable no puede leerla. |
| SMS / USSD (fuentes de terceros mencionan "SALDO" a 5510 o 52142, y `*101#`; esas fuentes no coinciden entre sí) | Saldo por mensaje | No. iOS no deja que un script envíe ni lea SMS ni USSD. |
| Portal **mibait.com** (`/login` → `/home`) | Login y vista de consumo | **Sí.** Es una app web (Angular) que llama a una API JSON. |
| API pública documentada para desarrolladores | **No existe.** No hay documentación ni repositorios públicos. | — |

### 1.2 Análisis del portal (evidencia pública)

Descargué y analicé el JavaScript **público** que mibait.com envía a cualquier navegador (`main.<hash>.js` y sus *chunks*, versión de app `4.6.6`, noviembre de 2026). Ahí están definidos los endpoints, las cabeceras y la forma de las respuestas que usa el propio portal. No inventé nada: lo que sigue sale de ese código.

**Inicio de sesión (dos flujos conviven):**

1. **Cuenta Walmart (SSO)**, el flujo principal actual:
   `POST /api/v1/sso/redirect/url?operation=login&validate=true` con `{dn: número}` devuelve una URL de `https://www.walmart.com.mx/sso/`. El usuario inicia sesión ahí y regresa a `/sso-callback?code=…`. Luego `POST /api/v1/sso/token/get?decrypt=true` con `{code}` entrega `token.access_token`.
   Para renovar el token: `POST /api/v1/sso/token/refresh?decrypt=true` con `Authorization: Bearer`.
2. **Cuenta "legacy" BAIT** (número y contraseña, con registro por PIN SMS):
   `POST /conn/page/api/bait/api/aplicacion/acceso` con `{operacion:"login", numero, pass}` devuelve `{success, access, numero, nombre, …}`.
   El registro por OTP usa `operacion: "pinv2"` y después `"validar_pin"`.

Los dos flujos pueden pedir **contraseña, OTP por SMS o el login de Walmart**, y el de Walmart corre en el dominio de Walmart. Por eso un script no puede iniciar sesión solo de forma confiable, y además no conviene que tus credenciales pasen por el script.

**Consulta de consumo (las tres variantes que usa el portal):**

| Endpoint | Autenticación | Respuesta |
|---|---|---|
| `GET /api/core/q/dn/{número}/get/consumption` (la que usa la pantalla `/home` actual) | cabecera `x-ord-service` | `{success, data:[{category, type, resume:{total, unused, expire_date}, unlimited, tethering, offers_detail}]}` |
| `POST /conn/page/api/app/consumoV3` | cabecera `ordServicio`, cuerpo `{access}` | `{success, consumo:[{nombre, mb_usados, mb_totales, mb_disponibles, …}], proxima_recarga, offeringsIds:[{expireDate}], esIlimitado}` |
| `POST /conn/page/api/sso/consumoSSO` | `Authorization: Bearer`, cuerpo `{numero}` | igual que consumoV3 |

Las cantidades están en **MB**. El portal calcula el total de datos sumando los rubros `BestEffort` y `Throttling`, y la vigencia como la fecha `expire_date` más lejana de los rubros Data, Minutes y Message. El script hace exactamente lo mismo.

**Limitaciones encontradas:**

- **No hay API pública** y estos endpoints internos pueden cambiar sin aviso.
- **El login no se puede automatizar:** requiere contraseña, OTP o la cuenta Walmart, que corre en otro dominio.
- El portal **guarda la sesión en `localStorage`** (`memberbt`, `access_token`) y limita la actualización manual a **una cada 10 minutos**.
- El JavaScript de la página de recargas tiene **CAPTCHA**. El login y la consulta de consumo no lo tienen.
- **No probé los endpoints en vivo** con una cuenta real porque no tengo una línea BAIT. El script trae una pantalla de **Diagnóstico** para comprobarlo en tu iPhone.

### 1.3 Fuentes

- Código público de [mibait.com/login](https://mibait.com/login) (bundles `main.*.js` y *chunks* lazy), analizado el 15/11/2026
- [App Mi Bait en App Store](https://apps.apple.com/MX/app/id1534628243)
- [Selectra: recargas y consulta de saldo Bait](https://selectra.mx/companias/bait/recargas)
- [internetencasa.mx: atención a clientes Bait](https://internetencasa.mx/atencion-clientes/bait)
- [Walmex: informe del ecosistema Bait](https://informes.walmex.mx/2021/en/ecosistema.html)
- [Documentación de Scriptable](https://docs.scriptable.app)

---

## 2. Arquitectura elegida

```
 ┌──────────── Primera vez / sesión expirada (dentro de la app Scriptable) ───────────┐
 │  WebView → https://mibait.com/login  (página OFICIAL; tú escribes tus datos ahí)   │
 │        └─ el script lee localStorage del portal: memberbt / access_token           │
 │           └─ guarda SOLO la sesión (número + token) en el Llavero de iOS           │
 └─────────────────────────────────────────────────────────────────────────────────────┘
 ┌──────────── Cada refresco del widget ───────────────────────────────────────────────┐
 │ Caché (<20 min) ─sí→ dibuja                                                         │
 │      no ↓                                                                           │
 │ ClientKeys: lee cabeceras públicas desde main.js de mibait.com (caché de 24 h)      │
 │ Api.fetchUsage: 1) GET consumption  2) POST consumoV3 (legacy)  3) POST consumoSSO  │
 │      401/403 → intenta renovar token SSO → si no, estado "Sesión expirada"          │
 │ Parse → {usado, total, disponible, %, vigencia, días, estado, redes, min, SMS}      │
 │ Cache + History (FileManager) → Widget (pequeño / mediano / grande)                 │
 └─────────────────────────────────────────────────────────────────────────────────────┘
 Respaldo, solo en la app: si la API directa falla, abre /home en un WebView oculto y
 lee el consumo que el propio portal descarga ('mibait-consumo').
```

| Módulo (en `BaitData.js`) | Función |
|---|---|
| `Auth` | Login interactivo en el WebView oficial, guarda y borra la sesión, renueva el token SSO |
| `ClientKeys` | Descubre en vivo las cabeceras públicas del portal (no van escritas en el código) |
| `Api` | Las tres estrategias de consulta, el respaldo por WebView y la clasificación de errores |
| `Parse` | Normaliza los tres formatos de respuesta |
| `Store` | Llavero de iOS para sesión, claves y ajustes; FileManager para caché e historial |
| `Cache` / `History` | Evita solicitudes de más, conserva el último dato válido y guarda un registro diario de 35 días |
| `getUsage` | Actualización: caché → API → respaldo → error con datos previos |
| `build*` | Dibuja el widget con `DrawContext`: anillo, barra y gráfica |
| `diagnostics` | Prueba cada endpoint y muestra los códigos HTTP, sin mostrar tokens |

**Seguridad**
- **No se guarda ninguna contraseña ni OTP:** se escriben en la página de BAIT o Walmart y el script nunca las ve.
- La sesión (número y token) se guarda en el **Llavero de iOS**, que está cifrado. Caché e historial no contienen secretos.
- Solo se consulta el número que corresponde a **tu propia sesión**.
- Solo hay tráfico hacia `mibait.com`, sin terceros.

---

## 3. Cómo se obtienen los datos reales

1. Inicias sesión una vez en mibait.com dentro de Scriptable.
2. El portal guarda tu sesión y el script la copia al Llavero. Si el portal ya cargó tu consumo, esa es la primera lectura.
3. Después, cada vez que iOS ejecuta el widget (si la caché tiene más de 20 min), el script llama al mismo endpoint de consumo que usa `mibait.com/home` y procesa la respuesta igual que el portal.
4. Si la llamada falla, el widget **conserva el último dato válido** y avisa con "Sin conexión" o "Sesión expirada".
5. El historial diario se arma con las lecturas reales: la diferencia del consumo acumulado entre un día y otro. Si el acumulado baja, se detecta la renovación del paquete.

**Lo que no puede hacerse automáticamente (y cómo se resolvió):**
- **Login:** BAIT exige contraseña, OTP o la cuenta Walmart. Lo haces tú una vez en la página oficial y la sesión se reutiliza hasta que BAIT la expire. Cuando expira, el widget lo indica y basta con tocarlo para volver a entrar.
- **Frecuencia:** iOS decide cuándo refrescar los widgets (normalmente cada 15 a 60 min, a veces menos seguido). El script pide 30 min y nunca consulta más de una vez cada 20.
- **Animaciones:** WidgetKit no permite animar los widgets de Scriptable. Las barras y anillos son estáticos y se redibujan en cada refresco.
- Si la API directa de BAIT **rechaza las llamadas que no vienen del navegador** (por ejemplo, si exige cookies de sesión), el widget no podrá refrescar solo. En ese caso cada **toque al widget** actualiza mediante el respaldo por WebView. Usa **Diagnóstico** para saber en qué caso estás.

---

## 4. Instalación desde el iPhone

1. Instala **Scriptable** (gratis) desde el App Store.
2. Abre Scriptable, toca **+** y nombra el script **`BAIT DATA`** (toca el título arriba para renombrarlo).
3. Copia **todo** el contenido de [`BaitData.js`](./BaitData.js) y pégalo en el script.
   Las tres primeras líneas de comentario (`// Variables used by Scriptable…`) le dan al script su ícono y color.
4. Toca **▶︎**. La primera vez aparece **"Iniciar sesión en BAIT"**:
   - Se abre mibait.com. Escribe tu número BAIT y completa lo que te pida BAIT: cuenta Walmart, contraseña o código SMS.
   - Cuando aparezca tu consumo, el script muestra **"✅ Línea vinculada"**. Cierra la ventana con *Cerrar*/*Done*.
5. Se muestra un resumen con tus datos reales.
6. *(Recomendado)* Vuelve a ejecutarlo y elige **Diagnóstico**. Debe aparecer al menos una línea `consumption: HTTP 200 → X GB de Y GB`.

## 5. Agregar el widget a la pantalla de inicio

1. Mantén presionada la pantalla de inicio y toca **+** (arriba a la izquierda).
2. Busca **Scriptable**, elige el tamaño (pequeño, mediano o grande) y toca **Agregar widget**.
3. Mantén presionado el widget, toca **Editar widget** y configura:
   - **Script:** `BAIT DATA`
   - **When Interacting:** `Run Script`
4. Listo. **Tocar el widget** fuerza una actualización manual: abre Scriptable, consulta a BAIT y muestra el resultado.
   El widget se redibuja con el dato nuevo en el siguiente refresco de iOS.

También funciona en la pantalla de bloqueo, con los tamaños circular y rectangular.

**Contenido por tamaño**
- **Pequeño:** anillo con los GB disponibles, % consumido y fecha de vencimiento.
- **Mediano:** disponibles de totales, barra, consumidos, días restantes y última sincronización.
- **Grande:** anillo, barra, consumidos, % usado, días restantes, renovación, redes sociales, minutos y SMS, gráfica de consumo diario de 10 días con promedio, estado de conexión con BAIT y hora de actualización.

Colores: **verde** con menos de 60 % usado, **amarillo** entre 60 y 85 %, **rojo** con más de 85 % o menos de 512 MB.

---

## 6. Errores frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| Widget dice **"Toca para vincular"** | No hay sesión guardada | Tócalo y completa el login |
| **"Sesión expirada · toca"** (amarillo) | BAIT invalidó el token | Tócalo y vuelve a iniciar sesión. Se siguen mostrando los últimos datos válidos |
| **"Sin conexión"** y hora antigua | Sin internet o mibait.com caído | Se reintenta solo. Los datos mostrados son los últimos válidos |
| **"Error de BAIT" / "respondió de forma inesperada"** | BAIT cambió su API o sus cabeceras | Ejecuta **Diagnóstico**. Las cabeceras se vuelven a leer solas. Si el formato cambió, hay que actualizar `Parse` |
| El login se queda cargando o no detecta la sesión | Cerraste la ventana antes de llegar a `/home`, o el login de Walmart no regresó a mibait.com | Repite el login y espera a ver tu consumo antes de cerrar |
| Diagnóstico: `consumption: HTTP 401/403` en todas las líneas, pero **Actualizar ahora** sí funciona | La API solo acepta llamadas del navegador. Funciona el respaldo por WebView | Usa el widget tocándolo para actualizar. Es la limitación descrita en la sección 3 |
| "Sin paquete de datos activo" | BAIT informa un total de 0 MB (sin recarga vigente) | Es el estado real. Si tu paquete sí existe pero BAIT no informa el total, configura **Paquete manual** |
| El widget tarda en cambiar | iOS limita los refrescos | Es normal. Tócalo para forzar la consulta |
| El historial está vacío | Se necesitan lecturas de al menos 2 días distintos | Se llena solo con el uso |
| Quiero empezar de cero | — | Ejecuta el script y elige **Cerrar sesión y borrar datos** |

---

## 7. Mantenimiento

Si BAIT publica una versión nueva del portal:
- Las **cabeceras** (`x-ord-service`, `ordServicio`, SSO) se vuelven a leer solas desde `main.*.js`.
- Si cambian las **rutas** o el **formato JSON**, ajusta `Api.strategies` y `Parse.*` en `BaitData.js`. Hay un comentario con el formato esperado sobre cada parser.
