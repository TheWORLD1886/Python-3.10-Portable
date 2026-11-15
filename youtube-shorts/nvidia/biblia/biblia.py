#!/usr/bin/env python3
# Biblia visual: una ficha por personaje (frente, 3/4, perfil, expresiones) + tabla de escala. Usa el rig compartido (episodio01/rig.py).
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'episodio01')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'chapo'))
import numpy as np, cv2
import rig as RG
import lib as L
EXPR = {
    'jensen': [('SEGURIDAD', dict(boca='sonrisa', frown=-.1)), ('PREOCUPACIÓN', dict(boca='triste', frown=-.5, brow_up=.25)), ('SORPRESA', dict(boca='o', brow_up=.9)),
               ('TENSIÓN', dict(boca='tensa', frown=.6)), ('TRISTEZA', dict(boca='triste', frown=-.6, look=(0, .35))), ('DESCONCIERTO', dict(boca='tensa', brow_asym=.5, look=(.3, 0)))],
    'alice': [('SERENIDAD', dict(boca='neutra', frown=-.1)), ('MISTERIO', dict(boca='neutra', frown=.2, look=(.45, 0), blink=.3)), ('DESCONFIANZA', dict(boca='tensa', frown=.4, brow_asym=.3, look=(.35, 0))),
              ('CONCENTRACIÓN', dict(boca='neutra', frown=.5, look=(0, .3))), ('PREOCUPACIÓN', dict(boca='triste', frown=-.5, brow_up=.3))],
    'colette': [('PROFESIONAL', dict(boca='sonrisa', frown=-.1)), ('SEGURIDAD', dict(boca='neutra', frown=.1)), ('ATENCIÓN', dict(boca='neutra', brow_up=.3, look=(.3, 0))), ('FIRMEZA', dict(boca='tensa', frown=.4))],
    'agente': [('SERIO', dict(boca='neutra', frown=.35)), ('ALERTA', dict(boca='tensa', frown=.5, look=(.4, 0))), ('INFORMA', dict(boca='habla', abre=.6, frown=.2)), ('SORPRESA CONTENIDA', dict(boca='neutra', brow_up=.5))],
}
DESC = {'jensen': ['Cabeza esférica blanca, ojos ovalados negros', 'Pelo gris peinado hacia atrás (no tapa cejas)', 'Chaqueta de cuero negra con cierre, camiseta negra',
                   'Altura 1.00 (referencia de escala)'],
        'alice': ['Melena negra a la mandíbula, cuello visible', 'Blazer color crema, pantalón oscuro', 'Silueta estilizada · altura 0.94', 'Expresiones sutiles'],
        'colette': ['Melena rubia hasta la mandíbula', 'Traje ejecutivo azul marino', 'Postura erguida · altura 0.95', 'Aparece solo en el giro final'],
        'agente': ['Traje oscuro, corbata negra', 'Gafas oscuras y auricular discreto', 'Carpeta / dispositivo como accesorio', 'Movimientos contenidos · altura 1.00']}
BG = (26, 28, 36)
def txt(fr, s, x, y, px=30, col=(255, 255, 255)): L.blit(fr, L.text_sprite(s, px, col + (255,), pad=6, spacing=2), x, y)
def head_crop(who, pose, size=260):
    c = np.full((900, 700, 3), BG, np.uint8); RG.person(c, who, 350, 880, 820, pose, 0.)
    u = 820 * RG.CAST[who]['alto'] / 8.; hy = 880 - 3.35 * u - 2.45 * u - 1.25 * u * RG.CAST[who]['cabeza'] + .2 * u
    y0 = int(max(0, hy - 1.5 * u)); return cv2.resize(c[y0:y0 + int(3.1 * u), int(350 - 1.55 * u):int(350 + 1.55 * u)], (size, size))
def sheet(who):
    fr = np.full((1500, 2000, 3), BG, np.uint8); c = RG.CAST[who]; H_ = 760
    txt(fr, c['nombre'], 1000, 60, 64, (150, 240, 110) if who == 'jensen' else (255, 210, 120))
    for i, (lab, x) in enumerate((('FRENTE', 330), ('TRES CUARTOS', 760), ('PERFIL', 1180))):
        fy = 940; cv2.line(fr, (x - 220, fy), (x + 220, fy), (70, 74, 90), 3)
        if i == 0: RG.person(fr, who, x, fy, H_, dict(frown=.1), 0.)
        elif i == 1: RG.person_34(fr, who, x, fy, H_, dict(frown=.1), 0., turn=1)
        else: RG.person_side(fr, who, x, fy, H_, dict(frown=.1, look=(.55, 0)), 0., facing=1)
        txt(fr, lab, x, 990, 30, (200, 210, 230))
    u = H_ / 8.                                                              # reglas de proporción (unidades u = altura / 8)
    for k in range(9): y = 940 - k * u; cv2.line(fr, (60, int(y)), (90, int(y)), (110, 120, 140), 2); txt(fr, f'{k}u', 40, int(y), 18, (140, 150, 170))
    for i, d in enumerate(DESC[who]): sp = L.text_sprite('• ' + d, 24, (255, 255, 255, 255), pad=6, spacing=1); L.blit(fr, sp, 1400 + sp.shape[1] / 2, 240 + i * 70)
    for i, (lab, pose) in enumerate(EXPR[who]):
        x = 150 + i * 300; fr[1060:1320, x - 130:x + 130] = head_crop(who, pose); cv2.rectangle(fr, (x - 130, 1060), (x + 130, 1320), (70, 74, 90), 2)
        txt(fr, lab, x, 1355, 24, (230, 230, 240))
    cv2.imwrite(os.path.join(HERE, f'ficha_{who}.png'), fr[:, :, ::-1])
def scale():
    fr = np.full((1000, 1600, 3), BG, np.uint8); cv2.line(fr, (80, 900), (1520, 900), (70, 74, 90), 3)
    for i, w in enumerate(('jensen', 'alice', 'colette', 'agente', 'portavoz', 'directora')):
        x = 190 + i * 245; RG.person(fr, w, x, 900, 700, dict(frown=0.), 0.); txt(fr, RG.CAST[w]['nombre'], x, 950, 24)
    for k in range(9): y = 900 - k * 700 / 8.; cv2.line(fr, (60, int(y)), (1540, int(y)), (44, 48, 60), 1)
    txt(fr, 'ESCALA COMÚN · líneas cada 1u (altura de referencia = 8u)', 800, 40, 30, (200, 210, 230))
    cv2.imwrite(os.path.join(HERE, 'escala_personajes.png'), fr[:, :, ::-1])
if __name__ == '__main__':
    for w in EXPR: sheet(w)
    scale(); print('ok')
