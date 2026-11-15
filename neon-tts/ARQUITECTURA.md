# NEON CINEMATIC STUDIO · Sistema TTS multipersona (fase 1)

Sistema de doblaje automatizado en la nube. Toma un guion y entrega un archivo de audio por intervención, cada personaje con su propia voz, más un manifiesto JSON para sincronizar con la animación. No depende de tu MacBook ni de una GPU local.

## 1. Arquitectura

```
 Claude ──(guion JSON o texto «PERSONAJE (acotación): línea»)──► n8n Cloud · Webhook (token)
                                                                    │
     Google Drive ◄── character_voice_registry.json ◄── descarga ───┤
     Google Drive ◄── E001_manifest.json (anterior) ◄── descarga ───┤  (idempotencia)
                                                                    ▼
                                         Plan (nodo Code): valida personajes, asigna voces del registro,
                                         traduce emoción → estilo real o prosodia, arma SSML y hash
                                                                    │  1 clip por vuelta, 3.2 s entre clips (F0 = 20/min)
                     ┌──────────────────────────────────────────────┤
                     ▼                                              ▼
           Azure AI Speech · TTS (SSML)          clips sin cambios → se omiten (no se pagan dos veces)
                     │  WAV 48 kHz
                     ▼
     audio-worker (Google Cloud Run + FFmpeg) ── normaliza −18 LUFS / −1.5 dBTP, filtros por personaje
                     │                            (teléfono, detrás de la puerta), mide la duración REAL, QA
                     ▼
           Azure STT (verificación) ── transcribe el clip → el worker calcula WER contra el texto
                     ▼
     Google Drive ── E001_SC005_LAURA_001.wav   +   E001_manifest.json   ──► respuesta con informe a Claude
                                                                              (fallidos y clips por revisar)
```

| Pieza | Para qué | Por qué así |
|---|---|---|
| **Azure AI Speech** (motor principal) | Voces neuronales es-MX, SSML con estilos, velocidad, tono, volumen y pausas | Nivel gratuito permanente. El SSML permite dirigir cada línea. |
| **Chatterbox Multilingual** (motor secundario, fase 2) | Voces personalizadas (ej. una voz infantil real para Sofía si Azure no convence) | Licencia MIT, uso comercial permitido. Necesita GPU: se usa **solo bajo demanda** en GPU serverless que se apaga sola. |
| **n8n Cloud** (orquestación) | Recibe guiones, coordina, reintenta, informa | Lo pediste. Guarda las claves en su gestor de credenciales. |
| **audio-worker en Cloud Run** | FFmpeg en la nube | **n8n Cloud no permite el nodo Execute Command** (documentación oficial de n8n), así que FFmpeg vive en un servicio HTTP propio que escala a cero. |
| **Google Drive** (almacenamiento) | Registro de voces, WAV y manifiestos | 15 GB gratis. Un episodio de ~90 s en WAV 48 kHz mono pesa ~9 MB. |

## 2. Servicios y límites gratuitos (verificados en noviembre de 2026)

| Servicio | Gratis | Después | Ojo |
|---|---|---|---|
| Azure AI Speech F0 | **500,000 caracteres/mes** de TTS neuronal; 5 h/mes de STT | ~$15 USD por millón de caracteres (S0) | F0 permite **20 solicitudes por minuto**: el workflow espera 3.2 s entre clips. Un episodio como el 01 usa ~4,600 caracteres de SSML → **~100 episodios al mes gratis**. Crear la cuenta de Azure pide tarjeta, pero F0 no cobra. |
| n8n Cloud | **No tiene nivel gratuito permanente**: prueba de 14 días | Starter ≈ €20–24/mes (2,500 ejecuciones) | Los precios varían según la fuente. **No contrato nada sin tu permiso.** Alternativa gratis: n8n Community autoalojado en Cloud Run o en una VM gratuita (el workflow es el mismo). |
| Google Cloud Run | 180,000 vCPU-s, 360,000 GiB-s y 2 millones de solicitudes al mes | Por segundo de uso | Procesar un clip toma ~1 s → el worker cabe de sobra en el nivel gratuito. Requiere un proyecto con facturación habilitada. |
| Google Drive | 15 GB | Google One | — |
| Chatterbox | Modelo gratis (MIT) | Costo de GPU por segundo de uso | ~3.5 GB de VRAM. Solo por lotes y apagando la GPU al terminar. |

Fuentes: [Azure TTS pricing (texttolab)](https://texttolab.com/blog/azure-text-to-speech-pricing), [Azure Speech free tier (lullula)](https://lullula.io/blog/azure-speech-free-tier), [Cartesia: Azure TTS pricing](https://www.cartesia.ai/learn/top-microsoft-azure-text-to-speech-alternatives), [n8n pricing 2026 (activepieces)](https://www.activepieces.com/blog/n8n-pricing-2026-plans-free-tier-costs-explained), [n8n pricing (jetadmin)](https://www.jetadmin.io/blog/n8n-pricing/), [n8n docs: Execute Command (no disponible en Cloud)](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.executecommand), [Cloud Run pricing](https://cloud.google.com/run/pricing), [Chatterbox (Resemble AI)](https://www.resemble.ai/learn/models/chatterbox), [NVIDIA Chatterbox model card](https://docs.nvidia.com/ace-for-games/chatterbox-tts/nvigi-chatterbox-model-card.html).

Confirma siempre los precios en las páginas oficiales antes de pagar algo.

## 3. Registro de voces (`character_voice_registry.json`)

Cada personaje tiene estos campos:
- `character_id`, `nombre`, `aliases` (para reconocerlo en el texto)
- `engine` y `voice_id`
- `idioma`, `descripcion_vocal` y `personalidad`
- `velocidad_predeterminada`, `tono` y `volumen`
- `parametros_emocionales`: emoción por defecto, emociones permitidas y estilo máximo
- `supported_styles`, `voice_version` y `approval_status`
- `casting_candidates`: voces a probar en el casting

Reglas:
- **Bloqueo de voz:** el sistema solo lee el `voice_id`, nunca lo escribe.
  - Cambiar una voz aprobada exige editar el archivo a mano y subir `voice_version`.
  - El manifiesto guarda la versión usada en cada clip.
- **Producción solo con voces aprobadas:** si un personaje no está `approved`, el workflow rechaza el guion (salvo en modo `test`).
- **Estilos reales, no etiquetas:** `supported_styles` se llena con la lista real de Azure (`neon_tts.py voices` + `validate`).
  - Si la voz soporta la emoción (ej. `whispering`), se usa `mstts:express-as`.
  - Si no la soporta, la emoción se interpreta **solo con prosodia y pausas**. El manifiesto lo marca como `interpretation: prosody_only`.
- **Presets de emoción:** cada preset define estilos candidatos, intensidad, velocidad, tono, volumen y pausas previa y posterior. Hay 12:
  - neutral, calma, alegría, preocupación, miedo, desesperación
  - tristeza, susurro, enojo, grito, narración de terror, narración cálida

  La `intensity` de cada línea (0–2) escala el estilo y la prosodia.

Casting inicial (candidatos, **pendientes de tu aprobación**):

| Personaje | Voz propuesta | Alternativas |
|---|---|---|
| Narrador | es-MX-JorgeNeural | GerardoNeural, LibertoNeural |
| Daniel | es-MX-CecilioNeural | LucianoNeural, YagoNeural |
| Laura | es-MX-DaliaNeural | RenataNeural, LarissaNeural |
| Sofía | es-MX-MarinaNeural | NuriaNeural, CandelaNeural |
| Marcos (teléfono) | es-MX-PelayoNeural | LibertoNeural |
| Hombre en la puerta | es-MX-GerardoNeural | LibertoNeural |

Notas del casting:
- Todas las voces se validan contra la lista real de Azure antes de usarse.
- Microsoft también anuncia voces es-MX nuevas (serie MAI, ej. «Alejo» y «Valeria») con estilos como *fearful*, *whispering* y *sad*, ideales para terror. Las incluyo en el casting si aparecen en `voices/list` de tu región.
- Sofía necesita una voz infantil real. Si ninguna voz de Azure convence, es el primer caso para Chatterbox.

## 4. Formato del guion (lo que envía Claude)

Opción A, texto (el sistema identifica personajes, escenas y acotaciones):
```
ESCENA 5
NARRADOR (terror): Y entonces… tres golpes sacuden la puerta.
HOMBRE (gritando): ¡Por favor! ¡Déjenme entrar!
LAURA (susurro): Daniel… no lo dejes entrar.
```

Opción B, JSON con dirección completa por intervención (`tests/prueba_voces.json`):
```json
{"character_id": "laura", "text": "Daniel… no lo dejes entrar.", "emotion": "susurro", "intensity": 1.0,
 "pause_before_ms": 300, "pause_after_ms": 500, "intent": "Advertencia íntima"}
```

Pausas dentro de una línea: «…» agrega 350 ms y `[pausa 600ms]` permite una pausa exacta.

Cuerpo del webhook:
```json
{"script_text": "...", "episode_id": "E001", "mode": "test"}
{"script": {...}, "mode": "production"}
{"script": {...}, "clip_ids": ["E001_SC005_LAURA_001"]}   ← regenera solo esos clips (nueva toma _T02)
```

## 5. Salida

- **Archivos:** `E001_SC005_LAURA_001.wav`, en WAV 48 kHz mono 16 bits, normalizado a −18 LUFS con pico máximo de −1.5 dBTP.
  - Las tomas nuevas se guardan como `_T02`, `_T03`, … y nunca sobrescriben las anteriores.
- **Manifiesto `E001_manifest.json`.** Cada clip incluye:
  - `episode_id`, `scene_id`, `clip_id`, `character_id`, `voice_id`, `voice_version`
  - `text`, `emotion`, `intensity`, `style`, `interpretation`, `speaking_rate`, `pitch`, `volume`
  - `pause_before_ms`, `pause_after_ms`, `intent`, `output_file`, `drive_file_id`
  - `duration` (**medida con FFmpeg después de generar**, nunca estimada), `sequence`, `take`, `content_hash`, `qa`, `generation_status`
- **Estados:** `generated` · `needs_review` (QA detectó algo) · `failed` · `skipped` · `approved` / `rejected` (los pones tú).
  - Para pedir otra toma, marca el clip como `rejected` en el manifiesto y vuelve a enviar el guion: solo se regenera ese clip.

## 6. Control de calidad

Revisión automática en cada clip:
1. El archivo existe y FFmpeg lo decodifica; si no, queda en `failed`.
2. **Palabras omitidas o cambiadas:** Azure STT transcribe el clip y se mide la tasa de error por palabra (WER).
   - Si es mayor al 15 %, el clip queda en `needs_review`.
   - Además se compara la duración real con la esperada para el texto.
3. Saturación (pico > −1 dBFS), silencios internos > 1.6 s y volumen fuera de rango.
4. Correspondencia texto ↔ archivo: el nombre, el hash del SSML y la transcripción quedan en el manifiesto.

Revisión humana (la aprobación final siempre es tuya): acento mexicano, identidad de voz, naturalidad y emoción. Un clip pasa a `approved` solo cuando tú lo apruebas.

## 7. Reintentos e idempotencia

- **Reintentos:** cada llamada (Azure, worker, Drive) se reintenta 3 veces cada 5 s. Los errores de autenticación no se reintentan.
  - Si sigue fallando, el clip queda en `failed` con el mensaje de error y el lote **continúa**.
  - El informe final lista los fallidos.
- **Sin duplicados:**
  - Hash = motor + voz + versión de voz + SSML + formato de salida.
  - Si el clip ya existe con el mismo hash, no se vuelve a pedir a Azure (no se gastan caracteres).
  - El hash es idéntico en n8n (JavaScript) y en `neon_tts.py` (Python); está verificado.

## 8. Seguridad

- Las claves de Azure, el token del worker y el token del webhook viven **solo** en el gestor de credenciales de n8n (y el token del worker en Google Secret Manager).
- El registro, los guiones, los manifiestos y este repositorio no contienen claves.
- El webhook y el worker rechazan las solicitudes sin token (probado: 401).

## 9. Instalación (cuando apruebes)

1. **Azure:** crea un recurso *Speech* con plan **F0 (gratis)**, de preferencia en la región **East US**, que tiene el catálogo de voces más amplio. Necesitas la clave y la región.
2. **Google Cloud:** ejecuta `PROJECT=tu-proyecto worker/deploy.sh`. Despliega el worker con mínimo 0 instancias y crea el token en Secret Manager.
3. **Google Drive:** crea la carpeta `NEON TTS` y sube `character_voice_registry.json`.
4. **n8n:**
   - Importa `n8n/neon_tts_workflow.json`.
   - Crea 4 credenciales:
     - *Header Auth* `Ocp-Apim-Subscription-Key`
     - *Header Auth* `X-Worker-Token`
     - *Header Auth* del webhook
     - *Google Drive OAuth2*
   - Rellena el nodo **Config**: región, ID de la carpeta, ID del registro y URL del worker.
5. **Prueba:** envía `tests/prueba_voces.json` con `"mode": "test"`.

## 10. Archivos

| Archivo | Qué es |
|---|---|
| `character_voice_registry.json` | Registro permanente de voces y presets de emoción |
| `n8n/neon_tts_workflow.json` | Workflow importable (30 nodos), generado por `n8n/build_workflow.py` |
| `n8n/plan_core.js` | Lógica de planeación del nodo Code (validación, voces, emociones, SSML, hash, idempotencia) |
| `worker/` | audio-worker para Cloud Run: `app.py`, `Dockerfile`, `deploy.sh` |
| `tools/neon_tts.py` | Implementación de referencia y herramienta: voces, validación, casting, generación por lotes, revisión |
| `scripts/E001_guion.txt` / `.json` | Episodio 01 en formato de texto y estructurado (14 intervenciones) |
| `tests/prueba_voces.json` | Prueba: narrador, Daniel, Laura y Sofía con 6 emociones distintas |
