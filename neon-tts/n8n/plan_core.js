// NEON TTS · lógica de planeación (la misma que tools/neon_tts.py, para el nodo Code de n8n).
// Recibe el guion, el registro de voces y el manifiesto anterior; devuelve un item por intervención
// con su voz, dirección de doblaje, SSML, hash y acción: generate | skip.
const OUTPUT_FORMAT = 'riff-48khz-16bit-mono-pcm';

function norm(s) { return s.toUpperCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
function pct(s) { return parseFloat(String(s).replace('%', '')) || 0; }
function fmtPct(v) { const r = Math.round(v); return (r >= 0 ? '+' : '') + r + '%'; }
function addPct(...xs) { return fmtPct(xs.reduce((a, x) => a + pct(x), 0)); }
function cyrb53(str, seed = 0) {
  let h1 = 0xdeadbeef ^ seed, h2 = 0x41c6ce57 ^ seed;
  for (let i = 0; i < str.length; i++) { const c = str.charCodeAt(i); h1 = Math.imul(h1 ^ c, 2654435761); h2 = Math.imul(h2 ^ c, 1597334677); }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(16);
}
function escapeXml(t) { return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function ssmlBody(text) {
  return escapeXml(text).replace(/\[pausa (\d+)ms\]/g, '<break time="$1ms"/>').replace(/(…|\.\.\.)/g, '$1<break time="350ms"/>');
}
// JSON.stringify igual al de Python (ensure_ascii=False, separators=(',', ':'))
function pyJson(x) { return JSON.stringify(x); }

const DIRECTION_EMOTION = { susurro: 'susurro', susurra: 'susurro', grita: 'grito', gritando: 'grito', llorando: 'tristeza', triste: 'tristeza',
  miedo: 'miedo', asustad: 'miedo', desesper: 'desesperacion', enojad: 'enojo', furios: 'enojo', alegre: 'alegria',
  calma: 'calma', tranquil: 'calma', preocupad: 'preocupacion', terror: 'narracion_terror' };

function parseText(txt, registry, episodeId = 'E001') {
  const alias = {}; for (const c of registry.characters) for (const a of [...c.aliases, c.nombre]) alias[norm(a)] = c.character_id;
  const scenes = []; let cur = null; const unknown = new Set();
  for (const raw of txt.split(/\r?\n/)) {
    if (!raw.trim()) continue;
    let m = raw.match(/^\s*(?:ESCENA|SCENE)\s+(\d+)/i);
    if (m) { cur = { scene_id: 'SC' + String(parseInt(m[1])).padStart(3, '0'), lines: [] }; scenes.push(cur); continue; }
    m = raw.match(/^\s*([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ _]{1,40})\s*(?:\(([^)]*)\))?\s*:\s*(.+)$/);
    if (!m) continue;
    const who = norm(m[1].trim()), direction = (m[2] || '').toLowerCase(), text = m[3].trim().replace(/^[“”"]+|[“”"]+$/g, '');
    const cid = alias[who]; if (!cid) { unknown.add(m[1].trim()); continue; }
    const emo = Object.entries(DIRECTION_EMOTION).find(([k]) => direction.includes(k));
    if (!cur) { cur = { scene_id: 'SC001', lines: [] }; scenes.push(cur); }
    const line = { character_id: cid, text }; if (emo) line.emotion = emo[1]; if (direction) line.direction = direction;
    cur.lines.push(line);
  }
  return { episode_id: episodeId, language: 'es-MX', scenes, unknown_speakers: [...unknown].sort() };
}

function resolveLine(line, ch, presets) {
  const emo = line.emotion || ch.parametros_emocionales.default_emotion;
  if (!presets[emo]) throw new Error(`emoción desconocida: ${emo}`);
  const allowed = ch.parametros_emocionales.allowed_emotions;
  if (allowed && !allowed.includes(emo)) throw new Error(`${ch.character_id}: la emoción «${emo}» no está permitida para este personaje`);
  const pr = presets[emo], k = parseFloat(line.intensity ?? 1.0), sup = ch.supported_styles || [];
  const style = pr.styles.find(s => sup.includes(s)) || null;                // solo estilos reales de la voz
  const degree = style ? (Math.round(Math.min(ch.parametros_emocionales.max_styledegree ?? 2.0, Math.max(.01, pr.styledegree * k)) * 100) / 100).toFixed(2) : null;
  const scale = v => fmtPct(pct(v) * k);
  return { emotion: emo, intensity: k, style, styledegree: degree, interpretation: style ? 'style+prosody' : 'prosody_only',
    speaking_rate: line.rate || addPct(ch.velocidad_predeterminada, scale(pr.rate)),
    pitch: line.pitch || addPct(ch.tono, scale(pr.pitch)),
    volume: line.volume || addPct(ch.volumen || '0%', scale(pr.volume)),
    pause_before_ms: parseInt(line.pause_before_ms ?? pr.pause_before_ms), pause_after_ms: parseInt(line.pause_after_ms ?? pr.pause_after_ms),
    intent: line.intent || '' };
}

function buildSsml(text, ch, d, locale = 'es-MX') {
  let body = `<prosody rate="${d.speaking_rate}" pitch="${d.pitch}" volume="${d.volume}">${ssmlBody(text)}</prosody>`;
  if (d.style) body = `<mstts:express-as style="${d.style}" styledegree="${d.styledegree}">${body}</mstts:express-as>`;
  return `<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="${locale}"><voice name="${ch.voice_id}">${body}</voice></speak>`;
}

function planAll(script, registry, oldManifest, opts = {}) {
  const mode = opts.mode || 'production', only = opts.clip_ids ? new Set(opts.clip_ids) : null;
  const chars = Object.fromEntries(registry.characters.map(c => [c.character_id, c])), presets = registry.emotion_presets;
  const old = Object.fromEntries(((oldManifest && oldManifest.clips) || []).map(c => [c.clip_id, c]));
  const out = [], errors = []; let seq = 0;
  if (script.unknown_speakers && script.unknown_speakers.length) errors.push(`personajes sin voz registrada: ${script.unknown_speakers.join(', ')}`);
  for (const sc of script.scenes) {
    const count = {};
    for (const line of sc.lines) {
      const cid = line.character_id, ch = chars[cid];
      if (!ch) { errors.push(`${sc.scene_id}: personaje no registrado «${cid}»`); continue; }
      if (mode === 'production' && ch.approval_status !== 'approved') { errors.push(`${cid}: voz no aprobada (estado ${ch.approval_status})`); continue; }
      count[cid] = (count[cid] || 0) + 1; seq += 1;
      const clip_id = `${script.episode_id}_${sc.scene_id}_${cid.toUpperCase()}_${String(count[cid]).padStart(3, '0')}`;
      let d; try { d = resolveLine(line, ch, presets); } catch (e) { errors.push(`${clip_id}: ${e.message}`); continue; }
      const ssml = buildSsml(line.text, ch, d, script.language || 'es-MX');
      const content_hash = cyrb53(pyJson([ch.engine, ch.voice_id, ch.voice_version, ssml, OUTPUT_FORMAT]));
      const prev = old[clip_id]; let take = prev ? prev.take : 1, action = 'generate';
      const rejected = prev && prev.generation_status === 'rejected';
      if (only) { if (!only.has(clip_id)) action = 'skip'; else if (prev) take += 1; }
      else if (rejected) take += 1;
      else if (prev && prev.content_hash === content_hash && ['generated', 'needs_review', 'approved'].includes(prev.generation_status)) action = 'skip';
      const output_file = clip_id + (take > 1 ? `_T${String(take).padStart(2, '0')}` : '') + '.wav';
      out.push({ episode_id: script.episode_id, scene_id: sc.scene_id, clip_id, sequence: seq, character_id: cid, voice_id: ch.voice_id,
        voice_version: ch.voice_version, engine: ch.engine, text: line.text, ...d, post_fx: ch.post_fx || null, ssml, content_hash, take,
        output_file: action === 'skip' && prev ? prev.output_file : output_file, action, previous: action === 'skip' ? (prev || null) : null });
    }
  }
  return { clips: out, errors };
}

if (typeof module !== 'undefined') module.exports = { planAll, parseText, cyrb53, buildSsml, resolveLine };
