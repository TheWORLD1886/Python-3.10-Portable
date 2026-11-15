#!/usr/bin/env python3
# PLANO DE PRUEBA · «La junta directiva abrió una investigación independiente para determinar si Jensen fue objetivo
# de una operación extranjera.»  7.2 s · 1080x1920 · 30 fps.
# Acción: Jensen entra caminando (perfil, pies fijos) → frena → gira a tres cuartos → mira el expediente → lo toma con
# las dos manos → lee → en «operación extranjera» se sorprende (retrocede un paso, hombros arriba, cejas arriba) →
# preocupación. Dos miembros de la junta reaccionan con retraso (acción superpuesta). Nadie habla en cámara: bocas cerradas.
# Cada llamada al rig queda registrada (articulaciones por fotograma) para el control de calidad automático (qc.py).
import os, sys, json, math, subprocess
HERE_P = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE_P, '..'))
import nvidia as NV
from nvidia import *
RG = NV.RG

A0 = 95.70; DURP = 7.2                                   # recorte de la locución (no contiene la palabra NVIDIA)
WP = [[w, round(a - A0, 3), round(b - A0, 3)] for w, a, b in NV.WORDS if A0 <= a < A0 + DURP]
def TW(word): return next(a for w, a, b in WP if NV._clean(w).startswith(word))
T_OP = TW('operación')                                   # ≈ 5.48 s: la sorpresa cae en «operación extranjera»

LOG = {}                                                 # fotograma -> lista de registros del rig
def act(fn, rid, who, x, fy, h, pose, t, speaking=False, tag=None, ground=None, **kw):
    """dibuja con el rig y registra articulaciones, pose de boca, agarres y pies planeados (para el QC)."""
    pose = dict(pose, ikid=rid); hands, j = fn(FR['img'], who, x, fy, h, pose, t, **kw)
    if FR['rec']:
        rec = dict(id=rid, who=who, view=j.get('view'), u=float(j.get('u', 0)), fy=float(kw.pop('_g', ground if ground is not None else fy)), hand_r=float(j.get('hand_r', 0)), tag=tag,
                   speaking=speaking, boca=pose.get('boca', 'neutra'), abre=float(pose.get('abre', 0)),
                   joints={k: [float(v[0]), float(v[1])] for k, v in j.items() if isinstance(v, np.ndarray) and v.shape == (2,)},
                   raw={k: [float(v[0]), float(v[1])] for k, v in (j.get('raw') or {}).items()},
                   grip={k: [float(g[0]), float(g[1]), float(g[2] if len(g) > 2 else 1)] for k, g in (pose.get('grip') or {}).items()},
                   feet={k: [float(a), float(b)] for k, (a, b) in (kw.get('feet') or {}).items()}, z={k: float(v) for k, v in (j.get('z') or {}).items()})
        LOG.setdefault(FR['f'], []).append(rec)
    return hands, j
FR = dict(img=None, f=0, rec=True)

BASE = dict(ik3d=True, tz=.8, brow_up=0., brow_asym=0., abre=0., lean=0., sh=0., hip_dx=0., look=(0., 0.), tilt=0., frown=0., boca='neutra', grip=None)
def P(**kw): return dict(BASE, **kw)

class TestShot(Sb):
    def __init__(s):
        s.back, s.main = NV.office(31)
        s.front = [(bokeh_layer(8, (150, 240, 110), 431, ymin=200, ymax=1100), 1.7)]
        s.hJ = 640; s.uJ = s.hJ * RG.CAST['jensen']['alto'] / 8.; s.st = RG.step_len(s.uJ)
        s.x_stop = 4 * s.st; s.x_start = s.x_stop - 5 * s.st; s.T_STOP = 2.4; s.fy = 1640
        s.doc0 = A(545, 1352)                                                 # expediente sobre la mesa
        J = s
        x, u = s.x_stop, s.uJ
        s.cL0, s.cR0 = (490, 1352), (600, 1352)                               # esquinas donde se toma el expediente
        s.cL1, s.cR1 = (480, 1300), (590, 1300)                               # a la altura del pecho
        s.keys = [
            (2.40, P(look=(.15, .1), frown=.1)),
            (2.75, P(look=(.25, .35), tilt=.05, frown=.15)),                                  # mira el expediente
            (3.00, P(look=(.25, .45), tilt=.06, lean=.04, frown=.2, grip={'L': s.cL0 + (0.,), 'R': s.cR0 + (0.,)})),
            (3.50, P(look=(.2, .5), tilt=.06, lean=.08, frown=.25, sh=.1, grip={'L': s.cL0 + (1.,), 'R': s.cR0 + (1.,)})),   # alcanza con ambas manos
            (4.10, P(look=(.1, .4), tilt=.03, lean=.0, frown=.35, grip={'L': s.cL1 + (1.,), 'R': s.cR1 + (1.,)})),            # lo levanta
            (T_OP - .08, P(look=(.1, .42), tilt=.03, frown=.4, sh=.12, grip={'L': (s.cL1[0], s.cL1[1] + 6, 1.), 'R': (s.cR1[0], s.cR1[1] + 6, 1.)})),  # lee (anticipación: baja un poco)
            (T_OP + .22, P(look=(0., -.1), tilt=-.04, lean=-.07, hip_dx=-.14, sh=-.55, brow_up=.95, boca='o', frown=-.1,
                           grip={'L': (s.cL1[0] - 6, s.cL1[1] - 12, 1.), 'R': (s.cR1[0] - 6, s.cR1[1] - 12, 1.)})),                  # ¡sorpresa!
            (T_OP + .75, P(look=(-.05, .0), tilt=-.02, lean=-.04, hip_dx=-.12, sh=-.3, brow_up=.6, boca='o', frown=-.3,
                           grip={'L': (s.cL1[0] - 4, s.cL1[1] - 8, 1.), 'R': (s.cR1[0] - 4, s.cR1[1] - 8, 1.)})),
            (T_OP + 1.25, P(look=(-.25, .1), tilt=.02, lean=-.02, hip_dx=-.1, sh=-.05, brow_up=.3, boca='triste', frown=-.55,
                            grip={'L': (s.cL1[0], s.cL1[1] + 10, 1.), 'R': (s.cR1[0], s.cR1[1] + 10, 1.)})),                         # preocupación
            (DURP, P(look=(-.3, .12), tilt=.02, lean=-.02, hip_dx=-.1, sh=0., brow_up=.3, boca='triste', frown=-.6,
                     grip={'L': (s.cL1[0], s.cL1[1] + 14, 1.), 'R': (s.cR1[0], s.cR1[1] + 14, 1.)})),
        ]
    # ------------------------------------------------ caminata con desaceleración: la fase sale de la posición x
    def walk_x(s, t):
        k = min(1., max(0., t / s.T_STOP)); return s.x_start + (s.x_stop - s.x_start) * (k * (2 - k))
    def feet34(s, t):
        x, u = s.x_stop, s.uJ; L_, R_ = [x - .3 * u, s.fy], [x + .28 * u, s.fy]
        q = min(1., max(0., (t - (T_OP + .02)) / .3))                          # paso atrás del pie derecho al sorprenderse
        if q > 0: e = RG.ease(q); R_ = [x + .28 * u - .3 * u * e, s.fy - 4 * e - math.sin(math.pi * q) * .25 * u]
        return {'L': tuple(L_), 'R': tuple(R_)}
    def board(s, fr, t):
        react = RG.ease((t - (T_OP + .25)) / .6)                              # reaccionan 0.25 s después (acción superpuesta)
        for i, (x, w_) in enumerate(((730, 'directora'), (850, 'ejecutivo'))):
            look_j = RG.ease((t - 1.0 - i * .15) / .5); u = 470 * RG.CAST[w_]['alto'] / 8.
            idle = math.sin(t * 1.3 + i * 2.1)                                 # respiración y peso: nunca quedan congelados
            if i == 0: g = {'R': (x + .1 * u, 1420 - 4.9 * u, react)}         # se lleva la mano al pecho
            else: g = {'L': (x - .15 * u, 1420 - 6.35 * u, react)}            # se lleva la mano al mentón
            pose = P(look=(-.35 * look_j, .05 + .05 * react), frown=.25 - .5 * react, brow_up=.8 * react, sh=-.3 * react, lean=-.05 * react + .015 * idle,
                     hip_dx=.05 * math.sin(t * .7 + i), uL=-.1 + .05 * idle, uR=.1 - .05 * idle, lL=.08 + .06 * idle, lR=-.08 - .06 * idle,
                     boca='o' if (i == 1 and .3 < react < .9) else 'neutra', grip=g, tz=.9, blink=RG.blink(t, 3 + i))
            act(RG.person_34, f'junta{i}', w_, x, 1420, 470, pose, t + i, turn=-1)
    def table(s, fr):
        poly(fr, [(380, 1318), (1060, 1318), (1080, 1400), (360, 1400)], (74, 50, 34)); poly(fr, [(360, 1400), (1080, 1400), (1080, 1424), (360, 1424)], (46, 30, 20))
        for x in (390, 1040): cv2.rectangle(fr, (x - 12, 1424), (x + 12, 1560), (40, 26, 18), -1)
        cv2.ellipse(fr, (720, 1360), (300, 30), 0, 0, 360, (96, 70, 48), -1, cv2.LINE_AA)       # reflejo de la lámpara
    def doc(s, fr, t, hands):
        lift = RG.ease((t - 3.5) / .6) if t > 3.5 else 0.
        if t < 3.5 or not hands: c = s.doc0; w, h = 120, 28; up = 0.
        else: c = (A(*hands['L']) + A(*hands['R'])) / 2; w = abs(hands['R'][0] - hands['L'][0]) + 40; h = 28 + 118 * lift; up = lift
        x0, x1 = c[0] - w / 2, c[0] + w / 2; yb = c[1] + 14 * (1 - up) + 46 * up; yt = yb - h
        sk = 14 * (1 - up)                                                     # en la mesa se ve en perspectiva; en las manos, de frente
        poly(fr, [(x0 + sk, yt), (x1 - sk, yt), (x1, yb), (x0, yb)], (236, 228, 206)); pline(fr, [(x0 + sk, yt), (x1 - sk, yt), (x1, yb), (x0, yb)], (170, 160, 130), 2, True)
        if up > .3:
            for i in range(4): cv2.rectangle(fr, (int(x0 + 14), int(yt + 22 + i * 24)), (int(x1 - 14 - (i % 2) * 30), int(yt + 34 + i * 24)), (14, 14, 16) if i % 2 else (120, 110, 90), -1)
            cv2.putText(fr, 'CONFIDENCIAL', (int(x0 + 10), int(yt + 16)), cv2.FONT_HERSHEY_DUPLEX, .45, (200, 40, 40), 1, cv2.LINE_AA)
        if hands and t >= 3.0:                                                 # las manos quedan por encima del borde (lo sujetan)
            u = s.uJ
            for hd in hands.values(): circ(fr, hd, .31 * u * .9, (170, 172, 182)); circ(fr, hd, .27 * u * .9, SKIN)
    def draw(s, fr, t, d):
        FR['img'] = fr
        fbeam(fr, (640, 700), (640, 1400), 30, 420, (255, 240, 200), .10, 40)                # lámpara cenital sobre la mesa
        s.board(fr, t); s.table(fr)
        u = s.uJ; hands = None
        if t < s.T_STOP:                                                       # perfil caminando (pies fijos al suelo)
            x = s.walk_x(t); gp, feet, bob = RG.gait_x(x, 1, u, s.fy)
            v = (s.x_stop - s.x_start) * 2 * (1 - t / s.T_STOP) / s.T_STOP; k = min(1., v / 260.)
            gp.update(uL=gp['uL'] * k, uR=gp['uR'] * k, lean=gp['lean'] * k, blink=RG.blink(t, 5), frown=.1, look=(.55, .05 + .1 * (1 - k)))
            act(RG.person_side, 'jensen', 'jensen', x, s.fy + bob * k, s.hJ, dict(P(), **gp), t, feet=feet, facing=1, tag='camina', ground=s.fy)
        elif t < s.T_STOP + .2:                                                # giro: fundido de 6 fotogramas perfil → tres cuartos
            q = (t - s.T_STOP) / .2; x = s.x_stop
            prof = fr.copy(); FR['img'] = prof; gp, feet, bob = RG.gait_x(x, 1, u, s.fy); gp.update(uL=0., uR=0., lean=0., look=(.55, .1))
            act(RG.person_side, 'jensen', 'jensen', x, s.fy, s.hJ, dict(P(), **gp), t, feet=feet, facing=1, tag='giro')
            FR['img'] = fr; pose = RG.anim(s.keys, t); pose['blink'] = RG.blink(t, 5)
            hands, _ = act(RG.person_34, 'jensen', 'jensen', x, s.fy, s.hJ, pose, t, feet=s.feet34(t), turn=1, tag='giro')
            fr[:] = cv2.addWeighted(prof, 1 - RG.ease(q), fr, RG.ease(q), 0)
        else:
            pose = RG.anim(s.keys, t); pose['blink'] = 0. if T_OP - .1 < t < T_OP + .6 else RG.blink(t, 5)   # no parpadea en la sorpresa
            hands, _ = act(RG.person_34, 'jensen', 'jensen', s.x_stop, s.fy, s.hJ, pose, t, feet=s.feet34(t), turn=1)
        s.doc(fr, t, hands)
    def cam(s, t, d):
        k = RG.ease(t / d); return lerp(1.34, 1.46, k), lerp(430, 560, RG.ease(t / 3.)), 1250, 0, 0       # empuje lento; la acción la hacen los personajes

def build(out_mp4, frames_dir=None):
    sc = TestShot(); NV.TR.DUR = DURP
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in NV.TR.build_subs(WP)]
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', os.path.join(HERE_P, 'out', 'video.mp4')], stdin=subprocess.PIPE)
    n = int(round(DURP * FPS))
    for i in range(n):
        t = i / FPS; FR['f'] = i
        fr = cinema(render3d(sc, t, DURP, t + 40), 4, t + 40); fr2 = fr.copy(); draw_overlays(fr2, t, subs, [])
        if frames_dir: cv2.imwrite(os.path.join(frames_dir, f'f_{i:03d}.png'), fr[:, :, ::-1])   # sin subtítulos: para el QC de imagen
        p.stdin.write(np.ascontiguousarray(fr2).tobytes())
    p.stdin.close(); p.wait()
    json.dump(LOG, open(os.path.join(HERE_P, 'out', 'rig_log.json'), 'w'))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(A0), '-t', str(DURP), '-i', os.path.join(HERE_N, 'voz.mp3'), '-af', 'afade=t=out:st=6.9:d=0.3',
                    os.path.join(HERE_P, 'out', 'voz.wav')], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(HERE_P, 'out', 'video.mp4'), '-i', os.path.join(HERE_P, 'out', 'voz.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out_mp4], check=True)

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE_P, 'out', 'frames'), exist_ok=True)
    build(os.path.join(HERE_P, 'plano_prueba.mp4'), os.path.join(HERE_P, 'out', 'frames')); print('ok')
