#!/usr/bin/env python3
# Hoja de diseño de personajes: cuerpo completo, poses y expresiones de Daniel, Laura y Sofía.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rig import *

HERE = os.path.dirname(os.path.abspath(__file__))
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
def text(img, s, xy, px, col=(240, 240, 240), anchor='mm'):
    im = Image.fromarray(img); d = ImageDraw.Draw(im); d.text(xy, s, font=ImageFont.truetype(FB, px), fill=col, anchor=anchor); img[:] = np.array(im)

EXPR = [('TRANQUILO', dict(frown=-.05, boca='sonrisa')), ('PREOCUPADO', dict(frown=-.38, boca='triste', tilt=.1, look=(.15, .1))),
        ('SORPRESA', dict(frown=-.55, boca='o', look=(0, -.15))), ('MIEDO', dict(frown=-.45, boca='grito', sh=.8, look=(-.2, 0)))]
POSES = {'daniel': dict(uR=2.5, lR=.5, uL=-.15, lL=.2, boca='sonrisa', frown=-.05, thL=-.08, thR=.08),          # saluda con una mano
         'laura': dict(uR=.2, lR=-1.75, uL=-.2, lL=1.75, boca='sonrisa', frown=-.05, look=(-.2, 0), tilt=-.06),   # brazos cruzados suaves
         'sofia': dict(uR=2.6, lR=.3, uL=-2.5, lL=-.3, boca='sonrisa', frown=-.1, thL=-.15, thR=.15)}         # brazos arriba, contenta

W_, H_ = 1920, 1080
sheet = np.zeros((H_, W_, 3), np.uint8)
for y in range(H_): sheet[y] = (int(14 + 10 * y / H_), int(16 + 12 * y / H_), int(28 + 18 * y / H_))
text(sheet, 'EL DÍA QUE TODO TERMINÓ · DISEÑO DE PERSONAJES', (W_ // 2, 46), 40, (255, 224, 160))
for i, who in enumerate(['daniel', 'laura', 'sofia']):
    c = CAST[who]; cx = 320 + i * 640
    cv2.rectangle(sheet, (cx - 300, 90), (cx + 300, 1060), (40, 46, 70), 2)
    text(sheet, c['nombre'], (cx, 130), 46); text(sheet, c['edad'], (cx, 175), 26, (190, 200, 220))
    # cuerpo completo: pose neutra (izquierda) y pose de personalidad (derecha)
    cv2.ellipse(sheet, (cx - 140, 720), (90, 14), 0, 0, 360, (8, 10, 18), -1, cv2.LINE_AA); cv2.ellipse(sheet, (cx + 140, 720), (90, 14), 0, 0, 360, (8, 10, 18), -1, cv2.LINE_AA)
    person(sheet, who, cx - 140, 716, 500, dict(boca='neutra'))
    person(sheet, who, cx + 140, 716, 500, POSES[who])
    text(sheet, 'NEUTRA', (cx - 140, 752), 20, (150, 160, 190)); text(sheet, 'PERSONALIDAD', (cx + 140, 752), 20, (150, 160, 190))
    # expresiones (primeros planos de la cabeza)
    for k, (lab, ex) in enumerate(EXPR):
        big = np.zeros((900, 600, 3), np.uint8); big[:] = (24, 28, 46)
        _, j = person(big, who, 300, 1500, 1500 / CAST[who]['alto'] * .8 if who == 'sofia' else 1500, dict(ex))
        hx, hy = j['head']; r = int(150 if who != 'sofia' else 170)
        crop = big[max(0, int(hy) - r - 30):int(hy) + r - 10, max(0, int(hx) - r):int(hx) + r]
        crop = cv2.resize(crop, (128, 128), interpolation=cv2.INTER_AREA)
        x0 = cx - 280 + k * 142; sheet[800:928, x0:x0 + 128] = crop; cv2.rectangle(sheet, (x0, 800), (x0 + 128, 928), (70, 80, 110), 2)
        text(sheet, lab, (x0 + 64, 948), 16, (200, 210, 230))
    # paleta de colores fija
    sw = [c['top'], c.get('plaid', c['top']), c['pants'], c['shoe'], c['pelo_col']]
    for k, col in enumerate(sw): cv2.rectangle(sheet, (cx - 150 + k * 62, 990), (cx - 100 + k * 62, 1030), col[::-1] if False else col, -1); cv2.rectangle(sheet, (cx - 150 + k * 62, 990), (cx - 100 + k * 62, 1030), (200, 200, 210), 1)
    text(sheet, 'PALETA FIJA', (cx, 1046), 14, (150, 160, 190))
cv2.imwrite(os.path.join(HERE, 'diseno_personajes.png'), sheet[:, :, ::-1])
print('ok')
