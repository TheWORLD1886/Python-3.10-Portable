#!/usr/bin/env python3
# Escenarios, utilería y utilidades de animación del episodio 01 (capas con profundidad para render3d).
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'chapo')); sys.path.insert(0, HERE)
import narco_short as N
from narco3d import dof, rgba, haze, bokeh_layer, render3d, cinema, vgrad, radial, beam, glow_sprite, W, H, FPS, to8, blit, sub_sprite
from rig import *

rng = np.random.RandomState(11)
def opaque(img): return rgba(img, np.ones((H, W)))
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

# ---------------------------------------------------------------- escenarios (capas)
def set_street(shop_open=True, seed=3):
    sky = vgrad([(0, (6, 8, 20)), (.55, (22, 24, 46)), (1, (40, 30, 40))])
    for i in range(160): x, y = rng.randint(0, W), rng.randint(0, 700); sky[y:y + 2, x:x + 2] += rng.uniform(40, 140)
    back = [(dof(opaque(sky), 2), .1)]
    far = np.zeros((H, W, 3), np.uint8); r_ = np.random.RandomState(seed); x = -20
    while x < W:
        bw, bh = r_.randint(90, 170), r_.randint(300, 650); cv2.rectangle(far, (x, 1120 - bh), (x + bw, 1130), (30, 28, 40), -1)
        for wy in range(1120 - bh + 20, 1110, 34):
            for wx in range(x + 12, x + bw - 16, 26):
                if r_.rand() < .35: cv2.rectangle(far, (wx, wy), (wx + 12, wy + 16), (255, 196, 120), -1)
        x += bw + r_.randint(4, 14)
    back.append((dof(haze(layer_from(far), (40, 30, 40), .35), 2.5), .4))
    m = np.zeros((H, W, 3), np.uint8)
    cv2.rectangle(m, (-10, 760), (W + 10, 1360), (70, 56, 52), -1)                                     # fachada de la tienda
    for x in range(-10, W, 46): cv2.line(m, (x, 760), (x, 1360), (62, 50, 46), 2)
    cv2.rectangle(m, (120, 1000), (560, 1330), (255, 220, 160) if shop_open else (40, 40, 50), -1)     # vitrina
    for k in range(4): cv2.rectangle(m, (150 + k * 100, 1080), (220 + k * 100, 1300), (220, 150, 90), -1)
    cv2.rectangle(m, (640, 1010), (820, 1340), (40, 30, 26), -1); cv2.rectangle(m, (650, 1020), (810, 1340), (255, 214, 150), -1)    # puerta (hueco)
    cv2.rectangle(m, (100, 860), (980, 960), (24, 20, 30), -1)
    m2 = m.copy(); txt = N.text_sprite('MINI MARKET · 24 H', 64, (255, 90, 120, 255), glow=(255, 60, 120), glow_r=14, spacing=6)
    m[:] = to8(m.astype(np.float32)); blit(m, txt, 540, 910)
    cv2.rectangle(m, (-10, 1360), (W + 10, 1500), (88, 86, 92), -1)                                    # banqueta
    for x in range(0, W, 140): cv2.line(m, (x, 1360), (x - 30, 1500), (70, 68, 74), 3)
    cv2.rectangle(m, (-10, 1500), (W + 10, H), (34, 34, 40), -1)                                       # calle
    for x in range(0, W, 220): cv2.rectangle(m, (x, 1720), (x + 120, 1736), (230, 210, 120), -1)
    al = np.zeros((H, W)); al[760:] = 1
    front = [(bokeh_layer(10, (255, 200, 130), seed + 40, ymin=300, ymax=1300), 1.7)]
    return back, rgba(m, al), front

def set_dining():
    i8 = walls((40, 30, 28), (78, 58, 46), (44, 32, 26), 1300)
    for x in range(0, W, 64): cv2.line(i8, (x, 0), (x, 1300), (70, 52, 42), 2)
    cv2.rectangle(i8, (700, 420), (1000, 900), (16, 24, 44), -1); cv2.rectangle(i8, (700, 420), (1000, 900), (120, 90, 60), 14); cv2.line(i8, (850, 420), (850, 900), (120, 90, 60), 8)
    for (x, y) in [(740, 760), (790, 700), (880, 780), (960, 720), (930, 640)]: cv2.circle(i8, (x, y), 4, (255, 210, 140), -1)
    for (x, y, w, h) in [(100, 380, 180, 230), (320, 470, 140, 110)]:
        cv2.rectangle(i8, (x, y), (x + w, y + h), (150, 120, 70), 10); cv2.rectangle(i8, (x + 10, y + 10), (x + w - 10, y + h - 10), (90, 110, 120), -1)
    cv2.rectangle(i8, (0, 1240), (W, 1300), (90, 66, 48), -1)
    wf = i8.astype(np.float32); radial(wf, (540, 500), 650, (255, 190, 120), .3)
    back = [(dof(opaque(wf), 2.5), .45)]
    main = floor_layer(1300, (96, 66, 44), (80, 54, 36))
    front = [(bokeh_layer(8, (255, 200, 140), 7, ymin=200, ymax=1200), 1.7)]
    return back, main, front

def draw_table(fr, y=1330, x0=40, x1=1040, plates=((260, 1), (540, 1), (820, 1))):
    poly(fr, [(x0, y), (x1, y), (x1 + 30, y + 60), (x0 - 30, y + 60)], (150, 110, 74)); cv2.rectangle(fr, (x0 - 30, y + 60), (x1 + 30, y + 90), (110, 76, 50), -1)
    cv2.rectangle(fr, (x0 - 20, y + 90), (x1 + 20, H), (70, 48, 32), -1)
    for (px, _) in plates:
        cv2.ellipse(fr, (px, y + 26), (90, 22), 0, 0, 360, (236, 236, 240), -1, cv2.LINE_AA); cv2.ellipse(fr, (px, y + 24), (60, 13), 0, 0, 360, (200, 120, 70), -1, cv2.LINE_AA)
    for gx in (390, 690):
        poly(fr, [(gx, y - 50), (gx + 34, y - 50), (gx + 30, y + 16), (gx + 4, y + 16)], (150, 170, 190)); poly(fr, [(gx + 4, y - 20), (gx + 30, y - 20), (gx + 30, y + 14), (gx + 4, y + 14)], (200, 120, 70))

def lamp(fr, x=540, y=0, ly=420):
    line(fr, (x, y), (x, ly), (30, 30, 30), 4); poly(fr, [(x - 110, ly + 90), (x + 110, ly + 90), (x + 50, ly), (x - 50, ly)], (60, 40, 30))
    blit(fr, glow_sprite(140, (255, 200, 130)), x, ly + 100, .6, add=True)

def set_hall(door_x=760):
    i8 = walls((36, 32, 34), (66, 56, 52), (38, 32, 30), 1320)
    for x in range(0, W, 80): cv2.line(i8, (x, 0), (x, 1320), (58, 50, 46), 2)
    cv2.rectangle(i8, (0, 1260), (W, 1320), (80, 62, 50), -1)
    wf = i8.astype(np.float32); radial(wf, (300, 400), 500, (255, 190, 120), .18)
    back = [(dof(opaque(wf), 2), .45)]
    m = np.zeros((H, W, 3), np.uint8); al = np.zeros((H, W))
    cv2.rectangle(m, (door_x - 190, 520), (door_x + 190, 1320), (60, 40, 28), -1); al[520:1320, door_x - 190:door_x + 190] = 1   # marco
    cv2.rectangle(m, (door_x - 170, 540), (door_x + 170, 1320), (120, 78, 46), -1)
    for (yy) in (600, 900): cv2.rectangle(m, (door_x - 130, yy), (door_x + 130, yy + 230), (104, 66, 38), 6)
    m[1320:] = (90, 64, 44); al[1320:] = 1
    for j in range(1, 9): y = int(1320 + (H - 1320) * (j / 8.) ** 1.6); cv2.line(m, (0, y), (W, y), (76, 54, 36), 2)
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
