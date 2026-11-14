#!/usr/bin/env python3
# Verifica con Whisper (palabra aislada, dos ventanas) cada «Envidia» de voz.mp3 y regenera los bloques de voz por sección.
import json, subprocess, numpy as np, re
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
w = json.load(open('words.json')); res = []
def stt(a, b):
    au = np.frombuffer(subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(a), '-to', str(b), '-i', 'voz.mp3', '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    au = np.concatenate([np.zeros(8000, np.float32), au, np.zeros(8000, np.float32)])
    return ' '.join(s.text.strip() for s in m.transcribe(au, language='es', beam_size=5, condition_on_previous_text=False)[0])
for x in w:
    if 'envidia' not in x[0].lower(): continue
    i1, i2 = stt(x[1] - .08, x[2] + .12), stt(x[1] - .15, x[2] + .2)
    ok = bool(re.search(r'\benvidia', i1, re.I) and re.search(r'\benvidia', i2, re.I)) and not re.search(r'nvidia', re.sub(r'envidia', '', i1 + i2, flags=re.I), re.I)
    res.append(dict(t=x[1], aislada_1=i1, aislada_2=i2, ok=ok)); print(f'{x[1]:7.2f}', 'OK ' if ok else 'MAL', i1, '/', i2)
json.dump(res, open('voz_segmentos/verificacion_whisper.json', 'w'), ensure_ascii=False, indent=1)
secs = [('01_gancho', 'Una', 0), ('02_quien_es_ella', 'El', 15), ('03_como_lo_descubrieron', 'Según', 44), ('04_impacto', 'El', 82), ('05_gobierno', 'Washington', 112), ('06_giro_final', 'Y', 131), ('07_interaccion', 'Pero', 149)]
st = [next(x[1] for x in w if x[1] >= a and re.sub(r'[^\wáéíóúñ]', '', x[0].lower()).startswith(k.lower())) for _, k, a in secs] + [w[-1][2] + .4]
for i, (n, _, _) in enumerate(secs):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{max(0, st[i] - .15):.3f}', '-to', f'{st[i + 1] - .05:.3f}', '-i', 'voz.mp3', '-c:a', 'libmp3lame', '-b:a', '192k', f'voz_segmentos/{n}.mp3'], check=True)
print('TODAS OK' if all(r['ok'] for r in res) else 'HAY FALLOS', '· bloques', [round(x, 2) for x in st])
