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
        else: r[key] = b if k >= .5 else a
    return r

def ik2(root, target, l1, l2, bend_sign):
    """IK de dos huesos (muslo-espinilla o brazo-antebrazo): devuelve la articulación media."""
    d = target - root; D = min(np.linalg.norm(d), l1 + l2 - 1e-3); D = max(D, abs(l1 - l2) + 1e-3)
    a = math.acos(max(-1, min(1, (l1 * l1 + D * D - l2 * l2) / (2 * l1 * D))))
    base = math.atan2(d[1], d[0]); ang = base + a * bend_sign
    return root + A(math.cos(ang), math.sin(ang)) * l1

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
        hp = hip + tn * (sd * .42 * u); L1 = L2 = 1.55 * u
        key = 'L' if sd < 0 else 'R'
        if feet and key in feet:
            an = A(*feet[key]) - A(0, .22 * u); kn = ik2(hp, an, L1, L2, -1 if facing >= 0 else 1)
            if facing == 0: kn = ik2(hp, an, L1, L2, 1 if sd < 0 else -1)
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
    elif c['ropa'] == 'sudadera':
        ell(fr, neck + tv * .05 * u, .78 * u, .32 * u, math.degrees(p['lean']), dark(top, .8))        # capucha detrás del cuello
        poly(fr, [hip - tn * .6 * u - tv * .3 * u, hip + tn * .6 * u - tv * .3 * u, hip + tn * .45 * u - tv * 1.0 * u, hip - tn * .45 * u - tv * 1.0 * u], dark(top, .86))
        for sd in (-1, 1): line(fr, neck + tn * sd * .2 * u - tv * .1 * u, neck + tn * sd * .24 * u - tv * .8 * u, (240, 240, 244), 3)
    # ---------------- brazos (codo y muñeca articulados)
    hands = {}
    for sd, ua, la in ((-1, p['uL'], p['lL']), (1, p['uR'], p['lR'])):
        S = shY + tn * (sd * .86 * u) + tv * (p['sh'] * .2 * u)
        g = p['grip'] and p['grip'].get('L' if sd < 0 else 'R')
        if g is not None: hd = A(*g); e = ik2(S, hd, 1.3 * u, 1.25 * u, -1 if sd < 0 else 1)
        else: e = S + down(ua + p['lean']) * 1.3 * u; hd = e + down(ua + la + p['lean']) * 1.25 * u
        col = top; dk = dark(top, .62)
        line(fr, S, e, dk, lw + 5); line(fr, e, hd, dk, lw + 4); line(fr, S, e, col, lw); line(fr, e, hd, col, lw * .92)
        circ(fr, e, lw / 2, col)                                         # codo
        if c['ropa'] == 'franela': dv = hd - e; dv /= max(1e-6, np.linalg.norm(dv)); line(fr, hd - dv * .3 * u, hd - dv * .18 * u, dark(col, .55), lw)   # puño
        circ(fr, hd, .31 * u, (170, 172, 182)); circ(fr, hd, .27 * u, SKIN); hands['L' if sd < 0 else 'R'] = hd
    # ---------------- cabeza
    uh = u * c['cabeza']
    head = neck + rot(A(0, -1.0 * uh - .25 * u), p['tilt'])
    line(fr, neck + tv * .05 * u, head, (214, 214, 222), .34 * u)
    hair_back(fr, c, head, uh, p)
    circ(fr, head, 1.0 * uh, (150, 154, 170)); circ(fr, head, .96 * uh, (204, 206, 218)); circ(fr, head + A(-.05 * uh, -.06 * uh), .9 * uh, SKIN)
    face(fr, c, head, uh, p, who)
    hair_front(fr, c, head, uh, p)
    joints.update(head=head, hip=hip, neck=neck); return hands, joints

def face(fr, c, head, u, p, who):
    lx, ly = p['look']; fc = head + A(lx * .34 * u, ly * .3 * u)
    for sd in (-1, 1):
        e = fc + A(sd * .34 * u, -.05 * u)
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

def hair_back(fr, c, head, u, p):
    hc = c['pelo_col']
    if c['pelo'] == 'melena':                                            # melena hasta los hombros, por detrás de la cabeza
        poly(fr, [head + A(-1.1 * u, -.2 * u), head + A(1.1 * u, -.2 * u), head + A(1.18 * u, 1.25 * u), head + A(.6 * u, 1.4 * u), head + A(-.6 * u, 1.4 * u), head + A(-1.18 * u, 1.25 * u)], hc)
    if c['pelo'] == 'coletas':
        for sd in (-1, 1):
            b = head + A(sd * 1.0 * u, -.25 * u)
            poly(fr, [b, b + A(sd * .35 * u, -.1 * u), b + A(sd * .7 * u, .5 * u), b + A(sd * .55 * u, 1.05 * u), b + A(sd * .3 * u, .55 * u)], hc)
            circ(fr, b + A(sd * .1 * u, 0), .14 * u, (240, 90, 150))

def hair_front(fr, c, head, u, p):
    hc = c['pelo_col']; hl = tuple(min(255, int(v * 1.35)) for v in hc)
    if c['pelo'] == 'corto':
        ell(fr, head + A(0, -.55 * u), 1.0 * u, .5 * u, 0, hc, 180, 360)
        poly(fr, [head + A(-.98 * u, -.55 * u), head + A(-.2 * u, -.62 * u), head + A(-.6 * u, -.35 * u), head + A(-.95 * u, -.2 * u)], hc)   # flequillo de lado
        for sd in (-1, 1): poly(fr, [head + A(sd * .99 * u, -.55 * u), head + A(sd * .86 * u, -.08 * u), head + A(sd * .97 * u, -.2 * u)], hc)
        line(fr, head + A(-.3 * u, -1.0 * u), head + A(.2 * u, -.62 * u), hl, 2)
    elif c['pelo'] == 'melena':
        ell(fr, head + A(0, -.52 * u), 1.03 * u, .54 * u, 0, hc, 180, 360)
        for sd in (-1, 1): poly(fr, [head + A(sd * 1.0 * u, -.52 * u), head + A(sd * .7 * u, -.9 * u), head + A(sd * 1.0 * u, .4 * u), head + A(sd * 1.1 * u, .1 * u)], hc)
        line(fr, head + A(.15 * u, -1.03 * u), head + A(.05 * u, -.58 * u), hl, 2)
    elif c['pelo'] == 'coletas':
        ell(fr, head + A(0, -.5 * u), 1.0 * u, .52 * u, 0, hc, 180, 360)
        poly(fr, [head + A(-.95 * u, -.5 * u), head + A(.95 * u, -.5 * u), head + A(.6 * u, -.35 * u), head + A(0, -.42 * u), head + A(-.6 * u, -.35 * u)], hc)   # flequillo
        line(fr, head + A(0, -1.02 * u), head + A(0, -.62 * u), hl, 2)
