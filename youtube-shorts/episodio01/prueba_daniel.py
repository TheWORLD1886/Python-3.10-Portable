#!/usr/bin/env python3
# Plano de prueba: Daniel camina (perfil), frena, gira hacia la cámara y levanta una mano. 6 s, 1080x1920, 30 fps.
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'chapo')); sys.path.insert(0, HERE)
import narco3d as D
from narco3d import dof, rgba, bokeh_layer, render3d, cinema, vgrad, radial, beam, glow_sprite, W, H, FPS, to8
import rig
from rig import *

def opaque(img): return rgba(img, np.ones((H, W)))

class Room:
    """sala de la casa de noche: pared con cuadros y ventana (fondo), piso de madera (plano principal), lámpara y bokeh (frente)."""
    def __init__(s):
        wall = vgrad([(0, (44, 34, 30)), (.65, (70, 54, 44)), (1, (40, 30, 26))]); i8 = to8(wall)
        for x in range(0, W, 64): cv2.line(i8, (x, 0), (x, 1300), (64, 50, 42), 2)                       # papel tapiz
        cv2.rectangle(i8, (640, 420), (980, 900), (16, 24, 44), -1); cv2.rectangle(i8, (640, 420), (980, 900), (120, 90, 60), 14)  # ventana
        for (x, y) in [(700, 760), (760, 700), (850, 780), (930, 720)]: cv2.circle(i8, (x, y), 4, (255, 210, 140), -1)
        cv2.line(i8, (810, 420), (810, 900), (120, 90, 60), 8)
        for (x, y, w, h) in [(120, 380, 180, 230), (340, 470, 140, 110)]:
            cv2.rectangle(i8, (x, y), (x + w, y + h), (150, 120, 70), 10); cv2.rectangle(i8, (x + 10, y + 10), (x + w - 10, y + h - 10), (90, 110, 120), -1)
        cv2.rectangle(i8, (0, 1240), (W, 1300), (90, 66, 48), -1)                                      # zócalo
        wf = i8.astype(np.float32); radial(wf, (300, 300), 600, (255, 190, 120), .25)
        s.back = [(dof(opaque(wf), 2.5), .45)]
        fl = np.zeros((H, W, 3), np.uint8); fl[1300:] = (96, 66, 44); al = np.zeros((H, W)); al[1300:] = 1
        for j in range(1, 10): y = int(1300 + (H - 1300) * (j / 9.) ** 1.6); cv2.line(fl, (0, y), (W, y), (80, 54, 36), 2)
        for k in range(-12, 13): cv2.line(fl, (540 + k * 60, 1300), (540 + k * 260, H), (84, 58, 40), 2)
        s.main = rgba(fl, al)
        lamp = np.zeros((H, W, 4), np.uint8); cv2.ellipse(lamp, (980, 1700), (240, 420), 0, 0, 360, (24, 18, 16, 255), -1)   # sillón borroso
        s.front = [(dof(lamp, 12), 1.5), (bokeh_layer(8, (255, 200, 140), 7, ymin=200, ymax=1200), 1.7)]
        s.u = 780 * CAST['daniel']['alto'] / 8.; s.fy = 1700
        s.D = 2 * step_len(s.u) * 2                                      # termina en fase entera: ambos pies apoyados
        s.x0 = 120
    def walk_x(s, t):
        k = min(1., t / 2.6); return s.D * (k * (2 - k))                  # ease out: viene caminando y frena
    def draw(s, fr, t, d):
        u, fy = s.u, s.fy
        cv2.ellipse(fr, (int(s.x0 + s.walk_x(t)), fy + 6), (120, 18), 0, 0, 360, (50, 34, 24), -1, cv2.LINE_AA)   # sombra de contacto
        if t < 3.45:                                                     # caminar y frenar (perfil)
            dist = s.walk_x(t); x, p, feet, bob = gait(0, s.x0, 1, u, fy, dist=dist)
            v = s.D * 2 * (1 - min(1, t / 2.6)) / 2.6                     # velocidad actual
            k = min(1., v / 300.)                                         # al frenar se apagan balanceo e inclinación
            settle = math.sin(min(1, max(0, (t - 2.6) / .5)) * math.pi) * .05 * u   # el peso baja y se asienta
            p.update(uL=p['uL'] * k, uR=p['uR'] * k, lean=p['lean'] * k + .03 * (1 - k), blink=blink(t, 3), frown=-.05)
            if t > 3.0:                                                   # anticipación del giro: la cabeza voltea primero
                q = ease((t - 3.0) / .45); p['look'] = (.55 * (1 - q), 0.)
            person_side(fr, 'daniel', x, fy + bob * k + settle, 780, p, t, feet=feet, facing=1)
        else:                                                            # de frente: levanta la mano y saluda
            x = s.x0 + s.D
            keys = [(3.45, dict(uR=.1, lR=-.08, uL=-.1, lL=.08, look=(.25, 0), frown=-.05)),
                    (3.75, dict(uR=.15, lR=-.1, uL=-.12, lL=.1, look=(0, 0), sh=.2, frown=-.1)),            # anticipación: hombro baja
                    (4.25, dict(uR=2.45, lR=.55, uL=-.15, lL=.15, look=(0, 0), boca='sonrisa', frown=-.15)), # mano arriba
                    (5.5, dict(uR=2.45, lR=.55, uL=-.15, lL=.15, boca='sonrisa', frown=-.15)),
                    (5.95, dict(uR=.12, lR=-.1, uL=-.1, lL=.08, boca='sonrisa'))]
            p = anim(keys, t)
            if 4.25 < t < 5.5: p['lR'] = .55 + .45 * math.sin((t - 4.25) * 2 * math.pi * 1.8)              # saludo con el antebrazo
            sq = 1 - .03 * math.exp(-((t - 3.5) / .08) ** 2)                                              # ligero squash al plantar el giro
            p['blink'] = blink(t, 3)
            person(fr, 'daniel', x, fy, 780 * sq, p, t)
    def cam(s, t, d):
        x = s.x0 + s.walk_x(t); return 1.06, 540, 1150, -(x - 540) * .35, 0      # la cámara acompaña sin sustituir la animación

sc = Room(); DUR = 6.0
mode = sys.argv[1] if len(sys.argv) > 1 else 'video'
out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
if mode == 'frames':
    for T in [float(a) for a in sys.argv[2:]]:
        cv2.imwrite(f'{out}/p_{T:04.1f}.jpg', cv2.resize(cinema(render3d(sc, T, DUR, T), 0, T), (540, 960))[:, :, ::-1])
else:
    path = os.path.join(HERE, 'prueba_daniel.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        T = i / FPS; p.stdin.write(np.ascontiguousarray(cinema(render3d(sc, T, DUR, T), 0, T)).tobytes())
    p.stdin.close(); p.wait(); print(path)
