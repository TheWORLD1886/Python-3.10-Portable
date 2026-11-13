#!/usr/bin/env python3
# Voz gratuita (Kokoro, Apache-2.0) más natural: velocidad normal, una frase por síntesis
# (la entonación se calcula frase a frase) y pausas naturales entre frases.
import re, json, sys, numpy as np, soundfile as sf
from kokoro import KPipeline
VOICE = sys.argv[1] if len(sys.argv) > 1 else 'em_alex'; SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 1.05
FIX = [('θ', 's'), ('ʎ', 'ʝ'), ('tɾˈump', 'tɾˈamp'), ('wasˈiŋɡton', 'wˈaʃinton')]
p = KPipeline(lang_code='e'); pack = p.load_voice(VOICE)
txt = open('guion_voz.txt').read().replace('\n', ' ')
parts = re.split(r'<break time="([\d.]+)s" />', txt)
SR = 24000; audio = [np.zeros(int(.25 * SR))]; t = .25; words = []
def fade(a, n=240):
    a = a.copy(); r = np.linspace(0, 1, min(n, len(a) // 2)); a[:len(r)] *= r; a[-len(r):] *= r[::-1]; return a
for i in range(0, len(parts), 2):
    chunk = parts[i].strip(); pause = float(parts[i + 1]) if i + 1 < len(parts) else 0
    # una síntesis por frase: corta en . ? ! … (las comas quedan dentro para que la entonación fluya)
    for sent in [x for x in re.split(r'(?<=[.?!…])\s+', chunk) if x.strip()]:
        ps = ' '.join(r[1] for r in p(sent, voice=VOICE))
        for a, b in FIX: ps = ps.replace(a, b)
        out = KPipeline.infer(p.model, ps, pack, SPEED)
        a = out.audio.cpu().numpy() if hasattr(out, 'audio') else np.asarray(out)
        nz = np.where(np.abs(a) > .008)[0]; a = a[max(0, nz[0] - 900):nz[-1] + 2400] if len(nz) else a
        a = fade(a); dur = len(a) / SR; ws = sent.split(); tot = sum(len(w) + 1 for w in ws); c = 0
        for w in ws:
            s0 = t + .04 + (dur - .14) * c / tot; c += len(w) + 1; words.append([w, round(s0, 3), round(t + .04 + (dur - .14) * (c - 1) / tot, 3)])
        audio.append(a); t += dur
        gap = .18 if sent[-1] in '.?!…' else .08; audio.append(np.zeros(int(gap * SR))); t += gap
    if pause: audio.append(np.zeros(int(pause * .55 * SR))); t += pause * .55
sf.write('voz_natural.wav', np.concatenate(audio), SR)
json.dump(words, open('words_natural.json', 'w'), ensure_ascii=False)
print('dur', round(t, 2), 'palabras', len(words))
