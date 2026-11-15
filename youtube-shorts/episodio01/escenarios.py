#!/usr/bin/env python3
# Escenarios, utilería y utilidades de animación del episodio 01 (capas con profundidad para render3d).
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'chapo')); sys.path.insert(0, HERE)
import narco_short as N
from narco3d import dof, rgba, haze, bokeh_layer, render3d, cinema, vgrad, radial, beam, glow_sprite, W, H, FPS, to8, blit, sub_sprite
from rig import *

rng = np.random.RandomState(11)
def opaque(img): return rgba(np.clip(img, 0, 255), np.ones((H, W)))   # sin desbordes de color
def layer_from(img8):
    """capa RGBA a partir de un dibujo sobre negro (lo que no es negro es opaco)."""
    return rgba(img8, (img8.max(2) > 0).astype(np.float32))
def ss(a, b, x): return ease((x - a) / max(1e-6, b - a))
def fbeam(fr, *a):
    f = fr.astype(np.float32); beam(f, *a); fr[:] = to8(f)
def tint(fr, col, k, x0=0, x1=W, y0=0, y1=H):
    """baño de luz de color (ej. luz de la TV o de las sirenas)."""
    if k <= 0: return
    roi = fr[y0:y1, x0:x1].astype(np.float32); fr[y0:y1, x0:x1] = to8(roi * (1 - k) + np.array(col, np.float32) * k * (roi.mean(2, keepdims=True) / 128 + .3))

def draw_rotated(fr, draw_fn, pivot, ang):
    """dibuja un personaje en un lienzo aparte y lo rota alrededor de un pivote (caídas, figura que se arrastra)."""
    can = np.zeros_like(fr); draw_fn(can)
    M = cv2.getRotationMatrix2D((float(pivot[0]), float(pivot[1])), math.degrees(-ang), 1.)
    r = cv2.warpAffine(can, M, (fr.shape[1], fr.shape[0]), flags=cv2.INTER_LINEAR)
    m = (r.max(2) > 6)[:, :, None]; fr[:] = np.where(m, r, fr)

def walls(c_top, c_mid, c_bot, y_floor):
    img = vgrad([(0, c_top), (.6, c_mid), (1, c_bot)]); i8 = to8(img); return i8

def floor_layer(y0, col, line_col, planks=True):
    fl = np.zeros((H, W, 3), np.uint8); fl[y0:] = col
    for j in range(1, 10): y = int(y0 + (H - y0) * (j / 9.) ** 1.6); cv2.line(fl, (0, y), (W, y), line_col, 2)
    if planks:
        for k in range(-12, 13): cv2.line(fl, (540 + k * 60, y0), (540 + k * 260, H), line_col, 2)
    al = np.zeros((H, W)); al[y0:] = 1; return rgba(fl, al)

# ---------------------------------------------------------------- utilería
def car(fr, x, y, sc, col, t, ang=0., lights=True, wheel=0.):
    """auto de perfil (mira a la derecha); ang = derrape."""
    pts = np.array([(-210, -40), (-200, -95), (-120, -105), (-70, -170), (70, -172), (130, -110), (205, -95), (215, -40), (200, -22), (-200, -22)], np.float64) * sc
    R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]]); P = lambda q: (q @ R.T) + np.array([x, y])
    poly(fr, P(pts), col); poly(fr, P(pts * [1, .55] + [0, -10 * sc]), dark(col, .8))
    poly(fr, P(np.array([(-60, -158), (-5, -158), (-5, -110), (-105, -110)]) * sc), (90, 130, 170)); poly(fr, P(np.array([(5, -158), (62, -158), (115, -110), (5, -110)]) * sc), (80, 120, 160))
    for wx in (-130, 130):
        c = P(np.array([[wx * sc, -22 * sc]]))[0]; circ(fr, c, 40 * sc, (18, 18, 20)); circ(fr, c, 20 * sc, (150, 150, 158))
        for k in range(3): a_ = wheel + k * 2.1; line(fr, c, c + A(math.cos(a_), math.sin(a_)) * 18 * sc, (90, 90, 96), 3)
    if lights:
        blit(fr, glow_sprite(int(60 * sc) + 6, (255, 240, 200)), *P(np.array([[212 * sc, -70 * sc]]))[0], .9, add=True)
        blit(fr, glow_sprite(int(30 * sc) + 4, (255, 40, 40)), *P(np.array([[-206 * sc, -70 * sc]]))[0], .8, add=True)

def tree(fr, x, y, sc, t, col=(30, 46, 34)):
    line(fr, (x, y), (x, y - 260 * sc), (50, 36, 28), 22 * sc)
    sw = math.sin(t * 1.3 + x) * 10 * sc
    for (dx, dy, r) in [(0, -330, 110), (-80, -270, 85), (80, -275, 90), (0, -230, 95)]:
        circ(fr, (x + dx * sc + sw * (1 + dy / -300), y + dy * sc), r * sc, col)
        circ(fr, (x + dx * sc + sw * (1 + dy / -300) - 20 * sc, y + dy * sc - 25 * sc), r * .55 * sc, tuple(min(255, int(v * 1.25)) for v in col))

def streetlamp(fr, x, y, h=520):
    line(fr, (x, y), (x, y - h), (40, 42, 48), 12); line(fr, (x, y - h), (x + 70, y - h), (40, 42, 48), 10)
    blit(fr, glow_sprite(90, (255, 200, 120)), x + 70, y - h + 14, .8, add=True); circ(fr, (x + 70, y - h + 10), 14, (255, 236, 200))

def phone_sprite(text, sub=None, w=300, h=560, glow=(120, 200, 255)):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, w - 5, h - 5), 40, fill=(20, 20, 24, 255), outline=(80, 80, 90, 255), width=6)
    d.rounded_rectangle((18, 30, w - 19, h - 30), 24, fill=(14, 30, 50, 255))
    f = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Black.otf', 40); f2 = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Black.otf', 24)
    d.text((w // 2, h // 2 - 40), text, font=f, fill=(240, 240, 250, 255), anchor='mm')
    if sub: d.text((w // 2, h // 2 + 20), sub, font=f2, fill=glow + (255,), anchor='mm')
    return np.array(im)

FISH = {}
def fisheye(img, k=.35):
    """lente ojo de pez de la mirilla."""
    h, w = img.shape[:2]
    if (h, w, k) not in FISH:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); cx, cy = w / 2, h / 2; r = min(cx, cy)
        nx, ny = (xx - cx) / r, (yy - cy) / r; rr = np.sqrt(nx * nx + ny * ny); f = 1 + k * rr * rr
        FISH[(h, w, k)] = ((cx + nx / f * r).astype(np.float32), (cy + ny / f * r).astype(np.float32), rr)
    mx, my, rr = FISH[(h, w, k)]
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR)
    vig = np.clip((1.0 - rr) / .25, 0, 1)[:, :, None]; return to8(out * vig)

def caption_sprite(text, col=(255, 255, 255), px=62):
    return N.text_sprite(text, px, col + (255,), stroke=7, stroke_col=(0, 0, 0, 230), maxw=940, pad=20)

# ---------------------------------------------------------------- texturas y detalles
def bricks(img, x0, y0, x1, y1, base, mortar, bw=60, bh=22, seed=1):
    r_ = np.random.RandomState(seed); cv2.rectangle(img, (x0, y0), (x1, y1), mortar, -1)
    for j, y in enumerate(range(y0, y1, bh)):
        off = (bw // 2) * (j % 2)
        for x in range(x0 - off, x1, bw):
            k = r_.uniform(.82, 1.12); c = tuple(int(min(255, v * k)) for v in base)
            cv2.rectangle(img, (max(x0, x + 2), y + 2), (min(x1, x + bw - 2), min(y1, y + bh - 2)), c, -1)
def wallpaper(img, x0, y0, x1, y1, base, motif, step=56):
    cv2.rectangle(img, (x0, y0), (x1, y1), base, -1)
    for j, y in enumerate(range(y0 + 20, y1, step)):
        for x in range(x0 + 20 + (step // 2) * (j % 2), x1, step):
            pts = np.array([(x, y - 9), (x + 7, y), (x, y + 9), (x - 7, y)], np.int32); cv2.fillPoly(img, [pts], motif, cv2.LINE_AA)
            cv2.circle(img, (x, y), 2, tuple(min(255, v + 25) for v in motif), -1)
def wainscot(img, y0, y1, col, x0=0, x1=W, panel=180):
    cv2.rectangle(img, (x0, y0), (x1, y1), col, -1); cv2.rectangle(img, (x0, y0), (x1, y0 + 16), tuple(min(255, v + 22) for v in col), -1)
    for x in range(x0 + 20, x1 - 40, panel): cv2.rectangle(img, (x, y0 + 40), (x + panel - 40, y1 - 30), dark(col, .82), 4)
def frame_pic(img, x, y, w, h, frame=(150, 118, 70), content='paisaje', seed=0):
    cv2.rectangle(img, (x - 10, y - 10), (x + w + 10, y + h + 10), frame, -1); cv2.rectangle(img, (x, y), (x + w, y + h), (230, 226, 214), -1)
    if content == 'paisaje':
        cv2.rectangle(img, (x + 8, y + 8), (x + w - 8, y + h // 2), (120, 170, 210), -1); cv2.rectangle(img, (x + 8, y + h // 2), (x + w - 8, y + h - 8), (90, 140, 80), -1)
        cv2.circle(img, (x + w * 3 // 4, y + h // 4), max(4, w // 10), (250, 220, 120), -1)
    elif content == 'familia':                                                       # foto de la familia: tres figuritas
        cv2.rectangle(img, (x + 6, y + 6), (x + w - 6, y + h - 6), (170, 200, 220), -1)
        for k, (cx, hh, col) in enumerate([(.3, .62, (52, 86, 132)), (.55, .58, (200, 146, 62)), (.75, .4, (252, 206, 70))]):
            px = x + int(w * cx); py = y + h - 10; uu = h * hh / 8
            cv2.line(img, (px, py), (px, int(py - 3.3 * uu)), col, max(2, int(uu * .9))); cv2.circle(img, (px, int(py - 4.3 * uu)), max(3, int(uu * .9)), (246, 244, 240), -1)
    elif content == 'abstracto':
        for k in range(4): cv2.circle(img, (x + 10 + (k * 37 + seed * 13) % max(1, w - 20), y + 10 + (k * 53) % max(1, h - 20)), max(5, w // 6), [(200, 80, 60), (60, 120, 180), (230, 190, 80), (90, 160, 110)][k], -1)
def bookshelf(img, x, y, w, h, seed=2):
    r_ = np.random.RandomState(seed); cv2.rectangle(img, (x, y), (x + w, y + h), (92, 62, 40), -1)
    rows = 3; rh = h // rows
    for r in range(rows):
        yb = y + (r + 1) * rh - 10; cv2.rectangle(img, (x, yb), (x + w, yb + 10), (120, 84, 54), -1); bx = x + 12
        while bx < x + w - 30:
            if r_.rand() < .12:                                                       # maceta o adorno
                cv2.rectangle(img, (bx, yb - 40), (bx + 34, yb), (180, 100, 70), -1)
                for k in range(5): cv2.ellipse(img, (bx + 17 + (k - 2) * 8, yb - 48 - (k % 2) * 10), (9, 20), (k - 2) * 20, 0, 360, (60, 130, 70), -1, cv2.LINE_AA)
                bx += 46; continue
            bwk = r_.randint(14, 26); bhk = r_.randint(int(rh * .5), int(rh * .82))
            col = [(170, 40, 40), (40, 80, 150), (60, 120, 70), (200, 160, 60), (110, 60, 120), (220, 220, 210), (40, 40, 44)][r_.randint(0, 7)]
            cv2.rectangle(img, (bx, yb - bhk), (bx + bwk, yb), col, -1); cv2.line(img, (bx + 3, yb - bhk + 10), (bx + bwk - 3, yb - bhk + 10), (230, 210, 150), 2)
            bx += bwk + 2
def plant(img, x, y, sc=1., pot=(170, 96, 64), leaf=(56, 128, 70), seed=3):
    r_ = np.random.RandomState(seed)
    poly(img, [(x - 40 * sc, y - 80 * sc), (x + 40 * sc, y - 80 * sc), (x + 30 * sc, y), (x - 30 * sc, y)], pot)
    for k in range(9):
        a_ = -math.pi / 2 + (k - 4) * .32 + r_.uniform(-.1, .1); L = (110 + r_.uniform(0, 70)) * sc
        p0 = A(x, y - 80 * sc); p1 = p0 + A(math.cos(a_), math.sin(a_)) * L
        line(img, p0, p1, dark(leaf, .7), 4 * sc); ell(img, p1, 26 * sc, 11 * sc, math.degrees(a_), leaf)
def clock(img, x, y, r, hh=10, mm=47):
    cv2.circle(img, (x, y), r + 8, (90, 66, 40), -1); cv2.circle(img, (x, y), r, (240, 236, 226), -1)
    for k in range(12): a_ = k * math.pi / 6; cv2.line(img, (int(x + math.cos(a_) * r * .82), int(y + math.sin(a_) * r * .82)), (int(x + math.cos(a_) * r * .95), int(y + math.sin(a_) * r * .95)), (40, 40, 44), 3)
    am = (mm / 60) * 2 * math.pi - math.pi / 2; ah = ((hh % 12) / 12 + mm / 720) * 2 * math.pi - math.pi / 2
    cv2.line(img, (x, y), (int(x + math.cos(ah) * r * .5), int(y + math.sin(ah) * r * .5)), (30, 30, 34), 6); cv2.line(img, (x, y), (int(x + math.cos(am) * r * .78), int(y + math.sin(am) * r * .78)), (30, 30, 34), 4)
    cv2.circle(img, (x, y), 5, (180, 40, 40), -1)
def window_night(img, x, y, w, h, curtains=(130, 50, 56), blinds=True, outside='casas', frame=(120, 90, 60)):
    cv2.rectangle(img, (x, y), (x + w, y + h), (14, 22, 42), -1)
    r_ = np.random.RandomState(x)
    if outside == 'casas':
        for k in range(4):
            hx = x + 10 + k * (w // 4); hy = y + h - 60 - r_.randint(0, 50); cv2.rectangle(img, (hx, hy), (hx + w // 4 - 12, y + h), (24, 30, 46), -1)
            poly(img, [(hx - 6, hy), (hx + w // 8 - 6, hy - 30), (hx + w // 4 - 6, hy)], (30, 34, 50))
            if r_.rand() < .7: cv2.rectangle(img, (hx + 10, hy + 14), (hx + 26, hy + 30), (255, 210, 140), -1)
        for k in range(14): cv2.circle(img, (x + r_.randint(5, w - 5), y + r_.randint(5, h // 2)), 1, (220, 220, 255), -1)
    if blinds:
        for yy in range(y + 6, y + int(h * .35), 14): cv2.line(img, (x, yy), (x + w, yy), (190, 180, 160), 6)
    cv2.rectangle(img, (x, y), (x + w, y + h), frame, 14); cv2.line(img, (x + w // 2, y), (x + w // 2, y + h), frame, 8)
    cv2.rectangle(img, (x - 30, y + h), (x + w + 30, y + h + 22), dark(frame, 1.15) if False else frame, -1)        # repisa
    for sd, cx in ((-1, x - 20), (1, x + w + 20)):                                                          # cortinas con pliegues
        pts = [(cx - 50, y - 40), (cx + 50, y - 40), (cx + 40 + sd * 10, y + h + 80), (cx - 40 + sd * 10, y + h + 80)]
        cv2.fillPoly(img, [np.array(pts, np.int32)], curtains, cv2.LINE_AA)
        for k in range(4): cv2.line(img, (cx - 36 + k * 24, y - 30), (cx - 30 + k * 24 + sd * 8, y + h + 70), dark(curtains, .78), 4)
    cv2.rectangle(img, (x - 90, y - 52), (x + w + 90, y - 40), (70, 60, 50), -1)                           # barra

def set_street(shop_open=True, seed=3):
    sky = vgrad([(0, (6, 8, 22)), (.55, (22, 24, 48)), (1, (44, 32, 44))])
    r_ = np.random.RandomState(seed)
    for i in range(220): x, y = r_.randint(0, W), r_.randint(0, 760); sky[y:y + 2, x:x + 2] += r_.uniform(40, 150)
    radial(sky, (860, 170), 160, (200, 210, 255), .25); cv2.circle(sky, (860, 170), 46, (232, 232, 220), -1); cv2.circle(sky, (876, 160), 40, (200, 204, 210), -1)  # luna
    for k in range(5): cv2.ellipse(sky, (r_.randint(0, W), r_.randint(80, 500)), (r_.randint(140, 260), r_.randint(18, 34)), 0, 0, 360, (40, 42, 66), -1, cv2.LINE_AA)
    back = [(dof(opaque(sky), 2), .08)]
    far = np.zeros((H, W, 3), np.uint8); x = -20
    while x < W:
        bw, bh = r_.randint(90, 170), r_.randint(330, 700); top = 1080 - bh
        cv2.rectangle(far, (x, top), (x + bw, 1090), (30, 28, 42), -1)
        if r_.rand() < .4: cv2.rectangle(far, (x + 20, top - 40), (x + 50, top), (36, 34, 46), -1); cv2.line(far, (x + 30, top - 40), (x + 30, top - 60), (36, 34, 46), 3)   # tinaco
        if r_.rand() < .3: cv2.line(far, (x + bw - 20, top), (x + bw - 20, top - 70), (44, 42, 54), 3); cv2.circle(far, (x + bw - 20, top - 70), 5, (255, 40, 40), -1)  # antena
        for wy in range(top + 20, 1070, 34):
            for wx in range(x + 12, x + bw - 16, 26):
                if r_.rand() < .33: cv2.rectangle(far, (wx, wy), (wx + 12, wy + 16), (255, 196, 120) if r_.rand() < .8 else (140, 200, 255), -1)
        x += bw + r_.randint(4, 14)
    back.append((dof(haze(layer_from(far), (44, 32, 44), .35), 2.5), .35))
    m = np.zeros((H, W, 3), np.uint8)
    bricks(m, -10, 300, W + 10, 1360, (110, 58, 48), (70, 50, 46), seed=seed)                             # edificio de ladrillo
    for row, yy in enumerate((380, 640)):                                                                   # departamentos arriba
        for k, xx in enumerate(range(60, W - 60, 200)):
            lit = r_.rand() < .6; cv2.rectangle(m, (xx - 8, yy - 8), (xx + 128, yy + 168), (200, 190, 170), -1)
            cv2.rectangle(m, (xx, yy), (xx + 120, yy + 160), (255, 214, 150) if lit else (30, 36, 56), -1)
            cv2.line(m, (xx + 60, yy), (xx + 60, yy + 160), (200, 190, 170), 6); cv2.line(m, (xx, yy + 70), (xx + 120, yy + 70), (200, 190, 170), 6)
            if lit:
                cv2.rectangle(m, (xx + 4, yy + 4), (xx + 30, yy + 156), (170, 80, 80), -1); cv2.rectangle(m, (xx + 90, yy + 4), (xx + 116, yy + 156), (170, 80, 80), -1)
                if r_.rand() < .4: cv2.circle(m, (xx + 60, yy + 70), 22, (120, 80, 50), -1); cv2.rectangle(m, (xx + 42, yy + 90), (xx + 78, yy + 160), (120, 80, 50), -1)   # silueta
            cv2.rectangle(m, (xx - 12, yy + 168), (xx + 132, yy + 184), (90, 80, 76), -1)
            if r_.rand() < .5:
                for q in range(5): cv2.circle(m, (xx + 10 + q * 25, yy + 160), 10, [(220, 60, 80), (240, 200, 60), (230, 120, 160)][q % 3], -1)   # macetas con flores
            if r_.rand() < .3: cv2.rectangle(m, (xx + 130, yy + 90), (xx + 190, yy + 140), (170, 170, 176), -1); [cv2.line(m, (xx + 134, yy + 96 + j * 8), (xx + 186, yy + 96 + j * 8), (120, 120, 126), 2) for j in range(5)]  # aire acondicionado
    for yy in range(560, 1000, 120): cv2.rectangle(m, (W - 120, yy), (W, yy + 10), (40, 40, 44), -1); [cv2.line(m, (W - 120 + j * 20, yy - 50), (W - 120 + j * 20, yy), (40, 40, 44), 3) for j in range(7)]   # escalera de incendios
    cv2.line(m, (40, 300), (40, 1360), (70, 70, 76), 10)                                                     # bajante
    cv2.rectangle(m, (60, 900), (700, 1360), (54, 44, 42), -1)                                               # local MINI MARKET
    cv2.rectangle(m, (90, 1010), (520, 1330), (255, 224, 170) if shop_open else (40, 40, 50), -1)            # vitrina
    for sh in (1100, 1190, 1280):
        cv2.rectangle(m, (95, sh), (515, sh + 8), (150, 120, 90), -1); bx = 100
        while bx < 500:
            bw_ = r_.randint(16, 30); bh_ = r_.randint(30, 70); col = [(200, 50, 50), (60, 140, 200), (240, 200, 60), (90, 170, 90), (230, 230, 230), (230, 120, 40)][r_.randint(0, 6)]
            cv2.rectangle(m, (bx, sh - bh_), (bx + bw_, sh), col, -1); bx += bw_ + 4
    cv2.rectangle(m, (90, 1010), (520, 1330), (200, 190, 170), 8); cv2.line(m, (305, 1010), (305, 1330), (200, 190, 170), 6)
    for k in range(10): poly(m, [(80 + k * 46, 960), (126 + k * 46, 960), (126 + k * 46, 1000), (80 + k * 46, 1000)], (200, 40, 40) if k % 2 == 0 else (240, 236, 226))  # toldo a rayas
    for k in range(10): cv2.ellipse(m, (103 + k * 46, 1000), (23, 12), 0, 0, 180, (200, 40, 40) if k % 2 == 0 else (240, 236, 226), -1)
    cv2.rectangle(m, (540, 1010), (700, 1340), (40, 30, 26), -1); cv2.rectangle(m, (550, 1020), (690, 1340), (255, 214, 150) if shop_open else (30, 30, 36), -1)  # puerta
    cv2.rectangle(m, (590, 1060), (650, 1100), (230, 40, 60), -1)                                            # letrero «abierto»
    for k, (px, py, col) in enumerate([(110, 920, (240, 210, 80)), (600, 920, (80, 180, 220))]): cv2.rectangle(m, (px, py), (px + 70, py + 30), col, -1)   # carteles
    cv2.rectangle(m, (720, 900), (W, 1360), (60, 70, 66), -1); cv2.rectangle(m, (760, 1010), (1040, 1330), (210, 240, 220), -1)   # FARMACIA
    for k in range(3): cv2.rectangle(m, (780 + k * 90, 1100), (850 + k * 90, 1310), (240, 250, 245), -1); cv2.rectangle(m, (790 + k * 90, 1150), (840 + k * 90, 1180), (80, 170, 110), -1)
    cv2.rectangle(m, (760, 1010), (1040, 1330), (180, 190, 186), 8)
    m[1360:1500] = (96, 94, 100); cv2.rectangle(m, (-10, 1360), (W + 10, 1376), (126, 124, 130), -1)          # banqueta
    for x in range(0, W, 120): cv2.line(m, (x, 1376), (x - 26, 1500), (80, 78, 84), 3)
    cv2.line(m, (300, 1400), (340, 1440), (70, 68, 74), 2); cv2.line(m, (340, 1440), (330, 1480), (70, 68, 74), 2)   # grietas
    cv2.rectangle(m, (-10, 1490), (W + 10, 1504), (150, 148, 154), -1)                                       # orilla
    m[1504:] = (34, 34, 40); nz = r_.randint(0, 14, (H - 1504, W, 1)).astype(np.uint8); m[1504:] = cv2.add(m[1504:], np.repeat(nz, 3, 2))   # asfalto
    for x in range(0, W, 220): cv2.rectangle(m, (x, 1720), (x + 120, 1736), (230, 210, 120), -1)
    for k in range(6): cv2.rectangle(m, (20 + k * 40, 1520), (44 + k * 40, 1900), (200, 200, 204), -1)      # paso peatonal
    cv2.ellipse(m, (700, 1850), (80, 22), 0, 0, 360, (50, 50, 56), -1); cv2.ellipse(m, (700, 1850), (60, 15), 0, 0, 360, (70, 70, 76), 3)   # coladera
    for (px, py, col) in [(420, 1640, (255, 90, 140)), (900, 1780, (90, 220, 150)), (150, 1880, (255, 200, 120))]:      # charcos con reflejos de neón
        ov = m.copy(); cv2.ellipse(ov, (px, py), (110, 24), 0, 0, 360, col, -1); m[:] = cv2.addWeighted(m, .75, ov, .25, 0)
    # mobiliario urbano
    cv2.rectangle(m, (330, 1290), (390, 1380), (40, 90, 60), -1); cv2.rectangle(m, (322, 1280), (398, 1296), (30, 70, 46), -1)      # bote de basura
    cv2.rectangle(m, (980, 1280), (1040, 1380), (40, 70, 150), -1); cv2.ellipse(m, (1010, 1280), (30, 16), 0, 180, 360, (40, 70, 150), -1)   # buzón
    cv2.rectangle(m, (868, 1320), (896, 1380), (200, 40, 40), -1); cv2.circle(m, (882, 1316), 16, (200, 40, 40), -1); cv2.rectangle(m, (858, 1338), (906, 1348), (170, 30, 30), -1)  # hidrante
    cv2.rectangle(m, (420, 1330), (520, 1346), (110, 76, 50), -1); [cv2.line(m, (q, 1346), (q, 1380), (40, 40, 44), 4) for q in (428, 512)]   # banca
    cv2.circle(m, (640, 1350), 26, (30, 30, 34), 4); cv2.circle(m, (700, 1350), 26, (30, 30, 34), 4); cv2.line(m, (640, 1350), (672, 1316), (40, 140, 200), 4); cv2.line(m, (672, 1316), (700, 1350), (40, 140, 200), 4)   # bicicleta
    al = np.zeros((H, W)); al[300:] = 1
    wires = np.zeros((H, W, 4), np.uint8)
    for k in range(3): cv2.line(wires, (-10, 150 + k * 26), (W + 10, 200 + k * 30), (20, 20, 24, 255), 3)    # cables de luz (primer plano)
    front = [(dof(wires, 2), 1.3), (bokeh_layer(10, (255, 200, 130), seed + 40, ymin=300, ymax=1300), 1.7)]
    return back, rgba(m, al), front

def street_props(fr, t, lamps=(250, 820), trees=(60, 1000), signal=True):
    """elementos animados de la calle: árboles, farolas con polillas, semáforo, neón que parpadea, vapor."""
    for x in trees: tree(fr, x, 1380, .95, t)
    for x in lamps:
        streetlamp(fr, x, 1370)
        for k in range(3): circ(fr, (x + 70 + math.sin(t * 7 + k * 2) * 26, 864 + math.cos(t * 5 + k) * 16), 2, (255, 240, 200))
    if signal:
        line(fr, (1050, 1370), (1050, 1000), (40, 42, 48), 10); cv2.rectangle(fr, (1024, 870), (1076, 1010), (30, 30, 34), -1)
        st = int(t / 2.5) % 3
        for k, col in enumerate([(255, 50, 40), (255, 190, 40), (60, 230, 90)]):
            on = (k == [2, 1, 0][st]); circ(fr, (1050, 900 + k * 42), 14, col if on else dark(col, .25))
            if on: blit(fr, glow_sprite(40, col), 1050, 900 + k * 42, .7, add=True)
    fl = .75 + .25 * (math.sin(t * 23) > -.8)
    blit(fr, N.text_sprite('MINI MARKET · 24 H', 54, (255, 90, 120, 255), glow=(255, 60, 120), glow_r=14, spacing=6), 380, 940, fl)
    blit(fr, N.text_sprite('FARMACIA', 46, (120, 255, 170, 255), glow=(60, 220, 120), glow_r=12, spacing=6), 900, 950, 1)
    for k in range(6):                                                                    # vapor de la coladera
        f = (t * .4 + k / 6.) % 1; blit(fr, glow_sprite(60, (120, 120, 130)), 700 + math.sin(f * 6 + k) * 20, 1840 - f * 300, (1 - f) * .25, 1 + f)

def set_dining():
    i8 = np.zeros((H, W, 3), np.uint8)
    wallpaper(i8, 0, 0, W, 1000, (96, 70, 56), (110, 82, 64)); cv2.rectangle(i8, (0, 0), (W, 26), (140, 110, 80), -1)   # moldura
    wainscot(i8, 1000, 1300, (110, 76, 52))
    window_night(i8, 720, 400, 280, 440)
    bookshelf(i8, 30, 300, 280, 520)
    frame_pic(i8, 380, 330, 150, 110, content='familia'); frame_pic(i8, 380, 480, 100, 130, content='paisaje'); clock(i8, 600, 200, 56)
    cv2.rectangle(i8, (330, 860), (680, 1000), (90, 58, 38), -1); cv2.rectangle(i8, (320, 846), (690, 864), (120, 82, 54), -1)   # aparador
    for k in range(3): cv2.rectangle(i8, (350 + k * 110, 880), (440 + k * 110, 980), (76, 48, 30), 4); cv2.circle(i8, (395 + k * 110, 930), 5, (200, 170, 90), -1)
    poly(i8, [(470, 846), (510, 846), (500, 780), (480, 780)], (90, 130, 170))                                # florero
    for k in range(5): cv2.circle(i8, (470 + k * 10, 770 - (k % 2) * 16), 12, [(230, 60, 80), (250, 220, 90), (240, 140, 180)][k % 3], -1)
    cv2.ellipse(i8, (610, 836), (50, 14), 0, 0, 360, (200, 200, 190), -1); [cv2.circle(i8, (590 + k * 18, 826), 11, c_, -1) for k, c_ in enumerate([(220, 60, 50), (240, 200, 60), (120, 180, 70)])]   # frutero
    cv2.rectangle(i8, (1040, 600), (1062, 640), (230, 226, 214), -1)                                          # apagador
    plant(i8, 1040, 1290, 1.1)
    wf = i8.astype(np.float32); radial(wf, (540, 520), 700, (255, 190, 120), .3)
    back = [(dof(opaque(wf), 2.2), .45)]
    main = floor_layer(1300, (96, 66, 44), (80, 54, 36))
    rug = main.copy(); cv2.ellipse(rug, (540, 1700), (520, 170), 0, 0, 360, (130, 50, 46, 255), -1); cv2.ellipse(rug, (540, 1700), (470, 140), 0, 0, 360, (170, 120, 80, 255), 6)
    front = [(bokeh_layer(8, (255, 200, 140), 7, ymin=200, ymax=1200), 1.7)]
    return back, rug, front

def chair_back(fr, x, y, w=190, h=330, col=(110, 70, 44)):
    for sd in (-1, 1): cv2.rectangle(fr, (int(x + sd * w / 2 - 12), int(y)), (int(x + sd * w / 2 + 12), int(y + h)), col, -1)
    cv2.rectangle(fr, (int(x - w / 2 - 12), int(y - 10)), (int(x + w / 2 + 12), int(y + 26)), dark(col, 1.15) if False else col, -1)
    for k in range(3): cv2.rectangle(fr, (int(x - w / 2 + 20 + k * (w - 40) / 3 + 10), int(y + 26)), (int(x - w / 2 + 34 + k * (w - 40) / 3 + 10), int(y + h * .6)), dark(col, .85), -1)

def draw_table(fr, y=1330, x0=40, x1=1040, plates=((260, 1), (540, 1), (820, 1)), t=0.):
    poly(fr, [(x0, y), (x1, y), (x1 + 30, y + 60), (x0 - 30, y + 60)], (236, 232, 222))                      # mantel
    for k in range(int((x1 - x0) / 40) + 2): cv2.line(fr, (x0 - 30 + k * 40, y + 60), (x0 - 30 + k * 40, y + 110), (190, 60, 60) if k % 2 else (236, 232, 222), 20)
    cv2.rectangle(fr, (x0 - 30, y + 60), (x1 + 30, y + 110), (210, 70, 66), 3)
    cv2.rectangle(fr, (x0 - 20, y + 110), (x1 + 20, H), (70, 48, 32), -1)
    for (px, _) in plates:
        cv2.ellipse(fr, (px, y + 30), (92, 22), 0, 0, 360, (200, 196, 190), -1, cv2.LINE_AA); cv2.ellipse(fr, (px, y + 28), (88, 20), 0, 0, 360, (250, 250, 252), -1, cv2.LINE_AA)
        cv2.ellipse(fr, (px - 22, y + 26), (30, 9), 0, 0, 360, (246, 240, 220), -1, cv2.LINE_AA)               # arroz
        cv2.ellipse(fr, (px + 18, y + 26), (26, 10), 0, 0, 360, (170, 100, 50), -1, cv2.LINE_AA)               # pollo
        for k in range(4): cv2.circle(fr, (px + 40 + (k % 2) * 8, y + 20 + k * 3), 5, (90, 170, 80), -1)        # ensalada
        cv2.line(fr, (px - 110, y + 18), (px - 104, y + 46), (200, 200, 206), 4); cv2.line(fr, (px + 104, y + 18), (px + 110, y + 46), (200, 200, 206), 4)   # cubiertos
        poly(fr, [(px + 112, y + 20), (px + 150, y + 20), (px + 160, y + 48), (px + 118, y + 48)], (240, 236, 200))   # servilleta
    for gx in ([g for g in (380, 700) if x0 < g < x1 - 40] if x1 - x0 > 600 else [x1 - 90]):                    # vasos apoyados en el mantel
        gy = y + 44; cv2.ellipse(fr, (gx + 16, gy + 2), (24, 6), 0, 0, 360, (200, 196, 186), -1)
        poly(fr, [(gx, gy - 66), (gx + 34, gy - 66), (gx + 30, gy), (gx + 4, gy)], (190, 210, 228)); poly(fr, [(gx + 3, gy - 40), (gx + 31, gy - 40), (gx + 29, gy - 2), (gx + 5, gy - 2)], (150, 190, 230))
        cv2.line(fr, (gx + 8, gy - 60), (gx + 9, gy - 8), (250, 252, 255), 3); cv2.ellipse(fr, (gx + 17, gy - 66), (17, 4), 0, 0, 360, (220, 230, 240), 2)
    if x1 - x0 > 600:                                                                                          # jarra, pan, saleros y vela
        jx = x1 - 40
        poly(fr, [(jx - 30, y + 40), (jx + 30, y + 40), (jx + 36, y - 60), (jx - 36, y - 60)], (180, 210, 230)); poly(fr, [(jx - 28, y + 38), (jx + 28, y + 38), (jx + 32, y - 20), (jx - 32, y - 20)], (140, 190, 230))
        cv2.ellipse(fr, (jx - 40, y - 20), (14, 26), 0, 90, 270, (180, 210, 230), 6)
        bx = x0 + 70; cv2.ellipse(fr, (bx, y + 34), (56, 16), 0, 0, 360, (150, 100, 50), -1); [cv2.ellipse(fr, (bx - 25 + k * 25, y + 22), (20, 12), 0, 0, 360, (220, 170, 100), -1) for k in range(3)]
        for k, c_ in enumerate([(240, 240, 240), (60, 60, 64)]): cv2.rectangle(fr, (452 + k * 22, y + 14), (466 + k * 22, y + 44), c_, -1)
        for cx_ in (640, 660):
            cv2.rectangle(fr, (cx_ - 7, y - 26), (cx_ + 7, y + 38), (240, 236, 220), -1); fl = .8 + .2 * math.sin(t * 14 + cx_)
            ell(fr, (cx_, y - 36), 5 * fl, 11 * fl, 0, (255, 200, 90)); blit(fr, glow_sprite(44, (255, 180, 90)), cx_, y - 36, .5 * fl, add=True)

def lamp(fr, x=540, y=0, ly=420):
    line(fr, (x, y), (x, ly), (30, 30, 30), 4); poly(fr, [(x - 110, ly + 90), (x + 110, ly + 90), (x + 50, ly), (x - 50, ly)], (60, 40, 30))
    blit(fr, glow_sprite(140, (255, 200, 130)), x, ly + 100, .6, add=True)

def set_hall(door_x=760):
    i8 = np.zeros((H, W, 3), np.uint8)
    cv2.rectangle(i8, (0, 0), (W, 1000), (96, 92, 84), -1)
    for x in range(0, W, 70): cv2.rectangle(i8, (x, 0), (x + 35, 1000), (104, 100, 90), -1)                  # papel a rayas
    cv2.rectangle(i8, (0, 0), (W, 24), (150, 140, 120), -1)
    wainscot(i8, 1000, 1320, (120, 100, 80), panel=160)
    side = door_x < 600
    # puerta del sótano (opción B) al otro lado de la puerta principal
    bx = 60 if not side else W - 260
    cv2.rectangle(i8, (bx - 14, 560), (bx + 214, 1320), (70, 52, 38), -1); cv2.rectangle(i8, (bx, 576), (bx + 200, 1320), (96, 72, 52), -1)
    cv2.circle(i8, (bx + 170, 960), 12, (200, 170, 100), -1); blit(i8, N.text_sprite('SÓTANO', 22, (230, 220, 200, 255), pad=6), bx + 100, 640)
    # fotos, espejo, perchero, consola
    ox = 330 if not side else 60
    frame_pic(i8, ox, 330, 110, 140, content='familia'); frame_pic(i8, ox + 140, 360, 90, 90, content='abstracto', seed=2)
    cv2.ellipse(i8, (ox + 120, 640), (70, 100), 0, 0, 360, (150, 120, 70), -1); cv2.ellipse(i8, (ox + 120, 640), (58, 88), 0, 0, 360, (150, 170, 180), -1)
    cv2.line(i8, (ox + 90, 580), (ox + 120, 700), (210, 220, 228), 6)                                          # reflejo
    cv2.rectangle(i8, (ox + 20, 880), (ox + 220, 900), (100, 70, 46), -1); [cv2.line(i8, (q, 900), (q, 1100), (90, 62, 40), 8) for q in (ox + 30, ox + 210)]   # consola
    cv2.rectangle(i8, (ox + 40, 830), (ox + 70, 880), (220, 214, 200), -1); poly(i8, [(ox + 30, 800), (ox + 80, 800), (ox + 70, 830), (ox + 40, 830)], (240, 220, 170))   # lámpara
    cv2.ellipse(i8, (ox + 150, 872), (34, 10), 0, 0, 360, (90, 130, 160), -1); cv2.line(i8, (ox + 140, 866), (ox + 160, 860), (200, 200, 90), 3)   # llaves
    cx = door_x + (260 if not side else -260); cx = min(max(cx, 120), W - 120)
    if abs(cx - bx - 100) > 240:
        cv2.line(i8, (cx, 560), (cx, 1300), (90, 62, 40), 10); cv2.line(i8, (cx - 60, 1300), (cx + 60, 1300), (90, 62, 40), 10)   # perchero
        for k, col in enumerate([(60, 70, 110), (140, 60, 50), (70, 90, 60)]):
            poly(i8, [(cx - 20 + k * 20, 600), (cx + 20 + k * 20, 600), (cx + 50 + k * 20 - 40 * (k == 1), 900), (cx - 40 + k * 20, 900)], col)
        cv2.ellipse(i8, (cx, 560), (50, 18), 0, 0, 360, (70, 50, 36), -1)
    cv2.rectangle(i8, (door_x + 200, 600), (door_x + 250, 1260), (40, 40, 50), -1) if door_x + 250 < W else None   # ventanita lateral
    if door_x + 250 < W: cv2.rectangle(i8, (door_x + 206, 606), (door_x + 244, 1254), (150, 190, 160), -1)
    cv2.rectangle(i8, (door_x - 250, 760), (door_x - 228, 800), (230, 226, 214), -1)                          # apagador
    wf = i8.astype(np.float32); radial(wf, (ox + 55, 815), 300, (255, 200, 130), .35)
    back = [(dof(opaque(wf), 1.8), .45)]
    m = np.zeros((H, W, 3), np.uint8); al = np.zeros((H, W))
    cv2.rectangle(m, (door_x - 200, 510), (door_x + 200, 1320), (70, 48, 32), -1); al[510:1320, door_x - 200:door_x + 200] = 1     # marco
    cv2.rectangle(m, (door_x - 170, 540), (door_x + 170, 1320), (126, 82, 48), -1)
    for yy in (600, 900): cv2.rectangle(m, (door_x - 130, yy), (door_x + 130, yy + 230), (108, 70, 40), 6)
    cv2.line(m, (door_x - 150, 760), (door_x - 120, 790), (200, 200, 206), 4); cv2.line(m, (door_x - 120, 790), (door_x - 90, 760), (200, 200, 206), 4)   # cadena
    m[1320:] = (92, 66, 44); al[1320:] = 1
    for j in range(1, 9): y = int(1320 + (H - 1320) * (j / 8.) ** 1.6); cv2.line(m, (0, y), (W, y), (78, 56, 38), 2)
    for k in range(-10, 11): cv2.line(m, (540 + k * 70, 1320), (540 + k * 260, H), (80, 58, 40), 2)
    poly(m, [(door_x - 160, 1330), (door_x + 160, 1330), (door_x + 200, 1390), (door_x - 200, 1390)], (90, 70, 50))     # tapete
    blit(m, N.text_sprite('BIENVENIDOS', 22, (170, 140, 100, 255), pad=4), door_x, 1360)
    poly(m, [(200, 1420), (880, 1420), (1000, H), (80, H)], (120, 46, 44)); [cv2.line(m, (210 + k * 60, 1430), (100 + k * 80, H), (150, 70, 60), 3) for k in range(12)]   # alfombra
    for k, col in enumerate([(30, 30, 34), (140, 60, 50), (240, 240, 240)]): cv2.ellipse(m, (ox + 40 + k * 60, 1345), (24, 10), 0, 0, 360, col, -1)   # zapatos
    cv2.rectangle(m, (ox + 220, 1220), (ox + 260, 1330), (60, 60, 70), -1); [cv2.line(m, (ox + 230 + k * 10, 1220), (ox + 226 + k * 12, 1120), [(200, 40, 40), (40, 90, 170)][k % 2], 6) for k in range(3)]   # paragüero
    front = [(bokeh_layer(6, (255, 200, 140), 21, ymin=200, ymax=1100), 1.7)]
    return back, rgba(m, al), front

def door_parts(fr, door_x, t_knocks, t, lock_k=0.):
    """mirilla, perilla y cerrojo; la puerta tiembla con cada golpe y cae polvo."""
    sh = sum(math.exp(-((t - tk) / .05) ** 2) for tk in t_knocks) * 6
    off = A(math.sin(t * 90) * sh, 0)
    circ(fr, A(door_x, 820) + off, 13, (200, 180, 120)); circ(fr, A(door_x, 820) + off, 7, (30, 30, 34))           # mirilla
    circ(fr, A(door_x - 130, 1000) + off, 20, (210, 180, 110))                                                      # perilla
    cv2.rectangle(fr, (door_x - 150, 930), (door_x - 110, 960), (180, 150, 90), -1)                                  # cerrojo
    a_ = lock_k * math.pi / 2; c = A(door_x - 130, 945) + off
    line(fr, c - A(math.cos(a_), math.sin(a_)) * 16, c + A(math.cos(a_), math.sin(a_)) * 16, (90, 70, 40), 7)
    for tk in t_knocks:
        f = t - tk
        if 0 < f < 1.2:
            for i in range(8):
                x = door_x - 160 + (i * 47) % 330; y = 540 + f * 400 + (i % 3) * 30
                circ(fr, (x, y), 2.5, (220, 200, 170))
    lt = .6 + .4 * math.sin(t * 7) * (1 if any(0 < t - tk < .6 for tk in t_knocks) else 0)
    cv2.rectangle(fr, (door_x - 170, 1312), (door_x + 170, 1320), (int(255 * lt), int(220 * lt), int(150 * lt)), -1)

# ---------------------------------------------------------------- más escenarios con detalle
def set_hospital():
    sky = vgrad([(0, (6, 8, 22)), (1, (26, 30, 52))]); back = [(dof(opaque(sky), 2), .1)]
    m = np.zeros((H, W, 3), np.uint8); r_ = np.random.RandomState(4)
    cv2.rectangle(m, (-10, 420), (W + 10, 1420), (186, 192, 202), -1)
    for r in range(5):
        for c in range(6):
            x0_, y0_ = 40 + c * 175, 470 + r * 130; lit = (r + c) % 3 != 0
            cv2.rectangle(m, (x0_, y0_), (x0_ + 110, y0_ + 90), (255, 240, 200) if lit else (110, 140, 170), -1); cv2.rectangle(m, (x0_, y0_), (x0_ + 110, y0_ + 90), (150, 156, 166), 4)
            if lit and r_.rand() < .35: cv2.circle(m, (x0_ + 55, y0_ + 40), 14, (90, 150, 140), -1); cv2.rectangle(m, (x0_ + 40, y0_ + 55), (x0_ + 70, y0_ + 90), (90, 150, 140), -1)   # personal en ventanas
    cv2.rectangle(m, (250, 1110), (830, 1150), (200, 40, 50), -1)                                              # marquesina URGENCIAS
    cv2.rectangle(m, (300, 1150), (780, 1420), (130, 200, 225), -1); cv2.line(m, (540, 1150), (540, 1420), (110, 120, 130), 8); cv2.rectangle(m, (300, 1150), (780, 1420), (100, 106, 116), 10)
    for k in range(3): cv2.rectangle(m, (330 + k * 150, 1300), (380 + k * 150, 1420), (70, 110, 140), -1)    # siluetas adentro
    for x in (180, 900): cv2.ellipse(m, (x, 1400), (80, 40), 0, 180, 360, (50, 100, 60), -1)                  # arbustos
    m[1420:] = (44, 44, 50); [cv2.line(m, (x, 1440), (x + 140, 1900), (220, 200, 90), 6) for x in range(-200, W, 260)]   # bahía de ambulancias
    cv2.line(m, (1000, 1420), (1000, 300), (160, 160, 166), 6); cv2.rectangle(m, (1004, 310), (1074, 356), (40, 80, 160), -1)   # asta y bandera
    al = np.zeros((H, W)); al[420:] = 1
    return back, rgba(m, al), [(bokeh_layer(10, (255, 80, 60), 31, ymin=300, ymax=1500), 1.7)]

def set_corridor():
    m = np.zeros((H, W, 3), np.uint8); m[:] = (190, 200, 196); vx, vy = 540, 980
    poly(m, [(0, 0), (W, 0), (vx + 120, vy - 120), (vx - 120, vy - 120)], (222, 228, 226)); poly(m, [(0, H), (W, H), (vx + 120, vy + 120), (vx - 120, vy + 120)], (150, 168, 164))
    poly(m, [(0, 0), (vx - 120, vy - 120), (vx - 120, vy + 120), (0, H)], (176, 192, 190)); poly(m, [(W, 0), (vx + 120, vy - 120), (vx + 120, vy + 120), (W, H)], (170, 186, 184))
    cv2.rectangle(m, (vx - 120, vy - 120), (vx + 120, vy + 120), (90, 110, 120), -1); cv2.rectangle(m, (vx - 60, vy - 80), (vx + 60, vy + 120), (60, 80, 90), -1)
    P = lambda f, side, yv: (int(lerp_(0 if side < 0 else W, vx + side * 120, f)), int(lerp_(H * (yv) if True else 0, vy + (yv - .5) * 240, f)))
    for k in range(5):                                                                                            # puertas con número, a ambos lados
        f0, f1 = .1 + k * .17, .18 + k * .17
        for side in (-1, 1):
            q = [P(f0, side, .28), P(f1, side, .32), P(f1, side, .56), P(f0, side, .62)]
            cv2.fillPoly(m, [np.array(q, np.int32)], (120, 150, 170) if k % 2 else (140, 120, 100), cv2.LINE_AA)
            cv2.circle(m, ((q[0][0] + q[1][0]) // 2, (q[0][1] + q[1][1]) // 2 + 40 - k * 6), max(3, 12 - k * 2), (240, 240, 240), -1)
    for side in (-1, 1): cv2.line(m, P(0, side, .5), P(.95, side, .5), (120, 130, 136), 8)                    # pasamanos
    for k in range(5):
        f = (k + 1) / 6.; y = int(lerp_(0, vy - 120, f ** .6)); x0 = int(lerp_(0, vx - 120, f ** .6)); x1 = W - x0
        cv2.rectangle(m, (x0 + 60, y - 6), (x1 - 60, y + 6), (250, 252, 255), -1)
    cv2.rectangle(m, (380, 330), (700, 400), (40, 120, 90), -1)
    cv2.rectangle(m, (40, 1240), (90, 1360), (200, 40, 40), -1); cv2.rectangle(m, (52, 1220), (78, 1244), (40, 40, 44), -1)   # extintor
    cv2.rectangle(m, (W - 150, 1260), (W - 30, 1300), (90, 110, 150), -1); [cv2.rectangle(m, (W - 150 + k * 42, 1300), (W - 140 + k * 42, 1400), (70, 70, 80), -1) for k in range(3)]   # sillas
    cv2.rectangle(m, (150, 800), (260, 920), (240, 240, 230), -1); [cv2.line(m, (160, 820 + k * 18), (250, 820 + k * 18), (120, 120, 130), 3) for k in range(5)]   # cartel informativo
    img = to8(m.astype(np.float32)); blit(img, N.text_sprite('URGENCIAS  →', 36, (255, 255, 255, 255), pad=6, spacing=4), 540, 365)
    return [(dof(opaque(img.astype(np.float32)), 1.2), .5)], np.zeros((H, W, 4), np.uint8), [(bokeh_layer(6, (220, 255, 240), 41, ymin=100, ymax=600), 1.6)]
def lerp_(a, b, k): return a + (b - a) * k

def set_livingtv():
    i8 = np.zeros((H, W, 3), np.uint8); wallpaper(i8, 0, 0, W, 1300, (60, 50, 50), (70, 58, 56)); wainscot(i8, 1300, 1500, (80, 60, 46))
    frame_pic(i8, 120, 220, 220, 160, content='abstracto', seed=5); frame_pic(i8, 760, 240, 180, 140, content='paisaje')
    cv2.rectangle(i8, (150, 1190), (930, 1460), (70, 46, 30), -1); [cv2.rectangle(i8, (180 + k * 250, 1230), (380 + k * 250, 1430), (60, 40, 26), 6) for k in range(3)]   # mueble de TV
    for x in (60, 970): cv2.rectangle(i8, (x - 40, 900), (x + 40, 1190), (30, 30, 34), -1); cv2.circle(i8, (x, 980), 26, (60, 60, 66), -1); cv2.circle(i8, (x, 1100), 34, (60, 60, 66), -1)   # bocinas
    plant(i8, 1000, 1190, .9, seed=9); cv2.rectangle(i8, (640, 1170), (700, 1190), (30, 30, 34), -1)          # control
    img = i8.astype(np.float32); return [(dof(opaque(img), 2.5), .4)], floor_layer(1500, (80, 56, 40), (66, 46, 32)), [(bokeh_layer(6, (120, 160, 255), 51, ymin=300, ymax=1500), 1.6)]

def set_porch():
    """lo que se ve por la mirilla: porche con lámpara, barandal, escalones y la calle oscura con un auto en llamas a lo lejos."""
    img = np.zeros((H, W, 3), np.uint8); img[:] = (14, 20, 18)
    for y in range(0, 1200, 46): cv2.rectangle(img, (0, y), (W, y + 40), (34, 44, 38), -1)                     # tablas de la fachada
    cv2.rectangle(img, (0, 1200), (W, 1350), (8, 10, 12), -1); blit(img, glow_sprite(220, (255, 120, 40)), 860, 1260, .55, add=True)   # calle y auto en llamas
    cv2.rectangle(img, (0, 1350), (W, H), (44, 50, 42), -1); [cv2.line(img, (0, y), (W, y), (34, 40, 34), 3) for y in range(1380, H, 60)]
    for x in range(0, W, 90): cv2.rectangle(img, (x, 1150), (x + 20, 1360), (70, 80, 66), -1)
    cv2.rectangle(img, (0, 1140), (W, 1166), (80, 90, 76), -1)
    cv2.rectangle(img, (470, 220), (610, 330), (40, 40, 36), -1); cv2.circle(img, (540, 360), 40, (230, 255, 220), -1)   # lámpara del porche
    plant(img, 140, 1500, 1.4, pot=(90, 70, 50), leaf=(40, 80, 50), seed=11)
    return img
