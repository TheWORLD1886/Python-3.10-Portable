#!/usr/bin/env python3
# Short: ¿QUÉ PASARÍA SI INTERNET DESAPARECIERA MAÑANA? · escenario hipotético · 1080x1920 · 30 fps.
# Personajes del rig compartido con actuación (caminar, tomar objetos, reaccionar) y registro de articulaciones por fotograma
# (mismo sistema de control de calidad que NVIDIA v2). Sin cifras: el guion no las usa.
import os, sys, json, math, subprocess
HERE_I = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE_I, '..', 'nvidia'))
import nvidia2 as N2
from nvidia2 import *                         # rig con registro automático, helpers de actuación y de escenario
NV = N2.NV; RG = N2.RG; CTX = N2.CTX
OUTI = os.path.join(HERE_I, 'out'); os.makedirs(OUTI, exist_ok=True)
WORDS = json.load(open(os.path.join(HERE_I, 'words.json'))); VOZ = os.path.join(HERE_I, 'voz.mp3')
_clean = NV._clean
def T(word, after=-1.):
    for w in WORDS:
        if w[1] >= after and _clean(w[0]).startswith(word.lower()): return w[1]
    raise KeyError(word)
DUR = int(math.ceil(WORDS[-1][2] + 2.2))
SC_T = [0, T('millones') - .3, T('las', 35) - .3, T('y', 55) - .3, T('porque', 77) - .3, T('y', 94) - .3, DUR]
class Si(NV.Shot):
    a = 0.
    def w(s, word, after=None): return T(word, s.a - .6 if after is None else s.a + after) - s.a
P, U, walk, stance, turn_blend, hands_on_top, blinkp = N2.P, N2.U, N2.walk, N2.stance, N2.turn_blend, N2.hands_on_top, N2.blinkp
HIPO = None
def hipo_label():
    global HIPO
    if HIPO is None: HIPO = label('ESCENARIO HIPOTÉTICO', 26, (255, 230, 170))
    return HIPO

# ---------------------------------------------------------------- escenarios y utilería
def street_bg(seed=1, col=(30, 32, 44), sky=((10, 12, 24), (40, 34, 52))):
    s_ = vgrad([(0, sky[0]), (1, sky[1])]); back = [(dof(opaque(s_), 2), .1)]
    city = np.zeros((H, W, 3), np.uint8); r_ = np.random.RandomState(seed); x = -20
    while x < W:
        bw, bh = r_.randint(110, 200), r_.randint(300, 700); cv2.rectangle(city, (x, 1260 - bh), (x + bw, 1270), col, -1)
        for wy in range(1260 - bh + 20, 1250, 36):
            for wx in range(x + 12, x + bw - 16, 28):
                if r_.rand() < .12: cv2.rectangle(city, (wx, wy), (wx + 12, wy + 16), (255, 190, 120), -1)
        x += bw + r_.randint(4, 12)
    back.append((dof(haze(rgba(city, np.any(city > 0, 2).astype(np.float32)), sky[1], .3), 2), .45))
    return back, floor_layer(1270, (34, 34, 40), (46, 46, 54))
def room_bg(wall=(40, 46, 64), floor=(70, 52, 40), seed=1):
    w_ = vgrad([(0, wall), (1, tuple(int(c * .7) for c in wall))]); i8 = to8(w_)
    for x in range(0, W, 70): cv2.line(i8, (x, 0), (x, 1300), tuple(int(c * 1.1) for c in wall), 2)
    cv2.rectangle(i8, (0, 1290), (W, 1330), tuple(int(c * .6) for c in wall), -1)
    return [(dof(opaque(i8.astype(np.float32)), 2.5), .4)], floor_layer(1330, floor, tuple(int(c * 1.2) for c in floor))
def screen(fr, x, y, w, h, title, col=(255, 70, 60), bg=(14, 18, 26), sub=None, icon='x'):
    cv2.rectangle(fr, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), (30, 32, 40), -1)
    cv2.rectangle(fr, (int(x - w / 2 + 8), int(y - h / 2 + 8)), (int(x + w / 2 - 8), int(y + h / 2 - 8)), bg, -1)
    if icon == 'x':
        r = min(w, h) * .16; line(fr, (x - r, y - h * .18 - r), (x + r, y - h * .18 + r), col, max(3, int(r * .25))); line(fr, (x + r, y - h * .18 - r), (x - r, y - h * .18 + r), col, max(3, int(r * .25)))
    elif icon == 'wifi':
        for k in range(3): cv2.ellipse(fr, (int(x), int(y - h * .05)), (int((k + 1) * w * .09), int((k + 1) * w * .09)), 0, 225, 315, col, max(2, int(w * .02)), cv2.LINE_AA)
        line(fr, (x - w * .2, y - h * .3), (x + w * .2, y + h * .05), (255, 70, 60), max(3, int(w * .025)))
    fs = max(.35, w / 520.); (tw, th), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, fs, 1)
    if tw > w - 24: fs *= (w - 24) / tw; (tw, th), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, fs, 1)
    cv2.putText(fr, title, (int(x - tw / 2), int(y + h * .28)), cv2.FONT_HERSHEY_DUPLEX, fs, col, max(1, int(fs * 2)), cv2.LINE_AA)
    if sub:
        fs2 = fs * .7; (tw2, _), _ = cv2.getTextSize(sub, cv2.FONT_HERSHEY_DUPLEX, fs2, 1)
        cv2.putText(fr, sub, (int(x - tw2 / 2), int(y + h * .42)), cv2.FONT_HERSHEY_DUPLEX, fs2, (200, 210, 220), 1, cv2.LINE_AA)
def handphone(fr, hd, lit=True, title='SIN CONEXIÓN'):
    x, y = hd[0], hd[1] - 36; cv2.rectangle(fr, (int(x - 22), int(y - 40)), (int(x + 22), int(y + 40)), (20, 22, 28), -1)
    cv2.rectangle(fr, (int(x - 18), int(y - 34)), (int(x + 18), int(y + 32)), (40, 70, 110) if lit else (24, 26, 30), -1)
    if lit:
        for k in range(3): cv2.ellipse(fr, (int(x), int(y)), ((k + 1) * 5, (k + 1) * 5), 0, 225, 315, (200, 220, 240), 2, cv2.LINE_AA)
        line(fr, (x - 10, y - 12), (x + 10, y + 6), (255, 70, 60), 3)
def card(fr, hd):
    x, y = hd[0], hd[1] - 22; cv2.rectangle(fr, (int(x - 26), int(y - 16)), (int(x + 26), int(y + 16)), (60, 110, 200), -1); cv2.rectangle(fr, (int(x - 18), int(y - 6)), (int(x - 6), int(y + 4)), (220, 190, 90), -1)
def bubble(fr, x, y, txt, k, col=(255, 255, 255)):
    if k <= 0: return
    sp = N.text_sprite(txt, 34, (20, 20, 26, 255), pad=10); h_, w_ = sp.shape[:2]
    cv2.ellipse(fr, (int(x), int(y)), (int(w_ * .62 * k), int(h_ * .9 * k)), 0, 0, 360, col, -1, cv2.LINE_AA)
    poly(fr, [(x - 20 * k, y + h_ * .7 * k), (x + 10 * k, y + h_ * .8 * k), (x - 34 * k, y + h_ * 1.25 * k)], col)
    if k > .6: blit(fr, sp, x, y, (k - .6) / .4)

# ================================================================ GANCHO
class Wake(Si):                                    # despierta, se estira, toma el celular: sin conexión
    def __init__(s):
        s.back, s.main = room_bg((34, 40, 62), (60, 46, 38), 1); s.front = [(bokeh_layer(6, (180, 200, 255), 501, ymin=200, ymax=1100), 1.7)]
        s.t = N.text_sprite('¿Y SI INTERNET', 74, (255, 255, 255, 255), stroke=5, stroke_col=(0, 0, 0, 220)); s.t2 = N.text_sprite('DESAPARECIERA?', 74, (120, 230, 255, 255), stroke=5, stroke_col=(0, 0, 0, 220))
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (640, 520), (980, 900), (60, 80, 120), -1); cv2.rectangle(fr, (640, 520), (980, 900), (110, 90, 70), 12); cv2.line(fr, (810, 520), (810, 900), (110, 90, 70), 8)   # ventana al amanecer
        cv2.rectangle(fr, (60, 1300), (520, 1450), (90, 60, 50), -1); cv2.rectangle(fr, (60, 1230), (520, 1300), (230, 230, 236), -1)   # cama
        x, fy, h = 560, 1700, 700; u = U('peaton1', h); ns = (x + 1.45 * u, fy - 3.35 * u)
        cv2.rectangle(fr, (int(ns[0] - 70), int(ns[1])), (int(ns[0] + 90), int(fy)), (80, 56, 40), -1)                   # buró
        blink_ = (t * 2) % 1 < .5; cv2.rectangle(fr, (int(ns[0] + 20), int(ns[1] - 30)), (int(ns[0] + 80), int(ns[1])), (30, 30, 36), -1)   # módem: luz roja
        cv2.circle(fr, (int(ns[0] + 70), int(ns[1] - 15)), 6, (255, 40, 40) if blink_ else (90, 20, 20), -1, cv2.LINE_AA)
        tg = 1.9
        keys = [(0, P(uR=2.6, lR=.25, uL=-2.6, lL=-.25, boca='o', look=(0, -.3), tilt=-.04, sh=-.2)),                      # se estira bostezando
                (.9, P(uR=2.7, lR=.2, uL=-2.7, lL=-.2, boca='o', look=(0, -.35), tilt=-.05, sh=-.25)),
                (1.5, P(look=(.3, .2), frown=-.1)),
                (tg, P(look=(.5, .4), frown=0., grip={'R': ns[:1] + (ns[1] - 10, 0.)}, tz=.4)),
                (tg + .4, P(look=(.5, .45), lean=.04, grip={'R': (ns[0], ns[1] - 10, 1.)}, tz=.4)),                         # toma el celular del buró
                (tg + 1.0, P(look=(.15, .35), tilt=.04, grip={'R': (x + .5 * u, fy - 5.9 * u, 1.)}, tz=.9)),
                (s.w('del') - .2, P(look=(.15, .4), tilt=.04, frown=.1, grip={'R': (x + .5 * u, fy - 5.9 * u, 1.)}, tz=.9)),
                (s.w('del') + .3, P(look=(.1, .35), tilt=.02, frown=-.2, brow_up=.6, brow_asym=.25, boca='tensa', sh=-.15, grip={'R': (x + .55 * u, fy - 6.0 * u, 1.)}, tz=.9)),
                (d, P(look=(.1, .35), frown=-.25, brow_up=.5, brow_asym=.25, boca='tensa', grip={'R': (x + .55 * u, fy - 6.0 * u, 1.)}, tz=.9))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 31)
        hands, _ = RG.person(fr, 'peaton1', x, fy, h, p, t, feet=stance(x, u, fy, .36))
        if t >= tg + .35: handphone(fr, hands['R']); hands_on_top(fr, {'R': hands['R']}, 'peaton1', h)
        else: cv2.rectangle(fr, (int(ns[0] - 30), int(ns[1] - 12)), (int(ns[0] + 4), int(ns[1])), (20, 22, 28), -1)
        blit(fr, s.t, 540, 330, ss(.1, .5, t)); blit(fr, s.t2, 540, 420, ss(.3, .7, t)); blit(fr, hipo_label(), 540, 500, ss(.5, .9, t))
    def cam(s, t, d): return lerp(1.05, 1.12, RG.ease(t / d)), 560, 1250, 0, 0

class Apps(Si):                                    # mensajes, redes y banco: sin servicio
    def __init__(s):
        s.back = NV.stage_bg(2, (8, 10, 20), (80, 120, 255)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (150, 180, 255), 502, ymin=200, ymax=1700), 1.7)]
        s.items = [('whatsapp', 'MENSAJES', 'NO SE PUDO ENVIAR', (60, 200, 120)), ('redes', 'REDES SOCIALES', 'SIN CONEXIÓN', (120, 140, 255)), ('dinero', 'TU BANCO', 'SERVICIO NO DISPONIBLE', (255, 190, 80))]
    def draw(s, fr, t, d):
        for i, (wd, ttl, err, col) in enumerate(s.items):
            k = ss(s.w(wd) - .7, s.w(wd) - .05, t)
            if k <= 0: continue
            x = 200 + i * 340; y = lerp(2300, 980, k); w, h = 300, 560                 # entra desde abajo, fuera del cuadro
            cv2.rectangle(fr, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), (20, 22, 28), -1)
            cv2.rectangle(fr, (int(x - w / 2 + 12), int(y - h / 2 + 30)), (int(x + w / 2 - 12), int(y + h / 2 - 30)), (234, 236, 240), -1)
            cv2.rectangle(fr, (int(x - w / 2 + 12), int(y - h / 2 + 30)), (int(x + w / 2 - 12), int(y - h / 2 + 100)), col, -1)
            fs = .7; (tw, _), _ = cv2.getTextSize(ttl, cv2.FONT_HERSHEY_DUPLEX, fs, 2); cv2.putText(fr, ttl, (int(x - tw / 2), int(y - h / 2 + 76)), cv2.FONT_HERSHEY_DUPLEX, fs, (255, 255, 255), 2, cv2.LINE_AA)
            for q in range(4): cv2.rectangle(fr, (int(x - w / 2 + 30), int(y - 140 + q * 50)), (int(x + w / 2 - 60 - q * 20), int(y - 116 + q * 50)), (200, 204, 212), -1)
            e = ss(s.w(wd) + .1, s.w(wd) + .5, t)
            if e > 0:
                ov = fr.copy()
                cv2.rectangle(ov, (int(x - w / 2 + 20), int(y + 80)), (int(x + w / 2 - 20), int(y + 200)), (255, 235, 235), -1)
                circ(ov, (x, y + 112), 18, (230, 50, 50)); line(ov, (x, y + 102), (x, y + 116), (255, 255, 255), 4); circ(ov, (x, y + 124), 2.5, (255, 255, 255))
                fs = .5; (tw, _), _ = cv2.getTextSize(err, cv2.FONT_HERSHEY_DUPLEX, fs, 1); cv2.putText(ov, err, (int(x - tw / 2), int(y + 175)), cv2.FONT_HERSHEY_DUPLEX, fs, (200, 40, 40), 1, cv2.LINE_AA)
                fr[:] = cv2.addWeighted(fr, 1 - e, ov, e, 0)   # el aviso de error aparece con fundido
        blit(fr, hipo_label(), 540, 360)

class Beginning(Si):                               # «apenas el comienzo»: la ciudad parpadea
    def __init__(s):
        s.back, s.main = street_bg(3); s.front = [(bokeh_layer(10, (255, 200, 140), 503, ymin=200, ymax=1200), 1.7)]
        s.t = N.text_sprite('APENAS EL COMIENZO', 80, (255, 236, 220, 255), glow=(255, 80, 40), glow_r=16, stroke=4, stroke_col=(0, 0, 0, 200))
    def draw(s, fr, t, d):
        dim = 1 - .35 * (.5 + .5 * math.sin(t * 9)) * (1 - ss(1.2, 1.8, t))                # baja la luz con pulso suave (sin destellos)
        fr[:] = (fr.astype(np.float32) * dim).astype(np.uint8)
        blit(fr, s.t, 540, 700, ss(.2, .6, t), lerp(1.3, 1, ss(.2, .6, t)))
    def cam(s, t, d): return lerp(1.0, 1.1, RG.ease(t / d)), 540, 1100, 0, 0

# ================================================================ EL CAOS
class Streets(Si):                                 # salen de sus casas y levantan el celular buscando señal
    def __init__(s):
        s.back, s.main = street_bg(4, col=(44, 40, 52)); s.front = [(bokeh_layer(10, (255, 210, 160), 504, ymin=200, ymax=1200), 1.7)]
        s.panel = N2.red_panel('MILLONES BUSCAN RESPUESTAS', w=880, h=150)
    def draw(s, fr, t, d):
        fy = 1660
        for dx in (150, 540, 930): cv2.rectangle(fr, (dx - 70, 1180), (dx + 70, 1420), (70, 52, 40), -1); cv2.rectangle(fr, (dx - 60, 1190), (dx + 60, 1420), (250, 210, 140), -1)   # puertas encendidas
        crew = [('vecino', 150, 330, .2, 1), ('vecina', 540, 700, .5, 1), ('peaton2', 930, 760, .8, -1)]
        for i, (w_, x0, x1, t0, dd) in enumerate(crew):
            h = 560; u = U(w_, h); x1s = N2.snap(x1, w_, h); x0s = N2.snap(x0, w_, h); tw = t0 + 1.5
            up = (x1s + (.55 if dd > 0 else -.55) * u, fy - 7.3 * u)
            keys = [(tw + .2, P(look=(.2 * dd, -.1), frown=.1)), (tw + 1.4, P(look=(.2 * dd, -.45), frown=.25, brow_up=.3, grip={'R' if dd > 0 else 'L': up + (1.,)}, tz=.4)),
                    (tw + 2.5, P(look=(-.3 * dd, -.45), frown=.35, brow_up=.3, grip={'R' if dd > 0 else 'L': (up[0] - .4 * u * dd, up[1], 1.)}, tz=.4)),
                    (d, P(look=(.3 * dd, -.4), frown=.4, brow_up=.3, grip={'R' if dd > 0 else 'L': up + (1.,)}, tz=.4))]
            def j34(f_, w_=w_, x1s=x1s, u=u, keys=keys, dd=dd, i=i):
                p = RG.anim(keys, t); p['blink'] = blinkp(t, 40 + i); return RG.person_34(f_, w_, x1s, fy + i * 12, h, p, t, feet=stance(x1s, u, fy + i * 12), turn=dd)[0]
            if t < t0: continue
            if t < tw: walk(fr, w_, x0s, x1s, t0, tw, fy + i * 12, h, t, mode='suave')
            elif t < tw + .2: hands = turn_blend(fr, (t - tw) / .2, lambda f_: walk(f_, w_, x0s, x1s, t0, tw, fy + i * 12, h, tw, mode='suave'), j34)
            else:
                hands = j34(fr); k_ = 'R' if dd > 0 else 'L'
                if t > tw + 1.1: handphone(fr, hands[k_]); hands_on_top(fr, {k_: hands[k_]}, w_, h)
        float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): return lerp(1.04, 1.1, RG.ease(t / d)), 540, 1250, 0, 0

class ATM(Si):                                     # cajero fuera de servicio: inserta la tarjeta, se frustra
    def __init__(s):
        s.back, s.main = street_bg(5, col=(40, 44, 56)); s.front = [(bokeh_layer(8, (160, 220, 255), 505, ymin=200, ymax=1200), 1.7)]
        s.panel = N2.red_panel('CAJEROS FUERA DE SERVICIO', w=860, h=150); s.term = chip('TERMINALES DE PAGO: ERROR', (255, 120, 100), w=700)
    def draw(s, fr, t, d):
        fy = 1680; ax = 760
        cv2.rectangle(fr, (ax - 150, 900), (ax + 150, 1680), (70, 76, 90), -1); cv2.rectangle(fr, (ax - 150, 900), (ax + 150, 960), (40, 90, 160), -1)
        cv2.putText(fr, 'CAJERO', (ax - 70, 942), cv2.FONT_HERSHEY_DUPLEX, 1., (255, 255, 255), 2, cv2.LINE_AA)
        err = t > 1.5; screen(fr, ax, 1090, 220, 160, 'FUERA DE SERVICIO' if err else 'INSERTE TARJETA', (255, 70, 60) if err else (120, 220, 255), icon='x' if err else None)
        slot = (ax - 40, 1280); cv2.rectangle(fr, (slot[0] - 50, slot[1] - 8), (slot[0] + 50, slot[1] + 8), (20, 20, 24), -1)
        x, h = 470, 640; u = U('vecina', h)
        keys = [(0, P(look=(.4, .2), frown=.1, grip={'R': (x + .7 * u, fy - 4.7 * u, 1.)}, tz=.8)),
                (.7, P(look=(.45, .25), lean=.04, frown=.15, grip={'R': (slot[0] - 30, slot[1], 1.)}, tz=.5)),                     # mete la tarjeta
                (1.4, P(look=(.45, .05), frown=.2, grip={'R': (slot[0] - 30, slot[1], 1.)}, tz=.5)),
                (1.8, P(look=(.4, 0), frown=.5, brow_asym=.3, boca='tensa', lean=-.02, grip={'R': (x + .7 * u, fy - 4.8 * u, 1.)}, tz=.8)),   # la saca
                (2.6, P(look=(.1, 0), frown=-.4, brow_up=.4, sh=-.35, boca='triste', grip={'R': (x + 1.3 * u, fy - 5.0 * u, 1.), 'L': (x - 1.1 * u, fy - 5.0 * u, 1.)}, tz=.6)),   # ¿y ahora?
                (d, P(look=(0, .05), frown=-.45, brow_up=.35, sh=-.25, boca='triste', grip={'R': (x + 1.2 * u, fy - 4.9 * u, 1.), 'L': (x - 1.0 * u, fy - 4.9 * u, 1.)}, tz=.6))]
        for i, (w_, qx) in enumerate((('peaton1', 140), ('jefe', 290))):          # fila detrás, impaciente
            uq = U(w_, 560); g = {'R': (qx + .5 * uq, fy - 5.9 * uq, 1.)} if i == 1 else None
            hq, _ = RG.person_34(fr, w_, qx, fy - 30, 560, P(look=(.5, .05 + .3 * (i == 1)), frown=.3, grip=g, tz=.9, hip_dx=.04 * math.sin(t + i), blink=blinkp(t, 50 + i)), t + i, feet=stance(qx, uq, fy - 30), turn=1)
            if i == 1: handphone(fr, hq['R']); hands_on_top(fr, {'R': hq['R']}, w_, 560)
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 52)
        hands, _ = RG.person_34(fr, 'vecina', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        if t < 1.2: card(fr, hands['R']); hands_on_top(fr, {'R': hands['R']}, 'vecina', h)
        elif t < 1.5: cv2.rectangle(fr, (slot[0] - 10, slot[1] - 6), (slot[0] + 30, slot[1] + 6), (60, 110, 200), -1)
        else: card(fr, hands['R']) if t < 2.3 else None; hands_on_top(fr, {'R': hands['R']}, 'vecina', h) if t < 2.3 else None
        float_in(fr, s.panel, 540, 330, t, .2)
        if t > s.w('terminales') - .2: float_in(fr, s.term, 540, 480, t, s.w('terminales') - .2)
    def cam(s, t, d): return lerp(1.06, 1.12, RG.ease(t / d)), 520, 1260, 0, 0

class Terminal(Si):                                # la terminal de pago falla en el mostrador
    def __init__(s):
        s.back, s.main = room_bg((70, 54, 40), (54, 40, 32), 6); s.front = [(bokeh_layer(8, (255, 210, 160), 506, ymin=200, ymax=1100), 1.7)]
        s.panel = N2.red_panel('PAGOS CON TARJETA: ERROR', w=800, h=150)
    def draw(s, fr, t, d):
        fy = 1700; cx, cy = 600, 1400
        xc, hc = 820, 600; uc = U('ejecutivo', hc)
        RG.person_34(fr, 'ejecutivo', xc, fy, hc, P(look=(-.4, .15), frown=.2 - .5 * RG.ease((t - 1.2) / .5), sh=-.35 * RG.ease((t - 1.2) / .5), brow_up=.3 * RG.ease((t - 1.2) / .5),
                                                  grip={'L': (xc - 1.2 * uc, fy - 4.9 * uc, RG.ease((t - 1.2) / .6)), 'R': (xc + 1.1 * uc, fy - 4.9 * uc, RG.ease((t - 1.2) / .6))}, tz=.6, blink=blinkp(t, 60)), t, feet=stance(xc, uc, fy), turn=-1)
        cv2.rectangle(fr, (420, 1360), (1080, 1720), (110, 76, 50), -1); cv2.rectangle(fr, (420, 1350), (1080, 1372), (150, 110, 70), -1)   # mostrador
        err = t > .9; screen(fr, cx, cy - 40, 110, 130, 'ERROR' if err else 'PAGO', (255, 70, 60) if err else (120, 220, 255), icon='x' if err else None)
        x, h = 330, 620; u = U('peaton2', h)
        keys = [(0, P(look=(.4, .2), frown=0., grip={'R': (cx - 70, cy - 40, 1.)}, tz=.5)), (.9, P(look=(.45, .25), frown=.1, grip={'R': (cx - 70, cy - 40, 1.)}, tz=.5)),
                (1.3, P(look=(.4, .2), frown=-.2, brow_up=.6, boca='o', grip={'R': (cx - 80, cy - 46, 1.)}, tz=.5)),
                (d, P(look=(.35, .1), frown=.45, brow_asym=.3, boca='tensa', grip={'R': (x + .6 * u, fy - 4.8 * u, 1.)}, tz=.8))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 61)
        hands, _ = RG.person_34(fr, 'peaton2', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        card(fr, hands['R']); hands_on_top(fr, {'R': hands['R']}, 'peaton2', h)
        float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): return lerp(1.06, 1.12, RG.ease(t / d)), 560, 1300, 0, 0

class Banks(Si):                                   # avalancha de operaciones interrumpidas
    def __init__(s):
        s.back, s.main = street_bg(7, col=(50, 50, 60)); s.front = [(bokeh_layer(8, (255, 230, 200), 507, ymin=200, ymax=1200), 1.7)]
        s.tk = N.text_sprite('OPERACIÓN INTERRUMPIDA', 26, (200, 40, 40, 255), pad=6)
        s.r = np.random.RandomState(9).uniform(0, 1, (40, 3))
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (180, 700), (900, 1420), (190, 186, 176), -1); poly(fr, [(140, 700), (940, 700), (540, 540)], (170, 166, 156))
        for k in range(5): cv2.rectangle(fr, (230 + k * 140, 820), (270 + k * 140, 1420), (160, 156, 146), -1)
        cv2.putText(fr, 'BANCO', (430, 680), cv2.FONT_HERSHEY_DUPLEX, 2., (60, 60, 70), 4, cv2.LINE_AA)
        for i, (a_, b_, c_) in enumerate(s.r):                                 # los comprobantes caen y se apilan
            st = .2 + i * .07; k = ss(st, st + .8, t)
            if k <= 0: continue
            y = lerp(-80, 1500 + (i % 8) * -16 - (i // 8) * 30, k); x = 120 + a_ * 840
            cv2.rectangle(fr, (int(x - 120), int(y - 24)), (int(x + 120), int(y + 24)), (250, 248, 240), -1); cv2.rectangle(fr, (int(x - 120), int(y - 24)), (int(x + 120), int(y + 24)), (200, 60, 60), 2)
            if k > .3: blit(fr, s.tk, x, y)
        float_in(fr, N2.red_panel('AVALANCHA DE OPERACIONES', w=860, h=150) if not hasattr(s, 'p') else s.p, 540, 330, t, .2); s.p = getattr(s, 'p', N2.red_panel('AVALANCHA DE OPERACIONES', w=860, h=150))

class Lines(Si):                                   # supermercado: la fila avanza paso a paso
    def __init__(s):
        wall = vgrad([(0, (60, 70, 80)), (1, (40, 46, 54))]); i8 = to8(wall)
        for r in range(4):
            cv2.rectangle(i8, (0, 640 + r * 160), (W, 652 + r * 160), (180, 180, 186), -1)
            for c in range(24): cv2.rectangle(i8, (c * 46 + 6, 600 + r * 160), (c * 46 + 40, 640 + r * 160), [(200, 60, 60), (60, 140, 200), (240, 200, 60), (90, 180, 90)][(c + r) % 4], -1)
        s.back = [(dof(opaque(i8.astype(np.float32)), 2.5), .4)]; s.main = floor_layer(1300, (190, 190, 196), (170, 170, 176))
        s.front = [(bokeh_layer(6, (255, 255, 240), 508, ymin=200, ymax=1000), 1.7)]
        s.panel = N2.red_panel('FILAS INTERMINABLES', w=760, h=150)
    def draw(s, fr, t, d):
        fy = 1700; cast_ = ['vecina', 'peaton1', 'jefe', 'mujer', 'vecino', 'peaton2']; h = 500
        for i, w_ in enumerate(cast_):
            u = U(w_, h); st = RG.step_len(u); base = N2.snap(980 - i * 3.0 * st, w_, h)
            n_moves = 2; seg = 1.6
            x = base
            for m in range(n_moves):
                ta = .4 + m * seg + i * .12                                      # cada uno avanza con un pequeño retraso (acción superpuesta)
                if t >= ta + 1.0: x = base + (m + 1) * 2 * st
                elif t >= ta: walk(fr, w_, base + m * 2 * st, base + (m + 1) * 2 * st, ta, ta + 1.0, fy, h, t, mode='suave', frown=.3); x = None; break
            if x is not None:
                gp, feet, bob = RG.gait_x(x, 1, u, fy); pp = dict(P(frown=.3 + .1 * (i % 2), look=(.5, .05), blink=blinkp(t, 70 + i)), **{k: v for k, v in gp.items() if k not in ('uL', 'uR', 'lean', 'look')})
                RG.person_side(fr, w_, x, fy, h, pp, t, feet=feet, facing=1)
        float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): return 1.08, 540, 1300, lerp(40, -40, RG.ease(t / d)), 0

class Register(Si):                                # la caja: sistema no disponible; el cliente espera con la compra
    def __init__(s):
        s.back, s.main = room_bg((70, 80, 90), (180, 180, 186), 9); s.front = [(bokeh_layer(6, (255, 255, 240), 509, ymin=200, ymax=1000), 1.7)]
        s.panel = N2.red_panel('SISTEMA DE COBRO NO DISPONIBLE', w=920, h=150); s.inv = chip('INVENTARIO: SIN DATOS', (255, 160, 120), w=600)
    def draw(s, fr, t, d):
        fy = 1700; xc, hc = 760, 620; uc = U('vecino', hc); kb = (xc - .8 * uc, fy - 3.9 * uc)
        tap = math.sin(t * 14) * .12 * uc * (t < 3.2)
        shake = math.sin(t * 9) * .15 * RG.ease((t - 3.2) / .4)
        pc = P(look=(-.25 + shake, .35 * (t < 3.2)), frown=.4, boca='tensa', grip={'L': (kb[0] - 20, kb[1] + tap, 1.), 'R': (kb[0] + 50, kb[1] - tap, 1.)}, tz=.9, blink=blinkp(t, 80))
        RG.person_34(fr, 'vecino', xc, fy, hc, pc, t, feet=stance(xc, uc, fy), turn=-1)
        cv2.rectangle(fr, (420, 1400), (1080, 1720), (60, 64, 76), -1); cv2.rectangle(fr, (420, 1390), (1080, 1410), (90, 96, 110), -1)
        screen(fr, 700, 1250, 200, 150, 'NO DISPONIBLE', icon='x')
        x, h = 300, 620; u = U('mujer', h)
        hold = {'L': (x + .1 * u, fy - 4.6 * u, 1.), 'R': (x + 1.0 * u, fy - 4.6 * u, 1.)}
        pm = P(look=(.4, .1), frown=.2 + .3 * RG.ease((t - 2.5) / .6), brow_asym=.25 * RG.ease((t - 2.5) / .6), grip=hold, tz=.9, hip_dx=.05 * math.sin(t * .9), blink=blinkp(t, 81))
        hands, _ = RG.person_34(fr, 'mujer', x, fy, h, pm, t, feet=stance(x, u, fy), turn=1)
        c = (A(*hands['L']) + A(*hands['R'])) / 2; cv2.ellipse(fr, (int(c[0]), int(c[1] - 40)), (70, 60), 0, 180, 360, (110, 200, 90), -1, cv2.LINE_AA)   # verduras
        cv2.rectangle(fr, (int(c[0] - 80), int(c[1] - 50)), (int(c[0] + 80), int(c[1] + 40)), (200, 170, 120), -1); hands_on_top(fr, hands, 'mujer', h)
        float_in(fr, s.panel, 540, 330, t, .2)
        if t > s.w('inventarios') - .2: float_in(fr, s.inv, 540, 480, t, s.w('inventarios') - .2)
    def cam(s, t, d): return lerp(1.06, 1.1, RG.ease(t / d)), 560, 1300, 0, 0

class HowLong(Si):                                 # nadie sabe cuánto va a durar
    def __init__(s):
        s.back, s.main = room_bg((30, 34, 50), (50, 40, 34), 10); s.front = [(bokeh_layer(6, (200, 210, 255), 510, ymin=200, ymax=1000), 1.7)]
        s.q = N.text_sprite('¿CUÁNTO DURARÁ?', 84, (255, 236, 200, 255), glow=(255, 160, 40), glow_r=16, stroke=4, stroke_col=(0, 0, 0, 200))
    def draw(s, fr, t, d):
        c = (760, 760); cv2.circle(fr, c, 170, (230, 226, 216), -1, cv2.LINE_AA); cv2.circle(fr, c, 170, (90, 80, 70), 10, cv2.LINE_AA)
        for k in range(12): a_ = k * math.pi / 6; line(fr, (c[0] + math.cos(a_) * 140, c[1] + math.sin(a_) * 140), (c[0] + math.cos(a_) * 158, c[1] + math.sin(a_) * 158), (60, 60, 60), 5)
        a1 = t * 6; a2 = t * .5; line(fr, c, (c[0] + math.sin(a1) * 130, c[1] - math.cos(a1) * 130), (30, 30, 30), 6); line(fr, c, (c[0] + math.sin(a2) * 90, c[1] - math.cos(a2) * 90), (30, 30, 30), 10)
        x, fy, h = 360, 1700, 680; u = U('laura', h)
        p = P(look=(.45, -.4), frown=-.45, brow_up=.35, boca='triste', grip={'R': (x + .2 * u, fy - 6.3 * u, RG.ease((t - .3) / 1.0))}, tz=.8, sh=.1, blink=blinkp(t, 90))
        RG.person_34(fr, 'laura', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        blit(fr, s.q, 540, 360, ss(.1, .5, t))

# ================================================================ EL MUNDO SE DETIENE
class Office(Si):                                  # la oficina sin red: teclea, intenta llamar; la jefa entra y pregunta
    def __init__(s):
        s.back, s.main = NV.office(12); s.front = [(bokeh_layer(8, (200, 220, 255), 511, ymin=200, ymax=1100), 1.7)]
        s.panel = N2.blue_panel('EMPRESAS SIN CONTACTO', w=800, h=150)
    def draw(s, fr, t, d):
        fy = 1700; x, h = 380, 620; u = U('ejecutivo', h); kb = (x + .1 * u, fy - 3.95 * u); ear = (x + .9 * u, fy - 6.9 * u)
        tap = math.sin(t * 13) * .1 * u * (t < 1.1)
        keys = [(0, P(look=(.25, .35), frown=.3, grip={'L': (kb[0] - 30, kb[1] + tap, 1.), 'R': (kb[0] + 40, kb[1] - tap, 1.)}, tz=.9)),
                (1.1, P(look=(.25, .35), frown=.45, grip={'L': (kb[0] - 30, kb[1], 1.), 'R': (kb[0] + 40, kb[1], 1.)}, tz=.9)),
                (2.0, P(look=(.1, .1), frown=.45, grip={'L': (kb[0] - 30, kb[1], 1.), 'R': ear + (1.,)}, tz=.6)),       # el teléfono al oído: no hay tono
                (d, P(look=(.5, 0), frown=-.3, brow_up=.4, boca='tensa', grip={'L': (kb[0] - 30, kb[1], 1.), 'R': ear + (1.,)}, tz=.6))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 100)
        hands, _ = RG.person_34(fr, 'ejecutivo', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        cv2.rectangle(fr, (160, 1420), (720, 1720), (90, 66, 46), -1); cv2.rectangle(fr, (160, 1410), (720, 1430), (130, 96, 66), -1)   # escritorio
        screen(fr, 560, 1290, 240, 180, 'SIN RED', icon='wifi')
        if t > 1.5: handphone(fr, hands['R'], lit=False); hands_on_top(fr, {'R': hands['R']}, 'ejecutivo', h)
        xd, hd_ = N2.snap(800, 'directora', 600), 600; ud = U('directora', hd_); ta, tb = .4, 2.0
        kd = [(tb + .2, P(look=(-.4, 0), frown=.2)), (tb + .7, P(look=(-.4, 0), frown=-.3, brow_up=.4, sh=-.3, grip={'L': (xd - 1.2 * ud, fy - 5 * ud, 1.), 'R': (xd + 1.0 * ud, fy - 5 * ud, 1.)}, tz=.6)),
              (d, P(look=(-.4, 0), frown=-.35, brow_up=.4, sh=-.25, grip={'L': (xd - 1.1 * ud, fy - 4.9 * ud, 1.), 'R': (xd + 1.0 * ud, fy - 4.9 * ud, 1.)}, tz=.6))]
        def jd(f_): q = RG.anim(kd, t); q['blink'] = blinkp(t, 101); return RG.person_34(f_, 'directora', xd, fy, hd_, q, t, feet=stance(xd, ud, fy), turn=-1)
        if ta < t < tb: walk(fr, 'directora', 1300, xd, ta - 1.2, tb, fy, hd_, t)
        elif tb <= t < tb + .2: turn_blend(fr, (t - tb) / .2, lambda f_: walk(f_, 'directora', 1300, xd, ta - 1.2, tb, fy, hd_, tb), jd)
        elif t >= tb + .2: jd(fr)
        float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): return lerp(1.06, 1.1, RG.ease(t / d)), 560, 1280, 0, 0

class Hospital(Si):                                # la doctora no puede abrir el expediente digital: vuelve al papel
    def __init__(s):
        s.back, s.main = room_bg((190, 210, 214), (200, 206, 210), 13); s.front = [(bokeh_layer(6, (255, 255, 255), 513, ymin=200, ymax=1000), 1.7)]
        s.panel = N2.blue_panel('HOSPITALES', 'SIN ACCESO A INFORMACIÓN DIGITAL', w=860, h=170)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (640, 1260), (1060, 1420), (240, 244, 248), -1); cv2.rectangle(fr, (640, 1420), (1060, 1450), (150, 160, 170), -1)   # cama
        for xx in (660, 1040): cv2.rectangle(fr, (xx - 8, 1450), (xx + 8, 1600), (150, 160, 170), -1)
        fy, x, h = 1700, 420, 660; u = U('doctora', h); sw = 1.9
        tab = {'L': (x - .1 * u, fy - 4.75 * u, 1.), 'R': (x + .85 * u, fy - 4.8 * u, 1.)}
        clip = {'L': (x + .1 * u, fy - 4.7 * u, 1.), 'R': (x + .75 * u + math.sin(t * 12) * .06 * u * (t > sw + .8), fy - 4.95 * u, 1.)}
        keys = [(0, P(look=(.15, .45), tilt=.05, frown=.3, grip=tab, tz=.9)), (1.2, P(look=(.15, .45), tilt=.05, frown=.55, brow_asym=.3, boca='tensa', grip=tab, tz=.9)),
                (sw, P(look=(.2, .35), frown=.4, grip=tab, tz=.9)), (sw + .6, P(look=(.15, .45), tilt=.05, frown=.3, grip=clip, tz=.9)), (d, P(look=(.15, .5), tilt=.06, frown=.3, grip=clip, tz=.9))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 111)
        hands, _ = RG.person_34(fr, 'doctora', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        if t < sw + .3:
            N2.tablet(fr, hands, t); c = (A(*hands['L']) + A(*hands['R'])) / 2
            cv2.putText(fr, 'SIN ACCESO', (int(c[0] - 46), int(c[1] - 30)), cv2.FONT_HERSHEY_DUPLEX, .5, (255, 90, 80), 1, cv2.LINE_AA)
        else: N2.paper(fr, hands, w_extra=30, h=150, col=(244, 240, 228))
        hands_on_top(fr, hands, 'doctora', h)
        float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): return lerp(1.06, 1.1, RG.ease(t / d)), 560, 1280, 0, 0

class Airport(Si):                                 # tablero de vuelos «RETRASADO» y contenedores detenidos
    def __init__(s):
        s.back = NV.stage_bg(14, (10, 12, 20), (80, 120, 220)); s.main = floor_layer(1500, (40, 44, 54), (60, 64, 76))
        s.front = [(bokeh_layer(8, (200, 220, 255), 514, ymin=200, ymax=1200), 1.7)]
        s.rows = ['MADRID', 'BOGOTÁ', 'LIMA', 'CDMX', 'BUENOS AIRES', 'SANTIAGO']
        s.panel = N2.blue_panel('AEROPUERTOS Y CADENAS DE SUMINISTRO', w=960, h=150)
    def draw(s, fr, t, d):
        tc = s.w('cadenas'); q = ss(tc - .3, tc + .1, t)
        if 0 < q < 1: a_ = fr.copy(); s.half(a_, t, d, False); b_ = fr.copy(); s.half(b_, t, d, True); fr[:] = cv2.addWeighted(a_, 1 - q, b_, q, 0); float_in(fr, s.panel, 540, 330, t, .2); return
        s.half(fr, t, d, q >= 1); float_in(fr, s.panel, 540, 330, t, .2)
    def half(s, fr, t, d, second):
        tc = s.w('cadenas')
        if not second:
            cv2.rectangle(fr, (80, 520), (1000, 1160), (14, 16, 22), -1); cv2.rectangle(fr, (80, 520), (1000, 1160), (90, 100, 120), 4)
            cv2.putText(fr, 'SALIDAS', (110, 580), cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 210, 90), 2, cv2.LINE_AA)
            for i, c in enumerate(s.rows):
                y = 650 + i * 84; cv2.putText(fr, c, (110, y), cv2.FONT_HERSHEY_DUPLEX, 1., (230, 230, 230), 2, cv2.LINE_AA)
                st = 'RETRASADO' if t > .4 + i * .25 else 'A TIEMPO'
                cv2.putText(fr, st, (700, y), cv2.FONT_HERSHEY_DUPLEX, 1., (255, 80, 60) if st == 'RETRASADO' else (120, 230, 140), 2, cv2.LINE_AA)
            x, fy, h = 640, 1720, 600; u = U('peaton2', h)
            p = P(look=(-.3, -.45), frown=.1 - .6 * RG.ease((t - 1.6) / .6), brow_up=.4 * RG.ease((t - 1.6) / .6), grip={'R': (x + 1.0 * u, fy - 3.6 * u, 1.)}, tz=.3, blink=blinkp(t, 120))
            hands, _ = RG.person_34(fr, 'peaton2', x, fy, h, p, t, feet=stance(x, u, fy), turn=-1)
            hd = hands['R']; cv2.rectangle(fr, (int(hd[0] - 10), int(hd[1])), (int(hd[0] + 90), int(hd[1] + 120)), (120, 50, 60), -1); cv2.line(fr, (int(hd[0]), int(hd[1])), (int(hd[0] + 20), int(hd[1])), (40, 40, 40), 6)   # maleta
            hands_on_top(fr, {'R': hd}, 'peaton2', h)
        else:
            for r in range(3):
                for c in range(4):
                    col = [(200, 70, 50), (50, 110, 170), (230, 170, 40), (70, 150, 90)][(r + c) % 4]; x0, y0 = 120 + c * 220, 1000 + r * 150
                    cv2.rectangle(fr, (x0, y0), (x0 + 200, y0 + 140), col, -1)
                    for k in range(6): cv2.line(fr, (x0 + 14 + k * 32, y0 + 10), (x0 + 14 + k * 32, y0 + 130), dark(col, .75), 4)
            if getattr(s, 'st', None) is None: s.st = N.stamp('RETRASO', (255, 59, 42), w=520, h=110, px=64)
            stamp_in(fr, s.st, 540, 860, t, tc)

class StillMoving(Si):                             # los camiones siguen, los aviones vuelan
    def __init__(s):
        sky = vgrad([(0, (60, 90, 140)), (1, (180, 170, 150))]); s.back = [(dof(opaque(sky), 2), .1)]
        s.main = floor_layer(1400, (70, 70, 74), (90, 90, 96)); s.front = [(bokeh_layer(6, (255, 240, 220), 515, ymin=200, ymax=900), 1.7)]
        s.t1 = chip('LOS CAMIONES NO DESAPARECEN', (150, 230, 255), w=760); s.t2 = chip('LOS AVIONES NO CAEN', (150, 230, 255), w=600)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (0, 1400), (W, 1560), (50, 50, 54), -1)
        for k in range(8): cv2.rectangle(fr, (int((k * 180 - t * 300) % 1300 - 100), 1474), (int((k * 180 - t * 300) % 1300 - 30), 1486), (230, 230, 200), -1)
        for i in range(2): TR.truck(fr, (i * 640 + t * 220) % 1500 - 300, 1470, 1.0, col=(70, 90, 120), star=False)
        ta = s.w('aviones')
        if t > ta - .5: TR.jet(fr, lerp(-200, 1300, (t - ta + .5) / 3.5), 720 - (t - ta) * 40, 1.2, t, col=(220, 224, 232))
        float_in(fr, s.t1, 540, 360, t, .2)
        if t > ta - .2: float_in(fr, s.t2, 540, 480, t, ta - .2)

class Coordination(Si):                            # coordinar todo se vuelve mucho más difícil
    def __init__(s):
        s.back = NV.stage_bg(16, (6, 10, 18), (60, 140, 220)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (140, 200, 255), 516, ymin=200, ymax=1700), 1.7)]
        r_ = np.random.RandomState(3); s.nodes = [(r_.uniform(120, 960), r_.uniform(620, 1500)) for _ in range(18)]
        s.edges = [(i, j) for i in range(18) for j in range(i + 1, 18) if math.dist(s.nodes[i], s.nodes[j]) < 320]
        s.panel = N2.red_panel('COORDINAR SE VUELVE DIFÍCIL', w=900, h=150)
    def draw(s, fr, t, d):
        for k, (i, j) in enumerate(s.edges):
            cut = t > 1.0 + (k % 9) * .25; a_, b_ = s.nodes[i], s.nodes[j]
            if not cut: line(fr, a_, b_, (90, 200, 255), 3); f = (t * .8 + k * .13) % 1; circ(fr, (lerp(a_[0], b_[0], f), lerp(a_[1], b_[1], f)), 5, (200, 240, 255))
            else:
                for q in range(6):
                    if q % 2 == 0: line(fr, (lerp(a_[0], b_[0], q / 6), lerp(a_[1], b_[1], q / 6)), (lerp(a_[0], b_[0], (q + 1) / 6), lerp(a_[1], b_[1], (q + 1) / 6)), (200, 70, 60), 2)
        for (x, y) in s.nodes: circ(fr, (x, y), 14, (255, 255, 255)); circ(fr, (x, y), 9, (60, 120, 200))
        float_in(fr, s.panel, 540, 330, t, .2)

# ================================================================ EL MIEDO
class Danger(Si):
    def __init__(s):
        s.back = NV.stage_bg(17, (16, 4, 4), (255, 40, 30)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 100, 80), 517, ymin=200, ymax=1700), 1.7)]
        s.t = N.text_sprite('EL VERDADERO PELIGRO', 76, (255, 236, 220, 255), glow=(255, 40, 30), glow_r=18, stroke=4, stroke_col=(0, 0, 0, 200))
    def draw(s, fr, t, d):
        blit(fr, s.t, 540 + math.sin(t * 40) * 3 * (t < .6), 820, ss(.1, .5, t), lerp(1.4, 1, ss(.1, .5, t)))
        hk = .5 + .5 * math.sin(t * 7); circ(fr, (540, 1100), 60 + 10 * hk, (200, 30, 30))

class Rumors(Si):                                  # el rumor pasa de oído en oído; cada mensaje recibe el sello FALSO
    def __init__(s):
        s.back, s.main = street_bg(18, col=(40, 30, 40), sky=((14, 6, 10), (50, 20, 26))); s.front = [(bokeh_layer(10, (255, 120, 100), 518, ymin=200, ymax=1200), 1.7)]
        s.msgs = [('rumores', '¿FUE UN ATAQUE?'), ('falsas', '¡NO SALGAN!'), ('pánico', '¡SE ACABÓ TODO!')]
        s.fake = N.stamp('FALSO', (255, 59, 42), w=300, h=90, px=56)
    def draw(s, fr, t, d):
        fy, h = 1700, 560; crew = [('vecino', 200), ('mujer', 540), ('peaton1', 880)]
        for i, (w_, x) in enumerate(crew):
            u = U(w_, h); tw = .4 + i * 1.6
            whisper = RG.ease((t - tw + .3) / .9) * (1 - RG.ease((t - tw - 1.1) / .7)) if i < 2 else 0
            listen = RG.ease((t - (tw - 1.6) - .2) / .4) * (1 - RG.ease((t - (tw - 1.6) - 1.4) / .4)) if i > 0 else 0
            g = {'R': (x + .8 * u, fy - 6.5 * u, whisper)} if i < 2 else None                 # mano junto a la boca, hacia el vecino
            p = P(look=(.5 * whisper - .4 * listen, .05), lean=.07 * whisper - .05 * listen, frown=.3 + .3 * listen, brow_up=.4 * listen, boca='tensa' if listen > .5 else 'neutra',
                  grip=g, tz=.6, blink=blinkp(t, 130 + i), hip_dx=.04 * math.sin(t + i))
            RG.person_34(fr, w_, x, fy, h, p, t, feet=stance(x, u, fy), turn=1 if i < 2 else -1)
        for i, (wd, msg) in enumerate(s.msgs):
            tk = s.w(wd); k = ss(tk - .3, tk + .1, t); bubble(fr, 200 + i * 340, 1050 - (i % 2) * 120, msg, k)
            if t > tk + .5: stamp_in(fr, s.fake, 200 + i * 340, 1050 - (i % 2) * 120, t, tk + .5)
        blit(fr, hipo_label(), 540, 360)
    def cam(s, t, d): return lerp(1.06, 1.1, RG.ease(t / d)), 540, 1300, 0, 0

class Unknown(Si):                                 # ¿ataque? ¿desastre tecnológico? ¿algo peor?
    def __init__(s):
        s.back = NV.stage_bg(19, (10, 6, 14), (200, 60, 120)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 140, 180), 519, ymin=200, ymax=1700), 1.7)]
        s.items = [('ataque', '¿UN ATAQUE?'), ('desastre', '¿UN DESASTRE TECNOLÓGICO?'), ('algo', '¿ALGO PEOR?')]
        s.ch = [chip(x, (255, 140, 180), w=760) for _, x in s.items]
    def draw(s, fr, t, d):
        for i, (wd, _) in enumerate(s.items):
            tk = s.w(wd) - .2
            if t > tk: float_in(fr, s.ch[i], 540, 640 + i * 200, t, tk)
        for k in range(9): RG.person(fr, 'figura', 110 + k * 108, 1700 + (k % 2) * 40, 380, P(look=(0, -.3)), t + k)

class Government(Si):                              # el gobierno en la tele y la radio; la familia escucha
    def __init__(s):
        s.back, s.main = room_bg((60, 44, 40), (70, 50, 38), 20); s.front = [(bokeh_layer(6, (255, 220, 170), 520, ymin=200, ymax=1000), 1.7)]
        s.panel = N2.gold_panel('RADIO · TELEVISIÓN · SISTEMAS ALTERNATIVOS', w=980, h=150)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (560, 860), (1000, 1180), (30, 30, 34), -1); cv2.rectangle(fr, (580, 880), (980, 1150), (40, 60, 90), -1)   # televisión
        RG.person(fr, 'portavoz', 780, 1150, 260, P(look=(0, 0), frown=.3, blink=blinkp(t, 140)), t)
        cv2.rectangle(fr, (700, 1180), (860, 1220), (50, 50, 54), -1); cv2.putText(fr, 'AVISO OFICIAL', (600, 1140), cv2.FONT_HERSHEY_DUPLEX, .8, (255, 220, 120), 2, cv2.LINE_AA)
        cv2.rectangle(fr, (580, 1300), (1000, 1460), (90, 66, 46), -1)                                                          # mueble
        rx, ry = 700, 1270; cv2.rectangle(fr, (rx - 70, ry - 50), (rx + 70, ry + 30), (150, 110, 70), -1); cv2.circle(fr, (rx - 30, ry - 10), 22, (60, 50, 40), -1, cv2.LINE_AA)   # radio
        for k in range(3): f = (t * 1.2 + k / 3) % 1; cv2.ellipse(fr, (rx + 70, ry - 20), (int(20 + f * 60), int(20 + f * 60)), 0, -40, 40, (255, 220, 160), 2, cv2.LINE_AA)
        fy = 1720
        for i, (w_, x, h) in enumerate((('vecino', 220, 640), ('vecina', 420, 600))):
            u = U(w_, h); lean_in = RG.ease((t - .5 - i * .3) / .8)
            g = {'L': (x + .2 * u, fy - 6.3 * u, lean_in)} if i == 1 else {'R': (x + .5 * u, fy - 4.9 * u, lean_in)}
            RG.person_34(fr, w_, x, fy, h, P(look=(.5, -.05), lean=.05 * lean_in, frown=.3, brow_up=.2, grip=g, tz=.8, blink=blinkp(t, 141 + i)), t, feet=stance(x, u, fy), turn=1)
        float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): return lerp(1.04, 1.1, RG.ease(t / d)), 600, 1250, 0, 0

class Button(Si):                                  # el técnico aprieta el gran botón… y no pasa nada
    def __init__(s):
        bg = vgrad([(0, (6, 10, 16)), (1, (16, 24, 34))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1500, (20, 26, 34), (40, 52, 66))
        s.front = [(bokeh_layer(8, (120, 200, 255), 521, ymin=200, ymax=1200), 1.7)]
        s.t = N.text_sprite('NO ES PRESIONAR UN BOTÓN', 64, (255, 255, 255, 255), stroke=4, stroke_col=(0, 0, 0, 220))
    def draw(s, fr, t, d):
        for i in range(5): NV.rack(fr, 40 + i * 205, 620, 180, 760, t * 0 + 3.0, seed=i)                                    # racks apagados
        fr[620:1380] = (fr[620:1380].astype(np.float32) * .6).astype(np.uint8)
        bx, by = 760, 1330; cv2.rectangle(fr, (bx - 110, by), (bx + 110, by + 300), (60, 64, 74), -1)
        tb = s.w('presionar'); press = RG.ease((t - tb) / .25) * (1 - RG.ease((t - tb - .5) / .3))
        cv2.ellipse(fr, (bx, by + 4), (70, 26), 0, 0, 360, (120, 20, 20), -1, cv2.LINE_AA); cv2.ellipse(fr, (bx, int(by - 12 + 10 * press)), (60, 22), 0, 0, 360, (230, 40, 40), -1, cv2.LINE_AA)
        x, fy, h = 470, 1720, 680; u = U('medico', h)
        keys = [(0, P(look=(.4, .3), frown=.3)), (tb - .5, P(look=(.45, .4), frown=.4, grip={'R': (bx - 30, by - 20, 0.)}, tz=.6)),
                (tb, P(look=(.45, .45), lean=.06, frown=.45, grip={'R': (bx - 30, by - 10, 1.)}, tz=.6)),                                     # presiona
                (tb + .6, P(look=(.3, -.2), lean=.03, frown=.2, grip={'R': (bx - 40, by - 34, 1.)}, tz=.5)),
                (tb + 1.2, P(look=(.05, 0), frown=-.3, brow_asym=.4, boca='tensa', sh=-.4, grip={'L': (x - 1.1 * u, fy - 5 * u, 1.), 'R': (x + 1.2 * u, fy - 5 * u, 1.)}, tz=.6)),   # se encoge de hombros
                (d, P(look=(0, 0), frown=-.3, brow_asym=.35, boca='tensa', sh=-.3, grip={'L': (x - 1.05 * u, fy - 4.95 * u, 1.), 'R': (x + 1.15 * u, fy - 4.95 * u, 1.)}, tz=.6))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 150); RG.person_34(fr, 'medico', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        blit(fr, s.t, 540, 380, ss(tb + .7, tb + 1.1, t))
    def cam(s, t, d): return lerp(1.06, 1.12, RG.ease(t / d)), 560, 1280, 0, 0

# ================================================================ LA VERDAD
class NotOneMachine(Si):                           # no es una sola máquina: se divide en miles de nodos
    def __init__(s):
        s.back = NV.stage_bg(22, (6, 10, 16), (60, 200, 255)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (140, 220, 255), 522, ymin=200, ymax=1700), 1.7)]
        s.t = N.text_sprite('NO ES UNA SOLA MÁQUINA', 66, (255, 255, 255, 255), stroke=4, stroke_col=(0, 0, 0, 220))
    def draw(s, fr, t, d):
        k = ss(.6, 1.6, t)
        if k < 1: cv2.rectangle(fr, (440, 900), (640, 1200), (60, 70, 90), -1); cv2.rectangle(fr, (440, 900), (640, 1200), (140, 200, 255), 4)
        r_ = np.random.RandomState(5)
        for i in range(40):
            a_ = r_.uniform(0, 2 * math.pi); rr = r_.uniform(150, 460); x, y = 540 + math.cos(a_) * rr * k, 1050 + math.sin(a_) * rr * k * 1.2
            if k > 0: line(fr, (540, 1050), (x, y), (60, 140, 200), 1); cv2.rectangle(fr, (int(x - 18), int(y - 24)), (int(x + 18), int(y + 24)), (60, 70, 90), -1); cv2.rectangle(fr, (int(x - 18), int(y - 24)), (int(x + 18), int(y + 24)), (140, 200, 255), 2)
        blit(fr, s.t, 540, 420, ss(.1, .5, t))

class Infra(Si):                                   # cables submarinos · centros de datos · servidores · conexiones en todo el mundo
    def __init__(s):
        s.back = NV.stage_bg(23, (4, 10, 20), (40, 120, 220)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (120, 200, 255), 523, ymin=200, ymax=1700), 1.7)]
        s.labels = {k: chip(v, (140, 220, 255), w=560) for k, v in (('cables', 'CABLES SUBMARINOS'), ('centros', 'CENTROS DE DATOS'), ('servidores', 'SERVIDORES'), ('conexiones', 'CONEXIONES GLOBALES'))}
    def draw(s, fr, t, d):
        cuts = [s.w('centros') - .2, s.w('servidores') - .2, s.w('conexiones') - .2]
        for c in cuts:
            q = ss(c - .3, c, t)
            if 0 < q < 1: a_ = fr.copy(); s.part(a_, c - .3001); b_ = fr.copy(); s.part(b_, c + .0001, t); fr[:] = cv2.addWeighted(a_, 1 - q, b_, q, 0); return
        s.part(fr, t)
    def part(s, fr, t, tt=None):
        tt = t if tt is None else tt
        tc, td, ts, tx = s.w('cables'), s.w('centros'), s.w('servidores'), s.w('conexiones')
        if t < td - .2:                                                        # corte del océano: el cable en el lecho marino
            cv2.rectangle(fr, (0, 700), (W, 1700), (20, 50, 90), -1); poly(fr, [(0, 1500), (300, 1460), (600, 1520), (900, 1470), (1080, 1500), (1080, 1700), (0, 1700)], (60, 54, 40))
            pts = [(x, 1490 + math.sin(x / 90) * 12) for x in range(0, W + 1, 20)]; pline(fr, pts, (20, 20, 20), 14); pline(fr, pts, (230, 180, 60), 4)
            for k in range(6): f = (t * .6 + k / 6) % 1; circ(fr, (f * W, 1490 + math.sin(f * W / 90) * 12), 7, (255, 240, 160))
            cv2.rectangle(fr, (0, 690), (W, 706), (90, 150, 210), -1); float_in(fr, s.labels['cables'], 540, 560, t, tc - .2)
        elif t < ts - .2:
            for i in range(5): NV.rack(fr, 40 + i * 205, 700, 180, 860, t, seed=i)
            float_in(fr, s.labels['centros'], 540, 560, t, td - .2)
        elif t < tx - .2:
            for i in range(3): NV.rack(fr, 160 + i * 280, 760, 200, 760, t, seed=10 + i)
            float_in(fr, s.labels['servidores'], 540, 560, t, ts - .2)
        else:                                                                  # globo abstracto (solo meridianos y paralelos, sin fronteras)
            c, r = (540, 1150), 380; cv2.circle(fr, c, r, (14, 40, 80), -1, cv2.LINE_AA); cv2.circle(fr, c, r, (90, 170, 255), 4, cv2.LINE_AA)
            for k in range(-2, 3): cv2.ellipse(fr, c, (int(r * abs(math.cos(k * .55 + t * .3)) + 1), r), 0, 0, 360, (50, 110, 190), 2, cv2.LINE_AA); cv2.ellipse(fr, (c[0], int(c[1] + k * r * .38)), (int(r * math.sqrt(max(0, 1 - (k * .38) ** 2))), 12), 0, 0, 360, (50, 110, 190), 2, cv2.LINE_AA)
            r_ = np.random.RandomState(8)
            for i in range(14):
                a1, a2 = r_.uniform(0, 2 * math.pi, 2); p1 = (c[0] + math.cos(a1) * r * .8, c[1] + math.sin(a1) * r * .8); p2 = (c[0] + math.cos(a2) * r * .8, c[1] + math.sin(a2) * r * .8)
                mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 - 160); q = [(lerp(lerp(p1[0], mid[0], f), lerp(mid[0], p2[0], f), f), lerp(lerp(p1[1], mid[1], f), lerp(mid[1], p2[1], f), f)) for f in np.linspace(0, ss(0, 1, (t - tx) * 1.5 - i * .05), 20)]
                if len(q) > 1: pline(fr, q, (255, 200, 90), 3)
            float_in(fr, s.labels['conexiones'], 540, 560, t, tx - .2)

class Extreme(Si):                                 # desaparición total: extraordinaria · interrupción masiva: devastadora
    def __init__(s):
        s.back = NV.stage_bg(24, (10, 8, 14), (160, 100, 220)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (220, 180, 255), 524, ymin=200, ymax=1700), 1.7)]
        s.a = 0.; s.p1 = N2.blue_panel('DESAPARICIÓN TOTAL', 'ESCENARIO EXTRAORDINARIO', w=820, h=170); s.p2 = N2.red_panel('INTERRUPCIÓN MASIVA', w=820, h=150)
        s.c = chip('CONSECUENCIAS DEVASTADORAS', (255, 120, 100), w=760)
    def draw(s, fr, t, d):
        float_in(fr, s.p1, 540, 640, t, .2); tp = s.w('pero')
        if t > tp - .2: float_in(fr, s.p2, 540, 1000, t, tp - .2)
        if t > s.w('consecuencias') - .2: float_in(fr, s.c, 540, 1180, t, s.w('consecuencias') - .2)

# ================================================================ CIERRE
class SevenDays(Si):                               # ¿podrías vivir siete días sin Internet?
    def __init__(s):
        s.back = NV.stage_bg(25, (8, 12, 20), (90, 200, 255)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (150, 220, 255), 525, ymin=200, ymax=1700), 1.7)]
        s.items = [('trabajar', '💼', 'TRABAJAR'), ('comprar', '🛒', 'COMPRAR'), ('comunicarte', '📞', 'COMUNICARTE'), ('vivir', '🏠', 'VIVIR')]
        s.spr = [(emoji_sprite(e), label(n, 30)) for _, e, n in s.items]; s.q = N.text_sprite('¿7 DÍAS SIN INTERNET?', 72, (255, 236, 200, 255), glow=(255, 160, 40), glow_r=16, stroke=4, stroke_col=(0, 0, 0, 200))
    def draw(s, fr, t, d):
        for i, ((wd, _, _), (e, n)) in enumerate(zip(s.items, s.spr)):
            tk = s.w(wd) - .15; g = ss(tk, tk + .3, t)
            if g <= 0: continue
            x, y = [300, 780][i % 2], [700, 1100][i // 2]
            cv2.circle(fr, (x, y), 150, (20, 40, 60), -1); cv2.circle(fr, (x, y), 150, (120, 220, 255), 5); blit(fr, e, x, y - 20, g, .7); blit(fr, n, x, y + 95, g)
        for k in range(7):                                                     # calendario de siete días
            x = 130 + k * 137; ts_ = s.w('siete') + k * .12; g = ss(ts_, ts_ + .2, t)
            cv2.rectangle(fr, (x - 55, 1280), (x + 55, 1390), (240, 236, 228), -1); cv2.putText(fr, str(k + 1), (x - 14, 1355), cv2.FONT_HERSHEY_DUPLEX, 1.4, (60, 60, 70), 2, cv2.LINE_AA)
            if g > 0: line(fr, (x - 40, 1293), (x - 40 + 80 * g, 1293 + 84 * g), (230, 50, 50), 7)
        blit(fr, s.q, 540, 400, ss(s.w('siete') - .3, s.w('siete'), t))

class Friend(Si):                                  # el amigo pierde el Wi-Fi cinco minutos… y entra en pánico
    def __init__(s):
        s.back, s.main = room_bg((50, 40, 70), (70, 56, 44), 26); s.front = [(bokeh_layer(8, (255, 200, 255), 526, ymin=200, ymax=1100), 1.7)]
        s.cta = N2.gold_panel('MÁNDASELO A ESE AMIGO', 'QUE NO ES ADICTO AL CELULAR', w=900, h=180)
        s.q = N.text_sprite('¿SE ACABÓ EL MUNDO?', 76, (255, 236, 220, 255), glow=(255, 60, 40), glow_r=16, stroke=4, stroke_col=(0, 0, 0, 200)); s.pill = DT.Blockade(None, cta=True)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (120, 1380), (1000, 1560), (110, 60, 80), -1); cv2.rectangle(fr, (120, 1300), (1000, 1390), (130, 74, 96), -1)   # sofá
        tw, tp = s.w('wi-fi'), s.w('preguntando'); x, fy, h = 540, 1720, 700; u = U('peaton2', h); ph = (x + .45 * u, fy - 5.8 * u)
        panic = RG.ease((t - tp + .7) / 1.2)
        head = {'L': (x - 1.05 * u, fy - 7.0 * u, 1.), 'R': (x + 1.05 * u, fy - 7.0 * u, 1.)}
        keys = [(0, P(look=(0, .4), tilt=.04, frown=-.2, boca='sonrisa', grip={'R': ph + (1.,)}, tz=.9)),
                (tw, P(look=(0, .4), tilt=.04, frown=-.2, boca='sonrisa', grip={'R': ph + (1.,)}, tz=.9)),
                (tw + .4, P(look=(0, .4), tilt=.03, frown=-.3, brow_up=.6, boca='o', grip={'R': (ph[0], ph[1] - 10, 1.)}, tz=.9)),         # ¿y el Wi-Fi?
                (tp - .7, P(look=(.05, .35), frown=-.4, brow_up=.6, boca='tensa', grip={'R': (ph[0] + 10, ph[1] - 30, 1.)}, tz=.9)),
                (tp + .5, P(look=(0, -.1), frown=-.6, brow_up=1., boca='grito', sh=-.4, grip=head, tz=.4)),                                # manos a la cabeza
                (d, P(look=(0, -.1), frown=-.6, brow_up=.9, boca='grito', sh=-.35, grip=head, tz=.4))]
        p = RG.anim(keys, t); p['blink'] = 0. if t > tp else blinkp(t, 160)
        hands, _ = RG.person(fr, 'peaton2', x, fy, h, p, t, feet=stance(x, u, fy, .38))
        if t < tp: handphone(fr, hands['R'], lit=True, title='') if t > tw + .2 else None
        if t < tw + .2:
            hd = hands['R']; cv2.rectangle(fr, (int(hd[0] - 22), int(hd[1] - 76)), (int(hd[0] + 22), int(hd[1] + 4)), (20, 22, 28), -1); cv2.rectangle(fr, (int(hd[0] - 18), int(hd[1] - 70)), (int(hd[0] + 18), int(hd[1] - 4)), (60, 160, 220), -1)
        if t < tp: hands_on_top(fr, {'R': hands['R']}, 'peaton2', h)
        if t < tw:
            for k in range(3): cv2.ellipse(fr, (850, 640), ((k + 1) * 40, (k + 1) * 40), 0, 225, 315, (120, 230, 140), 10, cv2.LINE_AA)   # Wi-Fi encendido
        else:
            for k in range(3): cv2.ellipse(fr, (850, 640), ((k + 1) * 40, (k + 1) * 40), 0, 225, 315, (90, 90, 100), 10, cv2.LINE_AA)
            line(fr, (790, 560), (910, 680), (255, 60, 50), 12)
        if t > tp: blit(fr, s.q, 540, 800, ss(tp, tp + .3, t), lerp(1.3, 1, ss(tp, tp + .3, t)))
        float_in(fr, s.cta, 540, 340, t, .2)
        k = ss(tp + .8, tp + 1.2, t)
        if k > 0: blit(fr, s.pill.ctaspr, 540, 1840, k, lerp(.6, 1, eBack(k)) * .8)
    def cam(s, t, d): return lerp(1.04, 1.1, RG.ease(t / d)), 540, 1250, 0, 0

# ================================================================ línea de tiempo
def tl():
    seq = [(0, Wake(), 0), (T('no', 4) - .3, Apps(), 0), (T('pero', 11) - .3, Beginning(), 0),
           (SC_T[1], Streets(), 3), (T('los', 17) - .25, ATM(), 3), (T('y', 20.5) - .2, Banks(), 3),
           (T('en', 24) - .25, Lines(), 1), (T('la', 28) - .25, Register(), 1), (T('y', 33) - .25, HowLong(), 4),
           (SC_T[2], Office(), 1), (T('los', 38) - .25, Hospital(), 1), (T('los', 42) - .25, Airport(), 1), (T('los', 47) - .25, StillMoving(), 1),
           (T('pero', 51) - .25, Coordination(), 4),
           (SC_T[3], Danger(), 3), (T('sin', 58) - .25, Rumors(), 3), (T('la', 64) - .25, Unknown(), 4), (T('los', 69) - .25, Government(), 2), (T('pero', 74) - .25, Button(), 4),
           (SC_T[4], NotOneMachine(), 1), (T('es', 79.8) - .25, Infra(), 1), (T('una', 87.5) - .25, Extreme(), 4),
           (SC_T[5], SevenDays(), 1), (T('mándaselo') - .3, Friend(), 2)]
    out = []
    for i, (a, sc, g) in enumerate(seq):
        b = seq[i + 1][0] if i + 1 < len(seq) else DUR; sc.a = a; out.append((a, b, sc, g))
    return out

KEYW = {'internet', 'desaparecido', 'whatsapp', 'redes', 'dinero', 'comienzo', 'millones', 'cajeros', 'terminales', 'bancos', 'avalancha', 'supermercados', 'interminables',
        'comida', 'cobro', 'inventarios', 'durar', 'empresas', 'hospitales', 'aeropuertos', 'suministro', 'camiones', 'aviones', 'difícil', 'peligro', 'rumores', 'falsas',
        'pánico', 'ataque', 'peor', 'gobiernos', 'radio', 'televisión', 'botón', 'máquina', 'cables', 'submarinos', 'datos', 'servidores', 'mundo', 'extraordinario',
        'devastadoras', 'siete', 'días', 'amigo', 'celular', 'wi-fi', 'acabó'}

_s = CH._src.replace("secs = [(0, 'tension', 1), (9.9, 'misterio', 2), (24.1, 'tension', 2), (37.2, 'epico', 2), (50.2, 'tension', 1)]",
     f"secs = [(0, 'misterio', 1), ({SC_T[1]:.2f}, 'tension', 2), ({SC_T[2]:.2f}, 'epico', 2), ({SC_T[3]:.2f}, 'tension', 2), ({SC_T[4]:.2f}, 'misterio', 2), ({SC_T[5]:.2f}, 'epico', 1)]")
_a = _s.index('    EF = ['); _b = _s.index(']]', _a) + 2
_ef = [[0, 'latido', .3], [T('desaparecido'), 'glitch', .2]]
for (a_, b_, sc, g) in tl()[1:]: _ef += [[a_ - .25, 'whoosh', .3], [a_, 'impacto', .3]]
_ef += [[T('comienzo'), 'boom', .6], [T('cajeros'), 'beep', .2], [T('fallan'), 'beep', .2], [T('avalancha'), 'caida', .3], [T('peligro'), 'boom', .7],
        [T('rumores'), 'glitch', .15], [T('presionar') + .3, 'beep', .25], [T('devastadoras'), 'impacto', .6], [T('siete'), 'riser', .25], [T('preguntando'), 'impacto', .5], [T('mundo', 107), 'ding', .3]]
_s = _s[:_a] + '    EF = ' + repr(sorted(_ef, key=lambda e: e[0])) + _s[_b:]
_s = _s.replace("env / (env.max() * .25)", "env / (env.max() * .25 + 1e-9)").replace("duck = 1 - .55 * env", "duck = 1 - .7 * env").replace(
    "out = np.tanh((mus * .75 * duck + fx * .6 * (1 - .35 * env)) * 1.1) * .8 + vv * .92", "out = np.tanh((mus * .5 * duck + fx * .32 * (1 - .5 * env)) * 1.1) * .7 + vv * .95")
_g = dict(globals()); _g['EMOJIS'] = []; exec(_s, _g); synth_audio = _g['synth_audio']

def make_frame():
    TR.DUR = DUR; TR.KEY = KEYW
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in TR.build_subs(WORDS)]
    shots = tl(); pill = DT.Blockade(None, cta=True); C0, C1 = T('millones') + 3, T('las', 19) + 2
    def one(i, T_):
        a, b, sc, g = shots[i]; CTX['shot'] = i; CTX['counts'] = {}
        return cinema(render3d(sc, T_ - a, b - a, T_), g, T_)
    def frame(T_, f=-1, rec=False):
        CTX['f'], CTX['rec'] = f, rec
        i = max(k for k, s_ in enumerate(shots) if T_ >= s_[0] - 1e-6)
        fr = one(i, T_); a = shots[i][0]
        if i > 0 and T_ - a < .3: CTX['rec'] = False; fr = cv2.addWeighted(one(i - 1, T_), 1 - ss(0, .3, T_ - a), fr, ss(0, .3, T_ - a), 0)
        clean = fr.copy(); c = ss(C0, C0 + .4, T_) * (1 - ss(C1 - .3, C1, T_))
        if c > 0: blit(fr, pill.ctaspr, 760, 1720, c, lerp(.6, 1, eBack((T_ - C0) / .4)) * .6); blit(fr, pill.bell, 1010, 1700 + math.sin(T_ * 9) * 4, c, .4)
        draw_overlays(fr, T_, subs, []); return fr, clean, i
    return frame, shots

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'info'
    frame, shots = make_frame()
    if mode == 'info':
        for i, (a, b, sc, g) in enumerate(shots): print(f'{i:2d} {a:6.2f}-{b:6.2f} {b - a:5.2f} {type(sc).__name__}')
    elif mode == 'test':
        os.makedirs(f'{OUTI}/test', exist_ok=True)
        for T_ in [float(x) for x in sys.argv[2:]]: cv2.imwrite(f'{OUTI}/test/n_{T_:06.2f}.jpg', cv2.resize(frame(T_)[0], (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1])
    elif mode in ('seg', 'qcshot'):
        if mode == 'seg': f0, f1 = int(sys.argv[2]), int(sys.argv[3]); tag = f'{f0:05d}'; D_ = OUTI
        else: i = int(sys.argv[2]); f0, f1 = int(math.ceil(shots[i][0] * FPS)), int(math.ceil(shots[i][1] * FPS)); tag = f'shot{i:02d}'; D_ = f'{OUTI}/iter'
        os.makedirs(f'{D_}/thumbs', exist_ok=True); p = None
        if mode == 'seg':
            p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', f'{OUTI}/seg_{f0:05d}.mp4'], stdin=subprocess.PIPE)
        diffs = {}; prev = None
        if f0 > 0: prev = cv2.resize(frame((f0 - 1) / FPS)[1], (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
        CTX['log'] = []
        for f in range(f0, f1):
            fr, clean, si = frame(f / FPS, f, True); small = cv2.resize(clean, (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
            if prev is not None: diffs[f] = float(np.abs(small - prev).mean())
            prev = small
            if f % 3 == 0: cv2.imwrite(f'{D_}/thumbs/t_{f:05d}.jpg', cv2.resize(clean, (180, 320), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 80])
            if p: p.stdin.write(np.ascontiguousarray(fr).tobytes())
        if p: p.stdin.close(); p.wait()
        json.dump(dict(log=CTX['log'], diffs=diffs, f0=f0, f1=f1), open(f'{D_}/qc_{tag}.json', 'w'))
        print('SEG' if mode == 'seg' else 'QCSHOT', f0, f1, flush=True)
    elif mode == 'audio': synth_audio(f'{OUTI}/audio.wav'); print('audio ok')

if __name__ == '__main__': main()
