#!/usr/bin/env python3
# Música y efectos del episodio 01 (sintetizados; sin voces todavía). La música evoluciona con la historia.
import numpy as np, subprocess, os, sys
SR = 48000; DUR = 93.0; N = int(DUR * SR) + SR
mus = np.zeros(N); fx = np.zeros(N); R = np.random.RandomState(7)
def T(d): return np.arange(int(d * SR)) / SR
def put(buf, t, sig, v=1.):
    i = int(t * SR); j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i] * v
def env(n, a, r): e = np.ones(n); ai = int(a * SR); ri = int(r * SR); e[:ai] = np.linspace(0, 1, ai) if ai else 1; e[-ri:] *= np.linspace(1, 0, ri) if ri else 1; return e
def lp(x, fc):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
mf = lambda m: 440 * 2 ** ((m - 69) / 12)
def piano(m, d=1.6):
    t = T(d); f = mf(m); s = sum(np.sin(2 * np.pi * f * k * t) * a for k, a in ((1, 1), (2, .45), (3, .2), (4, .1)))
    return s * np.exp(-t * 2.4) * env(len(t), .004, .05)
def pad(ms, d):
    t = T(d); s = sum(np.sin(2 * np.pi * mf(m) * t * (1 + dt)) for m in ms for dt in (-.003, 0, .003))
    return lp(s, 1400) * env(len(t), d * .3, d * .3) / (3 * len(ms))
def drone(f, d):
    t = T(d); s = np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 1.5 * t + np.sin(t * .7)) + .3 * lp(R.uniform(-1, 1, len(t)), 200)
    return s * env(len(t), 1.5, 1.5) * (1 + .2 * np.sin(2 * np.pi * .25 * t))
noise = lambda d: R.uniform(-1, 1, int(d * SR))

# ---------------------------------------------------------------- MÚSICA
# 0–22.5: piano nostálgico (La m – Fa – Do – Sol) + pad cálido
prog = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
t = 0.
while t < 22.5:
    ch = prog[int(t / 2.8) % 4]
    put(mus, t, pad([m - 12 for m in ch], 3.0), .5)
    for k, m in enumerate([ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1]]): put(mus, t + k * .46, piano(m + 12), .16 * (1 - .4 * (t > 19)))
    t += 2.8
# 22.5–46: entra lo grave con la alerta; tensión creciente con pulso
put(mus, 22.5, drone(55, 24), .32)
for k in range(int((46 - 25) / .9)): put(mus, 25 + k * .9, np.sin(2 * np.pi * 45 * T(.4)) * np.exp(-T(.4) * 9), .3 + .2 * k / 23)
for k, m in enumerate([69, 68, 69, 68]): put(mus, 23 + k * 5.5, pad([m - 12, m - 5], 5.5), .25)
# 46–61: caos (graves fuertes + golpes + cuerdas disonantes)
put(mus, 46, drone(49, 15.5), .38)
for k in range(int(15 / .45)): put(mus, 46 + k * .45, np.sin(2 * np.pi * 40 * T(.3)) * np.exp(-T(.3) * 12), .45)
put(mus, 46, lp(noise(15) * np.linspace(.05, .3, int(15 * SR)), 900), .5)
# 61–83: terror contenido (dron y latidos)
put(mus, 61, drone(41.2, 22), .34); put(mus, 61, pad([56, 57], 22), .12)
for k in range(int(22 / .85)): tt = 61 + k * .85; put(mus, tt, np.sin(2 * np.pi * 55 * T(.12)) * np.exp(-T(.12) * 30), .5); put(mus, tt + .22, np.sin(2 * np.pi * 50 * T(.12)) * np.exp(-T(.12) * 30), .35)
# 83–88.5: silencio musical · 88.5: golpe final y pad
put(mus, 88.5, pad([45, 52, 57], 4.5), .35)

# ---------------------------------------------------------------- EFECTOS (sincronizados con las acciones)
put(fx, 0, lp(noise(8), 600) * env(8 * SR, 1, 1.5), .12)                                     # tráfico lejano
for tt in (.2, 1.4, 4.4): put(fx, tt, bp(noise(2.2), 80, 400) * np.sin(np.linspace(0, np.pi, int(2.2 * SR))), .5)   # autos que pasan
put(fx, 6.4, sum(np.sin(2 * np.pi * f * T(1.2)) for f in (2093, 2637)) * np.exp(-T(1.2) * 5) * .4, .5)          # campanita de la tienda
sir = lambda d, f0=700: np.sin(2 * np.pi * np.cumsum(f0 + 250 * np.sin(2 * np.pi * .7 * T(d))) / SR)
put(fx, 8.0, sir(3.0) * env(int(3 * SR), .3, .6), .14)                                        # sirena de la ambulancia
for k in range(5): put(fx, 11.3 + k * .7, np.sin(2 * np.pi * 1000 * T(.12)) * env(int(.12 * SR), .005, .03), .1)   # monitor
put(fx, 11, lp(noise(3.5), 300) * .5, .2)                                                    # ruedas de la camilla
for tt in (15.2, 17.4, 19.6, 21.8): put(fx, tt, np.sin(2 * np.pi * 3100 * T(.25)) * np.exp(-T(.25) * 30), .12)      # cubiertos
put(fx, 22.6, np.concatenate([np.sin(2 * np.pi * 880 * T(.18)), np.zeros(int(.05 * SR)), np.sin(2 * np.pi * 660 * T(.3))]) * .5, .3)   # tono de alerta
for k in range(3): put(fx, 34.2 + k * .9, np.sign(np.sin(2 * np.pi * 150 * T(.5))) * lp(np.ones(int(.5 * SR)), 300) * .3, .35)      # vibración del teléfono
put(fx, 37.2, bp(noise(3.6), 400, 1800) * (.5 + .5 * np.sin(2 * np.pi * 5 * T(3.6))), .07)  # voz de Marcos (ininteligible, filtrada)
for k in range(3): put(fx, 41.3 + k * .35, np.sin(2 * np.pi * 480 * T(.2)), .15)            # pitidos de llamada cortada
put(fx, 43, sir(3.5, 600) * env(int(3.5 * SR), 1, 1), .06)                                   # sirenas lejanas
put(fx, 47.2, bp(noise(.9), 1500, 5000) * np.linspace(.2, 1, int(.9 * SR)), .3)            # derrape
put(fx, 48.0, lp(noise(1.2), 400) * np.exp(-T(1.2) * 3) + np.sin(2 * np.pi * 50 * T(1.2)) * np.exp(-T(1.2) * 4), .9)   # choque
for k in range(14): put(fx, 48.05 + R.uniform(0, .7), np.sin(2 * np.pi * R.uniform(3000, 6000) * T(.15)) * np.exp(-T(.15) * 30), .12)   # vidrios
put(fx, 48.3, np.sin(2 * np.pi * np.cumsum(900 + 300 * np.sign(np.sin(2 * np.pi * 2 * T(4)))) / SR) * .4, .06)   # alarma del auto
put(fx, 51.3, bp(noise(.6), 900, 3000) * np.sin(np.linspace(0, np.pi, int(.6 * SR))), .1)    # grito lejano (textura)
for k in range(6): put(fx, 53.6 + k * .28, lp(noise(.1), 300) * np.exp(-T(.1) * 40), .6)    # pasos de Daniel corriendo
put(fx, 55.6, np.sin(2 * np.pi * 2000 * T(.04)) + lp(noise(.06), 2000)[:int(.04 * SR)], .5)  # «clac» del cerrojo
put(fx, 56.5, sir(4, 650) * .5 + sir(4, 820) * .5, .07); put(fx, 59.5, hp(noise(1.5), 1000) * env(int(1.5 * SR), .02, .2), .2)   # sirenas / estática
knock = lambda: lp(noise(.25), 250) * np.exp(-T(.25) * 18) + np.sin(2 * np.pi * 85 * T(.25)) * np.exp(-T(.25) * 14)
for tt in (61.5, 62.1, 62.7): put(fx, tt, knock(), 1.0)                                       # TRES GOLPES
for tt in (64.4, 65.3, 66.2): put(fx, tt, knock(), .7)
put(fx, 64.3, bp(noise(1.4), 300, 2500) * np.sin(np.linspace(0, np.pi, int(1.4 * SR))) * (.6 + .4 * np.sin(2 * np.pi * 7 * T(1.4))), .12)   # «¡déjenme entrar!» (textura de grito tras la puerta)
put(fx, 67, lp(noise(2.4), 600) * (.5 + .5 * np.sin(2 * np.pi * .6 * T(2.4))), .05)        # respiración contenida
for k in range(10): put(fx, 69.8 + k * .45, knock(), .55)                                    # golpes por la mirilla
for k in range(5): put(fx, 77.2 + k * .55, knock(), .4)
put(fx, 78.6, bp(noise(1.4), 500, 2000) * (.5 + .5 * np.sin(2 * np.pi * 6 * T(1.4))), .05)  # sollozo (textura)
for k in range(5): put(fx, 80.2 + k * .5, knock(), .45)
put(fx, 81.5, lp(noise(1.5), 200) * np.linspace(0, 1, int(1.5 * SR)), .3)                   # algo se arrastra
put(fx, 85.5, knock(), .9)                                                                    # un solo golpe en el silencio
put(fx, 88.5, np.sin(2 * np.pi * 38 * T(2.5)) * np.exp(-T(2.5) * 1.5) + lp(noise(2.5), 120) * np.exp(-T(2.5) * 2), .9)   # golpe grave final

mix = np.tanh((mus * .55 + fx * .7) * 1.2) * .85
mix[int(83.0 * SR):int(85.4 * SR)] *= .15                                                      # silencio antes de las opciones
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'audio_ep01.wav')
import soundfile as sf; sf.write(out, mix[:int(DUR * SR)].astype(np.float32), SR)
print(out)
