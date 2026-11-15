#!/usr/bin/env python3
# Maqueta de cómo se vería el personaje en un envivo vertical (1080x1920). No es la interfaz real de TikTok.
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'episodio01')); sys.path.insert(0, os.path.join(HERE, '..', 'chapo'))
import numpy as np, cv2
import lib as L
import rig as RG
W, H = 1080, 1920
def frame(t, boca='o', subtitle='Según la prensa, nadie ha sido acusado formalmente.'):
    bg = L.vgrad([(0, (8, 10, 24)), (.6, (20, 24, 50)), (1, (10, 12, 26))]); L.radial(bg, (540, 900), 700, (60, 120, 255), .3)
    fr = np.clip(bg, 0, 255).astype(np.uint8)
    for x in range(0, W, 90): cv2.line(fr, (x, 1500), (540 + (x - 540) * 3, H), (40, 60, 120), 2)          # piso neón
    for y in (1500, 1560, 1650, 1780): cv2.line(fr, (0, y), (W, y), (40, 60, 120), 2)
    for i in range(3):                                                                                      # pantallas holográficas detrás
        x = 120 + i * 300; cv2.rectangle(fr, (x, 330), (x + 240, 560), (30, 60, 110), -1); cv2.rectangle(fr, (x, 330), (x + 240, 560), (90, 200, 255), 3)
        for k in range(5): cv2.line(fr, (x + 20, 360 + k * 40), (x + 120 + (k * 37) % 100, 360 + k * 40), (120, 220, 255), 4)
    RG.person(fr, 'jefe', 540, 1560, 900, dict(boca=boca, look=(0, 0), frown=-.2, uR=.55, lR=1.9, blink=0.), t)   # el narrador saluda
    cv2.rectangle(fr, (150, 1300), (930, 1620), (30, 34, 60), -1); cv2.rectangle(fr, (150, 1300), (930, 1322), (90, 200, 255), -1); cv2.rectangle(fr, (150, 1300), (930, 1620), (60, 80, 140), 4)   # escritorio (tapa las piernas)
    pill = L.text_sprite('● EN VIVO', 40, (255, 255, 255, 255), pad=8); cv2.rectangle(fr, (40, 60), (300, 130), (230, 40, 70), -1); L.blit(fr, pill, 170, 95)
    L.blit(fr, L.text_sprite('Contenido generado con IA', 30, (255, 255, 255, 255), stroke=3, stroke_col=(0, 0, 0, 220), pad=6), 830, 95)
    q = L.text_sprite('@usuario123: ¿Qué pasó con NVIDIA?', 38, (20, 20, 30, 255), pad=10)                 # pregunta que está respondiendo
    cv2.rectangle(fr, (60, 190), (1020, 290), (255, 230, 120), -1); L.blit(fr, q, 540, 240)
    for i, c in enumerate(['@ana_mx: ¿Y Bukele?', '@carlos22: saludos desde Monterrey', '@luz.v: ¿cuándo sale el otro short?']):   # comentarios del chat
        sp = L.text_sprite(c, 32, (255, 255, 255, 230), stroke=3, stroke_col=(0, 0, 0, 200), pad=6); L.blit(fr, sp, 50 + sp.shape[1] / 2, 1700 + i * 60)
    L.blit(fr, L.sub_sprite(subtitle), 540, 1470)
    return fr
if __name__ == '__main__':
    cv2.imwrite(os.path.join(HERE, 'maqueta_envivo.png'), frame(0.)[:, :, ::-1])
