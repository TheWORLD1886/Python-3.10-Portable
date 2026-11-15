#!/usr/bin/env python3
# Versión con profundidad 3D: capas con paralaje, desenfoque por distancia (DOF), bruma atmosférica,
# primer plano desenfocado, bokeh y mapa en perspectiva sobre una mesa.
import narco_short as N
from narco_short import *

# ---------------------------------------------------------------- utilidades de capas
def M3(z, cx, cy, dx, dy, ang=0.):
    m = np.eye(3); m[:2] = cv2.getRotationMatrix2D((cx, cy), ang, z); m[0, 2] += dx; m[1, 2] += dy; return m
def rgba(img_rgb, alpha):  # alpha float 0..1 (H,W)
    return np.dstack([img_rgb.astype(np.uint8), (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
def comp(dst, lay):  # dst float/uint8 RGB in-place, lay RGBA uint8 (same size)
    a = lay[:, :, 3:4].astype(np.float32) / 255.
    dst[:] = dst * (1 - a) + lay[:, :, :3].astype(np.float32) * a
def warp(lay, m, persp=False):
    if persp: return cv2.warpPerspective(lay, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return cv2.warpAffine(lay, m[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
def dof(lay, sig):  # desenfoque de lente (con alfa premultiplicado para bordes limpios)
    if sig <= 0: return lay
    f = lay.astype(np.float32); a = f[:, :, 3:4] / 255.; pm = f[:, :, :3] * a
    pm = cv2.GaussianBlur(pm, (0, 0), sig); ab = cv2.GaussianBlur(a[:, :, 0], (0, 0), sig)[:, :, None]
    return np.dstack([np.clip(pm / np.maximum(ab, 1e-4), 0, 255), ab * 255]).astype(np.uint8)
def haze(lay, col, k):  # perspectiva atmosférica
    out = lay.copy(); out[:, :, :3] = to8(lay[:, :, :3] * (1 - k) + np.array(col, np.float32) * k); return out
def bokeh_layer(n, col, seed, rmin=30, rmax=90, ymin=0, ymax=H):
    r_ = np.random.RandomState(seed); lay = np.zeros((H, W, 4), np.float32)
    for _ in range(n):
        x, y, r = r_.uniform(-50, W + 50), r_.uniform(ymin, ymax), r_.uniform(rmin, rmax)
        c = np.array(col, np.float32) * r_.uniform(.6, 1.1)
        cv2.circle(lay, (int(x), int(y)), int(r), (float(c[0]), float(c[1]), float(c[2]), r_.uniform(25, 60)), -1, cv2.LINE_AA)
        cv2.circle(lay, (int(x), int(y)), int(r), (float(min(255, c[0] + 40)), float(min(255, c[1] + 40)), float(min(255, c[2] + 40)), 90), 2, cv2.LINE_AA)
    return dof(np.clip(lay, 0, 255).astype(np.uint8), 7)

# ================================================================ 1 · Palacio: cielo lejano, ciudad media, palacio, multitud en primer plano
class S1D(N.S1):
    def __init__(s):
        super().__init__()
        bg = s.bg.astype(np.float32)
        # cielo (lejano): rellena lo que tapa el palacio con el degradado
        sky = bg.copy(); g = vgrad([(0, (4, 6, 16)), (.45, (16, 16, 34)), (.62, (36, 22, 30)), (1, (36, 22, 30))])
        sky[480:] = g[480:]
        s.back = [(dof(rgba(sky, np.ones((H, W))), 3), .15)]
        # ciudad lejana entre el cielo y el palacio
        city = np.zeros((H, W, 4), np.uint8); r_ = np.random.RandomState(4); x = -20
        while x < W:
            bw, bh = r_.randint(40, 110), r_.randint(60, 260); cv2.rectangle(city, (x, 730 - bh), (x + bw, 760), (40, 30, 46, 255), -1)
            for wy in range(730 - bh + 10, 740, 22):
                for wx in range(x + 6, x + bw - 8, 16):
                    if r_.rand() < .25: cv2.rectangle(city, (wx, wy), (wx + 6, wy + 8), (255, 180, 110, 255), -1)
            x += bw + r_.randint(0, 10)
        s.back.append((dof(haze(city, (36, 24, 40), .45), 2.2), .45))
        # plano principal: palacio + plaza (sin cielo)
        yy, xx = np.mgrid[0:H, 0:W]
        skym = (yy < 714) & ~((xx >= 430) & (xx <= 650) & (yy >= 500)) & ~((abs(xx - 540) < 6) & (yy >= 400))
        s.main = rgba(bg, (~skym).astype(np.float32))
        # primer plano: multitud en silueta + faroles, muy desenfocados
        fg = np.zeros((H, W, 4), np.uint8); r_ = np.random.RandomState(9)
        for i in range(26):
            x = r_.uniform(-40, W + 40); y = r_.uniform(1560, 1720); r = r_.uniform(48, 80)
            cv2.circle(fg, (int(x), int(y - r * 1.6)), int(r * .62), (6, 5, 8, 255), -1, cv2.LINE_AA)
            cv2.ellipse(fg, (int(x), int(y + r * .6)), (int(r * 1.2), int(r * 1.6)), 0, 0, 360, (6, 5, 8, 255), -1, cv2.LINE_AA)
        for x in (60, 1020):
            cv2.line(fg, (x, 1920), (x, 1150), (10, 9, 12, 255), 26, cv2.LINE_AA); cv2.rectangle(fg, (x - 36, 1080), (x + 36, 1160), (255, 190, 110, 255), -1)
        s.front = [(dof(fg, 9), 1.45), (bokeh_layer(10, (255, 170, 90), 3, ymin=900, ymax=1900), 1.7)]
    def cam(s, t, d):
        z, cx, cy, dx, dy = super().cam(t, d); return z, cx, cy, lerp(-45, 45, eIO(t / d)) * ss(1.2, 2.5, t), dy

# ================================================================ 2 · Despacho: pared lejana desenfocada, escritorio, lámpara en primer plano
class S2D(N.S2):
    def __init__(s):
        super().__init__()
        s.back = [(dof(rgba(s.bg, np.ones((H, W))), 2.6), .55)]
        s.main = np.zeros((H, W, 4), np.uint8)
        fg = np.zeros((H, W, 4), np.uint8)
        cv2.ellipse(fg, (110, 1760), (210, 140), 0, 180, 360, (16, 70, 34, 255), -1, cv2.LINE_AA)       # pantalla de lámpara verde
        cv2.line(fg, (110, 1760), (110, 1920), (150, 116, 50, 255), 22, cv2.LINE_AA)
        cv2.ellipse(fg, (110, 1770), (190, 30), 0, 0, 180, (255, 220, 150, 255), -1, cv2.LINE_AA)
        for i in range(5): cv2.rectangle(fg, (860 + i * 8, 1700 - i * 46), (1120, 1740 - i * 46), (70, 120, 70, 255), -1); cv2.rectangle(fg, (960, 1700 - i * 46), (990, 1740 - i * 46), (220, 200, 140, 255), -1)
        s.front = [(dof(fg, 10), 1.5), (bokeh_layer(8, (255, 190, 120), 5, ymin=200, ymax=1200), 1.7)]
    def cam(s, t, d):
        z, cx, cy, dx, dy = super().cam(t, d); return z, cx, cy, lerp(-60, 60, eIO(t / d)), dy

# ================================================================ 3 · Mapa en una mesa táctica inclinada (perspectiva real)
SRCQ = np.float32([(0, 260), (W, 260), (W, H), (0, H)])
DSTQ = np.float32([(250, 470), (830, 470), (W + 330, 1990), (-330, 1990)])
HP = cv2.getPerspectiveTransform(SRCQ, DSTQ)
def hpt(M, p): q = M @ np.array([p[0], p[1], 1.]); return q[:2] / q[2]

class S3D(N.S3):
    def __init__(s):
        super().__init__()
        # sala oscura detrás de la mesa: pared con pantallas desenfocadas
        room = vgrad([(0, (4, 8, 16)), (.3, (8, 18, 30)), (1, (3, 6, 12))]); i8 = to8(room)
        for (x, y, w, h, c) in [(40, 140, 300, 190, (40, 120, 200)), (380, 90, 320, 220, (200, 50, 40)), (740, 140, 300, 190, (40, 120, 200))]:
            cv2.rectangle(i8, (x, y), (x + w, y + h), c, -1); cv2.rectangle(i8, (x, y), (x + w, y + h), (180, 230, 255), 3)
            for k in range(6): cv2.line(i8, (x + 20, y + 30 + k * 26), (x + w - 40 - (k * 37) % 90, y + 30 + k * 26), (230, 240, 255), 3)
        roomf = i8.astype(np.float32); radial(roomf, (540, 200), 500, (60, 120, 200), .25)
        s.back = [(dof(rgba(roomf, np.ones((H, W))), 5), .3)]
        s.front = [(bokeh_layer(6, (120, 200, 255), 8, ymin=1500, ymax=1950, rmin=40, rmax=90), 1.7)]
        s.edge = None
    def draw(s, fr, t, d):  # solo lo que va pegado al mapa (en coordenadas del mapa)
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
        for i, (a, b) in enumerate(s.arrows):
            k = ss(9.2 + i * .25, 10.6 + i * .25, t)
            if k <= 0: continue
            p0, p1 = A(*prj(*a)), A(*prj(*b)); mid = (p0 + p1) / 2 + A(0, -120)
            pts = [tuple((1 - u_) ** 2 * p0 + 2 * (1 - u_) * u_ * mid + u_ ** 2 * p1) for u_ in np.linspace(0, k, 30)]
            pline(fr, pts, (110, 40, 30), 14); pline(fr, pts, (255, 80, 60), 6)
            if k > .98:
                e = A(*pts[-1]); dv = e - A(*pts[-3]); dv /= np.linalg.norm(dv); n = A(-dv[1], dv[0])
                poly(fr, [tuple(e + dv * 22), tuple(e - dv * 10 + n * 16), tuple(e - dv * 10 - n * 16)], (255, 90, 70))
    def floating(s, fr, t, d, P):  # en pantalla: helicópteros con sombra sobre la mesa, hologramas flotando
        hk = ss(11.0, 13.8, t)
        if hk > 0:
            for i, (dx, dy) in enumerate([(0, 0), (130, -70), (130, 70)]):
                wx = lerp(1300, 200, (t - 11.0) / 2.9) + dx * 1.6; wy = lerp(900, 1250, (t - 11.0) / 2.9) + dy * 1.6
                g = hpt(P, (wx, wy)); sc = .55 + .9 * cl(g[1] / H)
                cv2.ellipse(fr, (int(g[0]), int(g[1])), (int(70 * sc), int(18 * sc)), 0, 0, 360, (6, 8, 12), -1, cv2.LINE_AA)
                heli(fr, g[0], g[1] - 230 * sc, 1.7 * sc, t + i, col=(84, 94, 84))
        def floatp(spr, y, a, sc=1.):
            # sombra del holograma proyectada sobre la mesa
            sh = np.zeros_like(spr); sh[:, :, 3] = (spr[:, :, 3] * .55).astype(np.uint8)
            blit(fr, cv2.GaussianBlur(sh, (0, 0), 14), 560, y + 210, a * .8, sc * .95)
            blit(fr, spr, 540, y + math.sin(t * 1.6) * 6, a, sc)
        a = ss(6.4, 7.0, t) * (1 - ss(9.0, 9.3, t))
        if a > 0: floatp(s.panel, 520, a)
        k = ss(9.6, 9.9, t)
        if k > 0: floatp(s.stamp, 520, k, lerp(1.6, 1., eOut(k)))
        s.dust.draw(fr, t)
    def cam(s, t, d):
        k = eIO(t / d); return lerp(1.45, 1.22, eOut(t / 3)) * (1 + .05 * k), 520, 1200, lerp(-50, 50, k), lerp(30, -10, k)

# ================================================================ 4 · Ciudad: rascacielos lejanos con bruma, cercanos, calle, escombros al frente
class S4D(N.S4):
    def __init__(s):
        super().__init__()
        hz = 1250; r_ = np.random.RandomState(21)
        sky = vgrad([(0, (10, 6, 10)), (.5, (40, 16, 14)), (.65, (90, 34, 20)), (1, (90, 34, 20))])
        radial(sky, (540, hz), 700, (255, 110, 40), .35)
        s.back = [(dof(rgba(sky, np.ones((H, W))), 2), .1)]
        def skyline(col, hmin, hmax, lit, seed, ybase):
            lay = np.zeros((H, W, 4), np.uint8); q = np.random.RandomState(seed); x = -40
            while x < W + 40:
                bw = q.randint(60, 150); bh = q.randint(hmin, hmax); cv2.rectangle(lay, (x, ybase - bh), (x + bw, ybase + 30), col + (255,), -1)
                for wy in range(ybase - bh + 18, ybase - 12, 30):
                    for wx in range(x + 10, x + bw - 14, 22):
                        if q.rand() < lit: cv2.rectangle(lay, (wx, wy), (wx + 10, wy + 14), (255, 170, 80, 255) if q.rand() < .8 else (150, 200, 255, 255), -1)
                if q.rand() < .4: cv2.line(lay, (x + bw // 2, ybase - bh), (x + bw // 2, ybase - bh - 70), col + (255,), 3)
                x += bw + q.randint(0, 14)
            return lay
        s.back.append((dof(haze(skyline((40, 26, 30), 300, 760, .12, 2, hz - 30), (110, 46, 30), .55), 3.5), .3))
        s.back.append((dof(haze(skyline((22, 14, 18), 200, 560, .22, 5, hz), (90, 36, 24), .25), 1.5), .6))
        # plano principal: solo calle (el resto lo dan las capas)
        ground = np.zeros((H, W, 4), np.uint8); ground[hz:] = (18, 14, 14, 255)
        for j in range(1, 10):
            y = int(hz + (H - hz) * (j / 9.) ** 1.8); cv2.line(ground, (0, y), (W, y), (34, 26, 28, 255), 2, cv2.LINE_AA)
        for k in range(-10, 11): cv2.line(ground, (540, hz), (540 + k * 240, H), (30, 22, 24, 255), 2, cv2.LINE_AA)
        gf = ground[:, :, :3].astype(np.float32)
        for (x, y, r) in [(220, hz - 40, 300), (760, hz - 20, 360), (520, hz + 20, 220)]: radial(gf, (x, y), r, (255, 110, 30), .45)
        ground[:, :, :3] = to8(gf); s.main = ground
        # primer plano: barricada de sacos y escombros desenfocados + brasas grandes
        fg = np.zeros((H, W, 4), np.uint8)
        for i in range(9):
            x = 40 + i * 70 + r_.uniform(-10, 10); y = 1700 - (i % 2) * 40
            cv2.ellipse(fg, (int(x), int(y)), (60, 30), r_.uniform(-8, 8), 0, 360, (54, 44, 32, 255), -1, cv2.LINE_AA)
            cv2.ellipse(fg, (int(x), int(y - 8)), (54, 20), 0, 180, 360, (84, 70, 50, 255), -1, cv2.LINE_AA)
        for i in range(6):
            pts = np.array([(820 + i * 50 + r_.uniform(-20, 20), 1920), (850 + i * 50, 1620 + r_.uniform(-60, 40)), (900 + i * 50, 1920)], np.int32)
            cv2.fillPoly(fg, [pts], (30, 24, 24, 255), cv2.LINE_AA)
        s.front = [(dof(fg, 8), 1.5), (bokeh_layer(14, (255, 120, 40), 11, rmin=14, rmax=46, ymin=300, ymax=1700), 1.8)]
    def cam(s, t, d):
        z, cx, cy, dx, dy = super().cam(t, d); return z, cx, cy, lerp(-70, 70, eIO(t / d)), dy

# ================================================================ 5 · Globo: pared lejana, globo/balanza, columnas al frente
class S5D(N.S5):
    def __init__(s):
        super().__init__()
        bg = s.bg.astype(np.float32); fl = 1392
        wall = bg.copy(); wall[fl - 40:] = wall[fl - 41]
        s.back = [(dof(rgba(wall, np.ones((H, W))), 3), .35)]
        yy = np.mgrid[0:H, 0:W][0]
        # plano principal: suelo + balanza + base del globo (lo que está por debajo de la línea de pared o es dorado)
        diff = np.abs(bg - wall).sum(2) > 18
        s.main = rgba(bg, ((yy >= fl - 40) | diff).astype(np.float32))
        fg = np.zeros((H, W, 4), np.uint8)
        for x, w in [(-60, 120), (1020, 120)]:
            cv2.rectangle(fg, (x, 0), (x + w, H), (34, 22, 14, 255), -1)
            for k in range(4): cv2.line(fg, (x + 25 + k * 32, 0), (x + 25 + k * 32, H), (60, 40, 24, 255), 6)
        s.front = [(dof(fg, 12), 1.5), (bokeh_layer(10, (255, 200, 120), 6, ymin=200, ymax=1500), 1.7)]
    def cam(s, t, d):
        z, cx, cy, dx, dy = super().cam(t, d); return z, cx, cy, lerp(50, -50, eIO(t / d)), dy

# ---------------------------------------------------------------- render con profundidad
def render3d(sc, t, d, Tg):
    z, cx, cy, dx, dy = sc.cam(t, d)
    dx += math.sin(Tg * .73) * 3.2 + math.sin(Tg * 1.31 + 1) * 1.8; dy += math.sin(Tg * .61 + 2) * 2.6 + math.sin(Tg * 1.17) * 1.4
    ang = math.sin(Tg * .45) * .35
    Ld = lambda dd: M3(1 + (z - 1) * dd, cx, cy, dx * dd, dy * dd, ang * dd)
    M1 = Ld(1.)
    if isinstance(sc, S3D):
        scr = np.zeros((H, W, 3), np.float32)
        for lay, dd in sc.back: comp(scr, warp(lay, Ld(dd)))
        world = sc.bg.copy(); sc.draw(world, t, d)
        P = M1 @ HP
        wl = warp(np.dstack([world, np.full((H, W), 255, np.uint8)]), P, True); comp(scr, wl)
        # borde luminoso de la mesa
        q = np.array([hpt(P, p) for p in SRCQ]); pline_ = np.round(q * 8).astype(np.int32)
        fr = to8(scr); cv2.polylines(fr, [pline_], True, (80, 200, 255), 4, cv2.LINE_AA, 3)
        sc.floating(fr, t, d, P)
    else:
        world = np.zeros((H, W, 3), np.float32); Mi = np.linalg.inv(M1)
        for lay, dd in sc.back: comp(world, warp(lay, Mi @ Ld(dd)))
        comp(world, sc.main); world = to8(world); sc.draw(world, t, d)
        fr = cv2.warpAffine(world, M1[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    fr = fr.astype(np.float32)
    for lay, dd in sc.front: comp(fr, warp(lay, Ld(dd)))
    return to8(fr)
N.render_scene = render3d

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    objs = [S1D(), S2D(), S3D(), S4D(), S5D()]
    scenes = [(SC_T[i], SC_T[i + 1], objs[i]) for i in range(5)]
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in SUBS]; emos = [e + (emoji_sprite(e[2]),) for e in EMOJIS]
    title = objs[0].title
    def frame(T):
        idx = max(i for i, (a, b, _) in enumerate(scenes) if T >= a - 1e-6)
        a, b, sc = scenes[idx]; fr = cinema(render3d(sc, T - a, b - a, T), idx, T)
        if idx > 0 and T - a < .45:
            pa, pb, ps = scenes[idx - 1]; prev = cinema(render3d(ps, T - pa, pb - pa, T), idx - 1, T); k = ss(0, .45, T - a)
            fr = cv2.addWeighted(prev, 1 - k, fr, k, 0)
        k = ss(5.9, 6.4, T) * (1 - ss(8.5, 8.9, T))
        if k > 0: blit(fr, title, 540, 1265, k * (.9 + .1 * math.sin(T * 6)), lerp(1.3, 1, eOut((T - 5.9) / .5)))
        draw_overlays(fr, T, subs, emos); return fr
    if mode == 'test':
        for T in [float(x) for x in sys.argv[2:]]:
            fr = frame(T); cv2.imwrite(f'{OUT}/d_{T:05.1f}.jpg', cv2.resize(fr, (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    if mode == 'clip':  # clip de prueba: tramos de cada escena
        out = sys.argv[2]; spans = [(float(a), float(b)) for a, b in (x.split(':') for x in sys.argv[3:])]
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for a, b in spans:
            for i in range(int(a * FPS), int(b * FPS)): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('clip ok', out); return
    if mode == 'seg':
        f0, f1 = int(sys.argv[2]), int(sys.argv[3])
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', f'{OUT}/d_seg_{f0:04d}.mp4']
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(f0, f1): p.stdin.write(np.ascontiguousarray(frame(i / FPS)).tobytes())
        p.stdin.close(); p.wait(); print('SEG', f0, f1, flush=True); return

if __name__ == '__main__': main()
