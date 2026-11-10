#!/usr/bin/env python3
# Short: ¿Y si El Chapo regresara a México? (61 s, 1080x1920) · estilo plantilla + profundidad 3D
import narco_short as N
import narco3d as D
from narco3d import *

DUR = 61
VOZ = os.path.join(HERE, 'voz.mp3')
SC_T = [0, 9.9, 24.1, 37.2, 50.2, DUR]

SUBS = [
 (0.00, 2.40, 1460, "¿Y si el capo *más famoso* del mundo…"), (2.55, 4.40, 1460, "*regresara a México*?"),
 (4.65, 7.10, 1460, "¿Una jugada legal *imposible*…"), (7.20, 9.60, 1460, "o el inicio de una *pesadilla*?"),
 (10.10, 11.60, 1500, "Primero…"), (11.65, 13.60, 1500, "la *tormenta jurídica*."), (13.90, 16.50, 1500, "Un cambio en los *tratados internacionales*"),
 (16.55, 19.40, 1500, "obligaría a *Washington* a revisar su caso."), (19.75, 21.60, 1500, "Las cortes *estallarían*"), (21.60, 23.90, 1500, "en un debate *sin precedentes*."),
 (24.30, 25.70, 1440, "Segundo…"), (25.72, 27.50, 1440, "el *caos penitenciario*."), (27.60, 29.20, 1440, "¿Dónde lo *meterían*?"),
 (29.35, 31.00, 1440, "*El Altiplano* o *Puente Grande*"), (31.00, 33.40, 1440, "revivirían los *fantasmas* de sus fugas."), (33.55, 36.80, 1440, "La *alerta roja* se activaría al instante."),
 (37.40, 38.95, 1480, "Tercero…"), (39.00, 40.70, 1480, "el *gran escape*."), (40.90, 43.00, 1480, "En un traslado *nocturno*,"), (43.00, 44.40, 1480, "la *seguridad se rompe*…"),
 (44.40, 45.75, 1480, "y *desaparece de nuevo*,"), (45.78, 47.40, 1480, "con su ropa de siempre:"), (47.40, 49.90, 1480, "*camisa sencilla* y *vaqueros*."),
 (50.40, 53.60, 1480, "Una *pesadilla diplomática* para dos naciones…"), (53.70, 56.30, 1480, "¿Volvería a mandar desde las *sombras*?"),
 (56.40, 58.40, 1480, "¡*Dale like* y *sígueme*"), (58.40, 61.00, 1480, "para más historias!"),
]
EMOJIS = [
 (2.6, 4.6, '🇲🇽', 860, 900, 150, 'pop'), (7.3, 9.6, '⚠️', 200, 900, 150, 'late'),
 (14.4, 17.0, '📄', 860, 1180, 140, 'sacude'), (19.8, 23.8, '⚖️', 200, 1180, 150, 'flota'),
 (25.8, 28.2, '🏛️', 880, 1250, 140, 'pop'), (33.7, 36.8, '🚨', 200, 1250, 150, 'late'),
 (43.3, 45.6, '🔥', 860, 1250, 150, 'late'), (44.6, 47.3, '🏃', 200, 1250, 150, 'cae'),
 (53.8, 61, '💬', 180, 380, 140, 'late'), (56.5, 61, '👍', 540, 300, 150, 'pop'), (57.7, 61, '🔔', 900, 380, 140, 'sacude'),
]

def fence(img, y0, y1, x0=0, x1=W, col=(150, 156, 168)):
    for x in range(x0, x1, 18):
        cv2.line(img, (x, y0), (x + 30, y1), col, 1, cv2.LINE_AA); cv2.line(img, (x + 30, y0), (x, y1), col, 1, cv2.LINE_AA)
    for x in range(x0, x1, 180): cv2.line(img, (x, y0 - 30), (x, y1), (110, 116, 126), 6, cv2.LINE_AA)
    cv2.line(img, (x0, y0), (x1, y0), (110, 116, 126), 4)
    for x in range(x0, x1, 26): cv2.ellipse(img, (x, y0 - 22), (15, 18), 0, 0, 360, (190, 196, 206), 2, cv2.LINE_AA)  # concertina

# ================================================================ 1 · ADX Florence, Colorado
class C1:
    def __init__(s):
        sky = vgrad([(0, (3, 6, 18)), (.4, (12, 20, 44)), (.62, (30, 40, 70)), (1, (30, 40, 70))])
        for i in range(320): x, y = rng.randint(0, W), rng.randint(0, 900); sky[y:y + 2, x:x + 2] += rng.uniform(60, 220)
        radial(sky, (820, 240), 140, (220, 230, 255), .5); radial(sky, (820, 240), 40, (250, 250, 255), 1.)
        s.back = [(dof(rgba(sky, np.ones((H, W))), 2), .12)]
        mt = np.zeros((H, W, 4), np.uint8); xs = np.linspace(-60, W + 60, 13); r_ = np.random.RandomState(3)
        peaks = [(x, 760 - r_.uniform(80, 300)) for x in xs]
        poly(mt, [(-60, 980)] + peaks + [(W + 60, 980)], (34, 42, 66, 255))
        for (x, y) in peaks: poly(mt, [(x - 50, y + 60), (x, y), (x + 50, y + 60), (x + 20, y + 50), (x, y + 70), (x - 20, y + 50)], (200, 210, 230, 255))
        s.back.append((dof(haze(mt, (30, 40, 70), .4), 3), .3))
        # complejo penitenciario (plano medio)
        pr = np.zeros((H, W, 4), np.uint8)
        for (x0, x1, top) in [(0, 380, 880), (380, 700, 840), (700, W, 900)]:
            cv2.rectangle(pr, (x0, top), (x1, 1060), (96, 100, 108, 255), -1)
            for x in range(x0 + 20, x1 - 20, 46): cv2.rectangle(pr, (x, top + 40), (x + 8, top + 110), (30, 34, 40, 255), -1)   # ventanas-ranura
            cv2.rectangle(pr, (x0, top), (x1, top + 12), (120, 124, 132, 255), -1)
        cv2.rectangle(pr, (900, 560), (980, 1060), (84, 88, 96, 255), -1); cv2.rectangle(pr, (870, 520), (1010, 600), (70, 74, 82, 255), -1)
        cv2.rectangle(pr, (880, 540), (1000, 580), (255, 210, 140, 255), -1)          # garita iluminada
        prf = pr[:, :, :3].astype(np.float32); radial(prf, (940, 560), 160, (255, 200, 120), .25); pr[:, :, :3] = to8(prf)
        s.back.append((dof(haze(pr, (30, 40, 70), .25), 1.4), .62))
        # patio (plano principal) con doble malla y alambre de púas
        m = np.zeros((H, W, 3), np.uint8); m[1060:] = (52, 54, 60)
        for j in range(1, 10): y = int(1060 + (H - 1060) * (j / 9.) ** 1.8); cv2.line(m, (0, y), (W, y), (66, 68, 76), 2, cv2.LINE_AA)
        for k in range(-12, 13): cv2.line(m, (540, 1060), (540 + k * 200, H), (60, 62, 70), 2, cv2.LINE_AA)
        fence(m, 1000, 1150); al = np.zeros((H, W), np.float32); al[1060:] = 1; al[np.any(m > 0, 2)] = 1
        mf = m.astype(np.float32); radial(mf, (540, 1400), 600, (255, 140, 60), .12); s.main = rgba(mf, al)
        bars = np.zeros((H, W, 4), np.uint8)
        for x in list(range(-20, 170, 60)) + list(range(930, W + 40, 60)): cv2.rectangle(bars, (x, 0), (x + 26, H), (70, 74, 82, 255), -1); cv2.rectangle(bars, (x + 4, 0), (x + 10, H), (130, 136, 146, 255), -1)
        cv2.rectangle(bars, (0, 300), (170, 330), (70, 74, 82, 255), -1); cv2.rectangle(bars, (930, 300), (W, 330), (70, 74, 82, 255), -1)
        s.front = [(dof(bars, 10), 1.5), (bokeh_layer(10, (255, 180, 90), 4, ymin=500, ymax=1800), 1.7)]
        s.panel = N.holo_panel(760, 210, 'EXTRADICIÓN INVERSA', 'ADX FLORENCE · COLORADO, EE. UU.')
        s.dust = Dust(40, (40, 300, 1040, 1600), (200, 220, 255), 4, .45)
    def draw(s, fr, t, d):
        # reflector de la torre barriendo el patio
        a = math.sin(t * .9) * .5; p0 = (940, 600); p1 = (540 + math.sin(t * .9) * 520, 1500)
        lay = np.zeros((H // 4, W // 4, 3), np.float32)
        cv2.fillPoly(lay, [np.array([(p0[0] // 4, p0[1] // 4), (int(p1[0] // 4 - 60), int(p1[1] // 4)), (int(p1[0] // 4 + 60), int(p1[1] // 4))], np.int32)], (255, 240, 200))
        lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 6), (W, H)); fr[:] = np.clip(fr + lay * .16, 0, 255).astype(np.uint8)
        # luces de patrulla (roja / azul) en la garita
        on = (t * 2) % 1 < .5
        blit(fr, glow_sprite(90, (255, 40, 40) if on else (40, 90, 255)), 940, 530, .9, add=True)
        s.dust.draw(fr, t)
        cv2.ellipse(fr, (540, 1534), (170, 22), 0, 0, 360, (24, 24, 28), -1, cv2.LINE_AA)
        character(fr, 'reo', 540, 1530, 520, t, armR=('apunta', (580, 1300), .75), armL=('apunta', (500, 1300), .75),
                  look=(0, -.15), frown=-.3, smile=.3, mustache=True, cuffs=True)
        k = ss(2.6, 3.2, t)
        if k > 0: blit(fr, s.panel, 540, 640 + math.sin(t * 1.5) * 5, k, lerp(1.25, 1, eOut((t - 2.6) / .6)))
    def cam(s, t, d):
        k = eExpo(t / 1.6)
        return lerp(2.4, 1.05, k) * (1 + .06 * ss(1.6, d, t)), 540, lerp(1350, 1050, k), lerp(-40, 40, eIO(t / d)) * ss(1, 2.5, t), 0

# ================================================================ 2 · Corte federal
class C2:
    def __init__(s):
        wall = vgrad([(0, (14, 12, 18)), (.7, (34, 26, 24)), (1, (20, 16, 14))]); i8 = to8(wall)
        for x in (140, 460, 780):
            cv2.rectangle(i8, (x, 160), (x + 180, 820), (40, 56, 84), -1)
            for k in range(1, 4): cv2.line(i8, (x, 160 + k * 165), (x + 180, 160 + k * 165), (24, 30, 44), 6)
            cv2.line(i8, (x + 90, 160), (x + 90, 820), (24, 30, 44), 6); cv2.rectangle(i8, (x, 160), (x + 180, 820), (90, 80, 70), 10)
        cv2.circle(i8, (540, 110), 70, (170, 140, 60), -1, cv2.LINE_AA); cv2.circle(i8, (540, 110), 52, (110, 86, 30), -1, cv2.LINE_AA)
        wf = i8.astype(np.float32)
        for x in (230, 550, 870): beam(wf, (x, 200), (x - 160, 1500), 80, 260, (150, 180, 230), .07, 40)
        s.back = [(dof(rgba(wf, np.ones((H, W))), 4), .35)]
        mid = np.zeros((H, W, 4), np.uint8)
        cv2.rectangle(mid, (240, 860), (840, 1080), (78, 40, 20, 255), -1); cv2.rectangle(mid, (220, 840), (860, 870), (110, 60, 30, 255), -1)   # estrado del juez
        for x in (60, 760):
            cv2.rectangle(mid, (x, 1130), (x + 260, 1200), (90, 48, 24, 255), -1); cv2.rectangle(mid, (x + 10, 1200), (x + 30, 1320), (60, 30, 14, 255), -1); cv2.rectangle(mid, (x + 230, 1200), (x + 250, 1320), (60, 30, 14, 255), -1)
            cv2.ellipse(mid, (x + 200, 1110), (40, 22), 0, 180, 360, (30, 110, 60, 255), -1, cv2.LINE_AA)
        mf = mid[:, :, :3].astype(np.float32)
        for x in (260, 960): radial(mf, (x, 1120), 120, (255, 220, 150), .4)
        mid[:, :, :3] = to8(mf); s.back.append((dof(mid, 1.6), .7))
        floor = np.zeros((H, W, 3), np.uint8); floor[1300:] = (40, 26, 20)
        for j in range(1, 10): y = int(1300 + (H - 1300) * (j / 9.) ** 1.6); cv2.line(floor, (0, y), (W, y), (56, 36, 26), 2, cv2.LINE_AA)
        al = np.zeros((H, W)); al[1300:] = 1; s.main = rgba(floor, al)
        lec = np.zeros((H, W, 4), np.uint8); poly(lec, [(-40, 1380), (300, 1380), (260, 1920), (-40, 1920)], (60, 32, 16, 255)); cv2.rectangle(lec, (-40, 1370), (320, 1400), (100, 56, 28, 255), -1)
        s.front = [(dof(lec, 10), 1.5), (bokeh_layer(8, (255, 220, 160), 7, ymin=300, ymax=1400), 1.7)]
        s.doc = N.holo_panel(240, 300, 'CASO', 'EXP. 09-CR-466')
        im = Image.fromarray(s.doc); dd = ImageDraw.Draw(im)
        for k in range(7): dd.line((30, 160 + k * 18, 210 - (k * 37) % 70, 160 + k * 18), fill=(150, 230, 255, 200), width=5)
        s.doc = np.array(im)
        s.panel = N.holo_panel(860, 210, 'TRATADO MÉXICO · EE. UU.', 'REVISIÓN DEL CASO')
        s.stamp = N.stamp('APELACIÓN', (255, 59, 42), w=640, px=86)
        s.dust = Dust(36, (40, 200, 1040, 1500), (255, 220, 170), 4, .4)
    def draw(s, fr, t, d):
        s.dust.draw(fr, t)
        cv2.ellipse(fr, (540, 1594), (170, 22), 0, 0, 360, (20, 12, 8), -1, cv2.LINE_AA)
        look = math.sin(t * .8) * .5
        character(fr, 'reo', 540, 1590, 500, t, armR=('apunta', (580, 1360), .75), armL=('apunta', (500, 1360), .75), look=(look, -.2), frown=-.3, smile=.3, mustache=True, cuffs=True)
        o = ss(1.5, 2.3, t)
        for i in range(5):  # documentos legales orbitando
            a = t * .55 + i * 2 * math.pi / 5; x = 540 + math.cos(a) * 380; y = 1150 + math.sin(a) * 170
            sc = .55 + .25 * (math.sin(a) + 1) / 2
            if math.sin(a) < 0: blit(fr, s.doc, x, y - 120, o * .8, sc)
        k = ss(4.4, 5.0, t) * (1 - ss(9.6, 10.0, t))
        if k > 0: blit(fr, s.panel, 540, 560 + math.sin(t * 1.4) * 5, k, lerp(1.2, 1, eOut((t - 4.4) / .6)))
        k2 = ss(10.6, 10.9, t)
        if k2 > 0: blit(fr, s.stamp, 540, 560, k2, lerp(1.6, 1., eOut(k2)))
    def front_docs(s, fr, t):
        o = ss(1.5, 2.3, t)
        for i in range(5):
            a = t * .55 + i * 2 * math.pi / 5; x = 540 + math.cos(a) * 380; y = 1150 + math.sin(a) * 170
            sc = .55 + .25 * (math.sin(a) + 1) / 2
            if math.sin(a) >= 0: blit(fr, s.doc, x, y - 120, o * .9, sc)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.05, 1.15, k), 540, lerp(1100, 1180, k), lerp(-55, 55, k), 0

# ================================================================ 3 · Mapa táctico: prisiones y alerta roja
ALT = (-99.77, 19.37); PG = (-103.15, 20.57); ADX = (-105.1, 38.4)
class C3(D.S3D):
    def __init__(s):
        super().__init__()
        s.cd = prj(*ALT)
        s.arrows = [(ALT, (-96.1, 19.2)), (ALT, (-100.3, 25.7)), (ALT, (-106.4, 31.7)), (ALT, (-103.4, 20.7)), (ALT, (-92.6, 16.8))]
        s.labels = [(N.text_sprite('EL ALTIPLANO · FUGA 2015', 34, (255, 230, 220, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=3), ALT, (190, 70)),
                    (N.text_sprite('PUENTE GRANDE · FUGA 2001', 34, (255, 230, 220, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=3), PG, (-150, -80))]
        s.lab_adx = N.text_sprite('ADX FLORENCE', 32, (180, 220, 255, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=4)
        s.alert = N.stamp('MÁXIMA ALERTA', (255, 50, 40), w=760, h=130, px=84, fill=(40, 6, 6, 200))
        cta = np.zeros((120, 560, 4), np.uint8); im = Image.fromarray(cta); dd = ImageDraw.Draw(im)
        dd.rounded_rectangle((4, 4, 555, 115), 56, fill=(200, 20, 20, 230), outline=(255, 255, 255, 255), width=4); cta = np.array(im)
        over(cta, N.text_sprite('DALE LIKE · SÍGUEME', 40, (255, 255, 255, 255), spacing=3, pad=10), 300, 60)
        e1 = emoji_sprite('👍'); over(cta, cv2.resize(e1, (76, 76)), 62, 60); s.cta = cta; s.bell = emoji_sprite('🔔')
        s.prison = glow_sprite(60, (255, 50, 40))
    def draw(s, fr, t, d):
        super().draw(fr, t, d)
        # ruta del traslado desde ADX Florence (línea punteada azul)
        k = ss(.5, 3.0, t)
        if k > 0:
            p0, p1 = A(*prj(*ADX)), A(*prj(*ALT)); mid = (p0 + p1) / 2 + A(-160, 0)
            pts = [tuple((1 - u_) ** 2 * p0 + 2 * (1 - u_) * u_ * mid + u_ ** 2 * p1) for u_ in np.linspace(0, k, 60)]
            for i in range(0, len(pts) - 1, 2): line(fr, pts[i], pts[i + 1], (120, 200, 255), 6)
            circ(fr, tuple(p0), 12, (120, 200, 255)); blit(fr, s.lab_adx, p0[0] + 10, p0[1] - 40)
        for spr, ll, off in s.labels:
            a = ss(5.2, 5.8, t)
            if a > 0:
                x, y = prj(*ll); pul = .6 + .4 * math.sin(t * 5)
                blit(fr, s.prison, x, y, a * pul, add=True)
                cv2.rectangle(fr, (int(x - 22), int(y - 18)), (int(x + 22), int(y + 18)), (230, 230, 236), -1)
                for b in range(4): cv2.line(fr, (int(x - 15 + b * 10), int(y - 18)), (int(x - 15 + b * 10), int(y + 18)), (40, 40, 48), 3)
                blit(fr, spr, x + off[0], y + off[1], a)
    def floating(s, fr, t, d, P):
        k = ss(9.4, 9.8, t)
        if k > 0:
            pul = .82 + .18 * math.sin(t * 5)
            sh = np.zeros_like(s.alert); sh[:, :, 3] = (s.alert[:, :, 3] * .55).astype(np.uint8)
            blit(fr, cv2.GaussianBlur(sh, (0, 0), 14), 560, 660, k * .8)
            blit(fr, s.alert, 540, 450 + math.sin(t * 1.6) * 6, k * pul, lerp(1.6, 1., eOut(k)))
        c = ss(3.4, 3.8, t) * (1 - ss(8.4, 8.8, t))     # llamada a la acción a mitad de video
        if c > 0:
            blit(fr, s.cta, 600, 330, c, lerp(.6, 1, eBack((t - 3.4) / .4)) * .78)
            blit(fr, s.bell, 840, 300 + math.sin(t * 9) * 4 * c, c, .5)
        s.dust.draw(fr, t)

# ================================================================ 4 · El gran escape en la carretera
class C4:
    def __init__(s):
        sky = vgrad([(0, (8, 6, 14)), (.45, (40, 22, 18)), (.6, (120, 66, 30)), (1, (120, 66, 30))])
        radial(sky, (540, 1080), 700, (255, 150, 60), .3)
        s.back = [(dof(rgba(sky, np.ones((H, W))), 2), .1)]
        mt = np.zeros((H, W, 4), np.uint8); r_ = np.random.RandomState(8)
        poly(mt, [(-60, 1120)] + [(x, 1020 - r_.uniform(20, 160)) for x in np.linspace(-60, W + 60, 16)] + [(W + 60, 1120)], (40, 26, 26, 255))
        s.back.append((dof(haze(mt, (120, 66, 30), .5), 3), .25))
        # camionetas blindadas detenidas con puertas abiertas (plano medio)
        tr = np.zeros((H, W, 4), np.uint8)
        for (x, y, sc) in [(150, 1120, 1.0), (760, 1110, .9)]:
            w, h = int(300 * sc), int(130 * sc)
            cv2.rectangle(tr, (x, y - h), (x + w, y), (24, 26, 30, 255), -1); cv2.rectangle(tr, (x + int(20 * sc), y - h - int(60 * sc)), (x + int(200 * sc), y - h), (24, 26, 30, 255), -1)
            cv2.rectangle(tr, (x + int(40 * sc), y - h - int(48 * sc)), (x + int(180 * sc), y - h - int(8 * sc)), (60, 80, 100, 255), -1)
            poly(tr, [(x + w, y - h), (x + w + int(80 * sc), y - h - int(30 * sc)), (x + w + int(80 * sc), y - int(20 * sc)), (x + w, y)], (34, 36, 40, 255))   # puerta abierta
            for wx in (x + int(60 * sc), x + w - int(60 * sc)): cv2.circle(tr, (wx, y), int(40 * sc), (10, 10, 12, 255), -1, cv2.LINE_AA)
        s.back.append((dof(haze(tr, (120, 66, 30), .15), 1.5), .62))
        s.lights = [(330, 980), (920, 990)]
        road = np.zeros((H, W, 3), np.uint8); road[1120:] = (34, 28, 26)
        poly(road, [(470, 1120), (610, 1120), (1300, H), (-220, H)], (50, 46, 46))
        for j in range(8): y0 = int(1130 + (H - 1130) * (j / 8.) ** 1.7); y1 = int(1130 + (H - 1130) * ((j + .5) / 8.) ** 1.7); cv2.line(road, (540, y0), (540, y1), (220, 190, 80), 4 + j * 2)
        al = np.zeros((H, W)); al[1120:] = 1; s.main = rgba(road, al)
        bush = np.zeros((H, W, 4), np.uint8); r_ = np.random.RandomState(12)
        for i in range(30):
            x = r_.uniform(-100, W + 100); y = r_.uniform(1640, 1900); r = r_.uniform(40, 110)
            cv2.circle(bush, (int(x), int(y)), int(r), (18, 22, 14, 255), -1, cv2.LINE_AA)
        s.front = [(dof(bush, 9), 1.9), (bokeh_layer(16, (255, 140, 50), 13, rmin=10, rmax=40, ymin=400, ymax=1700), 1.6)]
        s.puff = glow_sprite(140, (110, 96, 90)); s.flame = glow_sprite(90, (255, 150, 50))
        s.stamp = N.stamp('LIBRE', (255, 59, 42), w=480, px=110)
        s.dust = Dust(40, (40, 300, 1040, 1600), (255, 170, 90), 4, .5)
    def draw(s, fr, t, d):
        for i in range(18):
            f = (i / 18. + t * .05) % 1; blit(fr, s.puff, 300 + (i % 3) * 220 + f * 160, 1080 - f * 800, min(1, f * 5) * (1 - f) * .4, .9 + f * 2.4)
        on = (t * 2.5) % 1 < .5
        for i, (x, y) in enumerate(s.lights): blit(fr, glow_sprite(70, (255, 40, 40) if on ^ (i % 2) else (40, 90, 255)), x, y, .9, add=True)
        brk = ss(6.0, 6.4, t)
        if brk > 0 and t < 8: blit(fr, s.flame, 600, 1150, brk * (1 - ss(6.6, 8, t)), 2.4, add=True)
        s.dust.draw(fr, t)
        if t < 6.3:   # traslado: con uniforme y esposas
            cv2.ellipse(fr, (560, 1494), (150, 20), 0, 0, 360, (16, 12, 10), -1, cv2.LINE_AA)
            character(fr, 'reo', 560, 1490, 440, t, armR=('apunta', (600, 1290), .75), armL=('apunta', (520, 1290), .75), look=(-.6, -.1), frown=-.2, mustache=True, cuffs=True)
        else:         # escape: camisa a cuadros y vaqueros, corriendo hacia la oscuridad
            u = ss(6.3, 12.5, t); x = lerp(620, 180, u); sc = lerp(1, .62, u); fy = lerp(1500, 1250, u)
            cv2.ellipse(fr, (int(x), int(fy + 4)), (int(130 * sc), int(18 * sc)), 0, 0, 360, (16, 12, 10), -1, cv2.LINE_AA)
            sw = math.sin(t * 11)
            character(fr, 'civil', x, fy, 440 * sc, t, armR=('apunta', (x + 260 * sw, fy - 330 * sc), .9), armL=('apunta', (x - 260 * sw, fy - 330 * sc), .9),
                      look=(-.8, 0), frown=-.3, smile=.5, mustache=True, run=11, cap=True)
            if u > .7: fr[:] = fr  # se pierde en la oscuridad (lo da la viñeta y la bruma)
        k = ss(8.6, 8.9, t)
        if k > 0: blit(fr, s.stamp, 540, 560, k, lerp(1.6, 1., eOut(k)))
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.05, 1.14, k), 540, 1150, lerp(60, -80, ss(6, d, t)), 0

# ================================================================ 5 · Cierre: globo, balanza agrietada, narrador
class C5(D.S5D):
    def __init__(s):
        super().__init__()
        s.cta = N.holo_panel(640, 200, '¿TÚ QUÉ OPINAS?', 'COMENTA ABAJO')
        ban = np.zeros((130, 760, 4), np.uint8); im = Image.fromarray(ban); dd = ImageDraw.Draw(im)
        dd.rounded_rectangle((4, 4, 755, 125), 60, fill=(210, 20, 20, 235), outline=(255, 255, 255, 255), width=5); ban = np.array(im)
        over(ban, N.text_sprite('DALE LIKE Y SÍGUEME', 56, (255, 255, 255, 255), spacing=3, pad=10, maxw=600), 410, 66)
        over(ban, cv2.resize(emoji_sprite('👍'), (86, 86)), 70, 66); s.banner = ban
        s.redg = glow_sprite(160, (255, 40, 30))
    def draw(s, fr, t, d):
        R, n = s.R, s.n; c = n / 2 - .5; la0 = 18; lo0 = lerp(-160, -101, eOut(t / 3.0)) + ss(3.0, 12, t) * 5
        pul = .5 + .5 * math.sin(t * 2.4)
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
        k = .82 + .18 * pul; fill(MX, (int(255 * k), int(192 * k), int(64 * k)), (255, 238, 176), 3)
        fill(NA, (int(120 * k), int(150 * k), int(200 * k)), (200, 220, 255), 2)
        gf = g.astype(np.float32) * s.shade + s.addl
        x0, y0 = int(s.cx - n / 2), int(s.cy - n / 2); roi = fr[y0:y0 + n, x0:x0 + n]
        roi[:] = np.clip(roi * (1 - s.mask) + gf * s.mask, 0, 255)
        blit(fr, s.redg, 200, 1040, .35 + .3 * math.sin(t * 4), add=True)   # balanza agrietada que late en rojo
        pline(fr, [(200, 930), (186, 980), (214, 1020), (194, 1080)], (255, 70, 50), 5)
        s.dust.draw(fr, t)
        o = ss(3.5, 4.1, t)
        if o > 0: blit(fr, s.cta, 420, 1000 + math.sin(t * 1.6) * 5, o, lerp(1.2, 1, eOut((t - 3.5) / .6)))
        b = ss(6.2, 6.6, t)
        if b > 0: blit(fr, s.banner, 430, 1225, b, lerp(.6, 1, eBack((t - 6.2) / .4)) * (1 + .03 * math.sin(t * 6)))
        cv2.ellipse(fr, (870, 1424), (150, 22), 0, 0, 360, (16, 10, 7), -1, cv2.LINE_AA)
        point = ss(.6, 1.3, t)
        armR = ('apunta', (540, 2600), point) if t < 6.0 else ('palma',)
        character(fr, 'elegante', 870, 1420, 430, t, armR=armR, armL=('jarra',), look=(.2, .2 * point), frown=.1, smile=.6 + .3 * ss(6, 7, t))

# ---------------------------------------------------------------- audio
_src = open(os.path.join(HERE, 'audio_base.py')).read()
_EF = """    EF = [[0, 'boom', .9], [.3, 'latido', .35], [2.6, 'impacto', .6], [8.9, 'whoosh', .5],
          [10.2, 'impacto', .6], [11.7, 'viento', .06, 6], [14.4, 'tecleo', .1, 1.2], [19.8, 'latido', .35], [20.7, 'impacto', .8], [23.4, 'whoosh', .5],
          [24.3, 'impacto', .6], [25.8, 'beep', .12], [27.5, 'pop', .15], [29.4, 'latido', .35], [33.6, 'alarma', .05, 2.4], [36.7, 'whoosh', .5],
          [37.5, 'impacto', .6], [38.2, 'viento', .08, 8], [43.2, 'boom', .7], [44.5, 'whoosh', .5], [45.8, 'impacto', .7], [49.6, 'whoosh', .5],
          [50.4, 'boom', .5], [53.8, 'riser', .12, 2.4], [56.5, 'ding', .3], [57.7, 'ding', .25]]"""
_a = _src.index('    EF = ['); _b = _src.index(']]', _a) + 2
_src = _src[:_a] + _EF + _src[_b:]
_src = _src.replace("VOZ = '/mnt/user-data/uploads/ElevenLabs_2026-11-10T00_49_33_Brian_C__-_Professional_Latin_Narrator_eleven_v4.mp3'", "")
_src = _src.replace("secs = [(0, 'tension', 1), (10.3, 'tension', 2), (23.7, 'epico', 2), (37.2, 'misterio', 2), (48.7, 'esperanza', 1)]",
                    "secs = [(0, 'tension', 1), (9.9, 'misterio', 2), (24.1, 'tension', 2), (37.2, 'epico', 2), (50.2, 'tension', 1)]")
_src = _src.replace("'/home/claude/voz44.wav'", "os.path.join(OUT, 'voz44.wav')")
exec(_src)

# ---------------------------------------------------------------- render
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    objs = [C1(), C2(), C3(), C4(), C5()]
    scenes = [(SC_T[i], SC_T[i + 1], objs[i]) for i in range(5)]
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in SUBS]; emos = [e + (emoji_sprite(e[2]),) for e in EMOJIS]
    def one(idx, T):
        a, b, sc = scenes[idx]; fr = render3d(sc, T - a, b - a, T)
        if isinstance(sc, C2): sc.front_docs(fr, T - a)
        return cinema(fr, min(idx, 4), T)
    def frame(T):
        idx = max(i for i, (a, b, _) in enumerate(scenes) if T >= a - 1e-6)
        a = scenes[idx][0]; fr = one(idx, T)
        if idx > 0 and T - a < .45: fr = cv2.addWeighted(one(idx - 1, T), 1 - ss(0, .45, T - a), fr, ss(0, .45, T - a), 0)
        draw_overlays(fr, T, subs, emos); return fr
    if mode == 'test':
        for T in [float(x) for x in sys.argv[2:]]:
            cv2.imwrite(f'{OUT}/c_{T:05.1f}.jpg', cv2.resize(frame(T), (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
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
