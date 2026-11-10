#!/usr/bin/env python3
# Short: ¿Y si el Cártel de Sinaloa lo sacara de máxima seguridad? (60 s, 1080x1920) · estilo plantilla + profundidad 3D
import chapo as CH
from chapo import *
import json

DUR = 60
VOZ = os.path.join(HERE, 'voz_rescate.mp3')
SC_T = [0, 8, 20, 35, 48, DUR]          # se recalculan con la voz final
SUBS = []                               # se generan con los tiempos de la voz (ver build_subs_from_words)
EMOJIS = [
 (2.5, 7.8, '🚨', 880, 900, 150, 'late'), (5.5, 7.8, '🔥', 200, 900, 150, 'late'),
 (9.0, 12.0, '🚁', 860, 1180, 150, 'sacude'), (12.5, 16.0, '💻', 200, 1180, 150, 'sacude'),
 (21.5, 25.0, '👑', 880, 760, 150, 'pop'), (29.0, 33.0, '🗺️', 200, 760, 150, 'late'),
 (36.0, 39.0, '⚠️', 880, 760, 150, 'cae'), (42.0, 46.0, '⚔️', 200, 760, 150, 'cae'),
 (50.0, 60, '💬', 180, 380, 140, 'late'), (54.0, 60, '👍', 540, 300, 150, 'pop'), (55.0, 60, '🔔', 900, 380, 140, 'sacude'),
]

def red_panel(title, w=820, h=200):
    return N.holo_panel(w, h, title, None, col=(255, 70, 60), fill=(50, 6, 6, 200))

# ================================================================ 1 · Celda de máxima seguridad en una noche de tormenta
class R1:
    def __init__(s):
        sky = vgrad([(0, (6, 8, 16)), (.5, (18, 22, 36)), (1, (26, 30, 44))])
        s.back = [(dof(rgba(sky, np.ones((H, W))), 2), .1)]
        cl_ = np.zeros((H, W, 4), np.uint8); r_ = np.random.RandomState(5)
        for i in range(40):
            x, y = r_.uniform(-100, W + 100), r_.uniform(40, 700); cv2.ellipse(cl_, (int(x), int(y)), (int(r_.uniform(120, 260)), int(r_.uniform(40, 90))), 0, 0, 360, (34, 38, 52, 200), -1, cv2.LINE_AA)
        s.clouds = dof(cl_, 14)
        t3 = np.zeros((H, W, 3), np.uint8)
        for (x, top) in [(160, 520), (900, 470)]:
            cv2.rectangle(t3, (x - 26, top), (x + 26, 1180), (52, 56, 64), -1); cv2.rectangle(t3, (x - 70, top - 70), (x + 70, top), (60, 64, 72), -1)
            cv2.rectangle(t3, (x - 56, top - 56), (x + 56, top - 20), (255, 220, 160), -1)
        cv2.rectangle(t3, (0, 1060), (W, 1180), (48, 52, 60), -1); fence(t3, 1000, 1080)
        tw = rgba(t3, np.any(t3 > 0, 2).astype(np.float32))
        s.back.append((dof(haze(tw, (20, 24, 36), .3), 2), .45))
        s.towers = [(160, 470), (900, 420)]
        # pared de la celda con ventana blindada (plano principal)
        wall = np.zeros((H, W, 3), np.uint8); wall[:] = (70, 72, 78); al = np.ones((H, W))
        wall += np.random.RandomState(2).normal(0, 4, (H, W, 1)).clip(-8, 8).astype(np.uint8)
        cv2.rectangle(wall, (180, 300), (900, 1150), (30, 32, 36), 30); al[315:1136, 195:886] = 0           # hueco de la ventana
        for y in (590, 860): wall[y - 6:y + 6, 195:886] = (40, 42, 46); al[y - 6:y + 6, 195:886] = 1
        wall[1150:] = (54, 56, 62)
        for j in range(1, 8): y = int(1150 + (H - 1150) * (j / 7.) ** 1.6); cv2.line(wall, (0, y), (W, y), (64, 66, 72), 2)
        s.main = rgba(wall, al)
        s.glass = np.zeros((H, W, 4), np.uint8); cv2.rectangle(s.glass, (195, 315), (886, 1136), (120, 160, 200, 34), -1)
        for k in range(6): cv2.line(s.glass, (200 + k * 140, 320), (320 + k * 140, 1130), (200, 230, 255, 40), 6, cv2.LINE_AA)
        bars = np.zeros((H, W, 4), np.uint8)
        for x in list(range(-30, 200, 70)) + list(range(900, W + 40, 70)): cv2.rectangle(bars, (x, 0), (x + 34, H), (60, 64, 72, 255), -1); cv2.rectangle(bars, (x + 6, 0), (x + 13, H), (140, 146, 156, 255), -1)
        s.front = [(dof(bars, 12), 1.55), (bokeh_layer(14, (255, 90, 60), 9, rmin=20, rmax=60, ymin=200, ymax=1700), 1.75)]
        s.title = red_panel('OPERACIÓN RESCATE')
        s.dust = Dust(36, (40, 300, 1040, 1600), (200, 210, 255), 4, .4)
    def draw(s, fr, t, d):
        # nubes que avanzan + rayos (detrás de la ventana: se dibujan solo dentro del hueco)
        win = fr[315:1136, 195:886]
        cl = np.roll(s.clouds, int(t * 40) % W, axis=1)[315:1136, 195:886]
        a = cl[:, :, 3:4] / 255.; win[:] = to8(win * (1 - a * .7) + cl[:, :, :3] * a * .7)
        for tb in (1.2, 4.6, 6.9):
            if tb <= t < tb + .35:
                k = 1 - (t - tb) / .35; win[:] = np.clip(win.astype(np.float32) + 120 * k, 0, 255).astype(np.uint8)
                xs = 300 + (tb * 97) % 400; pts = [(xs, 320)]
                for i in range(7): pts.append((pts[-1][0] + ((i * 53 + int(tb * 10)) % 60 - 30), pts[-1][1] + 70))
                pline(fr, pts, (230, 240, 255), 5 * k + 1)
        for i, (x, y) in enumerate(s.towers):   # reflectores rojo/blanco en las torres
            on = ((t * 1.6 + i * .5) % 1) < .5
            if 195 < x < 886: blit(fr, glow_sprite(70, (255, 50, 40) if on else (240, 240, 255)), x, y - 40, .8, add=True)
        blit(fr, s.glass, W / 2, H / 2)
        s.dust.draw(fr, t)
        cv2.ellipse(fr, (560, 1584), (170, 22), 0, 0, 360, (30, 30, 34), -1, cv2.LINE_AA)
        character(fr, 'reo', 560, 1580, 520, t, armR=('jarra',), armL=('jarra',), look=(-.5, -.6), frown=-.1, smile=.35 + .2 * ss(5, 6, t), mustache=True)
        k = ss(1.8, 2.3, t)
        if k > 0: blit(fr, s.title, 540, 360 + math.sin(t * 1.5) * 5, k * (.88 + .12 * math.sin(t * 5)), lerp(1.3, 1, eOut((t - 1.8) / .5)))
    def cam(s, t, d):
        k = eExpo(t / 1.5)
        return lerp(2.2, 1.05, k) * (1 + .06 * ss(1.5, d, t)), 560, lerp(1300, 1000, k), lerp(-40, 40, eIO(t / d)) * ss(1, 2.5, t), 0

# ================================================================ 2 · Centro de mando: hackeo, apagón y helicópteros
class R2:
    def __init__(s):
        r_ = np.random.RandomState(7)
        bg = vgrad([(0, (2, 8, 6)), (1, (4, 12, 10))]); i8 = to8(bg)
        f = font(22, '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'); im = Image.fromarray(i8); dd = ImageDraw.Draw(im)
        for (x, y, w, h) in [(30, 120, 320, 420), (380, 80, 320, 420), (730, 120, 320, 420), (30, 580, 320, 380), (730, 580, 320, 380)]:
            dd.rectangle((x, y, x + w, y + h), fill=(4, 22, 12), outline=(60, 200, 110), width=4)
            for ly in range(y + 12, y + h - 20, 26): dd.text((x + 12, ly), ''.join(r_.choice(['0', '1']) for _ in range(20)), font=f, fill=(60, 220, 120))
        bgf = np.array(im).astype(np.float32); radial(bgf, (540, 500), 700, (40, 200, 120), .12)
        s.back = [(dof(rgba(bgf, np.ones((H, W))), 4), .3)]
        # plano holográfico de la prisión (se "hackea" por zonas)
        s.cells = [(x, y) for y in range(0, 4) for x in range(0, 6)]
        s.bx, s.by, s.cw, s.ch = 190, 760, 117, 95
        floor = np.zeros((H, W, 3), np.uint8); floor[1250:] = (10, 18, 16)
        for j in range(1, 9): y = int(1250 + (H - 1250) * (j / 8.) ** 1.6); cv2.line(floor, (0, y), (W, y), (20, 50, 36), 2)
        for k in range(-10, 11): cv2.line(floor, (540, 1250), (540 + k * 220, H), (18, 44, 32), 2)
        al = np.zeros((H, W)); al[1250:] = 1; s.main = rgba(floor, al)
        mon = np.zeros((H, W, 4), np.uint8)
        for (x, w) in [(-60, 380), (760, 380)]:
            cv2.rectangle(mon, (x, 1560), (x + w, 1840), (20, 24, 26, 255), -1); cv2.rectangle(mon, (x + 20, 1580), (x + w - 20, 1820), (12, 50, 30, 255), -1)
        s.front = [(dof(mon, 11), 1.5), (bokeh_layer(16, (60, 220, 140), 10, rmin=10, rmax=40, ymin=100, ymax=1500), 1.7)]
        s.codes = N.holo_panel(620, 240, 'ACCESO 7-ALFA', '0x4F·AC·91·3E · NIVEL 5', col=(90, 255, 160), fill=(4, 40, 22, 190))
        s.stamp = N.stamp('INFILTRADO', (255, 59, 42), w=680, px=90)
        s.dust = Dust(40, (40, 200, 1040, 1500), (90, 255, 160), 3, .5)
    def draw(s, fr, t, d):
        # plano de la prisión: celdas que se apagan una por una (apagón) mientras una barra de escaneo lo recorre
        cut = ss(4.0, 9.0, t)
        for i, (cx, cy) in enumerate(s.cells):
            x0, y0 = s.bx + cx * s.cw, s.by + cy * s.ch; off = (i / len(s.cells)) < cut
            col = (40, 80, 60) if off else (90, 255, 170)
            cv2.rectangle(fr, (x0 + 4, y0 + 4), (x0 + s.cw - 4, y0 + s.ch - 4), col, 2)
            if not off: cv2.rectangle(fr, (x0 + 30, y0 + 30), (x0 + 50, y0 + 46), (90, 255, 170), -1)
            else: cv2.rectangle(fr, (x0 + 30, y0 + 30), (x0 + 50, y0 + 46), (255, 60, 40), -1)
        cv2.rectangle(fr, (s.bx, s.by), (s.bx + 6 * s.cw, s.by + 4 * s.ch), (90, 255, 170), 3)
        sy = s.by + ((t * .6) % 1) * 4 * s.ch; cv2.line(fr, (s.bx - 10, int(sy)), (s.bx + 6 * s.cw + 10, int(sy)), (255, 80, 60), 4)
        lbl = N.text_sprite('PLANO · PENAL FEDERAL', 30, (150, 255, 200, 255), spacing=4, pad=10); blit(fr, lbl, 540, s.by - 30)
        a = ss(1.0, 1.6, t) * (1 - ss(7.0, 7.4, t))
        if a > 0: blit(fr, s.codes, 540, 520 + math.sin(t * 1.5) * 5, a)
        # helicópteros tácticos con láser hacia abajo
        for i, (dx, dy) in enumerate([(0, 0), (260, -90)]):
            x = lerp(1300, -300, (t - 2 + i * .4) / 9.); y = 470 + dy + math.sin(t * 1.2 + i) * 10
            for k in (-1, 1): line(fr, (x - 10, y + 28), (x + k * 140 + 60, 1250), (255, 40, 40), 2)
            CH.heli(fr, x, y, 1.7 - .4 * i, t + i, col=(70, 78, 72))
        s.dust.draw(fr, t)
        k = ss(9.6, 9.9, t)
        if k > 0: blit(fr, s.stamp, 540, 520, k, lerp(1.6, 1., eOut(k)))
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.04, 1.12, k), 540, lerp(900, 1000, k), lerp(-50, 50, k), 0

# ================================================================ 3 · Poder total: el mapa se tiñe de rojo
class R3(D.S3D):
    def __init__(s):
        super().__init__()
        r_ = np.random.RandomState(4)
        s.cd = prj(-104.0, 23.5)
        s.arrows = []
        # puntos de control que aparecen y se expanden (ciudades principales del país)
        s.pts = [(-107.39, 24.8), (-106.4, 23.2), (-103.35, 20.66), (-100.31, 25.69), (-99.13, 19.43), (-106.45, 31.69), (-117.04, 32.52),
                 (-110.95, 29.07), (-104.66, 24.02), (-101.0, 22.15), (-96.13, 19.17), (-97.5, 25.87), (-92.93, 17.99), (-89.62, 20.97), (-86.85, 21.16), (-98.2, 19.04)]
        s.ord = r_.permutation(len(s.pts)); s.dotg = glow_sprite(80, (255, 40, 30))
        s.title = red_panel('PODER TOTAL', w=640, h=170)
        cta = np.zeros((120, 560, 4), np.uint8); im = Image.fromarray(cta); dd = ImageDraw.Draw(im)
        dd.rounded_rectangle((4, 4, 555, 115), 56, fill=(200, 20, 20, 230), outline=(255, 255, 255, 255), width=4); cta = np.array(im)
        over(cta, N.text_sprite('DALE LIKE · SÍGUEME', 40, (255, 255, 255, 255), spacing=3, pad=10), 300, 60)
        over(cta, cv2.resize(emoji_sprite('👍'), (76, 76)), 62, 60); s.cta = cta; s.bell = emoji_sprite('🔔')
    def draw(s, fr, t, d):
        pul = .5 + .5 * math.sin(t * 4)
        blit(fr, s.gl, s.glc[0], s.glc[1], .15 + .4 * pul, add=True)
        for n, i in enumerate(s.ord):    # el control se expande
            t0 = 2.5 + n * .55
            if t < t0: continue
            x, y = prj(*s.pts[i]); g = ss(t0, t0 + 1.2, t)
            ov_ = fr.copy(); cv2.circle(ov_, (int(x), int(y)), int(18 + 42 * g), (170, 24, 18), -1, cv2.LINE_AA); fr[:] = cv2.addWeighted(fr, .45, ov_, .55, 0)
            blit(fr, s.dotg, x, y, .5 + .4 * pul, add=True); circ(fr, (x, y), 9, (255, 220, 200))
            f = (t * .7 + n * .13) % 1; cv2.circle(fr, (int(x), int(y)), int(20 + f * 70), (int(255 * (1 - f)), int(60 * (1 - f)), int(40 * (1 - f))), 3, cv2.LINE_AA)
    def floating(s, fr, t, d, P):
        cv2.ellipse(fr, (250, 1604), (150, 20), 0, 0, 360, (6, 8, 12), -1, cv2.LINE_AA)
        character(fr, 'civil', 250, 1600, 470, t, armR=('apunta', (600, 1050), ss(1.0, 1.8, t) * (1 - ss(8, 8.6, t))), armL=('jarra',),
                  look=(.7, -.4), frown=-.2, smile=.35, mustache=True, cap=True)
        k = ss(10.5, 10.9, t)
        if k > 0: blit(fr, s.title, 540, 360 + math.sin(t * 1.6) * 5, k * (.86 + .14 * math.sin(t * 5)), lerp(1.5, 1., eOut(k)))
        c = ss(4.0, 4.4, t) * (1 - ss(9.5, 9.9, t))       # llamada a la acción a mitad de video (abajo a la derecha)
        if c > 0:
            blit(fr, s.cta, 760, 1720, c, lerp(.6, 1, eBack((t - 4.0) / .4)) * .62)
            blit(fr, s.bell, 960, 1700 + math.sin(t * 9) * 4 * c, c, .42)
        s.dust.draw(fr, t)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.35, 1.18, eOut(t / 3)) * (1 + .05 * k), 520, 1180, lerp(-40, 40, k), 0

# ================================================================ 4 · Guerra total: convoyes, soldados y drones
class R4(D.S4D):
    def __init__(s):
        super().__init__()
        s.stamp = N.stamp('ALERTA MÁXIMA', (255, 59, 42), w=760, px=84)
        s.dust2 = Dust(50, (40, 200, 1040, 1700), (255, 200, 120), 5, .7)
    def drone(s, fr, x, y, sc, t):
        line(fr, (x - 60 * sc, y), (x + 60 * sc, y), (40, 44, 48), 8 * sc)
        for k in (-1, 1):
            line(fr, (x + k * 60 * sc, y - 4 * sc), (x + k * 60 * sc, y - 14 * sc), (40, 44, 48), 4 * sc)
            cv2.ellipse(fr, P8((x + k * 60 * sc, y - 16 * sc)), (int(34 * sc * 8), int(5 * sc * 8)), 0, 0, 360, (90, 94, 100), 1, cv2.LINE_AA, 3)
        cv2.ellipse(fr, P8((x, y + 6 * sc)), (int(26 * sc * 8), int(14 * sc * 8)), 0, 0, 360, (30, 34, 38), -1, cv2.LINE_AA, 3)
        circ(fr, (x, y + 14 * sc), 7 * sc, (255, 40, 40))
        lay = np.zeros((H // 4, W // 4, 3), np.float32)
        cv2.fillPoly(lay, [np.array([(int(x / 4), int((y + 14 * sc) / 4)), (int((x - 90 * sc) / 4), int((y + 500 * sc) / 4)), (int((x + 90 * sc) / 4), int((y + 500 * sc) / 4))], np.int32)], (255, 40, 30))
        fr[:] = np.clip(fr + cv2.resize(cv2.GaussianBlur(lay, (0, 0), 4), (W, H)) * .25, 0, 255).astype(np.uint8)
    def mrap(s, fr, x, y, sc):  # vehículo blindado militar
        w, h = 300 * sc, 120 * sc
        poly(fr, [(x, y - h * .2), (x + w * .1, y - h), (x + w * .7, y - h), (x + w * .8, y - h * .7), (x + w, y - h * .6), (x + w, y), (x, y)], (58, 64, 50))
        poly(fr, [(x + w * .55, y - h * .92), (x + w * .68, y - h * .92), (x + w * .76, y - h * .66), (x + w * .55, y - h * .66)], (30, 40, 46))
        for wx in (x + w * .2, x + w * .78): circ(fr, (wx, y), 32 * sc, (14, 14, 16)); circ(fr, (wx, y), 14 * sc, (80, 84, 74))
        blit(fr, glow_sprite(30, (255, 240, 200)), x + w, y - h * .45, .8, sc, add=True)
    def draw(s, fr, t, d):
        super().draw(fr, t, d)     # humo, fuego, sirenas y el panel de territorios del original
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.04, 1.12, k), 540, lerp(1050, 1120, k), lerp(-60, 60, k), 0

def r4_draw(s, fr, t, d):
    # humo y fuego del original (sin panel de territorios ni personaje)
    for i, (ph0, src, dx) in enumerate(s.smoke):
        f = (ph0 + t * .06) % 1; fx, fyy = s.fires[src]
        blit(fr, s.puff, fx + dx * 40 + f * 140, fyy - f * 900, min(1, f * 5) * (1 - f) * .45, .8 + f * 2.6)
    for i, (fx, fyy) in enumerate(s.fires):
        fl = .75 + .25 * math.sin(t * 13 + i) * math.sin(t * 7 + i * 2)
        blit(fr, s.flame, fx, fyy, .9 * fl, 1.4 * fl, add=True); blit(fr, s.flame2, fx, fyy + 10, .8 * fl, 1.2, add=True)
    # convoy militar avanzando por la autopista
    for j in range(4):
        x = (lerp(-400, 1300, ((t * .09) + j * .27) % 1)); s.mrap(fr, x, 1260, .8)
    s.dust2.draw(fr, t)
    # bengalas
    for j in range(3):
        f = (t * .25 + j / 3.) % 1; blit(fr, glow_sprite(50, (255, 230, 200)), 200 + j * 330, 200 + f * 500, (1 - f) * .9, add=True)
    # soldados en posición táctica
    for i, (x, fy) in enumerate([(220, 1600), (520, 1640), (830, 1600)]):
        cv2.ellipse(fr, (x, fy + 4), (130, 18), 0, 0, 360, (8, 6, 6), -1, cv2.LINE_AA)
        character(fr, 'militar', x, fy, 400, t + i, armR=('apunta', (x + 300, fy - 330), .85), armL=('apunta', (x + 260, fy - 300), .8),
                  look=(.6, -.2), frown=.5, beret=True)
    # drones con visor infrarrojo
    for i in range(2):
        x = lerp(-150, 1250, ((t * .07) + i * .5) % 1); s.drone(fr, x, 420 + i * 160 + math.sin(t * 2 + i) * 12, 1.2 - .3 * i, t)
    k = ss(7.4, 7.7, t)
    if k > 0: blit(fr, s.stamp, 540, 560, k, lerp(1.6, 1., eOut(k)))
R4.draw = r4_draw

# ================================================================ 5 · Cierre
class R5(CH.C5):
    def __init__(s):
        super().__init__()
        s.cta = N.holo_panel(660, 200, '¿VOLVERÍA A MANDAR?', 'COMENTA ABAJO')

# ---------------------------------------------------------------- subtítulos desde los tiempos por palabra
KEY = {'Cártel', 'Sinaloa', 'máxima', 'seguridad', 'rescatarían', 'mandar', 'plan', 'rescate', 'túnel', 'infiltración', 'cibernética', 'apagones', 'masivos',
       'comando', 'élite', 'militar', 'poder', 'unifica', 'instantáneamente', 'tiemblan', 'mapa', 'narcotráfico', 'horas', 'guerra', 'total', 'Washington',
       'inteligencia', 'fuerzas', 'especiales', 'batalla', 'geopolítico', 'incontrolable', 'mito', 'película', 'pesadilla', 'posible', 'like', 'sígueme', 'extremo'}
def build_subs_from_words(words, ys):
    out, cur = [], []
    def flush():
        if cur: out.append(cur[:]); cur.clear()
    for w in words:
        cur.append(w)
        if len(cur) >= 4 or w[0][-1] in '.,:;?!…' or (len(cur) >= 3 and sum(len(x[0]) for x in cur) > 20): flush()
    flush()
    subs = []
    for i, g in enumerate(out):
        a = g[0][1]; b = out[i + 1][0][1] if i + 1 < len(out) else DUR
        b = min(b, g[-1][2] + .9)
        txt = ' '.join(f"*{w[0]}*" if w[0].strip('¿?¡!.,…:;') in KEY else w[0] for w in g)
        sc = max(i_ for i_ in range(5) if a >= SC_T[i_] - 1e-6); subs.append((a, b, ys[sc], txt))
    return subs

exec(CH._src.replace("secs = [(0, 'tension', 1), (9.9, 'misterio', 2), (24.1, 'tension', 2), (37.2, 'epico', 2), (50.2, 'tension', 1)]",
                  "secs = [(0, 'tension', 1), (8, 'misterio', 2), (20, 'epico', 2), (35, 'tension', 2), (48, 'epico', 1)]"))

def main():
    global SUBS
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    wpath = os.path.join(HERE, 'words_rescate.json')
    if os.path.exists(wpath): SUBS = build_subs_from_words(json.load(open(wpath)), [1460, 1500, 1460, 960, 1480])
    objs = [R1(), R2(), R3(), R4(), R5()]
    scenes = [(SC_T[i], SC_T[i + 1], objs[i]) for i in range(5)]
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in SUBS]; emos = [e + (emoji_sprite(e[2]),) for e in EMOJIS]
    def one(idx, T):
        a, b, sc = scenes[idx]; return cinema(render3d(sc, T - a, b - a, T), min(idx, 4), T)
    def frame(T):
        idx = max(i for i, (a, b, _) in enumerate(scenes) if T >= a - 1e-6)
        a = scenes[idx][0]; fr = one(idx, T)
        if idx > 0 and T - a < .45: fr = cv2.addWeighted(one(idx - 1, T), 1 - ss(0, .45, T - a), fr, ss(0, .45, T - a), 0)
        draw_overlays(fr, T, subs, emos); return fr
    if mode == 'test':
        for T in [float(x) for x in sys.argv[2:]]:
            cv2.imwrite(f'{OUT}/r_{T:05.1f}.jpg', cv2.resize(frame(T), (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == 'seg':
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', f'{OUT}/rseg_{f0:04d}.mp4']
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(f0, f1): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('SEG', f0, f1, flush=True); return
    if mode == 'audio': synth_audio(f'{OUT}/audio_rescate.wav'); print('audio ok'); return

if __name__ == '__main__': main()
