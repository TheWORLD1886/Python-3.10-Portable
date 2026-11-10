#!/usr/bin/env python3
# Versión con más detalle: cada sección del guion se divide en 3–5 tomas que cambian con la voz.
import realista as RL
from realista import *

def opaque(img): return rgba(img, np.ones((H, W)))
def floor_layer(y0, col, line_col):
    fl = np.zeros((H, W, 3), np.uint8); fl[y0:] = col
    for j in range(1, 9): y = int(y0 + (H - y0) * (j / 8.) ** 1.7); cv2.line(fl, (0, y), (W, y), line_col, 2, cv2.LINE_AA)
    for k in range(-10, 11): cv2.line(fl, (540, y0), (540 + k * 230, H), line_col, 2, cv2.LINE_AA)
    al = np.zeros((H, W)); al[y0:] = 1; return rgba(fl, al)
def wood_wall(c1=(54, 30, 18), c2=(30, 16, 10)):
    img = vgrad([(0, c2), (.6, c1), (1, c2)]); i8 = to8(img)
    for x in range(0, W, 120): cv2.rectangle(i8, (x + 10, 120), (x + 110, 1150), dark(c1, .7), 3)
    return i8.astype(np.float32)
def flag_us(img, x, y, w=220, h=130):
    for k in range(7): cv2.rectangle(img, (x, y + int(k * h / 7)), (x + w, y + int((k + .5) * h / 7)), (190, 40, 50), -1)
    for k in range(7): cv2.rectangle(img, (x, y + int((k + .5) * h / 7)), (x + w, y + int((k + 1) * h / 7)), (236, 236, 236), -1)
    cv2.rectangle(img, (x, y), (x + int(w * .42), y + int(h * .54)), (40, 50, 110), -1)
def flag_mx(img, x, y, w=210, h=130):
    for k, c in enumerate([(0, 104, 71), (240, 240, 240), (206, 17, 38)]): cv2.rectangle(img, (x + k * w // 3, y), (x + (k + 1) * w // 3, y + h), c, -1)
    cv2.circle(img, (x + w // 2, y + h // 2), 14, (122, 82, 40), -1)
def gavel(fr, hand, ang, u):
    hd = A(*hand); v = A(math.cos(ang), math.sin(ang)); n = A(-v[1], v[0])
    line(fr, hd, hd + v * 2.2 * u, (110, 60, 26), .22 * u)
    c = hd + v * 2.2 * u; poly(fr, [tuple(c - n * .55 * u - v * .3 * u), tuple(c + n * .55 * u - v * .3 * u), tuple(c + n * .55 * u + v * .3 * u), tuple(c - n * .55 * u + v * .3 * u)], (90, 48, 20))
class Shot:
    stamp_at = .7
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.04, 1.12, k), 540, 1000, lerp(-45, 45, k), 0
    def put_stamp(s, fr, t, y=480):
        k = ss(s.stamp_at, s.stamp_at + .3, t)
        if k > 0 and getattr(s, 'stamp', None) is not None: blit(fr, s.stamp, 540, y, k, lerp(1.6, 1., eOut(k)))

# ---------------------------------------------------------------- corte federal (aprobada / rechazada)
class Court(Shot):
    def __init__(s, text, col, gavel_t=.5, mx=False):
        wf = wood_wall(); i8 = to8(wf)
        (flag_mx if mx else flag_us)(i8, 140, 260); cv2.circle(i8, (540, 290), 110, (170, 140, 60), -1, cv2.LINE_AA); cv2.circle(i8, (540, 290), 84, (40, 46, 90), -1, cv2.LINE_AA)
        poly(i8, [(490, 300), (540, 240), (590, 300), (540, 330)], (200, 170, 90))
        cv2.line(i8, (900, 220), (900, 1100), (200, 170, 90), 6); flag_mx(i8, 905, 240, 150, 92) if False else None
        wf = i8.astype(np.float32); beam(wf, (540, 0), (540, 1300), 80, 360, (255, 220, 160), .1, 40)
        s.back = [(dof(opaque(wf), 3), .4)]
        s.main = floor_layer(1300, (46, 26, 16), (62, 38, 24))
        gal = np.zeros((H, W, 4), np.uint8)
        for k in range(3): cv2.rectangle(gal, (-40, 1700 + k * 80), (W + 40, 1730 + k * 80), (60, 32, 16, 255), -1)
        s.front = [(dof(gal, 10), 1.5), (bokeh_layer(8, (255, 210, 140), 41, ymin=200, ymax=1200), 1.7)]
        s.stamp = N.stamp(text, col, w=820, h=124, px=70, fill=tuple(int(c * .18) for c in col) + (210,))
        s.lbl = N.text_sprite('JUZGADO FEDERAL · MÉXICO' if mx else 'CORTE FEDERAL · BROOKLYN, NY', 30, (230, 220, 200, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=4)
        s.gavel_t = gavel_t; s.stamp_at = gavel_t + .25
    def draw(s, fr, t, d):
        # juez detrás del estrado golpeando el mazo
        hit = max(0., 1 - abs((t - s.gavel_t) / .18)) if t < s.gavel_t + .3 else 0
        up = ss(0, s.gavel_t - .2, t) * (1 - ss(s.gavel_t - .2, s.gavel_t, t))
        hs = character(fr, 'juez', 540, 1150, 430, t, armR=('apunta', (700, 760 - 120 * up), .85), armL=('reposo',), look=(0, .2), frown=.35)
        gavel(fr, hs[1][0], -1.2 - .9 * up + .6 * hit, 430 / 8.)
        cv2.rectangle(fr, (180, 880), (900, 1300), (78, 40, 20), -1); cv2.rectangle(fr, (160, 860), (920, 900), (110, 60, 30), -1)
        cv2.rectangle(fr, (420, 960), (660, 1040), (200, 170, 90), -1); over_t = N.text_sprite('JUEZ FEDERAL', 26, (40, 26, 10, 255), spacing=3, pad=6); blit(fr, over_t, 540, 1000)
        if hit > .5: blit(fr, glow_sprite(90, (255, 240, 200)), 720, 880, .7, add=True)
        # reo de espaldas al público (de frente a la cámara) con su abogado
        character(fr, 'reo', 660, 1640, 420, t, armR=('apunta', (690, 1470), .75), armL=('apunta', (630, 1470), .75), look=(-.3, -.5), frown=.1, mustache=True, cuffs=True)
        character(fr, 'traje', 380, 1650, 430, t, armR=('reposo',), armL=('jarra',), look=(.4, -.5), frown=.3)
        blit(fr, s.lbl, 540, 160)
        s.put_stamp(fr, t, 560)

# ---------------------------------------------------------------- traslado en avión: EE. UU. → México
class Plane(Shot):
    def __init__(s):
        sky = vgrad([(0, (6, 8, 18)), (.55, (20, 26, 46)), (1, (20, 26, 46))])
        for i in range(200): x, y = rng.randint(0, W), rng.randint(0, 800); sky[y:y + 2, x:x + 2] += rng.uniform(50, 180)
        s.back = [(dof(opaque(sky), 2), .1)]
        hang = np.zeros((H, W, 4), np.uint8); cv2.rectangle(hang, (600, 820), (W + 40, 1180), (40, 44, 52, 255), -1)
        cv2.ellipse(hang, (900, 820), (360, 120), 0, 180, 360, (40, 44, 52, 255), -1); cv2.rectangle(hang, (700, 940), (1000, 1180), (255, 210, 140, 255), -1)
        s.back.append((dof(haze(hang, (20, 26, 46), .3), 2.5), .4))
        rw = np.zeros((H, W, 3), np.uint8); rw[1180:] = (34, 36, 40)
        poly(rw, [(460, 1180), (620, 1180), (1500, H), (-420, H)], (46, 48, 54))
        for j in range(9): y0 = int(1190 + (H - 1190) * (j / 9.) ** 1.7); y1 = int(1190 + (H - 1190) * ((j + .5) / 9.) ** 1.7); cv2.line(rw, (540, y0), (540, y1), (230, 230, 230), 3 + j * 2)
        al = np.zeros((H, W)); al[1180:] = 1; s.main = rgba(rw, al)
        s.edge = [(int(540 + k * (H - y) * .62), y) for y in range(1200, H, 90) for k in (-1, 1)]
        s.front = [(bokeh_layer(10, (255, 200, 120), 43, ymin=1300, ymax=1900), 1.6)]
        s.route = N.holo_panel(620, 150, 'EE. UU.  →  MÉXICO', 'TRASLADO AUTORIZADO')
    def draw(s, fr, t, d):
        for i, (x, y) in enumerate(s.edge): blit(fr, glow_sprite(14, (255, 200, 90)), x, y, .8 + .2 * math.sin(t * 6 + i), add=True)
        # jet del gobierno con escalerilla
        x0, y0 = 120, 1240
        poly(fr, [(x0, y0 - 80), (x0 + 700, y0 - 80), (x0 + 820, y0 - 40), (x0 + 700, y0), (x0, y0)], (214, 218, 224))
        poly(fr, [(x0 + 40, y0 - 80), (x0 - 40, y0 - 230), (x0 + 40, y0 - 230), (x0 + 160, y0 - 80)], (190, 194, 202))
        poly(fr, [(x0 + 300, y0 - 30), (x0 + 520, y0 - 30), (x0 + 380, y0 + 70), (x0 + 330, y0 + 70)], (176, 180, 188))
        line(fr, (x0, y0 - 50), (x0 + 780, y0 - 50), (40, 70, 140), 8)
        for k in range(10): circ(fr, (x0 + 200 + k * 46, y0 - 58), 9, (40, 60, 90))
        poly(fr, [(x0 + 640, y0 - 70), (x0 + 690, y0 - 70), (x0 + 690, y0 - 8), (x0 + 640, y0 - 8)], (255, 220, 160))
        for k in range(6): line(fr, (x0 + 620 + k * 24, y0 + 10 + k * 22), (x0 + 690 + k * 24, y0 + 10 + k * 22), (150, 150, 158), 6)
        line(fr, (x0 + 620, y0 + 10), (x0 + 740, y0 + 140), (120, 120, 128), 6)
        blit(fr, glow_sprite(40, (255, 40, 40)), x0 + 30, y0 - 230, .5 + .5 * math.sin(t * 6), add=True)
        # alguaciles escoltando al reo hacia el avión
        u = ss(0, d, t); x = lerp(820, 690, u)
        for dx, kind in ((-130, 'traje'), (0, 'reo'), (130, 'traje')):
            kw = dict(armR=('apunta', (x + dx + 30, 1380), .75), armL=('apunta', (x + dx - 30, 1380), .75), mustache=True, cuffs=True, frown=.05) if kind == 'reo' else dict(armR=('reposo',), armL=('reposo',), frown=.4)
            character(fr, kind, x + dx, 1560, 380, t, look=(-.6, 0), run=5 * (u < 1), **kw)
        a = ss(.2, .6, t)
        if a > 0: blit(fr, s.route, 540, 520 + math.sin(t * 1.5) * 5, a)

# ---------------------------------------------------------------- "Olvida los rescates de Hollywood"
class Hollywood(Shot):
    def __init__(s):
        bg = vgrad([(0, (8, 6, 10)), (1, (18, 12, 14))])
        for i in range(8): cv2.circle(bg, (60 + i * 140, 1400), 50, (40, 26, 26), -1)
        s.back = [(dof(opaque(bg), 2), .3)]
        scr = np.zeros((H, W, 3), np.uint8); scr[:] = (40, 46, 54)
        cv2.rectangle(scr, (0, 1120), (W, 1400), (70, 70, 76), -1)                                 # muro de prisión en pantalla
        for x in range(0, W, 120): cv2.line(scr, (x, 1120), (x, 1400), (56, 56, 62), 3)
        scr = cv2.cvtColor(cv2.cvtColor(scr, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
        s.screen = scr
        s.main = np.zeros((H, W, 4), np.uint8)
        seats = np.zeros((H, W, 4), np.uint8)
        for i in range(12): cv2.circle(seats, (int(i * 100 - 20), 1800), 70, (12, 10, 12, 255), -1); cv2.circle(seats, (int(i * 100 + 30), 1650), 56, (16, 12, 14, 255), -1)
        s.front = [(dof(seats, 7), 1.4), (bokeh_layer(6, (255, 220, 160), 44, ymin=200, ymax=1200), 1.7)]
        s.stamp = N.stamp('NO EXISTE', (255, 59, 42), w=640, px=100); s.stamp_at = 1.0
        s.hw = N.text_sprite('HOLLYWOOD', 70, (240, 240, 240, 255), glow=(255, 220, 160), glow_r=12, spacing=14)
    def draw(s, fr, t, d):
        # pantalla de cine: rescate "de película" en blanco y negro
        x0, y0, x1, y1 = 90, 300, 990, 1080
        sc_ = s.screen[y0 + 300:y1 + 300, x0:x1].copy()
        hx = int(lerp(1000, 300, ss(0, d, t))); hy = 220
        CH.heli(sc_, hx, hy, 1.6, t, col=(30, 30, 34)); line(sc_, (hx, hy + 40), (hx - 10, 700), (20, 20, 20), 3)
        character(sc_, 'civil', hx - 10, 760, 220, t, armR=('apunta', (hx, 400), .9), armL=('apunta', (hx, 400), .9), look=(0, -.6), mustache=True)
        g = cv2.cvtColor(cv2.cvtColor(sc_, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB); fr[y0:y1, x0:x1] = g
        cv2.rectangle(fr, (x0 - 14, y0 - 14), (x1 + 14, y1 + 14), (40, 30, 30), 14)
        blit(fr, s.hw, 540, 220)
        # claqueta
        cx, cy = 790, 1300; op = ss(0, .25, t)
        cv2.rectangle(fr, (cx - 150, cy), (cx + 150, cy + 190), (20, 20, 22), -1)
        for k in range(5): cv2.line(fr, (cx - 140, cy + 40 + k * 32), (cx + 140, cy + 40 + k * 32), (200, 200, 200), 2)
        ang = lerp(-.5, 0, ss(.15, .35, t)); p0 = A(cx - 150, cy); v = A(math.cos(ang), math.sin(ang)) * 300; n = A(-math.sin(ang), math.cos(ang)) * -46
        poly(fr, [tuple(p0), tuple(p0 + v), tuple(p0 + v + n), tuple(p0 + n)], (230, 230, 230))
        for k in range(6): poly(fr, [tuple(p0 + v * (k / 6.)), tuple(p0 + v * ((k + .5) / 6.)), tuple(p0 + v * ((k + .5) / 6.) + n), tuple(p0 + v * (k / 6.) + n)], (20, 20, 22))
        k = ss(s.stamp_at, s.stamp_at + .3, t)
        if k > 0: line(fr, (x0, y0), (x1, y1), (255, 50, 40), 14 * k); line(fr, (x1, y0), (x0, y1), (255, 50, 40), 14 * k)
        s.put_stamp(fr, t, 700)

# ---------------------------------------------------------------- bloqueo en avenida a pantalla completa
class Blockade(Shot):
    def __init__(s, title=None, cta=False):
        sky = vgrad([(0, (10, 6, 8)), (.5, (60, 24, 16)), (1, (110, 50, 26))]); radial(sky, (540, 1200), 700, (255, 120, 40), .3)
        s.back = [(dof(opaque(sky), 2), .1)]
        city = np.zeros((H, W, 3), np.uint8); r_ = np.random.RandomState(51); x = -20
        while x < W:
            bw, bh = r_.randint(80, 170), r_.randint(250, 700); cv2.rectangle(city, (x, 1240 - bh), (x + bw, 1250), (30, 20, 22), -1)
            for wy in range(1240 - bh + 16, 1230, 32):
                for wx in range(x + 10, x + bw - 14, 24):
                    if r_.rand() < .2: cv2.rectangle(city, (wx, wy), (wx + 10, wy + 14), (255, 170, 80), -1)
            x += bw + r_.randint(2, 12)
        s.back.append((dof(haze(rgba(city, np.any(city > 0, 2).astype(np.float32)), (110, 50, 26), .3), 2), .45))
        s.main = floor_layer(1250, (26, 22, 22), (40, 34, 34))
        s.front = [(bokeh_layer(18, (255, 120, 40), 52, rmin=10, rmax=40, ymin=200, ymax=1800), 1.7)]
        s.flame = glow_sprite(70, (255, 140, 40)); s.puff = glow_sprite(130, (96, 84, 82))
        s.title = red_panel(title, w=700, h=170) if title else None; s.cta = cta
        if cta:
            c_ = np.zeros((120, 720, 4), np.uint8); im = Image.fromarray(c_); dd = ImageDraw.Draw(im)
            dd.rounded_rectangle((4, 4, 715, 115), 56, fill=(200, 20, 20, 230), outline=(255, 255, 255, 255), width=4); c_ = np.array(im)
            over(c_, N.text_sprite('DALE LIKE · SÍGUEME', 40, (255, 255, 255, 255), spacing=3, pad=10, maxw=560), 410, 60)
            over(c_, cv2.resize(emoji_sprite('👍'), (76, 76)), 62, 60); s.ctaspr = c_; s.bell = emoji_sprite('🔔')
    def draw(s, fr, t, d):
        for i in range(16):
            f = (i / 16. + t * .07) % 1; blit(fr, s.puff, 120 + (i % 5) * 220 + f * 100, 1300 - f * 900, min(1, f * 5) * (1 - f) * .55, 1 + f * 2.6)
        for j, (x, y, sc) in enumerate([(-80, 1430, .95), (520, 1450, 1.0), (230, 1340, .7)][::-1]):
            CH.C4.suv(s, fr, x, y, sc, t, 0, lights=False)
            for q in range(4):
                fl = .7 + .3 * math.sin(t * 13 + q + j); blit(fr, s.flame, x + 80 * sc + q * 90 * sc, y - 150 * sc, fl, (1.8 + .6 * fl) * sc, add=True)
        for i, (x, fy) in enumerate([(420, 1690), (900, 1660)]):
            hs = character(fr, 'comando', x, fy, 380, t + i, armR=('apunta', (x - 220, fy - 200), .85), armL=('apunta', (x - 220, fy - 200), .4), look=(-.4, 0), frown=.3, mask=True)
            lib.rifle(fr, hs, 380 / 8.)
        if s.title is not None:
            k = ss(.4, .8, t); blit(fr, s.title, 540, 420 + math.sin(t * 1.6) * 5, k * (.86 + .14 * math.sin(t * 5)), lerp(1.5, 1., eOut(k)))
        if s.cta:
            c = ss(.8, 1.2, t)
            if c > 0: blit(fr, s.ctaspr, 760, 1700, c, lerp(.6, 1, eBack((t - .8) / .4)) * .6); blit(fr, s.bell, 1010, 1680, c, .4)

# ---------------------------------------------------------------- dinero: bóveda y maletines (la primera parte de Q2)
class Vault(RL.Q2):
    def draw(s, fr, t, d):
        s.dust.draw(fr, t)
        for i in range(26):
            x = 60 + (i * 41) % 960; f = (t * .35 + (i * .37) % 1) % 1
            blit(fr, s.digits[(i * 7 + int(t * 6)) % 16], x, 200 + f * 1100, .35 * (1 - f))
        k = ss(.1, .6, t); s.briefcase(fr, 290, 1250, 1.0, t, k); s.briefcase(fr, 790, 1290, .9, t + 1, k)
        a = ss(.3, .8, t); blit(fr, s.tx, 540, 600 + math.sin(t * 1.4) * 5, a, lerp(1.2, 1, eOut(t / .8)))

# ---------------------------------------------------------------- "antes de disparar una sola bala"
class Bullet(Shot):
    def __init__(s):
        bg = vgrad([(0, (8, 8, 10)), (1, (20, 18, 16))]); s.back = [(dof(opaque(bg), 2), .2)]
        tb = np.zeros((H, W, 3), np.uint8); tb[1150:] = (40, 26, 16)
        for k in range(12): cv2.line(tb, (0, 1150 + k * 66), (W, 1150 + k * 66 + 20), (52, 34, 22), 3)
        al = np.zeros((H, W)); al[1150:] = 1; s.main = rgba(tb, al)
        s.front = [(bokeh_layer(8, (255, 200, 120), 61, ymin=200, ymax=1100), 1.7)]
        s.billspr = np.zeros((90, 200, 4), np.uint8)
        cv2.rectangle(s.billspr, (2, 2), (197, 87), (90, 170, 100, 255), -1); cv2.rectangle(s.billspr, (14, 12), (185, 77), (50, 110, 60, 255), 3); cv2.circle(s.billspr, (100, 45), 22, (190, 230, 190, 255), -1)
        s.panel = N.holo_panel(560, 150, '0 DISPAROS', 'PRIMERO: EL DINERO', col=(255, 210, 90), fill=(60, 40, 6, 190))
    def draw(s, fr, t, d):
        lay = np.zeros((H // 4, W // 4, 3), np.float32); cv2.fillPoly(lay, [np.array([(135, 0), (60, 330), (210, 330)], np.int32)], (255, 230, 190))
        fr[:] = np.clip(fr + cv2.resize(cv2.GaussianBlur(lay, (0, 0), 8), (W, H)) * .18, 0, 255).astype(np.uint8)
        cx, by = 540, 1330   # una sola bala de pie bajo el reflector
        poly(fr, [(cx - 34, by), (cx + 34, by), (cx + 34, by - 170), (cx - 34, by - 170)], (200, 150, 60))
        poly(fr, [(cx - 34, by - 170), (cx + 34, by - 170), (cx + 26, by - 250), (cx, by - 300), (cx - 26, by - 250)], (180, 110, 60))
        line(fr, (cx - 20, by - 160), (cx - 20, by - 10), (255, 220, 140), 6)
        cv2.ellipse(fr, (cx, by), (34, 10), 0, 0, 360, (140, 100, 40), -1, cv2.LINE_AA)
        for i in range(8):   # fajos de billetes que caen y la tapan
            k = ss(.6 + i * .12, .9 + i * .12, t)
            if k > 0: blit(fr, s.billspr, cx + (i % 3 - 1) * 90 + (i * 13) % 20, lerp(-200, by - 40 - (i // 3) * 70, eOut(k)), 1, .9)
        a = ss(.2, .6, t); blit(fr, s.panel, 540, 560 + math.sin(t * 1.5) * 5, a)

# ---------------------------------------------------------------- soborno bajo el escritorio
class Bribe(Shot):
    def __init__(s):
        wf = wood_wall((40, 34, 40), (20, 16, 20)); i8 = to8(wf); flag_mx(i8, 760, 300); cv2.line(i8, (755, 280), (755, 1100), (200, 170, 90), 6)
        cv2.rectangle(i8, (160, 260), (520, 640), (30, 40, 60), -1); cv2.rectangle(i8, (160, 260), (520, 640), (180, 150, 80), 10)
        s.back = [(dof(opaque(i8.astype(np.float32)), 3), .4)]
        s.main = floor_layer(1350, (34, 26, 22), (48, 38, 32))
        s.front = [(bokeh_layer(8, (255, 210, 140), 71, ymin=200, ymax=1200), 1.7)]
        s.stamp = N.stamp('CORRUPCIÓN', (255, 59, 42), w=680, px=92); s.stamp_at = 1.6
        s.env = np.zeros((70, 120, 4), np.uint8); cv2.rectangle(s.env, (2, 2), (117, 67), (230, 220, 190, 255), -1)
        cv2.line(s.env, (2, 2), (60, 40), (190, 180, 150, 255), 3); cv2.line(s.env, (117, 2), (60, 40), (190, 180, 150, 255), 3)
        cv2.rectangle(s.env, (10, -10 + 10), (50, 20), (90, 170, 100, 255), -1)
    def draw(s, fr, t, d):
        hsL = character(fr, 'traje', 280, 1500, 470, t, armR=('apunta', (520, 1380), .8), armL=('jarra',), look=(.5, 0), frown=.2)
        hsR = character(fr, 'elegante', 800, 1500, 470, t, armR=('jarra',), armL=('apunta', (560, 1380), .8), look=(-.5, 0), frown=-.2, smile=ss(1.2, 1.6, t))
        u = ss(.5, 1.4, t); p = (lerp(hsL[1][0][0], hsR[-1][0][0], u), lerp(hsL[1][0][1], hsR[-1][0][1], u))
        blit(fr, s.env, p[0], p[1], 1, 1.0)
        cv2.rectangle(fr, (60, 1300), (1020, 1340), (110, 60, 30), -1); cv2.rectangle(fr, (100, 1340), (980, 1600), (78, 40, 20), -1)   # escritorio
        lbl = N.text_sprite('BAJO LA MESA', 30, (255, 230, 200, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=4); blit(fr, lbl, 540, 1250, ss(.3, .6, t))
        s.put_stamp(fr, t, 520)

# ---------------------------------------------------------------- mapa con incendios (sin bloqueo al frente)
class FireMap(RL.Q3):
    def __init__(s):
        super().__init__(); s.title = red_panel('CULIACANAZO NACIONAL', w=820, h=170)
    def floating(s, fr, t, d, P):
        k = ss(.3, .7, t); blit(fr, s.title, 540, 330 + math.sin(t * 1.6) * 5, k * (.86 + .14 * math.sin(t * 5)), lerp(1.5, 1., eOut(k)))
        s.dust.draw(fr, t)
    def draw(s, fr, t, d):
        pul = .5 + .5 * math.sin(t * 4); blit(fr, s.gl, s.glc[0], s.glc[1], .15 + .4 * pul, add=True)
        for n, i in enumerate(s.ord):
            t0 = .2 + n * .14
            if t < t0: continue
            x, y = prj(*s.pts[i]); g = ss(t0, t0 + .4, t); fl = .7 + .3 * math.sin(t * 11 + n)
            blit(fr, s.flame, x, y - 10, g * fl, .7 + .3 * fl, add=True); circ(fr, (x, y), 7, (255, 230, 180))
            f = (t * .8 + n * .17) % 1; cv2.circle(fr, (int(x), int(y)), int(14 + f * 60), (int(255 * (1 - f)), int(60 * (1 - f)), int(40 * (1 - f))), 3, cv2.LINE_AA)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.15, 1.3, k), 520, 1150, lerp(-30, 30, k), 0

# ---------------------------------------------------------------- conferencia de prensa: el Estado negociando
class Presser(Shot):
    def __init__(s):
        bg = vgrad([(0, (14, 18, 30)), (1, (24, 28, 44))]); i8 = to8(bg)
        for x in (120, 760): flag_mx(i8, x, 260, 200, 124); cv2.line(i8, (x - 4, 240), (x - 4, 1100), (200, 170, 90), 6)
        cv2.rectangle(i8, (330, 220), (750, 560), (120, 30, 40), -1); cv2.circle(i8, (540, 390), 110, (200, 170, 90), 6, cv2.LINE_AA)
        s.back = [(dof(opaque(i8.astype(np.float32)), 3), .4)]
        s.main = floor_layer(1350, (30, 30, 36), (44, 44, 52))
        crowd = np.zeros((H, W, 4), np.uint8)
        for i in range(14): cv2.circle(crowd, (int(i * 85 - 20), 1760 + (i % 2) * 40), 64, (10, 10, 14, 255), -1)
        s.front = [(dof(crowd, 9), 1.5), (bokeh_layer(10, (220, 230, 255), 81, ymin=300, ymax=1500), 1.7)]
        s.panel = red_panel('NEGOCIANDO', w=600, h=160)
    def draw(s, fr, t, d):
        hs = character(fr, 'traje', 540, 1400, 480, t, armR=('palma',) if (t % 2) < 1 else ('reposo',), armL=('reposo',), look=(0, 0), frown=.4)
        poly(fr, [(400, 1180), (680, 1180), (650, 1500), (430, 1500)], (60, 40, 30)); cv2.circle(fr, (540, 1300), 50, (200, 170, 90), 4, cv2.LINE_AA)
        for k in (-60, 0, 60): line(fr, (540 + k, 1180), (540 + k * .3, 1090), (40, 40, 44), 5); circ(fr, (540 + k * .3, 1084), 12, (20, 20, 24))
        for i in range(4):   # flashes de las cámaras (suaves)
            f = (t * .9 + i * .29) % 1
            if f < .12: blit(fr, glow_sprite(60, (255, 255, 255)), 120 + i * 260, 1650, (1 - f / .12) * .8, add=True)
        k = ss(.3, .7, t); blit(fr, s.panel, 540, 640 + math.sin(t * 1.5) * 5, k, lerp(1.4, 1, eOut(k)))

# ---------------------------------------------------------------- sale libre por el portón del penal
class Gate(Shot):
    def __init__(s):
        sky = vgrad([(0, (6, 8, 16)), (1, (26, 30, 44))]); s.back = [(dof(opaque(sky), 2), .1)]
        wall = np.zeros((H, W, 3), np.uint8); wall[500:1300] = (84, 86, 92); al = np.zeros((H, W)); al[500:1300] = 1
        for x in range(0, W, 26): cv2.ellipse(wall, (x, 480), (14, 18), 0, 0, 360, (180, 186, 196), 2, cv2.LINE_AA); al[455:505, x - 16:x + 16] = 1
        cv2.rectangle(wall, (300, 640), (780, 1300), (255, 236, 200), -1)                              # luz al abrirse el portón
        wall[1300:] = (40, 40, 46); al[1300:] = 1
        for j in range(1, 8): y = int(1300 + (H - 1300) * (j / 7.) ** 1.7); cv2.line(wall, (0, y), (W, y), (52, 52, 58), 2)
        s.main = rgba(wall, al)
        s.front = [(bokeh_layer(10, (255, 230, 190), 91, ymin=300, ymax=1500), 1.7)]
        s.lbl = N.text_sprite('PENAL FEDERAL', 40, (220, 224, 232, 255), stroke=3, stroke_col=(0, 0, 0, 200), spacing=10)
    def draw(s, fr, t, d):
        op = ss(0, 1.2, t)
        for sd in (-1, 1):
            x0 = 540 + sd * 240 * op
            cv2.rectangle(fr, (int(min(x0, x0 + sd * 240)), 640), (int(max(x0, x0 + sd * 240)), 1300), (60, 62, 70), -1)
            for k in range(6): cv2.line(fr, (int(x0 + sd * k * 40), 640), (int(x0 + sd * k * 40), 1300), (44, 46, 52), 4)
        blit(fr, s.lbl, 540, 580)
        u = ss(.6, d, t); sc = lerp(.6, 1.05, u); fy = lerp(1300, 1640, u)
        cv2.ellipse(fr, (540, int(fy + 4)), (int(140 * sc), int(18 * sc)), 0, 0, 360, (20, 20, 24), -1, cv2.LINE_AA)
        sw = math.sin(t * 6)
        character(fr, 'civil', 540, fy, 470 * sc, t, armR=('apunta', (540 + 160 * sw, fy - 220 * sc), .9), armL=('apunta', (540 - 160 * sw, fy - 220 * sc), .9),
                  look=(0, 0), frown=-.2, smile=.5, mustache=True, cap=True, run=5)
        for x in (110, 970): CH.C4.suv(s, fr, x - (210 if x > 540 else 0), 1500, .8, t, 0)

# ---------------------------------------------------------------- territorios clave (Triángulo Dorado)
class Territory(RL.Q3):
    def __init__(s):
        super().__init__(); s.gold = glow_sprite(120, (255, 200, 70))
        s.zones = [(-107.39, 24.8, 'CULIACÁN'), (-107.5, 25.3, None), (-106.5, 26.0, None), (-105.6, 25.4, None), (-110.95, 29.07, 'SONORA'), (-106.1, 28.6, 'CHIHUAHUA'), (-104.66, 24.02, 'DURANGO')]
        s.tri = N.holo_panel(600, 140, 'TRIÁNGULO DORADO', 'SINALOA · DURANGO · CHIHUAHUA', col=(255, 210, 90), fill=(60, 40, 6, 190))
        s.lbls = {n: N.text_sprite(n, 30, (255, 230, 170, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=4) for _, _, n in s.zones if n}
    def draw(s, fr, t, d):
        pul = .5 + .5 * math.sin(t * 3)
        tri = [prj(-108.2, 25.6), prj(-106.0, 27.2), prj(-105.2, 24.6)]
        k = ss(.2, .8, t); ov = fr.copy(); poly(ov, tri, (255, 200, 70)); fr[:] = cv2.addWeighted(fr, 1 - .45 * k, ov, .45 * k, 0); pline(fr, tri + [tri[0]], (255, 230, 150), 4)
        for i, (lo, la, n) in enumerate(s.zones):
            x, y = prj(lo, la); g = ss(.2 + i * .15, .6 + i * .15, t)
            blit(fr, s.gold, x, y, g * (.4 + .3 * pul), .5, add=True); circ(fr, (x, y), 8 * g, (255, 240, 200))
            if n and g > 0: blit(fr, s.lbls[n], x, y - 40, g)
    def floating(s, fr, t, d, P):
        k = ss(.3, .7, t); blit(fr, s.tri, 540, 330 + math.sin(t * 1.5) * 5, k); s.dust.draw(fr, t)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.35, 1.55, k), 430, 1050, 0, 0

# ---------------------------------------------------------------- ajedrez: cambian las reglas del juego político
class Chess(Shot):
    def __init__(s):
        bg = vgrad([(0, (6, 6, 10)), (1, (18, 16, 22))]); s.back = [(dof(opaque(bg), 2), .2)]
        b = np.zeros((H, W, 3), np.uint8); al = np.zeros((H, W), np.float32)
        for r in range(8):
            for c in range(8):
                y0 = 1000 + r * 100 * (1 + r * .08); y1 = 1000 + (r + 1) * 100 * (1 + (r + 1) * .08)
                def X(cc, yy): return 540 + (cc - 4) * 90 * (1 + (yy - 1000) / 700)
                pts = np.array([(X(c, y0), y0), (X(c + 1, y0), y0), (X(c + 1, y1), y1), (X(c, y1), y1)], np.int32)
                cv2.fillPoly(b, [pts], (200, 190, 170) if (r + c) % 2 == 0 else (60, 40, 30), cv2.LINE_AA); cv2.fillPoly(al, [pts], 1.0)
        s.main = rgba(b, al)
        s.front = [(bokeh_layer(8, (255, 210, 140), 101, ymin=200, ymax=1000), 1.7)]
        s.panel = red_panel('NUEVAS REGLAS', w=640, h=160)
    def piece(s, fr, x, y, sc, col, king=True, ang=0.):
        M = cv2.getRotationMatrix2D((x, y), math.degrees(ang), 1.)
        def P(px, py): q = M @ np.array([px, py, 1.]); return (q[0], q[1])
        poly(fr, [P(x - 60 * sc, y), P(x + 60 * sc, y), P(x + 44 * sc, y - 40 * sc), P(x - 44 * sc, y - 40 * sc)], col)
        poly(fr, [P(x - 30 * sc, y - 40 * sc), P(x + 30 * sc, y - 40 * sc), P(x + 22 * sc, y - 200 * sc), P(x - 22 * sc, y - 200 * sc)], col)
        poly(fr, [P(x - 44 * sc, y - 200 * sc), P(x + 44 * sc, y - 200 * sc), P(x + 34 * sc, y - 250 * sc), P(x - 34 * sc, y - 250 * sc)], col)
        if king:
            poly(fr, [P(x - 8 * sc, y - 250 * sc), P(x + 8 * sc, y - 250 * sc), P(x + 8 * sc, y - 320 * sc), P(x - 8 * sc, y - 320 * sc)], col)
            poly(fr, [P(x - 26 * sc, y - 290 * sc), P(x + 26 * sc, y - 290 * sc), P(x + 26 * sc, y - 276 * sc), P(x - 26 * sc, y - 276 * sc)], col)
    def draw(s, fr, t, d):
        fall = eOut(ss(.5, 1.3, t))
        s.piece(fr, 360, 1350, 1.2, (236, 230, 220), True, fall * 1.4)            # rey blanco (el Estado) cae
        s.piece(fr, 720, 1420, 1.42, (200, 60, 40), True, 0); s.piece(fr, 720, 1420, 1.35, (24, 22, 24), True, 0)   # rey negro se impone (con contorno rojo)
        blit(fr, glow_sprite(140, (255, 60, 40)), 720, 1100, .3 + .2 * math.sin(t * 4), add=True)
        k = ss(.9, 1.3, t); blit(fr, s.panel, 540, 560 + math.sin(t * 1.5) * 5, k, lerp(1.4, 1, eOut(k)))

# ================================================================ línea de tiempo de tomas
def tl():
    T = RL.at; S = RL.SC_T
    return [
        (0, T('Estados') - .25, Court('EXTRADICIÓN APROBADA', (70, 230, 120), gavel_t=T('extradición') - .1), 0),
        (T('Estados') - .25, T('Olvida') - .2, Plane(), 0),
        (T('Olvida') - .2, T('organización') - .25, Hollywood(), 0),
        (T('organización') - .25, T('Culiacanazo') - .15, RL.Q1(), 0),
        (T('Culiacanazo') - .15, S[1], Blockade(), 0),
        (S[1], T('Antes') - .2, Vault(), 1),
        (T('Antes') - .2, T('intentarían') - .2, Bullet(), 1),
        (T('intentarían') - .2, S[2], Bribe(), 1),
        (S[2], T('desatarían') - .2, Court('LIBERACIÓN NEGADA', (255, 59, 42), gavel_t=1.4, mx=True), 2),
        (T('desatarían') - .2, T('bloqueos') - .2, FireMap(), 2),
        (T('bloqueos') - .2, T('obligar') - .2, Blockade('ESTADO DE SITIO', cta=True), 2),
        (T('obligar') - .2, S[3], Presser(), 2),
        (S[3], T('recuperar') - .4, Gate(), 3),
        (T('recuperar') - .4, T('viejas') - .2, Territory(), 3),
        (T('viejas') - .2, T('cambiando') - .2, RL.Q4(), 3),
        (T('cambiando') - .2, S[4], Chess(), 3),
        (S[4], RL.DUR, RL.Q5(), 4),
    ]

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    RS.SC_T[:] = RL.SC_T; RS.DUR = RL.DUR
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in RS.build_subs_from_words(RL.WORDS, [1500, 1500, 1500, 1500, 1480])]
    emos = [e + (emoji_sprite(e[2]),) for e in RL.EMOJIS]
    shots = tl()
    # el Q1 original pone sus sellos con tiempos absolutos: lo desplazamos a su inicio
    def one(i, T):
        a, b, sc, g = shots[i]; lt = T - a
        if isinstance(sc, RL.Q1): lt = T            # Q1 usa tiempos absolutos de la voz
        return cinema(render3d(sc, lt, b - a if not isinstance(sc, RL.Q1) else RL.SC_T[1], T), g, T)
    def frame(T):
        i = max(k for k, s_ in enumerate(shots) if T >= s_[0] - 1e-6)
        fr = one(i, T); a = shots[i][0]
        if i > 0 and T - a < .3: fr = cv2.addWeighted(one(i - 1, T), 1 - ss(0, .3, T - a), fr, ss(0, .3, T - a), 0)
        draw_overlays(fr, T, subs, emos); return fr
    if mode == 'info':
        for a, b, sc, g in shots: print(f'{a:6.2f}-{b:6.2f} {type(sc).__name__}')
        return
    if mode == 'test':
        for T in [float(x) for x in sys.argv[2:]]:
            cv2.imwrite(f'{OUT}/z_{T:05.1f}.jpg', cv2.resize(frame(T), (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == 'seg':
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', f'{OUT}/{os.environ.get("SEGP", "zseg")}_{f0:04d}.mp4']
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(f0, f1): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('SEG', f0, f1, flush=True); return

if __name__ == '__main__': main()
