#!/usr/bin/env python3
# Short: ¿Qué pasaría si el crimen organizado tomara oficialmente la Presidencia? (60 s, 1080x1920)
# Basado en plantilla_shorts.py (mismo estilo: muñecos de porcelana, neón, hologramas, mapas, globo).
from lib import *
import lib

VOZ = os.path.join(HERE, 'voz.mp3')
# escenas (s): gancho · primero · segundo · tercero · cierre
SC_T = [0, 8.9, 22.0, 35.8, 48.0, DUR]

# ---------------------------------------------------------------- subtítulos (sincronizados con with-timestamps)
SUBS = [
 (0.00, 1.40, 1450, "De las *sombras*…"), (1.45, 3.45, 1450, "al *Palacio Nacional*."),
 (3.75, 5.90, 1450, "¿Qué pasaría si el *crimen organizado*"), (5.90, 8.70, 1450, "tomara *oficialmente* la *Presidencia*?"),
 (9.15, 10.50, 1500, "Primero:"), (10.55, 13.10, 1500, "un *Narco-Estado* oficial."), (13.30, 14.85, 1500, "Las *instituciones* públicas"),
 (14.85, 17.05, 1500, "se *fusionarían* con los *carteles*,"), (17.10, 19.15, 1500, "*legalizando* sus operaciones"), (19.20, 21.90, 1500, "y cobrando *impuestos* directos."),
 (22.20, 23.50, 1440, "Segundo:"), (23.55, 25.55, 1440, "*intervención extranjera*."), (25.60, 27.90, 1440, "Para potencias como *Estados Unidos*,"),
 (27.92, 29.30, 1440, "esto sería una *amenaza*"), (29.30, 31.05, 1440, "de *seguridad nacional*."), (31.15, 33.60, 1440, "Habría *bloqueos comerciales*…"), (33.70, 35.70, 1440, "e *invasión militar*."),
 (36.05, 37.45, 1000, "Tercero:"), (37.48, 39.40, 1000, "*guerra civil* interna."), (39.45, 41.40, 1000, "La disputa por el *control total*"),
 (41.40, 44.25, 1000, "de los estados entre *carteles rivales*"), (44.28, 47.70, 1000, "desataría un conflicto *sin precedentes*."),
 (48.15, 51.55, 1480, "El *colapso* de la *democracia* sería total."), (51.70, 53.52, 1480, "¿Crees que este escenario"), (53.52, 55.40, 1480, "está *lejos* de la *realidad*?"),
 (55.50, 57.10, 1480, "¡*Comenta* abajo"), (57.10, 60.00, 1480, "y *suscríbete*!"),
]
EMOJIS = [
 (1.5, 3.6, '🏛️', 860, 620, 140, 'pop'), (4.9, 8.6, '💀', 190, 520, 165, 'late'), (7.2, 8.7, '👑', 880, 560, 160, 'pop'),
 (10.9, 13.1, '⚠️', 880, 1180, 150, 'late'), (15.5, 17.0, '🤝', 540, 700, 150, 'pop'), (17.5, 19.2, '📜', 180, 1180, 150, 'flota'),
 (19.5, 21.8, '💰', 880, 1180, 160, 'late'), (20.2, 21.8, '💵', 190, 1180, 150, 'flota'),
 (26.6, 29.0, '🇺🇸', 900, 300, 150, 'pop'), (28.8, 31.0, '⚠️', 180, 300, 150, 'late'), (31.6, 33.6, '🚫', 900, 1240, 160, 'sacude'), (33.8, 35.7, '🚁', 180, 1240, 160, 'flota'),
 (37.5, 39.4, '⚔️', 880, 1240, 150, 'sacude'), (39.6, 41.4, '🔥', 190, 1240, 150, 'late'), (42.3, 44.2, '🚨', 880, 1240, 150, 'late'), (44.6, 47.7, '📈', 190, 1240, 150, 'cae'),
 (48.4, 51.5, '⚖️', 880, 330, 150, 'flota'), (50.4, 51.6, '💔', 190, 330, 150, 'sacude'), (51.8, 55.4, '🤔', 880, 330, 160, 'late'),
 (55.6, 60, '💬', 860, 1290, 150, 'late'), (57.2, 60, '🔔', 860, 1290, 160, 'sacude'), (57.3, 60, '👍', 220, 1290, 150, 'pop'),
]

def holo_panel(w, h, title, sub=None, col=(120, 230, 255), fill=(8, 52, 82, 190)):
    pn = np.zeros((h, w, 4), np.uint8); im = Image.fromarray(pn); d = ImageDraw.Draw(im)
    d.rectangle((6, 6, w - 7, h - 7), fill=fill, outline=col + (240,), width=4)
    for y in range(12, h - 10, 6): d.line((10, y, w - 10, y), fill=col + (16,), width=2)
    for (x, y, dx, dy) in [(6, 6, 1, 1), (w - 7, 6, -1, 1), (6, h - 7, 1, -1), (w - 7, h - 7, -1, -1)]:
        d.line((x, y + dy * 54, x, y, x + dx * 54, y), fill=tuple(min(255, c + 40) for c in col) + (255,), width=10)
    pn = np.array(im)
    over(pn, text_sprite(title, 60, (224, 248, 255, 255), glow=col, glow_r=10, spacing=2, maxw=w - 80), w / 2, 70)
    if sub: over(pn, text_sprite(sub, 30, col + (235,), spacing=6, maxw=w - 100), w / 2, 132)
    return pn

def stamp(txt, col=(255, 59, 42), w=640, h=124, px=80, fill=None):
    stp = np.zeros((h, w, 4), np.uint8); im = Image.fromarray(stp); d = ImageDraw.Draw(im)
    d.rectangle((4, 4, w - 5, h - 5), fill=fill or col + (60,), outline=col + (255,), width=6); stp = np.array(im)
    over(stp, text_sprite(txt, px, tuple(min(255, c + 20) for c in col) + (255,), glow=col, glow_r=10, spacing=10, maxw=w - 60), w / 2, h / 2)
    return stp

def neon(txt, px, col, glow, maxw=900):
    return text_sprite(txt, px, col + (255,), glow=glow, glow_r=18, spacing=6, maxw=maxw, pad=60)

def heli(fr, x, y, s, t, col=(30, 34, 30), light=True):
    # silueta de helicóptero militar (vista lateral, mirando a la izquierda)
    cv2.ellipse(fr, P8((x, y)), (int(56 * s * 8), int(22 * s * 8)), 0, 0, 360, col, -1, cv2.LINE_AA, 3)
    poly(fr, [(x - 50 * s, y - 6 * s), (x - 30 * s, y - 20 * s), (x - 12 * s, y - 20 * s), (x - 20 * s, y)], (60, 90, 110))
    line(fr, (x + 40 * s, y - 4 * s), (x + 120 * s, y - 10 * s), col, 9 * s)
    poly(fr, [(x + 112 * s, y - 12 * s), (x + 128 * s, y - 40 * s), (x + 132 * s, y - 8 * s)], col)
    line(fr, (x - 30 * s, y + 30 * s), (x + 34 * s, y + 30 * s), col, 4 * s)
    for k in (-18, 18): line(fr, (x + k * s, y + 18 * s), (x + k * s, y + 30 * s), col, 3 * s)
    line(fr, (x, y - 22 * s), (x, y - 30 * s), col, 5 * s)
    ph = math.sin(t * 40); line(fr, (x - 95 * s * ph, y - 31 * s), (x + 95 * s * ph, y - 31 * s), (70, 74, 70), 4 * s)
    cv2.ellipse(fr, P8((x, y - 31 * s)), (int(98 * s * 8), int(6 * s * 8)), 0, 0, 360, (54, 58, 56), 1, cv2.LINE_AA, 3)
    circ(fr, (x + 128 * s, y - 10 * s), 10 * s * (.5 + .5 * abs(math.sin(t * 30))), (90, 90, 90))
    if light and math.sin(t * 6) > .3: circ(fr, (x + 8 * s, y + 20 * s), 5 * s, (255, 60, 50))

# ================================================================ ESCENA 1 · Palacio Nacional de noche
class S1:
    def __init__(s):
        img = vgrad([(0, (4, 6, 16)), (.45, (16, 16, 34)), (.62, (36, 22, 30)), (.63, (24, 20, 24)), (1, (8, 8, 12))])
        for i in range(260):
            x, y = rng.randint(0, W), rng.randint(0, 760); img[y:y + 2, x:x + 2] += rng.uniform(60, 220)
        radial(img, (840, 260), 140, (255, 240, 220), .5); radial(img, (840, 260), 40, (255, 250, 240), 1.)  # luna
        i8 = to8(img)
        # fachada de tezontle
        fy0, fy1 = 760, 1210
        fac = np.ones((fy1 - fy0, W, 3), np.float32) * np.array([92, 38, 32], np.float32)
        fac += rng.normal(0, 6, (fy1 - fy0, W, 1)).astype(np.float32)
        for y in range(0, fy1 - fy0, 26): fac[y:y + 2] *= .78
        i8[fy0:fy1] = to8(fac)
        for y, hgt in [(fy0 - 22, 22), (fy0 + 200, 14), (fy1 - 18, 18)]: cv2.rectangle(i8, (0, y), (W, y + hgt), (176, 160, 130), -1)
        for x in range(10, W, 46): cv2.rectangle(i8, (x, fy0 - 46), (x + 24, fy0 - 22), (160, 146, 118), -1)   # almenas
        # ventanas iluminadas con marco de cantera
        s.wins = []
        for row, y in enumerate([fy0 + 60, fy0 + 260]):
            for x in range(70, W, 160):
                if abs(x + 30 - 540) < 120: continue
                cv2.rectangle(i8, (x - 10, y - 14), (x + 70, y + 130), (186, 170, 140), -1)
                cv2.rectangle(i8, (x, y), (x + 60, y + 120), (255, 176, 80), -1)
                cv2.line(i8, (x + 30, y), (x + 30, y + 120), (120, 60, 20), 3); cv2.line(i8, (x, y + 60), (x + 60, y + 60), (120, 60, 20), 3)
                cv2.fillPoly(i8, [np.array([(x - 18, y - 14), (x + 78, y - 14), (x + 30, y - 46)], np.int32)], (186, 170, 140), cv2.LINE_AA)
                s.wins.append((x + 30, y + 60))
        # torre central con campana
        cv2.rectangle(i8, (440, 520), (640, fy0), (100, 42, 34), -1); cv2.rectangle(i8, (430, 500), (650, 530), (186, 170, 140), -1)
        cv2.ellipse(i8, (540, 620), (60, 70), 0, 180, 360, (20, 10, 10), -1, cv2.LINE_AA); cv2.rectangle(i8, (480, 620), (600, 700), (20, 10, 10), -1)
        cv2.ellipse(i8, (540, 640), (34, 40), 0, 180, 360, (200, 160, 60), -1, cv2.LINE_AA); cv2.rectangle(i8, (506, 640), (574, 668), (200, 160, 60), -1)
        cv2.line(i8, (540, 400), (540, 500), (200, 170, 90), 6, cv2.LINE_AA)               # asta
        # balcón central
        cv2.rectangle(i8, (380, fy0 + 30), (700, fy0 + 330), (186, 170, 140), -1)
        cv2.ellipse(i8, (540, fy0 + 140), (130, 110), 0, 180, 360, (255, 190, 100), -1, cv2.LINE_AA); cv2.rectangle(i8, (410, fy0 + 140), (670, fy0 + 320), (255, 190, 100), -1)
        cv2.rectangle(i8, (360, fy0 + 330), (720, fy0 + 352), (200, 186, 156), -1)
        for x in range(372, 712, 22): cv2.rectangle(i8, (x, fy0 + 352), (x + 10, fy0 + 420), (176, 160, 130), -1)
        cv2.rectangle(i8, (360, fy0 + 418), (720, fy0 + 434), (200, 186, 156), -1)
        # plaza (Zócalo) con perspectiva
        for k in range(-14, 15): cv2.line(i8, (540, fy1), (540 + k * 170, H), (34, 30, 34), 2, cv2.LINE_AA)
        for j in range(1, 9):
            y = int(fy1 + (H - fy1) * (j / 8.) ** 1.8); cv2.line(i8, (0, y), (W, y), (34, 30, 34), 2, cv2.LINE_AA)
        img = i8.astype(np.float32)
        for (x, y) in s.wins: radial(img, (x, y), 110, (255, 150, 60), .18)
        radial(img, (540, fy0 + 220), 360, (255, 170, 80), .35)
        beam(img, (0, 300), (480, 1250), 20, 260, (255, 40, 30), .26)
        beam(img, (1080, 300), (600, 1250), 20, 260, (40, 100, 255), .26)
        img = vignette(bloom(img, 220, 22, .8)); s.bg = to8(img)
        s.dust = Dust(46, (40, 300, 1040, 1500), (255, 200, 160), 5, .5)
        s.title = stamp('NARCO-PRESIDENCIA', (255, 59, 42), w=880, h=130, px=78, fill=(24, 4, 4, 215))
        s.fog = glow_sprite(260, (0, 0, 0))
    def draw(s, fr, t, d):
        # bandera ondeando
        x0, y0 = 540, 404
        for i in range(24):
            u0, u1 = i / 24., (i + 1) / 24.
            col = (0, 104, 71) if i < 8 else (240, 240, 240) if i < 16 else (206, 17, 38)
            w0 = math.sin(u0 * 6 - t * 5) * 10 * u0; w1 = math.sin(u1 * 6 - t * 5) * 10 * u1
            poly(fr, [(x0 + u0 * 220, y0 + w0), (x0 + u1 * 220, y0 + w1), (x0 + u1 * 220, y0 + 130 + w1), (x0 + u0 * 220, y0 + 130 + w0)], col)
        circ(fr, (x0 + 110, y0 + 65 + math.sin(.5 * 6 - t * 5) * 5), 14, (122, 82, 40))
        s.dust.draw(fr, t)
        wave = ss(2.0, 2.6, t) * (1 - ss(5.6, 6.2, t))
        armR = ('palma',) if wave > .5 else ('reposo',)
        character(fr, 'traje', 540, 1160, 380, t, armR=armR, armL=('reposo',), look=(0, -.1), frown=.6, smile=.6 * ss(6.5, 7.2, t), sash=True)
        # barandal delante del personaje
        cv2.rectangle(fr, (360, 1112), (720, 1128), (200, 186, 156), -1)
        for x in range(372, 712, 22): cv2.rectangle(fr, (x, 1128), (x + 10, 1192), (176, 160, 130), -1)
        cv2.rectangle(fr, (360, 1188), (720, 1204), (200, 186, 156), -1)
        # "de las sombras": niebla negra que se disipa
        op = 1 - ss(0, 1.6, t)
        if op > 0: fr[:] = (fr * (1 - .85 * op)).astype(np.uint8)
    def cam(s, t, d):
        k = eExpo(t / 1.6)
        return lerp(2.8, 1.35, k) * (1 + .08 * ss(1.6, 8.9, t)), 540, lerp(1500, 940, k), 0, 0

# ================================================================ ESCENA 2 · Despacho: Narco-Estado oficial
class S2:
    def __init__(s):
        img = vgrad([(0, (16, 10, 8)), (.7, (40, 24, 16)), (.71, (28, 18, 12)), (1, (12, 8, 6))])
        i8 = to8(img)
        for x in range(0, W, 120):
            cv2.rectangle(i8, (x + 10, 180), (x + 110, 640), (58, 34, 22), 3); cv2.rectangle(i8, (x + 10, 700), (x + 110, 1300), (58, 34, 22), 3)
        # ventana con ciudad de noche
        cv2.rectangle(i8, (360, 200), (720, 760), (8, 10, 22), -1)
        for i in range(140):
            x, y = rng.randint(370, 710), rng.randint(450, 750); cv2.circle(i8, (x, y), rng.randint(1, 4), (255, 190, 110) if rng.rand() < .7 else (140, 190, 255), -1, cv2.LINE_AA)
        cv2.rectangle(i8, (360, 200), (720, 760), (230, 220, 200), 10); cv2.line(i8, (540, 200), (540, 760), (230, 220, 200), 6)
        for sd in (-1, 1):  # cortinas
            pts = [(540 + sd * 180, 170)] + [(540 + sd * (240 + 20 * math.sin(y * .05)), y) for y in range(170, 900, 20)] + [(540 + sd * 180, 900)]
            cv2.fillPoly(i8, [np.array([(540 + sd * 150, 170), (540 + sd * 300, 170), (540 + sd * 300, 900), (540 + sd * 170, 900)], np.int32)], (110, 16, 24), cv2.LINE_AA)
            for k in range(6): cv2.line(i8, (540 + sd * (160 + k * 24), 170), (540 + sd * (170 + k * 24), 900), (80, 10, 18), 3, cv2.LINE_AA)
        for x in (180, 900):  # banderas
            cv2.line(i8, (x, 360), (x, 1240), (200, 160, 60), 6, cv2.LINE_AA)
            for k, c in enumerate([(0, 104, 71), (240, 240, 240), (206, 17, 38)]):
                cv2.fillPoly(i8, [np.array([(x + 3, 380 + k * 70), (x + 120, 400 + k * 70), (x + 110, 470 + k * 70), (x + 3, 450 + k * 70)], np.int32)], c, cv2.LINE_AA)
        img = i8.astype(np.float32)
        radial(img, (540, 480), 600, (255, 150, 70), .12)
        beam(img, (540, 180), (540, 1400), 60, 420, (255, 210, 150), .08, 40)
        beam(img, (0, 200), (440, 1300), 20, 200, (255, 40, 30), .22); beam(img, (1080, 200), (640, 1300), 20, 200, (40, 100, 255), .22)
        img = vignette(bloom(img, 220, 22, .7)); s.bg = to8(img)
        # escritorio (se dibuja encima del personaje)
        desk = np.zeros((420, W, 4), np.uint8)
        cv2.rectangle(desk, (60, 0), (W - 60, 50), (92, 46, 22, 255), -1); cv2.rectangle(desk, (60, 0), (W - 60, 8), (200, 160, 70, 255), -1)
        cv2.rectangle(desk, (100, 50), (W - 100, 420), (64, 30, 14, 255), -1)
        for x in (140, W - 420):
            for k in range(3):
                cv2.rectangle(desk, (x, 80 + k * 110), (x + 280, 170 + k * 110), (82, 40, 18, 255), 4); cv2.rectangle(desk, (x + 120, 118 + k * 110), (x + 160, 130 + k * 110), (210, 170, 70, 255), -1)
        cv2.rectangle(desk, (420, 60), (660, 120), (200, 160, 70, 255), -1)
        over(desk, text_sprite('PRESIDENCIA', 30, (60, 30, 10, 255), spacing=4, pad=10), 540, 90)
        s.desk = desk
        s.p1 = holo_panel(880, 320, 'NARCO-ESTADO', 'GOBIERNO + CÁRTELES')
        s.box_gob = holo_panel(300, 150, 'GOBIERNO'); s.box_cart = holo_panel(300, 150, 'CÁRTELES', col=(255, 90, 70), fill=(80, 10, 8, 190))
        s.stamp = stamp('LEGALIZADO', (60, 230, 120))
        s.tax = holo_panel(760, 420, 'IMPUESTOS', 'COBRO DIRECTO', col=(255, 200, 80), fill=(70, 46, 6, 190))
        s.dust = Dust(40, (40, 200, 1040, 1300), (255, 210, 170), 4, .45)
        s.money = glow_sprite(60, (80, 255, 120))
    def draw(s, fr, t, d):
        s.dust.draw(fr, t)
        # personaje con sello que golpea el escritorio
        ph = (t % 1.6) / 1.6; hit = 1 - abs(ph - .3) / .3 if ph < .6 else 0
        stampk = ss(8.0, 8.4, t) * (1 - ss(10.3, 10.6, t))
        armR = ('apunta', (760, 1080 + 120 * hit), .9) if stampk > .5 else ('jarra',)
        character(fr, 'traje', 540, 1490, 470, t, armR=armR, armL=('palma',) if 4.2 < t < 6 else ('reposo',), look=(.2, .3 if stampk > .5 else -.2), frown=.5, smile=.5 * ss(10.6, 11.4, t))
        blit(fr, s.desk, 540, 1260 + 210)
        # panel principal + fusión gobierno/cárteles
        a = ss(1.6, 2.2, t) * (1 - ss(7.6, 8.0, t)); py = 300 + math.sin(t * 1.5) * 5
        if a > 0:
            blit(fr, s.p1, 540, py, a)
            m = eIO(ss(6.0, 7.6, t)); gx = lerp(320, 470, m); cx_ = lerp(760, 610, m)
            blit(fr, s.box_gob, gx, py + 260, a); blit(fr, s.box_cart, cx_, py + 260, a)
            if m > .95:
                gl = glow_sprite(160, (255, 200, 120)); blit(fr, gl, 540, py + 260, .6 * a * (.6 + .4 * math.sin(t * 8)), add=True)
        k = ss(8.2, 8.5, t) * (1 - ss(10.4, 10.8, t))
        if k > 0: blit(fr, s.stamp, 540, 360, k, lerp(1.6, 1., eOut(ss(8.2, 8.5, t))))
        # impuestos: barras doradas que suben
        o = ss(10.6, 11.2, t)
        if o > 0:
            ty = 360 + math.sin(t * 1.3) * 4; blit(fr, s.tax, 540, ty, o)
            for i in range(6):
                v = eOut(ss(11.0 + i * .2, 12.2 + i * .2, t)) * (.25 + i * .14)
                x = 250 + i * 100; y1_ = ty + 180; y0_ = y1_ - v * 220
                cv2.rectangle(fr, (int(x), int(y0_)), (int(x + 64), int(y1_)), (255, 200, 60), -1)
                cv2.rectangle(fr, (int(x), int(y0_)), (int(x + 64), int(y1_)), (255, 240, 180), 2)
            if t > 12: poly(fr, [(860, ty - 60), (900, ty - 120), (940, ty - 60)], (255, 200, 60))
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.04, 1.13, k), 540, lerp(900, 1000, k), lerp(-20, 20, k), 0

# ================================================================ ESCENA 3 · Mapa: intervención extranjera
def prj(lon, lat): return (20 + (lon + 119) * 30.6, 1130 - (lat - 23.5) * 33.6)
def prjA(p): return np.stack([20 + (p[:, 0] + 119) * 30.6, 1130 - (p[:, 1] - 23.5) * 33.6], 1)

class S3:
    def __init__(s):
        img = vgrad([(0, (3, 9, 20)), (1, (5, 14, 28))]); i8 = to8(img)
        for lo in range(-120, -82, 2):
            x = int(prj(lo, 0)[0]); cv2.line(i8, (x, 0), (x, H), (14, 34, 52), 1)
        for la in range(-8, 60, 2):
            y = int(prj(0, la)[1]); cv2.line(i8, (0, y), (W, y), (14, 34, 52), 1)
        s.usq = prjA(NA)
        for p in OTHERS:
            q = prjA(p); poly(i8, q, (40, 62, 88)); pline(i8, q, (130, 160, 196), 2, True)
        mx = prjA(MX); poly(i8, mx, (96, 16, 12)); pline(i8, mx, (255, 86, 56), 5, True)
        lay = np.zeros((H, W, 3), np.uint8); pline(lay, mx, (255, 60, 36), 9, True)
        gl = cv2.GaussianBlur(lay.astype(np.float32), (0, 0), 16) * 1.6
        img = i8.astype(np.float32) + gl * .45
        img = vignette(img, .5); s.bg = to8(img)
        x0, y0 = int(mx[:, 0].min()) - 60, int(mx[:, 1].min()) - 60; x1, y1 = int(mx[:, 0].max()) + 60, int(mx[:, 1].max()) + 60
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
        g = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); g[:, :, :3] = to8(gl[y0:y1, x0:x1]); g[:, :, 3] = 255
        s.gl = g; s.glc = ((x0 + x1) / 2, (y0 + y1) / 2)
        # brillo azul de EE. UU.
        lay = np.zeros((H, W, 3), np.uint8); pline(lay, s.usq, (60, 120, 255), 9, True)
        ug = cv2.GaussianBlur(lay.astype(np.float32), (0, 0), 14) * 1.6; s.ug = np.dstack([to8(ug), np.full((H, W), 255, np.uint8)])
        for txt, lo, la, px, c, sp in [('MÉXICO', -102.6, 24.4, 50, (255, 255, 255, 255), 10), ('ESTADOS UNIDOS', -99, 36.5, 40, (190, 208, 230, 230), 6)]:
            spr = text_sprite(txt, px, c, stroke=3, stroke_col=(0, 0, 0, 200), spacing=sp); x, y = prj(lo, la); blit(s.bg, spr, x, y)
        s.cd = prj(-99.13, 19.43)
        s.panel = holo_panel(880, 220, 'AMENAZA', 'SEGURIDAD NACIONAL · EE. UU.', col=(120, 200, 255))
        s.stamp = stamp('BLOQUEO COMERCIAL', (255, 59, 42), w=820, px=70)
        s.dot = glow_sprite(70, (255, 60, 40)); s.dust = Dust(30, (40, 200, 1040, 1700), (150, 220, 255), 4, .4)
        s.arrows = [((-108, 40), (-106.4, 31.7)), ((-97, 40), (-100.3, 25.7)), ((-88, 30), (-96.1, 19.2)), ((-122, 33), (-117.0, 32.5))]
    def draw(s, fr, t, d):
        pul = .5 + .5 * math.sin(t * 4); cx, cy = s.cd
        blit(fr, s.gl, s.glc[0], s.glc[1], .15 + .5 * pul, add=True)
        u = ss(3.4, 4.2, t)
        if u > 0: blit(fr, s.ug, W / 2, H / 2, u * (.4 + .3 * pul), add=True)
        ov = np.zeros((440, 440, 3), np.uint8)
        for i in range(3):
            f = (t * .55 + i / 3.) % 1; k = (1 - f) * .95
            cv2.circle(ov, (220 * 8, 220 * 8), int((18 + f * 190) * 8), (int(255 * k), int(70 * k), int(46 * k)), 5, cv2.LINE_AA, 3)
        x0, y0 = int(cx) - 220, int(cy) - 220; roi = fr[y0:y0 + 440, x0:x0 + 440]; roi[:] = cv2.add(roi, ov)
        blit(fr, s.dot, cx, cy, .6 + .4 * pul, add=True); circ(fr, (cx, cy), 9, (255, 220, 200))
        # flechas de presión desde el norte (se dibujan progresivamente)
        for i, (a, b) in enumerate(s.arrows):
            k = ss(9.2 + i * .25, 10.6 + i * .25, t)
            if k <= 0: continue
            p0, p1 = A(*prj(*a)), A(*prj(*b)); mid = (p0 + p1) / 2 + A(0, -120)
            pts = [tuple((1 - u_) ** 2 * p0 + 2 * (1 - u_) * u_ * mid + u_ ** 2 * p1) for u_ in np.linspace(0, k, 30)]
            pline(fr, pts, (110, 40, 30), 14); pline(fr, pts, (255, 80, 60), 6)
            if k > .98:
                e = A(*pts[-1]); dv = e - A(*pts[-3]); dv /= np.linalg.norm(dv); n = A(-dv[1], dv[0])
                poly(fr, [tuple(e + dv * 22), tuple(e - dv * 10 + n * 16), tuple(e - dv * 10 - n * 16)], (255, 90, 70))
        # helicópteros cruzando hacia el sur
        hk = ss(11.0, 13.8, t)
        if hk > 0:
            for i, (dx, dy) in enumerate([(0, 0), (130, -70), (130, 70)]):
                x = lerp(1300, 200, (t - 11.0) / 2.9) + dx * 1.6; y = lerp(900, 1250, (t - 11.0) / 2.9) + dy * 1.6
                heli(fr, x, y, 1.6 - .25 * (i > 0), t + i)
        a = ss(6.4, 7.0, t) * (1 - ss(9.0, 9.3, t))
        if a > 0: blit(fr, s.panel, 540, 470 + math.sin(t * 1.6) * 5, a)
        k = ss(9.6, 9.9, t)
        if k > 0: blit(fr, s.stamp, 540, 470, k, lerp(1.6, 1., eOut(k)))
        s.dust.draw(fr, t)
    def cam(s, t, d):
        up = ss(3.0, 5.0, t) * (1 - ss(8.5, 10.5, t))
        return lerp(1.25, 1.05, eOut(t / 3)) * (1 + .05 * ss(10, d, t)), s.cd[0], lerp(s.cd[1], 780, up), 0, 0

# ================================================================ ESCENA 4 · Guerra civil interna
class S4:
    def __init__(s):
        hz = 1250
        img = vgrad([(0, (10, 6, 10)), (.5, (40, 16, 14)), (.65, (90, 34, 20)), (.651, (18, 14, 14)), (1, (8, 7, 8))])
        i8 = to8(img)
        for layer, (col, hmin, hmax, lit) in enumerate([((26, 18, 22), 200, 520, .15), ((14, 10, 14), 280, 700, .25)]):
            x = -20
            while x < W:
                bw = rng.randint(70, 160); bh = rng.randint(hmin, hmax); cv2.rectangle(i8, (x, hz - bh), (x + bw, hz), col, -1)
                for wy in range(hz - bh + 20, hz - 20, 34):
                    for wx in range(x + 12, x + bw - 16, 26):
                        if rng.rand() < lit: cv2.rectangle(i8, (wx, wy), (wx + 12, wy + 16), (255, 170, 80) if rng.rand() < .8 else (150, 200, 255), -1)
                if rng.rand() < .4: cv2.line(i8, (x + bw // 2, hz - bh), (x + bw // 2, hz - bh - 60), col, 3)
                x += bw + rng.randint(0, 12)
        for j in range(1, 10):
            y = int(hz + (H - hz) * (j / 9.) ** 1.8); cv2.line(i8, (0, y), (W, y), (30, 24, 26), 2, cv2.LINE_AA)
        img = i8.astype(np.float32)
        for (x, y, r) in [(220, hz - 40, 300), (760, hz - 20, 360), (520, hz + 20, 220)]: radial(img, (x, y), r, (255, 110, 30), .5)
        img = vignette(bloom(img, 200, 22, .8), .6); s.bg = to8(img)
        s.fires = [(220, hz - 30), (760, hz - 10), (520, hz + 30)]
        s.smoke = []
        for i in range(36): s.smoke.append((rng.uniform(0, 1), rng.choice(3), rng.uniform(-1, 1)))
        s.puff = glow_sprite(120, (96, 84, 82)); s.flame = glow_sprite(80, (255, 140, 40)); s.flame2 = glow_sprite(40, (255, 230, 150))
        s.dust = Dust(60, (40, 300, 1040, 1500), (255, 150, 80), 4, .6)
        # mapa de territorios en disputa (panel holográfico)
        pw, ph = 860, 560; s.pw, s.ph = pw, ph; pn = holo_panel(pw, ph, 'CONTROL TERRITORIAL', col=(255, 120, 90), fill=(40, 10, 10, 200))
        mx = MX.copy(); lo0, lo1, la0, la1 = -118, -86, 14, 33
        q = np.stack([60 + (mx[:, 0] - lo0) / (lo1 - lo0) * (pw - 120), 150 + (la1 - mx[:, 1]) / (la1 - la0) * (ph - 190)], 1)
        mask = np.zeros((ph, pw), np.uint8); cv2.fillPoly(mask, [q.astype(np.int32)], 255)
        seeds = np.array([(rng.uniform(80, pw - 80), rng.uniform(170, ph - 40)) for _ in range(14)])
        yy, xx = np.mgrid[0:ph, 0:pw]; dd = np.stack([(xx - a) ** 2 + (yy - b) ** 2 for a, b in seeds]); s.lab = dd.argmin(0)
        s.mask = mask > 0; s.pbase = pn; s.q = q
        s.facs = [(230, 50, 50), (60, 140, 255), (250, 190, 40), (160, 70, 220)]
        s.owner = rng.randint(0, 4, 14); s.flip = [(rng.uniform(1.5, 10), rng.randint(0, 4)) for _ in range(14)]
        s.big = neon('SIN PRECEDENTES', 100, (255, 80, 60), (255, 30, 16), maxw=760)
    def draw(s, fr, t, d):
        for i, (ph0, src, dx) in enumerate(s.smoke):
            f = (ph0 + t * .06) % 1; fx, fyy = s.fires[src]
            blit(fr, s.puff, fx + dx * 40 + f * 140, fyy - f * 900, min(1, f * 5) * (1 - f) * .45, .8 + f * 2.6)
        for i, (fx, fyy) in enumerate(s.fires):
            fl = .75 + .25 * math.sin(t * 13 + i) * math.sin(t * 7 + i * 2)
            blit(fr, s.flame, fx, fyy, .9 * fl, 1.4 * fl, add=True); blit(fr, s.flame2, fx, fyy + 10, .8 * fl, 1.2, add=True)
        s.dust.draw(fr, t)
        # sirenas rojo/azul barriendo
        sw = math.sin(t * 2.2)
        lay = np.zeros((H // 4, W // 4, 3), np.float32)
        cv2.fillPoly(lay, [np.array([(30, 330), (30 + int(120 * sw) - 60, 0), (30 + int(120 * sw) + 60, 0)], np.int32)], (255, 30, 30))
        cv2.fillPoly(lay, [np.array([(240, 330), (240 - int(120 * sw) - 60, 0), (240 - int(120 * sw) + 60, 0)], np.int32)], (40, 90, 255))
        lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 8), (W, H)); fr[:] = np.clip(fr + lay * .22, 0, 255).astype(np.uint8)
        cv2.ellipse(fr, (540, 1594), (170, 22), 0, 0, 360, (8, 6, 6), -1, cv2.LINE_AA)
        character(fr, 'militar', 540, 1590, 470, t, armR=('jarra',), armL=('apunta', (300, 400), ss(4.0, 5.0, t) * (1 - ss(8.5, 9.2, t))), look=(-.5 * ss(4, 5, t), -.6), frown=.7, beret=True)
        # panel de territorios
        a = ss(3.4, 4.0, t)
        if a > 0:
            pn = s.pbase.copy(); own = s.owner.copy()
            for r, (tf, nw) in enumerate(s.flip):
                if t > tf: own[r] = (own[r] + nw + int((t - tf) / 2.2)) % 4
            cols = np.array([s.facs[o] for o in own], np.uint8)[s.lab]
            pul = (.75 + .25 * math.sin(t * 5))
            reg = pn[:, :, :3]; m = s.mask
            reg[m] = (reg[m] * .25 + cols[m] * .75 * pul).astype(np.uint8); pn[:, :, 3][m] = 235
            edges = cv2.Canny(s.lab.astype(np.uint8) * 17, 1, 1) > 0
            reg[edges & m] = (20, 10, 10)
            pline(pn, s.q, (255, 120, 90, 255), 4, True)
            blit(fr, pn, 540, 400 + math.sin(t * 1.3) * 5, a)
        k = ss(8.5, 8.9, t)
        if k > 0: blit(fr, s.big, 540, 760, k * (.9 + .1 * math.sin(t * 6)), lerp(1.4, 1, eOut((t - 8.5) / .4)))
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.02, 1.12, k), 540, lerp(1000, 1100, k), math.sin(t * .9) * 6, math.sin(t * 1.3) * 4

# ================================================================ ESCENA 5 · Colapso de la democracia (globo + balanza rota)
class S5:
    def __init__(s):
        s.cx, s.cy, s.R = 600, 640, 250; cx, cy, R = s.cx, s.cy, s.R; fl = 1392
        img = vgrad([(0, (8, 7, 14)), (.72, (20, 13, 12)), (.725, (46, 31, 20)), (1, (18, 12, 8))])
        for i in range(260):
            x, y = rng.randint(0, W), rng.randint(0, fl - 60); img[y:y + 2, x:x + 2] += rng.uniform(60, 230)
        radial(img, (cx, cy), 600, (255, 170, 80), .3)
        i8 = to8(img)
        for j in range(12):
            y = int(fl + (H - fl) * (j / 12.) ** 1.6); cv2.line(i8, (0, y), (W, y), (26, 17, 11), 2, cv2.LINE_AA)
        gold, gold2, goldd = (206, 164, 66), (255, 228, 150), (120, 90, 34)
        # balanza de la justicia rota (izquierda)
        bx = 200
        cv2.ellipse(i8, (bx, fl + 8), (120, 26), 0, 0, 360, goldd, -1, cv2.LINE_AA); cv2.ellipse(i8, (bx, fl), (120, 26), 0, 0, 360, gold, -1, cv2.LINE_AA)
        cv2.line(i8, (bx, fl), (bx, 930), goldd, 22, cv2.LINE_AA); cv2.line(i8, (bx, fl), (bx, 930), gold, 14, cv2.LINE_AA)
        cv2.circle(i8, (bx, 920), 22, gold, -1, cv2.LINE_AA)
        cv2.line(i8, (bx, 930), (bx - 170, 990), gold, 12, cv2.LINE_AA)                  # brazo intacto
        cv2.line(i8, (bx + 6, 935), (bx + 70, 960), gold, 12, cv2.LINE_AA)               # muñón roto
        cv2.line(i8, (bx + 90, 1010), (bx + 200, 1180), gold, 12, cv2.LINE_AA)           # pieza caída
        for k in (-40, 0, 40): cv2.line(i8, (bx - 170, 990), (bx - 170 + k, 1130), gold2, 2, cv2.LINE_AA)
        cv2.ellipse(i8, (bx - 170, 1130), (70, 26), 0, 0, 180, gold, -1, cv2.LINE_AA)
        cv2.ellipse(i8, (bx + 180, fl - 10), (70, 22), 20, 180, 360, goldd, -1, cv2.LINE_AA)  # plato caído
        # base del globo
        cv2.ellipse(i8, (cx, fl + 12), (140, 30), 0, 0, 360, goldd, -1, cv2.LINE_AA); cv2.ellipse(i8, (cx, fl), (140, 30), 0, 0, 360, gold, -1, cv2.LINE_AA)
        cv2.line(i8, (cx, cy + R + 26), (cx, fl - 4), goldd, 26, cv2.LINE_AA); cv2.line(i8, (cx, cy + R + 26), (cx, fl - 4), gold, 18, cv2.LINE_AA)
        cv2.ellipse(i8, (cx, cy), (R + 28, R + 28), 0, -78, 96, goldd, 14, cv2.LINE_AA); cv2.ellipse(i8, (cx, cy), (R + 28, R + 28), 0, -78, 96, gold, 9, cv2.LINE_AA)
        img = i8.astype(np.float32)
        beam(img, (60, 220), (480, 1380), 40, 300, (255, 184, 120), .12, 40)
        beam(img, (1050, 200), (700, 1380), 30, 260, (255, 50, 40), .14, 40)
        img = vignette(bloom(img, 200, 22, .6), .55); s.bg = to8(img)
        n = 2 * R + 6; s.n = n; yy, xx = np.mgrid[0:n, 0:n].astype(np.float32); c = n / 2 - .5
        nx = (xx - c) / R; ny = (yy - c) / R; r2 = nx * nx + ny * ny; nz = np.sqrt(np.clip(1 - r2, 0, 1))
        L = A(-.5, -.55, .67); L /= np.linalg.norm(L)
        s.shade = (.3 + .85 * np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1))[:, :, None].astype(np.float32)
        Hh = L + A(0, 0, 1); Hh /= np.linalg.norm(Hh)
        spec = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1) ** 50 * .4; rim = (1 - nz) ** 3
        s.addl = (spec[:, :, None] * 255 + rim[:, :, None] * np.array([255, 180, 90], np.float32) * .5).astype(np.float32)
        s.mask = np.clip((1 - np.sqrt(r2)) * R + .5, 0, 1)[:, :, None].astype(np.float32)
        s.grat = [np.array([(lo, la) for la in range(-90, 91, 5)], float) for lo in range(-180, 180, 20)] + \
                 [np.array([(lo, la) for lo in range(-180, 181, 5)], float) for la in range(-60, 61, 20)]
        s.gg = glow_sprite(120, (255, 190, 80)); s.dust = Dust(40, (40, 300, 1040, 1400), (255, 214, 160), 5, .5)
        s.demo_l = neon('DEMO', 88, (255, 230, 170), (255, 170, 60)); s.demo_r = neon('CRACIA', 88, (255, 230, 170), (255, 170, 60))
        s.cta = holo_panel(640, 200, '¿TÚ QUÉ OPINAS?', 'COMENTA · SUSCRÍBETE', col=(255, 200, 90), fill=(60, 36, 6, 190))
    def proj(s, pts, la0, lo0):
        lon = np.radians(pts[:, 0]); lat = np.radians(pts[:, 1]); p0 = math.radians(la0); dl = lon - math.radians(lo0)
        x = np.cos(lat) * np.sin(dl); y = math.cos(p0) * np.sin(lat) - math.sin(p0) * np.cos(lat) * np.cos(dl)
        cc = math.sin(p0) * np.sin(lat) + math.cos(p0) * np.cos(lat) * np.cos(dl); return x, y, cc
    def draw(s, fr, t, d):
        R, n = s.R, s.n; c = n / 2 - .5; la0 = 18; lo0 = lerp(-160, -101, eOut(t / 3.0)) + ss(3.0, 12, t) * 5
        pul = .5 + .5 * math.sin(t * 2.4); crack = ss(1.2, 2.2, t)
        g = np.empty((n, n, 3), np.uint8); g[:] = (16, 50, 108)
        for ln in s.grat:
            x, y, cc = s.proj(ln, la0, lo0); vis = cc > 0; run = []
            for i in range(len(x)):
                if vis[i]: run.append((c + x[i] * R, c - y[i] * R))
                else:
                    if len(run) > 1: pline(g, run, (34, 80, 146), 1)
                    run = []
            if len(run) > 1: pline(g, run, (34, 80, 146), 1)
        def fill(p, col, edge, th):
            x, y, cc = s.proj(p, la0, lo0)
            if cc.max() <= 0: return
            b = cc < 0; nr = np.maximum(np.hypot(x, y), 1e-6); x = np.where(b, x / nr, x); y = np.where(b, y / nr, y)
            q = np.stack([c + x * R, c - y * R], 1); poly(g, q, col); pline(g, q, edge, th, True)
        for p in OTHERS: fill(p, (58, 108, 70), (34, 72, 48), 1)
        k = .82 + .18 * pul; gcol = (int(lerp(255, 230, crack) * k), int(lerp(192, 60, crack) * k), int(lerp(64, 40, crack) * k))
        fill(MX, gcol, (255, 238, 176), 3)
        gf = g.astype(np.float32) * s.shade + s.addl
        x0, y0 = int(s.cx - n / 2), int(s.cy - n / 2); roi = fr[y0:y0 + n, x0:x0 + n]
        roi[:] = np.clip(roi * (1 - s.mask) + gf * s.mask, 0, 255)
        x, y, cc = s.proj(np.array([[-102.5, 23.6]]), la0, lo0); mp = (s.cx + x[0] * R, s.cy - y[0] * R)
        if cc[0] > .15: blit(fr, s.gg, mp[0], mp[1], (.3 + .3 * pul) * cl(cc[0] * 1.5), add=True)
        s.dust.draw(fr, t)
        # "DEMOCRACIA" que se parte en dos
        a = ss(.3, .8, t) * (1 - ss(7.2, 7.6, t))
        if a > 0:
            sp = eOut(ss(1.2, 2.2, t)) * 70; rot = ss(1.2, 2.4, t)
            blit(fr, s.demo_l, 270 - sp, 1150 + rot * 30, a * (1 - .35 * crack)); blit(fr, s.demo_r, 530 + sp, 1150 - rot * 20, a * (1 - .35 * crack))
            if crack > 0: pline(fr, [(400, 1090), (380, 1125), (420, 1150), (390, 1185), (410, 1215)], (255, 60, 40), 6 * crack)
        o = ss(7.6, 8.2, t)
        if o > 0: blit(fr, s.cta, 430, 1150 + math.sin(t * 1.6) * 5, o, lerp(1.2, 1, eOut((t - 7.6) / .6)))
        cv2.ellipse(fr, (870, 1424), (150, 22), 0, 0, 360, (16, 10, 7), -1, cv2.LINE_AA)
        point = ss(3.8, 4.5, t)
        armR = ('apunta', (540, 2600), point) if t < 7.4 else ('palma',)
        character(fr, 'elegante', 870, 1420, 430, t, armR=armR, armL=('jarra',), look=(.2, .2 * point), frown=lerp(.3, -.25, ss(7.4, 8, t)), smile=ss(7.6, 8.3, t))
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.0, 1.1, k), 540, lerp(860, 1000, k), 0, 0

# ---------------------------------------------------------------- filtros de cine
def _lut(lift, gamma, gain):
    x = np.arange(256) / 255.; y = np.clip(lift + (gain - lift) * x, 0, 1) ** gamma
    y = y + .06 * np.sin((y - .5) * math.pi) * (1 - abs(2 * y - 1))      # curva en S suave
    return np.clip(y * 255, 0, 255).astype(np.uint8)
GRADE = [  # (R, G, B) por escena: sombras frías / altas cálidas
 [_lut(.02, 1.0, 1.04), _lut(.02, 1.02, .98), _lut(.05, .98, .96)],
 [_lut(.03, .98, 1.05), _lut(.02, 1.0, .98), _lut(.03, 1.04, .9)],
 [_lut(.0, 1.0, .98), _lut(.02, 1.0, 1.0), _lut(.05, .96, 1.05)],
 [_lut(.03, .96, 1.06), _lut(.01, 1.02, .97), _lut(.03, 1.03, .92)],
 [_lut(.03, .97, 1.05), _lut(.02, 1.0, 1.0), _lut(.02, 1.05, .9)],
]
_gr = np.random.RandomState(7)
GRAIN = [cv2.GaussianBlur(_gr.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (0, 0), .7) for _ in range(6)]
def cinema(fr, idx, T):
    lut = GRADE[idx]; fr = cv2.merge([cv2.LUT(fr[:, :, i], lut[i]) for i in range(3)])
    # destello anamórfico horizontal en las luces fuertes
    sm = cv2.resize(fr, (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
    hi = np.clip(sm - 210, 0, None); st = cv2.blur(hi, (61, 1)) * 1.6 + cv2.GaussianBlur(hi, (0, 0), 6) * .6
    st = cv2.resize(st, (W, H), interpolation=cv2.INTER_LINEAR) * np.array([.6, .8, 1.15], np.float32)
    f = fr.astype(np.float32) + st
    # aberración cromática sutil en los bordes
    f[:, :, 0] = cv2.warpAffine(f[:, :, 0], np.float32([[1.0025, 0, -1.35], [0, 1.0025, -2.4]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    f[:, :, 2] = cv2.warpAffine(f[:, :, 2], np.float32([[.9975, 0, 1.35], [0, .9975, 2.4]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    # grano de película (fino, sin parpadeo)
    g = cv2.resize(GRAIN[int(T * FPS) % 6], (W, H), interpolation=cv2.INTER_LINEAR)
    f += g[:, :, None] * 5.5
    return to8(f)

# ---------------------------------------------------------------- audio (síntesis de la plantilla, con nuestros tiempos)
_EF_SRC = """    EF = [[0, 'boom', .9], [.4, 'alarma', .08, 2.6], [2.3, 'beep', .15], [7.9, 'impacto', .7], [9.85, 'whoosh', .5],
          [10.6, 'glitch', .12], [11.4, 'tecleo', .12, 1.2], [18.65, 'impacto', .65], [18.8, 'alarma', .06, 1.4], [16.2, 'latido', .4], [23.25, 'whoosh', .5],
          [24.0, 'viento', .1, 13], [24.9, 'impacto', .8], [32.75, 'impacto', .6], [35.7, 'caida', .3], [36.75, 'whoosh', .5],
          [37.6, 'tecleo', .12, 1.5], [38.3, 'beep', .15], [41.2, 'caida', .3], [42.4, 'dinero', .25], [45.8, 'caida', .25], [48.25, 'whoosh', .5],
          [48.8, 'riser', .2, 2], [53.2, 'ding', .25], [57.9, 'ding', .3]]"""
_EF_NEW = """    EF = [[0, 'boom', .9], [1.5, 'latido', .4], [5.9, 'impacto', .7], [8.4, 'whoosh', .5],
          [10.6, 'impacto', .6], [11.0, 'tecleo', .1, 1.4], [15.0, 'latido', .35], [17.15, 'impacto', .8], [19.5, 'dinero', .25], [20.4, 'dinero', .2], [21.5, 'whoosh', .5],
          [22.3, 'impacto', .6], [24.0, 'viento', .08, 11], [28.4, 'alarma', .05, 1.6], [31.2, 'whoosh', .4], [31.6, 'impacto', .8], [33.6, 'riser', .12, 1.6], [35.3, 'whoosh', .5],
          [36.1, 'impacto', .6], [37.5, 'latido', .4], [41.0, 'latido', .35], [44.3, 'impacto', .8], [47.5, 'whoosh', .5],
          [48.3, 'boom', .6], [49.2, 'caida', .3], [55.6, 'ding', .25], [57.2, 'ding', .3]]"""
_src = open(os.path.join(HERE, 'audio_base.py')).read()
assert _EF_SRC in _src
exec(_src.replace(_EF_SRC, _EF_NEW).replace(
    "VOZ = '/mnt/user-data/uploads/ElevenLabs_2026-11-10T00_49_33_Brian_C__-_Professional_Latin_Narrator_eleven_v4.mp3'", "").replace(
    "secs = [(0, 'tension', 1), (10.3, 'tension', 2), (23.7, 'epico', 2), (37.2, 'misterio', 2), (48.7, 'esperanza', 1)]",
    "secs = [(0, 'tension', 1), (8.9, 'tension', 2), (22.0, 'epico', 2), (35.8, 'misterio', 2), (48.0, 'tension', 1)]").replace(
    "'/home/claude/voz44.wav'", "os.path.join(OUT, 'voz44.wav')"))

# ---------------------------------------------------------------- render
def render_scene(sc, t, d, Tg):
    fr = sc.bg.copy(); sc.draw(fr, t, d); z, cx, cy, dx, dy = sc.cam(t, d)
    # cámara en mano muy suave (sin sacudidas bruscas)
    dx += math.sin(Tg * .73) * 3.2 + math.sin(Tg * 1.31 + 1) * 1.8; dy += math.sin(Tg * .61 + 2) * 2.6 + math.sin(Tg * 1.17) * 1.4
    ang = math.sin(Tg * .45) * .35
    M = cv2.getRotationMatrix2D((cx, cy), ang, z); M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
    lib.rng = rng
    objs = [S1(), S2(), S3(), S4(), S5()]
    scenes = [(SC_T[i], SC_T[i + 1], objs[i]) for i in range(5)]
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in SUBS]; emos = [e + (emoji_sprite(e[2]),) for e in EMOJIS]
    title = objs[0].title
    def frame(T):
        idx = max(i for i, (a, b, _) in enumerate(scenes) if T >= a - 1e-6)
        a, b, sc = scenes[idx]; fr = render_scene(sc, T - a, b - a, T)
        fr = cinema(fr, idx, T)
        if idx > 0 and T - a < .45:
            pa, pb, ps = scenes[idx - 1]; prev = cinema(render_scene(ps, T - pa, pb - pa, T), idx - 1, T); k = ss(0, .45, T - a)
            fr = cv2.addWeighted(prev, 1 - k, fr, k, 0)
        k = ss(5.9, 6.4, T) * (1 - ss(8.5, 8.9, T))
        if k > 0: blit(fr, title, 540, 1265, k * (.9 + .1 * math.sin(T * 6)), lerp(1.3, 1, eOut((T - 5.9) / .5)))
        draw_overlays(fr, T, subs, emos)
        return fr
    if mode == 'test':
        for T in [float(x) for x in sys.argv[2:]]:
            fr = frame(T); cv2.imwrite(f'{OUT}/t_{T:05.1f}.jpg', cv2.resize(fr, (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == 'seg':
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', f'{OUT}/seg_{f0:04d}.mp4']
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(f0, f1): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('SEG', f0, f1, flush=True); return
    if mode == 'audio':
        synth_audio(f'{OUT}/audio.wav'); print('audio ok'); return

if __name__ == '__main__': main()
