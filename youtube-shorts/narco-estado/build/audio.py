import numpy as np, json, subprocess, wave
SR = 44100; T = 60.0; N = int(SR * T); t = np.arange(N) / SR; rng = np.random.default_rng(3)
tl = json.load(open('timeline.json')); starts = [s['start'] for s in tl['scenes']]; ends = [s['end'] for s in tl['scenes']]
def env(a, b, fade=.4):  # 0..1 window between a and b
    return np.clip((t - a) / fade, 0, 1) * np.clip((b - t) / fade, 0, 1)
def lp(x, k):  # one-pole lowpass
    y = np.empty_like(x); acc = 0.
    a = k
    from scipy.signal import lfilter
    return lfilter([a], [1, a - 1], x)
try:
    import scipy  # noqa
except ImportError:
    subprocess.run(['pip', 'install', '-q', 'scipy'])
from scipy.signal import lfilter, butter
def band(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
def low(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
noise = rng.standard_normal(N)
mix = np.zeros(N)
# dark cinematic drone (Dm): low strings-like pad with slow swell
for f, g in [(36.7, .5), (73.4, .35), (110, .18), (146.8, .12), (174.6, .08)]:
    mix += g * np.sin(2 * np.pi * f * t + .3 * np.sin(2 * np.pi * .07 * t)) * (.6 + .4 * np.sin(2 * np.pi * .05 * t + f))
mix += .25 * low(noise, 120)
# heartbeat pulse that intensifies
beat = np.zeros(N); bpm = 70
for k in np.arange(0, T, 60 / bpm):
    for d, a in [(0, 1), (.18, .6)]:
        i = int((k + d) * SR); L = int(.25 * SR); seg = np.arange(min(L, N - i)) / SR
        beat[i:i + len(seg)] += a * np.sin(2 * np.pi * 50 * seg) * np.exp(-seg * 18)
mix += beat * (.4 + .6 * t / T)
# impacts at every cut
for s in [0.02] + starts[1:]:
    i = int(s * SR); L = int(2.2 * SR); seg = np.arange(min(L, N - i)) / SR
    boom = np.sin(2 * np.pi * (70 * np.exp(-seg * 2) + 28) * seg) * np.exp(-seg * 2.2) * 2.2
    boom += low(noise[i:i + len(seg)], 900) * np.exp(-seg * 6) * 1.5
    mix[i:i + len(seg)] += boom
    j = max(0, i - int(.8 * SR)); w = np.arange(i - j) / SR   # reverse whoosh into the cut
    mix[j:i] += band(noise[j:i], 300, 3000) * (w / .8) ** 3 * .6
sfx = np.zeros(N)
# scene 2: stamp thuds every 1.6 s (stamp hits at phase .35)
for k in np.arange(starts[1] + .56, ends[1], 1.6):
    i = int(k * SR); L = int(.3 * SR); seg = np.arange(L) / SR
    sfx[i:i + L] += (np.sin(2 * np.pi * 95 * seg) * 1.4 + low(noise[i:i + L], 2500) * .8) * np.exp(-seg * 25)
# scene 3: distant helicopter — soft low "whump" pulses (no harsh square gating / no turbine whine)
ph = (t * 5.2) % 1; puls = np.exp(-ph * 9) * (1 - np.exp(-ph * 60))
rotor = low(low(noise, 160) * puls, 220) * 2.2
sw = np.clip((t - starts[2]) / (ends[2] - starts[2]), 0, 1); passby = np.sin(np.pi * sw) ** 2
sfx += rotor * env(starts[2], ends[2], 1.5) * (.25 + .5 * passby)
# scene 4: soft sirens + low fire rumble with sparse, gentle crackles (no broadband hiss)
siren = np.sin(2 * np.pi * np.cumsum(750 + 260 * np.sin(2 * np.pi * .45 * t)) / SR) * .12
siren = low(siren, 2500)
rumble = low(low(noise, 180), 180) * 1.6
clicks = np.zeros(N); idx = np.where(rng.random(N) < .00012)[0]
for i in idx:
    L = min(int(.012 * SR), N - i); clicks[i:i + L] += rng.standard_normal(L) * np.exp(-np.arange(L) / (SR * .002)) * (.3 + rng.random() * .4)
crackle = low(clicks, 3500) * .5
sfx += (siren + rumble + crackle) * env(starts[3], ends[3], .8)
for k in [starts[3] + 2.5, starts[3] + 6.8, starts[3] + 10.2]:
    i = int(k * SR); L = int(1.8 * SR); seg = np.arange(L) / SR; sfx[i:i + L] += low(noise[i:i + L], 200) * np.exp(-seg * 3) * 1.4
# scene 5: low choir-ish swell + final hit
sfx += .15 * np.sin(2 * np.pi * 220 * t) * np.sin(2 * np.pi * 293.7 * t * .5) * env(starts[4], 60, 2)
mix = mix * .32 + sfx * .35
mix *= np.clip((T - t) / 1.5, 0, 1)
mix = np.tanh(mix * 1.2) * .5
with wave.open('bed.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
# voice track: each scene's VO at its start, sped up 5%
inputs, filt = [], []
for i in range(5):
    inputs += ['-i', f'vo{i + 1}.mp3']; filt.append(f'[{i}:a]atempo=1.05,adelay={int(starts[i] * 1000)}|{int(starts[i] * 1000)}[v{i}]')
filt.append(''.join(f'[v{i}]' for i in range(5)) + 'amix=inputs=5:normalize=0,apad,atrim=0:60[vo]')
inputs += ['-i', 'bed.wav']
filt.append('[vo]asplit[vo1][vo2];[5:a][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck];[duck][vo2]amix=inputs=2:normalize=0:weights=1 1.6,loudnorm=I=-14:TP=-1.5:LRA=9[out]')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(filt), '-map', '[out]', '-ar', '48000', '-ac', '2', '-c:a', 'aac', '-b:a', '192k', 'audio.m4a'], check=True)
print('audio ok')
