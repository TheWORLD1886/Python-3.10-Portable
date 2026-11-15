#!/usr/bin/env python3
# Voz gratuita para el short de Trump y México. Voz gratuita (Kokoro, Apache-2.0) con pronunciación latinoamericana corregida.
import re, json, sys, numpy as np, soundfile as sf
from kokoro import KPipeline
VOICE = sys.argv[1] if len(sys.argv) > 1 else 'em_alex'; SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
FIX = [('θ', 's'), ('ʎ', 'ʝ'), ('ˌoʝiwoˈod', 'xˈoliwud'), ('lˈike', 'lˈajk'), ('tɾˈump', 'tɾˈamp'), ('wasˈiŋɡton', 'wˈaʃinton')]
p = KPipeline(lang_code='e'); pack = p.load_voice(VOICE)
txt = open('guion_voz.txt').read().replace('\n', ' ')
parts = re.split(r'<break time="([\d.]+)s" />', txt)          # texto, pausa, texto, pausa...
SR = 24000; audio = [np.zeros(int(.25 * SR))]; t = .25; words = []
for i in range(0, len(parts), 2):
    chunk = parts[i].strip(); pause = .5 * float(parts[i + 1]) if i + 1 < len(parts) else 0
    if chunk:
        ps = ' '.join(r[1] for r in p(chunk, voice=VOICE))
        for a, b in FIX: ps = ps.replace(a, b)
        out = KPipeline.infer(p.model, ps, pack, SPEED)
        a = out.audio.cpu().numpy() if hasattr(out, 'audio') else np.asarray(out)
        # recorta silencios del principio y final del trozo
        nz = np.where(np.abs(a) > .01)[0]; a = a[max(0, nz[0] - 600):nz[-1] + 1200] if len(nz) else a
        dur = len(a) / SR; ws = chunk.split(); tot = sum(len(w) + 1 for w in ws); c = 0
        for w in ws:
            s0 = t + dur * c / tot; c += len(w) + 1; words.append([w, round(s0, 3), round(t + dur * (c - 1) / tot, 3)])
        audio.append(a); t += dur
    if pause: audio.append(np.zeros(int(pause * SR))); t += pause
sf.write('voz.wav', np.concatenate(audio), SR)
json.dump(words, open('words.json', 'w'), ensure_ascii=False)
print('dur', round(t, 2), 'palabras', len(words))
