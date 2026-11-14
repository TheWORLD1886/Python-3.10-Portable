#!/usr/bin/env python3
# NVIDIA v2 · producción con actuación de personajes y control de calidad por fotograma.
# - Voz: «Envidia» en la locución (voz.mp3); en pantalla y subtítulos se lee NVIDIA.
# - Planos gráficos verificados: se reutilizan de nvidia.py.
# - Planos con personajes: reescritos como acciones (caminar, girar, tomar objetos, reaccionar) según STORYBOARD.md.
# - Cada llamada al rig (person / person_side / person_34) se registra automáticamente: articulaciones de cada personaje
#   en cada fotograma, para qc_final.py.
import os, sys, json, math, subprocess
HERE_2 = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE_2)
import nvidia as NV
from nvidia import *
RG = NV.RG
OUT2 = os.path.join(HERE_2, 'out2'); os.makedirs(OUT2, exist_ok=True)

# ---------------------------------------------------------------- subtítulos: se escucha «Envidia», se lee «NVIDIA»
WDISP = [[w.replace('Envidia', 'NVIDIA').replace('envidia', 'NVIDIA'), a, b] for w, a, b in NV.WORDS]
NV.TR.KEY = NV.KEYW | {'nvidia'}

# ---------------------------------------------------------------- registro automático de todas las llamadas al rig
CTX = dict(shot=-1, f=-1, rec=False, inner=False, tag=None, counts={}, log=[])
_orig = {n: getattr(RG, n) for n in ('person', 'person_side', 'person_34')}
def _wrap(name):
    fn = _orig[name]
    def w(fr, who, x, fy, hgt, pose, t=0., feet=None, **kw):
        if CTX['inner']: return fn(fr, who, x, fy, hgt, pose, t, feet=feet, **kw)
        c = CTX['counts']; k = (CTX['shot'], who); n = c.get(k, 0); c[k] = n + 1
        rid = f"{CTX['shot']}:{who}:{n}"; pose = dict(pose, ikid=rid)
        if name == 'person_34': CTX['inner'] = True
        try: hands, j = fn(fr, who, x, fy, hgt, pose, t, feet=feet, **kw)
        finally: CTX['inner'] = False
        if CTX['rec'] and j:
            ground = max(v[1] for v in feet.values()) if feet else fy
            CTX['log'].append(dict(f=CTX['f'], shot=CTX['shot'], id=rid, who=who, view=j.get('view'), u=float(j.get('u', 0)), fy=float(ground),
                                   hand_r=float(j.get('hand_r', 0)), tag=CTX['tag'], speaking=False, boca=pose.get('boca', 'neutra'), abre=float(pose.get('abre', 0)),
                                   joints={a: [round(float(v[0]), 2), round(float(v[1]), 2)] for a, v in j.items() if isinstance(v, np.ndarray) and v.shape == (2,)},
                                   raw={a: [round(float(v[0]), 2), round(float(v[1]), 2)] for a, v in (j.get('raw') or {}).items()},
                                   z={a: round(float(v), 2) for a, v in (j.get('z') or {}).items()},
                                   grip={a: [float(g[0]), float(g[1]), float(g[2] if len(g) > 2 else 1)] for a, g in (pose.get('grip') or {}).items()}))
        return hands, j
    return w
for _n in _orig: setattr(RG, _n, _wrap(_n))

# ---------------------------------------------------------------- herramientas de actuación
BASE = dict(ik3d=True, tz=.8, brow_up=0., brow_asym=0., abre=0., lean=0., sh=0., hip_dx=0., look=(0., 0.), tilt=0., frown=0., boca='neutra', grip=None,
            uL=-.1, lL=.08, uR=.1, lR=-.08)
def P(**kw): return dict(BASE, **kw)
def U(who, h): return h * RG.CAST[who]['alto'] / 8.
def snap(x, who, h): s = RG.step_len(U(who, h)); return round(x / s) * s          # parada con los dos pies apoyados
def walk(fr, who, x0, x1, t0, t1, fy, h, t, look=None, mode='llega', **pose):
    """camina de x0 a x1 entre t0 y t1 (perfil, pies fijos). mode: 'llega' frena al final, 'sale' arranca desde parado."""
    u = U(who, h); d = 1 if x1 > x0 else -1; k = min(1., max(0., (t - t0) / (t1 - t0)))
    e = k * (2 - k) if mode == 'llega' else k * k; de = 2 * (1 - k) if mode == 'llega' else 2 * k
    x = x0 + (x1 - x0) * e; v = abs(x1 - x0) * de / (t1 - t0); kv = min(1., v / (1.6 * RG.step_len(u)))
    gp, feet, bob = RG.gait_x(x, d, u, fy)
    gp.update(uL=gp['uL'] * kv, uR=gp['uR'] * kv, lean=gp['lean'] * kv, look=look or (.55 * d, .05), blink=RG.blink(t, 5))
    pp = dict(P(), **pose); pp.update(gp)
    prev = CTX['tag']; CTX['tag'] = prev or 'camina'; RG.person_side(fr, who, x, fy + bob * kv, h, pp, t, feet=feet, facing=d); CTX['tag'] = prev
    return x
def stance(x, u, fy, w=.3): return {'L': (x - w * u, fy), 'R': (x + w * u, fy)}
def turn_blend(fr, q, draw_a, draw_b):
    """giro con fundido corto (planificado): draw_a = vista anterior, draw_b = vista nueva."""
    a = fr.copy(); CTX['tag'] = 'giro'; draw_a(a); r = draw_b(fr); CTX['tag'] = None
    e = RG.ease(q); fr[:] = cv2.addWeighted(a, 1 - e, fr, e, 0); return r
def fade_in(fr, k, draw):
    if k >= 1: return draw(fr)
    a = fr.copy(); r = draw(fr); fr[:] = cv2.addWeighted(a, 1 - k, fr, k, 0); return r
def hands_on_top(fr, hands, who, h, sc=.9):
    u = U(who, h); piel = RG.CAST[who].get('piel', SKIN)
    for hd in hands.values(): circ(fr, hd, .31 * u * sc, (170, 172, 182)); circ(fr, hd, .27 * u * sc, piel)
def paper(fr, hands, w_extra=36, h=120, col=(236, 228, 206), lines=True, red=False):
    c = (A(*hands['L']) + A(*hands['R'])) / 2; w = abs(hands['R'][0] - hands['L'][0]) + w_extra
    x0, x1, yb = c[0] - w / 2, c[0] + w / 2, c[1] + 40; yt = yb - h
    cv2.rectangle(fr, (int(x0), int(yt)), (int(x1), int(yb)), col, -1); cv2.rectangle(fr, (int(x0), int(yt)), (int(x1), int(yb)), dark(col, .7), 2)
    if lines:
        for i in range(int((h - 30) / 22)): cv2.rectangle(fr, (int(x0 + 12), int(yt + 18 + i * 22)), (int(x1 - 12 - (i % 3) * 18), int(yt + 26 + i * 22)), (14, 14, 16) if (red and i % 2) else (120, 110, 90), -1)
def tablet(fr, hands, t):
    c = (A(*hands['L']) + A(*hands['R'])) / 2; w = abs(hands['R'][0] - hands['L'][0]) + 30
    x0, x1, yt, yb = c[0] - w / 2, c[0] + w / 2, c[1] - 70, c[1] + 30
    cv2.rectangle(fr, (int(x0), int(yt)), (int(x1), int(yb)), (20, 22, 28), -1); cv2.rectangle(fr, (int(x0 + 8), int(yt + 8)), (int(x1 - 8), int(yb - 8)), (30, 80, 120), -1)
    for i in range(4): cv2.line(fr, (int(x0 + 16), int(yt + 22 + i * 18)), (int(x0 + 16 + (w - 40) * (.4 + .5 * ((i * 37 + int(t * 3)) % 7) / 7)), int(yt + 22 + i * 18)), (150, 230, 255), 3)
def blinkp(t, seed): return RG.blink(t, seed)

# ================================================================ PLANOS CON PERSONAJES (actuación)
class Relation(Sb):                                # Jensen llega, gira y descubre a una mujer; en «trabajaba para China» la silueta es Alice
    def __init__(s):
        s.back = stage_bg(2, (14, 8, 14), (180, 60, 120)); s.main = floor_layer(1600, (20, 16, 22), (34, 28, 36))
        s.front = [(bokeh_layer(10, (255, 140, 180), 402, ymin=200, ymax=1500), 1.7)]
        s.n1 = label('CEO DE NVIDIA'); s.src = label('SEGÚN INTELIGENCIA DE EE. UU.', 30, (255, 220, 160))
        s.st = N.stamp('PRESUNTA ESPÍA', (255, 59, 42), w=640, h=110, px=60); s.cn = flag_sprite_cn(300, 200)
        s.hJ = 600; s.xJ = snap(300, 'jensen', s.hJ)
    def draw(s, fr, t, d):
        hJ, xJ, fy = s.hJ, s.xJ, 1660; uJ = U('jensen', hJ); tw = s.w('trabajaba')
        tm, ts = s.w('mujer'), s.w('según')
        keys = [(1.9, P(look=(.3, 0), frown=0.)), (tm, P(look=(.45, 0), brow_up=.3)), (ts, P(look=(.45, .05), frown=.2)),
                (tw, P(look=(.4, 0), frown=.25, brow_asym=.15)), (tw + .35, P(look=(.35, 0), frown=.45, brow_asym=.25, sh=-.25, lean=-.03, boca='tensa', hip_dx=-.06)),
                (d, P(look=(.35, .05), frown=.5, brow_asym=.2, sh=-.15, lean=-.02, boca='tensa', hip_dx=-.06))]
        def j34(f_): p = RG.anim(keys, t); p['blink'] = blinkp(t, 1); return RG.person_34(f_, 'jensen', xJ, fy, hJ, p, t, feet=stance(xJ, uJ, fy), turn=1)
        if t < 1.7: walk(fr, 'jensen', -160, xJ, 0, 1.7, fy, hJ, t)
        elif t < 1.9: turn_blend(fr, (t - 1.7) / .2, lambda f_: walk(f_, 'jensen', -160, xJ, 0, 1.7, fy, hJ, 1.7), j34)
        else: j34(fr)
        k = ss(tm - .3, tm + .3, t)                                            # la silueta aparece; en «trabajaba» se revela Alice
        if k > 0:
            fA = lambda f_: RG.person_34(f_, 'alice', 800, fy, 560, P(look=(-.45, 0), frown=.1, blink=blinkp(t, 2)), t, feet=stance(800, U('alice', 560), fy), turn=-1)
            fS = lambda f_: RG.person_34(f_, 'figura', 800, fy, 560, P(look=(-.4, 0)), t, feet=stance(800, U('figura', 560), fy), turn=-1)
            if t < tw: fade_in(fr, k, fS)
            elif t < tw + .3: turn_blend(fr, (t - tw) / .3, fS, fA)
            else: fA(fr)
        hk = ss(.3, .7, t); heart(fr, (540, 860), 80 * hk, (230, 60, 110), crack=ss(ts - .1, ts + .5, t))
        blit(fr, s.n1, xJ, 1740, ss(.2, .6, t)); blit(fr, s.src, 540, 560, ss(ts - .1, ts + .3, t))
        g = ss(tw, tw + .3, t)
        if g > 0: blit(fr, s.cn, 800, 700, g, .8); stamp_in(fr, s.st, 540, 380, t, s.w('china'))
    def cam(s, t, d): return lerp(1.08, 1.16, RG.ease(t / d)), 540, 1250, 0, 0

class JensenIntro(Sb):                             # Jensen sale al escenario, saluda y señala la pantalla
    def __init__(s):
        s.back = stage_bg(4, (6, 10, 8), (90, 200, 80)); s.main = floor_layer(1560, (16, 22, 16), (30, 44, 30))
        s.front = [(bokeh_layer(12, (150, 240, 110), 404, ymin=200, ymax=1300), 1.7)]
        s.card = green_panel('JENSEN HUANG', 'FUNDADOR DE NVIDIA', w=760, h=180); s.tag = chip('CEO HASTA EL 12 DE NOVIEMBRE DE 2026', (255, 210, 90), w=820)
        s.h = 700; s.x = snap(470, 'jensen', s.h)
    def draw(s, fr, t, d):
        for i in range(5):
            cv2.rectangle(fr, (80 + i * 190, 560), (250 + i * 190, 1250), (18, 40 + i * 8, 22), -1)
            for k in range(10): cv2.line(fr, (90 + i * 190, 600 + k * 64), (240 + i * 190, 600 + k * 64), (40, 90, 40), 2)
        fbeam(fr, (540, 0), (s.x, 1600), 40, 360, (220, 255, 220), .12, 40)
        fy, h, x = 1680, s.h, s.x; u = U('jensen', h)
        wave = (1.7 < t < 3.3); osc = math.sin((t - 1.7) * 2 * math.pi * 1.6) if wave else 0
        keys = [(1.6, P(look=(0, 0), boca='sonrisa', frown=-.15)), (1.95, P(look=(0, 0), boca='sonrisa', frown=-.15, uR=2.4, lR=.5, sh=-.05)),
                (3.2, P(look=(.05, 0), boca='sonrisa', frown=-.15, uR=2.4, lR=.5)),
                (3.6, P(look=(.35, -.25), boca='sonrisa', frown=-.1, grip={'R': (x + 2.3 * u, fy - 7.4 * u, 1.)}, tz=.3)),
                (d, P(look=(.4, -.3), boca='sonrisa', frown=-.1, grip={'R': (x + 2.35 * u, fy - 7.45 * u, 1.)}, tz=.3))]
        if t < 1.45: walk(fr, 'jensen', -170, x, 0, 1.45, fy, h, t)
        elif t < 1.65:
            def fb(f_): p = RG.anim(keys, t); return RG.person(f_, 'jensen', x, fy, h, p, t, feet=stance(x, u, fy, .38))
            turn_blend(fr, (t - 1.45) / .2, lambda f_: walk(f_, 'jensen', -170, x, 0, 1.45, fy, h, 1.45), fb)
        else:
            p = RG.anim(keys, t); p['blink'] = blinkp(t, 4)
            if wave: p['lR'] = .5 + .45 * osc                                  # saludo con el antebrazo
            p['uR'] = p['uR'] if t < 3.4 else p['uR']
            RG.person(fr, 'jensen', x, fy, h, p, t, feet=stance(x, u, fy, .38))
        float_in(fr, s.card, 540, 330, t, .3)
        if t > s.w('hasta') - .2: float_in(fr, s.tag, 540, 500, t, s.w('hasta') - .2)
    def cam(s, t, d): return lerp(1.12, 1.2, RG.ease(t / d)), 540, 1250, 0, 0

class AliceIntro(Sb):                              # Alice camina a su marca, se acomoda el blazer y mira a cámara
    def __init__(s):
        s.back, s.main = office(6); s.front = [(bokeh_layer(10, (255, 200, 160), 406, ymin=200, ymax=1300), 1.7)]
        s.card = red_panel('ALICE HUANG', w=640, h=150)
        s.t1 = chip('EMPRESARIA CHINA', (255, 160, 140), w=560); s.t2 = chip('DIRECTIVA EN MEGASPEED', (255, 160, 140), w=640)
        s.note = label('SIN PARENTESCO CON JENSEN', 26, (230, 230, 230)); s.note2 = label('NO HA SIDO ACUSADA FORMALMENTE', 26, (230, 230, 230))
        s.h = 680; s.x = snap(560, 'alice', s.h)
    def draw(s, fr, t, d):
        fy, h, x = 1680, s.h, s.x; u = U('alice', h)
        keys = [(1.75, P(look=(-.2, 0), frown=0.)),
                (2.3, P(look=(-.1, .2), tilt=.03, frown=.05, grip={'L': (x - .38 * u, fy - 5.55 * u, 1.), 'R': (x + .3 * u, fy - 5.55 * u, 1.)}, tz=.55)),   # se acomoda las solapas
                (2.75, P(look=(-.1, .15), tilt=.02, frown=.05, grip={'L': (x - .36 * u, fy - 4.9 * u, 1.), 'R': (x + .28 * u, fy - 4.9 * u, 1.)}, tz=.55)),
                (3.25, P(look=(0, 0), frown=-.05, grip={'L': (x - .36 * u, fy - 4.9 * u, 0.), 'R': (x + .28 * u, fy - 4.9 * u, 0.)}, tz=.55)),
                (d, P(look=(.02, 0), frown=-.1))]
        if t < 1.55: walk(fr, 'alice', 1260, x, 0, 1.55, fy, h, t)
        elif t < 1.75:
            def fb(f_): p = RG.anim(keys, t); return RG.person_34(f_, 'alice', x, fy, h, p, t, feet=stance(x, u, fy), turn=-1)
            turn_blend(fr, (t - 1.55) / .2, lambda f_: walk(f_, 'alice', 1260, x, 0, 1.55, fy, h, 1.55), fb)
        else:
            p = RG.anim(keys, t); p['blink'] = blinkp(t, 6); RG.person_34(fr, 'alice', x, fy, h, p, t, feet=stance(x, u, fy), turn=-1)
        float_in(fr, s.card, 540, 330, t, .2)
        if t > s.w('empresaria') - .2: float_in(fr, s.t1, 540, 480, t, s.w('empresaria') - .2)
        if t > s.w('megaspeed') - .3: float_in(fr, s.t2, 540, 590, t, s.w('megaspeed') - .3)
        blit(fr, s.note, 540, 1765, ss(.6, 1.0, t)); blit(fr, s.note2, 540, 1810, ss(.6, 1.0, t))
    def cam(s, t, d): return lerp(1.1, 1.16, RG.ease(t / d)), 540, 1250, 0, 0

class Buyer(Sb):                                   # Alice revisa una tableta mientras entran cajas de chips al almacén
    def __init__(s):
        s.back, s.main = office(8); s.front = [(bokeh_layer(8, (255, 210, 150), 408, ymin=200, ymax=1200), 1.7)]
        s.panel = gold_panel('CLIENTE DE NVIDIA', w=700, h=160)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (600, 900), (1060, 1600), (40, 46, 56), -1); cv2.rectangle(fr, (660, 1080), (1000, 1600), (20, 22, 28), -1)
        cv2.putText(fr, 'MEGASPEED', (650, 980), cv2.FONT_HERSHEY_DUPLEX, 1.4, (200, 230, 255), 3, cv2.LINE_AA)
        for i in range(4):
            x = 1150 - ((t * 200 + i * 230) % 560); y = 1590
            if x < 650: continue
            cv2.rectangle(fr, (int(x - 60), int(y - 95)), (int(x + 60), int(y)), (176, 140, 90), -1); cv2.rectangle(fr, (int(x - 60), int(y - 95)), (int(x + 60), int(y)), (120, 90, 56), 4)
            gpu(fr, x, y - 48, .28, t)
        fy, h, x = 1690, 660, 300; u = U('alice', h)
        tl_ = [(0, P(look=(.1, .45), tilt=.05, frown=.25, grip={'L': (x - .2 * u, fy - 4.4 * u, 1.), 'R': (x + .75 * u, fy - 4.45 * u, 1.)}, tz=.95)),
               (1.4, P(look=(.1, .45), tilt=.05, frown=.3, grip={'L': (x - .2 * u, fy - 4.4 * u, 1.), 'R': (x + .75 * u, fy - 4.45 * u, 1.)}, tz=.95)),
               (1.9, P(look=(.5, -.05), tilt=-.02, frown=.1, grip={'L': (x - .2 * u, fy - 4.3 * u, 1.), 'R': (x + .75 * u, fy - 4.35 * u, 1.)}, tz=.95)),   # levanta la vista al almacén
               (d, P(look=(.5, -.05), frown=.05, grip={'L': (x - .2 * u, fy - 4.3 * u, 1.), 'R': (x + .75 * u, fy - 4.35 * u, 1.)}, tz=.95))]
        p = RG.anim(tl_, t); p['blink'] = blinkp(t, 7); hands, _ = RG.person_34(fr, 'alice', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        tablet(fr, hands, t); hands_on_top(fr, hands, 'alice', h)
        float_in(fr, s.panel, 540, 360, t, .2)
    def cam(s, t, d): return 1.1, 540, 1250, lerp(30, -30, RG.ease(t / d)), 0

class Suspicion(Sb):                               # el foco barre; Alice, de brazos cruzados, mira por encima del hombro
    def __init__(s):
        s.back = stage_bg(9, (8, 8, 16), (90, 90, 200)); s.main = floor_layer(1600, (14, 14, 22), (28, 28, 40))
        s.front = [(bokeh_layer(10, (160, 160, 255), 409, ymin=200, ymax=1500), 1.7)]
        s.panel = blue_panel('¿ALGO MÁS?', 'SOSPECHAS DE INTELIGENCIA', w=760, h=180); s.eye = emoji_sprite('👁️')
    def draw(s, fr, t, d):
        a_ = math.sin(t * 1.1) * .5; p_ = (540 + math.sin(a_) * 520, 1550)
        fbeam(fr, (540, 600), p_, 20, 230, (200, 220, 255), .16, 30); blit(fr, s.eye, 540, 620, 1, 1.2)
        fy, h, x = 1690, 680, 540; u = U('alice', h)
        cross = {'L': (x + .5 * u, fy - 4.75 * u, 1.), 'R': (x - .42 * u, fy - 4.55 * u, 1.)}
        keys = [(0, P(look=(.2, 0), frown=.1, grip={'L': cross['L'][:2] + (0.,), 'R': cross['R'][:2] + (0.,)}, tz=.7)),
                (.8, P(look=(.25, 0), frown=.15, grip=cross, tz=.7)),                                                  # cruza los brazos
                (2.0, P(look=(.3, 0), frown=.2, grip=cross, tz=.7)),
                (2.45, P(look=(-.95, .02), tilt=-.06, frown=.4, brow_asym=.35, boca='tensa', grip=cross, tz=.7)),       # mira por encima del hombro
                (3.6, P(look=(-.95, .02), tilt=-.06, frown=.42, brow_asym=.35, boca='tensa', grip=cross, tz=.7)),
                (4.1, P(look=(.15, 0), frown=.35, brow_asym=.2, grip=cross, tz=.7)), (d, P(look=(.1, 0), frown=.35, brow_asym=.2, grip=cross, tz=.7))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 8); RG.person_34(fr, 'alice', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): return lerp(1.1, 1.18, RG.ease(t / d)), 540, 1250, 0, 0

class Surveil(Sb):                                 # el agente frente a los monitores: se toca el auricular, se inclina y señala
    def __init__(s):
        bg = vgrad([(0, (8, 10, 14)), (1, (18, 22, 30))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1560, (20, 22, 28), (34, 36, 44))
        s.front = [(bokeh_layer(8, (120, 200, 255), 410, ymin=200, ymax=1200), 1.7)]
        s.panel = blue_panel('VIGILANCIA', 'SEGÚN INVESTIGACIONES PERIODÍSTICAS', w=900, h=180); s.rec = label('● REC', 30, (255, 70, 60))
    def draw(s, fr, t, d):
        for i in range(4):
            x, y = 70 + (i % 2) * 290, 600 + (i // 2) * 290
            cv2.rectangle(fr, (x, y), (x + 270, y + 250), (12, 14, 18), -1); cv2.rectangle(fr, (x + 10, y + 10), (x + 260, y + 240), (30, 60, 80), -1)
            RG.person(fr, 'alice' if i % 2 == 0 else 'figura', x + 135 + math.sin(t + i) * 40, y + 230, 190, P(look=(.2, 0), blink=blinkp(t, 20 + i)), t + i)
            for k in range(0, 230, 6): cv2.line(fr, (x + 10, y + 10 + k), (x + 260, y + 10 + k), (20, 40, 54), 1)
            if (t * 2) % 1 < .6 and i == 0: blit(fr, s.rec, x + 210, y + 34)
        fy, h, x = 1700, 700, 800; u = U('agente', h)
        ear = (x + .82 * u, fy - 6.95 * u); mon = (380, 900)
        keys = [(0, P(look=(-.5, -.1), frown=.3)),
                (.6, P(look=(-.5, -.1), frown=.3, grip={'R': ear + (0.,)}, tz=.3)),
                (1.2, P(look=(-.45, -.1), frown=.4, grip={'R': ear + (1.,)}, tz=.3, tilt=.06)),                    # se toca el auricular: escucha
                (2.4, P(look=(-.5, -.12), frown=.45, grip={'R': ear + (1.,)}, tz=.3, tilt=.06)),
                (2.9, P(look=(-.6, -.15), frown=.5, lean=-.07, grip={'R': ear + (0.,), 'L': mon + (.0,)}, tz=.3)),
                (3.5, P(look=(-.65, -.2), frown=.55, lean=-.08, grip={'L': mon + (1.,)}, tz=.2)),                  # se inclina y señala el monitor
                (d, P(look=(-.65, -.2), frown=.55, lean=-.08, grip={'L': mon + (1.,)}, tz=.2))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 9); RG.person_34(fr, 'agente', x, fy, h, p, t, feet=stance(x, u, fy), turn=-1)
        float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): return lerp(1.06, 1.12, RG.ease(t / d)), 540, 1180, 0, 0

class FBIWarn(Sb):                                 # el agente entrega la carpeta; los legisladores la abren y se miran
    def __init__(s):
        sky = vgrad([(0, (14, 20, 40)), (1, (40, 50, 80))]); i8 = to8(sky); capitol(i8, 540, 1300, 1.0, (120, 130, 156))
        s.back = [(dof(opaque(i8.astype(np.float32)), 3), .35)]; s.main = floor_layer(1450, (40, 40, 48), (56, 56, 66))
        s.front = [(bokeh_layer(10, (200, 220, 255), 412, ymin=200, ymax=1400), 1.7)]
        s.panel = blue_panel('ADVERTENCIA DEL FBI', 'CASI UN AÑO ANTES DEL ESCÁNDALO', w=900, h=180)
        s.fbi = N.text_sprite('FBI', 56, (255, 230, 120, 255), stroke=4, stroke_col=(0, 0, 0, 220), spacing=8)
    def draw(s, fr, t, d):
        fy = 1720; hA, xA = 620, 290; uA = U('agente', hA); hL, xL = 580, 690; uL_ = U('ejecutivo', hL); xJ = 900; uJ = U('jefe', 560)
        T1, T2, T3 = 1.0, 2.0, 2.4                                              # ofrece · el legislador la toma · el agente suelta
        hold = lambda cx, cy, w: {'L': (cx - w / 2, cy, 1.), 'R': (cx + w / 2, cy, 1.)}
        cA0 = (xA + .25 * uA, fy - 4.45 * uA); cX = ((xA + xL) / 2 + 20, fy - 4.6 * uA); cL1 = (xL - .2 * uL_, fy - 4.4 * uL_)
        k1 = RG.ease((t - T1) / (T2 - T1)); k3 = RG.ease((t - T3) / .5)
        if t < T1: fc = cA0
        elif t < T2: fc = (lerp(cA0[0], cX[0], k1), lerp(cA0[1], cX[1], k1))
        elif t < T3 + .2: fc = cX
        else: k = RG.ease((t - T3 - .2) / .5); fc = (lerp(cX[0], cL1[0], k), lerp(cX[1], cL1[1], k))
        wF = 140
        gA = hold(fc[0], fc[1], wF) if t < T3 else {kk: v[:2] + (1 - k3,) for kk, v in hold(cX[0], cX[1], wF).items()}
        pA = P(look=(.3 if t < 3 else .4, .1), frown=.35, grip=gA, tz=.9, blink=blinkp(t, 10))
        handsA, _ = RG.person_34(fr, 'agente', xA, fy, hA, pA, t, feet=stance(xA, uA, fy), turn=1)
        kr = RG.ease((t - (T2 - .6)) / .6)                                      # el legislador alcanza la carpeta
        gL = {kk: (v[0], v[1], kr) for kk, v in hold(fc[0], fc[1], wF).items()}
        worry = RG.ease((t - 3.4) / .5); look_each = RG.ease((t - 4.3) / .4)
        pL = P(look=(-.35 + .7 * look_each, .25 * (1 - look_each)), frown=.25 - .65 * worry, brow_up=.35 * worry, grip=gL, tz=.9, blink=blinkp(t, 11))
        handsL, _ = RG.person_34(fr, 'ejecutivo', xL, fy, hL, pL, t, feet=stance(xL, uL_, fy), turn=-1)
        pJ = P(look=(-.5 - .2 * look_each, .1), frown=.2 - .6 * worry, brow_up=.3 * worry, grip={'L': (xJ - .1 * uJ, fy - 6.3 * uJ, worry)}, tz=.4, blink=blinkp(t, 12))
        RG.person_34(fr, 'jefe', xJ, fy, 560, pJ, t, feet=stance(xJ, uJ, fy), turn=-1)
        hs = handsA if t < T3 + .2 else handsL
        if t >= T3 + .2 or t < T3 + .2:
            open_ = RG.ease((t - 3.0) / .4)
            paper(fr, hs, w_extra=36 + 70 * open_, h=150, col=(214, 196, 150), lines=open_ > .5)
            hands_on_top(fr, handsA if t < T3 else {}, 'agente', hA); hands_on_top(fr, handsL if t > T2 - .1 else {}, 'ejecutivo', hL)
        blit(fr, s.fbi, xA, 1790); float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): return lerp(1.1, 1.16, RG.ease(t / d)), 560, 1260, 0, 0

class Board(Sb):                                   # PLANO DE PRUEBA aprobado: Jensen recibe el expediente y se sorprende en «operación extranjera»
    def __init__(s):
        s.back, s.main = NV.office(31); s.front = [(bokeh_layer(8, (150, 240, 110), 431, ymin=200, ymax=1100), 1.7)]
        s.panel = gold_panel('INVESTIGACIÓN INDEPENDIENTE', '¿FUE OBJETIVO DE UNA OPERACIÓN EXTRANJERA?', w=960, h=180)
        s.hJ = 640; s.uJ = U('jensen', s.hJ); s.st = RG.step_len(s.uJ); s.x_stop = 4 * s.st; s.fy = 1640
        s.doc0 = A(545, 1352); s.cL0, s.cR0 = (490, 1352), (600, 1352); s.cL1, s.cR1 = (480, 1300), (590, 1300)
    def feet34(s, t, top):
        x, u = s.x_stop, s.uJ; L_, R_ = [x - .3 * u, s.fy], [x + .28 * u, s.fy]
        q = min(1., max(0., (t - (top + .02)) / .3))
        if q > 0: e = RG.ease(q); R_ = [x + .28 * u - .3 * u * e, s.fy - 4 * e - math.sin(math.pi * q) * .25 * u]
        return {'L': tuple(L_), 'R': tuple(R_)}
    def draw(s, fr, t, d):
        top = s.w('operación'); cL0, cR0, cL1, cR1 = s.cL0, s.cR0, s.cL1, s.cR1; TS = 1.5
        keys = [(TS, P(look=(.15, .1), frown=.1)), (TS + .3, P(look=(.25, .35), tilt=.05, frown=.15)),
                (TS + .55, P(look=(.25, .45), tilt=.06, lean=.04, frown=.2, grip={'L': cL0 + (0.,), 'R': cR0 + (0.,)})),
                (TS + 1.0, P(look=(.2, .5), tilt=.06, lean=.08, frown=.25, sh=.1, grip={'L': cL0 + (1.,), 'R': cR0 + (1.,)})),
                (TS + 1.5, P(look=(.1, .4), tilt=.03, frown=.35, grip={'L': cL1 + (1.,), 'R': cR1 + (1.,)})),
                (top - .08, P(look=(.1, .42), tilt=.03, frown=.4, sh=.12, grip={'L': (cL1[0], cL1[1] + 6, 1.), 'R': (cR1[0], cR1[1] + 6, 1.)})),
                (top + .22, P(look=(0., -.1), tilt=-.04, lean=-.07, hip_dx=-.14, sh=-.55, brow_up=.95, boca='o', frown=-.1, grip={'L': (cL1[0] - 6, cL1[1] - 12, 1.), 'R': (cR1[0] - 6, cR1[1] - 12, 1.)})),
                (top + .75, P(look=(-.05, 0.), tilt=-.02, lean=-.04, hip_dx=-.12, sh=-.3, brow_up=.6, boca='o', frown=-.3, grip={'L': (cL1[0] - 4, cL1[1] - 8, 1.), 'R': (cR1[0] - 4, cR1[1] - 8, 1.)})),
                (max(d, top + 1.2), P(look=(-.25, .1), tilt=.02, lean=-.02, hip_dx=-.1, sh=-.05, brow_up=.3, boca='triste', frown=-.55, grip={'L': (cL1[0], cL1[1] + 10, 1.), 'R': (cR1[0], cR1[1] + 10, 1.)}))]
        fbeam(fr, (640, 700), (640, 1400), 30, 420, (255, 240, 200), .10, 40)
        react = RG.ease((t - (top + .25)) / .6)
        for i, (x, w_) in enumerate(((730, 'directora'), (850, 'ejecutivo'))):
            look_j = RG.ease((t - .8 - i * .15) / .5); u = 470 * RG.CAST[w_]['alto'] / 8.; idle = math.sin(t * 1.3 + i * 2.1)
            g = {'R': (x + .1 * u, 1420 - 4.9 * u, react)} if i == 0 else {'L': (x - .15 * u, 1420 - 6.35 * u, react)}
            pose = P(look=(-.35 * look_j, .05 + .05 * react), frown=.25 - .5 * react, brow_up=.8 * react, sh=-.3 * react, lean=-.05 * react + .015 * idle,
                     hip_dx=.05 * math.sin(t * .7 + i), uL=-.1 + .05 * idle, uR=.1 - .05 * idle, lL=.08 + .06 * idle, lR=-.08 - .06 * idle,
                     boca='o' if (i == 1 and .3 < react < .9) else 'neutra', grip=g, tz=.9, blink=blinkp(t, 3 + i))
            RG.person_34(fr, w_, x, 1420, 470, pose, t + i, turn=-1)
        poly(fr, [(380, 1318), (1060, 1318), (1080, 1400), (360, 1400)], (74, 50, 34)); poly(fr, [(360, 1400), (1080, 1400), (1080, 1424), (360, 1424)], (46, 30, 20))
        for x in (390, 1040): cv2.rectangle(fr, (x - 12, 1424), (x + 12, 1560), (40, 26, 18), -1)
        cv2.ellipse(fr, (720, 1360), (300, 30), 0, 0, 360, (96, 70, 48), -1, cv2.LINE_AA)
        x0 = s.x_stop - 4 * s.st; hands = None
        def j34(f_):
            p = RG.anim(keys, t); p['blink'] = 0. if top - .1 < t < top + .6 else blinkp(t, 5)
            return RG.person_34(f_, 'jensen', s.x_stop, s.fy, s.hJ, p, t, feet=s.feet34(t, top), turn=1)[0]
        if t < TS - .2: walk(fr, 'jensen', x0, s.x_stop, 0, TS - .2, s.fy, s.hJ, t)
        elif t < TS: hands = turn_blend(fr, (t - TS + .2) / .2, lambda f_: walk(f_, 'jensen', x0, s.x_stop, 0, TS - .2, s.fy, s.hJ, TS - .2), j34)
        else: hands = j34(fr)
        lift = RG.ease((t - (TS + 1.0)) / .5) if t > TS + 1.0 else 0.
        if t < TS + 1.0 or not hands: c = s.doc0; w, h_, up = 120, 28, 0.
        else: c = (A(*hands['L']) + A(*hands['R'])) / 2; w = abs(hands['R'][0] - hands['L'][0]) + 40; h_ = 28 + 118 * lift; up = lift
        x0_, x1_ = c[0] - w / 2, c[0] + w / 2; yb = c[1] + 14 * (1 - up) + 46 * up; yt = yb - h_; sk = 14 * (1 - up)
        poly(fr, [(x0_ + sk, yt), (x1_ - sk, yt), (x1_, yb), (x0_, yb)], (236, 228, 206)); pline(fr, [(x0_ + sk, yt), (x1_ - sk, yt), (x1_, yb), (x0_, yb)], (170, 160, 130), 2, True)
        if up > .3:
            for i in range(4): cv2.rectangle(fr, (int(x0_ + 14), int(yt + 22 + i * 24)), (int(x1_ - 14 - (i % 2) * 30), int(yt + 34 + i * 24)), (14, 14, 16) if i % 2 else (120, 110, 90), -1)
            cv2.putText(fr, 'CONFIDENCIAL', (int(x0_ + 10), int(yt + 16)), cv2.FONT_HERSHEY_DUPLEX, .45, (200, 40, 40), 1, cv2.LINE_AA)
        if hands and t >= TS + .55: hands_on_top(fr, hands, 'jensen', s.hJ)
        float_in(fr, s.panel, 540, 330, t, .3)
    def cam(s, t, d): return lerp(1.34, 1.44, RG.ease(t / d)), lerp(430, 560, RG.ease(t / 2.4)), 1250, 0, 0

class Statement(Sb):                               # Colette lee el comunicado en un atril y levanta la vista
    def __init__(s):
        bg = vgrad([(0, (8, 14, 10)), (1, (18, 30, 22))]); radial(bg, (540, 900), 600, (90, 200, 80), .2); s.back = [(dof(opaque(bg), 2), .2)]
        s.main = floor_layer(1600, (16, 24, 18), (30, 44, 32)); s.front = [(bokeh_layer(8, (150, 240, 110), 419, ymin=200, ymax=1500), 1.7)]
        s.head = N.text_sprite('COMUNICADO DE NVIDIA', 40, (30, 60, 30, 255), pad=6, spacing=4)
        s.q = [N.text_sprite(x, 34, (30, 30, 34, 255), pad=6) for x in ('«NO HAY MOTIVOS PARA CREER QUE', 'SE COMPROMETIERAN SECRETOS', 'NI LA SEGURIDAD NACIONAL»')]
    def draw(s, fr, t, d):
        k = ss(0, .5, t); y = lerp(-200, 360, eOut(k))                         # el comunicado, arriba
        cv2.rectangle(fr, (150, int(y - 170)), (930, int(y + 170)), (240, 240, 232), -1); cv2.rectangle(fr, (150, int(y - 170)), (930, int(y - 110)), GREEN, -1)
        blit(fr, s.head, 540, y - 140)
        for i, q in enumerate(s.q): blit(fr, q, 540, y - 50 + i * 56, ss(.5 + i * .3, .8 + i * .3, t))
        fy, h, x = 1700, 700, 540; u = U('colette', h); tc = s.w('comprometidos')
        hold = {'L': (x - .5 * u, fy - 4.75 * u, 1.), 'R': (x + .5 * u, fy - 4.75 * u, 1.)}
        keys = [(0, P(look=(0, .45), tilt=.05, frown=.2, grip=hold, tz=.9)), (2.5, P(look=(-.05, .5), tilt=.06, frown=.25, grip=hold, tz=.9)),
                (4.2, P(look=(.05, .45), tilt=.05, frown=.25, grip=hold, tz=.9)),
                (tc - .2, P(look=(0, .4), tilt=.04, frown=.25, grip=hold, tz=.9)), (tc + .3, P(look=(0, 0), tilt=0., frown=.15, grip=hold, tz=.9)),   # levanta la vista
                (d, P(look=(0, 0), frown=.1, grip=hold, tz=.9))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 13)
        hands, _ = RG.person(fr, 'colette', x, fy, h, p, t, feet=stance(x, u, fy, .36))
        paper(fr, hands, w_extra=50, h=150); hands_on_top(fr, hands, 'colette', h)
        mic_podium(fr, 540, 1560, seal_col=(150, 240, 90), body=(24, 40, 28))
    def cam(s, t, d): return lerp(1.04, 1.1, RG.ease(t / d)), 540, 1150, 0, 0

class Investors(Sb):                               # la gráfica cae; los inversionistas pasan de la atención a la preocupación
    def __init__(s):
        bg = vgrad([(0, (14, 8, 8)), (1, (30, 16, 16))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1600, (24, 18, 18), (40, 30, 30))
        s.front = [(bokeh_layer(10, (255, 120, 100), 420, ymin=200, ymax=1400), 1.7)]
        s.panel = red_panel('CONFIANZA GOLPEADA', w=760, h=160); s.lab = label('INVERSIONISTAS', 34, (255, 210, 200))
        r_ = np.random.RandomState(4); v = 0; s.pts = []
        for i in range(60): v += r_.normal(0, 1) - (2.2 if 30 < i < 44 else 0); s.pts.append(v)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (90, 520), (990, 1080), (12, 10, 12), -1); cv2.rectangle(fr, (90, 520), (990, 1080), (90, 60, 60), 4)
        n = int(2 + ss(.1, d * .8, t) * 58); mn, mx = min(s.pts), max(s.pts)
        q = [(120 + i * 14.5, 1050 - (p - mn) / (mx - mn + 1e-9) * 480) for i, p in enumerate(s.pts[:n])]
        pline(fr, q, (255, 70, 60) if n > 34 else (120, 240, 140), 6)
        tg = s.w('golpeó'); wk = RG.ease((t - tg) / .6); fy = 1760
        for i, (x, w_, gesture) in enumerate(((240, 'ejecutivo', 'frente'), (540, 'directora', 'pecho'), (840, 'jefe', 'cruza'))):
            h = 520; u = U(w_, h); d_ = RG.ease((t - tg - i * .15) / .6)        # cada uno reacciona con un pequeño desfase
            if gesture == 'frente': g = {'R': (x + .3 * u, fy - 7.0 * u, d_)}; tz = .5
            elif gesture == 'pecho': g = {'L': (x - .05 * u, fy - 4.9 * u, d_)}; tz = .9
            else: g = {'L': (x + .5 * u, fy - 4.75 * u, d_), 'R': (x - .42 * u, fy - 4.55 * u, d_)}; tz = .7
            p = P(look=(0, -.35 + .5 * d_), frown=.1 - .6 * d_, brow_up=.3 * d_, boca='triste' if d_ > .5 else 'neutra', sh=-.15 * d_, grip=g, tz=tz, blink=blinkp(t, 14 + i),
                  hip_dx=.04 * math.sin(t * .8 + i))
            RG.person(fr, w_, x, fy, h, p, t + i, feet=stance(x, u, fy, .36))
        blit(fr, s.lab, 540, 1820); float_in(fr, s.panel, 540, 340, t, .2)

class Lawmakers(Sb):                               # estrado: uno señala, otra gesticula, otro cruza los brazos; Jensen baja la cabeza
    def __init__(s):
        wall = vgrad([(0, (40, 26, 20)), (1, (70, 46, 32))]); i8 = to8(wall); DT.flag_us(i8, 60, 300, 260, 160); DT.flag_us(i8, 760, 300, 260, 160)
        s.back = [(dof(opaque(i8.astype(np.float32)), 2), .3)]; s.main = floor_layer(1560, (36, 28, 24), (50, 40, 34))
        s.front = [(bokeh_layer(8, (255, 220, 170), 423, ymin=200, ymax=1000), 1.7)]
        s.panel = red_panel('EXIGEN EXPLICACIONES', w=820, h=160)
    def draw(s, fr, t, d):
        fyD = 1140
        for i, (x, w_) in enumerate(((200, 'ejecutivo'), (540, 'directora'), (880, 'jefe'))):
            h = 380; u = U(w_, h)
            if i == 0: g = {'R': (x + 2.1 * u, fyD - 3.9 * u, RG.ease(t / .6))}; tz = .5          # señala hacia Jensen
            elif i == 1: g = {'R': (x + 1.0 * u + math.sin(t * 5) * .35 * u, fyD - 4.6 * u - abs(math.sin(t * 5)) * .25 * u, RG.ease(t / .5))}; tz = .7   # gesticula
            else: g = {'L': (x + .5 * u, fyD - 4.75 * u, 1.), 'R': (x - .42 * u, fyD - 4.55 * u, 1.)}; tz = .7
            RG.person(fr, w_, x, fyD, h, P(look=(0, .4), frown=.5, grip=g, tz=tz, blink=blinkp(t, 15 + i), hip_dx=.03 * math.sin(t + i)), t + i, feet=stance(x, u, fyD, .36))
        cv2.rectangle(fr, (0, 1000), (W, 1160), (100, 66, 40), -1); cv2.rectangle(fr, (0, 990), (W, 1010), (160, 120, 66), -1)
        te = s.w('nvidia') if False else T('envidia', s.a - .6) - s.a; dn = RG.ease((t - te) / .5)
        fy, h, x = 1780, 560, 540; u = U('jensen', h)
        p = P(look=(.1, -.4 + .85 * dn), tilt=.08 * dn, frown=-.1 - .4 * dn, boca='triste' if dn > .5 else 'neutra', sh=.15 * dn, blink=blinkp(t, 18))
        RG.person_34(fr, 'jensen', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        float_in(fr, s.panel, 540, 340, t, .2)

class Beijing(Sb):                                 # el portavoz niega con la mano y la cabeza
    def __init__(s):
        bg = vgrad([(0, (40, 8, 8)), (1, (70, 16, 14))]); i8 = to8(bg); flag_cn(i8, 150, 420, 780, 520)
        s.back = [(dof(opaque(i8.astype(np.float32)), 5), .3)]; s.main = floor_layer(1500, (40, 14, 14), (60, 24, 22))
        s.front = [(bokeh_layer(10, (255, 220, 120), 424, ymin=200, ymax=1400), 1.7)]
        s.st = N.stamp('RECHAZA LAS ACUSACIONES', (255, 59, 42), w=920, h=124, px=58); s.lab = label('PORTAVOZ DE LA CANCILLERÍA CHINA', 28, (255, 230, 200))
    def draw(s, fr, t, d):
        fy, h, x = 1560, 560, 540; u = U('portavoz', h); tr = s.w('rechazó')
        neg = RG.ease((t - (tr - .3)) / .4) * (1 - RG.ease((t - (tr + 1.8)) / .4)); osc = math.sin((t - tr) * 2 * math.pi * 1.5)
        g = {'R': (x + 1.1 * u + osc * .35 * u * neg, fy - 4.7 * u, .3 + .7 * neg)}
        p = P(look=(.12 * osc * neg, 0), frown=.45, boca='tensa' if neg > .5 else 'neutra', grip=g, tz=.6, blink=blinkp(t, 19))
        RG.person(fr, 'portavoz', x, fy, h, p, t, feet=stance(x, u, fy, .36))
        mic_podium(fr, 540, 1330, seal_col=(255, 210, 60), body=(90, 20, 20)); blit(fr, s.lab, 540, 1640)
        stamp_in(fr, s.st, 540, 380, t, max(.3, tr - .1))

class Resign(Sb):                                  # Jensen deja el gafete y sale caminando; Colette entra y asume
    def __init__(s):
        s.back, s.main = office(25); s.front = [(bokeh_layer(10, (150, 240, 110), 425, ymin=200, ymax=1300), 1.7)]
        s.golpe = N.text_sprite('OTRO GOLPE', 110, (255, 236, 220, 255), glow=(255, 60, 40), glow_r=16, stroke=4, stroke_col=(0, 0, 0, 200))
        s.date = N.stamp('12 NOV 2026', (255, 59, 42), w=520, h=110, px=60); s.res = label('JENSEN HUANG RENUNCIA', 40, (255, 220, 210))
        s.card = green_panel('COLETTE KRESS', 'DIRECTORA EJECUTIVA INTERINA', w=820, h=180)
        s.hJ = 640; s.xJ = snap(560, 'jensen', s.hJ); s.hC = 620; s.xC = snap(700, 'colette', s.hC)
    def draw(s, fr, t, d):
        tg, tr, tc = s.w('golpe'), s.w('renunció'), s.w('colette'); fy = 1700; uJ = U('jensen', s.hJ); xJ = s.xJ
        poly(fr, [(80, 1420), (520, 1420), (540, 1470), (60, 1470)], (74, 50, 34)); cv2.rectangle(fr, (60, 1470), (540, 1490), (46, 30, 20), -1)   # mesa
        for xx in (80, 520): cv2.rectangle(fr, (xx - 10, 1490), (xx + 10, 1610), (40, 26, 18), -1)
        badge_t = (430, 1440); t_put, t_turn, t_walk = tr + .1, tr + 1.0, tr + 1.25
        keys = [(0, P(look=(-.2, .1), frown=-.3, boca='triste', grip={'R': (xJ - .1 * uJ, fy - 5.0 * uJ, 1.)}, tz=.9)),           # gafete en la mano, a la altura del pecho
                (t_put - .5, P(look=(-.3, .3), frown=-.35, boca='triste', grip={'R': (xJ - .1 * uJ, fy - 5.0 * uJ, 1.)}, tz=.9)),
                (t_put, P(look=(-.35, .45), tilt=.05, lean=-.05, frown=-.4, boca='triste', grip={'R': badge_t + (1.,)}, tz=.9)),    # lo deja sobre la mesa
                (t_put + .35, P(look=(-.35, .4), tilt=.04, lean=-.04, frown=-.4, boca='triste', grip={'R': badge_t + (1.,)}, tz=.9)),
                (t_turn, P(look=(-.5, .1), frown=-.4, boca='triste', grip={'R': badge_t + (0.,)}, tz=.9))]
        badge_on_table = t > t_put + .1
        def jJ(f_):
            p = RG.anim(keys, t); p['blink'] = blinkp(t, 21)
            return RG.person_34(f_, 'jensen', xJ, fy, s.hJ, p, t, feet=stance(xJ, uJ, fy), turn=-1)[0]
        hands = None
        if t < t_turn: hands = jJ(fr)
        elif t < t_turn + .2: turn_blend(fr, (t - t_turn) / .2, jJ, lambda f_: walk(f_, 'jensen', xJ, xJ - 900, t_walk, t_walk + 2.2, fy, s.hJ, t_walk, mode='sale'))
        elif t < t_walk + 2.2: walk(fr, 'jensen', xJ, xJ - 900, t_walk, t_walk + 2.2, fy, s.hJ, max(t, t_walk), mode='sale')
        bx, by = (badge_t if badge_on_table else (hands['R'] if hands else badge_t))
        cv2.rectangle(fr, (int(bx - 26), int(by - 18)), (int(bx + 26), int(by + 18)), (236, 236, 240), -1); cv2.rectangle(fr, (int(bx - 26), int(by - 18)), (int(bx + 26), int(by - 8)), GREEN, -1)
        if hands and not badge_on_table: hands_on_top(fr, {'R': hands['R']}, 'jensen', s.hJ)
        uC = U('colette', s.hC); ca, cb = tc - 1.6, tc - .1                   # Colette entra caminando, se detiene, gira y asiente
        nod = math.sin((t - cb - .5) * 2 * math.pi * 1.2) * .06 * (1 - RG.ease((t - cb - 1.4) / .4)) if t > cb + .5 else 0
        kC = [(cb + .2, P(look=(-.3, 0), frown=-.1)), (cb + .6, P(look=(-.1, 0), frown=-.15, boca='sonrisa')), (d, P(look=(-.05, 0), frown=-.15, boca='sonrisa'))]
        def jC(f_): p = RG.anim(kC, t); p['tilt'] = nod; p['blink'] = blinkp(t, 22); return RG.person_34(f_, 'colette', s.xC, fy, s.hC, p, t, feet=stance(s.xC, uC, fy), turn=-1)
        if ca < t < cb: walk(fr, 'colette', 1300, s.xC, ca, cb, fy, s.hC, t)
        elif cb <= t < cb + .2: turn_blend(fr, (t - cb) / .2, lambda f_: walk(f_, 'colette', 1300, s.xC, ca, cb, fy, s.hC, cb), jC)
        elif t >= cb + .2: jC(fr)
        if t < tr + .2: blit(fr, s.golpe, 540, 400, ss(tg - .2, tg + .1, t) * (1 - ss(tr - .3, tr, t)), lerp(1.4, 1, ss(tg - .2, tg + .1, t)))
        if t > s.w('12') - .3: stamp_in(fr, s.date, 540, 560, t, s.w('12') - .3)
        if t > tr: blit(fr, s.res, 540, 700, ss(tr, tr + .3, t) * (1 - ss(tc - .3, tc, t)))
        if t > tc: float_in(fr, s.card, 540, 360, t, tc)
    def cam(s, t, d): return lerp(1.06, 1.12, RG.ease(t / d)), 540, 1250, 0, 0

class Close(Sb):                                   # Jensen frente a la silueta; la silueta se gira hacia él
    def __init__(s):
        s.back = stage_bg(27, (8, 10, 14), (90, 200, 80)); s.main = floor_layer(1600, (16, 20, 18), (30, 40, 32))
        s.front = [(bokeh_layer(12, (150, 240, 110), 427, ymin=200, ymax=1500), 1.7)]
        s.q = N.text_sprite('?', 240, (255, 230, 120, 255), glow=(255, 160, 40), glow_r=22)
        s.panel = gold_panel('¿TÚ QUÉ CREES?', 'TE LEO EN COMENTARIOS', w=780, h=190)
        s.a1 = chip('¿OPERACIÓN DE ESPIONAJE?', (255, 140, 120), w=700); s.a2 = chip('¿FALTA LA VERDADERA HISTORIA?', (150, 200, 255), w=760)
        s.pill = DT.Blockade(None, cta=True)
    def draw(s, fr, t, d):
        fy = 1660; uJ = U('jensen', 560); uF = U('figura', 540); tt = s.w('todavía')
        pJ = P(look=(.35, 0), frown=.1 - .3 * RG.ease((t - tt) / .5), brow_asym=.35 * RG.ease((t - 1.5) / .6), brow_up=.4 * RG.ease((t - tt - .3) / .5), blink=blinkp(t, 23))
        RG.person_34(fr, 'jensen', 280, fy, 560, pJ, t, feet=stance(280, uJ, fy), turn=1)
        fF0 = lambda f_: RG.person_34(f_, 'figura', 820, fy, 540, P(look=(.4, 0)), t, feet=stance(820, uF, fy), turn=1)    # de espaldas a Jensen
        fF1 = lambda f_: RG.person_34(f_, 'figura', 820, fy, 540, P(look=(-.4, 0)), t, feet=stance(820, uF, fy), turn=-1)  # se gira hacia él
        if t < tt: fF0(fr)
        elif t < tt + .25: turn_blend(fr, (t - tt) / .25, fF0, fF1)
        else: fF1(fr)
        blit(fr, s.q, 550, 1000, ss(.2, .6, t), 1 + .06 * math.sin(t * 4))
        float_in(fr, s.a1, 540, 560, t, .4)
        if t > tt - .2: float_in(fr, s.a2, 540, 690, t, tt - .2)
        if t > s.w('te') - .3: float_in(fr, s.panel, 540, 340, t, s.w('te') - .3)
        k = ss(s.w('te'), s.w('te') + .4, t)
        if k > 0: blit(fr, s.pill.ctaspr, 540, 1750, k, lerp(.6, 1, eBack(k)) * .8); blit(fr, s.pill.bell, 860, 1730 + math.sin(t * 9) * 4, k, .5)
    def cam(s, t, d): return lerp(1.06, 1.12, RG.ease(t / d)), 540, 1250, 0, 0

# ================================================================ línea de tiempo (mismos cortes que v1, con los tiempos de la voz nueva)
def tl():
    seq = [
        (0, NV.Scandal(), 0), (T('su') - .25, Relation(), 0), (T('y', 11) - .25, NV.Secrets(), 0),
        (NV.SC_T[1], JensenIntro(), 1), (T('la', 22) - .25, NV.ChipsAI(), 1), (T('la', 26.5) - .25, AliceIntro(), 1), (T('compañía', 32) - .3, NV.DataCenter(), 1),
        (T('megaspeed', 35) - .25, Buyer(), 1), (T('pero', 39) - .25, Suspicion(), 1),
        (NV.SC_T[2], Surveil(), 4), (T('mediante') - .25, NV.Intercept(), 4), (T('el', 57.5) - .25, FBIWarn(), 4), (T('después') - .25, NV.Photos(), 2),
        (T('la', 69.5) - .25, NV.NatSec(), 4), (T('pero', 73.5) - .25, NV.Classified(), 4),
        (NV.SC_T[3], NV.Problem(), 3), (T('sus', 84) - .25, NV.ExportWall(), 3), (T('la', 95) - .25, Board(), 2), (T('la', 100.8) - .25, Statement(), 1),
        (T('sin', 108.5) - .25, Investors(), 3),
        (NV.SC_T[4], NV.Capitol(), 1), (T('la', 115) - .25, NV.Questions(), 1), (T('legisladores', 123) - .25, Lawmakers(), 2), (T('mientras') - .25, Beijing(), 3),
        (NV.SC_T[5], Resign(), 3), (T('el', 140.5) - .25, NV.Infidelity(), 4),
        (NV.SC_T[6], Close(), 4),
    ]
    out = []
    for i, (a, sc, g) in enumerate(seq):
        b = seq[i + 1][0] if i + 1 < len(seq) else NV.DUR; sc.a = a; out.append((a, b, sc, g))
    return out

def make_frame():
    NV.TR.DUR = NV.DUR
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in NV.TR.build_subs(WDISP)]
    shots = tl(); pill = DT.Blockade(None, cta=True); C0, C1 = T('según', 44) - 1.0, T('pekín') + 1.0
    def one(i, T_):
        a, b, sc, g = shots[i]; CTX['shot'] = i; CTX['counts'] = {}
        return cinema(render3d(sc, T_ - a, b - a, T_), g, T_)
    def frame(T_, f=-1, rec=False):
        CTX['f'], CTX['rec'] = f, rec
        i = max(k for k, s_ in enumerate(shots) if T_ >= s_[0] - 1e-6)
        fr = one(i, T_); a = shots[i][0]
        if i > 0 and T_ - a < .3: CTX['rec'] = False; fr = cv2.addWeighted(one(i - 1, T_), 1 - ss(0, .3, T_ - a), fr, ss(0, .3, T_ - a), 0)
        clean = fr.copy()
        c = ss(C0, C0 + .4, T_) * (1 - ss(C1 - .3, C1, T_))
        if c > 0: blit(fr, pill.ctaspr, 760, 1720, c, lerp(.6, 1, eBack((T_ - C0) / .4)) * .6); blit(fr, pill.bell, 1010, 1700 + math.sin(T_ * 9) * 4, c, .4)
        draw_overlays(fr, T_, subs, []); return fr, clean, i
    return frame, shots

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'info'
    frame, shots = make_frame()
    if mode == 'info':
        for i, (a, b, sc, g) in enumerate(shots): print(f'{i:2d} {a:6.2f}-{b:6.2f} {b - a:5.2f} {type(sc).__name__}')
    elif mode == 'test':
        os.makedirs(f'{OUT2}/test', exist_ok=True)
        for T_ in [float(x) for x in sys.argv[2:]]: cv2.imwrite(f'{OUT2}/test/n_{T_:06.2f}.jpg', cv2.resize(frame(T_)[0], (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1])
    elif mode in ('seg', 'qcshot'):
        if mode == 'seg': f0, f1 = int(sys.argv[2]), int(sys.argv[3]); tag = f'{f0:05d}'
        else: i = int(sys.argv[2]); f0, f1 = int(math.ceil(shots[i][0] * FPS)), int(math.ceil(shots[i][1] * FPS)); tag = f'shot{i:02d}'
        os.makedirs(f'{OUT2}/thumbs', exist_ok=True)
        p = None
        if mode == 'seg':
            p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', f'{OUT2}/seg_{f0:05d}.mp4'], stdin=subprocess.PIPE)
        diffs = {}; prev = None
        if f0 > 0: prev = cv2.resize(frame((f0 - 1) / FPS)[1], (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)   # fotograma anterior: continuidad entre segmentos
        CTX['log'] = []
        for f in range(f0, f1):
            fr, clean, si = frame(f / FPS, f, True)
            small = cv2.resize(clean, (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
            if prev is not None: diffs[f] = float(np.abs(small - prev).mean())
            prev = small
            if f % 3 == 0: cv2.imwrite(f'{OUT2}/thumbs/t_{f:05d}.jpg', cv2.resize(clean, (180, 320), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 80])
            if p: p.stdin.write(np.ascontiguousarray(fr).tobytes())
        if p: p.stdin.close(); p.wait()
        json.dump(dict(log=CTX['log'], diffs=diffs, f0=f0, f1=f1), open(f'{OUT2}/qc_{tag}.json', 'w'))
        print('SEG' if mode == 'seg' else 'QCSHOT', f0, f1, flush=True)
    elif mode == 'audio':
        subprocess.run(['cp', f'{NV.OUT}/audio.wav', f'{OUT2}/audio_prev.wav'], check=False); NV.synth_audio(f'{OUT2}/audio.wav'); print('audio ok')

if __name__ == '__main__': main()
