#!/usr/bin/env python3
# Short: ¿Y si México aplicara el modelo Bukele? · 1080x1920 · 30 fps · estilo 2.5D de la plantilla.
# Cifras verificadas (noviembre 2026): tasa de homicidios oficial 38.0 (2019) → 1.3 (2025) = −96.6 %;
# más de 93,000 detenidos bajo el régimen de excepción; más de 6,400 denuncias de abusos (EFE / HRW / Cristosal / SJH).
import os, sys, json, math
HERE_B = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE_B, '..', 'trump-mexico')); sys.path.insert(0, os.path.join(HERE_B, '..', 'chapo'))
import trump as TR
from trump import *          # utilidades del short anterior (mapas, banderas, camiones, sellos, hologramas...)

OUT = os.path.join(HERE_B, 'out'); os.makedirs(OUT, exist_ok=True)
WORDS = json.load(open(os.path.join(HERE_B, 'words.json')))
VOZ = os.path.join(HERE_B, 'voz.mp3')
_clean = TR._clean
def T(word, after=-1.):
    for w in WORDS:
        if w[1] >= after and _clean(w[0]).startswith(word.lower()): return w[1]
    raise KeyError(word)
DUR = int(math.ceil(WORDS[-1][2] + 2.0))
SC_T = [0, T('en', 10) - .35, T('ahora') - .35, T('las', 70) - .35, T('además', 100) - .4, T('entonces') - .45, DUR]
class Sb(Shot):
    a = 0.
    def w(s, word): return T(word, s.a - .6) - s.a
red_panel = DT.RS.red_panel
def gold_panel(t1, t2=None, w=760, h=160): return N.holo_panel(w, h, t1, t2, col=(255, 210, 90), fill=(60, 40, 6, 190))
def blue_panel(t1, t2=None, w=760, h=160): return N.holo_panel(w, h, t1, t2)

# ---------------------------------------------------------------- personajes: rig articulado nuevo (episodio 01)
sys.path.insert(0, os.path.join(HERE_B, '..', 'episodio01'))
import rig as RG
KIND = {'militar': 'soldado', 'cecot': 'reo', 'traje': 'ejecutivo', 'elegante': 'jefe', 'bata': 'doctora', 'comando': 'soldado', 'reo': 'reo'}
def rig_character(fr, kind, x, fy, hgt, t, armR=('reposo',), armL=('reposo',), look=(0., 0.), frown=.3, smile=0., run=0., cuffs=False, cap=False,
                  mustache=False, hair=None, sash=False, mask=False, beret=False, who=None, **kw):
    """adaptador: las escenas siguen describiendo poses sencillas (reposo, jarra, palma, apunta) y aquí se traducen al rig
    articulado (codos y rodillas con IK, pies fijos al caminar, peinados que no tapan las cejas)."""
    if who is None:
        who = KIND.get(kind) or ('pandillero' if (kind == 'civil' and cap) else 'vecino' if kind == 'civil' else ('presidenta' if sash else 'vecina') if kind == 'dama' else 'ejecutivo')
    u = hgt * RG.CAST[who]['alto'] / 8.
    p = dict(frown=frown * .9, boca='sonrisa' if smile > .3 else 'neutra', look=tuple(look), blink=RG.blink(t, int(x) % 7), grip={})
    side = run > 0
    d = 1 if look[0] >= 0 else -1
    if side:
        gp, feet, bob = RG.gait_x(x, d, u, fy); p.update(gp); p['look'] = (.55 * d, look[1])
    for key, pose in (('R', armR), ('L', armL)):
        sd = 1 if key == 'R' else -1
        if pose[0] == 'apunta': p['grip'][key] = (pose[1][0], pose[1][1], pose[2])
        elif side: continue
        elif pose[0] == 'jarra': p['grip'][key] = (x + sd * 1.05 * u, fy - 3.45 * u, 1.); p['codo_afuera'] = True
        elif pose[0] == 'palma': p['u' + key] = sd * .55; p['l' + key] = sd * 1.9
    if not p['grip']: p['grip'] = None                                            # sin agarres: brazos con su pose natural
    if side: hands, j = RG.person_side(fr, who, x, fy + bob, hgt, p, t, feet=feet, facing=d)
    else: hands, j = RG.person(fr, who, x, fy, hgt, p, t)
    if cuffs and 'L' in hands and 'R' in hands:                                  # esposas en las muñecas
        a_, b_ = A(*hands['L']), A(*hands['R'])
        for q in (a_, b_): cv2.circle(fr, P8(q), int(.3 * u * 8), (200, 206, 216), max(2, int(.06 * u)), cv2.LINE_AA, 3)
        for k in range(5): cv2.circle(fr, P8(a_ + (b_ - a_) * (k + .5) / 5 + A(0, math.sin((k + .5) / 5 * math.pi) * .15 * u)), int(.06 * u * 8), (190, 196, 206), 2, cv2.LINE_AA, 3)
    hR, hL = A(*hands.get('R', (x + u, fy - 3 * u))), A(*hands.get('L', (x - u, fy - 3 * u)))
    return {1: (hR, hR), -1: (hL, hL)}
character = rig_character
CH.character = rig_character                                                    # también el narrador del cierre
def bukele(fr, x, fy, h, t, **kw): return rig_character(fr, 'traje', x, fy, h, t, who='bukele', **kw)
def presidenta(fr, x, fy, h, t, **kw):
    kw.pop('frown', None); return rig_character(fr, 'dama', x, fy, h, t, who='presidenta', frown=0., **kw)
OUTF['cecot'] = dict(top=(236, 236, 236), pants=(236, 236, 236), shoe=(220, 220, 220))

SV = [(-90.13, 13.73), (-89.8, 14.05), (-89.57, 14.4), (-89.35, 14.43), (-89.05, 14.33), (-88.8, 14.15), (-88.5, 13.98), (-88.05, 13.98), (-87.75, 13.85),
      (-87.8, 13.38), (-88.3, 13.17), (-88.9, 13.27), (-89.5, 13.48), (-89.85, 13.52), (-90.13, 13.73)]
def sv_map(img, x0, y0, w, h, glow=(60, 160, 255)):
    lo0, lo1, la0, la1 = -92.5, -86.5, 12.2, 15.6
    P = lambda p: np.stack([x0 + (np.array(p)[:, 0] - lo0) / (lo1 - lo0) * w, y0 + (la1 - np.array(p)[:, 1]) / (la1 - la0) * h], 1)
    for poly_ in (CA, MX):
        q = np.round(P(poly_) * 8).astype(np.int32); cv2.fillPoly(img, [q], (40, 56, 80), cv2.LINE_AA, 3); cv2.polylines(img, [q], True, (90, 120, 160), 2, cv2.LINE_AA, 3)
    q = np.round(P(chaikin(SV)) * 8).astype(np.int32); cv2.fillPoly(img, [q], dark(glow, .5), cv2.LINE_AA, 3); cv2.polylines(img, [q], True, glow, 5, cv2.LINE_AA, 3)
    return P
def flag_sv(img, x, y, w=210, h=130):
    for k, c in enumerate([(20, 70, 170), (245, 245, 245), (20, 70, 170)]): cv2.rectangle(img, (x, y + k * h // 3), (x + w, y + (k + 1) * h // 3), c, -1)
    cv2.circle(img, (x + w // 2, y + h // 2), max(4, h // 9), (200, 170, 60), -1, cv2.LINE_AA)
def flag_sv_sprite(w=440, h=280):
    f = np.zeros((h, w, 3), np.uint8); flag_sv(f, 0, 0, w, h); return np.dstack([f, np.full((h, w), 255, np.uint8)])
def night_street(seed=1, col=(30, 26, 34)):
    sky = vgrad([(0, (6, 6, 14)), (.55, (24, 20, 30)), (1, (40, 28, 32))]); back = [(dof(opaque(sky), 2), .1)]
    city = np.zeros((H, W, 3), np.uint8); r_ = np.random.RandomState(seed); x = -20
    while x < W:
        bw, bh = r_.randint(110, 200), r_.randint(300, 700); cv2.rectangle(city, (x, 1260 - bh), (x + bw, 1270), col, -1)
        for wy in range(1260 - bh + 20, 1250, 36):
            for wx in range(x + 12, x + bw - 16, 28):
                if r_.rand() < .25: cv2.rectangle(city, (wx, wy), (wx + 12, wy + 16), (255, 180, 100), -1)
        if r_.rand() < .5: cv2.rectangle(city, (x + 20, 1060), (x + bw - 20, 1270), dark(col, 1.25) if False else (46, 40, 50), -1)
        x += bw + r_.randint(4, 12)
    back.append((dof(haze(rgba(city, np.any(city > 0, 2).astype(np.float32)), (40, 28, 32), .3), 2), .45))
    return back, floor_layer(1270, (34, 32, 36), (46, 44, 48))
def seated_rows(fr, x0, y0, rows, cols, dx, dy, sc, t, upto=None):
    """filas de reclusos sentados con uniforme gris, número de reo y cabeza rapada."""
    n = 0; tot = rows * cols
    for r in range(rows):
        for c in range(cols):
            n += 1
            if upto is not None and n > upto * tot: return
            x = x0 + c * dx + (r % 2) * dx * .5; y = y0 + r * dy; s_ = sc * (1 + r * .08)
            cv2.ellipse(fr, (int(x), int(y + 26 * s_)), (int(31 * s_), int(35 * s_)), 0, 0, 360, (86, 90, 96), -1, cv2.LINE_AA)
            cv2.ellipse(fr, (int(x), int(y + 26 * s_)), (int(28 * s_), int(32 * s_)), 0, 0, 360, (122, 126, 132), -1, cv2.LINE_AA)
            cv2.rectangle(fr, (int(x - 16 * s_), int(y + 14 * s_)), (int(x + 16 * s_), int(y + 28 * s_)), (236, 236, 230), -1)
            if s_ > .75: cv2.putText(fr, str(1000 + (r * 97 + c * 31) % 9000), (int(x - 14 * s_), int(y + 26 * s_)), cv2.FONT_HERSHEY_PLAIN, .55 * s_, (30, 30, 34), 1, cv2.LINE_AA)
            cv2.circle(fr, (int(x), int(y - 16 * s_)), int(20 * s_), (230, 226, 220), -1, cv2.LINE_AA)
            cv2.circle(fr, (int(x), int(y - 16 * s_)), int(20 * s_), (150, 150, 160), 2, cv2.LINE_AA)
def bars(fr, x0, x1, y0, y1, k=1., col=(90, 96, 106), step=64):
    for x in range(int(x0), int(x1), step):
        yb = y0 + (y1 - y0) * (1 - k)
        cv2.rectangle(fr, (x, int(y0)), (x + 18, int(y0 + (y1 - y0) * k)), col, -1); cv2.rectangle(fr, (x + 4, int(y0)), (x + 8, int(y0 + (y1 - y0) * k)), (170, 176, 186), -1)
def chip(txt, col=(255, 210, 90)): return N.holo_panel(460, 90, txt, None, col=col, fill=tuple(int(c * .22) for c in col) + (200,))

# ================================================================ GANCHO
class MexWar(D.S3D, Sb):                           # el mapa de México se tiñe de rojo: «guerra total»
    a = 0.
    def __init__(s):
        D.S3D.__init__(s); s.title = red_panel('GUERRA TOTAL A LOS CÁRTELES', w=920, h=170); s.dot = glow_sprite(60, (255, 40, 30))
        s.pts = [(-107.4, 24.8), (-101.9, 19.2), (-103.4, 20.7), (-99.9, 17.6), (-101.2, 21.0), (-100.3, 25.7), (-106.4, 31.7), (-99.1, 19.4), (-117.0, 32.5)]
    def draw(s, fr, t, d):
        for i, p in enumerate(s.pts):
            g = ss(.3 + i * .18, .8 + i * .18, t)
            if g <= 0: continue
            x, y = prj(*p); blit(fr, s.dot, x, y, g * (.6 + .4 * math.sin(t * 6 + i)), add=True); circ(fr, (x, y), 8, (255, 230, 220))
            f = (t * .8 + i * .13) % 1; cv2.circle(fr, (int(x), int(y)), int(14 + f * 70), (int(255 * (1 - f)), int(50 * (1 - f)), 40), 3, cv2.LINE_AA)
    def floating(s, fr, t, d, P): float_in(fr, s.title, 540, 330, t, .3); s.dust.draw(fr, t)
    def cam(s, t, d): k = eExpo(t / 1.5); return lerp(1.8, 1.25, k) * (1 + .04 * ss(1.5, d, t)), 520, 1150, 0, 0

class Soldiers(Sb):                                # miles de soldados salen a las calles
    def __init__(s):
        s.back, s.main = night_street(3); s.front = [(bokeh_layer(12, (255, 80, 60), 301, ymin=200, ymax=1500), 1.7)]
        s.panel = red_panel('MILES DE SOLDADOS EN LAS CALLES', w=940, h=160)
    def draw(s, fr, t, d):
        on = (t * 2.4) % 1 < .5; tint_ = (255, 40, 40) if on else (40, 90, 255)
        blit(fr, glow_sprite(300, tint_), 540, 1100, .25, add=True)
        for i in range(3): truck(fr, lerp(-420, 1200, ((t / 5.) + i * .34) % 1.2 - .1), 1340, 1.0)
        for r, (fy, h, n) in enumerate([(1500, 300, 4), (1620, 360, 4), (1760, 420, 3)]):
            for i in range(n):
                x = (i * (W + 300) / n + t * 90 + r * 140) % (W + 300) - 150
                hs = character(fr, 'militar', x, fy, h, t + i * .3 + r, armR=('apunta', (x + 200, fy - h * .6), .85), armL=('apunta', (x + 200, fy - h * .6), .45), look=(.5, 0), frown=.35, run=4)
                lib.rifle(fr, hs, h / 8.)
        float_in(fr, s.panel, 540, 330, t, .2)
    def cam(s, t, d): k = eIO(t / d); return lerp(1.04, 1.12, k), 540, 1150, lerp(-40, 40, k), 0

class PrisonFill(Sb):                              # las cárceles se llenan
    def __init__(s):
        bg = vgrad([(0, (20, 20, 26)), (1, (40, 40, 48))]); s.back = [(dof(opaque(bg), 2), .2)]
        s.main = floor_layer(1500, (60, 60, 66), (74, 74, 80)); s.front = [(bokeh_layer(8, (255, 230, 200), 302, ymin=200, ymax=1200), 1.7)]
        s.panel = red_panel('CÁRCELES LLENAS', w=700, h=160); s.hip = N.text_sprite('ESCENARIO HIPOTÉTICO', 34, (255, 230, 170, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=6)
    def draw(s, fr, t, d):
        for c in range(3):
            x0 = 80 + c * 320; cv2.rectangle(fr, (x0, 600), (x0 + 280, 1480), (54, 54, 62), -1); cv2.rectangle(fr, (x0, 600), (x0 + 280, 1480), (110, 110, 120), 6)
            k = ss(.3 + c * .4, 1.8 + c * .4, t)
            for r in range(5):
                for q in range(3):
                    if (r * 3 + q) / 15. < k: cv2.circle(fr, (x0 + 50 + q * 90, 680 + r * 160), 26, (230, 226, 220), -1, cv2.LINE_AA); cv2.ellipse(fr, (x0 + 50 + q * 90, 740 + r * 160), (34, 30), 0, 180, 360, (122, 126, 132), -1, cv2.LINE_AA); cv2.rectangle(fr, (x0 + 38 + q * 90, 722 + r * 160), (x0 + 62 + q * 90, 734 + r * 160), (236, 236, 230), -1)
            bars(fr, x0, x0 + 280, 600, 1480)
        blit(fr, s.hip, 540, 520, ss(.3, .7, t))
        float_in(fr, s.panel, 540, 330, t, .2)

class BukeleQ(Sb):                                 # ¿podría México conseguir lo que Bukele consiguió?
    def __init__(s):
        bg = vgrad([(0, (8, 10, 22)), (1, (22, 22, 40))]); radial(bg, (540, 900), 700, (60, 80, 160), .25)
        s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1600, (20, 22, 34), (34, 36, 52)); s.front = [(bokeh_layer(12, (200, 220, 255), 303, ymin=200, ymax=1500), 1.7)]
        s.sv, s.mx = flag_sv_sprite(), flag_sprite(True)
        s.panel = gold_panel('¿EL MODELO BUKELE', 'EN MÉXICO?', w=760, h=180)
        s.n1 = N.text_sprite('EL SALVADOR', 34, (200, 220, 255, 255), spacing=6, stroke=3, stroke_col=(0, 0, 0, 220)); s.n2 = N.text_sprite('MÉXICO', 34, (200, 255, 210, 255), spacing=6, stroke=3, stroke_col=(0, 0, 0, 220))
    def draw(s, fr, t, d):
        for spr, x, ph in ((s.sv, 270, 0), (s.mx, 810, 1.7)): blit(fr, wave_flag(spr, t + ph), x, 760, 1, .9)
        blit(fr, s.n1, 270, 1000); blit(fr, s.n2, 810, 1000)
        bukele(fr, 290, 1640, 520, t, armR=('apunta', (600, 1100), ss(.4, 1, t)), armL=('jarra',), look=(.4, 0), frown=.2, smile=.2)
        presidenta(fr, 800, 1640, 500, t, armR=('reposo',), armL=('palma',), look=(-.4, 0))
        float_in(fr, s.panel, 540, 330, t, .3)

# ================================================================ EL CASO SALVADOREÑO
class March2022(Sb):                               # marzo 2022: ola de asesinatos
    def __init__(s):
        bg = vgrad([(0, (8, 8, 16)), (1, (24, 16, 22))]); i8 = to8(bg); sv_map(i8, 60, 700, 960, 560, glow=(255, 80, 60)); s.back = [(dof(opaque(i8.astype(np.float32)), 1.2), .3)]
        s.main = np.zeros((H, W, 4), np.uint8); s.front = [(bokeh_layer(10, (255, 90, 70), 304, ymin=200, ymax=1700), 1.7)]
        s.cal = np.zeros((320, 300, 4), np.uint8); im = Image.fromarray(s.cal); dd = ImageDraw.Draw(im)
        dd.rounded_rectangle((4, 4, 295, 315), 26, fill=(240, 236, 228, 255)); dd.rectangle((4, 4, 295, 90), fill=(200, 30, 40, 255)); s.cal = np.array(im)
        over(s.cal, N.text_sprite('MARZO', 46, (255, 255, 255, 255), pad=6, spacing=4), 150, 48); over(s.cal, N.text_sprite('2022', 110, (40, 30, 30, 255), pad=6), 150, 200)
        s.panel = red_panel('OLA DE ASESINATOS', w=760, h=160); s.dots = np.random.RandomState(5).uniform(0, 1, (24, 2))
    def draw(s, fr, t, d):
        P = lambda lo, la: (60 + (lo + 92.5) / 6. * 960, 700 + (15.6 - la) / 3.4 * 560)
        for i, (a_, b_) in enumerate(s.dots):
            g = ss(.4 + i * .08, .7 + i * .08, t)
            if g > 0: x, y = P(-90 + a_ * 2.1, 13.3 + b_ * .95); blit(fr, glow_sprite(26, (255, 40, 30)), x, y, g, add=True); circ(fr, (x, y), 4, (255, 220, 210))
        k = ss(0, .4, t); blit(fr, s.cal, 540, 560, k, lerp(1.3, 1, eOut(k)))
        float_in(fr, s.panel, 540, 300, t, 1.0)

class Decree(Sb):                                  # Bukele declara el régimen de excepción
    def __init__(s):
        bg = vgrad([(0, (14, 18, 34)), (1, (26, 30, 52))]); i8 = to8(bg)
        for x in (120, 760): flag_sv(i8, x, 260, 200, 124); cv2.line(i8, (x - 4, 240), (x - 4, 1100), (200, 170, 90), 6)
        cv2.circle(i8, (540, 400), 150, (200, 170, 90), 8, cv2.LINE_AA); cv2.circle(i8, (540, 400), 136, (20, 60, 150), -1, cv2.LINE_AA)
        s.back = [(dof(opaque(i8.astype(np.float32)), 3), .4)]; s.main = floor_layer(1350, (30, 30, 40), (44, 44, 56))
        crowd = np.zeros((H, W, 4), np.uint8)
        for i in range(14): cv2.circle(crowd, (int(i * 85 - 20), 1760 + (i % 2) * 40), 64, (10, 10, 14, 255), -1)
        s.front = [(dof(crowd, 9), 1.5), (bokeh_layer(10, (200, 220, 255), 305, ymin=300, ymax=1500), 1.7)]
        s.stamp = N.stamp('RÉGIMEN DE EXCEPCIÓN', (255, 59, 42), w=900, h=124, px=64)
    def draw(s, fr, t, d):
        bukele(fr, 540, 1400, 480, t, armR=('palma',) if (t % 2.2) < 1.2 else ('apunta', (700, 1000), .7), armL=('reposo',), look=(0, 0), frown=.45)
        mic_podium(fr, 540, 1180, body=(30, 40, 70))
        for i in range(4):
            f = (t * .9 + i * .29) % 1
            if f < .12: blit(fr, glow_sprite(60, (255, 255, 255)), 120 + i * 260, 1650, (1 - f / .12) * .8, add=True)
        stamp_in(fr, s.stamp, 540, 620, t, max(.4, s.w('régimen')))

class Arrests(Sb):                                 # detenciones masivas
    def __init__(s):
        s.back, s.main = night_street(6); s.front = [(bokeh_layer(12, (255, 90, 70), 306, ymin=200, ymax=1500), 1.7)]
        s.panel = red_panel('DETENCIONES MASIVAS', w=820, h=160)
    def draw(s, fr, t, d):
        on = (t * 2.4) % 1 < .5; blit(fr, glow_sprite(320, (255, 40, 40) if on else (40, 90, 255)), 540, 1150, .25, add=True)
        for i in range(5):                                                   # fila de detenidos esposados, escoltados
            x = 1180 - (t * 110 + i * 230) % 1500
            character(fr, 'cecot', x, 1640, 400, t + i, armR=('apunta', (x - 40, 1450), .7), armL=('apunta', (x - 60, 1450), .7), look=(-.5, -.3), frown=-.1, cuffs=True, run=4)
            if i % 2 == 0:
                hs = character(fr, 'militar', x + 120, 1660, 420, t + i, armR=('apunta', (x - 120, 1450), .8), armL=('apunta', (x - 120, 1450), .45), look=(-.5, 0), frown=.35, run=4)
                lib.rifle(fr, hs, 420 / 8.)
        float_in(fr, s.panel, 540, 330, t, .2)

class Ops(Sb):                                     # operaciones militares en barrios
    def __init__(s):
        s.back, s.main = night_street(7, col=(36, 30, 30)); s.front = [(bokeh_layer(10, (255, 200, 140), 307, ymin=200, ymax=1200), 1.7)]
        s.panel = gold_panel('OPERACIONES MILITARES', 'CERCOS A COMUNIDADES ENTERAS', w=860, h=170)
    def draw(s, fr, t, d):
        hx = lerp(1000, 300, ss(0, d, t)); CH.heli(fr, hx, 480, 1.3, t, col=(70, 78, 70)); fbeam(fr, (hx, 530), (hx - 80, 1300), 14, 170, (220, 240, 255), .14, 30)
        for i, (x0, fy, h) in enumerate([(80, 1700, 440), (330, 1620, 380), (600, 1560, 330), (-100, 1560, 330)]):
            x = x0 + 110 * ss(0, d, t)
            hs = character(fr, 'militar', x, fy, h, t + i, armR=('apunta', (x + 260, fy - h * .62), .85), armL=('apunta', (x + 260, fy - h * .62), .45), look=(.5, 0), frown=.4, run=3)
            lib.rifle(fr, hs, h / 8.)
        float_in(fr, s.panel, 540, 330, t, .2)

class Constitution(Sb):                            # suspensión de garantías constitucionales
    def __init__(s):
        bg = vgrad([(0, (14, 10, 8)), (1, (34, 26, 18))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 210, 140), 308, ymin=200, ymax=1600), 1.7)]
        s.title = N.text_sprite('CONSTITUCIÓN', 54, (90, 60, 30, 255), pad=6, spacing=6); s.stamp = N.stamp('GARANTÍAS SUSPENDIDAS', (255, 59, 42), w=920, h=124, px=60)
        s.items = [N.text_sprite(x, 30, (60, 40, 30, 255), pad=4, maxw=380) for x in ('Art. · Libertad de reunión', 'Art. · Derecho a la defensa', 'Art. · Plazo de detención', 'Art. · Inviolabilidad de comunicaciones')]
    def draw(s, fr, t, d):
        cx, cy = 540, 1020; op = ss(.1, .6, t)
        poly(fr, [(cx - 440, cy - 380), (cx, cy - 360), (cx, cy + 380), (cx - 440, cy + 360)], (232, 222, 196)); poly(fr, [(cx, cy - 360), (cx + 440, cy - 380), (cx + 440, cy + 360), (cx, cy + 380)], (240, 232, 206))
        line(fr, (cx, cy - 400), (cx, cy + 420), (170, 150, 120), 6); blit(fr, s.title, cx - 210, cy - 320)
        for i, it in enumerate(s.items):
            k = ss(.5 + i * .3, .8 + i * .3, t); blit(fr, it, cx + 210, cy - 280 + i * 120, k)
            kk = ss(1.0 + i * .3, 1.3 + i * .3, t)
            if kk > 0: line(fr, (cx + 20, cy - 280 + i * 120), (cx + 20 + 380 * kk, cy - 280 + i * 120), (220, 40, 40), 8)
        stamp_in(fr, s.stamp, 540, 520, t, 1.4)

class Cecot(Sb):                                   # la megacárcel
    def __init__(s):
        sky = vgrad([(0, (6, 8, 16)), (1, (30, 34, 46))]); s.back = [(dof(opaque(sky), 2), .1)]
        hills = np.zeros((H, W, 3), np.uint8); poly(hills, [(-50, 900), (300, 760), (620, 860), (900, 720), (1130, 820), (1130, 1000), (-50, 1000)], (24, 30, 30))
        s.back.append((dof(haze(rgba(hills, np.any(hills > 0, 2).astype(np.float32)), (30, 34, 46), .3), 3), .3))
        m = np.zeros((H, W, 3), np.uint8); m[1000:] = (60, 64, 60); al = np.zeros((H, W)); al[1000:] = 1
        cv2.rectangle(m, (60, 1100), (1020, 1160), (160, 160, 166), -1); cv2.rectangle(m, (60, 1560), (1020, 1620), (160, 160, 166), -1)   # muros
        cv2.rectangle(m, (60, 1100), (110, 1620), (160, 160, 166), -1); cv2.rectangle(m, (970, 1100), (1020, 1620), (160, 160, 166), -1)
        for r in range(2):
            for c in range(4): cv2.rectangle(m, (150 + c * 210, 1200 + r * 180), (320 + c * 210, 1340 + r * 180), (120, 124, 132), -1); [cv2.line(m, (155 + c * 210, 1215 + r * 180 + k * 16), (315 + c * 210, 1215 + r * 180 + k * 16), (96, 100, 108), 3) for k in range(8)]
        s.towers = [(60, 1100), (1020, 1100), (60, 1560), (1020, 1560)]
        for (x, y) in s.towers: cv2.rectangle(m, (x - 30, y - 170), (x + 30, y), (130, 130, 138), -1); cv2.rectangle(m, (x - 46, y - 210), (x + 46, y - 170), (100, 100, 108), -1)
        s.main = rgba(m, al); s.front = [(bokeh_layer(10, (220, 230, 255), 309, ymin=300, ymax=1100), 1.7)]
        s.panel = blue_panel('CECOT', 'MEGACÁRCEL · CAPACIDAD ANUNCIADA: 40,000', w=880, h=170)
    def draw(s, fr, t, d):
        for i, (x, y) in enumerate(s.towers):
            a_ = t * .8 + i * 1.6; p1 = (x + math.cos(a_) * 600, y + 250 + math.sin(a_) * 160)
            fbeam(fr, (x, y - 190), p1, 8, 90, (230, 240, 255), .12, 24); blit(fr, glow_sprite(30, (255, 255, 230)), x, y - 190, .9, add=True)
        float_in(fr, s.panel, 540, 330, t, .3)
    def cam(s, t, d): k = eIO(t / d); return lerp(1.2, 1.05, k), 540, lerp(1150, 1250, k), 0, 0          # grúa que se aleja

class Chart97(Sb):                                 # la tasa de homicidios: 38.0 → 1.3
    def __init__(s):
        bg = vgrad([(0, (6, 10, 20)), (1, (14, 22, 36))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (120, 200, 255), 310, ymin=200, ymax=1700), 1.7)]
        s.scr = N.holo_panel(940, 960, 'TASA DE HOMICIDIOS', 'POR CADA 100 MIL HABITANTES · DATOS OFICIALES')
        s.vals = [(2019, 38.0), (2020, 19.7), (2021, 18.1), (2022, 7.8), (2023, 2.4), (2024, 1.9), (2025, 1.3)]
        s.lbl = {y: N.text_sprite(str(y), 28, (200, 230, 255, 255), pad=4) for y, _ in s.vals}
        s.v0 = N.text_sprite('38.0', 46, (255, 120, 100, 255), stroke=3, stroke_col=(0, 0, 0, 220)); s.v1 = N.text_sprite('1.3', 46, (120, 255, 170, 255), stroke=3, stroke_col=(0, 0, 0, 220))
        s.big = N.text_sprite('−97 %', 170, (120, 255, 170, 255), glow=(60, 220, 120), glow_r=18)
        s.src = N.text_sprite('Fuente: Gobierno de El Salvador (2019–2025)', 26, (180, 200, 220, 255), pad=6)
    def draw(s, fr, t, d):
        blit(fr, s.scr, 540, 840, ss(0, .3, t))
        x0, x1, y0, y1 = 150, 930, 560, 1080; k = ss(s.w('tasa') - .2, s.w('97') - .1, t)
        for q in range(5): line(fr, (x0, y0 + q * (y1 - y0) / 4), (x1, y0 + q * (y1 - y0) / 4), (50, 90, 130), 1)
        pts = [(x0 + (y - 2019) / 6. * (x1 - x0), y1 - v / 40. * (y1 - y0)) for y, v in s.vals]
        n = 1 + k * (len(pts) - 1); full = int(n); part = n - full
        seg = pts[:full] + ([tuple(A(*pts[full - 1]) + (A(*pts[full]) - A(*pts[full - 1])) * part)] if full < len(pts) else [])
        if len(seg) > 1: pline(fr, seg, (40, 90, 60), 14); pline(fr, seg, (120, 255, 170), 6)
        for (y, v), p in zip(s.vals, pts): blit(fr, s.lbl[y], p[0], y1 + 40)
        blit(fr, s.v0, pts[0][0] + 50, pts[0][1] - 40);
        if k > .98: blit(fr, s.v1, pts[-1][0] - 20, pts[-1][1] - 50)
        g = ss(s.w('97') - .1, s.w('97') + .4, t); blit(fr, s.big, 540, 1230, g, lerp(1.4, 1, eOut(g))); blit(fr, s.src, 540, 1340, g)

class Price(Sb):                                   # más de 90 mil detenidos
    def __init__(s):
        bg = vgrad([(0, (18, 18, 22)), (1, (40, 40, 46))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(800, (70, 72, 76), (84, 86, 90))
        s.front = [(bokeh_layer(8, (255, 230, 200), 311, ymin=200, ymax=700), 1.7)]
        s.cnt = [N.text_sprite(f'+{n:,}', 120, (255, 236, 170, 255), glow=(255, 160, 40), glow_r=16) for n in range(0, 90001, 3000)]
        s.lab = N.text_sprite('PERSONAS DETENIDAS', 44, (255, 255, 255, 255), stroke=4, stroke_col=(0, 0, 0, 230), spacing=4)
        s.src = N.text_sprite('Más de 93,000 según el registro oficial (2026)', 26, (210, 210, 220, 255), pad=6)
    def draw(s, fr, t, d):
        seated_rows(fr, 80, 900, 7, 10, 104, 120, .9, t, upto=ss(.2, d * .8, t))
        n = int(min(len(s.cnt) - 1, ss(.1, d * .7, t) * (len(s.cnt) - 1)))
        cv2.rectangle(fr, (0, 240), (W, 700), (14, 14, 18), -1)
        blit(fr, s.cnt[n], 540, 400); blit(fr, s.lab, 540, 540); blit(fr, s.src, 540, 630, ss(1, 1.5, t))

class Protest(Sb):                                 # miles de denuncias por abusos
    def __init__(s):
        sky = vgrad([(0, (40, 46, 60)), (1, (80, 84, 96))]); s.back = [(dof(opaque(sky), 2), .1)]
        b_, s.main = night_street(8, col=(60, 60, 70)); s.back.append(b_[1])
        s.front = [(bokeh_layer(8, (255, 255, 230), 312, ymin=200, ymax=1200), 1.7)]
        s.panel = red_panel('MILES DE DENUNCIAS', w=800, h=160)
        s.signs = [N.text_sprite(x, 30, (30, 30, 34, 255), pad=6, maxw=180) for x in ('INOCENTE', 'DEBIDO PROCESO', '¿DÓNDE ESTÁ?', 'JUSTICIA')]
        s.tags = [chip('DETENCIONES ARBITRARIAS', (255, 120, 100)), chip('ABUSOS', (255, 120, 100)), chip('DEBIDO PROCESO', (255, 120, 100))]
    def draw(s, fr, t, d):
        for i, x in enumerate((110, 355, 600, 835)):                         # familiares con fotos y pancartas
            fy = 1650 + (i % 2) * 40; up = .5 + .5 * math.sin(t * 3 + i)
            sx, sy = x + 95, fy - 640 - 20 * up                                  # la pancarta va a un lado; una mano sostiene el palo
            cv2.line(fr, (int(sx), int(sy)), (int(sx), int(fy - 180)), (120, 90, 60), 8)
            character(fr, ['civil', 'dama', 'traje', 'civil'][i], x, fy, 430, t + i, armR=('apunta', (sx, fy - 330 - 20 * up), 1.), armL=('reposo',),
                      look=(.15, -.3), frown=-.3, who=['vecino', 'vecina', 'ejecutivo', 'pandillero'][i])
            cv2.rectangle(fr, (int(sx - 100), int(sy - 70)), (int(sx + 100), int(sy + 60)), (240, 236, 226), -1); blit(fr, s.signs[i], sx, sy - 5)
        for i, tg in enumerate(s.tags):
            if t > .6 + i * .5: float_in(fr, tg, [270, 810, 540][i], [560, 560, 700][i], t, .6 + i * .5)
        float_in(fr, s.panel, 540, 330, t, .2)

# ================================================================ ¿Y SI MÉXICO LO INTENTARA?
class States5(D.S3D, Sb):                          # operativos simultáneos en cinco estados
    a = 0.
    def __init__(s):
        D.S3D.__init__(s); s.st = [('sinaloa', 'SINALOA', (-107.5, 25.0)), ('michoacán', 'MICHOACÁN', (-101.9, 19.2)), ('jalisco', 'JALISCO', (-103.6, 20.6)),
                                   ('guerrero', 'GUERRERO', (-99.9, 17.6)), ('guanajuato', 'GUANAJUATO', (-101.2, 21.0))]
        s.lbl = {k: N.text_sprite(n, 30, (255, 236, 200, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=4) for k, n, _ in s.st}
        s.title = gold_panel('¿Y SI MÉXICO LO INTENTARA?', None, w=900, h=150); s.title2 = red_panel('OPERATIVOS SIMULTÁNEOS', w=860, h=150)
    def draw(s, fr, t, d):
        for i, (k, n, p) in enumerate(s.st):
            try: t0 = s.w(k)
            except KeyError: t0 = 99
            g = ss(t0 - .1, t0 + .3, t)
            if g <= 0: continue
            x, y = prj(*p); blit(fr, glow_sprite(90, (255, 60, 40)), x, y, g * (.5 + .4 * math.sin(t * 6 + i)), add=True); circ(fr, (x, y), 10, (255, 230, 220))
            f = (t * .9 + i * .2) % 1; cv2.circle(fr, (int(x), int(y)), int(16 + f * 80), (int(255 * (1 - f)), int(60 * (1 - f)), 40), 3, cv2.LINE_AA)
            blit(fr, s.lbl[k], x, y - 44, g)
    def floating(s, fr, t, d, P):
        k2 = s.w('operativos') if True else 0
        if t < k2 - .2: float_in(fr, s.title, 540, 330, t, .2)
        else: float_in(fr, s.title2, 540, 330, t, k2 - .2)
        s.dust.draw(fr, t)
    def cam(s, t, d): k = eIO(t / d); return lerp(1.35, 1.55, k), 470, 1150, lerp(-30, 30, k), 0

class Targets(Sb):                                 # miles de objetivos identificados
    def __init__(s):
        bg = vgrad([(0, (4, 10, 18)), (1, (10, 20, 34))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (120, 200, 255), 313, ymin=200, ymax=1700), 1.7)]
        s.panel = blue_panel('MILES DE OBJETIVOS', 'IDENTIFICADOS', w=760, h=170); s.mark = N.text_sprite('✕', 60, (255, 70, 60, 255), pad=4)
    def draw(s, fr, t, d):
        for r in range(5):
            for c in range(4):
                i = r * 4 + c; x = 170 + c * 250; y = 620 + r * 230; g = ss(.1 + i * .05, .3 + i * .05, t)
                if g <= 0: continue
                cv2.rectangle(fr, (x - 100, y - 100), (x + 100, y + 100), (20, 60, 90), -1); cv2.rectangle(fr, (x - 100, y - 100), (x + 100, y + 100), (120, 230, 255), 3)
                cv2.circle(fr, (x, y - 20), 40, (40, 50, 60), -1); cv2.ellipse(fr, (x, y + 70), (60, 40), 0, 180, 360, (40, 50, 60), -1)
                if (i * 7) % 3 == 0 and t > 1.2 + i * .04: blit(fr, s.mark, x, y - 10, .9)
        scan = 600 + ((t * 500) % 1200); line(fr, (60, scan), (1020, scan), (120, 230, 255), 3)
        float_in(fr, s.panel, 540, 330, t, .2)

class Frozen(Sb):                                  # bloqueos financieros
    def __init__(s):
        bg = vgrad([(0, (10, 14, 20)), (1, (24, 30, 40))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1500, (40, 44, 52), (54, 58, 66))
        s.front = [(bokeh_layer(10, (180, 230, 255), 314, ymin=200, ymax=1400), 1.7)]
        s.stamp = N.stamp('CUENTAS CONGELADAS', (90, 200, 255), w=860, h=124, px=66, fill=(10, 40, 60, 200))
        s.bill = np.zeros((90, 200, 4), np.uint8); cv2.rectangle(s.bill, (2, 2), (197, 87), (90, 170, 100, 255), -1); cv2.rectangle(s.bill, (14, 12), (185, 77), (50, 110, 60, 255), 3); cv2.circle(s.bill, (100, 45), 22, (190, 230, 190, 255), -1)
    def draw(s, fr, t, d):
        cx, cy = 540, 1100; cv2.circle(fr, (cx, cy), 330, (120, 124, 132), -1); cv2.circle(fr, (cx, cy), 300, (90, 94, 102), -1)    # bóveda
        for k in range(8): a_ = k * math.pi / 4 + t * .2 * (1 - ss(1, 1.6, t)); line(fr, (cx, cy), (cx + math.cos(a_) * 220, cy + math.sin(a_) * 220), (150, 154, 162), 16)
        cv2.circle(fr, (cx, cy), 60, (180, 184, 192), -1)
        for i in range(9):
            x = 160 + (i % 3) * 380; y = 600 + (i // 3) * 620; blit(fr, s.bill, x, y + math.sin(t * 2 + i) * 6 * (1 - ss(1, 1.4, t)), 1, .9)
            ice = ss(.15 + i * .04, .5 + i * .04, t)
            if ice > 0: ov = fr.copy(); cv2.rectangle(ov, (int(x - 110), int(y - 55)), (int(x + 110), int(y + 55)), (170, 220, 255), -1); fr[:] = cv2.addWeighted(fr, 1 - .45 * ice, ov, .45 * ice, 0)
        stamp_in(fr, s.stamp, 540, 400, t, .25)

class Capture(Sb):                                 # captura de líderes
    def __init__(s):
        s.back, s.main = night_street(10); s.front = [(bokeh_layer(10, (255, 200, 140), 315, ymin=200, ymax=1200), 1.7)]
        s.stamp = N.stamp('LÍDER CAPTURADO', (70, 230, 120), w=760, px=72, fill=(6, 40, 16, 200))
    def draw(s, fr, t, d):
        CH.heli(fr, 760, 520, 1.3, t, col=(70, 78, 70)); fbeam(fr, (760, 570), (520, 1500), 20, 220, (230, 240, 255), .16, 30)
        cv2.ellipse(fr, (520, 1652), (170, 22), 0, 0, 360, (14, 14, 16), -1, cv2.LINE_AA)
        character(fr, 'civil', 520, 1650, 480, t, armR=('apunta', (560, 1450), .75), armL=('apunta', (480, 1450), .75), look=(0, .2), frown=.5, cuffs=True)
        for i, (x, sd) in enumerate(((240, 1), (820, -1))):
            hs = character(fr, 'militar', x, 1680, 460, t + i, armR=('apunta', (x + sd * 250, 1400), .8), armL=('apunta', (x + sd * 250, 1400), .45), look=(.5 * sd, 0), frown=.4)
            lib.rifle(fr, hs, 460 / 8.)
        stamp_in(fr, s.stamp, 540, 420, t, .3)

class Recover(DT.Territory, Sb):                   # recuperación de territorios
    a = 0.
    def __init__(s):
        DT.Territory.__init__(s); s.tri = gold_panel('TERRITORIOS RECUPERADOS', None, w=820, h=150)
        s.zones = [(-107.4, 24.8), (-101.9, 19.2), (-103.4, 20.7), (-99.9, 17.6), (-101.2, 21.0), (-106.1, 28.6), (-98.3, 26.1)]
    def draw(s, fr, t, d):
        for i, p in enumerate(s.zones):
            x, y = prj(*p); k = ss(.4 + i * .25, .9 + i * .25, t)
            col = tuple(int(lerp(a_, b_, k)) for a_, b_ in zip((255, 50, 40), (60, 230, 120)))
            ov = fr.copy(); cv2.circle(ov, (int(x), int(y)), 50, col, -1, cv2.LINE_AA); fr[:] = cv2.addWeighted(fr, .5, ov, .5, 0); circ(fr, (x, y), 8, (255, 255, 240))
    def floating(s, fr, t, d, P): float_in(fr, s.tri, 540, 330, t, .2); s.dust.draw(fr, t)
    def cam(s, t, d): k = eIO(t / d); return lerp(1.3, 1.45, k), 460, 1150, 0, 0

class Headlines(Sb):                               # golpes importantes los primeros meses
    def __init__(s):
        bg = vgrad([(0, (20, 18, 16)), (1, (40, 34, 28))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(8, (255, 230, 200), 316, ymin=200, ymax=1700), 1.7)]
        s.papers = []
        for t1, t2 in (('GOLPE HISTÓRICO AL NARCO', 'Caen cabecillas en cinco estados'), ('DESMANTELAN LABORATORIOS', 'Operativo conjunto de fuerzas federales'), ('BAJAN LOS HOMICIDIOS', 'Primer mes de la estrategia (escenario)')):
            pp = np.zeros((520, 760, 4), np.uint8); im = Image.fromarray(pp); dd = ImageDraw.Draw(im); dd.rectangle((0, 0, 759, 519), fill=(236, 230, 214, 255)); pp = np.array(im)
            over(pp, N.text_sprite('EL DIARIO', 40, (40, 36, 30, 255), pad=6, spacing=8), 380, 50); cv2.line(pp, (30, 90), (730, 90), (40, 36, 30, 255), 3)
            over(pp, N.text_sprite(t1, 52, (20, 18, 16, 255), pad=6, maxw=700), 380, 170); over(pp, N.text_sprite(t2, 28, (70, 64, 56, 255), pad=6, maxw=700), 380, 250)
            for k in range(6): cv2.line(pp, (40, 310 + k * 30), (720 - (k * 47) % 200, 310 + k * 30), (150, 144, 130, 255), 6)
            s.papers.append(pp)
        s.hip = N.text_sprite('ESCENARIO HIPOTÉTICO', 30, (255, 230, 170, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=6)
    def draw(s, fr, t, d):
        for i, pp in enumerate(s.papers):
            k = ss(.2 + i * .9, .7 + i * .9, t)
            if k <= 0: continue
            M = cv2.getRotationMatrix2D((380, 260), (1 - k) * 540 + (i - 1) * 6, lerp(.2, 1, eOut(k)))
            r = cv2.warpAffine(pp, M, (760, 520)); blit(fr, r, 540 + (i - 1) * 40, 900 + i * 120)
        blit(fr, s.hip, 540, 300, ss(.2, .6, t))

class TwoEnemies(Sb):                              # no es el mismo enemigo
    def __init__(s):
        bg = np.zeros((H, W, 3), np.float32); bg[:, :540] = (14, 24, 54); bg[:, 540:] = (40, 14, 14)
        s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1600, (20, 20, 26), (34, 34, 40)); s.front = [(bokeh_layer(10, (255, 230, 200), 317, ymin=200, ymax=1500), 1.7)]
        s.panel = red_panel('NO ES EL MISMO ENEMIGO', w=880, h=160)
        s.l1 = N.text_sprite('PANDILLAS', 44, (200, 220, 255, 255), spacing=6, stroke=3, stroke_col=(0, 0, 0, 220)); s.l2 = N.text_sprite('CÁRTELES', 44, (255, 200, 190, 255), spacing=6, stroke=3, stroke_col=(0, 0, 0, 220))
    def draw(s, fr, t, d):
        line(fr, (540, 480), (540, 1700), (255, 255, 255), 3)
        character(fr, 'civil', 270, 1620, 480, t, armR=('jarra',), armL=('jarra',), look=(.2, 0), frown=.5, cap=True)
        for k in range(3): line(fr, (200 + k * 30, 1180), (210 + k * 30, 1230), (30, 30, 40), 4)            # tatuajes estilizados en la cara
        character(fr, 'elegante', 810, 1620, 500, t, armR=('palma',), armL=('jarra',), look=(-.2, 0), frown=.2, smile=.3)
        for k in range(6):                                                    # red internacional detrás del jefe
            a_ = k * math.pi / 3 + t * .3; p = (810 + math.cos(a_) * 230, 820 + math.sin(a_) * 120); line(fr, (810, 820), p, (255, 120, 100), 2); circ(fr, p, 12, (255, 160, 140))
        blit(fr, s.l1, 270, 1700); blit(fr, s.l2, 810, 1700)
        float_in(fr, s.panel, 540, 330, t, .3)

# ================================================================ LA GRAN DIFERENCIA
class Extortion(Sb):                               # las pandillas: control de barrios por extorsión
    def __init__(s):
        s.back, s.main = night_street(11, col=(50, 44, 40)); s.front = [(bokeh_layer(10, (255, 200, 140), 318, ymin=200, ymax=1200), 1.7)]
        s.panel = red_panel('EXTORSIÓN', w=600, h=160)
        s.env = np.zeros((70, 120, 4), np.uint8); cv2.rectangle(s.env, (2, 2), (117, 67), (230, 220, 190, 255), -1); cv2.line(s.env, (2, 2), (60, 40), (190, 180, 150, 255), 3); cv2.line(s.env, (117, 2), (60, 40), (190, 180, 150, 255), 3)
        s.shop = N.text_sprite('TIENDA', 40, (255, 230, 180, 255), pad=6, spacing=6)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (560, 900), (1040, 1280), (90, 60, 40), -1); cv2.rectangle(fr, (600, 980), (1000, 1280), (255, 214, 150), -1); blit(fr, s.shop, 800, 940)
        character(fr, 'traje', 800, 1600, 440, t, armR=('apunta', (600, 1380), ss(.3, 1.0, t) * .9), armL=('reposo',), look=(-.5, 0), frown=-.4)   # el comerciante paga
        for i, x in enumerate((300, 120)):
            character(fr, 'civil', x, 1620 + i * 20, 460, t + i, armR=('apunta', (560, 1400), .7 if i == 0 else .2), armL=('jarra',), look=(.5, 0), frown=.6, cap=True)
        u = ss(.6, 1.6, t); blit(fr, s.env, lerp(700, 480, u), lerp(1380, 1390, u), 1, 1)
        float_in(fr, s.panel, 540, 330, t, .2)

class Network2(Sb):                                # los cárteles: redes internacionales
    def __init__(s):
        bg = vgrad([(0, (4, 8, 18)), (1, (10, 16, 30))]); i8 = to8(bg); s.P = mini_map(i8, 40, 480, 1000, 900, col=(255, 80, 60), others=(30, 50, 80))
        s.back = [(dof(opaque(i8.astype(np.float32)), 1.2), .3)]; s.main = np.zeros((H, W, 4), np.uint8); s.front = [(bokeh_layer(10, (255, 120, 100), 319, ymin=200, ymax=1700), 1.7)]
        s.words = [('tráfico', 'TRÁFICO DE DROGAS'), ('lavado', 'LAVADO DE DINERO'), ('corrupción', 'CORRUPCIÓN'), ('empresas', 'EMPRESAS FACHADA'), ('laboratorios', 'LABORATORIOS'), ('conexiones', 'CONEXIONES GLOBALES')]
        s.chips = {k: chip(v) for k, v in s.words}
    def draw(s, fr, t, d):
        src = A(*s.P(np.array([[-102.5, 23.5]]))[0])
        for i, dst in enumerate([(-87.6, 41.9), (-118.2, 34.0), (-74.0, 40.7), (-83, 49), (-90, 15), (-80, 25)]):   # rutas hacia el norte y el sur
            p1 = A(*s.P(np.array([dst]))[0]); k = ss(.2 + i * .15, .9 + i * .15, t)
            if k <= 0: continue
            mid = (src + p1) / 2 + A(0, -120); pts = [tuple((1 - u) ** 2 * src + 2 * (1 - u) * u * mid + u ** 2 * p1) for u in np.linspace(0, k, 30)]
            pline(fr, pts, (110, 40, 30), 10); pline(fr, pts, (255, 110, 80), 4)
        for i, (k, _) in enumerate(s.words):
            try: tk = s.w(k)
            except KeyError: tk = 1 + i * .5
            if t > tk - .1: float_in(fr, s.chips[k], [270, 810][i % 2], 330 + (i // 2) * 110, t, tk - .1)

class Boss(Sb):                                    # capturar a un jefe no destruye la organización
    def __init__(s):
        bg = vgrad([(0, (6, 6, 12)), (1, (18, 10, 16))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 90, 70), 320, ymin=200, ymax=1700), 1.7)]
        s.boss = (540, 700); s.mid = [(160 + i * 190, 980) for i in range(5)]; s.low = [(90 + i * 112, 1260 + (i % 2) * 60) for i in range(9)]
        s.ml = [(i, j) for i in range(5) for j in range(9) if abs(s.mid[i][0] - s.low[j][0]) < 230]
        s.panel = N.holo_panel(900, 150, 'EL JEFE CAE, LA RED SIGUE', None, col=(255, 90, 70), fill=(50, 8, 8, 190)); s.crown = emoji_sprite('👑')
    def node(s, fr, p, r, op=1.):
        blit(fr, glow_sprite(int(r * 1.8), (255, 70, 50)), *p, .5 * op, add=True); circ(fr, p, r, dark((255, 70, 50), .5 + .5 * op)); circ(fr, p, r - 6, tuple(int(c * (.3 + .7 * op)) for c in SKIN))
    def draw(s, fr, t, d):
        gone = ss(.8, 1.5, t); new = ss(1.4, 2.2, t)
        for i, j in s.ml: line(fr, s.mid[i], s.low[j], (150, 50, 44), 3)
        for i in range(4): line(fr, s.mid[i], s.mid[i + 1], (255, 120, 90), max(1, 4 * new))
        for m in s.mid: line(fr, s.boss, m, (int(150 * (1 - gone)), 50, 44), max(1, int(4 * (1 - gone))))
        for p in s.low: s.node(fr, p, 26, .8)
        for p in s.mid: s.node(fr, p, 40, 1.)
        s.node(fr, s.boss, 62, 1 - gone); blit(fr, s.crown, s.boss[0], s.boss[1] - 90, 1 - gone, .7)
        if gone > 0: k = gone; line(fr, (s.boss[0] - 70 * k, s.boss[1] - 70 * k), (s.boss[0] + 70 * k, s.boss[1] + 70 * k), (255, 40, 30), 14); line(fr, (s.boss[0] + 70 * k, s.boss[1] - 70 * k), (s.boss[0] - 70 * k, s.boss[1] + 70 * k), (255, 40, 30), 14)
        float_in(fr, s.panel, 540, 330, t, .3)

class InnerWar(TR.Fragment, Sb):                   # guerra interna por el negocio
    a = 0.
    def __init__(s): TR.Fragment.__init__(s); s.title = red_panel('GUERRA INTERNA', w=680, h=170); s.lb = N.text_sprite('POR EL CONTROL DEL NEGOCIO', 34, (255, 230, 200, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=5)

class Displaced(Sb):                               # más violencia y desplazamientos
    def __init__(s):
        s.back, s.main = night_street(12, col=(44, 30, 28)); s.front = [(bokeh_layer(16, (255, 120, 40), 321, rmin=10, rmax=40, ymin=200, ymax=1800), 1.7)]
        s.panel = red_panel('DESPLAZAMIENTOS', w=720, h=160); s.puff = glow_sprite(130, (96, 84, 82)); s.flame = glow_sprite(70, (255, 140, 40))
    def draw(s, fr, t, d):
        for i in range(12): f = (i / 12. + t * .07) % 1; blit(fr, s.puff, 80 + (i % 6) * 190 + f * 80, 1250 - f * 800, min(1, f * 5) * (1 - f) * .5, 1 + f * 2.4)
        for q in range(5): fl = .7 + .3 * math.sin(t * 13 + q); blit(fr, s.flame, 120 + q * 200, 1250, fl * .8, 2 + .5 * fl, add=True)
        for i, (x0, kind, h, kw) in enumerate([(820, 'dama', 440, dict(hair='coleta')), (960, 'traje', 470, {}), (1100, 'civil', 300, {}), (700, 'civil', 450, dict(cap=True))]):   # familias que huyen con sus cosas
            x = x0 - 120 * t
            hs = character(fr, kind, x, 1680 + (i % 2) * 30, h, t + i * .7, armR=('reposo',), armL=('apunta', (x - 60, 1400), .3), look=(-.6, 0), frown=-.3, run=4, **kw)
            hx_, hy_ = hs[1][0]; cv2.line(fr, (int(hx_), int(hy_)), (int(hx_), int(hy_ + 18)), (60, 40, 26), 5); cv2.rectangle(fr, (int(hx_ - 42), int(hy_ + 16)), (int(hx_ + 42), int(hy_ + 86)), (120, 80, 50), -1); cv2.rectangle(fr, (int(hx_ - 42), int(hy_ + 16)), (int(hx_ + 42), int(hy_ + 86)), (80, 52, 32), 3)   # maleta
        float_in(fr, s.panel, 540, 330, t, .2)

# ================================================================ EL DILEMA
class NoEvidence(Sb):                              # detenciones masivas sin pruebas suficientes
    def __init__(s):
        s.back, s.main = night_street(13); s.front = [(bokeh_layer(10, (255, 90, 70), 322, ymin=200, ymax=1500), 1.7)]
        s.folder = np.zeros((260, 360, 4), np.uint8); cv2.rectangle(s.folder, (4, 30), (355, 255), (200, 170, 110, 255), -1); cv2.rectangle(s.folder, (4, 4), (150, 40), (200, 170, 110, 255), -1)
        over(s.folder, N.text_sprite('EXPEDIENTE', 32, (90, 60, 30, 255), pad=4, spacing=4), 180, 90)
        s.stamp = N.stamp('SIN PRUEBAS', (255, 59, 42), w=620, px=80)
    def draw(s, fr, t, d):
        on = (t * 2.4) % 1 < .5; blit(fr, glow_sprite(300, (255, 40, 40) if on else (40, 90, 255)), 540, 1150, .22, add=True)
        for i, (x, kind, kw) in enumerate([(220, 'bata', {}), (520, 'civil', dict(cap=True)), (820, 'dama', dict(hair='coleta'))]):   # civiles comunes detenidos
            character(fr, kind, x, 1660, 420, t + i, armR=('apunta', (x + 30, 1470), .7), armL=('apunta', (x - 30, 1470), .7), look=(0, -.2), frown=-.5, cuffs=True, **kw)
            hs = character(fr, 'militar', x + 110, 1690, 440, t + i, armR=('apunta', (x + 20, 1420), .8), armL=('reposo',), look=(-.5, 0), frown=.35)
        blit(fr, s.folder, 540, 560, ss(.2, .5, t))
        stamp_in(fr, s.stamp, 540, 580, t, 1.0)

class Reports(Sb):                                 # documentado por organizaciones de derechos humanos
    def __init__(s):
        bg = vgrad([(0, (12, 12, 16)), (1, (30, 28, 30))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1500, (60, 46, 36), (74, 58, 46))
        s.front = [(bokeh_layer(8, (255, 230, 200), 323, ymin=200, ymax=1400), 1.7)]
        s.doc = np.zeros((300, 230, 4), np.uint8); cv2.rectangle(s.doc, (2, 2), (227, 297), (240, 236, 226, 255), -1)
        for k in range(9): cv2.line(s.doc, (20, 40 + k * 26), (210 - (k * 37) % 60, 40 + k * 26), (130, 130, 140, 255), 4)
        cv2.circle(s.doc, (180, 260), 24, (200, 40, 40, 255), -1)
        s.panel = gold_panel('DERECHOS HUMANOS', 'MÁS DE 6,400 DENUNCIAS DOCUMENTADAS', w=900, h=170)
        s.stamp = N.stamp('DETENCIONES ARBITRARIAS', (255, 59, 42), w=920, h=124, px=58)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (160, 1260), (920, 1300), (110, 74, 46), -1); cv2.rectangle(fr, (190, 1300), (890, 1520), (80, 52, 32), -1)
        for i in range(14):
            k = ss(.1 + i * .1, .4 + i * .1, t)
            if k > 0: blit(fr, s.doc, 540 + ((i * 37) % 200 - 100), lerp(-200, 1200 - i * 14, eOut(k)), 1, .9)
        float_in(fr, s.panel, 540, 330, t, .2); stamp_in(fr, s.stamp, 540, 560, t, 1.8)

class Innocents(Sb):                               # inocentes encarcelados; líderes intactos
    def __init__(s):
        bg = np.zeros((H, W, 3), np.float32); bg[:, :540] = (30, 30, 36); bg[:, 540:] = (60, 44, 30); radial(bg, (810, 900), 400, (255, 200, 120), .25)
        s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1600, (40, 36, 34), (54, 50, 46)); s.front = [(bokeh_layer(10, (255, 220, 160), 324, ymin=200, ymax=1500), 1.7)]
        s.l1 = red_panel('INOCENTES PRESOS', w=480, h=140); s.l2 = gold_panel('LÍDERES INTACTOS', None, w=480, h=140)
        s.inst = N.text_sprite('INSTITUCIONES', 30, (230, 220, 200, 255), pad=6, spacing=4)
    def draw(s, fr, t, d):
        character(fr, 'civil', 270, 1620, 480, t, armR=('apunta', (300, 1300), .6), armL=('apunta', (240, 1300), .6), look=(0, .3), frown=-.6)
        bars(fr, 40, 520, 760, 1640)
        # el jefe, tranquilo en su terraza con un vaso
        cv2.rectangle(fr, (640, 1300), (1020, 1340), (120, 80, 50), -1)
        character(fr, 'elegante', 830, 1620, 500, t, armR=('apunta', (900, 1100), .8), armL=('jarra',), look=(-.2, 0), frown=-.1, smile=.6)
        poly(fr, [(915, 1060), (945, 1060), (940, 1110), (920, 1110)], (190, 220, 240))
        k = ss(2.0, 3.0, t)                                                       # columnas de las instituciones que se agrietan
        for i, x in enumerate((640, 760, 880, 1000)):
            cv2.rectangle(fr, (x - 20, 700), (x + 20, 1000), (200, 196, 186), -1)
            if k > 0: pline(fr, [(x, 700), (x - 12, 780), (x + 10, 860), (x - 8, 940 * 1 + 0)][:max(2, int(4 * k))], (60, 50, 50), 4)
        cv2.rectangle(fr, (600, 660), (1040, 700), (210, 206, 196), -1); blit(fr, s.inst, 820, 640)
        float_in(fr, s.l1, 280, 340, t, .2); float_in(fr, s.l2, 800, 500, t, .6)

# ================================================================ CIERRE
class HardHand(Sb):                                # ¿mano dura?
    def __init__(s):
        bg = vgrad([(0, (20, 6, 6)), (1, (50, 14, 12))]); radial(bg, (540, 900), 600, (255, 60, 40), .3); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (255, 120, 90), 325, ymin=200, ymax=1700), 1.7)]
        s.q = N.text_sprite('¿MANO DURA?', 130, (255, 236, 220, 255), glow=(255, 60, 40), glow_r=18)
    def draw(s, fr, t, d):
        hit = ss(.5, .8, t); y = lerp(600, 1150, eOut(hit))
        cv2.rectangle(fr, (420, int(y) - 260), (660, int(y) + 60), (190, 60, 50), -1)                       # manga
        circ(fr, (540, y + 120), 150, (170, 172, 182)); circ(fr, (540, y + 120), 140, SKIN)               # puño
        for k in range(4): line(fr, (440 + k * 50, y + 60), (440 + k * 50, y + 140), (200, 200, 206), 6)
        if hit > .95:
            for k in range(10): a_ = k * math.pi / 5; line(fr, (540 + math.cos(a_) * 200, 1420 + math.sin(a_) * 60), (540 + math.cos(a_) * 320, 1420 + math.sin(a_) * 100), (255, 200, 120), 6)
        blit(fr, s.q, 540, 420, ss(.1, .5, t), lerp(1.4, 1, ss(.1, .5, t)))

class DeepStrategy(Sb):                            # destruir el dinero, las armas, la corrupción y el poder territorial
    def __init__(s):
        bg = vgrad([(0, (6, 12, 22)), (1, (14, 24, 40))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = np.zeros((H, W, 4), np.uint8)
        s.front = [(bokeh_layer(10, (120, 200, 255), 326, ymin=200, ymax=1700), 1.7)]
        s.panel = blue_panel('¿UNA ESTRATEGIA', 'MÁS PROFUNDA?', w=760, h=180)
        s.items = [('dinero', '💰', 'DINERO'), ('armas', '🔫', 'ARMAS'), ('redes', '🕸️', 'CORRUPCIÓN'), ('poder', '🗺️', 'TERRITORIO')]
        s.spr = {k: (emoji_sprite(e), N.text_sprite(n, 38, (255, 255, 255, 255), stroke=4, stroke_col=(0, 0, 0, 220), spacing=4)) for k, e, n in s.items}
    def draw(s, fr, t, d):
        for i, (k, _, _) in enumerate(s.items):
            try: tk = s.w(k)
            except KeyError: tk = .6 + i * .6
            x, y = [300, 780][i % 2], [800, 1250][i // 2]; g = ss(tk - .1, tk + .3, t)
            if g <= 0: continue
            cv2.circle(fr, (x, y), 170, (20, 50, 80), -1); cv2.circle(fr, (x, y), 170, (120, 230, 255), 4)
            e, n = s.spr[k]; blit(fr, e, x, y - 20, g, .8); blit(fr, n, x, y + 120, g)
            c = ss(tk + .4, tk + .7, t)
            if c > 0: line(fr, (x - 120 * c, y - 120 * c), (x + 120 * c, y + 120 * c), (255, 60, 50), 14)
        float_in(fr, s.panel, 540, 340, t, .2)

class Doors(Sb):                                   # capturar a miles puede ser el comienzo…
    def __init__(s):
        bg = vgrad([(0, (16, 16, 20)), (1, (34, 34, 40))]); s.back = [(dof(opaque(bg), 2), .2)]; s.main = floor_layer(1550, (50, 50, 56), (64, 64, 70))
        s.front = [(bokeh_layer(8, (255, 230, 200), 327, ymin=200, ymax=1400), 1.7)]
        s.l = N.text_sprite('EL COMIENZO…', 80, (255, 255, 255, 255), stroke=6, stroke_col=(0, 0, 0, 230), spacing=6)
    def draw(s, fr, t, d):
        seated_rows(fr, 120, 1000, 4, 9, 105, 130, .8, t)
        k = ss(.4, 1.6, t); bars(fr, 0, W, 700, 1560, k=1.0, step=70) if k > .99 else bars(fr, 0, W * k, 700, 1560, step=70)
        blit(fr, s.l, 540, 420, ss(.8, 1.3, t))

class Empire(DT.Chess, Sb):                        # desmantelar un imperio criminal es otra historia
    a = 0.
    def __init__(s): DT.Chess.__init__(s); s.panel = red_panel('OTRA HISTORIA', w=640, h=160)

class Close(TR.Close, Sb):
    a = 0.
    def __init__(s): TR.Close.__init__(s); s.cta = N.holo_panel(660, 200, '¿SÍ o NO?', 'COMENTA ABAJO')

# ================================================================ línea de tiempo
def tl():
    seq = [
        (0, MexWar(), 0), (T('miles') - .25, Soldiers(), 0), (T('cárceles') - .25, PrisonFill(), 0), (T('podría') - .3, BukeleQ(), 0),
        (SC_T[1], March2022(), 1), (T('bukele', 15) - .25, Decree(), 1), (T('detenciones') - .25, Arrests(), 1), (T('operaciones') - .25, Ops(), 1),
        (T('suspensión') - .25, Constitution(), 1), (T('construcción') - .25, Cecot(), 1), (T('resultado') - .3, Chart97(), 1), (T('pero') - .25, Price(), 1),
        (T('miles', 43) - .25, Protest(), 1),
        (SC_T[2], States5(), 2), (T('miles', 55) - .25, Targets(), 2), (T('bloqueos') - .25, Frozen(), 2), (T('captura') - .25, Capture(), 2),
        (T('recuperación') - .25, Recover(), 2), (T('durante') - .25, Headlines(), 2), (T('pero', 62) - .25, TwoEnemies(), 2),
        (SC_T[3], Extortion(), 3), (T('los', T('violencia', 74)) - .25, Network2(), 3), (T('capturar', 85) - .25, Boss(), 3), (T('veces') - .4, InnerWar(), 3),
        (T('eso', 93) - .4, Displaced(), 3),
        (SC_T[4], NoEvidence(), 4), (T('organizaciones', 106) - .4, Reports(), 4), (T('méxico', 112) - .4, Innocents(), 4),
        (SC_T[5], HardHand(), 0), (T('o', 123.5) - .2, DeepStrategy(), 2), (T('porque', 128) - .25, Doors(), 4), (T('desmantelar') - .4, Empire(), 3),
        (T('tú') - .3, Close(), 4),
    ]
    out = []
    for i, (a, sc, g) in enumerate(seq):
        b = seq[i + 1][0] if i + 1 < len(seq) else DUR; sc.a = a; out.append((a, b, sc, g))
    return out

KEYW = {'méxico', 'guerra', 'total', 'cárteles', 'soldados', 'cárceles', 'bukele', 'salvador', '2022', 'asesinatos', 'excepción', 'detenciones', 'masivas', 'militares',
        'garantías', 'megacárcel', 'cecot', 'homicidios', '97%', 'oficiales', 'precio', '90', 'abusos', 'arbitrarias', 'sinaloa', 'michoacán', 'jalisco', 'guerrero',
        'guanajuato', 'objetivos', 'financieros', 'líderes', 'territorios', 'enemigo', 'pandillas', 'extorsión', 'internacionales', 'lavado', 'corrupción', 'fachada',
        'laboratorios', 'jefe', 'guerra', 'violencia', 'desplazamientos', 'pruebas', 'inocentes', 'instituciones', 'intactos', 'dura', 'profunda', 'dinero', 'armas',
        'imperio', 'historia', 'sí', 'no'}
TR.KEY = KEYW

_s = CH._src.replace("secs = [(0, 'tension', 1), (9.9, 'misterio', 2), (24.1, 'tension', 2), (37.2, 'epico', 2), (50.2, 'tension', 1)]",
     f"secs = [(0, 'tension', 1), ({SC_T[1]:.2f}, 'epico', 2), ({SC_T[2]:.2f}, 'tension', 2), ({SC_T[3]:.2f}, 'misterio', 2), ({SC_T[4]:.2f}, 'tension', 2), ({SC_T[5]:.2f}, 'epico', 1)]")
_a = _s.index('    EF = ['); _b = _s.index(']]', _a) + 2
_ef = [[0, 'boom', .9], [.3, 'latido', .3]]
for (a_, b_, sc, g) in tl()[1:]: _ef += [[a_ - .25, 'whoosh', .32], [a_, 'impacto', .38]]
_ef += [[T('régimen'), 'impacto', .7], [T('97%'), 'riser', .25], [T('90'), 'impacto', .6], [T('bloqueos'), 'impacto', .6], [T('capturar', 85) + .8, 'impacto', .6],
        [T('sin', 103) , 'impacto', .6], [T('dura') - .1, 'boom', .6], [T('comenta', 135), 'ding', .3], [DUR - 3.4 + 2.8, 'ding', .25]]
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
    pill = DT.Blockade(None, cta=True); C0, C1 = T('ahora') - 1.5, T('operativos') + 2.5            # «dale like y sígueme» a mitad del video
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
            try: cv2.imwrite(f'{OUT}/b_{T_:05.1f}.jpg', cv2.resize(frame(T_), (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
            except Exception as e: print('ERROR', T_, repr(e)); traceback.print_exc(limit=-3)
    elif mode == 'seg':
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', f'{OUT}/seg_{f0:05d}.mp4'], stdin=subprocess.PIPE)
        for i in range(f0, f1): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('SEG', f0, f1, flush=True)
    elif mode == 'audio': synth_audio(f'{OUT}/audio.wav'); print('audio ok')

if __name__ == '__main__': main()
