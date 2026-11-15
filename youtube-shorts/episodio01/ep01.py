#!/usr/bin/env python3
# EL DÍA QUE TODO TERMINÓ · Episodio 01 «La última noche normal» (versión sin voces: narración en pantalla)
import subprocess, json
from escenarios import *

def lerp(a, b, k): return a + (b - a) * k
class Shot:
    shake = 0.
    def cam(s, t, d):
        k = ease(t / d); dx = lerp(-25, 25, k); dy = 0.
        if s.shake: dx += (math.sin(t * 7.3) + .6 * math.sin(t * 13.1)) * s.shake; dy += (math.sin(t * 6.1 + 1) + .5 * math.sin(t * 11.7)) * s.shake
        return lerp(1.03, 1.09, k), 540, 1000, dx, dy

U = lambda who, h: h * CAST[who]['alto'] / 8.

# ================================================================ ESCENA 1 · 10:47 PM
class S11(Shot):                                   # calle principal: autos, árboles, farolas
    def __init__(s):
        s.back, s.main, s.front = set_street(); s.clock = N.text_sprite('10:47 PM', 120, (255, 240, 210, 255), glow=(255, 160, 80), glow_r=18, spacing=8)
        s.title = N.text_sprite('EL DÍA QUE TODO TERMINÓ', 44, (230, 230, 240, 255), stroke=4, stroke_col=(0, 0, 0, 200), spacing=10)
    def draw(s, fr, t, d):
        street_props(fr, t, trees=(1010,))
        for i, (x0, v, who) in enumerate([(-80, 150, 'peaton1'), (900, -130, 'mujer')]):
            x, p, feet, b = gait(t, x0, v, U(who, 330), 1440)
            person_side(fr, who, x, 1440 + b, 330, dict(p, blink=blink(t, i)), t, feet=feet, facing=1 if v > 0 else -1)
        car(fr, lerp(-300, 1400, (t / 4.)), 1660, 1.1, (170, 40, 40), t, wheel=t * 9)
        car(fr, lerp(1500, -400, (t / 3.4)), 1840, 1.25, (60, 90, 150), t, wheel=-t * 11)
        blit(fr, s.clock, 540, 330 + (1 - ease(t / .8)) * 40, ease(t / .8))
        blit(fr, s.title, 540, 450, ease((t - .5) / .8))
    def cam(s, t, d):
        k = ease(t / d); return lerp(1.18, 1.04, k), 540, lerp(900, 1100, k), 0, 0          # grúa que baja

class S12(Shot):                                   # pareja entra a la tienda
    def __init__(s): s.back, s.main, s.front = set_street(seed=5)
    def draw(s, fr, t, d):
        street_props(fr, t, lamps=(250,), trees=(1000,), signal=False)
        door_open = ss(1.9, 2.4, t)
        cv2.rectangle(fr, (550, 1020), (int(550 + 140 * (1 - door_open)), 1340), (150, 190, 210), -1)     # hoja de vidrio que se abre
        cv2.rectangle(fr, (550, 1020), (int(550 + 140 * (1 - door_open)), 1340), (200, 220, 230), 4)
        # peatón al fondo
        x, p, feet, b = gait(t, 1150, -150, U('peaton2', 300), 1430)
        person_side(fr, 'peaton2', x, 1430 + b, 300, dict(p, blink=blink(t, 4)), t, feet=feet, facing=-1)
        # pareja: caminan, él se detiene y abre; ella entra; él la sigue
        uH, uM = U('peaton1', 420), U('novia', 420)
        dh = lambda tt: min(420., 230 * tt) if tt < 2.0 else 420 + 60 * ease((tt - 2.0) / .6) + max(0, tt - 3.1) * 230
        dm = lambda tt: 230 * tt
        for who, x0, dist, uu, sd in (('peaton1', 40, dh(t), uH, 7), ('novia', -230, dm(t) * 1.12, uM, 8)):
            if who == 'novia' and x0 + dist > 640: continue                           # ya entró
            x, p, feet, b = gait(0, x0, 1, uu, 1490, dist=dist)
            if who == 'peaton1':                                                       # la mano va a la puerta y regresa (sin saltos)
                wgt = ss(1.6, 2.0, t) * (1 - ss(2.9, 3.3, t)); p['grip'] = {'R': (600, 1500 - 4.3 * uH, wgt)}; p['look'] = (.3 * wgt + .55 * (1 - wgt), 0)
            if who == 'novia' and x0 + dist > 560: p['look'] = (.6, 0)
            person_side(fr, who, x, 1490 + b, 420, dict(p, blink=blink(t, sd), boca='sonrisa'), t, feet=feet, facing=1)
        cv2.rectangle(fr, (686, 1010), (704, 1340), (40, 30, 26), -1)                  # marco de la puerta (por delante)
    def cam(s, t, d):
        k = ease(t / d); return 1.08, lerp(420, 620, k), 1080, 0, 0                   # travelling lateral

class S13(Shot):                                   # hospital: llega la ambulancia
    def __init__(s):
        s.back, s.main, s.front = set_hospital()
        s.sign = N.text_sprite('HOSPITAL', 90, (255, 255, 255, 255), glow=(255, 60, 60), glow_r=16, spacing=12)
        s.urg = N.text_sprite('URGENCIAS', 30, (255, 255, 255, 255), pad=4, spacing=6)
    def draw(s, fr, t, d):
        blit(fr, s.urg, 540, 1130); blit(fr, s.sign, 540, 360); poly(fr, [(900, 290), (940, 290), (940, 330), (980, 330), (980, 370), (940, 370), (940, 410), (900, 410), (900, 370), (860, 370), (860, 330), (900, 330)], (230, 30, 40))
        x = 540 + 900 * (1 - ease(t / 1.8)) * -1 + 0                                   # frena progresivamente
        ax = lerp(-600, 520, ease(t / 1.8)); sy = 1.35; by = 1760                                         # ambulancia grande, en primer plano
        P = lambda px, py: (ax + px * sy, by + py * sy)
        poly(fr, [P(-260, 0), P(150, 0), P(150, -230), P(-260, -230)], (240, 240, 244))
        poly(fr, [P(150, 0), P(270, 0), P(270, -110), P(220, -170), P(150, -170)], (236, 236, 240)); poly(fr, [P(170, -100), P(250, -100), P(215, -155), P(170, -155)], (80, 120, 160))
        poly(fr, [P(-260, -110), P(270, -110), P(270, -80), P(-260, -80)], (220, 40, 40))
        poly(fr, [P(-90, -200), P(-60, -200), P(-60, -170), P(-30, -170), P(-30, -140), P(-60, -140), P(-60, -110), P(-90, -110), P(-90, -140), P(-120, -140), P(-120, -170), P(-90, -170)], (220, 40, 40))
        blit(fr, N.text_sprite('AMBULANCIA', 30, (220, 40, 40, 255), pad=6), *P(60, -45))
        for wx in (-170, 180): circ(fr, P(wx, 6), 44 * sy, (18, 18, 20)); circ(fr, P(wx, 6), 20 * sy, (150, 150, 158))
        on = (t * 4) % 1 < .5
        blit(fr, glow_sprite(110, (255, 30, 30) if on else (40, 80, 255)), *P(-200, -240), 1, add=True); blit(fr, glow_sprite(110, (40, 80, 255) if on else (255, 30, 30)), *P(100, -240), 1, add=True)
        tint(fr, (255, 40, 40) if on else (40, 80, 255), .08)
        k = ss(2.3, 3.0, t); fr[:] = to8(fr * (1 - k) + 255 * k * .9)              # barrido de luz hacia el interior
    def cam(s, t, d): k = ease(t / d); return lerp(1.04, 1.14, k), lerp(380, 600, k), 1150, 0, 0

class S14(Shot):                                   # pasillo: camilla apresurada
    shake = 4.
    def __init__(s): s.back, s.main, s.front = set_corridor()
    def draw(s, fr, t, d):
        if (t * 9) % 1 < .12 and t > 1.5: fr[:] = to8(fr * .82)                         # fluorescente que parpadea
        dist = 300 * t
        gx = -120 + dist
        poly(fr, [(gx - 240, 1440), (gx + 240, 1440), (gx + 240, 1480), (gx - 240, 1480)], (200, 204, 214))       # camilla
        poly(fr, [(gx - 230, 1400), (gx + 220, 1400), (gx + 240, 1440), (gx - 240, 1440)], (240, 244, 248))       # sábana
        circ(fr, (gx + 200, 1395), 40, (240, 244, 248))
        for wx in (-200, 200): line(fr, (gx + wx, 1480), (gx + wx, 1600), (90, 90, 96), 6); circ(fr, (gx + wx, 1610), 14, (30, 30, 34))
        tw = math.sin(t * 25) * 6 * (t > 1.2)                                                                      # la mano del paciente se crispa
        line(fr, (gx + 60, 1440), (gx + 70 + tw, 1520), (240, 244, 248), 18); circ(fr, (gx + 72 + tw, 1530), 14, SKIN)
        for who, off, sd in (('medico', -330, 1), ('enfermera', 330, 2)):
            x, p, feet, b = gait(t, -120 + off, 300, U(who, 470), 1700, run=True)
            p.update(grip={'R' if off < 0 else 'L': (gx + (off * .75), 1450)}, blink=blink(t, sd), frown=.3, boca='tensa')
            if who == 'medico' and t > 1.6: p['look'] = (-.6, 0)                                                   # voltea hacia atrás (con retraso)
            person_side(fr, who, x, 1700 + b, 470, p, t, feet=feet, facing=1)
        x, p, feet, b = gait(t, -420, 300, U('medico', 450), 1760, run=True)
        person_side(fr, 'medico', x, 1760 + b, 450, dict(p, blink=blink(t, 5), frown=.2), t, feet=feet, facing=1)
    def cam(s, t, d): z, cx, cy, dx, dy = super().cam(t, d); return 1.06, 540, 1150, dx, dy

# ================================================================ ESCENA 2 · LA FAMILIA
class Dining(Shot):
    """la familia cenando detrás de la mesa. t_news: momento de la alerta; mode controla las reacciones."""
    def __init__(s, zoom=(1.03, 1.08), cy=1100, cx=540, mode='cena', tv=0.):
        s.back, s.main, s.front = set_dining(); s.zoom = zoom; s.cy = cy; s.cx = cx; s.mode = mode; s.tv = tv
        s.names = {k: N.text_sprite(v, 30, (255, 236, 200, 255), stroke=3, stroke_col=(0, 0, 0, 220), spacing=4) for k, v in [('daniel', 'DANIEL · 32'), ('laura', 'LAURA'), ('sofia', 'SOFÍA · 9')]}
    def poses(s, t):
        m = s.mode; P = {}
        eat = (t % 2.2) / 2.2; up = math.sin(min(1, eat / .45) * math.pi) if eat < .45 else 0           # tenedor a la boca (arco)
        if m in ('cena', 'cena2'):
            P['daniel'] = dict(grip={'R': (600 + 40 * up, 1320 - 330 * up), 'L': (470, 1325)}, look=(.1 * up, .2 - .3 * up), boca='neutra' if up < .5 else 'o', frown=-.05)
            k = ss(1.4, 2.0, t) * (1 - ss(2.6, 3.2, t))                                                      # Laura le pasa el pan
            P['laura'] = dict(grip={'R': (330 + 140 * k, 1320 - 40 * k), 'L': (180, 1325)}, look=(.4 * k, .1), boca='sonrisa', frown=-.1, lean=.05 * k)
            P['sofia'] = dict(grip={'L': (760, 1325), 'R': (880, 1320)}, look=(-.3 + .2 * math.sin(t * 1.3), 0), boca='sonrisa', hip_dx=.25 * math.sin(t * 4), tilt=.06 * math.sin(t * 2))
        elif m == 'alerta':                                                                                   # Daniel deja los cubiertos y mira la TV
            k = ss(.2, .9, t); kh = ss(.6, 1.2, t); kb = ss(.9, 1.6, t)
            P['daniel'] = dict(grip={'R': (600, 1320 - 60 * (1 - k)), 'L': (470, 1325)}, look=(-.55 * kh, -.05), lean=-.06 * kb, frown=-.25 * kh, boca='neutra', tilt=-.04 * kh)
            kl = ss(1.2, 1.9, t)
            P['laura'] = dict(grip={'R': (330, 1322), 'L': (180, 1325)}, look=(.5 * kl, 0), lean=.08 * kl, frown=-.35 * kl, boca='triste' if kl > .5 else 'neutra')
            P['sofia'] = dict(grip={'L': (760, 1325), 'R': (880, 1325)}, look=(-.4, 0), frown=-.1)
        elif m == 'calma':                                                                                    # gesto tranquilizador / Laura preocupada
            k = ss(.3, .9, t); pw = math.sin(max(0, t - .9) * 3) * .12
            P['daniel'] = dict(grip={'R': (680 + 30 * pw * 5, 1250 - 40 * k + 30 * pw), 'L': (470, 1325)}, look=(-.35, 0), boca='sonrisa', frown=-.2)
            P['laura'] = dict(uR=.2, lR=-1.75, uL=-.2, lL=1.75, look=(.4, .05), tilt=.08 * math.sin(t * 5) * ss(1.2, 1.6, t) * (1 - ss(2.4, 2.8, t)), frown=-.42, boca='triste')
            P['sofia'] = dict(grip={'L': (760, 1325), 'R': (880, 1325)}, look=(-.45, -.05), frown=-.3, sh=.4, boca='o')
        return P
    def draw(s, fr, t, d):
        lamp(fr)
        P = s.poses(t)
        for x in (260, 540, 820): chair_back(fr, x, 1000, w=230, h=340)
        for who, x, h, sd in (('laura', 260, 760, 2), ('daniel', 540, 800, 1), ('sofia', 820, 760, 3)):
            p = dict(P[who]); p['blink'] = blink(t, sd)
            if 'grip' in p: p['grip'] = {k: (v[0] + (x - {'laura': 260, 'daniel': 540, 'sofia': 820}[who]) * 0, v[1]) for k, v in p['grip'].items()}
            person(fr, who, x, 1690 if who != 'sofia' else 1560, h, p, t)
        draw_table(fr, t=t)
        if s.mode == 'cena':
            for i, (who, x) in enumerate((('daniel', 540), ('laura', 260), ('sofia', 820))):
                a_ = ss(.4 + i * .9, .8 + i * .9, t); blit(fr, s.names[who], x, 760 if who != 'sofia' else 860, a_)
        if s.tv > 0:                                                                                   # luz de la TV (a la izquierda, fuera de cuadro)
            fl = s.tv * (.75 + .25 * math.sin(t * 17) * math.sin(t * 5.3)); tint(fr, (80, 140, 255), .22 * fl, 0, 700)
    def cam(s, t, d): k = ease(t / d); return lerp(*s.zoom, k), s.cx, s.cy, lerp(-15, 15, k), 0

class TVShot(Shot):                                # televisor: noticiero / mensaje / estática
    def __init__(s, kind):
        s.kind = kind; s.back, s.main, s.front = set_livingtv()
        s.live = N.text_sprite('● EN VIVO', 30, (255, 255, 255, 255), pad=6); s.logo = N.text_sprite('NOTICIAS 24', 26, (255, 255, 255, 255), pad=6, spacing=3)
        s.tick = N.text_sprite('ÚLTIMA HORA · SE REPORTAN ATAQUES EN EL CENTRO · HOSPITALES SATURADOS · EVITE SALIR DE CASA · ', 26, (255, 255, 255, 255), pad=4)
        s.b1 = N.text_sprite('ÚLTIMA HORA', 56, (255, 255, 255, 255), spacing=6); s.b2 = N.text_sprite('ATAQUES EN TODA LA CIUDAD · HOSPITALES SATURADOS', 30, (255, 255, 255, 255), pad=8)
        s.msg = N.text_sprite('PERMANEZCAN EN SUS CASAS', 50, (255, 255, 255, 255), spacing=4, maxw=700); s.ns = N.text_sprite('SIN SEÑAL', 70, (240, 240, 240, 255), stroke=5, stroke_col=(0, 0, 0, 255), spacing=8)
    def draw(s, fr, t, d):
        x0, y0, x1, y1 = 110, 560, 970, 1080
        cv2.rectangle(fr, (x0 - 30, y0 - 30), (x1 + 30, y1 + 30), (20, 20, 22), -1); cv2.rectangle(fr, (480, y1 + 30), (600, y1 + 120), (20, 20, 22), -1)
        cv2.rectangle(fr, (330, y1 + 120), (750, y1 + 140), (20, 20, 22), -1)
        scr = np.zeros((y1 - y0, x1 - x0, 3), np.uint8)
        if s.kind == 'static':
            nz = np.random.RandomState(int(t * 30)).randint(0, 255, ((y1 - y0) // 4, (x1 - x0) // 4, 1)).astype(np.uint8)
            scr[:] = cv2.resize(np.repeat(nz, 3, 2), (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST); scr[:] = (scr * .8).astype(np.uint8)
            blit(scr, s.ns, (x1 - x0) / 2, (y1 - y0) / 2, .6 + .4 * math.sin(t * 9))
        else:
            scr[:] = (24, 40, 90); cv2.rectangle(scr, (0, 0), (scr.shape[1], scr.shape[0]), (30, 50, 110), -1)
            cv2.rectangle(scr, (560, 40), (830, 250), (16, 26, 60), -1); cv2.rectangle(scr, (560, 40), (830, 250), (120, 200, 255), 3)     # mapa de la ciudad
            for k in range(8): cv2.line(scr, (570, 60 + k * 25), (820, 70 + k * 22), (50, 80, 130), 2); cv2.line(scr, (580 + k * 32, 50), (590 + k * 30, 240), (50, 80, 130), 2)
            for k, (mx, my) in enumerate([(610, 100), (700, 170), (760, 90), (650, 210), (790, 200)]):
                if (t * 2 + k * .3) % 1 < .7: cv2.circle(scr, (mx, my), 10, (255, 50, 40), -1)
            cv2.rectangle(scr, (0, 0), (180, 50), (200, 20, 30), -1); blit(scr, s.live, 90, 25); blit(scr, s.logo, 760, 290)
            cv2.rectangle(scr, (40, 300), (520, 520), (40, 30, 26), -1); cv2.rectangle(scr, (40, 300), (520, 312), (120, 200, 255), -1)   # escritorio
            person(scr, 'presentadora', 280, 560, 520, dict(uL=.3, lL=-1.3, uR=-.3, lR=1.3, blink=blink(t, 9), boca='o' if (t * 6) % 1 < .5 else 'neutra', frown=-.2), t)
            if s.kind == 'news':
                k = ss(.2, .6, t); cv2.rectangle(scr, (0, 380), (int(scr.shape[1] * k), 520), (200, 20, 30), -1)
                if k > .9: blit(scr, s.b1, 230, 425); blit(scr, s.b2, 430, 490)
                blit(fr, glow_sprite(40, (255, 40, 40)), x1 - 40, y0 + 40, .5 + .5 * math.sin(t * 8), add=True)
            else:
                cv2.rectangle(scr, (0, 360), (scr.shape[1], 520), (180, 20, 30), -1); blit(scr, s.msg, 430, 440, .7 + .3 * math.sin(t * 6))
        if s.kind != 'static':                                                     # cintillo que corre
            cv2.rectangle(scr, (0, scr.shape[0] - 40), (scr.shape[1], scr.shape[0]), (10, 10, 16), -1); tw = s.tick.shape[1]; off = (t * 160) % tw
            for k in (0, 1): blit(scr, s.tick, scr.shape[1] + tw / 2 - off - k * tw, scr.shape[0] - 20)
        fr[y0:y1, x0:x1] = scr
        tint(fr, (80, 140, 255) if s.kind != 'static' else (220, 220, 230), .08)
    def cam(s, t, d): k = ease(t / d); return lerp(1.0, 1.08, k), 540, 820, 0, 0

class SofiaMCU(Shot):                              # Sofía reacciona en su silla
    def __init__(s): s.back, s.main, s.front = set_dining()
    def draw(s, fr, t, d):
        k = ss(.3, .9, t); k2 = ss(1.2, 1.8, t)
        p = dict(grip={'L': (430, 1560), 'R': (690, 1560)}, hip_dx=.4 * math.sin(t * 3) * (1 - k2), look=(lerp(.5, -.5, k) * (1 - k2) - .1 * k2, -.05 * k2),
                 frown=-.45 * k2, sh=.7 * k2, boca='o' if k2 > .5 else 'neutra', blink=blink(t, 3))
        chair_back(fr, 560, 1020, w=420, h=600)
        person(fr, 'sofia', 560, 2030, 1700, p, t)
        draw_table(fr, y=1560, plates=((560, 1),), t=t)
        tint(fr, (80, 140, 255), .14 * (.7 + .3 * math.sin(t * 13)), 0, 540)
    def cam(s, t, d): k = ease(t / d); return lerp(1.0, 1.06, k), 540, 1150, 0, 0

# ================================================================ ESCENA 3 · LA ADVERTENCIA
class Phone(Shot):
    """Daniel toma el teléfono (mode='toma'), habla (mode='llamada') o la llamada se corta (mode='corte')."""
    def __init__(s, mode):
        s.back, s.main, s.front = set_dining(); s.mode = mode
        s.ph = phone_sprite('MARCOS', 'LLAMADA ENTRANTE'); s.end = phone_sprite('MARCOS', 'LLAMADA FINALIZADA', glow=(255, 90, 90))
    def draw(s, fr, t, d):
        m = s.mode
        if m == 'toma':
            person(fr, 'laura', 120, 1950, 900, dict(look=(.5, 0), frown=-.2, blink=blink(t, 2), grip={'R': (280, 1500)}), t)
            reach = ss(.6, 1.2, t); lift = ss(1.3, 2.3, t)
            ph0 = A(820, 1500); uD = U('daniel', 1150); ear = A(560 + 1.0 * uD, 2150 - 7.0 * uD)
            path = ph0 + (ear - ph0) * lift + A(60, -120) * math.sin(lift * math.pi)                                 # arco natural
            hand = A(620, 1500) + (ph0 - A(620, 1500)) * reach if lift <= 0 else path
            p = dict(grip={'R': tuple(hand), 'L': (500, 1510)}, look=(.4 * (1 - lift), .25 * (1 - lift)), frown=-.15 - .1 * lift, blink=blink(t, 1), lean=.06 * reach * (1 - lift))
            person(fr, 'daniel', 560, 2150, 1150, p, t)
            draw_table(fr, y=1510, plates=((560, 1),))
            vib = math.sin(t * 60) * 6 * (reach < .9)
            spr = cv2.resize(s.ph, (110, 205));
            if lift <= 0: blit(fr, spr, ph0[0] + vib, ph0[1] - 40, 1)
            else: blit(fr, cv2.resize(s.ph, (80, 150)), path[0] + 30, path[1] - 20, 1)
        else:
            dur_k = ss(.0, 3.5, t) if m == 'llamada' else 1.
            # Laura desenfocada al fondo, siguiéndolo con la mirada
            bg = np.zeros_like(fr); person(bg, 'laura', 130, 2150, 900, dict(look=(.5, 0), frown=-.35, blink=blink(t, 2)), t)
            bg = cv2.GaussianBlur(bg, (0, 0), 9); msk = (bg.max(2) > 8)[:, :, None]; fr[:] = np.where(msk, (bg * .8).astype(np.uint8), fr)
            if m == 'llamada':
                fw = ss(1.0, 3.4, t)
                uD = U('daniel', 1500); ear = (600 + 1.0 * uD, 2650 - 7.0 * uD)
                p = dict(grip={'R': ear, 'L': (500, 1680)}, look=(-.1, .05), frown=-.15 - .4 * fw, boca='neutra' if fw < .3 else ('tensa' if fw < .7 else 'o'),
                         lean=.1 * fw, sh=.4 * fw, blink=blink(t, 1))
                person(fr, 'daniel', 600, 2650, 1500, p, t)
                blit(fr, cv2.resize(s.ph, (90, 170)), ear[0] + 20, ear[1] - 30, 1)
            else:
                low = ss(.2, .9, t); uD = U('daniel', 1500); ear = A(600 + 1.0 * uD, 2650 - 7.0 * uD)
                hand = ear + (A(660, 1700) - ear) * low
                p = dict(grip={'R': tuple(hand), 'L': (500, 1680)}, look=(.1, .35 * low), frown=-.5, boca='o', sh=.5, blink=blink(t, 1))
                person(fr, 'daniel', 600, 2650, 1500, p, t)
                blit(fr, cv2.resize(s.end, (150, 280)) if low > .6 else cv2.resize(s.ph, (80, 150)), hand[0] + 10, hand[1] - 60, 1)
            draw_table(fr, y=1700, plates=())
    def cam(s, t, d): k = ease(t / d); return lerp(1.0, 1.06 if s.mode != 'llamada' else 1.12, k), 560, 1150, 0, 0

class ToWindow(Shot):                              # Daniel camina hacia la ventana; luces rojas y azules afuera
    def __init__(s): s.back, s.main, s.front = set_dining()
    def draw(s, fr, t, d):
        on = (t * 2.5) % 1 < .5; c = (255, 40, 40) if on else (40, 90, 255)
        blit(fr, glow_sprite(200, c), 850, 700, .55, add=True)
        person(fr, 'laura', 220, 1760, 700, dict(look=(.5, 0), frown=-.4, blink=blink(t, 2), grip={'R': (330, 1320)}), t)
        draw_table(fr, x0=40, x1=500, plates=((260, 1),))
        uu = U('daniel', 760); D_ = 2 * step_len(uu) * 1; dist = D_ * min(1., (t / 2.2) * (2 - t / 2.2)) if t < 2.2 else D_
        x, p, feet, b = gait(0, 360, 1, uu, 1820, dist=dist)
        k = 1 - ss(1.8, 2.2, t); p.update(uL=p['uL'] * k, uR=p['uR'] * k, blink=blink(t, 1), frown=-.35)
        p.update(grip={'R': (x + 1.45 * uu, 1820 - 5.0 * uu, ss(1.9, 2.5, t))}, lean=.06 * ss(1.9, 2.5, t))                                   # apoya la mano en el marco
        person_side(fr, 'daniel', x, 1820 + b * k, 760, p, t, feet=feet, facing=1)
        tint(fr, c, .1 * ss(.3, .8, t), 600, W)

# ================================================================ ESCENA 4 · EL COMIENZO DEL FIN
def infected_run(t, x0, v, uu, fy, f):
    """carrera del infectado: torso muy inclinado, brazos estirados hacia la presa, cabeza que se sacude, paso cojo."""
    x, p, feet, b = gait(t, x0, v, uu, fy, run=True)
    k = feet['L'][1] < fy - 1 and math.sin(t * 9) > 0                     # una pierna arrastra (cojea)
    p.update(lean=f * .38, uL=f * (1.25 + .15 * math.sin(t * 11)), lL=.25, uR=f * (1.05 + .15 * math.sin(t * 9 + 1)), lR=.3,
             tilt=.22 * math.sin(t * 7) + f * .1, boca='grito', frown=-.2, look=(.6 * f, .1), blink=0)
    return x, p, feet, b * 1.4

class Crash(Shot):                                 # por la ventana: el auto derrapa y se estrella contra la tienda
    shake = 0.
    def __init__(s):
        s.back, s.main, s.front = set_street(seed=9); s.sparks = rng.uniform(0, 1, (46, 3))
        win = np.zeros((H, W, 4), np.uint8)
        cv2.rectangle(win, (0, 0), (W, H), (70, 48, 32, 255), 70); cv2.rectangle(win, (528, 0), (552, H), (70, 48, 32, 255), -1)      # marco de la ventana
        cv2.rectangle(win, (0, 0), (64, H), (130, 50, 56, 255), -1); cv2.rectangle(win, (W - 64, 0), (W, H), (130, 50, 56, 255), -1)   # cortinas recogidas
        cv2.rectangle(win, (0, H - 150), (W, H), (90, 64, 44, 255), -1)                                                                  # repisa
        poly(win, [(820, H - 150), (900, H - 150), (890, H - 70), (830, H - 70)], (170, 96, 64, 255))
        for k in range(7): cv2.ellipse(win, (860 + (k - 3) * 18, H - 180 - (k % 2) * 26), (12, 34), (k - 3) * 18, 0, 360, (56, 128, 70, 255), -1, cv2.LINE_AA)
        s.front = [(dof(win, 3), 1.2)]
    def draw(s, fr, t, d):
        street_props(fr, t)
        tc = 2.0
        if t < tc:                                                           # pierde el control: derrapa (giro moderado) y se va contra la vitrina
            k = t / tc; x = lerp(-320, 330, ease(k)); y = lerp(1720, 1430, k ** 1.6); ang = -.32 * ss(.5, 1.6, t) + .07 * math.sin(t * 14) * ss(.4, 1.0, t)
        else: x, y, ang = 330, 1430, -.32
        if t >= tc:
            cv2.rectangle(fr, (90, 1010), (520, 1330), (36, 30, 34), -1)                                     # vitrina rota
            for k in range(9): line(fr, (300, 1170), (300 + math.cos(k * .7) * 220, 1170 + math.sin(k * .7) * 150), (200, 220, 230), 2)
        car(fr, x, y, 1.25, (70, 74, 86), t, ang=ang, wheel=t * 12)
        if t >= tc:
            f = t - tc
            blit(fr, glow_sprite(240, (255, 140, 40)), 420, 1260, (.55 + .3 * math.sin(t * 13)) * min(1, f * 4), add=True)
            for i in range(10): g = (f * .5 + i / 10.) % 1; blit(fr, glow_sprite(90, (70, 66, 70)), 380 + math.sin(i * 3 + f) * 60, 1250 - g * 600, (1 - g) * .45 * min(1, f * 2), 1 + g * 1.5)   # humo
            for i, (a_, b_, c_) in enumerate(s.sparks):                                                      # vidrios y chispas
                vx, vy = (a_ - .3) * 900, -300 - b_ * 600; px = 300 + vx * f; py = 1200 + vy * f + 900 * f * f
                if py < 1500: circ(fr, (px, py), 3 + 3 * c_, (255, 230, 160) if i % 2 else (200, 230, 255))
            for i, (who, x0, v) in enumerate((('peaton1', 520, 520), ('mujer', 260, -480), ('peaton2', 760, 560))):   # la gente huye
                if f < .25: continue
                xx, p, feet, b = gait(f - .25, x0, v, U(who, 330), 1450 + i * 12, run=True)
                p.update(frown=-.5, boca='grito', sh=.8, blink=0, uL=p['uL'] * .6 - .6 * (v > 0) + .6 * (v < 0), lL=1.3)
                person_side(fr, who, xx, 1450 + i * 12 + b, 330, p, t, feet=feet, facing=1 if v > 0 else -1)
        s.shake = 12 * math.exp(-max(0, t - tc) * 3) if t >= tc else 0
    def cam(s, t, d): z, cx, cy, dx, dy = Shot.cam(s, t, d); return 1.08, 540, 1150, dx, dy

class Fall(Shot):                                  # una mujer huye, tropieza con unas bolsas de basura y cae; un infectado se abalanza
    shake = 5.
    def __init__(s):
        s.back, s.main, s.front = set_street(seed=13)
        s.front = [(bokeh_layer(14, (255, 120, 50), 61, rmin=20, rmax=60, ymin=200, ymax=1700), 1.7)]
    def draw(s, fr, t, d):
        street_props(fr, t, signal=False)
        blit(fr, glow_sprite(320, (255, 120, 40)), 160, 1250, .5 + .2 * math.sin(t * 11), add=True)
        bags = (560, 1716)
        for k, (dx, r) in enumerate([(-40, 46), (20, 52), (70, 40)]): ell(fr, (bags[0] + dx, bags[1] - r * .6), r, r * .75, 0, (30, 30, 34)); line(fr, (bags[0] + dx, bags[1] - r * 1.3), (bags[0] + dx + 8, bags[1] - r * 1.45), (60, 60, 64), 4)
        tf = 1.05; uu = U('mujer', 520)
        if t < tf:
            x, p, feet, b = gait(t, -60, 560, uu, 1720, run=True); p.update(frown=-.5, boca='grito', sh=.8, blink=0, look=(-.4, 0))   # mira hacia atrás mientras corre
            person_side(fr, 'mujer', x, 1720 + b, 520, p, t, feet=feet, facing=1)
        else:
            f = t - tf; x0 = -60 + 560 * tf
            ang = 1.45 * ease(f / .5); slide = 160 * ease(f / .55)
            p = dict(lean=0, uL=-1.6 * ease(f / .35), lL=.3, uR=-1.4 * ease(f / .35), lR=.3, thL=-.5, thR=.35, frown=-.6, boca='grito', sh=1., look=(.5, -.2))
            draw_rotated(fr, lambda c: person_side(c, 'mujer', x0 + slide, 1720, 520, p, t, facing=1), (x0 + slide, 1720), ang)
            if 0 < f < .4:
                for k in range(6): circ(fr, (x0 + slide + 340 + k * 14, 1700 - k * 6), 4, (200, 200, 190))      # polvo del golpe
        if t > 1.25:                                                         # el infectado llega cojeando y se lanza (corte antes del contacto)
            g = t - 1.25; dist = min(520., 620 * g)
            x, p, feet, b = infected_run(g, 1220, -1, U('infectado', 560), 1730, -1)
            x = 1220 - dist; feet = {k_: (v_[0] + (1220 - 620 * g) * 0 - (dist - 620 * g) * 0, v_[1]) for k_, v_ in gait(0, 1220, -1, U('infectado', 560), 1730, run=True, dist=dist)[2].items()}
            lunge = ss(.55, .95, g)
            p.update(lean=-.38 - .45 * lunge, uL=-1.5 - .2 * lunge, uR=-1.3 - .2 * lunge)
            person_side(fr, 'infectado', x, 1730 + b, 560, p, t, feet=feet, facing=-1)
        tint(fr, (255, 110, 40), .08)
    def cam(s, t, d): z, cx, cy, dx, dy = Shot.cam(s, t, d); return 1.08, 560, 1250, dx, dy

class RunLock(Shot):                               # Daniel corre a la puerta, frena, gira y pone el seguro
    def __init__(s): s.back, s.main, s.front = set_hall(door_x=820)
    def draw(s, fr, t, d):
        uu = U('daniel', 690); D_ = 4 * step_len(uu, True)
        dist = D_ * (1 - (1 - min(1, t / 1.6)) ** 2)                      # corre y desacelera en los últimos pasos
        door_parts(fr, 820, [], t, lock_k=ss(2.0, 2.3, t))
        x, p, feet, b = gait(0, -120, 1, uu, 1340, run=True, dist=dist)
        k = 1 - ss(1.2, 1.6, t)
        p.update(uL=p['uL'] * k, uR=p['uR'] * k, lean=p['lean'] * k + .04, frown=-.5, boca='tensa', blink=blink(t, 1))
        p.update(grip={'R': (690, 945 + 10 * math.sin(ss(2.0, 2.3, t) * math.pi), ss(1.3, 1.9, t))})                # extiende el brazo al cerrojo
        person_side(fr, 'daniel', x, 1340 + b * k, 690, p, t, feet=feet, facing=1)
    def cam(s, t, d): x = -120 + 4 * step_len(U('daniel', 690), True) * (1 - (1 - min(1, t / 1.6)) ** 2); return 1.06, 540, 1150, -(x - 540) * .25, 0

def carry(fr, t, x, fy, lift, h=800, cry=0., hide=0., step_back=None):
    """Laura (de frente) se agacha, toma a Sofía y la carga en la cadera; Sofía le rodea el cuello y su cabeza
    queda junto a la de su mamá (no la tapa)."""
    uL = U('laura', h); crouch = math.sin(min(1, lift * 2) * math.pi / 2) * (1 - max(0, lift - .5) * 2)
    body_fy = fy + crouch * 1.3 * uL
    hip = A(x, body_fy - 3.35 * uL); neck = hip + A(0, -2.45 * uL)
    sof_h = h * .95; uS = U('sofia', sof_h); up = ease(max(0, lift - .35) / .65)
    side = A(x + 1.65 * uL, hip[1] - 1.1 * uL)                              # cadera derecha de Laura (donde se sienta Sofía)
    ground = A(x + 2.6 * uL, fy)
    shp = ground + (side + A(0, 3.35 * uS) - ground) * up                    # «suelo» virtual de Sofía mientras la sube
    sx, sfy = shp
    ship = A(sx, sfy - 3.35 * uS)
    gw = ss(.12, .35, lift)
    pl = dict(grip={'R': tuple(ship + A(.2 * uS, .4 * uS)) + (gw,), 'L': tuple(ship + A(-.4 * uS, -1.6 * uS)) + (gw,)},
              lean=-.05 * up, frown=-.35, boca='tensa' if hide < .9 else 'o', look=(.35 * (1 - hide) - .1 * hide, .05), blink=blink(t, 2), tilt=.06 * up)
    ps = dict(uL=-.2 - 1.6 * up, lL=-1.2 * up, uR=.2, lR=0., thL=-.2 - .7 * up, snL=.9 * up, thR=.15 - .55 * up, snR=.65 * up,
              grip={'L': tuple(neck + A(.5 * uL, .55 * uL)) + (ss(.45, .85, up),), 'R': tuple(neck + A(1.0 * uL, .3 * uL)) + (ss(.45, .85, up),)},
              look=(-.5 * up, .1 + .2 * hide), frown=-.4 - .2 * cry, boca='grito' if cry > .5 else ('triste' if up > .5 else 'o'),
              sh=.5 * up + .25 * math.sin(t * 18) * cry, tilt=-.18 * up - .15 * hide, blink=1. if hide > .6 else blink(t, 3))
    person(fr, 'sofia', sx, sfy, sof_h, ps, t)
    person(fr, 'laura', x, body_fy, h, pl, t, feet={'L': (x - .5 * uL, fy), 'R': (x + .5 * uL, fy)})
    if lift > .25:                                                     # las manos de Laura quedan por delante (sosteniéndola)
        for h_, g in pl['grip'].items():
            if g[2] > .98: circ(fr, g[:2], .31 * uL, (170, 172, 182)); circ(fr, g[:2], .27 * uL, SKIN)

class Lift(Shot):
    def __init__(s): s.back, s.main, s.front = set_dining()
    def draw(s, fr, t, d):
        lamp(fr); draw_table(fr, x0=620, x1=1080, plates=((850, 1),))
        carry(fr, t, 360, 1780, ss(.2, 2.4, t))
        on = (t * 2.5) % 1 < .5; tint(fr, (255, 40, 40) if on else (40, 90, 255), .06)
    def cam(s, t, d): k = ease(t / d); return lerp(1.03, 1.1, k), 480, 1150, 0, 0

# ================================================================ ESCENA 5 · LOS GOLPES
class Knocks(Shot):
    def __init__(s): s.back, s.main, s.front = set_hall(door_x=700); s.kn = [.5, 1.1, 1.7]
    def draw(s, fr, t, d):
        door_parts(fr, 700, s.kn, t, lock_k=1)
        st = sum(math.exp(-((t - k) / .08) ** 2) for k in s.kn[:1]); jolt = ss(.5, .62, t) * (1 - ss(.9, 1.6, t))
        x, p, feet, b = gait(0, 330, 1, U('daniel', 690), 1340, dist=0)
        p.update(uL=-.5 * jolt, uR=-.3 * jolt, lL=1.2 * jolt, lR=1.2 * jolt, sh=1.0 * jolt + .4 * ss(1, 2, t), lean=-.1 * jolt, frown=-.6 * ss(.5, .7, t), boca='o' if jolt > .3 else 'tensa',
                 blink=blink(t, 1), look=(.5, 0))
        person_side(fr, 'daniel', x, 1340 - 40 * jolt * math.exp(-max(0, t - .55) * 6), 690, p, t, feet={k: (v[0], v[1]) for k, v in feet.items()}, facing=1)
        s.shake = 7 * sum(math.exp(-((t - k) / .07) ** 2) for k in s.kn)
    def cam(s, t, d): z, cx, cy, dx, dy = Shot.cam(s, t, d); return 1.04, 540, 1150, dx, dy

class Protect(Shot):                               # Laura retrocede protegiendo a Sofía
    def __init__(s): s.back, s.main, s.front = set_hall(door_x=980)
    def draw(s, fr, t, d):
        door_parts(fr, 980, [.4, 1.3, 2.2], t, lock_k=1)
        x = 560 - 160 * ease(t / 1.4)
        carry(fr, t, x, 1790, 1.0, h=820, hide=ss(.6, 1.2, t) * .4, cry=ss(1.0, 1.4, t) * .7)
        s.shake = 4 * sum(math.exp(-((t - k) / .07) ** 2) for k in (.4, 1.3, 2.2))

class Peephole_approach(Shot):                     # Daniel se acerca lento a la mirilla
    def __init__(s): s.back, s.main, s.front = set_hall(door_x=760)
    def draw(s, fr, t, d):
        door_parts(fr, 760, [], t, lock_k=1)
        uu = U('daniel', 690); dist = 2 * step_len(uu) * 1.0 * ease(t / 2.0)
        x, p, feet, b = gait(0, 330, 1, uu, 1340, dist=dist)
        k = ss(1.7, 2.3, t)
        p.update(uL=p['uL'] * .3, uR=p['uR'] * .3, sh=.8, lean=.05 + .2 * k, frown=-.5, boca='tensa', blink=blink(t, 1),
                 grip={'R': (640, 1000, ss(1.3, 2.0, t))})
        person_side(fr, 'daniel', x, 1340, 690, p, t, feet=feet, facing=1)
    def cam(s, t, d): k = ease(t / d); return lerp(1.02, 1.2, k), 640, lerp(1150, 1000, k), 0, 0      # dolly in

class Peephole(Shot):                              # vista por la mirilla (ojo de pez): el hombre golpea y suplica
    def __init__(s, creature=False):
        s.creature = creature; s.porch = set_porch(); sky = vgrad([(0, (8, 14, 12)), (1, (30, 46, 36))]); s.back = [(opaque(sky), .2)]
        s.main = np.zeros((H, W, 4), np.uint8); s.front = []
    def draw(s, fr, t, d):
        porch = s.porch.copy()
        fl = .85 + .15 * (math.sin(t * 31) > -.7); blit(porch, glow_sprite(260, (180, 255, 190)), 540, 380, .55 * fl, add=True)   # lámpara que parpadea
        look_back = 0.
        if s.creature:                                                       # detrás de él, en la penumbra, un infectado se acerca cojeando
            g = ss(.1, 2.8, t); look_back = ss(1.0, 1.4, t)
            sc = 420 + 200 * g; dist = 260 * g; x0 = 120
            x, p, feet, b = infected_run(t * .5, x0, 1, U('infectado', sc), 1440, 1)
            feet = gait(0, x0, 1, U('infectado', sc), 1440, dist=dist)[2]
            p.update(lean=.15, uL=1.0 + .2 * math.sin(t * 5), uR=.8, lL=-.3, lR=-.3, tilt=.25 * math.sin(t * 4))
            silh = np.zeros_like(porch); person_side(silh, 'infectado', x0 + dist, 1440 + b * .5, sc, p, t, feet=feet, facing=1)
            m = (silh.max(2) > 6)[:, :, None]; porch[:] = np.where(m, (silh * (.5 + .3 * g)).astype(np.uint8), porch)
            blit(porch, glow_sprite(14, (255, 250, 210)), x0 + dist + .5 * U('infectado', sc), 1440 - 7.0 * U('infectado', sc), .9, add=True)
        # el hombre: golpea con los puños alternando, pega la cara a la mirilla, voltea hacia atrás
        ph = (t * 1.6) % 1; hitR = ph < .5; k = math.sin(ph * 2 * math.pi)
        reach = lambda on, kk: (on * (.5 + .5 * kk))
        pr = reach(hitR, k); pl_ = reach(not hitR, -k)
        uH = U('hombre', 1150); head_y = 2050 - 7.0 * uH
        x_man = 600 if s.creature else 540                                    # puños al frente, a la altura del pecho: golpe hacia la puerta
        p = dict(grip={'R': (x_man + 170 - 30 * pr, head_y + 330 - 120 * pr, 1.), 'L': (x_man - 170 + 30 * pl_, head_y + 330 - 120 * pl_, 1.)},
                 look=(-.6 * look_back + .05 * math.sin(t * 3), -.05), tilt=.06 * math.sin(t * 2.3) - .15 * look_back, frown=-.6,
                 boca='grito' if (t * 2.4) % 1 < .55 else 'o', sh=.6, blink=blink(t, 7))
        person(porch, 'hombre', x_man, 2050, 1150, p, t)
        for pt, kk in ((p['grip']['R'], pr), (p['grip']['L'], pl_)):          # el puño crece al acercarse al lente
            circ(porch, pt[:2], (.27 + .12 * kk) * U('hombre', 1150), dark(CAST['hombre']['piel'], .9))
        tint(porch, (120, 255, 150), .1)
        fr[:] = fisheye(porch, .45)
        if t % .625 < .05: fr[:] = to8(fr * 1.06)                            # cada golpe: destello y sacudida leve
    def cam(s, t, d):
        hit = math.exp(-((t % .625) / .05) ** 2) * 6; return 1.0, 540, 960, math.sin(t * 2) * 3 + hit, hit * .5

class Whisper(Shot):                               # Laura susurra
    def __init__(s): s.back, s.main, s.front = set_hall(door_x=980)
    def draw(s, fr, t, d):
        carry(fr, t, 400, 2300, 1.0, h=1250, hide=.15, cry=.3)
    def cam(s, t, d): k = ease(t / d); return lerp(1.05, 1.12, k), 520, 900, 0, 0

# ================================================================ ESCENA 6 · LA DECISIÓN
class Doubt(Shot):                                 # Daniel duda: mira la puerta, a su familia, la puerta; la mano se acerca a la perilla
    def __init__(s): s.back, s.main, s.front = set_hall(door_x=880)
    def draw(s, fr, t, d):
        door_parts(fr, 880, [.6, 1.2], t, lock_k=1)
        lk = [(0, .6), (.45, .6), (.75, -.6), (1.15, -.6), (1.45, .6)]
        lx = lk[-1][1]
        for (a_, va), (b_, vb) in zip(lk[:-1], lk[1:]):
            if a_ <= t <= b_: lx = lerp(va, vb, ease((t - a_) / (b_ - a_))); break
        if t < lk[0][0]: lx = lk[0][1]
        p = dict(uL=-.12, lL=.12, grip={'R': (800, 1880 - 60 * ss(.9, 1.5, t), ss(.3, 1.2, t))}, look=(lx, 0), frown=-.55, boca='tensa', sh=.7,
                 blink=blink(t, 1), tilt=.05 * math.sin(t * 2), lean=.04 * lx)
        person(fr, 'daniel', 470, 2300, 1300, p, t)
    def cam(s, t, d): k = ease(t / d); return lerp(1.04, 1.1, k), 540, 1000, 0, 0

class Cry(Shot):
    def __init__(s): s.back, s.main, s.front = set_hall(door_x=980)
    def draw(s, fr, t, d): carry(fr, t, 400, 2150, 1.0, h=1100, hide=.2, cry=1.)

class Choice(Shot):                                # opciones A / B
    def __init__(s):
        s.back = [(opaque(np.zeros((H, W, 3), np.float32)), 0.)]; s.main = np.zeros((H, W, 4), np.uint8); s.front = []
        s.a1 = N.text_sprite('A', 200, (255, 90, 80, 255), glow=(255, 40, 40), glow_r=20); s.b1 = N.text_sprite('B', 200, (110, 170, 255, 255), glow=(60, 120, 255), glow_r=20)
        s.a2 = N.text_sprite('ABRIR LA PUERTA', 52, (255, 230, 230, 255), stroke=5, stroke_col=(0, 0, 0, 230), maxw=480); s.a3 = N.text_sprite('Intentar salvar al desconocido', 30, (230, 200, 200, 255), maxw=480)
        s.b2 = N.text_sprite('ESCONDERSE', 52, (230, 236, 255, 255), stroke=5, stroke_col=(0, 0, 0, 230), maxw=480); s.b3 = N.text_sprite('Llevar a su familia al sótano', 30, (200, 210, 235, 255), maxw=480)
        s.q = N.text_sprite('¿QUÉ DEBERÍA HACER DANIEL?', 56, (255, 255, 255, 255), stroke=5, stroke_col=(0, 0, 0, 230), maxw=960)
    def draw(s, fr, t, d):
        fr[:, :540] = (40, 8, 10); fr[:, 540:] = (8, 14, 40)
        blit(fr, glow_sprite(300, (255, 40, 40)), 270, 1000, .25, add=True); blit(fr, glow_sprite(300, (40, 90, 255)), 810, 1000, .25, add=True)
        # A: manija que brilla · B: escaleras al sótano
        cv2.rectangle(fr, (150, 820), (390, 1300), (90, 50, 30), -1); circ(fr, (350, 1080), 20, (255, 210, 120)); blit(fr, glow_sprite(60, (255, 200, 120)), 350, 1080, .6 + .4 * math.sin(t * 4), add=True)
        for k in range(7): cv2.rectangle(fr, (640 + k * 30, 820 + k * 70), (980, 880 + k * 70), (int(40 + k * 4), int(50 + k * 4), int(80 + k * 6)), -1)
        line(fr, (540, 300), (540, 1650), (255, 255, 255), 3)
        a = ss(.2, .6, t); b = ss(1.0, 1.4, t)
        blit(fr, s.q, 540, 360, ss(0, .4, t))
        blit(fr, s.a1, 270, 640, a, lerp(1.4, 1, a)); blit(fr, s.a2, 270, 1400, a); blit(fr, s.a3, 270, 1470, a)
        blit(fr, s.b1, 810, 640, b, lerp(1.4, 1, b)); blit(fr, s.b2, 810, 1400, b); blit(fr, s.b3, 810, 1470, b)
    def cam(s, t, d): return lerp(1.0, 1.04, ease(t / d)), 540, 960, 0, 0

class EndCard(Shot):
    def __init__(s):
        s.back = [(opaque(np.zeros((H, W, 3), np.float32)), 0.)]; s.main = np.zeros((H, W, 4), np.uint8); s.front = [(bokeh_layer(10, (255, 90, 70), 81, ymin=200, ymax=1700), 1.6)]
        s.l1 = N.text_sprite('TÚ DECIDES', 96, (255, 255, 255, 255), glow=(255, 60, 60), glow_r=14, spacing=8)
        s.l2 = N.text_sprite('COMENTA  A  o  B', 70, (255, 220, 120, 255), stroke=5, stroke_col=(0, 0, 0, 230), spacing=6)
        s.l3 = N.text_sprite('EL DÍA QUE TODO TERMINÓ', 44, (220, 220, 230, 255), spacing=10); s.l4 = N.text_sprite('EPISODIO 02 · PRÓXIMAMENTE', 34, (255, 120, 110, 255), spacing=6)
    def draw(s, fr, t, d):
        fr[:] = (10, 6, 8); blit(fr, glow_sprite(400, (120, 20, 20)), 540, 900, .5, add=True)
        blit(fr, s.l1, 540, 760, ss(0, .5, t), lerp(1.3, 1, ss(0, .5, t))); blit(fr, s.l2, 540, 920, ss(.5, .9, t))
        blit(fr, s.l3, 540, 1240, ss(1.4, 1.9, t)); blit(fr, s.l4, 540, 1320, ss(1.8, 2.3, t))
    def cam(s, t, d): return lerp(1.0, 1.05, ease(t / d)), 540, 960, 0, 0

# ================================================================ línea de tiempo · narración en pantalla
SHOTS = [  # (inicio, plano, grado de color, narración)
    (0.0, S11, (), 0, '10:47 de la noche. En una pequeña ciudad de Estados Unidos, todo parece normal.'),
    (4.0, S12, (), 0, 'Las familias cenan, los negocios siguen abiertos…'),
    (8.0, S13, (), 1, 'Pero en el hospital…'),
    (11.0, S14, (), 1, 'los médicos intentan contener algo que todavía no comprenden.'),
    (14.5, Dining, dict(mode='cena'), 2, 'Daniel tiene 32 años. Vive con su esposa Laura y su hija Sofía, de nueve.'),
    (19.0, Dining, dict(mode='cena2', zoom=(1.12, 1.2), cy=1050, tv=.6), 2, 'Esta noche cenan con las noticias de fondo…'),
    (22.5, TVShot, ('news',), 3, 'hasta que aparece una alerta de última hora:'),
    (25.0, Dining, dict(mode='alerta', zoom=(1.25, 1.32), cy=1020, cx=420, tv=1.), 3, 'personas atacando a desconocidos por toda la ciudad.'),
    (28.5, SofiaMCU, (), 3, 'Hospitales saturados.'),
    (31.0, Dining, dict(mode='calma', zoom=(1.2, 1.26), cy=1030, cx=400, tv=1.), 3, 'Las autoridades piden no salir de casa.'),
    (34.0, Phone, ('toma',), 3, 'Suena el teléfono. Es Marcos, su hermano.'),
    (37.0, Phone, ('llamada',), 4, 'Está desesperado: algo pasa en las calles… que cierre todas las puertas.'),
    (41.0, Phone, ('corte',), 4, 'Y la llamada… se corta.'),
    (43.0, ToWindow, (), 4, 'Daniel mira por la ventana.'),
    (46.0, Crash, (), 4, 'Un auto se estrella contra una tienda.'),
    (50.0, Fall, (), 4, 'La gente corre. Una mujer cae… y alguien se abalanza sobre ella.'),
    (53.5, RunLock, (), 4, ''),
    (56.5, Lift, (), 4, ''),
    (59.5, TVShot, ('static',), 4, ''),
    (61.0, Knocks, (), 4, 'Y entonces… tres golpes sacuden la puerta.'),
    (64.0, Protect, (), 4, '—¡POR FAVOR! ¡DÉJENME ENTRAR!'),
    (67.0, Peephole_approach, (), 4, 'Daniel mira por la mirilla.'),
    (69.5, Peephole, (), 4, 'Es un hombre cubierto de sangre. Pero algo no está bien: no deja de golpear.'),
    (74.0, Whisper, (), 4, 'LAURA: «Daniel… no lo dejes entrar.»'),
    (77.0, Doubt, (), 4, 'Su hija llora.'),
    (78.6, Cry, (), 4, 'El hombre suplica.'),
    (80.0, Peephole, (True,), 4, 'Y algo se mueve detrás de él, en la oscuridad.'),
    (83.0, Choice, (), 4, ''),
    (88.5, EndCard, (), 4, 'Porque mañana… quizá ya no exista un lugar seguro.'),
]
DUR = 93.0

def build():
    shots = []
    for i, (t0, cls, args, g, txt) in enumerate(SHOTS):
        t1 = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else DUR
        obj = cls(**args) if isinstance(args, dict) else cls(*args)
        shots.append((t0, t1, obj, g, txt))
    caps = []
    for t0, t1, _, _, txt in shots:                                       # narración en pantalla: frases de ≤ 7 palabras repartidas en el plano
        if not txt: continue
        dialog = txt.startswith(('—', 'LAURA'))
        words = txt.split(); chunks = []; cur = []
        for w in words:
            cur.append(w)
            if len(cur) >= 6 or w[-1] in '.,:…?!»': chunks.append(' '.join(cur)); cur = []
        if cur: chunks.append(' '.join(cur))
        tot = sum(len(c) for c in chunks); a = t0 + .25; span = (t1 - t0) - .45
        for c in chunks:
            b = a + span * len(c) / tot
            col = (255, 120, 110) if txt.startswith('—') else ((255, 236, 190) if dialog else (255, 255, 255))
            caps.append((a, b, caption_sprite(c, col)))
            a = b
    return shots, caps

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    shots, caps = build()
    def one(i, T):
        a, b, sc, g, _ = shots[i]; return cinema(render3d(sc, T - a, b - a, T), g, T)
    def frame(T):
        i = max(k for k, s_ in enumerate(shots) if T >= s_[0] - 1e-6)
        fr = one(i, T); a = shots[i][0]
        if i > 0 and T - a < .25 and shots[i][2].__class__ not in (Choice,): fr = cv2.addWeighted(one(i - 1, T), 1 - ss(0, .25, T - a), fr, ss(0, .25, T - a), 0)
        for a_, b_, spr in caps:
            if a_ <= T < b_: blit(fr, spr, 540, 1560, min(1, (T - a_) / .12) * min(1, (b_ - T) / .12))
        if T < .6: fr = to8(fr * (T / .6))                                  # fundido de entrada
        return fr
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    if mode == 'info':
        for t0, t1, sc, g, txt in shots: print(f'{t0:5.1f}-{t1:5.1f} {type(sc).__name__:18s} {txt[:50]}')
    elif mode == 'test':
        import traceback
        for T in [float(x) for x in sys.argv[2:]]:
          try:
            cv2.imwrite(f'{out}/e_{T:05.1f}.jpg', cv2.resize(frame(T), (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
          except Exception as e: print('ERROR', T, repr(e)); traceback.print_exc(limit=-2)
    elif mode == 'seg':
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', f'{out}/seg_{f0:05d}.mp4'], stdin=subprocess.PIPE)
        for i in range(f0, f1): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('SEG', f0, f1, flush=True)

if __name__ == '__main__': main()
