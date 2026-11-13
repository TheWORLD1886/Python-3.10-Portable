#!/usr/bin/env python3
# Short: ¿Una espía china logró acercarse al hombre más poderoso de NVIDIA? · 1080x1920 · 30 fps · estilo 2.5D de la plantilla.
# Hechos verificados en prensa (13 nov 2026): NYT 29 oct 2026 (relación y sospechas); CNN (FBI avisó a legisladores ~1 año antes);
# NVIDIA (investigación independiente; «sin motivos para creer» que se comprometieron secretos); China (portavoz: «difamación»);
# NVIDIA 8-K / comunicado 12 nov 2026: Jensen Huang renuncia, Colette Kress CEO interina. Nadie ha sido acusado formalmente.
import os, sys, json, math
HERE_N = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE_N, '..', 'trump-mexico')); sys.path.insert(0, os.path.join(HERE_N, '..', 'chapo'))
import trump as TR
from trump import *

OUT = os.path.join(HERE_N, 'out'); os.makedirs(OUT, exist_ok=True)
WORDS = json.load(open(os.path.join(HERE_N, 'words.json')))
VOZ = os.path.join(HERE_N, 'voz.mp3')
_clean = TR._clean
def T(word, after=-1.):
    for w in WORDS:
        if w[1] >= after and _clean(w[0]).startswith(word.lower()): return w[1]
    raise KeyError(word)
DUR = int(math.ceil(WORDS[-1][2] + 2.0))
SC_T = [0, T('el', 15) - .3, T('según', 44) - .3, T('el', 83) - .3, T('washington') - .3, T('y', 132) - .3, T('pero', 150) - .3, DUR]
class Sb(Shot):
    a = 0.
    def w(s, word): return T(word, s.a - .6) - s.a

# ---------------------------------------------------------------- personajes: mismo adaptador del rig articulado que el short de Bukele
HERE_B = os.path.join(HERE_N, '..', 'bukele')
_bk = open(os.path.join(HERE_N, '..', 'bukele', 'bukele.py')).read()
exec(_bk[_bk.index('# ---------------------------------------------------------------- personajes'):_bk.index("OUTF['cecot']")])
def who(name, fr, x, fy, h, t, **kw): return rig_character(fr, 'traje', x, fy, h, t, who=name, **kw)

red_panel = DT.RS.red_panel
def gold_panel(t1, t2=None, w=760, h=160): return N.holo_panel(w, h, t1, t2, col=(255, 210, 90), fill=(60, 40, 6, 190))
def blue_panel(t1, t2=None, w=760, h=160): return N.holo_panel(w, h, t1, t2)
def green_panel(t1, t2=None, w=760, h=160): return N.holo_panel(w, h, t1, t2, col=(150, 240, 90), fill=(16, 50, 10, 190))
def chip(txt, col=(255, 210, 90), w=460): return N.holo_panel(w, 90, txt, None, col=col, fill=tuple(int(c * .22) for c in col) + (200,))
def label(txt, px=34, col=(255, 255, 255)): return N.text_sprite(txt, px, col + (255,), stroke=3, stroke_col=(0, 0, 0, 220), spacing=4, pad=6)
GREEN = (118, 200, 40)

def star(fr, c, r, col, rot_=0.):
    pts = [(c[0] + math.sin(rot_ + k * math.pi / 5) * (r if k % 2 == 0 else r * .4), c[1] - math.cos(rot_ + k * math.pi / 5) * (r if k % 2 == 0 else r * .4)) for k in range(10)]
    poly(fr, pts, col)
def flag_cn(img, x, y, w=220, h=146):
    cv2.rectangle(img, (x, y), (x + w, y + h), (222, 41, 16), -1)
    u = w / 30.; star(img, (x + 5 * u, y + 5 * u), 3 * u, (255, 222, 0))
    for (a_, b_) in ((10, 2), (12, 4), (12, 7), (10, 9)): star(img, (x + a_ * u, y + b_ * u), u, (255, 222, 0), math.atan2(b_ - 5, a_ - 5))
def flag_sprite_cn(w=440, h=290):
    f = np.zeros((h, w, 3), np.uint8); flag_cn(f, 0, 0, w, h); return np.dstack([f, np.full((h, w), 255, np.uint8)])
def flag_sprite_us(w=440, h=260):
    f = np.zeros((h, w, 3), np.uint8); DT.flag_us(f, 0, 0, w, h); return np.dstack([f, np.full((h, w), 255, np.uint8)])

def gpu(fr, x, y, s, t=0., glow=1., txt='GPU'):
    """chip de IA estilizado: encapsulado verde oscuro, die brillante y pines dorados (sin logotipos)."""
    hw = 90 * s
    for k in range(7):
        q = -hw + (k + .5) * 2 * hw / 7
        for sd in (-1, 1):
            cv2.line(fr, (int(x + q), int(y + sd * hw)), (int(x + q), int(y + sd * (hw + 18 * s))), (210, 170, 70), max(2, int(5 * s)))
            cv2.line(fr, (int(x + sd * hw), int(y + q)), (int(x + sd * (hw + 18 * s)), int(y + q)), (210, 170, 70), max(2, int(5 * s)))
    cv2.rectangle(fr, (int(x - hw), int(y - hw)), (int(x + hw), int(y + hw)), (20, 40, 22), -1)
    cv2.rectangle(fr, (int(x - hw), int(y - hw)), (int(x + hw), int(y + hw)), (90, 160, 60), max(2, int(4 * s)))
    p = .6 + .4 * math.sin(t * 4)
    cv2.rectangle(fr, (int(x - hw * .55), int(y - hw * .55)), (int(x + hw * .55), int(y + hw * .55)), tuple(int(c * (.5 + .5 * p * glow)) for c in (150, 240, 90)), -1)
    for k in range(4): cv2.line(fr, (int(x - hw * .55), int(y - hw * .55 + k * hw * .37)), (int(x + hw * .55), int(y - hw * .55 + k * hw * .37)), (40, 90, 30), max(1, int(2 * s)))
    if s > .5: cv2.putText(fr, txt, (int(x - 30 * s), int(y + 10 * s)), cv2.FONT_HERSHEY_DUPLEX, .9 * s, (10, 30, 10), max(1, int(2 * s)), cv2.LINE_AA)
def rack(fr, x, y, w, h, t, seed=0):
    cv2.rectangle(fr, (x, y), (x + w, y + h), (24, 28, 36), -1); cv2.rectangle(fr, (x, y), (x + w, y + h), (70, 80, 96), 4)
    r_ = np.random.RandomState(seed)
    for k in range(int(h / 34)):
        yy = y + 12 + k * 34; cv2.rectangle(fr, (x + 10, yy), (x + w - 10, yy + 26), (36, 42, 54), -1)
        for j in range(4):
            on = (math.sin(t * (3 + r_.rand() * 6) + r_.rand() * 6) > .2)
            cv2.circle(fr, (x + 24 + j * 16, yy + 13), 4, (120, 255, 140) if on else (30, 70, 40), -1, cv2.LINE_AA)
        cv2.line(fr, (x + w // 2, yy + 13), (x + w - 22, yy + 13), (60, 70, 86), 3)
def capitol(img, x, y, s=1., col=(200, 204, 214)):
    c = col; d = tuple(int(v * .7) for v in col)
    cv2.rectangle(img, (int(x - 420 * s), int(y - 120 * s)), (int(x + 420 * s), int(y)), c, -1)
    for k in range(15): cv2.rectangle(img, (int(x - 400 * s + k * 56 * s), int(y - 110 * s)), (int(x - 388 * s + k * 56 * s), int(y - 10 * s)), d, -1)
    cv2.rectangle(img, (int(x - 160 * s), int(y - 220 * s)), (int(x + 160 * s), int(y - 120 * s)), c, -1)
    for k in range(9): cv2.rectangle(img, (int(x - 150 * s + k * 37 * s), int(y - 210 * s)), (int(x - 140 * s + k * 37 * s), int(y - 125 * s)), d, -1)
    cv2.ellipse(img, (int(x), int(y - 220 * s)), (int(150 * s), int(170 * s)), 0, 180, 360, c, -1, cv2.LINE_AA)
    cv2.rectangle(img, (int(x - 18 * s), int(y - 440 * s)), (int(x + 18 * s), int(y - 380 * s)), c, -1); cv2.circle(img, (int(x), int(y - 450 * s)), int(16 * s), c, -1, cv2.LINE_AA)
def dossier(fr, x, y, w, h, t, k=1., seed=1, redact=True):
    cv2.rectangle(fr, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), (236, 228, 206), -1)
    cv2.rectangle(fr, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), (170, 160, 130), 3)
    r_ = np.random.RandomState(seed); n = int((h - 80) / 34)
    for i in range(n):
        yy = int(y - h / 2 + 60 + i * 34); ln = int((w - 80) * (.5 + .5 * r_.rand()))
        if i / n > k: break
        if redact and r_.rand() < .55: cv2.rectangle(fr, (int(x - w / 2 + 40), yy - 10), (int(x - w / 2 + 40 + ln), yy + 12), (14, 14, 16), -1)
        else: cv2.line(fr, (int(x - w / 2 + 40), yy), (int(x - w / 2 + 40 + ln), yy), (120, 110, 90), 4)
def phone(fr, x, y, s, t, ring=False):
    cv2.rectangle(fr, (int(x - 70 * s), int(y - 140 * s)), (int(x + 70 * s), int(y + 140 * s)), (20, 22, 28), -1)
    cv2.rectangle(fr, (int(x - 60 * s), int(y - 120 * s)), (int(x + 60 * s), int(y + 115 * s)), (40, 90, 140), -1)
    for k in range(4): cv2.rectangle(fr, (int(x - 48 * s), int(y - 100 * s + k * 50 * s)), (int(x + (10 + 30 * ((k * 7) % 3)) * s), int(y - 70 * s + k * 50 * s)), (220, 236, 250), -1)
    if ring:
        for k in range(3): f = (t * 1.5 + k / 3.) % 1; cv2.ellipse(fr, (int(x), int(y)), (int((90 + f * 160) * s), int((150 + f * 160) * s)), 0, -40, 40, (120, 230, 255), 3, cv2.LINE_AA)
def heart(fr, c, r, col, crack=0.):
    x, y = c
    pts = [(x + 16 * math.sin(a_) ** 3 * r / 16, y - (13 * math.cos(a_) - 5 * math.cos(2 * a_) - 2 * math.cos(3 * a_) - math.cos(4 * a_)) * r / 16) for a_ in np.linspace(0, 2 * math.pi, 60)]
    if crack <= 0: poly(fr, pts, col); return
    o = crack * r * .35
    left = [p for p in pts if p[0] <= x] + [(x, y + r * .95), (x - r * .1, y + r * .3), (x + r * .08, y), (x - r * .05, y - r * .4)]
    right = [p for p in pts if p[0] >= x] + [(x - r * .05, y - r * .4), (x + r * .08, y), (x - r * .1, y + r * .3), (x, y + r * .95)]
    poly(fr, [(p[0] - o, p[1] + o * .3) for p in left], col); poly(fr, [(p[0] + o, p[1] + o * .3) for p in right], col)
def stage_bg(seed, col=(10, 14, 24), glow=(60, 120, 200)):
    bg = vgrad([(0, col), (1, tuple(min(255, int(c * 2.2)) for c in col))]); radial(bg, (540, 900), 700, glow, .25)
    return [(dof(opaque(bg), 2), .2)]
def office(seed=1):
    wall = vgrad([(0, (26, 30, 40)), (.7, (40, 46, 58)), (1, (30, 34, 44))]); i8 = to8(wall)
    for x in range(60, W, 240): cv2.rectangle(i8, (x, 380), (x + 180, 1100), (14, 20, 34), -1); cv2.rectangle(i8, (x, 380), (x + 180, 1100), (70, 76, 90), 8)
    r_ = np.random.RandomState(seed)
    for _ in range(80): cv2.circle(i8, (int(r_.uniform(60, W)), int(r_.uniform(420, 1060))), 3, (255, 210, 150), -1)
    return [(dof(opaque(i8.astype(np.float32)), 3), .4)], floor_layer(1400, (40, 34, 30), (52, 46, 40))

# ================================================================ GANCHO
class Scandal(Sb):                                 # una de las empresas más poderosas del mundo, en medio de un escándalo
    def __init__(s):
        sky = vgrad([(0, (4, 8, 10)), (1, (14, 26, 20))]); s.back = [(dof(opaque(sky), 2), .1)]
        city = np.zeros((H, W, 3), np.uint8); r_ = np.random.RandomState(2); x = -20
        while x < W:
            bw, bh = r_.randint(90, 170), r_.randint(200, 520); cv2.rectangle(city, (x, 1300 - bh), (x + bw, 1310), (22, 30, 30), -1)
            for wy in range(1300 - bh + 20, 1290, 34):
                for wx in range(x + 10, x + bw - 14, 26):
                    if r_.rand() < .25: cv2.rectangle(city, (wx, wy), (wx + 10, wy + 14), (170, 230, 140), -1)
            x += bw + 8
        cv2.rectangle(city, (380, 420), (700, 1310), (16, 26, 20), -1)                            # la torre
        for wy in range(450, 1290, 40): cv2.line(city, (400, wy), (680, wy), (60, 120, 50), 3)
        s.back.append((dof(rgba(city, np.any(city > 0, 2).astype(np.float32)), 1.5), .4))
        s.main = floor_layer(1310, (14, 18, 16), (30, 40, 30)); s.front = [(bokeh_layer(12, (150, 240, 110), 401, ymin=200, ymax=1500), 1.7)]
        s.panel = red_panel('ESCÁNDALO INTERNACIONAL', w=880, h=160); s.br = N.stamp('ÚLTIMA HORA', (255, 59, 42), w=520, h=100, px=56)
    def draw(s, fr, t, d):
        gpu(fr, 540, 380, 1.1 + .05 * math.sin(t * 2), t)
        for i in range(6):
            f = (t * .9 + i * .23) % 1
            if f < .1: blit(fr, glow_sprite(70, (255, 255, 255)), 120 + i * 170, 1500 + (i % 2) * 120, (1 - f / .1) * .8, add=True)   # flashes de prensa
        stamp_in(fr, s.br, 540, 700, t, .4); float_in(fr, s.panel, 540, 860, t, 1.0)
    def cam(s, t, d): k = eIO(t / d); return lerp(1.12, 1.02, k), 540, 1000, 0, 0

class Relation(Sb):                                # su CEO y una mujer que, según la inteligencia de EE. UU., trabajaba para China
    def __init__(s):
        s.back = stage_bg(2, (14, 8, 14), (180, 60, 120)); s.main = floor_layer(1600, (20, 16, 22), (34, 28, 36))
        s.front = [(bokeh_layer(10, (255, 140, 180), 402, ymin=200, ymax=1500), 1.7)]
        s.n1 = label('CEO DE NVIDIA'); s.n2 = label('¿?', 60, (255, 160, 200)); s.src = label('SEGÚN INTELIGENCIA DE EE. UU.', 30, (255, 220, 160))
        s.st = N.stamp('PRESUNTA ESPÍA', (255, 59, 42), w=640, h=110, px=60); s.cn = flag_sprite_cn(300, 200)
    def draw(s, fr, t, d):
        who('jensen', fr, 300, 1640, 560, t, armR=('reposo',), armL=('reposo',), look=(.4, 0), frown=-.1)
        k = ss(s.w('mujer') - .3, s.w('mujer') + .3, t)
        if k > 0:
            if t < s.w('trabajaba'): RG.person(fr, 'figura', 790, 1640, 520, dict(look=(-.3, 0)), t)            # silueta: aún sin identificar
            else: who('alice', fr, 790, 1640, 520, t, armR=('reposo',), armL=('reposo',), look=(-.3, 0), frown=0.)
        hk = ss(.3, .7, t); heart(fr, (540, 900), 90 * hk, (230, 60, 110), crack=ss(s.w('según') - .1, s.w('según') + .5, t))
        blit(fr, s.n1, 300, 1720, ss(.2, .6, t))
        if k > 0 and t < s.w('trabajaba'): blit(fr, s.n2, 790, 1100, k)
        blit(fr, s.src, 540, 560, ss(s.w('según') - .1, s.w('según') + .3, t))
        g = ss(s.w('trabajaba'), s.w('trabajaba') + .3, t)
        if g > 0: blit(fr, s.cn, 790, 700, g, .8); stamp_in(fr, s.st, 540, 380, t, s.w('china'))

class Secrets(Sb):                                 # todo podría estar relacionado con los secretos de la IA
    def __init__(s):
        s.back = stage_bg(3, (6, 12, 10), (80, 200, 90)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(12, (150, 240, 110), 403, ymin=200, ymax=1700), 1.7)]
        s.panel = green_panel('LOS SECRETOS DE LA', 'INTELIGENCIA ARTIFICIAL', w=860, h=180); s.lock = emoji_sprite('🔒')
    def draw(s, fr, t, d):
        for i in range(12):                                                    # red neuronal holográfica
            a_ = i * math.pi / 6 + t * .2; p = (540 + math.cos(a_) * 360, 1000 + math.sin(a_) * 360)
            line(fr, (540, 1000), p, (60, 140, 60), 2); circ(fr, p, 14, (150, 240, 110))
            q = ((540 + math.cos(a_ + .5) * 360, 1000 + math.sin(a_ + .5) * 360)); line(fr, p, q, (40, 100, 40), 2)
        f = (t * .7) % 1; cv2.circle(fr, (540, 1000), int(200 + f * 260), (int(150 * (1 - f)), int(240 * (1 - f)), int(110 * (1 - f))), 4, cv2.LINE_AA)
        gpu(fr, 540, 1000, 1.3, t)
        k = ss(s.w('secretos') - .2, s.w('secretos') + .3, t); blit(fr, s.lock, 540, 1360, k, lerp(1.6, 1., eOut(k)))
        float_in(fr, s.panel, 540, 380, t, .2)
    def cam(s, t, d): k = eIO(t / d); return lerp(1.0, 1.1, k), 540, 1000, 0, 0

# ================================================================ ¿QUIÉN ES ELLA?
class JensenIntro(Sb):                             # el protagonista: Jensen Huang, fundador y hasta hace poco CEO de NVIDIA
    def __init__(s):
        s.back = stage_bg(4, (6, 10, 8), (90, 200, 80)); s.main = floor_layer(1560, (16, 22, 16), (30, 44, 30))
        s.front = [(bokeh_layer(12, (150, 240, 110), 404, ymin=200, ymax=1300), 1.7)]
        s.card = green_panel('JENSEN HUANG', 'FUNDADOR DE NVIDIA', w=760, h=180)
        s.tag = chip('CEO HASTA EL 12 DE NOVIEMBRE DE 2026', (255, 210, 90), w=820)
    def draw(s, fr, t, d):
        for i in range(5):                                                     # pantalla gigante detrás del escenario
            cv2.rectangle(fr, (80 + i * 190, 560), (250 + i * 190, 1250), (18, 40 + i * 8, 22), -1)
            for k in range(10): cv2.line(fr, (90 + i * 190, 600 + k * 64), (240 + i * 190, 600 + k * 64), (40, 90, 40), 2)
        fbeam(fr, (540, 0), (540, 1600), 40, 360, (220, 255, 220), .12, 40)
        gesture = ('palma',) if (t % 2.6) < 1.4 else ('apunta', (780, 1100), .8)
        who('jensen', fr, 540, 1640, 640, t, armR=gesture, armL=('reposo',), look=(0, 0), frown=-.2, smile=.4)
        float_in(fr, s.card, 540, 330, t, .3)
        if t > s.w('hasta') - .2: float_in(fr, s.tag, 540, 500, t, s.w('hasta') - .2)

class ChipsAI(Sb):                                 # sus chips impulsan gran parte de la revolución mundial de la IA
    def __init__(s):
        s.back = stage_bg(5, (4, 8, 12), (60, 160, 200)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (120, 230, 255), 405, ymin=200, ymax=1700), 1.7)]
        s.panel = blue_panel('EL MOTOR DE LA IA', 'CENTROS DE DATOS EN TODO EL MUNDO', w=900, h=180)
        s.icons = [emoji_sprite(e) for e in ('🤖', '💬', '🧬', '🚗')]
    def draw(s, fr, t, d):
        for r in range(4):
            for c in range(4):
                x, y = 210 + c * 220, 700 + r * 220; k = ss(.1 + (r * 4 + c) * .06, .4 + (r * 4 + c) * .06, t)
                if k > 0: gpu(fr, x, y, .7 * k, t + r + c)
        for i, ic in enumerate(s.icons):
            a_ = t * .6 + i * math.pi / 2; x, y = 540 + math.cos(a_) * 460, 1030 + math.sin(a_) * 520
            blit(fr, ic, x, y, ss(1, 1.6, t), .7)
        float_in(fr, s.panel, 540, 360, t, .3)
    def cam(s, t, d): k = eIO(t / d); return lerp(1.15, 1.0, k), 540, 1030, 0, 0

class AliceIntro(Sb):                              # la mujer señalada: Alice Huang, directiva de Megaspeed
    def __init__(s):
        s.back, s.main = office(6); s.front = [(bokeh_layer(10, (255, 200, 160), 406, ymin=200, ymax=1300), 1.7)]
        s.card = red_panel('ALICE HUANG', w=640, h=150)
        s.t1 = chip('EMPRESARIA CHINA', (255, 160, 140), w=560); s.t2 = chip('DIRECTIVA EN MEGASPEED', (255, 160, 140), w=640)
        s.note = label('SIN PARENTESCO CON JENSEN', 26, (230, 230, 230)); s.note2 = label('NO HA SIDO ACUSADA FORMALMENTE', 26, (230, 230, 230))
    def draw(s, fr, t, d):
        who('alice', fr, 540, 1640, 620, t, armR=('reposo',), armL=('jarra',), look=(.1, 0), frown=.05)
        float_in(fr, s.card, 540, 330, t, .2)
        if t > s.w('empresaria') - .2: float_in(fr, s.t1, 540, 480, t, s.w('empresaria') - .2)
        if t > s.w('megaspeed') - .3: float_in(fr, s.t2, 540, 590, t, s.w('megaspeed') - .3)
        blit(fr, s.note, 540, 1720, ss(.6, 1.0, t)); blit(fr, s.note2, 540, 1770, ss(.6, 1.0, t))

class DataCenter(Sb):                              # Megaspeed: infraestructura informática y centros de datos
    def __init__(s):
        bg = vgrad([(0, (6, 10, 16)), (1, (16, 24, 34))]); s.back = [(dof(opaque(bg), 2), .2)]
        s.main = floor_layer(1500, (20, 26, 34), (40, 52, 66)); s.front = [(bokeh_layer(10, (120, 255, 160), 407, ymin=200, ymax=1400), 1.7)]
        s.panel = blue_panel('MEGASPEED', 'CENTROS DE DATOS · SINGAPUR', w=800, h=180)
    def draw(s, fr, t, d):
        for i in range(5): rack(fr, 40 + i * 205, 620, 180, 880, t, seed=i)
        for i in range(8):                                                     # cables de datos que pulsan
            f = (t * .8 + i * .12) % 1; x = 60 + i * 130; cv2.line(fr, (x, 600), (x, 560), (60, 200, 255), 3)
            cv2.circle(fr, (x, int(600 - f * 40)), 5, (180, 240, 255), -1, cv2.LINE_AA)
        float_in(fr, s.panel, 540, 360, t, .2)
    def cam(s, t, d): k = eIO(t / d); return 1.08, 540, 1100, lerp(60, -60, k), 0

class Buyer(Sb):                                   # Megaspeed también era un importante comprador de chips NVIDIA
    def __init__(s):
        s.back, s.main = office(8)
        s.front = [(bokeh_layer(8, (255, 210, 150), 408, ymin=200, ymax=1200), 1.7)]
        s.panel = gold_panel('CLIENTE DE NVIDIA', w=700, h=160)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (640, 900), (1060, 1560), (40, 46, 56), -1); cv2.rectangle(fr, (700, 1080), (1000, 1560), (20, 22, 28), -1)
        cv2.putText(fr, 'MEGASPEED', (680, 980), cv2.FONT_HERSHEY_DUPLEX, 1.4, (200, 230, 255), 3, cv2.LINE_AA)
        for i in range(5):                                                     # cajas de chips que entran al almacén
            x = -200 + ((t * 260 + i * 260) % 1100); y = 1500 - (i % 2) * 10
            if x > 760: continue
            cv2.rectangle(fr, (int(x - 70), int(y - 110)), (int(x + 70), int(y)), (176, 140, 90), -1); cv2.rectangle(fr, (int(x - 70), int(y - 110)), (int(x + 70), int(y)), (120, 90, 56), 4)
            gpu(fr, x, y - 55, .32, t)
        float_in(fr, s.panel, 540, 360, t, .2)

class Suspicion(Sb):                               # la inteligencia de EE. UU. empezó a sospechar
    def __init__(s):
        s.back = stage_bg(9, (8, 8, 16), (90, 90, 200)); s.main = floor_layer(1600, (14, 14, 22), (28, 28, 40))
        s.front = [(bokeh_layer(10, (160, 160, 255), 409, ymin=200, ymax=1500), 1.7)]
        s.q = N.text_sprite('?', 220, (255, 230, 120, 255), glow=(255, 160, 40), glow_r=20); s.panel = blue_panel('¿ALGO MÁS?', 'SOSPECHAS DE INTELIGENCIA', w=760, h=180)
        s.eye = emoji_sprite('👁️')
    def draw(s, fr, t, d):
        a_ = math.sin(t * 1.4) * .5; p = (540 + math.sin(a_) * 500, 1500)
        fbeam(fr, (540, 560), p, 20, 220, (200, 220, 255), .16, 30); blit(fr, s.eye, 540, 600, 1, 1.2)
        who('alice', fr, 540, 1640, 520, t, armR=('reposo',), armL=('reposo',), look=(math.sin(t * 1.4) * .4, 0), frown=0.)
        blit(fr, s.q, 800, 1050, ss(.5, .9, t), 1 + .05 * math.sin(t * 5))
        float_in(fr, s.panel, 540, 330, t, .2)

# ================================================================ ¿CÓMO LO DESCUBRIERON?
class Surveil(Sb):                                 # las agencias llevaban tiempo vigilándola
    def __init__(s):
        bg = vgrad([(0, (8, 10, 14)), (1, (18, 22, 30))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1560, (20, 22, 28), (34, 36, 44))
        s.front = [(bokeh_layer(8, (120, 200, 255), 410, ymin=200, ymax=1200), 1.7)]
        s.panel = blue_panel('VIGILANCIA', 'SEGÚN INVESTIGACIONES PERIODÍSTICAS', w=900, h=180); s.rec = label('● REC', 34, (255, 70, 60))
    def draw(s, fr, t, d):
        for i in range(4):                                                     # muro de monitores
            x, y = 130 + (i % 2) * 420, 560 + (i // 2) * 330
            cv2.rectangle(fr, (x, y), (x + 400, y + 300), (12, 14, 18), -1); cv2.rectangle(fr, (x + 12, y + 12), (x + 388, y + 288), (30, 60, 80), -1)
            RG.person(fr, 'alice' if i % 2 == 0 else 'figura', x + 200 + math.sin(t + i) * 60, y + 270, 220, dict(look=(.2, 0)), t + i)
            for k in range(0, 300, 6): cv2.line(fr, (x + 12, y + 12 + k), (x + 388, y + 12 + k), (20, 40, 54), 1)
            if (t * 2) % 1 < .6 and i == 0: blit(fr, s.rec, x + 320, y + 40)
        hs = who('agente', fr, 540, 1760, 520, t, armR=('apunta', (420, 1350), .6), armL=('reposo',), look=(0, -.3), frown=.3)
        float_in(fr, s.panel, 540, 330, t, .2)

class Intercept(Sb):                               # vigilancia de comunicaciones → información para Pekín (conclusión de las agencias)
    def __init__(s):
        s.back = stage_bg(11, (12, 6, 6), (200, 60, 50)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 120, 100), 411, ymin=200, ymax=1700), 1.7)]
        s.cn = flag_sprite_cn(360, 240); s.pk = label('PEKÍN', 44, (255, 220, 120)); s.panel = red_panel('COMUNICACIONES VIGILADAS', w=900, h=160)
        s.hyp = label('CONCLUSIÓN ATRIBUIDA A LAS AGENCIAS', 26, (255, 230, 200))
    def draw(s, fr, t, d):
        phone(fr, 260, 1150, 1.4, t, ring=True)
        for k in range(40):                                                    # onda interceptada
            x = 400 + k * 14; a_ = math.sin(t * 9 + k * .6) * (40 + 30 * math.sin(k * .3)); line(fr, (x, 1150 - a_), (x, 1150 + a_), (120, 230, 255), 4)
        g = ss(s.w('pekín') - .6, s.w('pekín'), t)
        if g > 0:
            blit(fr, s.cn, 820, 800, g, .9); blit(fr, s.pk, 820, 960, g)
            for k in range(6): f = (t * 1.2 + k / 6.) % 1; circ(fr, (lerp(330, 820, f), lerp(1080, 880, f) - math.sin(f * math.pi) * 120), 10, (255, 200, 120))
        float_in(fr, s.panel, 540, 330, t, .2); blit(fr, s.hyp, 540, 450, ss(.5, 1, t))

class FBIWarn(Sb):                                 # el FBI habría advertido a legisladores casi un año antes
    def __init__(s):
        sky = vgrad([(0, (14, 20, 40)), (1, (40, 50, 80))]); i8 = to8(sky); capitol(i8, 540, 1300, 1.0, (120, 130, 156))
        s.back = [(dof(opaque(i8.astype(np.float32)), 3), .35)]; s.main = floor_layer(1450, (40, 40, 48), (56, 56, 66))
        s.front = [(bokeh_layer(10, (200, 220, 255), 412, ymin=200, ymax=1400), 1.7)]
        s.panel = blue_panel('ADVERTENCIA DEL FBI', 'CASI UN AÑO ANTES DEL ESCÁNDALO', w=900, h=180)
        s.fbi = N.text_sprite('FBI', 64, (255, 230, 120, 255), stroke=4, stroke_col=(0, 0, 0, 220), spacing=8)
    def draw(s, fr, t, d):
        hs = who('agente', fr, 330, 1700, 560, t, armR=('apunta', (560, 1380), ss(.3, .9, t)), armL=('reposo',), look=(.4, 0), frown=.3)
        dossier(fr, lerp(400, 580, ss(.3, .9, t)), 1360, 150, 200, t, 1., seed=3)
        for i, (x, w_) in enumerate(((760, 'ejecutivo'), (960, 'jefe'))): who(w_, fr, x, 1720, 520, t + i, armR=('reposo',), armL=('palma',) if i else ('reposo',), look=(-.4, 0), frown=.1 + .3 * ss(.9, 1.3, t))
        blit(fr, s.fbi, 330, 1780); float_in(fr, s.panel, 540, 330, t, .2)

class Photos(Sb):                                  # fotografías de Alice junto a Jensen en reuniones y eventos privados
    def __init__(s):
        bg = vgrad([(0, (18, 12, 10)), (1, (40, 28, 22))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 210, 160), 413, ymin=200, ymax=1700), 1.7)]
        s.panel = gold_panel('FOTOGRAFÍAS JUNTOS', 'BANQUETES Y EVENTOS PRIVADOS', w=860, h=180)
    def draw(s, fr, t, d):
        for i, (x, y, ang) in enumerate(((310, 860, -6), (770, 1050, 5), (420, 1360, 3))):
            k = ss(.2 + i * .5, .5 + i * .5, t)
            if k <= 0: continue
            x = x + (1 - eOut(k)) * 600 * (1 if i % 2 else -1)
            cv2.rectangle(fr, (int(x - 230), int(y - 200)), (int(x + 230), int(y + 230)), (240, 236, 226), -1)
            cv2.rectangle(fr, (int(x - 205), int(y - 175)), (int(x + 205), int(y + 160)), (60, 40, 30) if i != 1 else (50, 90, 60), -1)
            if i != 1: cv2.rectangle(fr, (int(x - 205), int(y + 80)), (int(x + 205), int(y + 160)), (150, 110, 80), -1)     # mesa de banquete
            for q in range(3): cv2.circle(fr, (int(x - 150 + q * 150), int(y - 120)), 10, (255, 220, 150), -1, cv2.LINE_AA)
            RG.person(fr, 'jensen', x - 70, y + 150, 280, dict(look=(.3, 0), boca='sonrisa'), t)
            RG.person(fr, 'alice', x + 70, y + 150, 262, dict(look=(-.3, 0), boca='sonrisa'), t)
            if (t * 1.3 + i * .4) % 1 < .08: blit(fr, glow_sprite(140, (255, 255, 255)), x, y, .8, add=True)
        float_in(fr, s.panel, 540, 330, t, .2)

class NatSec(Sb):                                  # la relación personal se volvió un asunto de seguridad nacional
    def __init__(s):
        bg = vgrad([(0, (10, 14, 30)), (1, (26, 30, 56))]); i8 = to8(bg); DT.flag_us(i8, 140, 560, 800, 470)
        s.back = [(dof(opaque(i8.astype(np.float32)), 5), .3)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (200, 220, 255), 414, ymin=200, ymax=1700), 1.7)]
        s.st = N.stamp('SEGURIDAD NACIONAL', (255, 59, 42), w=900, h=124, px=64)
    def draw(s, fr, t, d):
        heart(fr, (540, 1150), 160, (230, 60, 110), crack=ss(.6, 1.4, t))
        stamp_in(fr, s.st, 540, 700, t, max(.3, s.w('seguridad') - .1))

class Classified(Sb):                              # las pruebas siguen clasificadas; no se ha demostrado qué se transmitió
    def __init__(s):
        bg = vgrad([(0, (14, 12, 10)), (1, (32, 28, 22))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(8, (255, 230, 180), 415, ymin=200, ymax=1700), 1.7)]
        s.pero = N.text_sprite('PERO…', 120, (255, 236, 200, 255), glow=(255, 180, 60), glow_r=16)
        s.st = N.stamp('CLASIFICADO', (255, 59, 42), w=700, h=124, px=70)
        s.t1 = chip('PRUEBAS NO PÚBLICAS', (255, 210, 90), w=600); s.t2 = chip('NO DEMOSTRADO PÚBLICAMENTE', (255, 210, 90), w=720)
    def draw(s, fr, t, d):
        blit(fr, s.pero, 540, 420, ss(0, .3, t) * (1 - ss(1.6, 2.0, t)))
        k = ss(1.7, 2.3, t)
        if k > 0:
            dossier(fr, 540, lerp(1500, 1050, eOut(k)), 700, 820, t, 1., seed=7)
            stamp_in(fr, s.st, 540, 900, t, s.w('clasificadas'))
            if t > s.w('clasificadas') + .4: float_in(fr, s.t1, 540, 330, t, s.w('clasificadas') + .4)
            if t > s.w('demostrado') - .2: float_in(fr, s.t2, 540, 450, t, s.w('demostrado') - .2)

# ================================================================ EL IMPACTO EN NVIDIA
class Problem(Sb):                                 # el problema para NVIDIA es enorme
    def __init__(s):
        s.back = stage_bg(16, (14, 6, 6), (220, 60, 40)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 120, 90), 416, ymin=200, ymax=1700), 1.7)]
        s.t = N.text_sprite('UN PROBLEMA ENORME', 66, (255, 236, 220, 255), glow=(255, 60, 40), glow_r=16, stroke=4, stroke_col=(0, 0, 0, 200))
    def draw(s, fr, t, d):
        sh = (1 - ss(.3, 1.2, t)) * 14 * math.sin(t * 60); gpu(fr, 540 + sh, 1000, 2.2, t, glow=.6)
        k = ss(.4, 1.0, t)
        for (a_, b_) in [((540, 820), (470, 980)), ((470, 980), (560, 1080)), ((560, 1080), (500, 1200)), ((540, 1000), (660, 940))]:
            line(fr, a_, (lerp(a_[0], b_[0], k), lerp(a_[1], b_[1], k)), (20, 20, 20), 8)
        blit(fr, s.t, 540, 420, ss(0, .4, t), lerp(1.3, 1, ss(0, .4, t)))

class ExportWall(Sb):                              # EE. UU. intenta impedir que China obtenga tecnología avanzada
    def __init__(s):
        bg = vgrad([(0, (8, 10, 20)), (1, (20, 20, 34))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1550, (20, 20, 30), (34, 34, 46))
        s.front = [(bokeh_layer(10, (200, 220, 255), 417, ymin=200, ymax=1500), 1.7)]
        s.us, s.cn = flag_sprite_us(340, 200), flag_sprite_cn(330, 220)
        s.p1 = green_panel('CHIPS = VENTAJA ESTRATÉGICA', w=900, h=150); s.p2 = red_panel('CONTROLES DE EXPORTACIÓN', w=900, h=150)
    def draw(s, fr, t, d):
        wk = ss(s.w('estados') - .3, s.w('estados') + .5, t)
        blit(fr, wave_flag(s.us, t), 230, 760); blit(fr, wave_flag(s.cn, t + 1.3), 850, 760)
        if wk > 0:                                                             # el muro sube entre los dos países
            top = lerp(1550, 600, eOut(wk)); cv2.rectangle(fr, (500, int(top)), (580, 1550), (90, 96, 110), -1)
            for y in range(int(top), 1550, 60): cv2.line(fr, (500, y), (580, y), (60, 64, 76), 3)
        for i in range(4):
            f = (t * .45 + i * .25) % 1; x = lerp(230, 850, f)
            if wk > .9 and x > 470: x = 470; blit(fr, glow_sprite(120, (255, 40, 20)), 540, 1100, .5 + .3 * math.sin(t * 6), add=True); line(fr, (470, 1030), (610, 1170), (255, 80, 60), 16); line(fr, (610, 1030), (470, 1170), (255, 80, 60), 16)
            gpu(fr, x, 1250 + (i % 2) * 120, .45, t)
        float_in(fr, s.p1, 540, 330, t, .2)
        if wk > 0: float_in(fr, s.p2, 540, 480, t, s.w('estados') - .3)

class Board(Sb):                                   # la junta abrió una investigación independiente
    def __init__(s):
        s.back, s.main = office(18); s.front = [(bokeh_layer(8, (255, 220, 170), 418, ymin=200, ymax=1100), 1.7)]
        s.panel = gold_panel('INVESTIGACIÓN INDEPENDIENTE', '¿FUE OBJETIVO DE UNA OPERACIÓN EXTRANJERA?', w=960, h=180); s.mag = emoji_sprite('🔍')
    def draw(s, fr, t, d):
        for i, (x, w_) in enumerate(((180, 'directora'), (420, 'ejecutivo'), (660, 'jefe'), (900, 'colette'))):
            who(w_, fr, x, 1480, 420, t + i, armR=('palma',) if (t + i) % 3 < 1 else ('reposo',), armL=('reposo',), look=((540 - x) / 900., .1), frown=.3)
        poly(fr, [(40, 1320), (1040, 1320), (1080, 1520), (0, 1520)], (70, 46, 30)); poly(fr, [(0, 1520), (1080, 1520), (1080, 1560), (0, 1560)], (44, 28, 18))
        dossier(fr, 540, 1420, 260, 150, t, 1., seed=2, redact=False)
        blit(fr, s.mag, 540 + math.sin(t * 1.5) * 90, 1400, ss(.4, .8, t), 1.0)
        float_in(fr, s.panel, 540, 340, t, .2)

class Statement(Sb):                               # NVIDIA: «sin motivos para creer» que se comprometieron secretos o la seguridad nacional
    def __init__(s):
        bg = vgrad([(0, (8, 14, 10)), (1, (18, 30, 22))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(8, (150, 240, 110), 419, ymin=200, ymax=1700), 1.7)]
        s.head = N.text_sprite('COMUNICADO DE NVIDIA', 44, (30, 60, 30, 255), pad=6, spacing=4)
        s.q = [N.text_sprite(x, 40, (30, 30, 34, 255), pad=6) for x in ('«NO HAY MOTIVOS', 'PARA CREER QUE', 'SE COMPROMETIERAN', 'SECRETOS NI LA', 'SEGURIDAD NACIONAL»')]
    def draw(s, fr, t, d):
        k = ss(0, .5, t); y = lerp(1500, 1000, eOut(k))
        cv2.rectangle(fr, (210, int(y - 520)), (870, int(y + 520)), (240, 240, 232), -1); cv2.rectangle(fr, (210, int(y - 520)), (870, int(y - 420)), GREEN, -1)
        blit(fr, s.head, 540, y - 360)
        for i, q in enumerate(s.q): blit(fr, q, 540, y - 240 + i * 66, ss(.6 + i * .25, .9 + i * .25, t))
        for i in range(5): cv2.line(fr, (270, int(y + 200 + i * 50)), (810 - (i % 3) * 80, int(y + 160 + i * 50)), (170, 170, 170), 5)

class Investors(Sb):                               # la polémica golpeó la confianza de los inversionistas
    def __init__(s):
        bg = vgrad([(0, (14, 8, 8)), (1, (30, 16, 16))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1600, (24, 18, 18), (40, 30, 30))
        s.front = [(bokeh_layer(10, (255, 120, 100), 420, ymin=200, ymax=1400), 1.7)]
        s.panel = red_panel('CONFIANZA GOLPEADA', w=760, h=160); s.lab = label('INVERSIONISTAS', 34, (255, 210, 200))
        r_ = np.random.RandomState(4); v = 0; s.pts = []
        for i in range(60): v += r_.normal(0, 1) - (2.2 if 30 < i < 44 else 0); s.pts.append(v)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (90, 560), (990, 1160), (12, 10, 12), -1); cv2.rectangle(fr, (90, 560), (990, 1160), (90, 60, 60), 4)
        n = int(2 + ss(.1, d * .8, t) * 58); mn, mx = min(s.pts), max(s.pts)
        q = [(120 + i * 14.5, 1130 - (p - mn) / (mx - mn + 1e-9) * 520) for i, p in enumerate(s.pts[:n])]
        pline(fr, q, (255, 70, 60) if n > 34 else (120, 240, 140), 6)
        for i, x in enumerate((250, 540, 830)):
            who(['ejecutivo', 'directora', 'jefe'][i], fr, x, 1760, 460, t + i, armR=('apunta', (x + 20, 1340), .9) if i == 1 else ('reposo',), armL=('reposo',), look=(0, -.4), frown=-.4 * ss(1, 2, t), smile=0)
        blit(fr, s.lab, 540, 1810); float_in(fr, s.panel, 540, 340, t, .2)

# ================================================================ ¿Y EL GOBIERNO?
class Capitol(Sb):                                 # Washington también quedó bajo presión
    def __init__(s):
        sky = vgrad([(0, (20, 26, 50)), (1, (70, 60, 80))]); i8 = to8(sky); capitol(i8, 540, 1380, 1.15, (210, 214, 226))
        s.back = [(dof(opaque(i8.astype(np.float32)), 1.5), .35)]; s.main = floor_layer(1380, (60, 60, 70), (80, 80, 92))
        s.front = [(bokeh_layer(8, (255, 230, 200), 421, ymin=200, ymax=1200), 1.7)]
        s.panel = blue_panel('WASHINGTON', 'BAJO PRESIÓN', w=720, h=180)
    def draw(s, fr, t, d):
        c = (540, 1840); cv2.ellipse(fr, c, (200, 200), 0, 180, 360, (30, 30, 40), -1, cv2.LINE_AA); cv2.ellipse(fr, c, (200, 200), 0, 180, 360, (200, 200, 210), 6, cv2.LINE_AA)
        for k, col in enumerate(((80, 200, 90), (255, 210, 90), (255, 70, 60))): cv2.ellipse(fr, c, (170, 170), 0, 180 + k * 60, 240 + k * 60, col, 18, cv2.LINE_AA)
        a_ = math.pi * (1 + ss(.2, 1.6, t) * .9 + .03 * math.sin(t * 20)); line(fr, c, (c[0] + math.cos(a_) * 150, c[1] + math.sin(a_) * 150), (240, 240, 240), 8)
        float_in(fr, s.panel, 540, 340, t, .2)
    def cam(s, t, d): k = eIO(t / d); return lerp(1.0, 1.08, k), 540, 1200, 0, 0

class Questions(Sb):                               # controles de exportación · big tech y gobierno · acceso de China
    def __init__(s):
        s.back = stage_bg(22, (8, 10, 20), (90, 120, 220)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (180, 200, 255), 422, ymin=200, ymax=1700), 1.7)]
        s.panel = blue_panel('PREGUNTAS ABIERTAS', w=760, h=150)
        s.items = [('controles', '📦', 'CONTROLES DE EXPORTACIÓN'), ('grandes', '🏛️', 'BIG TECH Y GOBIERNO'), ('acceso', '🇨🇳', 'ACCESO DE CHINA A LOS CHIPS')]
        s.spr = [(emoji_sprite(e), chip(n, (150, 200, 255), w=760)) for _, e, n in s.items]
    def draw(s, fr, t, d):
        for i, (k, _, _) in enumerate(s.items):
            tk = s.w(k) - .2
            if t < tk: continue
            e, c = s.spr[i]; y = 640 + i * 260; g = ss(tk, tk + .3, t)
            blit(fr, e, 200, y, g, .9); float_in(fr, c, 600, y, t, tk)
        float_in(fr, s.panel, 540, 360, t, .2)

class Lawmakers(Sb):                               # legisladores exigieron explicaciones a Jensen y a NVIDIA
    def __init__(s):
        wall = vgrad([(0, (40, 26, 20)), (1, (70, 46, 32))]); i8 = to8(wall)
        cv2.rectangle(i8, (0, 1040), (W, 1230), (90, 58, 36), -1); cv2.rectangle(i8, (0, 1030), (W, 1050), (150, 110, 60), -1)    # estrado
        DT.flag_us(i8, 60, 300, 260, 160); DT.flag_us(i8, 760, 300, 260, 160)
        s.back = [(dof(opaque(i8.astype(np.float32)), 2), .3)]; s.main = floor_layer(1560, (36, 28, 24), (50, 40, 34))
        s.front = [(bokeh_layer(8, (255, 220, 170), 423, ymin=200, ymax=1000), 1.7)]
        s.panel = red_panel('EXIGEN EXPLICACIONES', w=820, h=160)
    def draw(s, fr, t, d):
        for i, (x, w_) in enumerate(((200, 'ejecutivo'), (540, 'directora'), (880, 'jefe'))):
            who(w_, fr, x, 1140, 380, t + i, armR=('apunta', (540, 1300), .9) if i != 1 else ('palma',), armL=('reposo',), look=(0, .4), frown=.5)
        cv2.rectangle(fr, (0, 1000), (W, 1160), (100, 66, 40), -1); cv2.rectangle(fr, (0, 990), (W, 1010), (160, 120, 66), -1)
        who('jensen', fr, 540, 1760, 520, t, armR=('reposo',), armL=('reposo',), look=(0, -.4), frown=-.2)
        float_in(fr, s.panel, 540, 340, t, .2)

class Beijing(Sb):                                 # Pekín rechazó las acusaciones de espionaje
    def __init__(s):
        bg = vgrad([(0, (40, 8, 8)), (1, (70, 16, 14))]); i8 = to8(bg); flag_cn(i8, 150, 420, 780, 520)
        s.back = [(dof(opaque(i8.astype(np.float32)), 5), .3)]; s.main = floor_layer(1500, (40, 14, 14), (60, 24, 22))
        s.front = [(bokeh_layer(10, (255, 220, 120), 424, ymin=200, ymax=1400), 1.7)]
        s.st = N.stamp('RECHAZA LAS ACUSACIONES', (255, 59, 42), w=920, h=124, px=58); s.lab = label('PORTAVOZ DE LA CANCILLERÍA CHINA', 28, (255, 230, 200))
    def draw(s, fr, t, d):
        who('portavoz', fr, 540, 1540, 520, t, armR=('palma',) if (t % 2) < 1.1 else ('reposo',), armL=('reposo',), look=(0, 0), frown=.4)
        mic_podium(fr, 540, 1330, seal_col=(255, 210, 60), body=(90, 20, 20)); blit(fr, s.lab, 540, 1640)
        stamp_in(fr, s.st, 540, 380, t, max(.3, s.w('rechazó') - .1))

# ================================================================ EL GIRO FINAL
class Resign(Sb):                                  # 12 de noviembre: Jensen Huang renuncia; Colette Kress, CEO interina
    def __init__(s):
        s.back, s.main = office(25); s.front = [(bokeh_layer(10, (150, 240, 110), 425, ymin=200, ymax=1300), 1.7)]
        s.golpe = N.text_sprite('OTRO GOLPE', 110, (255, 236, 220, 255), glow=(255, 60, 40), glow_r=16, stroke=4, stroke_col=(0, 0, 0, 200))
        s.date = N.stamp('12 NOV 2026', (255, 59, 42), w=520, h=110, px=60); s.res = label('JENSEN HUANG RENUNCIA', 40, (255, 220, 210))
        s.card = green_panel('COLETTE KRESS', 'DIRECTORA EJECUTIVA INTERINA', w=820, h=180)
    def draw(s, fr, t, d):
        tg, tr, tc = s.w('golpe'), s.w('renunció'), s.w('colette')
        if t < tr + .2: blit(fr, s.golpe, 540, 400, ss(tg - .2, tg + .1, t) * (1 - ss(tr - .3, tr, t)), lerp(1.4, 1, ss(tg - .2, tg + .1, t)))
        if t > s.w('12') - .3: stamp_in(fr, s.date, 540, 560, t, s.w('12') - .3)
        x = 540 if t < tr else 540 - (t - tr) * 260                            # Jensen sale caminando (perfil, pies fijos)
        if x > -200:
            if t < tr: who('jensen', fr, x, 1680, 560, t, armR=('reposo',), armL=('reposo',), look=(0, .2), frown=-.3)
            else: who('jensen', fr, x, 1680, 560, t, look=(-.6, 0), frown=-.3, run=4)
        if t > tr: blit(fr, s.res, 540, 700, ss(tr, tr + .3, t) * (1 - ss(tc - .3, tc, t)))
        k = ss(tc - .5, tc + .3, t)
        if k > 0:
            xc = lerp(1300, 600, eOut(k))
            who('colette', fr, xc, 1680, 540, t, armR=('reposo',), armL=('palma',) if k > .99 else ('reposo',), look=(-.2, 0), frown=0., run=4 if k < .99 else 0)
            if t > tc: float_in(fr, s.card, 540, 360, t, tc)

class Infidelity(Sb):                              # no es solo infidelidad: espionaje, IA, dinero y poder internacional
    def __init__(s):
        s.back = stage_bg(26, (10, 8, 16), (160, 80, 200)); s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (220, 180, 255), 426, ymin=200, ymax=1700), 1.7)]
        s.l1 = N.text_sprite('NO SOLO INFIDELIDAD', 70, (255, 236, 240, 255), glow=(230, 60, 110), glow_r=14, stroke=4, stroke_col=(0, 0, 0, 200))
        s.items = [('espionaje', '🕵️', 'ESPIONAJE'), ('inteligencia', '🤖', 'IA'), ('dinero', '💰', 'DINERO'), ('poder', '🌐', 'PODER INTERNACIONAL')]
        s.spr = [(emoji_sprite(e), label(n, 34)) for _, e, n in s.items]
    def draw(s, fr, t, d):
        te = T('es', s.a + 2.5) - s.a
        if t < s.w('espionaje') - .1: heart(fr, (540, 1000), 180, (230, 60, 110), crack=ss(s.w('infidelidad') - .2, s.w('infidelidad') + .4, t)); blit(fr, s.l1, 540, 420, ss(0, .4, t) * (1 - ss(te - .2, te + .2, t)))
        for i, (k, _, _) in enumerate(s.items):
            tk = s.w(k, ) - .15 if k != 'inteligencia' else T('inteligencia', s.a + te - .5) - s.a - .15
            g = ss(tk, tk + .3, t)
            if g <= 0: continue
            x, y = [300, 780][i % 2], [700, 1120][i // 2]
            cv2.circle(fr, (x, y), 190, (30, 20, 50), -1); cv2.circle(fr, (x, y), 190, (200, 160, 255), 5)
            e, n = s.spr[i]; blit(fr, e, x, y - 30, g, lerp(1.4, .9, eOut(g))); blit(fr, n, x, y + 120, g)

class Close(Sb):                                   # ¿China usó una relación personal… o falta la verdadera historia? Te leo en comentarios
    def __init__(s):
        s.back = stage_bg(27, (8, 10, 14), (90, 200, 80)); s.main = floor_layer(1600, (16, 20, 18), (30, 40, 32))
        s.front = [(bokeh_layer(12, (150, 240, 110), 427, ymin=200, ymax=1500), 1.7)]
        s.q = N.text_sprite('?', 260, (255, 230, 120, 255), glow=(255, 160, 40), glow_r=22)
        s.panel = gold_panel('¿TÚ QUÉ CREES?', 'TE LEO EN COMENTARIOS', w=780, h=190)
        s.a1 = chip('¿OPERACIÓN DE ESPIONAJE?', (255, 140, 120), w=700); s.a2 = chip('¿FALTA LA VERDADERA HISTORIA?', (150, 200, 255), w=760)
        s.pill = DT.Blockade(None, cta=True)
    def draw(s, fr, t, d):
        who('jensen', fr, 260, 1640, 520, t, armR=('reposo',), armL=('reposo',), look=(.3, 0), frown=-.1)
        RG.person(fr, 'figura', 820, 1640, 500, dict(look=(-.3, 0)), t)
        blit(fr, s.q, 540, 1050, ss(.2, .6, t), 1 + .06 * math.sin(t * 4))
        float_in(fr, s.a1, 540, 560, t, .4)
        if t > s.w('todavía') - .2: float_in(fr, s.a2, 540, 690, t, s.w('todavía') - .2)
        if t > s.w('te') - .3: float_in(fr, s.panel, 540, 340, t, s.w('te') - .3)
        k = ss(s.w('te'), s.w('te') + .4, t)
        if k > 0: blit(fr, s.pill.ctaspr, 540, 1750, k, lerp(.6, 1, eBack(k)) * .8); blit(fr, s.pill.bell, 860, 1730 + math.sin(t * 9) * 4, k, .5)

# ================================================================ línea de tiempo
def tl():
    seq = [
        (0, Scandal(), 0), (T('su') - .25, Relation(), 0), (T('y', 11) - .25, Secrets(), 0),
        (SC_T[1], JensenIntro(), 1), (T('la', 22) - .25, ChipsAI(), 1), (T('la', 26.5) - .25, AliceIntro(), 1), (T('compañía', 32) - .3, DataCenter(), 1),
        (T('megaspeed', 35) - .25, Buyer(), 1), (T('pero', 39) - .25, Suspicion(), 1),
        (SC_T[2], Surveil(), 4), (T('mediante') - .25, Intercept(), 4), (T('el', 57.5) - .25, FBIWarn(), 4), (T('después') - .25, Photos(), 2),
        (T('la', 69.5) - .25, NatSec(), 4), (T('pero', 74) - .25, Classified(), 4),
        (SC_T[3], Problem(), 3), (T('sus', 85.5) - .25, ExportWall(), 3), (T('la', 95.8) - .25, Board(), 2), (T('la', 102.6) - .25, Statement(), 1),
        (T('sin', 109.5) - .25, Investors(), 3),
        (SC_T[4], Capitol(), 1), (T('la', 116.3) - .25, Questions(), 1), (T('legisladores', 125) - .25, Lawmakers(), 2), (T('mientras') - .25, Beijing(), 3),
        (SC_T[5], Resign(), 3), (T('el', 141.3) - .25, Infidelity(), 4),
        (SC_T[6], Close(), 4),
    ]
    out = []
    for i, (a, sc, g) in enumerate(seq):
        b = seq[i + 1][0] if i + 1 < len(seq) else DUR; sc.a = a; out.append((a, b, sc, g))
    return out

KEYW = {'escándalo', 'internacional', 'ceo', 'china', 'secretos', 'inteligencia', 'artificial', 'jensen', 'huang', 'nvidia', 'alice', 'megaspeed', 'chips',
        'sospechar', 'vigilando', 'comunicaciones', 'pekín', 'fbi', 'año', 'fotografías', 'seguridad', 'nacional', 'clasificadas', 'demostrado', 'enorme',
        'ventaja', 'estratégica', 'investigación', 'independiente', 'extranjera', 'comprometidos', 'inversionistas', 'washington', 'presión', 'exportación',
        'explicaciones', 'rechazó', 'espionaje', 'golpe', 'renunció', 'colette', 'kress', 'interina', 'infidelidad', 'dinero', 'poder', 'verdadera', 'comentarios'}
TR.KEY = KEYW

_s = CH._src.replace("secs = [(0, 'tension', 1), (9.9, 'misterio', 2), (24.1, 'tension', 2), (37.2, 'epico', 2), (50.2, 'tension', 1)]",
     f"secs = [(0, 'tension', 1), ({SC_T[1]:.2f}, 'misterio', 2), ({SC_T[2]:.2f}, 'tension', 2), ({SC_T[3]:.2f}, 'epico', 2), ({SC_T[4]:.2f}, 'misterio', 2), ({SC_T[5]:.2f}, 'tension', 2), ({SC_T[6]:.2f}, 'epico', 1)]")
_a = _s.index('    EF = ['); _b = _s.index(']]', _a) + 2
_ef = [[0, 'boom', .9], [.3, 'latido', .3]]
for (a_, b_, sc, g) in tl()[1:]: _ef += [[a_ - .25, 'whoosh', .32], [a_, 'impacto', .38]]
_ef += [[T('china', 9) , 'impacto', .7], [T('secretos') , 'riser', .25], [T('mediante'), 'tecleo', .12, 2.0], [T('pekín'), 'impacto', .6],
        [T('fbi'), 'beep', .2], [T('fotografías'), 'glitch', .15], [T('seguridad', 70), 'impacto', .7], [T('clasificadas'), 'impacto', .6],
        [T('enorme'), 'boom', .6], [T('inversionistas'), 'caida', .3], [T('rechazó'), 'impacto', .6], [T('golpe'), 'boom', .7],
        [T('renunció'), 'impacto', .6], [T('colette'), 'ding', .25], [T('comentarios') , 'ding', .3]]
_s = _s[:_a] + '    EF = ' + repr(sorted(_ef, key=lambda e: e[0])) + _s[_b:]
_s = _s.replace("env / (env.max() * .25)", "env / (env.max() * .25 + 1e-9)").replace("duck = 1 - .55 * env", "duck = 1 - .7 * env").replace(
    "out = np.tanh((mus * .75 * duck + fx * .6 * (1 - .35 * env)) * 1.1) * .8 + vv * .92",
    "out = np.tanh((mus * .5 * duck + fx * .32 * (1 - .5 * env)) * 1.1) * .7 + vv * .95")
exec(_s)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    TR.DUR = DUR
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in TR.build_subs(WORDS)]
    shots = tl()
    pill = DT.Blockade(None, cta=True); C0, C1 = T('según', 44) - 1.0, T('pekín') + 1.0          # «dale like y sígueme» a mitad del video
    def one(i, T_):
        a, b, sc, g = shots[i]; return cinema(render3d(sc, T_ - a, b - a, T_), g, T_)
    def frame(T_):
        i = max(k for k, s_ in enumerate(shots) if T_ >= s_[0] - 1e-6)
        fr = one(i, T_); a = shots[i][0]
        if i > 0 and T_ - a < .3: fr = cv2.addWeighted(one(i - 1, T_), 1 - ss(0, .3, T_ - a), fr, ss(0, .3, T_ - a), 0)
        c = ss(C0, C0 + .4, T_) * (1 - ss(C1 - .3, C1, T_))
        if c > 0: blit(fr, pill.ctaspr, 760, 1720, c, lerp(.6, 1, eBack((T_ - C0) / .4)) * .6); blit(fr, pill.bell, 1010, 1700 + math.sin(T_ * 9) * 4, c, .4)
        draw_overlays(fr, T_, subs, []); return fr
    if mode == 'info':
        print('DUR', DUR, 'SC_T', [round(x, 2) for x in SC_T])
        for a, b, sc, g in shots: print(f'{a:6.2f}-{b:6.2f} {b - a:5.2f} {type(sc).__name__}')
    elif mode == 'test':
        import traceback
        for T_ in [float(x) for x in sys.argv[2:]]:
            try: cv2.imwrite(f'{OUT}/n_{T_:05.1f}.jpg', cv2.resize(frame(T_), (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
            except Exception as e: print('ERROR', T_, repr(e)); traceback.print_exc(limit=-3)
    elif mode == 'seg':
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', f'{OUT}/seg_{f0:05d}.mp4'], stdin=subprocess.PIPE)
        for i in range(f0, f1): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('SEG', f0, f1, flush=True)
    elif mode == 'audio': synth_audio(f'{OUT}/audio.wav'); print('audio ok')

if __name__ == '__main__': main()
