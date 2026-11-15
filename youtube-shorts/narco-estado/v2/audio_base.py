# ---------------------------------------------------------------- audio
SR = 44100
VOZ = '/mnt/user-data/uploads/ElevenLabs_2026-11-10T00_49_33_Brian_C__-_Professional_Latin_Narrator_eleven_v4.mp3'
def synth_audio(path):
    N = DUR * SR; mus = np.zeros(N + SR); fx = np.zeros(N + SR); ar = np.random.RandomState(5)
    def T(d): return np.arange(int(d * SR)) / SR
    def put(buf, t, sig, v=1.):
        i = int(t * SR)
        if i < 0 or i >= len(buf): return
        n = min(len(sig), len(buf) - i); buf[i:i + n] += sig[:n] * v
    def lpf(x, fc, o=2):
        b, a = butter(o, fc / (SR / 2)); return lfilter(b, a, x)
    def hpf(x, fc, o=2):
        b, a = butter(o, fc / (SR / 2), 'high'); return lfilter(b, a, x)
    def mf(m): return 440 * 2 ** ((m - 69) / 12.)
    def ad(n, a, r):
        e = np.ones(n); na = min(n, max(1, int(a * SR))); nr = min(n, max(1, int(r * SR)))
        e[:na] *= np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
    def saw(f, d):
        t = T(d); return sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 9)) * .5
    def sweep(f): return np.sin(2 * np.pi * np.cumsum(f) / SR)
    def noise(n): return ar.uniform(-1, 1, n)
    def kick():
        t = T(.28); return sweep(110 * np.exp(-t * 28) + 42) * np.exp(-t * 13)
    def hat():
        t = T(.05); return hpf(noise(len(t)), 7000) * np.exp(-t * 90)
    def snare():
        t = T(.18); return (hpf(noise(len(t)), 1500) * .7 + np.sin(2 * np.pi * 190 * t) * .4) * np.exp(-t * 22)
    PROG = {'tension': [(45, 'm'), (45, 'm'), (41, 'M'), (40, 'M')], 'epico': [(38, 'm'), (34, 'M'), (41, 'M'), (36, 'M')],
            'misterio': [(40, 'm'), (36, 'M'), (45, 'm'), (35, 'M')], 'esperanza': [(36, 'M'), (43, 'M'), (45, 'm'), (41, 'M')]}
    beat = 60 / 92.
    secs = [(0, 'tension', 1), (10.3, 'tension', 2), (23.7, 'epico', 2), (37.2, 'misterio', 2), (48.7, 'esperanza', 1)]
    for si, (t0, sty, inten) in enumerate(secs):
        t1 = secs[si + 1][0] if si + 1 < len(secs) else DUR; bar = 0; tb = t0
        while tb < t1 - .05:
            root, q = PROG[sty][bar % 4]; third = 3 if q == 'm' else 4; dur = min(4 * beat, t1 - tb)
            for m in (root + 12, root + 12 + third, root + 19, root + 24):
                n = int((dur + .3) * SR)
                put(mus, tb, lpf(saw(mf(m), dur + .3) + saw(mf(m) * 1.004, dur + .3), 1100) * ad(n, .25, .35), .05)
            nb = 8 if inten >= 1 else 1
            for i in range(nb):
                tt = tb + i * 4 * beat / nb
                if tt >= t1: break
                t = T(4 * beat / nb * .95); f = mf(root)
                put(mus, tt, (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * ad(len(t), .01, .08), .2)
            if inten >= 1:
                for b in range(4):
                    tt = tb + b * beat
                    if tt >= t1: break
                    if b % 2 == 0 or sty == 'epico': put(mus, tt, kick(), .55)
                    put(mus, tt, hat(), .10); put(mus, tt + beat / 2, hat(), .07)
                    if inten >= 2 and b % 2 == 1: put(mus, tt, snare(), .22)
            if inten >= 2:
                notes = [root + 24, root + 24 + third, root + 31, root + 36, root + 31, root + 24 + third, root + 24, root + 31]
                for i, m in enumerate(notes):
                    tt = tb + i * beat / 2
                    if tt >= t1: break
                    t = T(.3); put(mus, tt, (np.sin(2 * np.pi * mf(m) * t) + .3 * np.sin(6 * np.pi * mf(m) * t)) * np.exp(-t * 9), .07)
            tb += 4 * beat; bar += 1
    def ding(f0=1320):
        t = T(1.1); return (np.sin(2 * np.pi * f0 * t) + .5 * np.sin(2 * np.pi * f0 * 2.01 * t) + .25 * np.sin(2 * np.pi * f0 * 3.02 * t)) * np.exp(-t * 4.5) * ad(len(t), .003, .05)
    def mk(name, dur):
        if name == 'boom':
            t = T(1.6); return sweep(80 * np.exp(-t * 3) + 32) * np.exp(-t * 2.6) + lpf(noise(len(t)), 300) * np.exp(-t * 5) * .8
        if name == 'impacto':
            t = T(.7); return sweep(150 * np.exp(-t * 9) + 45) * np.exp(-t * 6) + lpf(noise(len(t)), 1800) * np.exp(-t * 25) * .6
        if name == 'whoosh':
            t = T(.7); return hpf(lpf(noise(len(t)), 2600), 350) * np.sin(np.pi * t / .7) ** 2 * 1.6
        if name == 'alarma':
            t = T(dur or 1.5); f = np.where((t * 4).astype(int) % 2 == 0, 660., 880.); return lpf(np.sign(sweep(f)), 2500) * ad(len(t), .02, .1)
        if name == 'beep':
            t = T(.12); return np.sin(2 * np.pi * 1250 * t) * ad(len(t), .005, .03)
        if name == 'glitch':
            t = T(.2); return noise(len(t)) * ((t * 40).astype(int) % 2) * .6
        if name == 'riser':
            d = dur or 2; t = T(d); return (sweep(200 + 1200 * (t / d) ** 2) * .5 + hpf(noise(len(t)), 2000) * .4) * (t / d) ** 2 * ad(len(t), .01, .05)
        if name == 'ding': return ding()
        if name == 'caida':
            t = T(.8); return sweep(900 * np.exp(-t * 2.6) + 120) * ad(len(t), .01, .25) * .8
        if name == 'tecleo':
            d = dur or 1; out = np.zeros(int(d * SR)); tt = 0.
            while tt < d - .05:
                n = int(.02 * SR); c = hpf(noise(n), 2500) * np.exp(-np.arange(n) / SR * 220); i = int(tt * SR); m = min(n, len(out) - i)
                out[i:i + m] += c[:m]; tt += ar.uniform(.06, .14)
            return out
        if name == 'latido':
            out = np.zeros(int(.7 * SR))
            for o in (0, .26):
                t = T(.3); sgn = np.sin(2 * np.pi * 58 * t) * np.exp(-t * 14); i = int(o * SR); out[i:i + len(sgn)] += sgn
            return out
        if name == 'viento':
            t = T(dur or 5); return hpf(lpf(noise(len(t)), 500), 120) * (.6 + .4 * np.sin(2 * np.pi * .23 * t)) * ad(len(t), 1.5, 1.5) * 3
        if name == 'dinero':
            out = np.zeros(int(.9 * SR)); a = ding(2100)[:int(.5 * SR)]; b = ding(2794)[:int(.7 * SR)]
            out[:len(a)] += a; i = int(.12 * SR); out[i:i + len(b)] += b; return out
        if name == 'pop':
            t = T(.09); return sweep(420 + 700 * t / .09) * ad(len(t), .004, .04)
    EF = [[0, 'boom', .9], [.4, 'alarma', .08, 2.6], [2.3, 'beep', .15], [7.9, 'impacto', .7], [9.85, 'whoosh', .5],
          [10.6, 'glitch', .12], [11.4, 'tecleo', .12, 1.2], [18.65, 'impacto', .65], [18.8, 'alarma', .06, 1.4], [16.2, 'latido', .4], [23.25, 'whoosh', .5],
          [24.0, 'viento', .1, 13], [24.9, 'impacto', .8], [32.75, 'impacto', .6], [35.7, 'caida', .3], [36.75, 'whoosh', .5],
          [37.6, 'tecleo', .12, 1.5], [38.3, 'beep', .15], [41.2, 'caida', .3], [42.4, 'dinero', .25], [45.8, 'caida', .25], [48.25, 'whoosh', .5],
          [48.8, 'riser', .2, 2], [53.2, 'ding', .25], [57.9, 'ding', .3]]
    for e in EF: put(fx, e[0], mk(e[1], e[3] if len(e) > 3 else None), e[2])
    for em in EMOJIS: put(fx, em[0], mk('pop', None), .12)
    mus = mus[:N]; fx = fx[:N]
    mus = mus / np.abs(mus).max() * .40
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', VOZ, '-ac', '1', '-ar', str(SR), '/home/claude/voz44.wav'], check=True)
    _, v = wavfile.read('/home/claude/voz44.wav'); v = v.astype(np.float64) / 32768; vv = np.zeros(N); vv[:min(N, len(v))] = v[:N]
    vv = vv / (np.abs(vv).max() + 1e-9) * .95
    env = np.convolve(np.abs(vv), np.ones(4410) / 4410, 'same'); env = np.clip(env / (env.max() * .25), 0, 1)
    env = lfilter([1 / 8000.], [1, -(1 - 1 / 8000.)], env); env = np.clip(env * 3, 0, 1)
    duck = 1 - .55 * env
    out = np.tanh((mus * .75 * duck + fx * .6 * (1 - .35 * env)) * 1.1) * .8 + vv * .92
    out = out / max(1., np.abs(out).max() / .98)
    fade = int(1.2 * SR); out[-fade:] *= np.linspace(1, 0, fade)
    st = np.stack([out, out], 1); wavfile.write(path, SR, (st * 32767).astype(np.int16))
