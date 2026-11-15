#!/usr/bin/env python3
# Short: ¿Qué pasaría si Trump invadiera México para destruir a los cárteles? (escenario hipotético)
# 1080x1920 · 30 fps · estilo 2.5D de la plantilla (reutiliza las piezas del short de El Chapo).
import os, sys, re, json
HERE_T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE_T, '..', 'chapo'))
import detalle as DT
from detalle import *

OUT = os.path.join(HERE_T, 'out'); os.makedirs(OUT, exist_ok=True)
WORDS = json.load(open(os.path.join(HERE_T, 'words.json')))
VOZ = os.path.join(HERE_T, 'voz.mp3')
def _clean(w): return w.strip('¿?¡!.,…:;').lower()
def T(word, after=-1.):
    """inicio (s) de la primera aparición de la palabra a partir del segundo `after`."""
    for w in WORDS:
        if w[1] >= after and _clean(w[0]).startswith(word.lower()): return w[1]
    raise KeyError(word)
DUR = int(math.ceil(WORDS[-1][2] + 1.8))
SC_T = [0, T('primero') - .35, T('segundo') - .35, T('tercero') - .35, T('aquí') - .45, T('entonces') - .5, T('dime') - .6, DUR]

class Sh(Shot):
    a = 0.
    def w(s, word): return T(word, s.a - .6) - s.a          # tiempo local de una palabra dentro de la toma

def fbeam(fr, *a):
    f = fr.astype(np.float32); beam(f, *a); fr[:] = to8(f)
def float_in(fr, spr, x, y, t, t0, sc0=1.3, op=1., wob=5):
    k = ss(t0, t0 + .4, t)
    if k > 0: blit(fr, spr, x, y + math.sin(t * 1.5) * wob, k * op, lerp(sc0, 1, eOut((t - t0) / .4)))
def stamp_in(fr, spr, x, y, t, t0):
    k = ss(t0, t0 + .3, t)
    if k > 0: blit(fr, spr, x, y, k, lerp(1.6, 1., eOut(k)))

def mini_map(img, x0, y0, w, h, col=(255, 60, 40), others=(60, 90, 130)):
    """contorno de Norteamérica y México dentro de una caja (para pantallas y hologramas)."""
    lo0, lo1, la0, la1 = -125., -82., 12., 50.
    def P(p): return np.stack([x0 + (p[:, 0] - lo0) / (lo1 - lo0) * w, y0 + (la1 - p[:, 1]) / (la1 - la0) * h], 1)
    for p in (NA, CA, sCUBA):
        q = np.round(P(p) * 8).astype(np.int32); cv2.fillPoly(img, [q], others, cv2.LINE_AA, 3); cv2.polylines(img, [q], True, tuple(min(255, c + 60) for c in others), 2, cv2.LINE_AA, 3)
    q = np.round(P(MX) * 8).astype(np.int32); cv2.fillPoly(img, [q], dark(col, .55), cv2.LINE_AA, 3); cv2.polylines(img, [q], True, col, 4, cv2.LINE_AA, 3)
    return P

def wave_flag(spr, t, amp=10, k=.018, sp=3.):
    h, w = spr.shape[:2]; xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    off = np.sin(xx * k - t * sp) * amp * (xx / w)
    out = cv2.remap(spr, xx, yy - off, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    shade = (1 + .18 * np.cos(xx * k - t * sp))[:, :, None]
    out[:, :, :3] = np.clip(out[:, :, :3] * shade, 0, 255).astype(np.uint8); return out
def flag_sprite(mx, w=440, h=280):
    f = np.zeros((h, w, 3), np.uint8); (flag_mx if mx else flag_us)(f, 0, 0, w, h)
    if mx:
        cv2.circle(f, (w // 2, h // 2), int(h * .17), (150, 100, 50), -1, cv2.LINE_AA); cv2.circle(f, (w // 2, h // 2), int(h * .1), (90, 130, 60), -1, cv2.LINE_AA)
    else:
        for r in range(4):
            for c in range(5): cv2.circle(f, (int(w * .42 / 6 * (c + .8)), int(h * .54 / 5 * (r + .8))), 5, (240, 240, 240), -1, cv2.LINE_AA)
    return np.dstack([f, np.full((h, w), 255, np.uint8)])

def jet(fr, x, y, sc, t, col=(120, 128, 140)):
    P = lambda px, py: (x + px * sc, y + py * sc)
    poly(fr, [P(-150, 0), P(110, -14), P(170, 0), P(110, 14)], col)                              # fuselaje
    poly(fr, [P(-10, -6), P(40, -6), P(-60, -110), P(-90, -110)], dark(col, .8))                # ala lejana
    poly(fr, [P(-10, 6), P(40, 6), P(-70, 120), P(-100, 120)], col)                              # ala cercana
    poly(fr, [P(-150, -4), P(-110, -4), P(-140, -60), P(-160, -60)], dark(col, .75))            # timón
    poly(fr, [P(70, -10), P(120, -8), P(100, -18), P(80, -18)], (60, 120, 170))                  # cabina
    blit(fr, glow_sprite(int(40 * sc) + 4, (255, 160, 60)), *P(-165, 0), .8 + .2 * math.sin(t * 30), 1.4, add=True)
    blit(fr, glow_sprite(int(14 * sc) + 3, (255, 40, 40)), *P(-95, 120), .5 + .5 * math.sin(t * 7), add=True)

def truck(fr, x, y, sc, col=(70, 82, 56), star=True):
    P = lambda px, py: (x + px * sc, y + py * sc)
    poly(fr, [P(0, -150), P(250, -150), P(250, -30), P(0, -30)], dark(col, .85))                 # caja con lona
    for k in range(4): line(fr, P(20 + k * 60, -150), P(20 + k * 60, -30), dark(col, .65), 3)
    poly(fr, [P(255, -110), P(330, -110), P(360, -70), P(360, -30), P(255, -30)], col)           # cabina
    poly(fr, [P(275, -100), P(325, -100), P(345, -72), P(275, -72)], (60, 90, 120))
    if star: blit(fr, N.text_sprite('★', int(36 * sc) + 6, (236, 236, 236, 255), pad=4), *P(305, -50))
    for px in (60, 190, 310): circ(fr, P(px, -22), 30 * sc, (20, 20, 22)); circ(fr, P(px, -22), 13 * sc, (90, 90, 96))

def semi(fr, x, y, sc, body=(210, 214, 220), cab=(170, 40, 40)):
    P = lambda px, py: (x + px * sc, y + py * sc)
    poly(fr, [P(0, -200), P(330, -200), P(330, -30), P(0, -30)], body)
    line(fr, P(10, -110), P(320, -110), dark(body, .8), 3)
    poly(fr, [P(340, -150), P(420, -150), P(450, -100), P(450, -30), P(340, -30)], cab)
    poly(fr, [P(360, -140), P(410, -140), P(432, -104), P(360, -104)], (60, 90, 120))
    for px in (40, 100, 250, 300, 400): circ(fr, P(px, -22), 24 * sc, (20, 20, 22)); circ(fr, P(px, -22), 10 * sc, (90, 90, 96))

def facade(i8, y0, y1, col=(118, 52, 40)):
    """fachada colonial larga (tipo palacio de gobierno) con arcos y ventanas iluminadas."""
    cv2.rectangle(i8, (-10, y0), (W + 10, y1), col, -1)
    cv2.rectangle(i8, (-10, y0 - 30), (W + 10, y0), dark(col, .7), -1)
    for row, yy in enumerate((y0 + 70, y0 + 300)):
        for x in range(40, W, 130):
            cv2.rectangle(i8, (x, yy), (x + 70, yy + 150), (255, 206, 130) if (x // 130 + row) % 3 else (180, 140, 90), -1)
            cv2.ellipse(i8, (x + 35, yy), (35, 30), 0, 180, 360, (255, 206, 130), -1)
            cv2.rectangle(i8, (x - 8, yy + 150), (x + 78, yy + 162), dark(col, .6), -1)
    cv2.rectangle(i8, (380, y0 + 260), (700, y0 + 290), (60, 50, 44), -1)                  # balcón central
    for x in range(390, 700, 22): cv2.line(i8, (x, y0 + 260), (x, y0 + 230), (60, 50, 44), 4)
    cv2.rectangle(i8, (440, y1 - 260), (640, y1), (190, 140, 80), -1); cv2.ellipse(i8, (540, y1 - 260), (100, 70), 0, 180, 360, (190, 140, 80), -1)

def mic_podium(fr, x, y, seal_col=(200, 170, 90), body=(60, 40, 30)):
    poly(fr, [(x - 140, y), (x + 140, y), (x + 110, y + 320), (x - 110, y + 320)], body); cv2.circle(fr, (x, y + 120), 50, seal_col, 4, cv2.LINE_AA)
    for k in (-60, 0, 60): line(fr, (x + k, y), (x + k * .3, y - 90), (40, 40, 44), 5); circ(fr, (x + k * .3, y - 96), 12, (20, 20, 24))

# ================================================================ GANCHO
class Oval(Sh):
    def __init__(s):
        wf = vgrad([(0, (14, 18, 36)), (1, (26, 30, 52))]); i8 = to8(wf)
        for x in (70, 880): flag_us(i8, x, 300, 150, 96); cv2.line(i8, (x - 4, 280), (x - 4, 1150), (200, 170, 90), 6)
        cv2.rectangle(i8, (250, 200), (830, 760), (8, 30, 50), -1); cv2.rectangle(i8, (250, 200), (830, 760), (120, 230, 255), 5)
        mini_map(i8, 270, 220, 540, 520)
        for y in range(206, 756, 8): cv2.line(i8, (256, y), (824, y), (12, 40, 60), 1)
        s.back = [(dof(opaque(i8.astype(np.float32)), 2.5), .4)]
        s.main = floor_layer(1360, (40, 34, 30), (56, 48, 44))
        s.front = [(bokeh_layer(10, (255, 210, 140), 201, ymin=200, ymax=1300), 1.7)]
        s.title = DT.RS.red_panel('¿TRUMP INVADIRÍA MÉXICO?', w=880, h=160)
        s.hipo = N.text_sprite('ESCENARIO HIPOTÉTICO', 30, (255, 230, 170, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=6)
        s.target = glow_sprite(90, (255, 50, 40))
    def draw(s, fr, t, d):
        tx, ty = 565, 590                                    # México en la pantalla del fondo
        blit(fr, s.target, tx, ty, .4 + .4 * math.sin(t * 5), add=True)
        for k in range(2):
            f = (t * .7 + k * .5) % 1; cv2.circle(fr, (tx, ty), int(20 + f * 90), (int(255 * (1 - f)), int(60 * (1 - f)), 40), 3, cv2.LINE_AA)
        pt = ss(.4, 1.0, t)
        character(fr, 'traje', 540, 1640, 620, t, armR=('apunta', (720, 600), pt), armL=('jarra',), look=(.3, -.1), frown=.35, hair='rubio')
        cv2.rectangle(fr, (120, 1340), (960, 1380), (120, 70, 34), -1); cv2.rectangle(fr, (150, 1380), (930, 1640), (86, 46, 22), -1)   # escritorio
        cv2.circle(fr, (540, 1500), 70, (200, 170, 90), 4, cv2.LINE_AA); cv2.circle(fr, (540, 1500), 52, (40, 50, 110), -1, cv2.LINE_AA)
        blit(fr, s.hipo, 540, 140, ss(.2, .6, t))
        if s.title is not None: float_in(fr, s.title, 540, 900, t, s.w('méxico'))
    def cam(s, t, d):
        k = eExpo(t / 1.5); return lerp(2.0, 1.05, k) * (1 + .05 * ss(1.5, d, t)), 540, lerp(1300, 1000, k), lerp(-30, 30, eIO(t / d)) * ss(1, 2.5, t), 0

class Flags(Sh):
    def __init__(s):
        bg = vgrad([(0, (6, 8, 16)), (1, (20, 14, 22))]); radial(bg, (540, 900), 600, (90, 40, 60), .3)
        s.back = [(dof(opaque(bg), 2), .2)]
        s.main = floor_layer(1450, (18, 16, 22), (30, 28, 36))
        s.front = [(bokeh_layer(12, (255, 200, 160), 202, ymin=200, ymax=1700), 1.7)]
        s.us, s.mx = flag_sprite(False), flag_sprite(True)
        s.panel = N.holo_panel(760, 150, 'LA HISTORIA CAMBIARÍA', 'DOS PAÍSES · UN CONFLICTO', col=(255, 210, 90), fill=(60, 40, 6, 190))
    def draw(s, fr, t, d):
        sep = lerp(0, 50, ss(.3, 1.2, t))
        for spr, x, ph in ((s.us, 290 - sep, 0), (s.mx, 790 + sep, 1.7)):
            line(fr, (x - 220, 700), (x - 220, 1450), (200, 170, 90), 8)
            blit(fr, wave_flag(spr, t + ph), x, 840, 1, 1.0)
        # grieta luminosa entre las dos banderas
        k = ss(.5, 1.0, t); pts = [(540, 560), (520, 700), (556, 820), (526, 960), (552, 1100), (534, 1250)]
        pts = pts[:max(2, int(len(pts) * k))]
        blit(fr, glow_sprite(160, (255, 80, 50)), 540, 900, .35 * k, 1.2, add=True); pline(fr, pts, (255, 120, 80), 8 * k + 1); pline(fr, pts, (255, 240, 220), 3)
        float_in(fr, s.panel, 540, 400, t, .4)

# ================================================================ PRIMERO: ventaja militar, laboratorios y fragmentación
class Jets(Sh):
    def __init__(s):
        sky = vgrad([(0, (4, 6, 16)), (.6, (20, 26, 52)), (1, (60, 40, 50))])
        for i in range(220): x, y = rng.randint(0, W), rng.randint(0, 1000); sky[y:y + 2, x:x + 2] += rng.uniform(40, 160)
        s.back = [(dof(opaque(sky), 2), .1)]
        gr = np.zeros((H, W, 3), np.uint8); gr[1350:] = (14, 16, 22); r_ = np.random.RandomState(7)
        for i in range(260): cv2.circle(gr, (r_.randint(0, W), r_.randint(1360, 1500)), r_.randint(1, 3), (255, 190, 110), -1)
        mini_map(gr, 160, 1500, 760, 600, col=(255, 70, 50), others=(30, 46, 70))
        al = np.zeros((H, W)); al[1350:] = 1
        s.back.append((dof(haze(rgba(gr, al), (30, 30, 50), .2), 1.5), .5))
        s.main = np.zeros((H, W, 4), np.uint8)
        cl_ = np.zeros((H, W, 4), np.uint8)
        for i in range(14): cv2.ellipse(cl_, (int(r_.uniform(-100, W + 100)), int(r_.uniform(300, 1300))), (int(r_.uniform(160, 300)), int(r_.uniform(40, 80))), 0, 0, 360, (60, 66, 90, 120), -1, cv2.LINE_AA)
        s.front = [(dof(cl_, 16), 1.6)]
        s.panel = N.holo_panel(700, 150, 'OPERACIÓN MILITAR', 'VENTAJA AÉREA · EE. UU.', col=(255, 90, 70), fill=(50, 8, 8, 190))
    def draw(s, fr, t, d):
        for i, (dx, dy, sc) in enumerate([(0, 0, 1.0), (-230, -130, .8), (-230, 140, .85), (-430, -40, .6)]):
            u = t / d; x = lerp(-200, 1250, u) + dx * .2; y = lerp(900, 560, u) + dy
            jet(fr, x + dx + 300, y, sc * 1.1, t + i)
        sw = 380 + 260 * math.sin(t * .9)
        fbeam(fr, (sw, 1350), (sw + 200, 300), 10, 120, (180, 220, 255), .12, 30)
        float_in(fr, s.panel, 540, 330, t, .3)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.08, 1.18, k), 540, 1000, lerp(60, -60, k), 0

class Raid(Sh):
    def __init__(s):
        sky = vgrad([(0, (6, 8, 14)), (1, (40, 30, 34))]); s.back = [(dof(opaque(sky), 2), .1)]
        hills = np.zeros((H, W, 3), np.uint8); poly(hills, [(-50, 1250), (200, 1080), (420, 1180), (700, 1030), (1000, 1160), (1130, 1100), (1130, 1300), (-50, 1300)], (30, 26, 30))
        s.back.append((dof(haze(rgba(hills, np.any(hills > 0, 2).astype(np.float32)), (40, 30, 34), .3), 3), .35))
        gnd = np.zeros((H, W, 3), np.uint8); gnd[1260:] = (56, 46, 38)
        for j in range(1, 8): y = int(1260 + (H - 1260) * (j / 7.) ** 1.7); cv2.line(gnd, (0, y), (W, y), (66, 54, 44), 2)
        # laboratorio clandestino: galera de lámina con tambos
        cv2.rectangle(gnd, (560, 1000), (980, 1260), (70, 66, 60), -1); poly(gnd, [(540, 1000), (1000, 1000), (940, 930), (600, 930)], (90, 84, 76))
        for x in range(570, 980, 36): cv2.line(gnd, (x, 1000), (x, 1260), (60, 56, 52), 3)
        cv2.rectangle(gnd, (700, 1110), (800, 1260), (255, 190, 110), -1)
        for x in (600, 650, 880, 930): cv2.rectangle(gnd, (x, 1190), (x + 40, 1260), (40, 80, 140), -1); cv2.line(gnd, (x, 1205), (x + 40, 1205), (90, 140, 200), 3)
        al = np.zeros((H, W)); al[1260:] = 1; al[930:1260, 540:1000] = np.any(gnd[930:1260, 540:1000] > 0, 2)
        s.main = rgba(gnd, al)
        brush = np.zeros((H, W, 4), np.uint8)
        for i in range(16): cv2.ellipse(brush, (int(i * 75), 1840 + (i % 3) * 30), (90, 70), 0, 180, 360, (20, 24, 16, 255), -1)
        s.front = [(dof(brush, 9), 1.5), (bokeh_layer(8, (255, 200, 140), 203, ymin=200, ymax=1100), 1.7)]
        s.puff = glow_sprite(120, (90, 86, 84))
        s.panel = N.holo_panel(700, 150, 'OBJETIVO: LABORATORIOS', 'Y CAPTURA DE CAPOS', col=(255, 90, 70), fill=(50, 8, 8, 190))
        s.stamp = N.stamp('NO ES EL FIN', (255, 59, 42), w=640, px=86)
    def draw(s, fr, t, d):
        for i in range(10):
            f = (i / 10. + t * .06) % 1; blit(fr, s.puff, 640 + (i % 3) * 120 + f * 80, 930 - f * 600, min(1, f * 5) * (1 - f) * .45, 1 + f * 2)
        hx = lerp(950, 600, ss(0, d, t)); CH.heli(fr, hx, 470, 1.2, t, col=(70, 78, 70))
        fbeam(fr, (hx, 520), (hx - 60, 1250), 14, 160, (220, 240, 255), .14, 30)
        for i, (x0, fy, h) in enumerate([(120, 1640, 400), (330, 1560, 340), (-20, 1520, 300)]):
            x = x0 + 120 * ss(0, d, t)
            hs = character(fr, 'militar', x, fy, h, t + i, armR=('apunta', (x + 260, fy - h * .62), .85), armL=('apunta', (x + 260, fy - h * .62), .45), look=(.5, 0), frown=.4, run=4)
            lib.rifle(fr, hs, h / 8.)
        a = ss(s.w('laboratorios') - .1, s.w('laboratorios') + .3, t) * (1 - ss(s.w('significa') - .2, s.w('significa'), t))
        if a > 0: blit(fr, s.panel, 540, 330 + math.sin(t * 1.5) * 5, a)
        stamp_in(fr, s.stamp, 540, 330, t, s.w('significa'))

class Fragment(D.S3D):
    a = 0.
    def __init__(s):
        super().__init__()
        s.title = DT.RS.red_panel('FRAGMENTACIÓN', w=660, h=170); s.spark = glow_sprite(40, (255, 210, 120))
        s.c = A(*prj(-104.5, 24.5)); r_ = np.random.RandomState(3)
        s.dirs = [A(math.cos(a_), math.sin(a_) * .8) for a_ in np.linspace(0, 2 * math.pi, 7)[:-1] + .3]
        s.lb = N.text_sprite('NUEVAS DISPUTAS', 34, (255, 230, 200, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=5)
    def draw(s, fr, t, d):
        sp = eOut(ss(.6, 2.2, t)); pul = .5 + .5 * math.sin(t * 5)
        if sp < .05:
            ov = fr.copy(); cv2.circle(ov, tuple(int(v) for v in s.c), 170, (180, 24, 18), -1, cv2.LINE_AA); fr[:] = cv2.addWeighted(fr, .45, ov, .55, 0)
        cells = [s.c + dv * 230 * sp for dv in s.dirs]
        for i, p in enumerate(cells):
            r = lerp(170, 64, sp) + 6 * math.sin(t * 6 + i)
            ov = fr.copy(); cv2.circle(ov, (int(p[0]), int(p[1])), int(r), (180, 24, 18), -1, cv2.LINE_AA); fr[:] = cv2.addWeighted(fr, .5, ov, .5, 0)
            cv2.circle(fr, (int(p[0]), int(p[1])), int(r), (255, 90, 70), 3, cv2.LINE_AA)
        if sp > .6:
            for i in range(len(cells)):
                a_, b_ = cells[i], cells[(i + 1) % len(cells)]; m = (a_ + b_) / 2
                for q in range(2): blit(fr, s.spark, m[0] + math.sin(t * 9 + i + q) * 14, m[1] + math.cos(t * 7 + i) * 10, (.5 + .5 * math.sin(t * 14 + i * 2 + q)) * pul, add=True)
                pline(fr, [tuple(a_ + (b_ - a_) * .3), tuple(a_ + (b_ - a_) * .7)], (255, 200, 120), 2)
    def floating(s, fr, t, d, P):
        float_in(fr, s.title, 540, 330, t, .3)
        if t > 2.4: float_in(fr, s.lb, 540, 470, t, 2.4)
        s.dust.draw(fr, t)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.5, 1.7, k), 470, 1080, lerp(-30, 30, k), 0

# ================================================================ SEGUNDO: soberanía, tropas sin autorización, respuesta y cooperación
class Palace(Sh):
    def __init__(s):
        sky = vgrad([(0, (6, 8, 18)), (1, (24, 26, 44))]); i8 = to8(sky); facade(i8, 520, 1300)
        cv2.line(i8, (540, 140), (540, 520), (200, 200, 210), 6); flag_mx(i8, 544, 160, 300, 180)
        s.back = [(dof(opaque(i8.astype(np.float32)), 2.5), .4)]
        s.main = floor_layer(1300, (54, 50, 48), (70, 66, 62))
        crowd = np.zeros((H, W, 4), np.uint8)
        for i in range(14): cv2.circle(crowd, (int(i * 85 - 20), 1790 + (i % 2) * 40), 66, (10, 10, 14, 255), -1)
        s.front = [(dof(crowd, 9), 1.5), (bokeh_layer(10, (255, 210, 150), 204, ymin=300, ymax=1300), 1.7)]
        s.panel = DT.RS.red_panel('CRISIS DE SOBERANÍA', w=820, h=170)
    def draw(s, fr, t, d):
        cv2.ellipse(fr, (540, 1594), (170, 22), 0, 0, 360, (20, 18, 18), -1, cv2.LINE_AA)
        character(fr, 'dama', 540, 1590, 500, t, armR=('reposo',), armL=('reposo',), look=(0, -.05), frown=0, sash=True, hair='coleta')
        float_in(fr, s.panel, 540, 330, t, max(.2, s.w('soberanía') - .2))
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.04, 1.13, k), 540, lerp(1000, 1080, k), 0, 0

class Border(Sh):
    def __init__(s):
        sky = vgrad([(0, (8, 8, 16)), (1, (50, 36, 40))]); s.back = [(dof(opaque(sky), 2), .1)]
        far = np.zeros((H, W, 3), np.uint8); poly(far, [(-50, 1150), (300, 1040), (640, 1120), (1130, 1020), (1130, 1200), (-50, 1200)], (34, 28, 34))
        s.back.append((dof(haze(rgba(far, np.any(far > 0, 2).astype(np.float32)), (50, 36, 40), .3), 3), .35))
        g = np.zeros((H, W, 3), np.uint8); g[1200:] = (60, 50, 42); al = np.zeros((H, W)); al[1200:] = 1
        for x in list(range(-10, 380, 26)) + list(range(700, W + 20, 26)):   # muro fronterizo con un hueco al centro
            cv2.rectangle(g, (x, 760), (x + 14, 1230), (110, 90, 70), -1); al[760:1230, max(0, x):x + 14] = 1
        cv2.rectangle(g, (380, 1180), (700, 1240), (80, 80, 86), -1)
        s.main = rgba(g, al)
        s.front = [(bokeh_layer(10, (255, 120, 80), 205, ymin=200, ymax=1500), 1.7)]
        s.sign = N.text_sprite('FRONTERA · MÉXICO', 34, (240, 230, 210, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=6)
        s.stamp = N.stamp('SIN AUTORIZACIÓN', (255, 59, 42), w=780, px=74)
    def draw(s, fr, t, d):
        for i in range(3):
            x = lerp(-420, 1180, ((t / 4.2) + i * .34) % 1.2 - .1)
            truck(fr, x, 1300 + i * 0, 1.05, star=True)
        blit(fr, s.sign, 540, 700)
        on = (t * 2.2) % 1 < .5
        blit(fr, glow_sprite(60, (255, 40, 40) if on else (40, 90, 255)), 380, 750, .8, add=True); blit(fr, glow_sprite(60, (40, 90, 255) if on else (255, 40, 40)), 700, 750, .8, add=True)
        for i, x in enumerate((180, 900)):
            hs = character(fr, 'militar', x, 1660, 360, t + i, armR=('apunta', (x + (220 if x < 540 else -220), 1440), .8), armL=('apunta', (x + (220 if x < 540 else -220), 1440), .4), look=(.4 if x < 540 else -.4, 0), frown=.4)
            lib.rifle(fr, hs, 360 / 8.)
        stamp_in(fr, s.stamp, 540, 400, t, s.w('autorización'))
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.05, 1.14, k), 540, 1100, lerp(-60, 60, k), 0

class Note(Sh):
    def __init__(s):
        bg = vgrad([(0, (14, 18, 30)), (1, (24, 28, 44))]); i8 = to8(bg)
        for x in (120, 760): flag_mx(i8, x, 260, 200, 124); cv2.line(i8, (x - 4, 240), (x - 4, 1100), (200, 170, 90), 6)
        cv2.rectangle(i8, (330, 220), (750, 560), (120, 30, 40), -1); cv2.circle(i8, (540, 390), 110, (200, 170, 90), 6, cv2.LINE_AA)
        s.back = [(dof(opaque(i8.astype(np.float32)), 3), .4)]
        s.main = floor_layer(1350, (30, 30, 36), (44, 44, 52))
        crowd = np.zeros((H, W, 4), np.uint8)
        for i in range(14): cv2.circle(crowd, (int(i * 85 - 20), 1760 + (i % 2) * 40), 64, (10, 10, 14, 255), -1)
        s.front = [(dof(crowd, 9), 1.5), (bokeh_layer(10, (220, 230, 255), 206, ymin=300, ymax=1500), 1.7)]
        s.panel = N.holo_panel(720, 170, 'NOTA DIPLOMÁTICA', 'RESPUESTA POLÍTICA', col=(255, 210, 90), fill=(60, 40, 6, 190))
        s.doc = np.zeros((150, 120, 4), np.uint8); cv2.rectangle(s.doc, (2, 2), (117, 147), (240, 236, 226, 255), -1)
        for k in range(6): cv2.line(s.doc, (14, 26 + k * 18), (104 - (k * 13) % 30, 26 + k * 18), (120, 120, 130, 255), 3)
        cv2.circle(s.doc, (90, 128), 13, (190, 40, 40, 255), -1)
    def draw(s, fr, t, d):
        character(fr, 'dama', 540, 1400, 480, t, armR=('palma',) if (t % 2.2) < 1.1 else ('reposo',), armL=('reposo',), look=(0, 0), frown=0, sash=True, hair='coleta')
        mic_podium(fr, 540, 1180)
        for i in range(4):
            f = (t * .9 + i * .29) % 1
            if f < .12: blit(fr, glow_sprite(60, (255, 255, 255)), 120 + i * 260, 1650, (1 - f / .12) * .8, add=True)
        for i in range(3):
            k = ss(.6 + i * .35, 1.6 + i * .35, t)
            if k > 0: blit(fr, s.doc, lerp(540, [200, 880, 300][i], eOut(k)), lerp(1100, [760, 820, 980][i], eOut(k)), k * (1 - ss(2.6, 3.0, t)) + .0, .9)
        float_in(fr, s.panel, 540, 330, t, .3)

class Coop(Sh):
    def __init__(s):
        bg = np.zeros((H, W, 3), np.float32); bg[:, :540] = (14, 24, 54); bg[:, 540:] = (12, 40, 26)
        radial(bg, (270, 900), 500, (60, 90, 200), .25); radial(bg, (810, 900), 500, (200, 60, 50), .25)
        s.back = [(dof(opaque(bg), 2), .2)]
        s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 230, 200), 207, ymin=200, ymax=1700), 1.7)]
        s.lw = N.text_sprite('WASHINGTON', 44, (200, 220, 255, 255), glow=(80, 140, 255), glow_r=10, spacing=8)
        s.lm = N.text_sprite('MÉXICO', 44, (220, 255, 220, 255), glow=(80, 220, 120), glow_r=10, spacing=8)
        s.stamp = N.stamp('COOPERACIÓN SUSPENDIDA', (255, 59, 42), w=900, h=124, px=62)
        s.us, s.mx = flag_sprite(False, 140, 90), flag_sprite(True, 140, 90)
    def arm(s, fr, side, gap, t):
        sd = -1 if side == 'L' else 1; hx = 540 + sd * (60 + gap); hy = 1000 + math.sin(t * 2) * 4
        col = (52, 70, 150) if sd < 0 else (150, 40, 64)
        line(fr, (540 + sd * 640, hy + 160), (hx + sd * 90, hy), (230, 230, 240), 150); line(fr, (540 + sd * 640, hy + 160), (hx + sd * 90, hy), col, 136)
        line(fr, (hx + sd * 95, hy - 70), (hx + sd * 95, hy + 70), (236, 236, 240), 34)        # puño de la camisa
        blit(fr, s.us if sd < 0 else s.mx, hx + sd * 330, hy + 70, 1, .8)
        circ(fr, (hx, hy), 90, (170, 172, 182)); circ(fr, (hx, hy), 84, SKIN)
    def draw(s, fr, t, d):
        gap = 0 if t < s.w('suspender') else 260 * eOut(ss(s.w('suspender'), s.w('suspender') + .7, t))
        s.arm(fr, 'L', gap, t); s.arm(fr, 'R', gap, t)
        # eslabón de cadena que se rompe
        k = ss(s.w('suspender'), s.w('suspender') + .5, t)
        for sd in (-1, 1):
            cx = 540 + sd * (40 + 240 * k); cv2.ellipse(fr, (int(cx), 1240), (70, 36), 0, (0 if sd > 0 else 180) + 30 * k * sd, (180 if sd > 0 else 360) + 30 * k * sd, (200, 206, 216), 12, cv2.LINE_AA)
        if 0 < k < 1: blit(fr, glow_sprite(120, (255, 220, 160)), 540, 1240, 1 - k, add=True)
        blit(fr, s.lw, 270, 560); blit(fr, s.lm, 810, 560)
        stamp_in(fr, s.stamp, 540, 360, t, s.w('cooperación'))

# ================================================================ TERCERO: reacción de los cárteles
class CartelMap(DT.FireMap):
    a = 0.
    def __init__(s):
        super().__init__(); s.title = DT.RS.red_panel('REACCIÓN DE LOS CÁRTELES', w=900, h=170)

class Facility(Sh):
    def __init__(s):
        sky = vgrad([(0, (6, 6, 12)), (1, (44, 20, 22))]); s.back = [(dof(opaque(sky), 2), .1)]
        pl = np.zeros((H, W, 3), np.uint8)
        for (x, w_, h_) in [(60, 90, 520), (200, 70, 420), (760, 80, 560), (900, 100, 380)]:
            cv2.rectangle(pl, (x, 1250 - h_), (x + w_, 1250), (60, 60, 66), -1)
            for y in range(1250 - h_ + 30, 1250, 70): cv2.line(pl, (x - 10, y), (x + w_ + 10, y), (90, 90, 96), 4)
        for (x, r) in [(420, 120), (640, 100)]:
            cv2.rectangle(pl, (x - r, 1050), (x + r, 1250), (84, 86, 92), -1); cv2.ellipse(pl, (x, 1050), (r, 30), 0, 0, 360, (110, 112, 120), -1)
        cv2.rectangle(pl, (-10, 1250), (W + 10, 1290), (40, 40, 46), -1)
        s.back.append((dof(haze(rgba(pl, np.any(pl > 0, 2).astype(np.float32)), (44, 20, 22), .2), 2), .45))
        s.main = floor_layer(1290, (30, 28, 30), (44, 40, 44))
        fence_ = np.zeros((H, W, 4), np.uint8)
        for x in range(-20, W + 40, 60): cv2.line(fence_, (x, 1500), (x + 60, 1800), (120, 126, 136, 255), 3); cv2.line(fence_, (x + 60, 1500), (x, 1800), (120, 126, 136, 255), 3)
        cv2.line(fence_, (0, 1500), (W, 1500), (150, 156, 166, 255), 6)
        s.front = [(dof(fence_, 6), 1.45), (bokeh_layer(10, (255, 80, 60), 208, ymin=300, ymax=1300), 1.7)]
        s.panel = DT.RS.red_panel('INSTALACIONES ESTRATÉGICAS', w=920, h=170)
        s.warn = N.text_sprite('⚠ AMENAZA', 46, (255, 220, 80, 255), stroke=4, stroke_col=(0, 0, 0, 230), spacing=6)
    def draw(s, fr, t, d):
        on = (t * 2.5) % 1 < .5
        for (x, y) in [(105, 720), (235, 820), (800, 680), (950, 860)]: blit(fr, glow_sprite(50, (255, 40, 30)), x, y, .9 if on else .3, add=True)
        for i in range(3):
            f = (t * .5 + i / 3.) % 1; cv2.circle(fr, (530, 1000), int(60 + f * 380), (int(255 * (1 - f)), int(50 * (1 - f)), 40), 4, cv2.LINE_AA)
        float_in(fr, s.panel, 540, 330, t, .2)
        k = ss(.6, .9, t); blit(fr, s.warn, 540, 520, k * (.7 + .3 * math.sin(t * 8)))

class Experts(Sh):
    def __init__(s):
        bg = vgrad([(0, (6, 10, 20)), (1, (14, 22, 36))]); s.back = [(dof(opaque(bg), 2), .2)]
        s.main = floor_layer(1400, (20, 26, 36), (34, 44, 58))
        s.front = [(bokeh_layer(10, (120, 200, 255), 209, ymin=200, ymax=1300), 1.7)]
        s.scr = N.holo_panel(860, 560, 'ANÁLISIS DE RIESGO', None)
        s.stamp = N.stamp('MÁS VIOLENCIA', (255, 59, 42), w=700, px=86)
        s.lbl = N.text_sprite('REPRESALIAS', 36, (255, 150, 130, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=5)
    def draw(s, fr, t, d):
        x0, y0 = 110, 330; blit(fr, s.scr, 540, y0 + 280 + math.sin(t * 1.4) * 4, ss(0, .3, t))
        k = ss(.3, s.w('violencia'), t); n = 40; pts = []
        for i in range(int(n * k) + 1):
            u = i / n; v = .15 + .1 * math.sin(u * 9) + .7 * (u ** 2.2); pts.append((x0 + 60 + u * 700, y0 + 520 - v * 360))
        for q in range(4): line(fr, (x0 + 60, y0 + 160 + q * 90), (x0 + 760, y0 + 160 + q * 90), (60, 120, 160), 1)
        if len(pts) > 1: pline(fr, pts, (110, 30, 24), 12); pline(fr, pts, (255, 80, 60), 5); blit(fr, glow_sprite(30, (255, 120, 90)), *pts[-1], 1, add=True)
        if t > s.w('represalias'): blit(fr, s.lbl, 760, y0 + 140, ss(s.w('represalias'), s.w('represalias') + .3, t))
        character(fr, 'bata', 300, 1620, 420, t, armR=('apunta', (600, 700), .9), armL=('reposo',), look=(.5, -.4), frown=.5)
        character(fr, 'traje', 790, 1640, 430, t, armR=('reposo',), armL=('jarra',), look=(-.4, -.4), frown=.55)
        stamp_in(fr, s.stamp, 540, 1000, t, s.w('violencia'))

# ================================================================ ECONOMÍA
class Econ(Sh):
    def __init__(s):
        bg = vgrad([(0, (16, 10, 4)), (1, (40, 26, 8))]); radial(bg, (540, 900), 600, (255, 180, 60), .2)
        s.back = [(dof(opaque(bg), 2), .2)]
        s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(14, (255, 210, 120), 210, ymin=200, ymax=1700), 1.7)]
        s.olv = N.text_sprite('LO QUE MUCHOS OLVIDAN…', 44, (255, 240, 210, 255), stroke=4, stroke_col=(0, 0, 0, 220), spacing=4)
        s.eco = N.text_sprite('LA ECONOMÍA', 96, (255, 236, 170, 255), glow=(255, 180, 60), glow_r=16, spacing=10)
        s.digits = [N.text_sprite(c, 34, (255, 210, 120, 200), pad=4) for c in '$0123456789%']
        s.dollar = N.text_sprite('$', 260, (120, 80, 20, 255), pad=10)
    def draw(s, fr, t, d):
        for i in range(30):
            x = 40 + (i * 37) % 1000; f = (t * .3 + (i * .41) % 1) % 1; blit(fr, s.digits[(i * 5 + int(t * 4)) % 12], x, 200 + f * 1400, .3 * (1 - f))
        sx = abs(math.cos(t * 1.6)) * .9 + .1; c = (540, 900)
        cv2.ellipse(fr, c, (int(250 * sx), 250), 0, 0, 360, (150, 100, 30), -1, cv2.LINE_AA); cv2.ellipse(fr, c, (int(230 * sx), 230), 0, 0, 360, (240, 190, 80), -1, cv2.LINE_AA)
        cv2.ellipse(fr, c, (int(190 * sx), 190), 0, 0, 360, (210, 160, 60), 6, cv2.LINE_AA)
        if sx > .3: blit(fr, cv2.resize(s.dollar, (max(4, int(s.dollar.shape[1] * sx)), s.dollar.shape[0])), 540, 900)
        blit(fr, glow_sprite(260, (255, 200, 90)), 540, 900, .25, add=True)
        blit(fr, s.olv, 540, 330, ss(.1, .4, t) * (1 - ss(s.w('economía') - .2, s.w('economía'), t)))
        float_in(fr, s.eco, 540, 330, t, s.w('economía'), sc0=1.5)

class Trade(D.S3D):
    a = 0.
    def __init__(s):
        super().__init__()
        s.routes = [((-103.35, 20.67), (-112.07, 33.45)), ((-100.31, 25.69), (-96.8, 32.78)), ((-99.13, 19.43), (-87.6, 41.9)), ((-106.1, 28.6), (-106.65, 35.08)),
                    ((-116.9, 32.0), (-118.2, 34.05))]
        s.panel = N.holo_panel(760, 170, 'COMERCIO BILATERAL', 'MÉXICO ⇄ ESTADOS UNIDOS', col=(255, 210, 90), fill=(60, 40, 6, 190))
        s.dotG = glow_sprite(26, (255, 220, 120)); s.dotB = glow_sprite(26, (120, 200, 255))
        s.bord = glow_sprite(60, (255, 220, 120))
    def draw(s, fr, t, d):
        pb = [prj(*p) for p in sUSB]; pline(fr, pb, (120, 80, 20), 14); pline(fr, pb, (255, 220, 120), 5)
        for i, (a_, b_) in enumerate(s.routes):
            k = ss(.2 + i * .15, .9 + i * .15, t)
            if k <= 0: continue
            p0, p1 = A(*prj(*a_)), A(*prj(*b_)); mid = (p0 + p1) / 2 + A(-60, 0)
            bz = lambda u_: (1 - u_) ** 2 * p0 + 2 * (1 - u_) * u_ * mid + u_ ** 2 * p1
            pts = [tuple(bz(u_)) for u_ in np.linspace(0, k, 30)]; pline(fr, pts, (80, 60, 20), 10); pline(fr, pts, (255, 200, 90), 4)
            if k > .95:
                for j in range(3):
                    u1 = (t * .35 + j / 3. + i * .1) % 1; blit(fr, s.dotG, *bz(u1), .9, add=True)          # mercancía MX → EE. UU.
                    u2 = 1 - (t * .3 + j / 3. + i * .17) % 1; blit(fr, s.dotB, *bz(u2), .9, add=True)      # EE. UU. → MX
        for p in [(-117.03, 32.53), (-110.94, 31.33), (-106.45, 31.72), (-99.5, 27.48), (-97.5, 25.87)]:
            blit(fr, s.bord, *prj(*p), .5 + .4 * math.sin(t * 4 + p[0]), add=True)
    def floating(s, fr, t, d, P):
        float_in(fr, s.panel, 540, 330, t, .3); s.dust.draw(fr, t)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.08, 1.2, k), 520, 1000, lerp(-30, 30, k), 0

class Factory(Sh):
    def __init__(s):
        sky = vgrad([(0, (8, 8, 14)), (1, (34, 30, 36))]); s.back = [(dof(opaque(sky), 2), .1)]
        f = np.zeros((H, W, 3), np.uint8); s.wins = []
        for i, x in enumerate(range(-20, W, 280)):
            cv2.rectangle(f, (x, 900), (x + 260, 1300), (66, 64, 70), -1)
            for k in range(4): poly(f, [(x + k * 65, 900), (x + k * 65 + 65, 900), (x + k * 65 + 65, 840)], (80, 78, 84))
            cv2.rectangle(f, (x + 190, 640), (x + 225, 900), (90, 86, 90), -1)
            for r in range(3):
                for c in range(4): s.wins.append((x + 20 + c * 60, 960 + r * 100, i))
        s.chim = [(x + 207, 640) for x in range(-20, W, 280)]
        cv2.rectangle(f, (-10, 1300), (W + 10, H), (40, 40, 44), -1)
        al = np.zeros((H, W)); al[840:] = np.any(f[840:] > 0, 2)
        for x in range(-20, W, 280): al[640:900, x + 190:x + 225] = 1
        s.main = rgba(f, al)
        s.front = [(bokeh_layer(10, (255, 200, 120), 211, ymin=300, ymax=1300), 1.7)]
        s.puff = glow_sprite(90, (110, 106, 110))
        s.panel = DT.RS.red_panel('EMPLEOS EN RIESGO', w=760, h=170)
        s.inv = N.text_sprite('INVERSIONES ↓', 44, (255, 150, 130, 255), stroke=4, stroke_col=(0, 0, 0, 230), spacing=5)
    def draw(s, fr, t, d):
        nb = len(s.chim)
        for (x, y, i) in s.wins:
            off = ss(.6 + i * .35, .9 + i * .35, t); col = tuple(int(lerp(c, 26, off)) for c in (255, 200, 120))
            cv2.rectangle(fr, (x, y), (x + 40, y + 60), col, -1)
        for j, (x, y) in enumerate(s.chim):
            off = ss(.6 + j * .35, .9 + j * .35, t)
            for i in range(5):
                f = (i / 5. + t * .25 + j * .13) % 1; blit(fr, s.puff, x + f * 60, y - f * 360, min(1, f * 5) * (1 - f) * .5 * (1 - off), .6 + f * 1.6)
        for i, x in enumerate((230, 540, 850)):
            character(fr, 'civil', x, 1640, 360, t + i, armR=('reposo',), armL=('jarra',) if i == 1 else ('reposo',), look=(0, -.3), frown=.15)
        float_in(fr, s.panel, 540, 330, t, max(.2, s.w('empleos') - .3))
        if t > s.w('inversiones'): float_in(fr, s.inv, 540, 500, t, s.w('inversiones'))

class Customs(Sh):
    def __init__(s):
        sky = vgrad([(0, (8, 8, 16)), (1, (30, 28, 40))]); s.back = [(dof(opaque(sky), 2), .1)]
        s.main = floor_layer(1250, (40, 40, 44), (56, 56, 60))
        s.front = [(bokeh_layer(14, (255, 60, 40), 212, rmin=10, rmax=40, ymin=1100, ymax=1500), 1.6)]
        s.panel = DT.RS.red_panel('MERCANCÍAS DETENIDAS', w=820, h=170)
        s.ad = N.text_sprite('ADUANA', 40, (240, 240, 240, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=8)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (60, 800), (1020, 860), (60, 64, 72), -1); blit(fr, s.ad, 540, 830)
        for x in (100, 980): cv2.rectangle(fr, (x - 20, 860), (x + 20, 1260), (70, 74, 82), -1)
        blit(fr, glow_sprite(60, (255, 30, 30)), 540, 920, .7 + .3 * math.sin(t * 6), add=True); circ(fr, (540, 920), 20, (255, 80, 70))
        for r, (y, sc) in enumerate([(1350, .7), (1560, .95), (1800, 1.15)]):
            for k in range(3):
                x = -120 + k * 520 * sc + r * 60 - 40 * ss(0, .8, t) * (2 - k)
                semi(fr, x, y, sc, body=[(210, 214, 220), (230, 200, 120), (170, 190, 210)][(k + r) % 3])
                if (t * 2 + k + r) % 1 < .5: blit(fr, glow_sprite(26, (255, 60, 40)), x, y - 40 * sc, .8, add=True)
        float_in(fr, s.panel, 540, 330, t, .25)

# ================================================================ ENTONCES: ¿acabaría con los cárteles? · la red sigue
class Mission(Sh):
    def __init__(s):
        bg = vgrad([(0, (14, 18, 34)), (1, (26, 30, 52))]); i8 = to8(bg)
        for x in (120, 760): flag_us(i8, x, 260, 200, 124); cv2.line(i8, (x - 4, 240), (x - 4, 1100), (200, 170, 90), 6)
        cv2.circle(i8, (540, 400), 150, (200, 170, 90), 8, cv2.LINE_AA); cv2.circle(i8, (540, 400), 136, (30, 40, 90), -1, cv2.LINE_AA)
        s.back = [(dof(opaque(i8.astype(np.float32)), 3), .4)]
        s.main = floor_layer(1350, (30, 30, 40), (44, 44, 56))
        s.front = [(bokeh_layer(10, (200, 220, 255), 213, ymin=300, ymax=1500), 1.7)]
        s.q = N.holo_panel(720, 170, '¿MISIÓN CUMPLIDA?', 'ACABAR CON LOS CÁRTELES', col=(255, 210, 90), fill=(60, 40, 6, 190))
        s.qm = N.text_sprite('?', 150, (255, 220, 120, 255), glow=(255, 180, 60), glow_r=14)
    def draw(s, fr, t, d):
        character(fr, 'traje', 540, 1400, 480, t, armR=('palma',), armL=('jarra',), look=(.2, -.3), frown=.2, hair='rubio')
        mic_podium(fr, 540, 1180, body=(40, 46, 70))
        for i, (x, y) in enumerate([(200, 820), (880, 760), (840, 1000)]):
            k = ss(.4 + i * .3, .8 + i * .3, t); blit(fr, s.qm, x, y + math.sin(t * 2 + i) * 10, k, .6 + .2 * i)
        float_in(fr, s.q, 540, 330, t, .25)

class Network(Sh):
    def __init__(s):
        bg = vgrad([(0, (6, 6, 12)), (1, (18, 10, 16))]); s.back = [(dof(opaque(bg), 2), .2)]
        s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 90, 70), 214, ymin=200, ymax=1700), 1.7)]
        s.boss = (540, 640); s.mid = [(160 + i * 190, 900) for i in range(5)]; r_ = np.random.RandomState(8)
        s.low = [(90 + i * 112, 1180 + (i % 2) * 60) for i in range(9)]
        s.ml = [(i, j) for i in range(5) for j in range(9) if abs(s.mid[i][0] - s.low[j][0]) < 230]
        s.mm = [(i, i + 1) for i in range(4)] + [(0, 2), (2, 4)]
        s.stamp = N.stamp('NO NECESARIAMENTE', (255, 59, 42), w=820, px=70)
        s.panel = N.holo_panel(900, 150, 'EL JEFE CAE, LA RED SIGUE', None, col=(255, 90, 70), fill=(50, 8, 8, 190))
        s.chips = {w_: N.holo_panel(300, 90, lab, None, col=(255, 210, 90), fill=(60, 40, 6, 200)) for w_, lab in
                   [('corrupción', 'CORRUPCIÓN'), ('dinero', 'DINERO'), ('rutas', 'RUTAS'), ('demanda', 'DEMANDA')]}
        s.crown = emoji_sprite('👑')
    def node(s, fr, p, r, col, op=1.):
        blit(fr, glow_sprite(int(r * 1.8), col), *p, .5 * op, add=True); circ(fr, p, r, dark(col, .5 + .5 * op)); circ(fr, p, r - 6, tuple(int(c * (.3 + .7 * op)) for c in SKIN))
    def draw(s, fr, t, d):
        te = s.w('eliminar'); gone = ss(te + .2, te + .9, t)
        for i, j in s.ml: line(fr, s.mid[i], s.low[j], (150, 50, 44), 3)
        new = ss(te + .8, te + 1.6, t)
        for i, j in s.mm: line(fr, s.mid[i], s.mid[j], (255, 120, 90), 3 * new + 1 if new > 0 else 1)
        for m in s.mid: line(fr, s.boss, m, (int(150 * (1 - gone)), 50, 44), max(1, int(4 * (1 - gone))))
        for p in s.low: s.node(fr, p, 26, (255, 70, 50), .8)
        for p in s.mid: s.node(fr, p, 40, (255, 70, 50), 1.)
        s.node(fr, s.boss, 62, (255, 70, 50), 1 - gone)
        blit(fr, s.crown, s.boss[0], s.boss[1] - 90, 1 - gone, .7)
        if gone > 0: k = gone; line(fr, (s.boss[0] - 70 * k, s.boss[1] - 70 * k), (s.boss[0] + 70 * k, s.boss[1] + 70 * k), (255, 40, 30), 14); line(fr, (s.boss[0] + 70 * k, s.boss[1] - 70 * k), (s.boss[0] - 70 * k, s.boss[1] + 70 * k), (255, 40, 30), 14)
        a = ss(.05, .35, t) * (1 - ss(te - .2, te, t))
        if a > 0: blit(fr, s.stamp, 540, 330, a, lerp(1.6, 1, eOut(ss(.05, .35, t))))
        float_in(fr, s.panel, 540, 330, t, te)
        for n_, (w_, (x, y)) in enumerate(zip(s.chips, [(230, 470), (850, 470), (230, 1000), (850, 1000)])):
            if t > s.w(w_) - .1: float_in(fr, s.chips[w_], x, y if n_ < 2 else 1440, t, s.w(w_) - .1)

# ================================================================ CIERRE
class Split(Sh):
    def __init__(s):
        bg = np.zeros((H, W, 3), np.float32); bg[:] = (8, 10, 18); radial(bg, (270, 800), 520, (60, 100, 220), .3); radial(bg, (810, 800), 520, (220, 60, 50), .3)
        s.back = [(dof(opaque(bg), 2), .2)]
        s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(12, (255, 230, 200), 215, ymin=200, ymax=1700), 1.7)]
        s.us, s.mx = flag_sprite(False, 420, 270), flag_sprite(True, 420, 270)
        s.seg = N.holo_panel(520, 140, '¿SEGURIDAD?', None, col=(120, 255, 160), fill=(6, 50, 20, 190))
        s.con = N.holo_panel(620, 140, '¿O MÁS CONFLICTO?', None, col=(255, 90, 70), fill=(50, 8, 8, 190))
    def draw(s, fr, t, d):
        blit(fr, wave_flag(s.us, t), 270, 820, 1, 1.0); blit(fr, wave_flag(s.mx, t + 1.4), 810, 820, 1, 1.0)
        pline(fr, [(540, 520), (540, 1150)], (255, 255, 255), 4); blit(fr, glow_sprite(90, (255, 255, 255)), 540, 830, .3 + .2 * math.sin(t * 3), add=True)
        mini_map(fr, 340, 1180, 400, 330, col=(255, 200, 90), others=(50, 80, 140))
        float_in(fr, s.seg, 540, 330, t, s.w('seguridad') - .1)
        if t > s.w('conflicto') - .2: float_in(fr, s.con, 540, 500, t, s.w('conflicto') - .2)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.03, 1.16, k), 540, 950, 0, 0

class Close(DT.RL.Q5):
    a = 0.
    def __init__(s):
        super().__init__(); s.cta = N.holo_panel(640, 200, '¿TÚ QUÉ OPINAS?', 'TE LEO EN COMENTARIOS')
    def draw(s, fr, t, d): super().draw(fr, t + 3.4, d)
    def cam(s, t, d): return super().cam(t + 3.4, d + 3.4)

# ================================================================ línea de tiempo de tomas
def tl():
    S = SC_T
    seq = [
        (0, Oval(), 0), (T('ocurriría') - .3 - .15, Flags(), 0),
        (S[1], Jets(), 1), (T('pero') - .2, Raid(), 1), (T('sus') - .2, Fragment(), 1),
        (S[2], Palace(), 2), (T('tropas') - .4, Border(), 2), (T('gobierno') - .3, Note(), 2), (T('incluso') - .25, Coop(), 2),
        (S[3], CartelMap(), 3), (T('bloqueos') - .25, Blockade('BLOQUEOS'), 3), (T('amenazas') - .25, Facility(), 3), (T('expertos') - .4, Experts(), 3),
        (S[4], Econ(), 4), (T('méxico', SC_T[4]) - .25, Trade(), 4), (T('una', T('mundo')) - .2, Factory(), 4), (T('transporte') - .45, Customs(), 4),
        (S[5], Mission(), 0), (T('no', SC_T[5]) - .15, Network(), 3),
        (S[6], Split(), 2), (T('te', T('grande')) - .35, Close(), 4),
    ]
    out = []
    for i, (a, sc, g) in enumerate(seq):
        b = seq[i + 1][0] if i + 1 < len(seq) else DUR; sc.a = a; out.append((a, b, sc, g))
    return out

# ---------------------------------------------------------------- subtítulos, emojis y audio
KEY = {'trump', 'ejército', 'méxico', 'cárteles', 'historia', 'ventaja', 'militar', 'laboratorios', 'capos', 'fragmentarse', 'violentas', 'soberanía', 'autorización',
       'diplomática', 'cooperación', 'washington', 'bloqueos', 'autoridades', 'estratégicas', 'represalias', 'violencia', 'economía', 'comerciales', 'fábricas', 'empleos',
       'inversiones', 'mercancías', 'necesariamente', 'corrupción', 'dinero', 'rutas', 'demanda', 'drogas', 'seguridad', 'conflicto', 'comentarios', 'intervención'}
def build_subs(words, y=1500):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 4 or w[0][-1] in '.,:;?!…' or (len(cur) >= 3 and sum(len(x[0]) for x in cur) > 20): out.append(cur); cur = []
    if cur: out.append(cur)
    subs = []
    for i, g in enumerate(out):
        a = g[0][1]; b = out[i + 1][0][1] if i + 1 < len(out) else DUR; b = min(b, g[-1][2] + .9)
        subs.append((a, b, y, ' '.join(f"*{w[0]}*" if _clean(w[0]) in KEY else w[0] for w in g)))
    return subs

EMOJIS = [
 (T('trump'), T('ocurriría') - .3 - .2, '🇺🇸', 880, 1180, 140, 'pop'), (T('méxico'), T('primero') - .4, '🇲🇽', 200, 1180, 140, 'pop'),
 (T('ventaja'), T('pero') - .3, '⚔️', 880, 1180, 140, 'late'), (T('laboratorios'), T('sus') - .3, '🧪', 880, 1180, 140, 'sacude'),
 (T('fragmentarse'), SC_T[2] - .1, '💥', 880, 1260, 140, 'late'),
 (T('soberanía'), T('tropas') - .4, '🏛️', 880, 1180, 140, 'pop'), (T('autorización'), T('gobierno') - .35, '🚫', 880, 1000, 140, 'sacude'),
 (T('diplomática'), T('incluso') - .3, '📄', 880, 1000, 130, 'pop'), (T('cooperación'), SC_T[3] - .1, '🤝', 880, 1640, 130, 'sacude'),
 (T('bloqueos'), T('amenazas') - .3, '🚧', 200, 860, 130, 'late'), (T('amenazas'), T('expertos') - .45, '⚠️', 880, 1000, 140, 'late'),
 (T('aumentar'), SC_T[4] - .1, '📈', 880, 1180, 140, 'pop'), (T('economía'), T('méxico', SC_T[4]) - .3, '💰', 880, 1180, 150, 'late'),
 (T('fábricas'), T('transporte') - .5, '🏭', 200, 1180, 130, 'pop'), (T('empleos'), T('transporte') - .5, '💼', 880, 1180, 130, 'pop'),
 (T('transporte'), SC_T[5] - .1, '🚚', 880, 1180, 140, 'sacude'), (T('trump', SC_T[5]), T('no', SC_T[5]) - .2, '❓', 880, 1180, 140, 'late'),
 (SC_T[6] + .3, DUR, '💬', 180, 1180, 130, 'late'), (T('comentarios') - .3, DUR, '🔔', 900, 380, 130, 'sacude'),
]

_s = CH._src.replace("secs = [(0, 'tension', 1), (9.9, 'misterio', 2), (24.1, 'tension', 2), (37.2, 'epico', 2), (50.2, 'tension', 1)]",
     f"secs = [(0, 'tension', 1), ({SC_T[1]:.2f}, 'epico', 2), ({SC_T[2]:.2f}, 'tension', 2), ({SC_T[3]:.2f}, 'epico', 2), ({SC_T[4]:.2f}, 'misterio', 2), ({SC_T[5]:.2f}, 'tension', 2), ({SC_T[6]:.2f}, 'tension', 1)]")
_a = _s.index('    EF = ['); _b = _s.index(']]', _a) + 2
_ef = [[0, 'boom', .9], [.3, 'latido', .3], [T('méxico') + .1, 'impacto', .6], [T('ocurriría') - .3 - .4, 'whoosh', .45]]
for sec in SC_T[1:7]: _ef += [[sec - .45, 'whoosh', .45], [sec, 'impacto', .55]]
_ef += [[SC_T[1] + .2, 'riser', .2], [T('pero') + .2, 'beep', .12], [T('significa'), 'impacto', .7], [T('autorización'), 'impacto', .7], [T('cooperación'), 'impacto', .7],
        [T('suspender'), 'caida', .3], [T('bloqueos') - .1, 'boom', .4], [T('bloqueos') + .5, 'pop', .15], [T('amenazas'), 'alarma', .05, 1.8], [T('violencia'), 'impacto', .7],
        [T('economía'), 'dinero', .3], [T('fábricas'), 'caida', .25], [T('no', SC_T[5]), 'impacto', .7], [T('eliminar') + .3, 'impacto', .6], [T('dinero', SC_T[5]), 'dinero', .2],
        [T('dime') - .2, 'latido', .3], [T('conflicto'), 'boom', .4], [T('comentarios'), 'ding', .3], [DUR - 3.4 + 2.8, 'ding', .25]]
_s = _s[:_a] + '    EF = ' + repr(sorted(_ef, key=lambda e: e[0])) + _s[_b:]
_s = _s.replace("env / (env.max() * .25)", "env / (env.max() * .25 + 1e-9)").replace("duck = 1 - .55 * env", "duck = 1 - .7 * env").replace(
    "out = np.tanh((mus * .75 * duck + fx * .6 * (1 - .35 * env)) * 1.1) * .8 + vv * .92",
    "out = np.tanh((mus * .5 * duck + fx * .32 * (1 - .5 * env)) * 1.1) * .7 + vv * .95")
exec(_s)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in build_subs(WORDS)]
    emos = [e + (emoji_sprite(e[2]),) for e in EMOJIS]
    shots = tl()
    pill = Blockade(None, cta=True); C0, C1 = T('bloqueos') + .3, T('violencia') - .3      # «dale like y sígueme» a mitad del video
    def one(i, T_):
        a, b, sc, g = shots[i]; return cinema(render3d(sc, T_ - a, b - a, T_), g, T_)
    def frame(T_):
        i = max(k for k, s_ in enumerate(shots) if T_ >= s_[0] - 1e-6)
        fr = one(i, T_); a = shots[i][0]
        if i > 0 and T_ - a < .3: fr = cv2.addWeighted(one(i - 1, T_), 1 - ss(0, .3, T_ - a), fr, ss(0, .3, T_ - a), 0)
        c = ss(C0, C0 + .4, T_) * (1 - ss(C1 - .3, C1, T_))
        if c > 0: blit(fr, pill.ctaspr, 760, 1720, c, lerp(.6, 1, eBack((T_ - C0) / .4)) * .6); blit(fr, pill.bell, 1010, 1700 + math.sin(T_ * 9) * 4, c, .4)
        draw_overlays(fr, T_, subs, emos); return fr
    if mode == 'info':
        print('DUR', DUR, 'SC_T', [round(x, 2) for x in SC_T])
        for a, b, sc, g in shots: print(f'{a:6.2f}-{b:6.2f} {b - a:5.2f} {type(sc).__name__}')
        return
    if mode == 'test':
        for T_ in [float(x) for x in sys.argv[2:]]:
            cv2.imwrite(f'{OUT}/t_{T_:05.1f}.jpg', cv2.resize(frame(T_), (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == 'seg':
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', f'{OUT}/seg_{f0:04d}.mp4']
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(f0, f1): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('SEG', f0, f1, flush=True); return
    if mode == 'audio': synth_audio(f'{OUT}/audio.wav'); print('audio ok'); return

if __name__ == '__main__': main()
