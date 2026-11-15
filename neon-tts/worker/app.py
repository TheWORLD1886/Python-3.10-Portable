"""
NEON TTS · audio-worker (Google Cloud Run). FFmpeg en la nube, porque n8n Cloud no puede ejecutar comandos.
POST /process   multipart: audio (WAV de Azure), text, speaking_rate, post_fx  ->  JSON con el audio normalizado,
                la duración REAL medida, el control de calidad y una copia de 16 kHz para verificar con STT.
POST /assemble  JSON {clips:[{audio_b64, pause_before_ms, pause_after_ms}]} -> MP3 de revisión de la escena.
Seguridad: cabecera X-Worker-Token (secreto guardado en Secret Manager y en el gestor de credenciales de n8n).
Escala a cero: sin solicitudes no hay instancias encendidas ni costo.
"""
import base64, hmac, os, subprocess, tempfile
from pathlib import Path
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
import neon_tts as N

app = FastAPI(title='neon-tts audio-worker')
TOKEN = os.environ.get('WORKER_TOKEN', '')

def auth(tok):
    if not TOKEN or not hmac.compare_digest(tok or '', TOKEN): raise HTTPException(401, 'token inválido')

@app.get('/health')
def health(): return {'ok': True, 'post_version': N.POST_VERSION}

@app.post('/process')
async def process(audio: UploadFile = File(...), text: str = Form(...), speaking_rate: str = Form('0%'), post_fx: str = Form(''),
                  x_worker_token: str = Header(None)):
    auth(x_worker_token)
    with tempfile.TemporaryDirectory() as d:
        raw, out, s16 = Path(d) / 'raw.wav', Path(d) / 'out.wav', Path(d) / 's16.wav'
        raw.write_bytes(await audio.read())
        try:
            N.process_audio(raw, out, post_fx or None)
            q = N.qa(out, text, speaking_rate)
        except Exception as e: raise HTTPException(422, f'audio inválido: {e}')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(out), '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', str(s16)], check=True)
        return {'duration': q['duration'], 'qa': q, 'post_version': N.POST_VERSION,
                'audio_b64': base64.b64encode(out.read_bytes()).decode(), 'stt16k_b64': base64.b64encode(s16.read_bytes()).decode()}

@app.post('/wer')
def wer(body: dict, x_worker_token: str = Header(None)):
    """compara el texto original con la transcripción de Azure STT (palabras omitidas o cambiadas)."""
    auth(x_worker_token); import re
    w = lambda s: re.findall(r'\w+', N.norm(s)); a, b = w(body.get('text', '')), w(body.get('transcript', ''))
    D = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, D[0] = D[0], i
        for j in range(1, len(b) + 1): prev, D[j] = D[j], min(D[j] + 1, D[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
    return {'wer': round(D[len(b)] / max(1, len(a)), 3)}

@app.post('/assemble')
def assemble(body: dict, x_worker_token: str = Header(None)):
    auth(x_worker_token)
    with tempfile.TemporaryDirectory() as d:
        clips = []
        for i, c in enumerate(body['clips']):
            p = Path(d) / f'{i:04d}.wav'; p.write_bytes(base64.b64decode(c['audio_b64']))
            clips.append({'output_file': p.name, 'pause_before_ms': c.get('pause_before_ms', 0), 'pause_after_ms': c.get('pause_after_ms', 300), 'generation_status': 'generated'})
        N.save_json(Path(d) / 'm.json', {'clips': clips}); out = Path(d) / 'review.mp3'
        N.assemble(Path(d) / 'm.json', out)
        return {'audio_b64': base64.b64encode(out.read_bytes()).decode(), 'duration': N.ffprobe_duration(out)}
