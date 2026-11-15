#!/usr/bin/env python3
# Regraba frases sueltas cuya palabra «Envidia» quedó ambigua, elige la toma que Whisper entiende como «envidia»
# (en contexto y aislada) y la empalma en la narración, desplazando los tiempos por palabra.
import json, base64, subprocess, re, sys, numpy as np
from voz_prueba import para_voz
SP = '/tmp/claude-0/-home-user-Python-3-10-Portable/e54c0773-2bc1-5cb2-91d5-06f8a723d723/scratchpad'
FRASES_TODAS = [('Megaspeed', 'Megaspeed también era un importante comprador de chips NVIDIA.', 35.),
          ('Legisladores', 'Legisladores exigieron explicaciones a Jensen y a NVIDIA.', 120.),
          ('¿Crees', '¿Crees que China intentó utilizar una relación personal para acercarse a los secretos de NVIDIA?', 150.),
          ('El', 'El protagonista es Jensen Huang, fundador y hasta hace poco CEO de NVIDIA, la compañía cuyos chips impulsan gran parte de la revolución mundial de la inteligencia artificial.', 15.)]
FRASES = [f for f in FRASES_TODAS if f[0] in sys.argv[1:]] or FRASES_TODAS
from faster_whisper import WhisperModel
M = WhisperModel('small', device='cpu', compute_type='int8')
def stt(path, a=None, b=None, pad=False):
    cmd = ['ffmpeg', '-loglevel', 'error'] + (['-ss', str(a), '-to', str(b)] if a is not None else []) + ['-i', path, '-ac', '1', '-ar', '16000', '-f', 's16le', '-']
    au = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    if pad: au = np.concatenate([np.zeros(8000, np.float32), au, np.zeros(8000, np.float32)])
    return ' '.join(s.text.strip() for s in M.transcribe(au, language='es', beam_size=5, condition_on_previous_text=False)[0])
def tts(text, out):
    body = {'text': para_voz(text), 'model_id': 'eleven_multilingual_v2',
            'voice_settings': {'stability': .45, 'similarity_boost': .75, 'style': .25, 'use_speaker_boost': True, 'speed': 1.2}}
    open(f'{SP}/rep.json', 'w').write(json.dumps(body))
    r = json.loads(subprocess.run(['curl', '-sS', '-f', '-X', 'POST', 'https://api.elevenlabs.io/v1/text-to-speech/uCQe5kObQIjtylU0HL3m/with-timestamps?output_format=mp3_44100_128',
                                   '-H', 'xi-api-key: proxy-injected', '-H', 'Content-Type: application/json', '--data-binary', f'@{SP}/rep.json'], capture_output=True, check=True).stdout)
    open(f'{SP}/raw.mp3', 'wb').write(base64.b64decode(r['audio_base64']))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{SP}/raw.mp3', '-filter:a', 'atempo=1.08', '-ar', '44100', '-ac', '1', out], check=True)
    al = r['alignment']; words, cur = [], None
    for c, a, b in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
        if c.isspace():
            if cur: words.append(cur); cur = None
            continue
        if cur is None: cur = [c, a / 1.08, b / 1.08]
        else: cur[0] += c; cur[2] = b / 1.08
    if cur: words.append(cur)
    json.dump(words, open(out + '.json', 'w'))
    return words
words = json.load(open('words.json'))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'voz.mp3', '-ar', '44100', '-ac', '1', f'{SP}/voz_full.wav'], check=True)
import wave
def rd(p):
    w = wave.open(p); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32), w.getframerate()
full, SR = rd(f'{SP}/voz_full.wav'); log = []
for key, frase, after in FRASES:
    i0 = next(i for i, x in enumerate(words) if x[1] >= after and x[0].startswith(key)); n = len(frase.split()); i1 = i0 + n - 1
    a, b = words[i0][1] - .05, words[i1][2] + .08
    best = None
    for intento in range(3):
        cand = f'{SP}/cand_{key}_{intento}.wav'
        import os
        ws = json.load(open(cand + '.json')) if os.path.exists(cand + '.json') else tts(frase, cand)
        ev = next(x for x in ws if 'envidia' in x[0].lower())
        ctx, iso, iso2 = stt(cand), stt(cand, ev[1] - .08, ev[2] + .12, pad=True), stt(cand, ev[1] - .15, ev[2] + .2, pad=True)
        ok = bool(re.search(r'\benvidia', iso, re.I)) and bool(re.search(r'\benvidia', iso2, re.I)) and not re.search(r'nvidia', (iso + iso2).replace('envidia', '').replace('Envidia', ''), re.I)   # en contexto Whisper tiende a escribir «Nvidia» por el modelo de lenguaje: se juzga la palabra aislada
        iso = iso + ' / ' + iso2
        log.append(dict(frase=frase, intento=intento, contexto=ctx, aislada=iso, ok=ok)); print(intento, 'OK ' if ok else 'MAL', '|', ctx, '|', iso, flush=True)
        if ok: best = (cand, ws); break
    if best is None: print('SIN TOMA LIMPIA para', key); sys.exit(1)
    seg, _ = rd(best[0]); ws = best[1]
    s0, e0 = max(0., ws[0][1] - .05), ws[-1][2] + .08                             # recorta la toma a sus palabras (nunca índice negativo)
    seg = seg[int(s0 * SR):int(e0 * SR)]
    fade = int(.01 * SR); seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
    ia, ib = int(a * SR), int(b * SR); delta = len(seg) / SR - (b - a)
    full = np.concatenate([full[:ia], seg, full[ib:]])
    neww = [[x[0], round(a + (x[1] - s0), 3), round(a + (x[2] - s0), 3)] for x in ws]
    words = words[:i0] + neww + [[x[0], round(x[1] + delta, 3), round(x[2] + delta, 3)] for x in words[i1 + 1:]]
    print('empalme', key, f'{a:.2f}-{b:.2f}', f'delta {delta:+.3f}s')
w = wave.open(f'{SP}/voz_rep.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.clip(full, -32768, 32767).astype(np.int16).tobytes()); w.close()
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{SP}/voz_rep.wav', '-c:a', 'libmp3lame', '-b:a', '192k', 'voz.mp3'], check=True)
json.dump(words, open('words.json', 'w'), ensure_ascii=False)
json.dump(log, open('voz_segmentos/regrabaciones.json', 'w'), ensure_ascii=False, indent=1)
print('ok', words[-1])
