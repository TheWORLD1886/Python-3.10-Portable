#!/usr/bin/env python3
# Prueba de pronunciación: en el texto que va a ElevenLabs, «NVIDIA» se sustituye por «Envidia». En pantalla sigue diciendo NVIDIA.
import json, base64, re, subprocess, sys
def para_voz(txt):
    out = re.sub(r'\bNVIDIA\b', 'Envidia', txt, flags=re.IGNORECASE)
    assert not re.search(r'\bnvidia\b', out, re.IGNORECASE), 'quedó una NVIDIA sin corregir'
    return out
if __name__ == '__main__':
    txt = para_voz('El problema para NVIDIA es enorme. Jensen Huang, fundador y hasta hace poco CEO de NVIDIA. Megaspeed también era un importante comprador de chips NVIDIA.')
    print(txt)
    body = {'text': txt, 'model_id': 'eleven_multilingual_v2',
            'voice_settings': {'stability': .45, 'similarity_boost': .75, 'style': .25, 'use_speaker_boost': True, 'speed': 1.2}}
    p = '/tmp/claude-0/-home-user-Python-3-10-Portable/e54c0773-2bc1-5cb2-91d5-06f8a723d723/scratchpad/el_test.json'; open(p, 'w').write(json.dumps(body))
    raw = subprocess.run(['curl', '-sS', '-f', '-X', 'POST', 'https://api.elevenlabs.io/v1/text-to-speech/uCQe5kObQIjtylU0HL3m?output_format=mp3_44100_128',
                          '-H', 'xi-api-key: proxy-injected', '-H', 'Content-Type: application/json', '--data-binary', '@' + p], capture_output=True, check=True).stdout
    open('voz_segmentos/prueba_envidia_raw.mp3', 'wb').write(raw)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'voz_segmentos/prueba_envidia_raw.mp3', '-filter:a', 'atempo=1.08', '-b:a', '192k', 'voz_segmentos/prueba_pronunciacion_envidia.mp3'], check=True)
    print('ok')
