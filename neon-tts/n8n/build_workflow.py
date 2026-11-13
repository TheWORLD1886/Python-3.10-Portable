#!/usr/bin/env python3
"""Genera n8n/neon_tts_workflow.json (importable en n8n Cloud: Workflows → Import from file).
La lógica de planeación se incrusta desde plan_core.js para que n8n y tools/neon_tts.py nunca diverjan."""
import json, uuid
from pathlib import Path
HERE = Path(__file__).resolve().parent
CORE = (HERE / 'plan_core.js').read_text(encoding='utf-8').replace("if (typeof module !== 'undefined') module.exports = { planAll, parseText, cyrb53, buildSsml, resolveLine };", '')

nodes, conns = [], {}
def node(name, type_, ver, params, pos, **extra):
    nodes.append({'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'neon-tts/' + name)), 'name': name, 'type': type_, 'typeVersion': ver, 'position': pos, 'parameters': params, **extra})
def link(a, b, out=0, inp=0):
    conns.setdefault(a, {'main': []})
    while len(conns[a]['main']) <= out: conns[a]['main'].append([])
    conns[a]['main'][out].append({'node': b, 'type': 'main', 'index': inp})
def code(name, js, pos, mode='runOnceForAllItems'):
    p = {'jsCode': js}
    if mode != 'runOnceForAllItems': p['mode'] = mode
    node(name, 'n8n-nodes-base.code', 2, p, pos)
CRED_AZ = {'httpHeaderAuth': {'id': '', 'name': 'Azure Speech key (Ocp-Apim-Subscription-Key)'}}
CRED_WK = {'httpHeaderAuth': {'id': '', 'name': 'NEON audio-worker token (X-Worker-Token)'}}
CRED_HOOK = {'httpHeaderAuth': {'id': '', 'name': 'NEON webhook token'}}
CRED_DRIVE = {'googleDriveOAuth2Api': {'id': '', 'name': 'Google Drive NEON'}}
RETRY = dict(retryOnFail=True, maxTries=3, waitBetweenTries=5000)
cfg = "$('Config').first().json"

node('Webhook: recibir guion', 'n8n-nodes-base.webhook', 2, {'httpMethod': 'POST', 'path': 'neon-tts', 'authentication': 'headerAuth', 'responseMode': 'responseNode', 'options': {}},
     [0, 300], webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, 'neon-tts-hook')), credentials=CRED_HOOK)
node('Config', 'n8n-nodes-base.set', 3.4, {'assignments': {'assignments': [
    {'id': 'a1', 'name': 'azure_region', 'value': 'eastus', 'type': 'string'},
    {'id': 'a2', 'name': 'drive_folder_id', 'value': 'PEGA_AQUI_ID_CARPETA_DRIVE', 'type': 'string'},
    {'id': 'a3', 'name': 'registry_file_id', 'value': 'PEGA_AQUI_ID_DE_character_voice_registry.json', 'type': 'string'},
    {'id': 'a4', 'name': 'worker_url', 'value': 'https://neon-audio-worker-XXXX.a.run.app', 'type': 'string'},
    {'id': 'a5', 'name': 'episode_id', 'value': "={{ $json.body.episode_id || ($json.body.script && $json.body.script.episode_id) || 'E001' }}", 'type': 'string'}]}, 'options': {}}, [220, 300])
node('Descargar registro de voces', 'n8n-nodes-base.googleDrive', 3, {'operation': 'download', 'fileId': {'__rl': True, 'value': '={{ $json.registry_file_id }}', 'mode': 'id'}, 'options': {}}, [440, 300], credentials=CRED_DRIVE, **RETRY)
node('Registro a JSON', 'n8n-nodes-base.extractFromFile', 1, {'operation': 'fromJson', 'options': {}}, [660, 300])
node('Buscar manifiesto', 'n8n-nodes-base.googleDrive', 3, {'resource': 'fileFolder', 'searchMethod': 'name', 'queryString': f"={{{{ {cfg}.episode_id }}}}_manifest.json",
     'filter': {'folderId': {'__rl': True, 'value': f"={{{{ {cfg}.drive_folder_id }}}}", 'mode': 'id'}}, 'options': {}}, [880, 300], credentials=CRED_DRIVE, alwaysOutputData=True)
node('¿Existe manifiesto?', 'n8n-nodes-base.if', 2, {'conditions': {'options': {'caseSensitive': True, 'typeValidation': 'loose'}, 'combinator': 'and',
     'conditions': [{'id': 'c1', 'leftValue': '={{ $json.id }}', 'rightValue': '', 'operator': {'type': 'string', 'operation': 'exists', 'singleValue': True}}]}, 'options': {}}, [1100, 300])
node('Descargar manifiesto', 'n8n-nodes-base.googleDrive', 3, {'operation': 'download', 'fileId': {'__rl': True, 'value': '={{ $json.id }}', 'mode': 'id'}, 'options': {}}, [1320, 200], credentials=CRED_DRIVE, **RETRY)
node('Manifiesto a JSON', 'n8n-nodes-base.extractFromFile', 1, {'operation': 'fromJson', 'options': {}}, [1540, 200])
code('Sin manifiesto previo', "return [{ json: { data: null } }];", [1320, 420])

code('Plan: validar, asignar voces y SSML', CORE + r"""
// ---------------------------------------------------------------- nodo n8n
const body = $('Webhook: recibir guion').first().json.body || {};
const registry = $('Registro a JSON').first().json.data;
const old = $input.first().json.data || null;
let script = body.script;
if (!script && body.script_text) script = parseText(body.script_text, registry, body.episode_id || 'E001');
if (!script) return [{ json: { _validation_errors: ['El cuerpo debe traer "script" (estructurado) o "script_text" (texto con PERSONAJE: línea).'] } }];
const { clips, errors } = planAll(script, registry, old, { mode: body.mode || 'production', clip_ids: body.clip_ids });
if (errors.length) return [{ json: { _validation_errors: errors } }];
return clips.map(c => ({ json: c }));
""", [1760, 300])
node('¿Guion válido?', 'n8n-nodes-base.if', 2, {'conditions': {'options': {'caseSensitive': True, 'typeValidation': 'loose'}, 'combinator': 'and',
     'conditions': [{'id': 'v1', 'leftValue': '={{ $json._validation_errors }}', 'rightValue': '', 'operator': {'type': 'array', 'operation': 'notExists', 'singleValue': True}}]}, 'options': {}}, [1980, 300])
node('Responder: guion inválido', 'n8n-nodes-base.respondToWebhook', 1.1, {'respondWith': 'json', 'responseBody': '={{ { ok: false, errors: $json._validation_errors } }}', 'options': {'responseCode': 422}}, [2200, 480])

node('Lote (1 clip por vuelta)', 'n8n-nodes-base.splitInBatches', 3, {'batchSize': 1, 'options': {}}, [2200, 200])
node('¿Generar este clip?', 'n8n-nodes-base.if', 2, {'conditions': {'options': {'caseSensitive': True, 'typeValidation': 'strict'}, 'combinator': 'and',
     'conditions': [{'id': 'g1', 'leftValue': '={{ $json.action }}', 'rightValue': 'generate', 'operator': {'type': 'string', 'operation': 'equals'}}]}, 'options': {}}, [2420, 120])
code('Fila: omitido (ya existe)', "return $input.all().map(i => ({ json: { ...i.json.previous, ...i.json, ssml: undefined, previous: undefined, generation_status: (i.json.previous || {}).generation_status || 'skipped' } }));", [2640, 360])

node('Azure TTS', 'n8n-nodes-base.httpRequest', 4.2, {'method': 'POST', 'url': f"=https://{{{{ {cfg}.azure_region }}}}.tts.speech.microsoft.com/cognitiveservices/v1",
     'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth', 'sendHeaders': True,
     'headerParameters': {'parameters': [{'name': 'X-Microsoft-OutputFormat', 'value': 'riff-48khz-16bit-mono-pcm'}, {'name': 'User-Agent', 'value': 'neon-tts-n8n'}]},
     'sendBody': True, 'contentType': 'raw', 'rawContentType': 'application/ssml+xml', 'body': '={{ $json.ssml }}',
     'options': {'response': {'response': {'responseFormat': 'file', 'outputPropertyName': 'data'}}, 'timeout': 60000}},
     [2640, 40], credentials=CRED_AZ, onError='continueErrorOutput', **RETRY)
node('Worker: normalizar y medir (FFmpeg)', 'n8n-nodes-base.httpRequest', 4.2, {'method': 'POST', 'url': f"={{{{ {cfg}.worker_url }}}}/process",
     'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth', 'sendBody': True, 'contentType': 'multipart-form-data',
     'bodyParameters': {'parameters': [{'parameterType': 'formBinaryData', 'name': 'audio', 'inputDataFieldName': 'data'},
                                       {'name': 'text', 'value': "={{ $('Lote (1 clip por vuelta)').item.json.text }}"},
                                       {'name': 'speaking_rate', 'value': "={{ $('Lote (1 clip por vuelta)').item.json.speaking_rate }}"},
                                       {'name': 'post_fx', 'value': "={{ $('Lote (1 clip por vuelta)').item.json.post_fx || '' }}"}]},
     'options': {'timeout': 120000}}, [2860, 40], credentials=CRED_WK, onError='continueErrorOutput', **RETRY)
code('Preparar audio para STT', "return $input.all().map(i => ({ json: { ...i.json, audio_b64: undefined }, binary: { stt: { data: i.json.stt16k_b64, mimeType: 'audio/wav', fileName: 'stt.wav' } } }));", [3080, 40])
node('Azure STT (verificar texto)', 'n8n-nodes-base.httpRequest', 4.2, {'method': 'POST',
     'url': f"=https://{{{{ {cfg}.azure_region }}}}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=es-MX&format=simple",
     'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth', 'sendHeaders': True,
     'headerParameters': {'parameters': [{'name': 'Content-Type', 'value': 'audio/wav; codecs=audio/pcm; samplerate=16000'}]},
     'sendBody': True, 'contentType': 'binaryData', 'inputDataFieldName': 'stt', 'options': {'timeout': 60000}},
     [3300, 40], credentials=CRED_AZ, onError='continueRegularOutput', **RETRY)
node('Worker: comparar texto (WER)', 'n8n-nodes-base.httpRequest', 4.2, {'method': 'POST', 'url': f"={{{{ {cfg}.worker_url }}}}/wer",
     'authentication': 'genericCredentialType', 'genericAuthType': 'httpHeaderAuth', 'sendBody': True, 'specifyBody': 'json',
     'jsonBody': "={{ JSON.stringify({ text: $('Lote (1 clip por vuelta)').item.json.text, transcript: $json.DisplayText || '' }) }}", 'options': {}},
     [3520, 40], credentials=CRED_WK, onError='continueRegularOutput')
code('Armar resultado + WAV', r"""
return $input.all().map((i, k) => {
  const clip = $('Lote (1 clip por vuelta)').itemMatching(k).json;
  const w = $('Worker: normalizar y medir (FFmpeg)').itemMatching(k).json;
  const stt = $('Azure STT (verificar texto)').itemMatching(k).json || {};
  const flags = [...(w.qa.flags || [])];
  const wer = typeof i.json.wer === 'number' ? i.json.wer : null;
  if (wer === null) flags.push('stt_no_disponible'); else if (wer > 0.15) flags.push('transcripcion_no_coincide');
  const row = { ...clip, ssml: undefined, previous: undefined, action: undefined, duration: w.duration,   // duración REAL medida por FFmpeg
    qa: { ...w.qa, transcript: stt.DisplayText || null, wer, flags }, post_version: w.post_version,
    generation_status: flags.length ? 'needs_review' : 'generated' };
  return { json: row, binary: { wav: { data: w.audio_b64, mimeType: 'audio/wav', fileName: clip.output_file } } };
});""", [3740, 40])
node('Subir WAV a Drive', 'n8n-nodes-base.googleDrive', 3, {'name': '={{ $json.output_file }}', 'inputDataFieldName': 'wav',
     'driveId': {'__rl': True, 'value': 'My Drive', 'mode': 'list'}, 'folderId': {'__rl': True, 'value': f"={{{{ {cfg}.drive_folder_id }}}}", 'mode': 'id'}, 'options': {}},
     [3960, 40], credentials=CRED_DRIVE, onError='continueErrorOutput', **RETRY)
code('Fila: generado', "return $input.all().map((i, k) => ({ json: { ...$('Armar resultado + WAV').itemMatching(k).json, drive_file_id: i.json.id } }));", [4180, 0])
code('Fila: fallido', r"""
return $input.all().map((i, k) => {
  const clip = $('Lote (1 clip por vuelta)').itemMatching(k).json;
  const err = (i.json.error && (i.json.error.message || i.json.error.description)) || i.json.message || 'error desconocido';
  return { json: { ...clip, ssml: undefined, previous: undefined, action: undefined, duration: null, generation_status: 'failed', error: String(err).slice(0, 300) } };
});""", [4180, 240])
node('Esperar (límite 20/min del nivel gratuito)', 'n8n-nodes-base.wait', 1.1, {'amount': 3.2}, [4400, 120], webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, 'neon-wait')))

code('Armar manifiesto', r"""
const rows = $input.all().map(i => i.json).filter(r => r.clip_id).sort((a, b) => a.sequence - b.sequence);
const summary = {};
for (const r of rows) summary[r.generation_status] = (summary[r.generation_status] || 0) + 1;
const reg = $('Registro a JSON').first().json.data;
const manifest = { episode_id: $('Config').first().json.episode_id, generated_at: new Date().toISOString(), registry_version: reg.registry_version,
  clips: rows.map(r => ({ episode_id: r.episode_id, scene_id: r.scene_id, clip_id: r.clip_id, sequence: r.sequence, character_id: r.character_id,
    voice_id: r.voice_id, voice_version: r.voice_version, text: r.text, emotion: r.emotion, intensity: r.intensity, style: r.style, styledegree: r.styledegree,
    interpretation: r.interpretation, speaking_rate: r.speaking_rate, pitch: r.pitch, volume: r.volume, pause_before_ms: r.pause_before_ms,
    pause_after_ms: r.pause_after_ms, intent: r.intent, post_fx: r.post_fx, output_file: r.output_file, drive_file_id: r.drive_file_id || null,
    duration: r.duration ?? null, take: r.take, content_hash: r.content_hash, qa: r.qa || null, generation_status: r.generation_status, error: r.error || null })),
  summary };
const txt = JSON.stringify(manifest, null, 2);
return [{ json: { manifest, summary, failed: manifest.clips.filter(c => c.generation_status === 'failed').map(c => ({ clip_id: c.clip_id, error: c.error })),
  needs_review: manifest.clips.filter(c => c.generation_status === 'needs_review').map(c => ({ clip_id: c.clip_id, flags: c.qa && c.qa.flags })) },
  binary: { manifest: { data: Buffer.from(txt, 'utf8').toString('base64'), mimeType: 'application/json', fileName: `${manifest.episode_id}_manifest.json` } } }];
""", [2420, -160])
node('¿Actualizar manifiesto existente?', 'n8n-nodes-base.if', 2, {'conditions': {'options': {'caseSensitive': True, 'typeValidation': 'loose'}, 'combinator': 'and',
     'conditions': [{'id': 'm1', 'leftValue': "={{ $('Buscar manifiesto').first().json.id }}", 'rightValue': '', 'operator': {'type': 'string', 'operation': 'exists', 'singleValue': True}}]}, 'options': {}}, [2640, -160])
node('Actualizar manifiesto en Drive', 'n8n-nodes-base.googleDrive', 3, {'operation': 'update', 'fileId': {'__rl': True, 'value': "={{ $('Buscar manifiesto').first().json.id }}", 'mode': 'id'},
     'changeFileContent': True, 'inputDataFieldName': 'manifest', 'updateFields': {}}, [2860, -260], credentials=CRED_DRIVE, **RETRY)
node('Crear manifiesto en Drive', 'n8n-nodes-base.googleDrive', 3, {'name': "={{ $('Config').first().json.episode_id }}_manifest.json", 'inputDataFieldName': 'manifest',
     'driveId': {'__rl': True, 'value': 'My Drive', 'mode': 'list'}, 'folderId': {'__rl': True, 'value': f"={{{{ {cfg}.drive_folder_id }}}}", 'mode': 'id'}, 'options': {}},
     [2860, -60], credentials=CRED_DRIVE, **RETRY)
node('Responder: informe', 'n8n-nodes-base.respondToWebhook', 1.1, {'respondWith': 'json',
     'responseBody': "={{ { ok: $('Armar manifiesto').first().json.failed.length === 0, summary: $('Armar manifiesto').first().json.summary, failed: $('Armar manifiesto').first().json.failed, needs_review: $('Armar manifiesto').first().json.needs_review, manifest_file: $('Config').first().json.episode_id + '_manifest.json' } }}",
     'options': {}}, [3080, -160])

link('Webhook: recibir guion', 'Config'); link('Config', 'Descargar registro de voces'); link('Descargar registro de voces', 'Registro a JSON')
link('Registro a JSON', 'Buscar manifiesto'); link('Buscar manifiesto', '¿Existe manifiesto?')
link('¿Existe manifiesto?', 'Descargar manifiesto', 0); link('¿Existe manifiesto?', 'Sin manifiesto previo', 1)
link('Descargar manifiesto', 'Manifiesto a JSON'); link('Manifiesto a JSON', 'Plan: validar, asignar voces y SSML'); link('Sin manifiesto previo', 'Plan: validar, asignar voces y SSML')
link('Plan: validar, asignar voces y SSML', '¿Guion válido?'); link('¿Guion válido?', 'Lote (1 clip por vuelta)', 0); link('¿Guion válido?', 'Responder: guion inválido', 1)
link('Lote (1 clip por vuelta)', 'Armar manifiesto', 0); link('Lote (1 clip por vuelta)', '¿Generar este clip?', 1)
link('¿Generar este clip?', 'Azure TTS', 0); link('¿Generar este clip?', 'Fila: omitido (ya existe)', 1); link('Fila: omitido (ya existe)', 'Lote (1 clip por vuelta)')
link('Azure TTS', 'Worker: normalizar y medir (FFmpeg)', 0); link('Azure TTS', 'Fila: fallido', 1)
link('Worker: normalizar y medir (FFmpeg)', 'Preparar audio para STT', 0); link('Worker: normalizar y medir (FFmpeg)', 'Fila: fallido', 1)
link('Preparar audio para STT', 'Azure STT (verificar texto)'); link('Azure STT (verificar texto)', 'Worker: comparar texto (WER)')
link('Worker: comparar texto (WER)', 'Armar resultado + WAV'); link('Armar resultado + WAV', 'Subir WAV a Drive')
link('Subir WAV a Drive', 'Fila: generado', 0); link('Subir WAV a Drive', 'Fila: fallido', 1)
link('Fila: generado', 'Esperar (límite 20/min del nivel gratuito)'); link('Fila: fallido', 'Esperar (límite 20/min del nivel gratuito)')
link('Esperar (límite 20/min del nivel gratuito)', 'Lote (1 clip por vuelta)')
link('Armar manifiesto', '¿Actualizar manifiesto existente?'); link('¿Actualizar manifiesto existente?', 'Actualizar manifiesto en Drive', 0); link('¿Actualizar manifiesto existente?', 'Crear manifiesto en Drive', 1)
link('Actualizar manifiesto en Drive', 'Responder: informe'); link('Crear manifiesto en Drive', 'Responder: informe')

wf = {'name': 'NEON TTS · doblaje multipersona', 'nodes': nodes, 'connections': conns, 'active': False,
      'settings': {'executionOrder': 'v1', 'saveManualExecutions': True, 'timezone': 'America/Mexico_City'}, 'pinData': {}, 'meta': {'templateCredsSetupCompleted': False}}
names = {n['name'] for n in nodes}
for a, c in conns.items():
    assert a in names, a
    for outs in c['main']:
        for l in outs: assert l['node'] in names, l['node']
(HERE / 'neon_tts_workflow.json').write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding='utf-8')
print(len(nodes), 'nodos ·', sum(len(o) for c in conns.values() for o in c['main']), 'conexiones')
