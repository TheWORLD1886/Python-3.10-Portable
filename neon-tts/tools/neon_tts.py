#!/usr/bin/env python3
"""
NEON CINEMATIC STUDIO · motor de doblaje TTS multipersona (implementación de referencia).

Hace lo mismo que el workflow de n8n y sirve para probarlo, para correrlo como trabajo por lotes
en la nube (Cloud Run Job) o como respaldo:

  python neon_tts.py voices                       # descarga la lista real de voces es-MX (estilos incluidos)
  python neon_tts.py validate                     # revisa el registro contra la lista real de voces
  python neon_tts.py parse guion.txt > ep.json    # guion en texto  ->  guion estructurado (JSON)
  python neon_tts.py plan ep.json                 # muestra los clips, voces, estilos y SSML sin gastar caracteres
  python neon_tts.py generate ep.json --mode test # genera, normaliza, mide y escribe el manifiesto
  python neon_tts.py generate ep.json --only E001_SC002_LAURA_001   # regenera solo clips rechazados
  python neon_tts.py casting --line "Texto de prueba" --character laura

Credenciales: AZURE_SPEECH_KEY y AZURE_SPEECH_REGION como variables de entorno (o en el gestor de
secretos de la nube). Nunca se escriben en archivos ni en el manifiesto.
"""
import argparse, hashlib, json, math, os, re, subprocess, sys, time, unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = Path(os.environ.get('NEON_REGISTRY', ROOT / 'character_voice_registry.json'))
VOICES_CACHE = ROOT / 'tools' / 'voices_es-MX.json'
POST_VERSION = 'post-v1'                # sube este valor si cambia la cadena de FFmpeg (se reprocesa sin volver a pagar TTS)
OUTPUT_FORMAT = 'riff-48khz-16bit-mono-pcm'
MIN_INTERVAL = 3.2                      # nivel gratuito F0: 20 solicitudes por minuto

def region(): return os.environ.get('AZURE_SPEECH_REGION', 'eastus')
def key(): return os.environ.get('AZURE_SPEECH_KEY', 'proxy-injected')
def tts_url(): return f'https://{region()}.tts.speech.microsoft.com/cognitiveservices/v1'
def voices_url(): return f'https://{region()}.tts.speech.microsoft.com/cognitiveservices/voices/list'
def stt_url(): return f'https://{region()}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=es-MX&format=simple'

def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def save_json(p, d): Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def norm(s): return ''.join(c for c in unicodedata.normalize('NFD', s.upper()) if unicodedata.category(c) != 'Mn')

# ================================================================ 1-3 · guion -> intervenciones
LINE_RE = re.compile(r'^\s*([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ _]{1,40})\s*(?:\(([^)]*)\))?\s*:\s*(.+)$')
SCENE_RE = re.compile(r'^\s*(?:ESCENA|SCENE)\s+(\d+)', re.I)
DIRECTION_EMOTION = {'susurro': 'susurro', 'susurra': 'susurro', 'grita': 'grito', 'gritando': 'grito', 'llorando': 'tristeza', 'triste': 'tristeza',
                     'miedo': 'miedo', 'asustad': 'miedo', 'desesper': 'desesperacion', 'enojad': 'enojo', 'furios': 'enojo', 'alegre': 'alegria',
                     'calma': 'calma', 'tranquil': 'calma', 'preocupad': 'preocupacion', 'terror': 'narracion_terror'}

def parse_text(txt, episode_id='E001'):
    """Guion en texto libre -> guion estructurado. Reconoce «PERSONAJE (acotación): texto» y «ESCENA n»."""
    reg = load_json(REGISTRY); alias = {norm(a): c['character_id'] for c in reg['characters'] for a in c['aliases'] + [c['nombre']]}
    scenes, cur, unknown = [], None, set()
    for raw in txt.splitlines():
        if not raw.strip(): continue
        m = SCENE_RE.match(raw)
        if m: cur = {'scene_id': f'SC{int(m.group(1)):03d}', 'lines': []}; scenes.append(cur); continue
        m = LINE_RE.match(raw)
        if not m: continue                                   # acotaciones de imagen: no se locutan
        who, direction, text = norm(m.group(1).strip()), (m.group(2) or '').lower(), m.group(3).strip().strip('“”"')
        cid = alias.get(who)
        if cid is None: unknown.add(m.group(1).strip()); continue
        emo = next((v for k, v in DIRECTION_EMOTION.items() if k in direction), None)
        if cur is None: cur = {'scene_id': 'SC001', 'lines': []}; scenes.append(cur)
        cur['lines'].append({'character_id': cid, 'text': text, **({'emotion': emo} if emo else {}), **({'direction': direction} if direction else {})})
    return {'episode_id': episode_id, 'language': 'es-MX', 'scenes': scenes, 'unknown_speakers': sorted(unknown)}

# ================================================================ 4-5 · registro, emociones y SSML
def pct(s): return float(str(s).rstrip('%') or 0)
def jsround(v): return math.floor(v + .5)                     # mismo redondeo que Math.round de JavaScript (n8n)
def fmt_pct(v): r = jsround(v); return f'{"+" if r >= 0 else ""}{r}%'
def add_pct(*xs): return fmt_pct(sum(pct(x) for x in xs))
def cyrb53(s, seed=0):
    """hash de 53 bits idéntico al del nodo Code de n8n (mismo resultado en Python y en JavaScript)."""
    M = 0xffffffff; imul = lambda a, b: (a * b) & M
    h1, h2 = 0xdeadbeef ^ seed, 0x41c6ce57 ^ seed
    b = s.encode('utf-16-le')
    for i in range(0, len(b), 2):
        c = b[i] | (b[i + 1] << 8); h1 = imul(h1 ^ c, 2654435761); h2 = imul(h2 ^ c, 1597334677)
    h1 = imul(h1 ^ (h1 >> 16), 2246822507) ^ imul(h2 ^ (h2 >> 13), 3266489909)
    h2 = imul(h2 ^ (h2 >> 16), 2246822507) ^ imul(h1 ^ (h1 >> 13), 3266489909)
    return format(4294967296 * (2097151 & h2) + h1, 'x')

def resolve_line(line, ch, presets):
    """Dirección de doblaje: combina el preset de la emoción, la intensidad y los valores del personaje.
    Solo usa estilos que la voz realmente soporta (supported_styles); si no, interpreta con prosodia."""
    emo = line.get('emotion') or ch['parametros_emocionales']['default_emotion']
    if emo not in presets: raise ValueError(f'emoción desconocida: {emo}')
    allowed = ch['parametros_emocionales'].get('allowed_emotions')
    if allowed and emo not in allowed: raise ValueError(f"{ch['character_id']}: la emoción «{emo}» no está permitida para este personaje")
    pr = presets[emo]; k = float(line.get('intensity', 1.0))                 # intensidad 0..2 escala el estilo y la prosodia
    sup = ch.get('supported_styles') or []
    style = next((s for s in pr['styles'] if s in sup), None)
    degree = f"{jsround(min(ch['parametros_emocionales'].get('max_styledegree', 2.0), max(.01, pr['styledegree'] * k)) * 100) / 100:.2f}" if style else None
    scale = lambda v: fmt_pct(pct(v) * k)
    return {
        'emotion': emo, 'intensity': k, 'style': style, 'styledegree': degree,
        'interpretation': 'style+prosody' if style else 'prosody_only',
        'speaking_rate': line.get('rate') or add_pct(ch['velocidad_predeterminada'], scale(pr['rate'])),
        'pitch': line.get('pitch') or add_pct(ch['tono'], scale(pr['pitch'])),
        'volume': line.get('volume') or add_pct(ch.get('volumen', '0%'), scale(pr['volume'])),
        'pause_before_ms': int(line.get('pause_before_ms', pr['pause_before_ms'])),
        'pause_after_ms': int(line.get('pause_after_ms', pr['pause_after_ms'])),
        'intent': line.get('intent', ''),
    }

def text_to_ssml_body(text):
    """«…» y «...» -> pausa de suspenso; el resto se escapa. Pausas explícitas: [pausa 400ms]."""
    t = escape(text)
    t = re.sub(r'\[pausa (\d+)ms\]', r'<break time="\1ms"/>', t)
    t = re.sub(r'(…|\.\.\.)', r'\1<break time="350ms"/>', t)
    return t

def build_ssml(text, ch, d, locale='es-MX'):
    body = f'<prosody rate="{d["speaking_rate"]}" pitch="{d["pitch"]}" volume="{d["volume"]}">{text_to_ssml_body(text)}</prosody>'
    if d['style']: body = f'<mstts:express-as style="{d["style"]}" styledegree="{d["styledegree"]}">{body}</mstts:express-as>'
    return (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{locale}">'
            f'<voice name="{ch["voice_id"]}">{body}</voice></speak>')

def plan(script, mode='production', only=None):
    reg = load_json(REGISTRY); chars = {c['character_id']: c for c in reg['characters']}; presets = reg['emotion_presets']
    ep = script['episode_id']; clips, errors, seq = [], [], 0
    for sc in script['scenes']:
        count = {}
        for line in sc['lines']:
            cid = line['character_id']; ch = chars.get(cid)
            if ch is None: errors.append(f"{sc['scene_id']}: personaje no registrado «{cid}»"); continue
            if mode == 'production' and ch['approval_status'] != 'approved':
                errors.append(f"{cid}: voz no aprobada (estado {ch['approval_status']}); usa --mode test o aprueba el casting"); continue
            count[cid] = count.get(cid, 0) + 1; seq += 1
            clip_id = f"{ep}_{sc['scene_id']}_{cid.upper()}_{count[cid]:03d}"
            try: d = resolve_line(line, ch, presets)
            except ValueError as e: errors.append(f'{clip_id}: {e}'); continue
            ssml = build_ssml(line['text'], ch, d, script.get('language', 'es-MX'))
            h = cyrb53(json.dumps([ch['engine'], ch['voice_id'], ch['voice_version'], ssml, OUTPUT_FORMAT], ensure_ascii=False, separators=(',', ':')))
            clips.append({'episode_id': ep, 'scene_id': sc['scene_id'], 'clip_id': clip_id, 'sequence': seq, 'character_id': cid,
                          'voice_id': ch['voice_id'], 'voice_version': ch['voice_version'], 'engine': ch['engine'], 'text': line['text'],
                          **d, 'post_fx': ch.get('post_fx'), 'ssml': ssml, 'content_hash': h, 'take': 1})
    if only: clips = [c for c in clips if c['clip_id'] in set(only)]
    return clips, errors

# ================================================================ 6 · Azure TTS (con reintentos y límite de velocidad)
_last = [0.]
def http(method, url, **kw):
    import requests
    kw.setdefault('timeout', 60); kw.setdefault('headers', {}); kw['headers'].setdefault('User-Agent', 'neon-tts/1.0')
    kw['headers']['Ocp-Apim-Subscription-Key'] = key()
    return requests.request(method, url, **kw)

def synthesize(ssml, retries=4):
    for att in range(retries):
        wait = MIN_INTERVAL - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        try:
            r = http('POST', tts_url(), data=ssml.encode('utf-8'), headers={'Content-Type': 'application/ssml+xml', 'X-Microsoft-OutputFormat': OUTPUT_FORMAT})
            if r.status_code == 200 and len(r.content) > 1000: return r.content
            err = f'HTTP {r.status_code}: {r.text[:200]}'
            if r.status_code in (400, 401, 403): raise RuntimeError(err)            # no tiene caso reintentar
        except RuntimeError: raise
        except Exception as e: err = str(e)
        time.sleep(2 ** (att + 1))                                                    # 2, 4, 8, 16 s
    raise RuntimeError(f'falló después de {retries} intentos: {err}')

# ================================================================ 8 · FFmpeg: normalización, filtros y medición real
FX = {None: '', 'telefono': ',highpass=f=300,lowpass=f=3400,acrusher=bits=12:mix=0.15',
      'detras_de_puerta': ',lowpass=f=1600,aecho=0.6:0.4:18|35:0.25|0.15'}
def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)
def ffprobe_duration(p):
    r = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)]); return float(r.stdout.strip())
def process_audio(raw, out, post_fx=None, target=-18.0):
    """normaliza a -18 LUFS (dos pasadas), pico -1.5 dBTP, 48 kHz mono; aplica el filtro del personaje."""
    pre = f'highpass=f=60{FX[post_fx]}'
    m = run(['ffmpeg', '-hide_banner', '-i', str(raw), '-af', f'{pre},loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'])
    js = json.loads(m.stderr[m.stderr.rindex('{'):m.stderr.rindex('}') + 1])
    ln = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    r = run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(raw), '-af', f'{pre},{ln}', '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(out)])
    if r.returncode: raise RuntimeError('ffmpeg: ' + r.stderr[-300:])

def qa(path, text, rate):
    """control de calidad automático (la aprobación final siempre es humana)."""
    flags = []
    dur = ffprobe_duration(path)                                   # 1) existe y se puede decodificar
    st = run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', 'astats=metadata=0,silencedetect=n=-45dB:d=1.2', '-f', 'null', '-']).stderr
    peak = max([float(x) for x in re.findall(r'Peak level dB: (-?[\d.]+|-inf)', st) if x != '-inf'] or [-99])
    sil = [float(x) for x in re.findall(r'silence_duration: ([\d.]+)', st)]
    lufs = json.loads((lambda e: e[e.rindex('{'):e.rindex('}') + 1])(run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', 'loudnorm=print_format=json', '-f', 'null', '-']).stderr))['input_i']
    expected = len(text) / (14.5 * (1 + pct(rate) / 100))         # ~14.5 caracteres/s en español a velocidad normal
    ratio = dur / max(expected, .3)
    if dur < .3: flags.append('demasiado_corto')
    if ratio < .55: flags.append('posibles_palabras_omitidas')
    if ratio > 1.9: flags.append('demasiado_largo_o_ruido')
    if peak > -1.0: flags.append('posible_saturacion')
    if any(s > 1.6 for s in sil): flags.append('silencio_interno_largo')
    return {'duration': round(dur, 3), 'peak_db': peak, 'lufs': float(lufs), 'duration_vs_expected': round(ratio, 2), 'flags': flags}

def stt_check(path, text):
    """transcribe el clip con Azure STT (nivel gratuito: 5 h/mes) y compara con el texto: detecta palabras omitidas o cambiadas."""
    tmp = Path(path).with_suffix('.16k.wav')
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(path), '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', str(tmp)])
    r = http('POST', stt_url(), data=tmp.read_bytes(), headers={'Content-Type': 'audio/wav; codecs=audio/pcm; samplerate=16000'}); tmp.unlink()
    heard = r.json().get('DisplayText', '') if r.status_code == 200 else ''
    w = lambda s: re.findall(r'\w+', norm(s))
    a, b = w(text), w(heard)
    # distancia de edición por palabras (WER)
    D = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, D[0] = D[0], i
        for j in range(1, len(b) + 1): prev, D[j] = D[j], min(D[j] + 1, D[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
    return {'transcript': heard, 'wer': round(D[len(b)] / max(1, len(a)), 3)}

# ================================================================ 9-12 · generación por lotes, manifiesto e idempotencia
def generate(script_path, out_dir, mode, only, use_stt):
    script = load_json(script_path); out = Path(out_dir); (out / 'raw').mkdir(parents=True, exist_ok=True)
    mpath = out / f"{script['episode_id']}_manifest.json"
    old = {c['clip_id']: c for c in (load_json(mpath)['clips'] if mpath.exists() else [])}
    clips, errors = plan(script, mode, only)
    if errors: print('ERRORES DE VALIDACIÓN:\n  ' + '\n  '.join(errors)); sys.exit(1)
    rows = dict(old)
    for c in clips:
        prev = old.get(c['clip_id']); take = prev['take'] if prev else 1
        rejected = prev and prev.get('generation_status') == 'rejected'
        if prev and not rejected and prev.get('content_hash') == c['content_hash'] and Path(out / prev['output_file']).exists():
            print(f"= {c['clip_id']}  sin cambios, no se regenera"); continue                     # 12) evita duplicados
        if rejected or (only and prev): take += 1
        name = c['clip_id'] + (f'_T{take:02d}' if take > 1 else '') + '.wav'; c.update(take=take, output_file=name)
        raw = out / 'raw' / (c['content_hash'] + '.wav')
        try:
            if not raw.exists() or rejected: raw.write_bytes(synthesize(c['ssml']))                  # 6) TTS (11: reintentos)
            process_audio(raw, out / name, c['post_fx'])                                            # 8) normalización
            q = qa(out / name, c['text'], c['speaking_rate'])                                       # duración REAL medida
            if use_stt: q.update(stt_check(out / name, c['text'])); q['flags'] += ['transcripcion_no_coincide'] if q['wer'] > .15 else []
            c.update(duration=q['duration'], qa=q, generation_status='needs_review' if q['flags'] else 'generated', post_version=POST_VERSION)
            print(f"+ {name}  {q['duration']:.2f}s  {c['interpretation']}{' ' + c['style'] if c['style'] else ''}  {', '.join(q['flags']) or 'ok'}")
        except Exception as e:
            c.update(duration=None, generation_status='failed', error=str(e)[:300]); print(f"! {c['clip_id']}  FALLÓ: {e}")
        rows[c['clip_id']] = {k: v for k, v in c.items() if k != 'ssml'} | {'ssml_sha': c['content_hash']}
    manifest = {'episode_id': script['episode_id'], 'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'post_version': POST_VERSION,
                'clips': sorted(rows.values(), key=lambda r: r['sequence'])}
    save_json(mpath, manifest)
    st = {}
    for r in manifest['clips']: st[r['generation_status']] = st.get(r['generation_status'], 0) + 1
    print('manifiesto:', mpath, st)

def assemble(manifest_path, out):
    """pista continua de revisión: todos los clips en orden con sus pausas previas y posteriores."""
    m = load_json(manifest_path); base = Path(manifest_path).parent; parts = []
    for c in m['clips']:
        if c.get('generation_status') in ('failed', 'rejected'): continue
        parts += [f"anullsrc=r=48000:cl=mono:d={c['pause_before_ms'] / 1000}", str(base / c['output_file']), f"anullsrc=r=48000:cl=mono:d={c['pause_after_ms'] / 1000}"]
    cmd = ['ffmpeg', '-y', '-loglevel', 'error']; n = 0; labels = ''
    for p in parts:
        if p.startswith('anullsrc'): cmd += ['-f', 'lavfi', '-i', p]
        else: cmd += ['-i', p]
        labels += f'[{n}:a]'; n += 1
    cmd += ['-filter_complex', f'{labels}concat=n={n}:v=0:a=1[a]', '-map', '[a]', '-c:a', 'libmp3lame', '-b:a', '192k', str(out)]
    r = run(cmd)
    if r.returncode: raise RuntimeError(r.stderr[-400:])
    print(out, f'{ffprobe_duration(out):.1f}s')

# ================================================================ voces reales y validación del registro
def cmd_voices():
    r = http('GET', voices_url())
    if r.status_code != 200: sys.exit(f'HTTP {r.status_code}: {r.text[:200]}')
    vs = [{k: v.get(k) for k in ('ShortName', 'DisplayName', 'Gender', 'Locale', 'VoiceType', 'StyleList', 'RolePlayList', 'VoiceTag', 'Status')}
          for v in r.json() if v.get('Locale') == 'es-MX']
    save_json(VOICES_CACHE, vs); print(len(vs), 'voces es-MX guardadas en', VOICES_CACHE)
    for v in vs: print(f"  {v['ShortName']:42s} {v['Gender']:7s} estilos: {', '.join(v.get('StyleList') or []) or '—'}")

def cmd_validate(write=True):
    reg = load_json(REGISTRY); vs = {v['ShortName']: v for v in load_json(VOICES_CACHE)}; ok = True
    for c in reg['characters']:
        v = vs.get(c['voice_id'])
        if v is None: print(f"✗ {c['character_id']}: la voz {c['voice_id']} no existe en es-MX"); ok = False; continue
        styles = v.get('StyleList') or []
        if c['approval_status'] == 'approved' and c.get('supported_styles') not in (None, styles):
            print(f"⚠ {c['character_id']}: los estilos de la voz aprobada cambiaron en Azure; revisar (no se modifica la voz)")
        c['supported_styles'] = styles
        unsupported = sorted({e for e in c['parametros_emocionales']['allowed_emotions'] if not any(s in styles for s in reg['emotion_presets'][e]['styles'])} - {'neutral'})
        print(f"✓ {c['character_id']:14s} {c['voice_id']:30s} {v['Gender']:7s} estilos reales: {', '.join(styles) or 'ninguno'}"
              + (f"\n    (solo prosodia para: {', '.join(unsupported)})" if unsupported else ''))
    if write: save_json(REGISTRY, reg)
    return ok

def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('voices'); sp.add_parser('validate')
    p = sp.add_parser('parse'); p.add_argument('file'); p.add_argument('--episode', default='E001')
    p = sp.add_parser('plan'); p.add_argument('script'); p.add_argument('--mode', default='production')
    p = sp.add_parser('generate'); p.add_argument('script'); p.add_argument('--out', default='output'); p.add_argument('--mode', default='production')
    p.add_argument('--only', nargs='*'); p.add_argument('--stt', action='store_true')
    p = sp.add_parser('assemble'); p.add_argument('manifest'); p.add_argument('--out', default='revision.mp3')
    p = sp.add_parser('casting'); p.add_argument('--character', required=True); p.add_argument('--line', required=True); p.add_argument('--emotion'); p.add_argument('--out', default='casting')
    a = ap.parse_args()
    if a.cmd == 'voices': cmd_voices()
    elif a.cmd == 'validate': sys.exit(0 if cmd_validate() else 1)
    elif a.cmd == 'parse': print(json.dumps(parse_text(Path(a.file).read_text(encoding='utf-8'), a.episode), ensure_ascii=False, indent=2))
    elif a.cmd == 'plan':
        clips, errors = plan(load_json(a.script), a.mode)
        for c in clips: print(f"{c['clip_id']:28s} {c['voice_id']:24s} {c['emotion']:16s} {c['interpretation']:13s} rate {c['speaking_rate']} pitch {c['pitch']}  «{c['text'][:50]}»")
        for e in errors: print('ERROR', e)
        print(f"{len(clips)} clips · {sum(len(c['ssml']) for c in clips)} caracteres SSML facturables (aprox.)")
    elif a.cmd == 'generate': generate(a.script, a.out, a.mode, a.only, a.stt)
    elif a.cmd == 'assemble': assemble(a.manifest, a.out)
    elif a.cmd == 'casting':
        reg = load_json(REGISTRY); ch = next(c for c in reg['characters'] if c['character_id'] == a.character); Path(a.out).mkdir(exist_ok=True)
        for vid in ch['casting_candidates']:
            cache = {v['ShortName']: v for v in load_json(VOICES_CACHE)} if VOICES_CACHE.exists() else {}
            c2 = dict(ch, voice_id=vid, supported_styles=(cache.get(vid) or {}).get('StyleList') or []); d = resolve_line({'emotion': a.emotion} if a.emotion else {}, c2, reg['emotion_presets'])
            raw = Path(a.out) / f'{a.character}_{vid}_raw.wav'; raw.write_bytes(synthesize(build_ssml(a.line, c2, d)))
            process_audio(raw, Path(a.out) / f'{a.character}_{vid}.wav', ch.get('post_fx')); raw.unlink(); print('✓', vid)

if __name__ == '__main__': main()
