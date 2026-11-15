#!/usr/bin/env python3
# Voz con ElevenLabs (Brian C.) + tiempos por palabra. La clave la pone el proxy del entorno.
import json, base64, re, subprocess
txt = open('guion_voz.txt').read().replace('\n\n', ' ').replace('\n', ' ')
txt = re.sub(r'<break time="([\d.]+)s" />', lambda m: f'<break time="{float(m.group(1)) * .45:.2f}s" />', txt)   # pausas más cortas
body = {'text': txt, 'model_id': 'eleven_multilingual_v2',
        'voice_settings': {'stability': .45, 'similarity_boost': .75, 'style': .25, 'use_speaker_boost': True, 'speed': 1.2}}
open('/tmp/claude-0/-home-user-Python-3-10-Portable/e54c0773-2bc1-5cb2-91d5-06f8a723d723/scratchpad/el_body.json', 'w').write(json.dumps(body))
raw = subprocess.run(['curl', '-sS', '-f', '-X', 'POST', 'https://api.elevenlabs.io/v1/text-to-speech/uCQe5kObQIjtylU0HL3m/with-timestamps?output_format=mp3_44100_128',
                      '-H', 'xi-api-key: proxy-injected', '-H', 'Content-Type: application/json',
                      '--data-binary', '@/tmp/claude-0/-home-user-Python-3-10-Portable/e54c0773-2bc1-5cb2-91d5-06f8a723d723/scratchpad/el_body.json'], capture_output=True, check=True).stdout
r = json.loads(raw)
open('voz_elevenlabs.mp3', 'wb').write(base64.b64decode(r['audio_base64']))
al = r['alignment']; ch, st, en = al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']
words, cur, tag = [], None, False
for c, a, b in zip(ch, st, en):
    if c == '<': tag = True
    if tag:
        if c == '>': tag = False
        continue
    if c.isspace():
        if cur: words.append(cur); cur = None
        continue
    if cur is None: cur = [c, a, b]
    else: cur[0] += c; cur[2] = b
if cur: words.append(cur)
words = [[w, round(a, 3), round(b, 3)] for w, a, b in words]
json.dump(words, open('words_elevenlabs.json', 'w'), ensure_ascii=False)
print('palabras', len(words), 'fin', words[-1])
