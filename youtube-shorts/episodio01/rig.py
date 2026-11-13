#!/usr/bin/env python3
# Rig 2D articulado para «El día que todo terminó» (episodio 01).
# Estilo de muñecos de palo «porcelana», con articulaciones reales: cadera → torso → cuello → cabeza,
# hombro → codo → muñeca y cadera → rodilla → tobillo → pie. Las poses se describen con ángulos
# (cinemática directa) y las piernas de apoyo se resuelven con IK de dos huesos para fijar los pies al suelo.
import math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

def A(*p): return np.array(p, dtype=np.float64)
def P8(p): return (int(round(p[0] * 8)), int(round(p[1] * 8)))
def line(fr, a, b, col, th): cv2.line(fr, P8(a), P8(b), col, max(1, int(round(th))), cv2.LINE_AA, 3)
def circ(fr, c, r, col, th=-1): cv2.circle(fr, P8(c), max(1, int(round(r * 8))), col, th, cv2.LINE_AA, 3)
def poly(fr, pts, col): cv2.fillPoly(fr, [np.round(np.array(pts) * 8).astype(np.int32)], col, cv2.LINE_AA, 3)
def ell(fr, c, ax, ay, ang, col, a0=0, a1=360, th=-1): cv2.ellipse(fr, P8(c), (max(1, int(ax * 8)), max(1, int(ay * 8))), ang, a0, a1, col, th, cv2.LINE_AA, 3)
def dark(c, k=.62): return tuple(int(v * k) for v in c)
def rot(v, a): c, s = math.cos(a), math.sin(a); return A(v[0] * c - v[1] * s, v[0] * s + v[1] * c)
def down(a): return A(math.sin(a), math.cos(a))          # vector unitario: 0 rad = hacia abajo, + = hacia la derecha de la pantalla
SKIN = (246, 244, 240); INK = (18, 18, 24)

# ---------------------------------------------------------------- personajes (diseño fijo para toda la serie)
CAST = {
    'daniel': dict(nombre='DANIEL', edad='32 años', alto=1.0, cabeza=1.0, top=(52, 86, 132), plaid=(30, 52, 90), pants=(56, 86, 140), shoe=(92, 58, 34),
                   ropa='franela', pelo='corto', pelo_col=(70, 46, 30)),
    'laura': dict(nombre='LAURA', edad='31 años', alto=.94, cabeza=1.0, top=(200, 146, 62), pants=(40, 46, 70), shoe=(110, 60, 46),
                  ropa='sueter', pelo='melena', pelo_col=(96, 52, 34)),
    'sofia': dict(nombre='SOFÍA', edad='9 años', alto=.62, cabeza=1.28, top=(252, 206, 70), pants=(150, 92, 176), shoe=(244, 244, 248),
                  ropa='sudadera', pelo='coletas', pelo_col=(58, 36, 26)),
}

# ---------------------------------------------------------------- poses
NEUTRA = dict(lean=0., sh=0., hip_dx=0., uL=-.1, lL=.08, uR=.1, lR=-.08, thL=-.05, snL=0., thR=.05, snR=0.,
              look=(0., 0.), tilt=0., frown=0., boca='neutra', blink=0., grip=None)
def mix(p, q, k):
    """interpolación entre dos poses (los valores no numéricos cambian a la mitad)."""
    r = {}
    for key in p:
        a, b = p[key], q.get(key, p[key])
        if isinstance(a, (int, float)) and isinstance(b, (int, float)): r[key] = a + (b - a) * k
        elif isinstance(a, tuple) and isinstance(b, tuple): r[key] = tuple(x + (y - x) * k for x, y in zip(a, b))
        elif key == 'grip' and (a or b):
            a, b = a or {}, b or {}; r[key] = {}
            for h in set(a) | set(b):
                ga, gb = a.get(h), b.get(h)
                if ga and gb: r[key][h] = tuple(x + (y - x) * k for x, y in zip(ga[:2], gb[:2])) + ((ga[2] if len(ga) > 2 else 1) + ((gb[2] if len(gb) > 2 else 1) - (ga[2] if len(ga) > 2 else 1)) * k,)
                elif ga: r[key][h] = tuple(ga[:2]) + ((ga[2] if len(ga) > 2 else 1) * (1 - k),)
                else: r[key][h] = tuple(gb[:2]) + ((gb[2] if len(gb) > 2 else 1) * k,)
        else: r[key] = b if k >= .5 else a
    return r

def ik2(root, target, l1, l2, bend_sign):
    """IK de dos huesos (muslo-espinilla o brazo-antebrazo): devuelve la articulación media."""
    d = target - root; D = min(np.linalg.norm(d), l1 + l2 - 1e-3); D = max(D, abs(l1 - l2) + 1e-3)
    a = math.acos(max(-1, min(1, (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D))))
    base = math.atan2(d[1], d[0]); ang = base + a * bend_sign
    return root + A(math.cos(ang), math.sin(ang)) * l1

def ik_limb(root, target, l1, l2, prefer):
    """IK de dos huesos robusto: (1) el objetivo se acerca a lo alcanzable, así ningún hueso cambia de largo;
    (2) de las dos soluciones posibles se elige la anatómica (codo hacia afuera y abajo, rodilla hacia adelante)."""
    root, target = A(*root), A(*target); d = target - root; n = np.linalg.norm(d)
    if n < 1e-6: d, n = A(0, 1.), 1.
    D = min(max(n, abs(l1 - l2) + 1e-3), (l1 + l2) * .995); end = root + d / n * D
    a = math.acos(max(-1, min(1, (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D)))); base = math.atan2(d[1], d[0])
    cands = [root + A(math.cos(base + a * sg), math.sin(base + a * sg)) * l1 for sg in (1, -1)]
    mid = (root + end) / 2; pv = A(*prefer)
    e = max(cands, key=lambda c: float(np.dot(c - mid, pv)))
    return e, end

def reach(fk_hand, g):
    """objetivo de la mano: g = (x, y) o (x, y, peso). Con peso < 1 la mano viaja suavemente desde su pose natural."""
    if len(g) > 2: w = max(0., min(1., g[2])); return A(*fk_hand) + (A(g[0], g[1]) - A(*fk_hand)) * ease(w)
    return A(*g)

def person(fr, who, x, fy, hgt, pose, t=0., feet=None, facing=0):
    """Dibuja al personaje. fy = suelo. feet = {'L': (x, y), 'R': (x, y)} fija los tobillos (IK) para que no resbalen."""
    c = CAST[who]; u = hgt * c['alto'] / 8.; p = dict(NEUTRA, **pose)
    br = math.sin(t * 2.1) * u * .04                                   # respiración
    hip = A(x + p['hip_dx'] * u, fy - 3.35 * u + br * .3)
    tv = A(math.sin(p['lean']), -math.cos(p['lean']))                  # eje del torso (hacia arriba)
    tn = A(math.cos(p['lean']), math.sin(p['lean']))                   # perpendicular (hacia la derecha)
    neck = hip + tv * (2.45 * u) + A(0, br - p['sh'] * .18 * u)
    shY = neck - tv * (.15 * u)
    lw = u * .5; joints = {}
    # ---------------- piernas (detrás del torso)
    for sd, th, sn in ((-1, p['thL'], p['snL']), (1, p['thR'], p['snR'])):
        hp = hip + tn * (sd * (.42 if facing == 0 else .16) * u); L1 = L2 = 1.55 * u
        key = 'L' if sd < 0 else 'R'
        if feet and key in feet:
            kn, an = ik_limb(hp, A(*feet[key]) - A(0, .22 * u), L1, L2, (sd, -.15) if facing == 0 else (facing, -.1))
        else:
            kn = hp + down(th) * L1; an = kn + down(th + sn) * L2
        col = c['pants']; w = lw * (1.25 if c['ropa'] == 'franela' else 1.12 if who == 'laura' else 1.0)
        for a_, b_ in ((hp, kn), (kn, an)): line(fr, a_, b_, dark(col, .68), w + 4)
        for a_, b_ in ((hp, kn), (kn, an)): line(fr, a_, b_, col, w)
        circ(fr, kn, w / 2, col); circ(fr, kn, .09 * u, dark(col, .8))     # rodilla visible
        if c['ropa'] == 'franela':                                      # mezclilla: costura y bastilla
            dv = an - kn; dv /= max(1e-6, np.linalg.norm(dv)); line(fr, an - dv * .3 * u, an - dv * .1 * u, dark(col, .7), w)
        fo = 1 if facing >= 0 else -1
        toe = an + A(fo * .2 * u if facing else sd * .14 * u, .14 * u)
        ell(fr, toe, .5 * u, .25 * u, 0, c['shoe']); ell(fr, toe + A(0, .1 * u), .5 * u, .12 * u, 0, dark(c['shoe'], .6), 0, 180)
        if who == 'sofia': ell(fr, toe + A(0, -.02 * u), .5 * u, .25 * u, 0, (200, 120, 200), 200, 340, 3)
        joints['knee' + key], joints['ankle' + key] = kn, an
    # ---------------- brazos (codo y muñeca articulados); de perfil, el brazo que va hacia atrás queda detrás del torso
    hands = {}; arm_geo = []
    spread = .86 if facing == 0 else .5
    for sd, ua, la in ((-1, p['uL'], p['lL']), (1, p['uR'], p['lR'])):
        S = shY + tn * (sd * spread * u) + tv * (p['sh'] * .2 * u)
        g = p['grip'] and p['grip'].get('L' if sd < 0 else 'R')
        e = S + down(ua + p['lean']) * 1.3 * u; hd = e + down(ua + la + p['lean']) * 1.25 * u
        if g is not None: e, hd = ik_limb(S, reach(hd, g), 1.3 * u, 1.25 * u, (sd, -.1) if p.get('codo_afuera') else (sd * .55, 1.))   # codo hacia abajo y un poco afuera
        behind = facing != 0 and (hd[0] - S[0]) * facing < 0
        arm_geo.append((sd, S, e, hd, behind))
    def draw_arm(sd, S, e, hd):
        col = c['top']; dk = dark(col, .62)
        line(fr, S, e, dk, lw + 5); line(fr, e, hd, dk, lw + 4); line(fr, S, e, col, lw); line(fr, e, hd, col, lw * .92)
        circ(fr, e, lw / 2, col)                                         # codo
        if c['ropa'] == 'franela': dv = hd - e; dv /= max(1e-6, np.linalg.norm(dv)); line(fr, hd - dv * .3 * u, hd - dv * .18 * u, dark(col, .55), lw)
        if c['ropa'] == 'sin_camisa': tat_limb(fr, S, e, lw, u); tat_limb(fr, e, hd, lw * .92, u)
        circ(fr, hd, .31 * u, (170, 172, 182)); circ(fr, hd, .27 * u, c.get('piel', SKIN)); hands['L' if sd < 0 else 'R'] = hd
    for sd, S, e, hd, behind in arm_geo:
        if behind: draw_arm(sd, S, e, hd)
    # ---------------- torso
    top = c['top']; ta = neck - tv * (.25 * u); tb = hip
    def torso_mask():
        pts = [shY - tn * .95 * u, shY + tn * .95 * u, hip + tn * .92 * u + tv * -.25 * u, hip - tn * .92 * u + tv * -.25 * u]
        return pts
    tp = torso_mask(); poly(fr, tp, dark(top, .62))
    tp2 = [shY - tn * .9 * u, shY + tn * .9 * u, hip + tn * .87 * u - tv * .2 * u, hip - tn * .87 * u - tv * .2 * u]; poly(fr, tp2, top)
    ell(fr, (shY + hip) / 2, .95 * u, 1.35 * u, math.degrees(p['lean']), top)
    if c['ropa'] == 'franela':
        for k in np.linspace(-.7, .7, 5): line(fr, shY + tn * k * u, hip + tn * k * u, c['plaid'], .1 * u)
        for k in np.linspace(.3, .95, 4): q = shY + (hip - shY) * k; line(fr, q - tn * .9 * u, q + tn * .9 * u, c['plaid'], .08 * u)
        for sd in (-1, 1): poly(fr, [shY + tn * sd * .38 * u, neck + tn * sd * .02 * u, shY + tn * sd * .1 * u + tv * -.45 * u], dark(top, .5))   # cuello de camisa
        for i in range(4): circ(fr, shY + (hip - shY) * (.25 + i * .19), .06 * u, (236, 232, 220))
        ell(fr, hip - tv * .05 * u, .93 * u, .2 * u, math.degrees(p['lean']), c['pants'])      # cinturón de mezclilla
    elif c['ropa'] == 'sueter':
        ell(fr, neck - tv * .02 * u, .42 * u, .22 * u, math.degrees(p['lean']), dark(top, .75))
        ell(fr, neck - tv * .02 * u, .32 * u, .14 * u, math.degrees(p['lean']), (236, 232, 226))
        poly(fr, [hip - tn * .9 * u - tv * .5 * u, hip + tn * .9 * u - tv * .5 * u, hip + tn * .88 * u - tv * .15 * u, hip - tn * .88 * u - tv * .15 * u], dark(top, .85))   # resorte del suéter
    elif c['ropa'] == 'quirurgica':
        poly(fr, [neck - tn * .34 * u - tv * .05 * u, neck + tn * .34 * u - tv * .05 * u, neck - tv * .7 * u], dark(top, .7))
        line(fr, shY + tn * .45 * u - tv * -.6 * u, shY + tn * .75 * u - tv * -.6 * u, (240, 240, 240), 3)
    elif c['ropa'] == 'sudadera':
        ell(fr, neck + tv * .05 * u, .78 * u, .32 * u, math.degrees(p['lean']), dark(top, .8))        # capucha detrás del cuello
        poly(fr, [hip - tn * .6 * u - tv * .3 * u, hip + tn * .6 * u - tv * .3 * u, hip + tn * .45 * u - tv * 1.0 * u, hip - tn * .45 * u - tv * 1.0 * u], dark(top, .86))
        for sd in (-1, 1): line(fr, neck + tn * sd * .2 * u - tv * .1 * u, neck + tn * sd * .24 * u - tv * .8 * u, (240, 240, 244), 3)
    elif c['ropa'] == 'traje':                                            # saco con solapas, camisa y corbata opcional
        mid = shY + (hip - shY) * .5
        poly(fr, [shY - tn * .36 * u, shY + tn * .36 * u, mid], (236, 236, 240))
        if c.get('corbata'): poly(fr, [neck - tv * .02 * u - tn * .08 * u, neck - tv * .02 * u + tn * .08 * u, mid + tn * .1 * u - tv * .15 * u, mid - tv * .25 * u, mid - tn * .1 * u - tv * .15 * u], c['corbata'])
        for sd in (-1, 1): poly(fr, [shY + tn * sd * .34 * u, shY + tn * sd * .72 * u, mid + tn * sd * .18 * u + tv * .05 * u, mid + tn * sd * .02 * u], dark(top, .75))
        for k in (.62, .8): circ(fr, shY + (hip - shY) * k + tn * .05 * u, .07 * u, dark(top, .5))
    elif c['ropa'] == 'militar':                                          # uniforme camuflado, bolsillos y cinturón
        for (a_, b_, ra, rb) in [(-.45, .25, .32, .2), (.4, .45, .34, .18), (-.2, .7, .3, .16), (.5, .85, .22, .14), (-.55, .9, .2, .14)]:
            ell(fr, shY + (hip - shY) * b_ + tn * a_ * u, ra * u, rb * u, 20, dark(top, .72))
        for sd in (-1, 1): cv2.rectangle(fr, P8(shY + (hip - shY) * .25 + tn * (sd * .45 - .2) * u), P8(shY + (hip - shY) * .45 + tn * (sd * .45 + .2) * u), dark(top, .6), 2, cv2.LINE_AA, 3)
        line(fr, hip - tv * .15 * u - tn * .9 * u, hip - tv * .15 * u + tn * .9 * u, (34, 34, 26), .22 * u); circ(fr, hip - tv * .15 * u, .12 * u, (190, 160, 70))
    elif c['ropa'] == 'sin_camisa':                                       # torso desnudo tatuado (pandillero)
        tat_torso_front(fr, shY, hip, tn, tv, u, top); tat_waist(fr, hip, tn, tv, u, c['pants'])
    elif c['ropa'] in ('blanco', 'gris'):                                 # uniforme de recluso con número
        ell(fr, neck - tv * .02 * u, .4 * u, .2 * u, math.degrees(p['lean']), dark(top, .8))
        line(fr, shY + (hip - shY) * .15, hip - tv * .25 * u, dark(top, .75), 2)
        if c['ropa'] == 'gris':
            q = shY + (hip - shY) * .36 - tn * .38 * u; w_, h_ = .95 * u, .36 * u
            cv2.rectangle(fr, P8(q - A(w_ / 2, h_ / 2)), P8(q + A(w_ / 2, h_ / 2)), (236, 236, 230), -1, cv2.LINE_AA, 3)
            num = str(p.get('numero', 10000 + (int(x) * 37) % 89999))
            sc_ = max(.22, .0058 * u); (tw, th), _ = cv2.getTextSize(num, cv2.FONT_HERSHEY_DUPLEX, sc_, 1)
            cv2.putText(fr, num, (int(q[0] - tw / 2), int(q[1] + th / 2)), cv2.FONT_HERSHEY_DUPLEX, sc_, (30, 30, 34), max(1, int(u * .03)), cv2.LINE_AA)
    if c.get('banda'):                                                    # banda presidencial
        for k, col in enumerate(c['banda']):
            o_ = (k - 1) * .2 * u; line(fr, shY - tn * .78 * u + tn * o_, hip + tn * .72 * u - tv * .1 * u + tn * o_, col, .2 * u)
        circ(fr, hip + tn * .7 * u - tv * .12 * u, .2 * u, (232, 190, 80)); circ(fr, hip + tn * .7 * u - tv * .12 * u, .12 * u, (150, 110, 40))
    if c.get('rasgada'):
        for k in range(5):
            q = hip - tv * .3 * u + tn * (-.8 + k * .4) * u; poly(fr, [q - tn * .16 * u, q + tn * .16 * u, q + tv * -.35 * u * (1 + (k % 2) * .6)], dark(top, .45))
        line(fr, shY + tn * .3 * u + tv * -.4 * u, shY + tn * .55 * u + tv * -1.1 * u, dark(top, .4), .08 * u)
    if c.get('sangre'):                                                   # manchas estilizadas (sin heridas)
        for (a_, b_, r_) in [(-.3, .35, .32), (.35, .6, .22), (-.1, .8, .2), (.5, .2, .16)]:
            ell(fr, shY + (hip - shY) * b_ + tn * a_ * u, r_ * u, r_ * .8 * u, 20, (110, 16, 20))
    for sd, S, e, hd, behind in arm_geo:
        if not behind: draw_arm(sd, S, e, hd)
    # ---------------- cabeza
    uh = u * c['cabeza']
    head = neck + rot(A(0, -1.0 * uh - .25 * u), p['tilt'])
    line(fr, neck + tv * .05 * u, head, (214, 214, 222), .34 * u)
    hair_back(fr, c, head, uh, p)
    circ(fr, head, 1.0 * uh, (150, 154, 170)); circ(fr, head, .96 * uh, dark(c.get('piel', SKIN), .84)); circ(fr, head + A(-.05 * uh, -.06 * uh), .9 * uh, c.get('piel', SKIN))
    if c.get('sombra'):
        circ(fr, head, 1.0 * uh, (20, 20, 24))
        for sd in (-1, 1): ell(fr, head + A(sd * .32 * uh + p['look'][0] * .3 * uh, -.05 * uh), .1 * uh, .05 * uh, 0, (230, 230, 200))
    else: face(fr, c, head, uh, p, who)
    hair_front(fr, c, head, uh, p)
    head_extras(fr, c, head, uh, p, 0)
    joints.update(head=head, hip=hip, neck=neck); return hands, joints

def infected_marks(fr, fc, u, k, sides=(-1, 1), f=None):
    """rasgos de infección (k = 0..1): ojeras hundidas, venas oscuras, manchas en la boca."""
    for sd in sides:
        e = fc + A(sd * .34 * u, -.05 * u) if f is None else fc
        ell(fr, e + A(0, .03 * u), .17 * u, .21 * u, 0, (int(190 - 50 * k), int(176 - 50 * k), int(186 - 44 * k)))
        for j in range(1 + int(k)):
            a_ = (j * 1.3 + (sd > 0) * .7) + .4; v0 = e + A(math.cos(a_) * .2 * u, math.sin(a_) * .22 * u)
            line(fr, v0, v0 + A(math.cos(a_) * .14 * u, math.sin(a_) * .12 * u), (150, 110, 130), max(1., .025 * u))
def face(fr, c, head, u, p, who):
    lx, ly = p['look']; fc = head + A(lx * .34 * u, ly * .3 * u)
    inf = c.get('infectado', 0)
    if inf: infected_marks(fr, fc, u, inf)
    for sd in (-1, 1):
        e = fc + A(sd * .34 * u, -.05 * u)
        if inf >= .9 and p['blink'] <= .5:                                 # infectado: ojo pálido con pupila diminuta
            ell(fr, e, .1 * u, .13 * u, 0, (226, 226, 196)); circ(fr, e + A(lx * .04 * u, 0), .035 * u, INK)
            line(fr, fc + A(sd * .56 * u, -.38 * u), fc + A(sd * .14 * u, -.5 * u + (sd > 0) * .1 * u), INK, .09 * u); continue
        if p['blink'] > .5: line(fr, e - A(.1 * u, 0), e + A(.1 * u, 0), INK, .07 * u)
        else:
            sy = .165 * (1 - p['blink'] * 1.6 if p['blink'] < .5 else .2)
            big = 1.18 if p['boca'] in ('o', 'grito') else 1.
            ell(fr, e, .1 * u * big, max(.02, sy) * u * big, 0, INK); circ(fr, e + A(-.03 * u, -.06 * u), .03 * u, (250, 250, 255))
        fr_ = p['frown']; line(fr, fc + A(sd * .54 * u, -.45 * u - (fr_ < 0) * .06 * u), fc + A(sd * .16 * u, -.47 * u + fr_ * .24 * u), INK, .09 * u)
    m = fc + A(0, .42 * u); b = p['boca']
    if b == 'sonrisa': ell(fr, m - A(0, .06 * u), .26 * u, .16 * u, 0, INK, 0, 180, max(2, int(.08 * u)))
    elif b == 'o': ell(fr, m, .1 * u, .13 * u, 0, INK)
    elif b == 'grito': ell(fr, m, .16 * u, .2 * u, 0, INK); ell(fr, m + A(0, .08 * u), .1 * u, .07 * u, 0, (190, 70, 80))
    elif b == 'tensa': pts = [m + A(-.2 * u, .02 * u), m + A(-.07 * u, -.03 * u), m + A(.07 * u, .03 * u), m + A(.2 * u, -.02 * u)]; [line(fr, a, b_, INK, .07 * u) for a, b_ in zip(pts[:-1], pts[1:])]
    elif b == 'triste': ell(fr, m + A(0, .08 * u), .2 * u, .1 * u, 0, INK, 180, 360, max(2, int(.07 * u)))
    else: line(fr, m - A(.2 * u, 0), m + A(.2 * u, 0), INK, .08 * u)
    if who == 'sofia':
        for sd in (-1, 1): ell(fr, fc + A(sd * .55 * u, .22 * u), .15 * u, .08 * u, 0, (250, 196, 196))
    if inf:                                                                # manchas oscuras en la barbilla (estilizadas, sin gore)
        for k in range(3): line(fr, m + A((-.12 + k * .12) * u, .1 * u), m + A((-.1 + k * .11) * u, (.3 + .08 * (k % 2)) * u), (110, 20, 26), .06 * u)

def hair_back(fr, c, head, u, p):
    hc = c['pelo_col']
    if c['pelo'] == 'melena':                                            # melena hasta los hombros, por detrás de la cabeza
        poly(fr, [head + A(-1.08 * u, -.3 * u), head + A(1.08 * u, -.3 * u), head + A(1.12 * u, .55 * u), head + A(.92 * u, .86 * u), head + A(.55 * u, .78 * u), head + A(-.55 * u, .78 * u), head + A(-.92 * u, .86 * u), head + A(-1.12 * u, .55 * u)], hc)
    if c['pelo'] == 'cola':
        tb_ = head + A(.86 * u, -.35 * u)
        poly(fr, [tb_ + A(-.1 * u, 0), tb_ + A(.24 * u, -.05 * u), tb_ + A(.5 * u, .7 * u), tb_ + A(.42 * u, 1.5 * u), tb_ + A(.22 * u, 1.7 * u), tb_ + A(.16 * u, .9 * u)], hc)
        circ(fr, tb_ + A(.1 * u, .05 * u), .14 * u, (150, 30, 50))
    if c['pelo'] == 'coletas':
        for sd in (-1, 1):
            b = head + A(sd * 1.0 * u, -.25 * u)
            poly(fr, [b, b + A(sd * .35 * u, -.1 * u), b + A(sd * .7 * u, .5 * u), b + A(sd * .55 * u, 1.05 * u), b + A(sd * .3 * u, .55 * u)], hc)
            circ(fr, b + A(sd * .1 * u, 0), .14 * u, (240, 90, 150))

def hair_front(fr, c, head, u, p):
    hc = c['pelo_col']; hl = tuple(min(255, int(v * 1.35)) for v in hc)
    if c['pelo'] == 'gorro':
        ell(fr, head + A(0, -.5 * u), 1.02 * u, .58 * u, 0, hc, 180, 360); line(fr, head + A(-.98 * u, -.5 * u), head + A(.98 * u, -.5 * u), dark(hc, .8), .12 * u)
    elif c['pelo'] == 'revuelto':
        for k in range(7):
            a_ = math.pi * (1.05 + k * .15); circ(fr, head + A(math.cos(a_) * .82 * u, math.sin(a_) * .72 * u - .12 * u), .32 * u, hc)
    elif c['pelo'] == 'peinado':                                          # peinado hacia atrás con copete, frente despejada
        ell(fr, head + A(0, -.6 * u), 1.0 * u, .48 * u, 0, hc, 180, 360); ell(fr, head + A(.15 * u, -.98 * u), .78 * u, .2 * u, -4, hc)
        for sd in (-1, 1): poly(fr, [head + A(sd * .99 * u, -.6 * u), head + A(sd * .9 * u, -.1 * u), head + A(sd * .98 * u, -.3 * u)], hc)
        for k in range(3): line(fr, head + A((-.5 + k * .35) * u, -1.05 * u), head + A((-.2 + k * .35) * u, -.68 * u), hl, 2)
    elif c['pelo'] == 'rapado':                                           # cabeza rapada: sombra de pelo muy corto
        ell(fr, head + A(0, -.58 * u), .96 * u, .44 * u, 0, c.get('rapado_col', tuple(int(v * .82) for v in c.get('piel', SKIN))), 180, 360)
    elif c['pelo'] == 'cola':                                             # recogido en cola de caballo, raya en medio
        ell(fr, head + A(0, -.56 * u), 1.0 * u, .48 * u, 0, hc, 180, 360)
        for sd in (-1, 1): poly(fr, [head + A(sd * .99 * u, -.56 * u), head + A(sd * .76 * u, -.86 * u), head + A(sd * .92 * u, -.15 * u)], hc)
        line(fr, head + A(0, -1.02 * u), head + A(.04 * u, -.62 * u), hl, 2)
    elif c['pelo'] == 'corto':
        ell(fr, head + A(0, -.55 * u), 1.0 * u, .5 * u, 0, hc, 180, 360)
        poly(fr, [head + A(-.98 * u, -.56 * u), head + A(-.18 * u, -.66 * u), head + A(-.55 * u, -.57 * u), head + A(-.96 * u, -.44 * u)], hc)   # flequillo de lado (arriba de las cejas)
        for sd in (-1, 1): poly(fr, [head + A(sd * .99 * u, -.55 * u), head + A(sd * .86 * u, -.08 * u), head + A(sd * .97 * u, -.2 * u)], hc)
        line(fr, head + A(-.3 * u, -1.0 * u), head + A(.2 * u, -.62 * u), hl, 2)
    elif c['pelo'] == 'melena':
        ell(fr, head + A(0, -.52 * u), 1.03 * u, .54 * u, 0, hc, 180, 360)
        for sd in (-1, 1): poly(fr, [head + A(sd * 1.0 * u, -.52 * u), head + A(sd * .72 * u, -.88 * u), head + A(sd * .9 * u, .1 * u), head + A(sd * 1.0 * u, .72 * u), head + A(sd * 1.1 * u, .35 * u)], hc)
        line(fr, head + A(.15 * u, -1.03 * u), head + A(.05 * u, -.58 * u), hl, 2)
    elif c['pelo'] == 'coletas':
        ell(fr, head + A(0, -.5 * u), 1.0 * u, .52 * u, 0, hc, 180, 360)
        poly(fr, [head + A(-.95 * u, -.52 * u), head + A(.95 * u, -.52 * u), head + A(.6 * u, -.58 * u), head + A(0, -.62 * u), head + A(-.6 * u, -.58 * u)], hc)   # flequillo (arriba de las cejas)
        line(fr, head + A(0, -1.02 * u), head + A(0, -.62 * u), hl, 2)

# ================================================================ extras (mismo estilo y rig)
CAST.update({
    'medico':  dict(nombre='MÉDICO', alto=.98, cabeza=1.0, top=(70, 150, 130), pants=(60, 130, 112), shoe=(230, 230, 236), ropa='quirurgica', pelo='gorro', pelo_col=(70, 150, 130)),
    'enfermera': dict(nombre='ENFERMERA', alto=.92, cabeza=1.0, top=(80, 120, 190), pants=(70, 106, 170), shoe=(230, 230, 236), ropa='quirurgica', pelo='melena', pelo_col=(40, 30, 26)),
    'peaton1': dict(nombre='PEATÓN', alto=1.0, cabeza=1.0, top=(150, 50, 46), pants=(40, 40, 48), shoe=(30, 30, 34), ropa='liso', pelo='corto', pelo_col=(30, 24, 20)),
    'peaton2': dict(nombre='PEATÓN', alto=.95, cabeza=1.0, top=(110, 112, 120), pants=(50, 60, 90), shoe=(220, 220, 224), ropa='sudadera', pelo='corto', pelo_col=(150, 110, 60)),
    'novia':   dict(nombre='PAREJA', alto=.93, cabeza=1.0, top=(60, 110, 80), pants=(36, 40, 56), shoe=(90, 50, 40), ropa='sueter', pelo='melena', pelo_col=(30, 22, 20)),
    'mujer':   dict(nombre='MUJER', alto=.93, cabeza=1.0, top=(170, 120, 150), pants=(46, 46, 60), shoe=(70, 40, 40), ropa='liso', pelo='melena', pelo_col=(120, 80, 40)),
    'hombre':  dict(nombre='HOMBRE', alto=1.0, cabeza=1.0, top=(200, 204, 210), pants=(64, 70, 80), shoe=(40, 36, 32), ropa='liso', pelo='corto', pelo_col=(60, 46, 36), sangre=True, rasgada=True, infectado=.5, piel=(232, 230, 222)),
    'infectado': dict(nombre='INFECTADO', alto=1.0, cabeza=1.0, top=(96, 104, 92), pants=(52, 54, 60), shoe=(30, 28, 26), ropa='liso', pelo='revuelto', pelo_col=(46, 40, 36), sangre=True, rasgada=True, infectado=1., piel=(206, 212, 200)),
    'figura':  dict(nombre='FIGURA', alto=1.02, cabeza=1.0, top=(26, 26, 30), pants=(20, 20, 24), shoe=(14, 14, 16), ropa='liso', pelo='revuelto', pelo_col=(14, 14, 16), sombra=True),
    'presentadora': dict(nombre='NOTICIAS', alto=.94, cabeza=1.0, top=(40, 60, 120), pants=(30, 30, 40), shoe=(20, 20, 24), ropa='sueter', pelo='melena', pelo_col=(170, 120, 60)),
})

# ================================================================ animación: poses clave, retrasos y parpadeo
def ease(k): k = min(1., max(0., k)); return k * k * (3 - 2 * k)
def track(keys, t):
    """keys = [(tiempo, pose), ...] -> pose interpolada con ease in/out (los extremos se mantienen)."""
    if t <= keys[0][0]: return dict(NEUTRA, **keys[0][1])
    for (t0, p0), (t1, p1) in zip(keys[:-1], keys[1:]):
        if t <= t1: return mix(dict(NEUTRA, **p0), dict(NEUTRA, **p1), ease((t - t0) / max(1e-6, t1 - t0)))
    return dict(NEUTRA, **keys[-1][1])
ARMS = ('uL', 'lL', 'uR', 'lR', 'grip'); HEADK = ('look', 'tilt')
def anim(keys, t, lag_arms=.07, lag_head=.11):
    """pose con acción superpuesta: los brazos llegan 2 fotogramas después del cuerpo y la cabeza 3 (follow through)."""
    p = track(keys, t); pa = track(keys, t - lag_arms); ph = track(keys, t - lag_head)
    for k in ARMS: p[k] = pa[k]
    for k in HEADK: p[k] = ph[k]
    return p
def blink(t, seed=0):
    r = np.random.RandomState(seed); times = np.cumsum(r.uniform(2.2, 4.6, 40)) - 1.5
    d = np.min(np.abs(times - t)); return max(0., 1 - d / .075)

# ================================================================ caminata / carrera con pies fijos al suelo
def gait(t, x0, v, u, fy, run=False, dist=None):
    """devuelve (x de la cadera, pose parcial, pies). La pierna de apoyo queda fija en el suelo (sin deslizar);
    la otra avanza en arco. v = px/s (signo = dirección)."""
    s = (2.1 if run else 1.45) * u * math.copysign(1, v)           # medio paso
    x = x0 + (v * t if dist is None else math.copysign(dist, v)); ph = (x - x0) / (2 * s)   # fase del ciclo (2 pasos)
    feet = {}
    for key, off in (('L', 0.), ('R', .5)):
        f = ph + off; n = math.floor(f); fr = f - n
        P = lambda m: x0 + 2 * s * (m + .25 - off)
        if fr < .5: fx, fyy = P(n), fy                            # apoyo: pie fijo
        else:
            q = (fr - .5) / .5; e = ease(q)
            fx = P(n) + (P(n + 1) - P(n)) * e; fyy = fy - math.sin(math.pi * q) * (.55 if run else .35) * u
        feet[key] = (fx, fyy)
    sw = math.sin(2 * math.pi * ph); d = math.copysign(1, v)
    bob = math.cos(4 * math.pi * (ph - .25))
    pose = dict(hip_dx=0., lean=d * (.22 if run else .05), uL=d * sw * (.6 if run else .4), lL=(1.5 if run else .25),
                uR=-d * sw * (.6 if run else .4), lR=(1.5 if run else .25), look=(.55 * d, 0.), tilt=d * .03)
    return x, pose, feet, bob * (.08 if run else .05) * u

# ================================================================ VISTA DE PERFIL (para caminar, correr y girar)
def person_side(fr, who, x, fy, hgt, pose, t=0., feet=None, facing=1):
    """Perfil real: torso angosto, una sola cadera y un solo hombro; brazo y pierna lejanos más oscuros y detrás
    del cuerpo; rodillas y codos que solo se doblan hacia donde anatómicamente pueden; pies apuntando al frente."""
    c = CAST[who]; u = hgt * c['alto'] / 8.; p = dict(NEUTRA, **pose); f = 1 if facing >= 0 else -1
    br = math.sin(t * 2.1) * u * .04
    hip = A(x, fy - 3.35 * u + br * .3)
    tv = A(math.sin(p['lean']), -math.cos(p['lean'])); tn = A(math.cos(p['lean']), math.sin(p['lean']))
    neck = hip + tv * 2.45 * u + A(0, br - p['sh'] * .18 * u); shY = neck - tv * .3 * u
    lw = u * .5; top, pants = c['top'], c['pants']; joints = {}
    def leg(key, shade):
        L1 = L2 = 1.55 * u
        if feet and key in feet: an = A(*feet[key]) - A(0, .22 * u)
        else:
            th = p['thL'] if key == 'L' else p['thR']; an = hip + down(th) * 3.05 * u
        kn, an = ik_limb(hip, an, L1, L2, (f, -.1))                     # rodilla hacia adelante
        col = dark(pants, shade); w = lw * 1.15
        for a_, b_ in ((hip, kn), (kn, an)): line(fr, a_, b_, dark(col, .68), w + 4)
        for a_, b_ in ((hip, kn), (kn, an)): line(fr, a_, b_, col, w)
        circ(fr, kn, w / 2, col)
        sh = dark(c['shoe'], shade); toe = an + A(f * .22 * u, .16 * u)
        ell(fr, toe, .52 * u, .22 * u, 0, sh); ell(fr, toe + A(0, .08 * u), .52 * u, .1 * u, 0, dark(sh, .6), 0, 180)
        joints['knee' + key], joints['ankle' + key] = kn, an
    def arm(key, shade):
        S = shY + tn * (-f * .05 * u)
        ua = p['uL'] if key == 'L' else p['uR']; la = abs(p['lL'] if key == 'L' else p['lR'])
        g = p['grip'] and p['grip'].get(key)
        e = S + down(ua + p['lean']) * 1.3 * u; hd = e + down(ua + p['lean'] + f * la) * 1.25 * u   # el codo solo dobla hacia adelante
        if g is not None: e, hd = ik_limb(S, reach(hd, g), 1.3 * u, 1.25 * u, (-f * .5, 1.))     # codo hacia abajo y atrás
        col = dark(top, shade)
        line(fr, S, e, dark(col, .62), lw + 5); line(fr, e, hd, dark(col, .62), lw + 4); line(fr, S, e, col, lw); line(fr, e, hd, col, lw * .92)
        circ(fr, e, lw / 2, col)
        if c['ropa'] == 'sin_camisa': tat_limb(fr, S, e, lw, u); tat_limb(fr, e, hd, lw * .92, u)
        circ(fr, hd, .31 * u, dark((170, 172, 182), shade)); circ(fr, hd, .27 * u, dark(c.get('piel', SKIN), shade)); return hd
    hands = {}
    near, far = ('R', 'L') if f > 0 else ('L', 'R')
    hands[far] = arm(far, .72); leg(far, .78)
    # torso de perfil: más angosto (profundidad) y con pecho y espalda
    def silhouette(grow):
        # (altura desde la cadera 0..1.1, desplazamiento hacia el frente en u): pecho redondeado, espalda curva, cintura más angosta
        prof = [(1.06, .15), (1.02, .42), (.9, .66), (.72, .74), (.5, .6), (.3, .54), (.08, .6), (-.08, .58),
                (-.08, -.6), (.08, -.62), (.3, -.52), (.55, -.58), (.78, -.66), (.95, -.58), (1.04, -.35), (1.08, -.1)]
        H_ = (shY - hip)
        pts_ = [hip + H_ * h_ + tn * f * (o_ + np.sign(o_) * grow) * u for h_, o_ in prof]
        return chaikin_c(pts_, 2)
    poly(fr, silhouette(.06), dark(top, .62)); poly(fr, silhouette(0.), top)
    front = lambda k: (shY + (hip - shY) * k) + tn * f * .64 * u
    if c['ropa'] == 'franela':
        for k in (-.3, .05, .35): line(fr, shY + tn * k * u, hip + tn * k * u, c['plaid'], .1 * u)
        for k in np.linspace(.3, .95, 4): q = shY + (hip - shY) * k; line(fr, q - tn * .55 * u, q + tn * .55 * u, c['plaid'], .08 * u)
        for i in range(4): circ(fr, front(.25 + i * .19) - tn * f * .08 * u, .06 * u, (236, 232, 220))
        poly(fr, [neck + tn * f * .25 * u, neck - tn * f * .2 * u, shY + tn * f * .3 * u - tv * .3 * u], dark(top, .5))
    elif c['ropa'] == 'sueter':
        poly(fr, [hip - tn * .56 * u - tv * .5 * u, hip + tn * .6 * u - tv * .5 * u, hip + tn * .58 * u - tv * .15 * u, hip - tn * .54 * u - tv * .15 * u], dark(top, .85))
    elif c['ropa'] == 'sudadera':
        ell(fr, neck - tn * f * .35 * u, .38 * u, .3 * u, 0, dark(top, .8))
        poly(fr, [hip + tn * f * .1 * u - tv * .3 * u, hip + tn * f * .55 * u - tv * .3 * u, hip + tn * f * .5 * u - tv * 1.0 * u, hip + tn * f * .15 * u - tv * 1.0 * u], dark(top, .86))
    if c['ropa'] == 'traje':
        poly(fr, [shY + tn * f * .45 * u, shY + tn * f * .68 * u, shY + (hip - shY) * .5 + tn * f * .6 * u], (236, 236, 240))
        if c.get('corbata'): line(fr, shY + tn * f * .62 * u, shY + (hip - shY) * .45 + tn * f * .66 * u, c['corbata'], .14 * u)
        line(fr, shY + tn * f * .4 * u, shY + (hip - shY) * .55 + tn * f * .55 * u, dark(top, .7), .1 * u)
    elif c['ropa'] == 'gris':                                             # número del recluso también de perfil
        q = shY + (hip - shY) * .3 + tn * f * .3 * u; w_, h_ = .8 * u, .3 * u
        cv2.rectangle(fr, P8(q - A(w_ / 2, h_ / 2)), P8(q + A(w_ / 2, h_ / 2)), (236, 236, 230), -1, cv2.LINE_AA, 3)
        num = str(p.get('numero', 10000 + (int(x) * 37) % 89999)); sc_ = max(.2, .0048 * u); (tw, th), _ = cv2.getTextSize(num, cv2.FONT_HERSHEY_DUPLEX, sc_, 1)
        cv2.putText(fr, num, (int(q[0] - tw / 2), int(q[1] + th / 2)), cv2.FONT_HERSHEY_DUPLEX, sc_, (30, 30, 34), max(1, int(u * .03)), cv2.LINE_AA)
    elif c['ropa'] == 'sin_camisa':                                       # de perfil: pectoral, letras en el costado, cintura caída
        H_ = hip - shY
        ell(fr, shY + H_ * .34 + tn * f * .38 * u, .3 * u, .13 * u, 0, dark(top, .82), 0 if f > 0 else 180, 90 if f > 0 else 270, max(2, int(.05 * u)))
        tat_text(fr, 'MS', shY + H_ * .3 + tn * f * .32 * u, .56 * u); tat_text(fr, '13', shY + H_ * .66 + tn * f * .3 * u, .4 * u)
        line(fr, hip + tv * .12 * u - tn * .56 * u, hip + tv * .12 * u + tn * .6 * u, (236, 236, 240), .2 * u)
        line(fr, hip - tv * .06 * u - tn * .62 * u, hip - tv * .06 * u + tn * .64 * u, pants, .3 * u)
    elif c['ropa'] == 'militar':
        for (a_, b_, ra, rb) in [(-.3, .3, .26, .18), (.3, .55, .28, .16), (-.1, .8, .24, .14)]: ell(fr, shY + (hip - shY) * b_ + tn * a_ * u, ra * u, rb * u, 20, dark(top, .72))
        line(fr, hip - tv * .15 * u - tn * .7 * u, hip - tv * .15 * u + tn * .74 * u, (34, 34, 26), .22 * u)
    if c.get('banda'):
        for k, col in enumerate(c['banda']):
            o_ = (k - 1) * .16 * u; line(fr, shY - tn * f * .5 * u + tn * o_, hip + tn * f * .55 * u - tv * .1 * u + tn * o_, col, .16 * u)
    if c.get('sangre'):
        for (a_, b_, r_) in [(.2, .35, .3), (-.1, .7, .22)]: ell(fr, shY + (hip - shY) * b_ + tn * f * a_ * u, r_ * u, r_ * .8 * u, 20, (110, 16, 20))
    leg(near, 1.0)
    hands[near] = arm(near, 1.0)
    # cabeza de perfil
    uh = u * c['cabeza']; head = neck + rot(A(f * .1 * uh, -1.0 * uh - .25 * u), p['tilt'])
    line(fr, neck + tv * .05 * u, head, (214, 214, 222), .34 * u)
    hc = c['pelo_col']
    L = lambda xf, y: head + A(f * xf * uh, y * uh)                       # coordenadas locales: xf hacia el frente
    # pelo largo / colas que cuelgan por detrás de la cabeza
    if c['pelo'] == 'melena': poly(fr, [L(-.2, -.75), L(-1.1, -.15), L(-1.05, .82), L(-.5, .8), L(-.3, .4)], hc)
    if c['pelo'] == 'coletas':
        b_ = L(-.95, -.25); poly(fr, [b_, L(-1.3, -.35), L(-1.65, .25), L(-1.5, .8), L(-1.25, .3)], hc); circ(fr, b_, .14 * uh, (240, 90, 150))
    if c['pelo'] == 'cola':
        poly(fr, [L(-.85, -.45), L(-1.12, -.4), L(-1.32, .4), L(-1.22, 1.3), L(-1.02, 1.45), L(-1.02, .5)], hc); circ(fr, L(-.95, -.4), .14 * uh, (150, 30, 50))
    circ(fr, head, 1.0 * uh, (150, 154, 170)); circ(fr, head, .96 * uh, dark(c.get('piel', SKIN), .84)); circ(fr, head + A(f * .05 * uh, -.06 * uh), .9 * uh, c.get('piel', SKIN))
    if c.get('sombra'): circ(fr, head, 1.0 * uh, (20, 20, 24)); ell(fr, head + A(f * .55 * uh, -.05 * uh), .1 * uh, .05 * uh, 0, (230, 230, 200))
    else:
        if c.get('barba'): beard_profile(fr, c['barba'], L)               # la barba va debajo de los ojos y la boca
        e = head + A(f * .55 * uh, -.05 * uh + p['look'][1] * .2 * uh)                      # un solo ojo, hacia el frente
        if c.get('infectado'): infected_marks(fr, e, uh, c['infectado'], sides=(1,), f=f)
        if p['blink'] > .5: line(fr, e - A(.08 * uh, 0), e + A(.08 * uh, 0), INK, .07 * uh)
        else: ell(fr, e, .09 * uh, .16 * uh, 0, INK); circ(fr, e + A(f * .03 * uh, -.06 * uh), .03 * uh, (250, 250, 255))
        fr_ = p['frown']; line(fr, e + A(-f * .2 * uh, -.42 * uh), e + A(f * .12 * uh, -.36 * uh + fr_ * .2 * uh), INK, .09 * uh)
        m = head + A(f * .62 * uh, .42 * uh); bo = p['boca']
        if bo == 'sonrisa': ell(fr, m, .16 * uh, .1 * uh, 0, INK, 0, 180, max(2, int(.07 * uh)))
        elif bo in ('o', 'grito'): ell(fr, m, .08 * uh, .12 * uh * (1.3 if bo == 'grito' else 1), 0, INK)
        else: line(fr, m - A(f * .12 * uh, 0), m + A(f * .08 * uh, 0), INK, .07 * uh)
        if who == 'sofia': ell(fr, head + A(f * .45 * uh, .25 * uh), .14 * uh, .08 * uh, 0, (250, 196, 196))
    hair_profile(fr, c, L, uh, f, hc)
    head_extras(fr, c, head, uh, p, f)
    joints.update(head=head, hip=hip, neck=neck); return hands, joints
def step_len(u, run=False): return (2.1 if run else 1.45) * u


# ================================================================ accesorios de cabeza: barba, gorra, casco (nunca bajan de las cejas)
def head_extras(fr, c, head, u, p, f):
    lx, ly = p['look']
    if f == 0: fc = head + A(lx * .34 * u, ly * .3 * u)
    else: fc = head + A(f * .45 * u, ly * .2 * u)
    if c.get('barba'):                                                    # barba corta que sigue la mandíbula; la boca queda libre
        bc = c['barba']
        if f == 0:
            cv2.ellipse(fr, P8(fc + A(0, .02 * u)), (int(.8 * u * 8), int(.78 * u * 8)), 0, 25, 155, bc, max(2, int(.2 * u)), cv2.LINE_AA, 3)
            cv2.ellipse(fr, P8(fc + A(0, .3 * u)), (int(.22 * u * 8), int(.06 * u * 8)), 0, 180, 360, bc, max(2, int(.05 * u)), cv2.LINE_AA, 3)   # bigote fino (arriba de la boca)
        else: pass                                                            # de perfil: ver beard_profile
    if c.get('tatuajes'):
        if f == 0:
            tat_text(fr, 'MS', fc + A(0, -.72 * u), .56 * u)                                           # frente, arriba de las cejas
            for sd in (-1, 1):                                                                         # mejillas: tres puntos / 13
                if sd < 0:
                    for q in ((-.6, .14), (-.5, .14), (-.55, .24)): circ(fr, fc + A(q[0] * u, q[1] * u), .035 * u, TINTA)
                else: tat_text(fr, '13', fc + A(.6 * u, .2 * u), .22 * u)
            line(fr, fc + A(-.34 * u, .06 * u), fc + A(-.34 * u, .14 * u), TINTA, .04 * u)          # lágrima bajo el ojo
        else:
            L = lambda xf, y: head + A(f * xf * u, y * u)
            tat_text(fr, 'MS', L(-.3, -.5), .55 * u)                                                  # costado del cráneo
            for q in ((.4, .14), (.5, .14), (.45, .24)): circ(fr, L(*q), .035 * u, TINTA)            # tres puntos en la mejilla
    g = c.get('gorra')
    if g:                                                                 # gorra: la visera queda arriba de las cejas
        col = c.get('gorra_col', (36, 40, 50))
        ell(fr, head + A(0, -.62 * u), 1.0 * u, .5 * u, 0, col, 180, 360); poly(fr, [head + A(-1.0 * u, -.62 * u), head + A(1.0 * u, -.62 * u), head + A(.96 * u, -.54 * u), head + A(-.96 * u, -.54 * u)], dark(col, .8))
        if g == 'frente' and f == 0: ell(fr, head + A(0, -.6 * u), 1.05 * u, .14 * u, 0, dark(col, .7), 0, 180)
        elif g == 'frente': poly(fr, [head + A(f * .6 * u, -.62 * u), head + A(f * 1.5 * u, -.6 * u), head + A(f * 1.45 * u, -.52 * u), head + A(f * .7 * u, -.54 * u)], dark(col, .7))
        circ(fr, head + A(0, -1.1 * u), .09 * u, dark(col, 1.3) if False else (60, 64, 74))
    if c.get('casco'):                                                    # casco militar
        col = c['casco']
        ell(fr, head + A(0, -.6 * u), 1.1 * u, .62 * u, 0, col, 180, 360); poly(fr, [head + A(-1.12 * u, -.62 * u), head + A(1.12 * u, -.62 * u), head + A(1.08 * u, -.55 * u), head + A(-1.08 * u, -.55 * u)], dark(col, .75))
        line(fr, head + A(-.6 * u, -.6 * u), head + A(-.5 * u, -1.0 * u), dark(col, .8), 2)

CAST.update({
    'bukele':    dict(nombre='BUKELE', alto=1.0, cabeza=1.0, top=(30, 34, 44), pants=(26, 28, 36), shoe=(14, 14, 18), ropa='traje', pelo='peinado', pelo_col=(30, 24, 20), barba=(46, 36, 30), banda=[(20, 70, 170), (245, 245, 245), (20, 70, 170)]),
    'presidenta': dict(nombre='PRESIDENTA', alto=.95, cabeza=1.0, top=(92, 26, 44), pants=(40, 22, 30), shoe=(20, 12, 14), ropa='traje', pelo='cola', pelo_col=(44, 30, 26), banda=[(0, 120, 72), (245, 245, 245), (206, 24, 40)]),
    'soldado':   dict(nombre='SOLDADO', alto=1.0, cabeza=1.0, top=(92, 104, 64), pants=(72, 82, 52), shoe=(26, 26, 26), ropa='militar', pelo='corto', pelo_col=(40, 32, 26), casco=(70, 82, 50)),
    'reo':       dict(nombre='DETENIDO', alto=.98, cabeza=1.0, top=(122, 126, 132), pants=(110, 114, 120), shoe=(40, 40, 44), ropa='gris', pelo='rapado', pelo_col=(200, 196, 190)),
    'pandillero': dict(nombre='PANDILLERO', alto=.98, cabeza=1.0, top=SKIN, pants=(34, 36, 42), shoe=(236, 236, 240), ropa='sin_camisa', pelo='rapado', pelo_col=(60, 56, 54), rapado_col=(234, 232, 228), tatuajes=True),
    'jefe':      dict(nombre='JEFE', alto=1.0, cabeza=1.0, top=(40, 78, 178), pants=(24, 28, 48), shoe=(14, 14, 18), ropa='traje', pelo='peinado', pelo_col=(60, 46, 36), corbata=(200, 170, 60)),
    'ejecutivo': dict(nombre='EJECUTIVO', alto=1.0, cabeza=1.0, top=(34, 38, 60), pants=(28, 31, 48), shoe=(14, 14, 18), ropa='traje', pelo='corto', pelo_col=(70, 60, 50), corbata=(190, 32, 36)),
    'vecino':    dict(nombre='VECINO', alto=.98, cabeza=1.0, top=(128, 34, 40), pants=(52, 84, 146), shoe=(70, 46, 30), ropa='franela', plaid=(90, 24, 28), pelo='corto', pelo_col=(40, 30, 24)),
    'vecina':    dict(nombre='VECINA', alto=.93, cabeza=1.0, top=(70, 120, 110), pants=(40, 46, 70), shoe=(110, 60, 46), ropa='sueter', pelo='cola', pelo_col=(60, 40, 30)),
    'doctora':   dict(nombre='DOCTORA', alto=.94, cabeza=1.0, top=(236, 239, 244), pants=(54, 58, 70), shoe=(20, 20, 24), ropa='quirurgica', pelo='melena', pelo_col=(90, 60, 40)),
})

TINTA = (40, 48, 70)                                                    # tinta de tatuaje: azul-negro desgastado
def tat_text(fr, txt, c, w_px, col=TINTA, font=cv2.FONT_HERSHEY_COMPLEX | cv2.FONT_ITALIC, th=None):
    """texto tatuado centrado en c, escalado para medir w_px de ancho (letras tipo old english simplificadas)."""
    (tw, tth), _ = cv2.getTextSize(txt, font, 1., 2); sc = max(.15, w_px / max(1, tw)); th = th or max(1, int(sc * 1.6))
    (tw, tth), _ = cv2.getTextSize(txt, font, sc, th)
    org = (int(c[0] - tw / 2), int(c[1] + tth / 2)); cv2.putText(fr, txt, org, font, sc, col, th, cv2.LINE_AA)
def tat_limb(fr, a, b, w, u, seed=0):
    """manga tatuada sobre un segmento del brazo: bandas, picos y rombos que siguen la dirección del hueso."""
    d = b - a; L = np.linalg.norm(d)
    if L < 1e-3: return
    d = d / L; n = A(-d[1], d[0]); hw = w * .42
    for k in (.18, .82): q = a + d * L * k; line(fr, q - n * hw, q + n * hw, TINTA, .07 * u)              # bandas
    for i in range(3):                                                                                  # picos tribales
        k = .3 + i * .17; q = a + d * L * k
        poly(fr, [q - n * hw * .9, q + d * .12 * u, q - n * hw * .2 + d * .03 * u], TINTA)
        poly(fr, [q + n * hw * .9, q + d * .12 * u, q + n * hw * .2 + d * .03 * u], TINTA)
    q = a + d * L * .7; poly(fr, [q + d * .1 * u, q + n * hw * .45, q - d * .1 * u, q - n * hw * .45], TINTA)
def tat_torso_front(fr, shY, hip, tn, tv, u, top):
    """pecho y abdomen marcados + tatuajes grandes: letras en el pecho, número en el abdomen, ornamentos en clavículas."""
    H_ = hip - shY; at = lambda k, o: shY + H_ * k + tn * o * u
    for sd in (-1, 1): ell(fr, at(.33, sd * .42), .42 * u, .14 * u, 0, dark(top, .82), 10, 170, max(2, int(.05 * u)))   # pectorales
    line(fr, at(.12, 0), at(.4, 0), dark(top, .86), .04 * u)
    for k in (.55, .7): line(fr, at(k, -.22), at(k, .22), dark(top, .88), .035 * u)                    # abdomen
    circ(fr, at(.88, 0), .05 * u, dark(top, .7))                                                         # ombligo
    for sd in (-1, 1):                                                                                   # ornamento en clavícula
        a0 = at(.05, sd * .2); a1 = at(.1, sd * .78)
        line(fr, a0, a1, TINTA, .06 * u); circ(fr, at(.08, sd * .5), .07 * u, TINTA)
    tat_text(fr, 'MS', at(.26, 0), 1.25 * u)
    tat_text(fr, '13', at(.66, 0), .62 * u)
    for sd in (-1, 1):                                                                                   # cuernos (mano «la garra») en los costados
        q = at(.6, sd * .64)
        poly(fr, [q + A(-.12 * u, .14 * u), q + A(-.1 * u, -.2 * u), q + A(-.04 * u, .02 * u), q + A(.04 * u, .02 * u), q + A(.1 * u, -.2 * u), q + A(.12 * u, .14 * u)], TINTA)
def tat_waist(fr, hip, tn, tv, u, pants):
    """pantalón holgado caído con el elástico del bóxer a la vista."""
    line(fr, hip + tv * .12 * u - tn * .86 * u, hip + tv * .12 * u + tn * .86 * u, (236, 236, 240), .2 * u)
    line(fr, hip - tv * .06 * u - tn * .92 * u, hip - tv * .06 * u + tn * .92 * u, pants, .3 * u)

def chaikin_c(pts, it=2):
    """suaviza un contorno cerrado (esquinas redondeadas)."""
    p = [A(*q) for q in pts]
    for _ in range(it):
        q = []
        for a_, b_ in zip(p, p[1:] + p[:1]): q += [a_ * .75 + b_ * .25, a_ * .25 + b_ * .75]
        p = q
    return p
def gait_x(x, d, u, fy, run=False):
    """caminata con pies fijos a partir de la posición absoluta x (sirve cuando la escena mueve al personaje por su cuenta)."""
    s = step_len(u, run) * d; ph = x / (2 * s); feet = {}
    for key, off in (('L', 0.), ('R', .5)):
        f = ph + off; n = math.floor(f); fr_ = f - n; P = lambda m: 2 * s * (m + .25 - off)
        if fr_ < .5: fx, fyy = P(n), fy
        else:
            q = (fr_ - .5) / .5; fx = P(n) + (P(n + 1) - P(n)) * ease(q); fyy = fy - math.sin(math.pi * q) * (.55 if run else .35) * u
        feet[key] = (fx, fyy)
    sw = math.sin(2 * math.pi * ph); bob = math.cos(4 * math.pi * (ph - .25)) * (.08 if run else .05) * u
    pose = dict(lean=d * (.22 if run else .05), uL=d * sw * (.6 if run else .4), lL=(1.5 if run else .25), uR=-d * sw * (.6 if run else .4), lR=(1.5 if run else .25), look=(.55 * d, 0.))
    return pose, feet, bob


def _arc(L, a0, a1, r=1.0, n=24):
    """puntos sobre el contorno de la cabeza (ángulos en grados: 0 = frente, -90 = coronilla, 90 = barbilla)."""
    return [L(math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r) for a in np.linspace(a0, a1, n)]

def hair_profile(fr, c, L, uh, f, hc):
    """pelo de perfil: sigue la forma del cráneo, con la línea del nacimiento curva por ARRIBA de la ceja
    y la nuca detrás de la oreja (sin bloques cuadrados)."""
    st = c['pelo']
    if st in ('corto', 'peinado', 'coletas', 'cola', 'melena', 'rapado'):
        col = c.get('rapado_col', tuple(int(v * .82) for v in c.get('piel', SKIN))) if st == 'rapado' else hc
        arc = _arc(L, -38, -222, 1.03)                                        # de la frente, por la coronilla, hasta la nuca
        inner = [L(-.6, .55), L(-.5, .18), L(-.32, -.22), L(-.05, -.5), L(.3, -.64), L(.62, -.66)]
        if st == 'melena': arc = _arc(L, -38, -210, 1.04); inner = [L(-.75, .62), L(-.55, .2), L(-.3, -.25)] + inner[3:]
        poly(fr, arc + inner, col)
        hl = tuple(min(255, int(v * 1.35)) for v in col)
        for k in range(3): line(fr, L(-.1 - k * .25, -.98 + k * .06), L(.25 - k * .25, -.8 + k * .05), hl, max(1, int(.02 * uh)))   # brillo / mechones
        if st == 'peinado': ell(fr, L(.32, -.92), .62 * uh, .2 * uh, -6 * f, hc)                      # copete
        if st == 'corto': poly(fr, [L(.55, -.66), L(.9, -.62), L(.62, -.56)], hc)                        # punta del fleco
        if st in ('corto', 'peinado'): poly(fr, [L(-.14, -.2), L(-.06, -.18), L(-.09, .02), L(-.17, 0)], col)   # patilla corta (solo hombres)
    elif st == 'gorro':
        poly(fr, _arc(L, -36, -205, 1.05) + [L(-.85, .3), L(-.5, -.1), L(-.1, -.5), L(.35, -.66), L(.68, -.68)], hc)
        rim = [L(-.82, .28), L(-.48, -.12), L(-.08, -.52), L(.35, -.68), L(.68, -.7)]
        for a_, b_ in zip(rim[:-1], rim[1:]): line(fr, a_, b_, dark(hc, .8), max(2, int(.06 * uh)))   # borde del gorro, arriba de la ceja
    elif st == 'revuelto':
        for k in range(7):
            a_ = math.radians(-40 - k * 27); circ(fr, L(math.cos(a_) * .82, math.sin(a_) * .72 - .1), .32 * uh, hc)
    if st not in ('melena', 'gorro', 'sombra'):                              # oreja con detalle
        e0 = L(-.28, .06); circ(fr, e0, .17 * uh, dark(c.get('piel', SKIN), .78)); circ(fr, e0, .14 * uh, c.get('piel', SKIN))
        cv2.ellipse(fr, P8(e0), (int(.08 * uh * 8), int(.1 * uh * 8)), 0, 200 if f > 0 else -20, 340 if f > 0 else 160, dark(c.get('piel', SKIN), .7), max(1, int(.03 * uh)), cv2.LINE_AA, 3)

def beard_profile(fr, col, L):
    """barba de perfil: solo la mandíbula (de la patilla a la barbilla), deja libre la boca; bigote corto."""
    pts = _arc(L, 25, 118, .99) + [L(-.4, .55), L(-.22, .2), L(.1, .5), L(.42, .58), L(.7, .5)]
    poly(fr, pts, col)
    line(fr, L(.48, .31), L(.74, .33), col, .07 * L(1, 0)[0] * 0 + 4)
