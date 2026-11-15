#!/usr/bin/env python3
# Short: ¿Qué pasaría si aprobaran la extradición de El Chapo a México? · versión realista
# Sin voz: tiempos estimados a partir del guion (se reemplazan con los tiempos reales de la voz).
import rescate as RS
from rescate import *
import re, json

HERE_ = os.path.dirname(os.path.abspath(__file__))
TXT = open(os.path.join(HERE_, 'guion_realista_voz.txt')).read()

def estimate_words(txt):
    """Tiempos aproximados por palabra (narrador ~2.6 palabras/s) respetando las pausas <break>."""
    t = .25; words = []
    for tok in re.findall(r'<break time="([\d.]+)s" />|(\S+)', txt.replace('\n', ' ')):
        brk, w = tok
        if brk: t += float(brk); continue
        d = .08 + .044 * len(w); words.append([w, t, t + d]); t += d + .04
        if w[-1] in ',:': t += .12
        if w[-1] in '.?!': t += .2
        if w.endswith('…'): t += .3
    return words
WORDS = json.load(open(os.path.join(HERE_, 'words_realista.json'))) if os.path.exists(os.path.join(HERE_, 'words_realista.json')) else estimate_words(TXT)
def start_of(word):
    return next(w[1] for w in WORDS if w[0].startswith(word)) - .35
DUR = int(math.ceil(WORDS[-1][2] + 1.6))
SC_T = [0, start_of('Primero'), start_of('Segundo'), start_of('Tercero'), start_of('¿Crees'), DUR]
def at(word, k=0):  # tiempo (relativo a su escena) de la k-ésima aparición de una palabra
    hits = [w[1] for w in WORDS if w[0].strip('¿?¡!.,…:;').lower().startswith(word.lower())]; return hits[min(k, len(hits) - 1)]

RS.KEY |= {'extradición', 'Chapo', 'Guzmán', 'Hollywood', 'táctica', 'real:', 'sobornos', 'Culiacanazo', 'dinero', 'bala', 'corromper', 'judicial',
           'caos', 'calles', 'bloqueos', 'incendios', 'terror', 'negociar', 'regreso', 'territorios', 'reactivarían', 'reglas', 'político', 'poder', 'armas', 'reales'}
EMOJIS = [
 (at('extradición'), at('Olvida'), '🇲🇽', 860, 900, 150, 'pop'), (at('Olvida'), SC_T[1], '🚫', 200, 900, 150, 'sacude'), (at('sobornos'), SC_T[1], '⚠️', 860, 900, 150, 'late'),
 (at('dinero'), at('dinero') + 3, '💰', 860, 1180, 150, 'late'), (at('corromper'), SC_T[2] - .2, '📄', 200, 1180, 150, 'sacude'),
 (at('caos'), at('caos') + 3, '🏙️', 860, 1240, 140, 'pop'), (at('incendios'), SC_T[3] - .2, '🔥', 200, 1240, 150, 'late'),
 (at('regreso'), at('regreso') + 3, '🇲🇽', 860, 900, 150, 'cae'), (at('territorios'), SC_T[4] - .2, '👑', 200, 900, 150, 'cae'),
 (SC_T[4] + .3, DUR, '💬', 180, 380, 140, 'late'), (at('like'), DUR, '👍', 540, 300, 150, 'pop'), (at('sígueme'), DUR, '🔔', 900, 380, 140, 'sacude'),
]

# ================================================================ 1 · Gancho: ciudad en penumbra y el reo
class Q1:
    def __init__(s):
        sky = vgrad([(0, (6, 6, 12)), (.5, (24, 16, 22)), (1, (40, 22, 24))]); radial(sky, (540, 1000), 800, (120, 30, 20), .25)
        s.back = [(dof(rgba(sky, np.ones((H, W))), 2), .1)]
        city = np.zeros((H, W, 3), np.uint8); r_ = np.random.RandomState(31); x = -30; s.wins = []
        while x < W:
            bw, bh = r_.randint(90, 180), r_.randint(300, 900); cv2.rectangle(city, (x, 1250 - bh), (x + bw, 1260), (26, 22, 30), -1)
            for wy in range(1250 - bh + 20, 1240, 34):
                for wx in range(x + 12, x + bw - 16, 26):
                    if r_.rand() < .3: cv2.rectangle(city, (wx, wy), (wx + 12, wy + 16), (255, 170, 80), -1); s.wins.append((wx + 6, wy + 8, r_.rand()))
            x += bw + r_.randint(4, 16)
        for (x, y) in [(120, 520), (980, 600)]: cv2.circle(city, (x, y), 6, (255, 40, 30), -1)
        s.back.append((dof(haze(rgba(city, np.any(city > 0, 2).astype(np.float32)), (40, 22, 24), .3), 2), .45))
        fl = np.zeros((H, W, 3), np.uint8); fl[1260:] = (30, 28, 32)
        for j in range(1, 9): y = int(1260 + (H - 1260) * (j / 8.) ** 1.7); cv2.line(fl, (0, y), (W, y), (44, 40, 46), 2, cv2.LINE_AA)
        al = np.zeros((H, W)); al[1260:] = 1; s.main = rgba(fl, al)
        bars = np.zeros((H, W, 4), np.uint8)
        for x in list(range(-30, 200, 70)) + list(range(900, W + 40, 70)): cv2.rectangle(bars, (x, 0), (x + 34, H), (60, 64, 72, 255), -1); cv2.rectangle(bars, (x + 6, 0), (x + 13, H), (140, 146, 156, 255), -1)
        s.front = [(dof(bars, 12), 1.55), (bokeh_layer(12, (255, 170, 80), 21, rmin=20, rmax=60, ymin=200, ymax=1700), 1.7)]
        s.ext = N.stamp('EXTRADICIÓN APROBADA', (70, 230, 120), w=840, h=124, px=66, fill=(6, 40, 16, 200))
        s.title = red_panel('TÁCTICA REAL', w=640, h=170)
        s.dust = Dust(36, (40, 300, 1040, 1600), (255, 190, 120), 4, .45)
    def draw(s, fr, t, d):
        s.dust.draw(fr, t)
        cv2.ellipse(fr, (540, 1594), (170, 22), 0, 0, 360, (16, 14, 16), -1, cv2.LINE_AA)
        character(fr, 'reo', 540, 1590, 520, t, armR=('jarra',), armL=('jarra',), look=(0, -.1), frown=.15, mustache=True)
        k = ss(at('extradición') + .2, at('extradición') + .5, t) * (1 - ss(at('Olvida') - .3, at('Olvida'), t))
        if k > 0: blit(fr, s.ext, 540, 360, k, lerp(1.6, 1., eOut(k)))
        k2 = ss(at('táctica'), at('táctica') + .4, t)
        if k2 > 0: blit(fr, s.title, 540, 360 + math.sin(t * 1.5) * 5, k2 * (.88 + .12 * math.sin(t * 5)), lerp(1.3, 1, eOut((t - at('táctica')) / .4)))
    def cam(s, t, d):
        k = eExpo(t / 1.5); return lerp(2.2, 1.05, k) * (1 + .06 * ss(1.5, d, t)), 540, lerp(1350, 1050, k), lerp(-40, 40, eIO(t / d)) * ss(1, 2.5, t), 0

# ================================================================ 2 · El poder del dinero: oficina de gobierno, maletines y sobornos
class Q2(CH.C2):
    def __init__(s):
        super().__init__()
        seal = np.zeros((H, W, 4), np.uint8)
        cv2.circle(seal, (110, 1780), 230, (150, 120, 50, 255), -1, cv2.LINE_AA); cv2.circle(seal, (110, 1780), 180, (100, 76, 26, 255), -1, cv2.LINE_AA)
        cv2.circle(seal, (110, 1780), 120, (150, 120, 50, 255), 10, cv2.LINE_AA)
        s.front = [(dof(seal, 10), 1.5), (bokeh_layer(10, (255, 210, 120), 22, ymin=200, ymax=1400), 1.7)]
        s.tx = N.holo_panel(620, 230, 'TRANSFERENCIA', '$ 25,000,000 · CIFRADO', col=(255, 210, 90), fill=(60, 40, 6, 190))
        s.stamp = N.stamp('CORRUPCIÓN', (255, 59, 42), w=680, px=92)
        s.bill = np.zeros((44, 90, 4), np.uint8); cv2.rectangle(s.bill, (2, 2), (87, 41), (90, 170, 100, 255), -1); cv2.rectangle(s.bill, (8, 8), (81, 35), (50, 110, 60, 255), 2)
        cv2.circle(s.bill, (45, 22), 9, (190, 230, 190, 255), -1)
        s.digits = [N.text_sprite(c, 30, (120, 230, 255, 220), pad=4) for c in '0123456789ABCDEF']
    def briefcase(s, fr, x, y, sc, t, k):
        c = (255, 210, 90); w, h = 260 * sc, 150 * sc
        ov = fr.copy()
        cv2.rectangle(ov, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), (60, 40, 6), -1)
        poly(ov, [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2 - 20 * sc, y - h * 1.3), (x - w / 2 + 20 * sc, y - h * 1.3)], (40, 28, 6))   # tapa abierta
        fr[:] = cv2.addWeighted(fr, 1 - .6 * k, ov, .6 * k, 0)
        cv2.rectangle(fr, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), c, 3)
        pline(fr, [(x - w / 2, y - h / 2), (x - w / 2 + 20 * sc, y - h * 1.3), (x + w / 2 - 20 * sc, y - h * 1.3), (x + w / 2, y - h / 2)], c, 3)
        for i in range(3):
            for j in range(4): blit(fr, s.bill, x - w / 2 + 40 * sc + j * 60 * sc, y - h / 4 + i * 34 * sc, k, sc * .7)
        for i in range(6):  # flujo de dinero digital hacia arriba
            f = (t * .8 + i / 6.) % 1; blit(fr, s.bill, x + math.sin(i * 2 + t) * 80 * sc, y - h - f * 420 * sc, k * (1 - f), sc * .6)
    def draw(s, fr, t, d):
        s.dust.draw(fr, t)
        for i in range(26):   # datos cifrados cayendo
            x = 60 + (i * 41) % 960; f = (t * .35 + (i * .37) % 1) % 1
            blit(fr, s.digits[(i * 7 + int(t * 6)) % 16], x, 200 + f * 1100, .35 * (1 - f))
        k = ss((at('dinero') - SC_T[1]) + .2, (at('dinero') - SC_T[1]) + .8, t)
        if k > 0:
            s.briefcase(fr, 290, 1250, 1.0, t, k); s.briefcase(fr, 790, 1290, .9, t + 1, k)
        a = ss((at('disparar') - SC_T[1]), (at('disparar') - SC_T[1]) + .5, t) * (1 - ss((at('sobornos', 1) - SC_T[1]) - .3, (at('sobornos', 1) - SC_T[1]), t))
        if a > 0: blit(fr, s.tx, 540, 600 + math.sin(t * 1.4) * 5, a, lerp(1.2, 1, eOut((t - (at('disparar') - SC_T[1])) / .5)))
        k2 = ss((at('sobornos', 1) - SC_T[1]), (at('sobornos', 1) - SC_T[1]) + .3, t)
        if k2 > 0: blit(fr, s.stamp, 540, 600, k2, lerp(1.6, 1., eOut(k2)))
    def front_docs(s, fr, t): pass
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.05, 1.15, k), 540, lerp(1000, 1100, k), lerp(-55, 55, k), 0

# ================================================================ 3 · Culiacanazo nacional: mapa en llamas + bloqueo en la avenida
class Q3(RS.R3):
    def __init__(s):
        super().__init__()
        s.title = red_panel('ESTADO DE SITIO', w=700, h=170)
        s.flame = glow_sprite(70, (255, 140, 40)); s.puff = glow_sprite(120, (90, 80, 80))
    def draw(s, fr, t, d):
        pul = .5 + .5 * math.sin(t * 4)
        blit(fr, s.gl, s.glc[0], s.glc[1], .15 + .4 * pul, add=True)
        for n, i in enumerate(s.ord):   # focos de fuego y alertas por todo el país
            t0 = 2.0 + n * .45
            if t < t0: continue
            x, y = prj(*s.pts[i]); g = ss(t0, t0 + .6, t); fl = .7 + .3 * math.sin(t * 11 + n)
            blit(fr, s.flame, x, y - 10, g * fl, .7 + .3 * fl, add=True); circ(fr, (x, y), 7, (255, 230, 180))
            f = (t * .8 + n * .17) % 1; cv2.circle(fr, (int(x), int(y)), int(14 + f * 60), (int(255 * (1 - f)), int(60 * (1 - f)), int(40 * (1 - f))), 3, cv2.LINE_AA)
    def floating(s, fr, t, d, P):
        # bloqueo en una avenida (primer plano): camionetas atravesadas e incendiadas, humo y hombres armados
        y0 = 1380; ov = fr.copy(); cv2.rectangle(ov, (0, y0), (W, H), (14, 12, 14), -1); fr[:] = cv2.addWeighted(fr, .15, ov, .85, 0)
        for k in range(-6, 7): cv2.line(fr, (540, y0), (540 + k * 260, H), (30, 26, 28), 2)
        for i in range(14):
            f = (i / 14. + t * .06) % 1; blit(fr, s.puff, 160 + (i % 4) * 250 + f * 100, y0 + 60 - f * 700, min(1, f * 5) * (1 - f) * .5, 1 + f * 2.4)
        for j, (x, y, sc) in enumerate([(-60, 1560, 1.0), (560, 1580, 1.05)]):
            CH.C4.suv(s, fr, x, y, sc, t, 0, lights=False)
            for q in range(4):
                fl = .7 + .3 * math.sin(t * 13 + q + j)
                blit(fr, s.flame, x + 80 + q * 90 * sc, y - 150 * sc, fl, 1.8 + .6 * fl, add=True); blit(fr, glow_sprite(40, (255, 230, 150)), x + 80 + q * 90 * sc, y - 130 * sc, fl, 1.2, add=True)
        for i, x in enumerate((420, 930)):
            hs = character(fr, 'comando', x, 1700, 330, t + i, armR=('apunta', (x - 200, 1560), .8), armL=('apunta', (x - 200, 1560), .4), look=(-.4, 0), frown=.3, mask=True)
            lib.rifle(fr, hs, 330 / 8.)
        k = ss(at('Culiacanazo', 1) - SC_T[2], at('Culiacanazo', 1) - SC_T[2] + .4, t)
        if k > 0: blit(fr, s.title, 540, 330 + math.sin(t * 1.6) * 5, k * (.86 + .14 * math.sin(t * 5)), lerp(1.5, 1., eOut(k)))
        c = ss(3.2, 3.6, t) * (1 - ss(8.6, 9.0, t))        # llamada a la acción pequeña, abajo a la derecha
        if c > 0:
            blit(fr, s.cta, 790, 1290, c, lerp(.6, 1, eBack((t - 3.2) / .4)) * .6)
            blit(fr, s.bell, 980, 1270 + math.sin(t * 9) * 4 * c, c, .4)
        s.dust.draw(fr, t)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.3, 1.15, eOut(t / 3)) * (1 + .04 * k), 520, 1150, lerp(-40, 40, k), 0

# ================================================================ 4 · El regreso: retenes en la carretera y postura de mando
class Q4(CH.C4):
    def __init__(s):
        super().__init__()
        s.stamp = N.stamp('CONTROL', (255, 59, 42), w=560, px=110)
    def draw(s, fr, t, d):
        for i in range(10):
            f = (i / 10. + t * .05) % 1; blit(fr, s.puff, 300 + (i % 3) * 220 + f * 160, 1080 - f * 800, min(1, f * 5) * (1 - f) * .25, .9 + f * 2.4)
        on = (t * 2.5) % 1 < .5
        for i, (x, y) in enumerate(s.lights): blit(fr, glow_sprite(70, (255, 40, 40) if on ^ (i % 2) else (40, 90, 255)), x, y, .9, add=True)
        # retén: caseta, conos y pluma, con guardias armados
        for (bx, sc) in [(70, .9), (830, .95)]:
            cv2.rectangle(fr, (int(bx), int(1300 - 200 * sc)), (int(bx + 170 * sc), 1300), (52, 50, 46), -1)
            cv2.rectangle(fr, (int(bx + 20 * sc), int(1300 - 170 * sc)), (int(bx + 150 * sc), int(1300 - 100 * sc)), (255, 200, 120), -1)
            cv2.rectangle(fr, (int(bx - 10), int(1300 - 210 * sc)), (int(bx + 180 * sc), int(1300 - 190 * sc)), (40, 38, 34), -1)
        line(fr, (250, 1260), (820, 1240), (240, 240, 240), 10);
        for k in range(8): line(fr, (250 + k * 72, 1259 - k * 2.5), (286 + k * 72, 1258 - k * 2.5), (220, 40, 40), 10)
        for x in (300, 420, 660, 780): poly(fr, [(x - 16, 1330), (x + 16, 1330), (x, 1280)], (255, 120, 30))
        for i, x in enumerate((140, 940)):
            hs = character(fr, 'comando', x, 1420, 300, t + i, armR=('apunta', (x + (200 if i == 0 else -200), 1300), .8), armL=('apunta', (x + (200 if i == 0 else -200), 1300), .4),
                           look=(.4 if i == 0 else -.4, 0), frown=.3, mask=True)
            lib.rifle(fr, hs, 300 / 8.)
        s.dust.draw(fr, t)
        cv2.ellipse(fr, (540, 1604), (170, 22), 0, 0, 360, (16, 12, 10), -1, cv2.LINE_AA)
        character(fr, 'civil', 540, 1600, 500, t, armR=('jarra',), armL=('jarra',), look=(0, -.1), frown=.1, smile=.25, mustache=True, cap=True)
        k = ss(at('reactivarían') - SC_T[3], at('reactivarían') - SC_T[3] + .3, t)
        if k > 0: blit(fr, s.stamp, 540, 560, k, lerp(1.6, 1., eOut(k)))
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.06, 1.14, k), 540, 1200, lerp(-130, 130, k), 0     # travelling lateral rápido

# ================================================================ 5 · Cierre
class Q5(RS.R5):
    def __init__(s):
        super().__init__()
        s.cta = N.holo_panel(620, 200, '¿PODER REAL?', 'COMENTA ABAJO')

VOZ = os.path.join(HERE_, 'voz_realista.mp3')
if not os.path.exists(VOZ):
    VOZ = os.path.join(OUT, 'silencio.mp3')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=mono', '-t', str(DUR), VOZ], check=True)
_s = CH._src.replace("secs = [(0, 'tension', 1), (9.9, 'misterio', 2), (24.1, 'tension', 2), (37.2, 'epico', 2), (50.2, 'tension', 1)]",
     f"secs = [(0, 'tension', 1), ({SC_T[1]:.2f}, 'misterio', 2), ({SC_T[2]:.2f}, 'epico', 2), ({SC_T[3]:.2f}, 'tension', 2), ({SC_T[4]:.2f}, 'epico', 1)]")
_a = _s.index('    EF = ['); _b = _s.index(']]', _a) + 2
_EF = (f"    EF = [[0, 'boom', .9], [{at('Olvida') - .3:.2f}, 'whoosh', .5], [{at('táctica'):.2f}, 'impacto', .6], [{SC_T[1] - .5:.2f}, 'whoosh', .5],"
       f" [{SC_T[1]:.2f}, 'impacto', .6], [{at('dinero'):.2f}, 'dinero', .25], [{at('corromper'):.2f}, 'latido', .35], [{at('sobornos', 1) + .1:.2f}, 'impacto', .8], [{SC_T[2] - .5:.2f}, 'whoosh', .5],"
       f" [{SC_T[2]:.2f}, 'impacto', .6], [{SC_T[2] + 3.2:.2f}, 'pop', .15], [{at('incendios'):.2f}, 'alarma', .05, 2.2], [{at('Culiacanazo', 1):.2f}, 'boom', .5], [{SC_T[3] - .5:.2f}, 'whoosh', .5],"
       f" [{SC_T[3]:.2f}, 'impacto', .6], [{SC_T[3] + .5:.2f}, 'viento', .07, 8], [{at('reactivarían') + .1:.2f}, 'impacto', .8], [{SC_T[4] - .5:.2f}, 'whoosh', .5],"
       f" [{SC_T[4]:.2f}, 'boom', .5], [{at('like') + .1:.2f}, 'ding', .3], [{at('sígueme') + .1:.2f}, 'ding', .25]]")
_s = _s[:_a] + _EF + _s[_b:]
# mezcla: música y efectos más bajos; la música baja aún más cuando habla la voz
_s = _s.replace("env / (env.max() * .25)", "env / (env.max() * .25 + 1e-9)").replace("duck = 1 - .55 * env", "duck = 1 - .7 * env").replace(
    "out = np.tanh((mus * .75 * duck + fx * .6 * (1 - .35 * env)) * 1.1) * .8 + vv * .92",
    "out = np.tanh((mus * .5 * duck + fx * .32 * (1 - .5 * env)) * 1.1) * .7 + vv * .95")
exec(_s)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    subs_def = RS.build_subs_from_words(WORDS, [1460, 1500, 1200, 1460, 1480]) if mode != 'nosubs' else []
    # build_subs usa SC_T del módulo rescate: lo alineamos
    RS.SC_T[:] = SC_T; RS.DUR = DUR; subs_def = RS.build_subs_from_words(WORDS, [1460, 1500, 1200, 1460, 1480])
    objs = [Q1(), Q2(), Q3(), Q4(), Q5()]
    scenes = [(SC_T[i], SC_T[i + 1], objs[i]) for i in range(5)]
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in subs_def]; emos = [e + (emoji_sprite(e[2]),) for e in EMOJIS]
    def one(idx, T):
        a, b, sc = scenes[idx]; return cinema(render3d(sc, T - a, b - a, T), min(idx, 4), T)
    def frame(T):
        idx = max(i for i, (a, b, _) in enumerate(scenes) if T >= a - 1e-6)
        a = scenes[idx][0]; fr = one(idx, T)
        if idx > 0 and T - a < .45: fr = cv2.addWeighted(one(idx - 1, T), 1 - ss(0, .45, T - a), fr, ss(0, .45, T - a), 0)
        draw_overlays(fr, T, subs, emos); return fr
    if mode == 'info': print('DUR', DUR, 'SC_T', [round(x, 2) for x in SC_T]); return
    if mode == 'test':
        for T in [float(x) for x in sys.argv[2:]]:
            cv2.imwrite(f'{OUT}/q_{T:05.1f}.jpg', cv2.resize(frame(T), (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == 'seg':
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', f'{OUT}/qseg_{f0:04d}.mp4']
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(f0, f1): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('SEG', f0, f1, flush=True); return
    if mode == 'audio': synth_audio(f'{OUT}/audio_realista.wav'); print('audio ok'); return

if __name__ == '__main__': main()
