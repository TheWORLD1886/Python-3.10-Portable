#!/usr/bin/env python3
# Short: ¿Qué pasaría si México tuviera por primera vez una bomba nuclear? (60 s, 1080x1920)
import numpy as np, cv2, math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.signal import butter, lfilter
from scipy.io import wavfile

W, H, FPS, DUR = 1080, 1920, 30, 60
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out'); os.makedirs(OUT, exist_ok=True)
rng = np.random.RandomState(11)
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
EMO = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
_fc = {}
def font(px, path=FB):
    k = (px, path)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, px)
    return _fc[k]

def cl(x, a=0., b=1.): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def ss(a, b, x):
    t = cl((x - a) / (b - a)); return t * t * (3 - 2 * t)
def eOut(t): t = cl(t); return 1 - (1 - t) ** 3
def eExpo(t): t = cl(t); return 1. if t >= 1 else 1 - 2 ** (-10 * t)
def eIO(t): t = cl(t); return t * t * (3 - 2 * t)
def eBack(t):
    t = cl(t); c = 1.70158; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def to8(img): return np.clip(img, 0, 255).astype(np.uint8)
def A(*p): return np.array(p, dtype=np.float64)

# ---------------------------------------------------------------- dibujo base
def vgrad(stops, w=W, h=H):
    ys = np.linspace(0, 1, h); xs = [s[0] for s in stops]
    out = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        out[:, :, c] = np.interp(ys, xs, [s[1][c] for s in stops])[:, None]
    return out

def vignette(img, strength=.6):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2)
    v = 1 - strength * np.clip(d - .35, 0, 1) ** 1.4 * 1.5
    return img * np.clip(v, .2, 1)[:, :, None]

def bloom(img, thr=175, sig=22, k=1.1):
    b = np.clip(img - thr, 0, None)
    return img + cv2.GaussianBlur(b, (0, 0), sig) * k

def beam(img, p0, p1, r0, r1, color, alpha, blur=28):
    lay = np.zeros((H, W, 3), np.float32)
    p0 = A(*p0); p1 = A(*p1); d = p1 - p0; n = A(-d[1], d[0]); n /= np.linalg.norm(n)
    pts = np.array([p0 + n * r0, p0 - n * r0, p1 - n * r1, p1 + n * r1]).astype(np.int32)
    cv2.fillPoly(lay, [pts], color)
    img += cv2.GaussianBlur(lay, (0, 0), blur) * alpha

def radial(img, c, r, color, k):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - c[0]) ** 2 + (yy - c[1]) ** 2) / r
    img += (np.clip(1 - d, 0, 1) ** 2)[:, :, None] * np.array(color, np.float32) * k

def P8(p): return (int(round(p[0] * 8)), int(round(p[1] * 8)))
def line(fr, a, b, col, th): cv2.line(fr, P8(a), P8(b), col, max(1, int(round(th))), cv2.LINE_AA, 3)
def circ(fr, c, r, col, th=-1): cv2.circle(fr, P8(c), max(1, int(round(r * 8))), col, th, cv2.LINE_AA, 3)
def poly(fr, pts, col): cv2.fillPoly(fr, [np.round(np.array(pts) * 8).astype(np.int32)], col, cv2.LINE_AA, 3)
def pline(fr, pts, col, th, closed=False):
    cv2.polylines(fr, [np.round(np.array(pts) * 8).astype(np.int32)], closed, col, max(1, int(th)), cv2.LINE_AA, 3)

def blit(fr, spr, cx, cy, op=1., sc=1., add=False):
    if op <= .004: return
    if abs(sc - 1.) > 1e-3:
        nw = max(1, int(spr.shape[1] * sc)); nh = max(1, int(spr.shape[0] * sc))
        spr = cv2.resize(spr, (nw, nh), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR)
    h, w = spr.shape[:2]; x0 = int(round(cx - w / 2)); y0 = int(round(cy - h / 2))
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(fr.shape[1], x0 + w), min(fr.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    s = spr[ya - y0:yb - y0, xa - x0:xb - x0]; roi = fr[ya:yb, xa:xb]
    a = s[:, :, 3:4].astype(np.float32) * (op / 255.)
    if add: roi[:] = np.clip(roi + s[:, :, :3] * a, 0, 255)
    else: roi[:] = roi * (1 - a) + s[:, :, :3] * a

def over(dst, src, cx, cy):
    h, w = src.shape[:2]; x0 = int(cx - w / 2); y0 = int(cy - h / 2)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(dst.shape[1], x0 + w), min(dst.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    s = src[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); d = dst[ya:yb, xa:xb].astype(np.float32)
    sa = s[:, :, 3:4] / 255.; da = d[:, :, 3:4] / 255.; oa = sa + da * (1 - sa)
    rgb = (s[:, :, :3] * sa + d[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-4)
    dst[ya:yb, xa:xb, :3] = np.clip(rgb, 0, 255); dst[ya:yb, xa:xb, 3:4] = np.clip(oa * 255, 0, 255)

def glow_sprite(r, color):
    s = 2 * r + 1; yy, xx = np.mgrid[0:s, 0:s]; d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 2
    spr = np.zeros((s, s, 4), np.uint8); spr[:, :, :3] = color; spr[:, :, 3] = (a * 255).astype(np.uint8)
    return spr

_md = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
def text_w(txt, px, spacing=0, path=FB):
    f = font(px, path)
    if spacing: return sum(_md.textlength(ch, font=f) + spacing for ch in txt) - spacing
    return _md.textlength(txt, font=f)
def fit_px(txt, px, maxw, spacing=0, path=FB):
    while px > 12 and text_w(txt, px, spacing, path) > maxw: px -= 2
    return px
def text_sprite(txt, px, color, stroke=0, stroke_col=(0, 0, 0), glow=None, glow_r=12, spacing=0, pad=44, path=FB, maxw=None):
    if maxw: px = fit_px(txt, px, maxw, spacing, path)
    f = font(px, path); w = text_w(txt, px, spacing, path); asc, desc = f.getmetrics()
    im = Image.new('RGBA', (int(w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = pad
    if spacing:
        for ch in txt:
            d.text((x, pad), ch, font=f, fill=color, stroke_width=stroke, stroke_fill=stroke_col)
            x += d.textlength(ch, font=f) + spacing
    else:
        d.text((pad, pad), txt, font=f, fill=color, stroke_width=stroke, stroke_fill=stroke_col)
    if glow:
        a = im.split()[3].filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, int(v * 1.5)))
        g = Image.new('RGBA', im.size, tuple(glow) + (0,)); g.putalpha(a)
        im = Image.alpha_composite(g, im)
    return np.array(im)

# ---------------------------------------------------------------- subtítulos y emojis
def sub_sprite(chunk, px=78, maxw=820):
    words = []; cur = []; key = False; buf = ''
    for ch in chunk:
        if ch == '*':
            if buf: cur.append((buf, key)); buf = ''
            key = not key
        elif ch == ' ':
            if buf: cur.append((buf, key)); buf = ''
            if cur: words.append(cur); cur = []
        else: buf += ch
    if buf: cur.append((buf, key))
    if cur: words.append(cur)
    def ww(wd, f): return sum(_md.textlength(fr, font=f) for fr, _ in wd)
    def lw(ws, f):
        sp = _md.textlength(' ', font=f); return sum(ww(w, f) for w in ws) + sp * (len(ws) - 1)
    f = font(px); lines = [words]
    if lw(words, f) > maxw and len(words) > 1:
        best = None
        for i in range(1, len(words)):
            m = max(lw(words[:i], f), lw(words[i:], f))
            if best is None or m < best[0]: best = (m, i)
        lines = [words[:best[1]], words[best[1]:]]
    while px > 40 and max(lw(l, font(px)) for l in lines) > maxw: px -= 2
    f = font(px); sw = max(6, int(px * .12)); lh = int(px * 1.16); pad = 40
    im = Image.new('RGBA', (maxw + 2 * pad, lh * len(lines) + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sp = d.textlength(' ', font=f)
    for stroke in (True, False):
        for li, ws in enumerate(lines):
            x = (im.size[0] - lw(ws, f)) / 2; y = pad + li * lh
            for wd in ws:
                for frag, k in wd:
                    col = (255, 210, 31, 255) if k else (255, 255, 255, 255)
                    if stroke: d.text((x, y), frag, font=f, fill=(0, 0, 0, 255), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
                    else: d.text((x, y), frag, font=f, fill=col)
                    x += d.textlength(frag, font=f)
                x += sp
    sh = im.split()[3].filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * .7))
    s = Image.new('RGBA', im.size, (0, 0, 0, 0)); s.putalpha(sh)
    base = Image.new('RGBA', im.size, (0, 0, 0, 0)); base.paste(s, (0, 7), s)
    return np.array(Image.alpha_composite(base, im))



EMOJIS = [
 (.9, 3.6, '🇲🇽', 880, 520, 165, 'pop'), (1.2, 9.8, '☢️', 220, 400, 185, 'late'), (7.9, 10.25, '💥', 860, 800, 195, 'sacude'),
 (11.4, 15.0, '📜', 215, 1150, 160, 'flota'), (12.0, 16.0, '❌', 860, 880, 155, 'sacude'), (16.1, 18.6, '🕊️', 860, 880, 165, 'flota'), (20.2, 23.6, '⚠️', 860, 880, 170, 'late'),
 (26.9, 30.5, '🇺🇸', 170, 1330, 165, 'pop'), (30.7, 33.2, '🚫', 910, 1330, 160, 'sacude'), (34.6, 37.1, '💸', 180, 735, 160, 'flota'), (35.7, 37.1, '📉', 900, 735, 160, 'cae'),
 (38.3, 43.9, '📉', 900, 1480, 140, 'sacude'), (42.3, 44.2, '💰', 680, 1480, 140, 'late'), (44.4, 48.5, '🏥', 680, 1480, 140, 'pop'), (44.9, 48.5, '🚓', 900, 1480, 140, 'pop'),
 (53.2, 56.6, '🕊️', 230, 560, 175, 'flota'), (53.4, 54.95, '🤝', 870, 1250, 165, 'pop'), (55.0, 57.7, '💬', 870, 1250, 165, 'late'), (57.9, 60, '🔔', 870, 1250, 175, 'sacude'), (57.9, 60, '👍', 230, 560, 165, 'pop'),
]
def emoji_sprite(e):
    f = font(109, EMO); im = Image.new('RGBA', (220, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((20, 15), e, font=f, embedded_color=True)
    im = im.crop(im.getbbox()); s = max(im.size) + 8
    sq = Image.new('RGBA', (s, s), (0, 0, 0, 0)); sq.paste(im, ((s - im.size[0]) // 2, (s - im.size[1]) // 2))
    return np.array(sq)

def draw_overlays(fr, T, subs, emos):
    for t0, t1, e, x, y, tam, anim, spr in emos:
        if t0 <= T < t1:
            lt = T - t0; sc = eBack(lt / .28) * tam / spr.shape[0]; op = cl((t1 - T) / .2); dx = dy = 0
            if anim == 'flota': dy = math.sin(lt * 2.4) * 14
            elif anim == 'sacude': dx = math.sin(lt * 26) * 9 * (1 if lt < 1.2 else .35)
            elif anim == 'late': sc *= 1 + .08 * math.sin(lt * 7)
            elif anim == 'cae': dy = -160 * (1 - eOut(lt / .5)) + 60 * ss(.6, 2.2, lt)
            blit(fr, spr, x + dx, y + dy, op, sc)
    for t0, t1, y, spr in subs:
        if t0 <= T < t1:
            lt = T - t0
            blit(fr, spr, 530, y, cl(lt / .07), lerp(.84, 1, eBack(lt / .16)))


# ---------------------------------------------------------------- personaje
OUTF = {'militar': dict(top=(92, 104, 64), pants=(72, 82, 52), shoe=(26, 26, 26)),
        'traje': dict(top=(34, 38, 60), pants=(28, 31, 48), shoe=(14, 14, 18)),
        'bata': dict(top=(236, 239, 244), pants=(54, 58, 70), shoe=(20, 20, 24)),
        'elegante': dict(top=(40, 78, 178), pants=(24, 28, 48), shoe=(14, 14, 18)),
        'reo': dict(top=(240, 112, 28), pants=(228, 100, 24), shoe=(36, 36, 40)),
        'civil': dict(top=(128, 34, 40), pants=(52, 84, 146), shoe=(70, 46, 30)),
        'comando': dict(top=(26, 28, 32), pants=(22, 24, 28), shoe=(10, 10, 12)),
        'juez': dict(top=(22, 22, 28), pants=(22, 22, 28), shoe=(12, 12, 14))}
SKIN = (246, 244, 240)
def dark(c, k=.6): return tuple(int(v * k) for v in c)

def character(fr, kind, x, fy, hgt, t, armR=('reposo',), armL=('reposo',), look=(0., 0.), frown=.3, beret=False, smile=0., sash=False, mustache=False, run=0., cuffs=False, cap=False, mask=False):
    hands = {}
    u = hgt / 8.; o = OUTF[kind]; br = math.sin(t * 2.2) * u * .05
    hipy = fy - 3.3 * u; shy = fy - 5.75 * u + br
    head = A(x + look[0] * u * .12, fy - 6.95 * u + br)
    lw = u * .5
    for sd in (-1, 1):
        hp = A(x + sd * .42 * u, hipy); ft = A(x + sd * .58 * u, fy - .25 * u)
        pc_ = o['pants']; lwp = lw * (1.25 if kind == 'civil' else 1.)
        if run:  # pierna en dos tramos: muslo y espinilla, la rodilla se dobla al correr
            ph_ = t * run + (sd > 0) * math.pi; th = math.sin(ph_) * .6; bend = max(0., -math.cos(ph_)) * 1.1 + .15
            dirn = -1 if look[0] < 0 else 1; kn_ = hp + A(math.sin(th), math.cos(th)) * 1.55 * u; sa = th - bend * dirn
            ft = kn_ + A(math.sin(sa), math.cos(sa)) * 1.55 * u
            segs = [(hp, kn_), (kn_, ft)]
        else:
            kn_ = (hp + ft) / 2; segs = [(hp, ft)]
        for a_, b_ in segs: line(fr, a_, b_, dark(pc_, .7), lwp + 4)
        for a_, b_ in segs: line(fr, a_, b_, pc_, lwp)
        if run: circ(fr, kn_, lwp / 2, pc_)
        if kind == 'civil':  # mezclilla: costura clara y bastilla doblada
            for a_, b_ in segs: line(fr, A(*a_) + A(sd * .12 * u, 0), A(*b_) + A(sd * .12 * u, 0), (120, 150, 200), 2)
            dv = A(*segs[-1][1]) - A(*segs[-1][0]); dv /= max(1e-6, np.linalg.norm(dv)); hb = A(*ft) - dv * .35 * u
            line(fr, hb, A(*ft) - dv * .12 * u, (40, 66, 118), lwp)
        cv2.ellipse(fr, P8(ft + A(sd * .16 * u, .08 * u)), (int(.46 * u * 8), int(.24 * u * 8)), 0, 0, 360, o['shoe'], -1, cv2.LINE_AA, 3)
    top = o['top']; ta = A(x, shy + .55 * u); tb = A(x, hipy)
    if kind == 'bata':
        kn = hipy + 1.55 * u
        poly(fr, [(x - .95 * u, hipy - .3 * u), (x + .95 * u, hipy - .3 * u), (x + 1.02 * u, kn), (x - 1.02 * u, kn)], dark(top, .72))
        poly(fr, [(x - .9 * u, hipy - .3 * u), (x + .9 * u, hipy - .3 * u), (x + .97 * u, kn - 3), (x - .97 * u, kn - 3)], top)
    line(fr, ta, tb, dark(top, .62), 1.78 * u + 5); line(fr, ta, tb, top, 1.78 * u)
    if kind == 'traje':
        poly(fr, [(x - .34 * u, shy - .22 * u), (x + .34 * u, shy - .22 * u), (x, shy + 1.25 * u)], (240, 240, 244))
        poly(fr, [(x - .1 * u, shy - .1 * u), (x + .1 * u, shy - .1 * u), (x + .14 * u, shy + .95 * u), (x, shy + 1.2 * u), (x - .14 * u, shy + .95 * u)], (190, 32, 36))
        if sash:  # banda presidencial tricolor
            for k, c in enumerate([(0, 120, 72), (245, 245, 245), (206, 24, 40)]):
                o_ = (k - 1) * .2 * u
                line(fr, (x - .78 * u + o_, shy + .05 * u), (x + .72 * u + o_, hipy - .1 * u), c, .2 * u)
            circ(fr, (x + .7 * u, hipy - .12 * u), .2 * u, (232, 190, 80)); circ(fr, (x + .7 * u, hipy - .12 * u), .12 * u, (150, 110, 40))
    elif kind == 'militar':
        for (ex, ey, ea, eb) in [(-.45, .9, .3, .2), (.4, 1.5, .34, .18), (-.2, 2.0, .3, .16), (.5, .6, .22, .14)]:
            cv2.ellipse(fr, P8((x + ex * u, shy + ey * u)), (int(ea * u * 8), int(eb * u * 8)), 20, 0, 360, (62, 74, 44), -1, cv2.LINE_AA, 3)
        line(fr, (x, shy + .75 * u), (x, shy + 1.55 * u), (58, 66, 42), 1.3 * u)
        for sd in (-1, 1):
            cv2.rectangle(fr, (int(x + sd * .36 * u - .2 * u), int(shy + .95 * u)), (int(x + sd * .36 * u + .2 * u), int(shy + 1.4 * u)), (46, 54, 34), -1)
        line(fr, (x - .78 * u, hipy - .12 * u), (x + .78 * u, hipy - .12 * u), (34, 34, 26), .24 * u)
        cv2.rectangle(fr, (int(x - .14 * u), int(hipy - .26 * u)), (int(x + .14 * u), int(hipy + .02 * u)), (190, 160, 70), -1)
    elif kind == 'bata':
        poly(fr, [(x - .3 * u, shy - .22 * u), (x + .3 * u, shy - .22 * u), (x, shy + 1.0 * u)], (96, 150, 210))
        line(fr, (x - .32 * u, shy - .2 * u), (x, shy + 1.05 * u), (170, 176, 188), 3); line(fr, (x + .32 * u, shy - .2 * u), (x, shy + 1.05 * u), (170, 176, 188), 3)
        line(fr, (x, shy + 1.05 * u), (x, hipy + 1.5 * u), (176, 182, 194), 3)
        for i in range(3): circ(fr, (x + .12 * u, shy + (1.4 + i * .55) * u), .06 * u, (150, 156, 170))
        cv2.rectangle(fr, (int(x + .3 * u), int(shy + .9 * u)), (int(x + .68 * u), int(shy + 1.3 * u)), (200, 206, 216), 2)
        line(fr, (x + .42 * u, shy + .78 * u), (x + .42 * u, shy + 1.0 * u), (40, 90, 200), .08 * u)
    elif kind == 'reo':
        poly(fr, [(x - .3 * u, shy - .22 * u), (x + .3 * u, shy - .22 * u), (x, shy + .55 * u)], dark(top, .75))
        cv2.rectangle(fr, (int(x - .62 * u), int(shy + .75 * u)), (int(x - .1 * u), int(shy + 1.1 * u)), (245, 245, 245), -1)
        for k in range(3): line(fr, (x - .56 * u, shy + (.82 + k * .1) * u), (x - .16 * u, shy + (.82 + k * .1) * u), (40, 40, 40), 2)
        line(fr, (x, shy + .55 * u), (x, hipy), dark(top, .7), 3)
    elif kind == 'civil':
        x0_, y0_ = int(x - 1.1 * u), int(shy - .6 * u); x1_, y1_ = int(x + 1.1 * u), int(hipy + 1.2 * u)
        x0_, y0_ = max(0, x0_), max(0, y0_); x1_, y1_ = min(fr.shape[1], x1_), min(fr.shape[0], y1_)
        if x1_ > x0_ and y1_ > y0_:
            mk = np.zeros((y1_ - y0_, x1_ - x0_), np.uint8)
            cv2.line(mk, (int(ta[0] - x0_), int(ta[1] - y0_)), (int(tb[0] - x0_), int(tb[1] - y0_)), 255, max(1, int(1.78 * u)), cv2.LINE_AA)
            m_ = (mk.astype(np.float32) / 255.)[:, :, None]
            yy_, xx_ = np.mgrid[y0_:y1_, x0_:x1_].astype(np.float32); per = .62 * u
            band = ((((xx_ - x) % per) < .2 * u) | (((yy_ - shy) % per) < .2 * u)).astype(np.float32)
            both = ((((xx_ - x) % per) < .2 * u) & (((yy_ - shy) % per) < .2 * u)).astype(np.float32)
            thin = ((np.abs(((xx_ - x + per * .5) % per) - per * .5) < 1.2) | (np.abs(((yy_ - shy + per * .5) % per) - per * .5) < 1.2)).astype(np.float32)
            pat = np.ones_like(xx_)[:, :, None] * np.array(top, np.float32)
            pat = pat * (1 - .32 * band[:, :, None]) * (1 - .25 * both[:, :, None])
            pat = pat * (1 - .45 * thin[:, :, None]) + np.array([214, 196, 168], np.float32) * .45 * thin[:, :, None]
            roi = fr[y0_:y1_, x0_:x1_].astype(np.float32); fr[y0_:y1_, x0_:x1_] = to8(roi * (1 - m_) + pat * m_)
        poly(fr, [(x - .34 * u, shy - .24 * u), (x, shy + .18 * u), (x - .14 * u, shy + .32 * u), (x - .42 * u, shy - .05 * u)], dark(top, .55))   # cuello
        poly(fr, [(x + .34 * u, shy - .24 * u), (x, shy + .18 * u), (x + .14 * u, shy + .32 * u), (x + .42 * u, shy - .05 * u)], dark(top, .55))
        cv2.rectangle(fr, (int(x - .62 * u), int(shy + .7 * u)), (int(x - .22 * u), int(shy + 1.12 * u)), dark(top, .7), 2)        # bolsillo
        cv2.ellipse(fr, P8((x, hipy + .1 * u)), (int(.92 * u * 8), int(.82 * u * 8)), 0, 0, 180, (52, 84, 146), -1, cv2.LINE_AA, 3)
        poly(fr, [(x - .92 * u, hipy - .3 * u), (x + .92 * u, hipy - .3 * u), (x + .92 * u, hipy + .12 * u), (x - .92 * u, hipy + .12 * u)], (52, 84, 146))
        line(fr, (x, hipy - .1 * u), (x, hipy + .6 * u), (40, 66, 118), 3)
        for sd2 in (-1, 1): line(fr, (x + sd2 * .5 * u, hipy - .1 * u), (x + sd2 * .3 * u, hipy + .3 * u), (120, 150, 200), 2)
        line(fr, (x - .92 * u, hipy - .26 * u), (x + .92 * u, hipy - .26 * u), (70, 44, 26), .22 * u)
        cv2.rectangle(fr, (int(x - .15 * u), int(hipy - .38 * u)), (int(x + .15 * u), int(hipy - .14 * u)), (210, 180, 96), -1)
        line(fr, (x, shy + .3 * u), (x, hipy - .4 * u), dark(top, .5), 2)
        for i in range(4): circ(fr, (x + .07 * u, shy + (.55 + i * .45) * u), .05 * u, (236, 230, 220))
    elif kind == 'juez':
        poly(fr, [(x - 1.05 * u, shy + .1 * u), (x + 1.05 * u, shy + .1 * u), (x + 1.25 * u, hipy + 1.8 * u), (x - 1.25 * u, hipy + 1.8 * u)], (22, 22, 28))
        poly(fr, [(x - .28 * u, shy - .2 * u), (x + .28 * u, shy - .2 * u), (x + .12 * u, shy + .55 * u), (x - .12 * u, shy + .55 * u)], (240, 240, 244))
        line(fr, (x, shy + .55 * u), (x, hipy + 1.6 * u), (40, 40, 48), 2)
    elif kind == 'comando':
        cv2.rectangle(fr, (int(x - .78 * u), int(shy + .35 * u)), (int(x + .78 * u), int(hipy - .2 * u)), (44, 48, 40), -1)      # chaleco
        for k in range(3): cv2.rectangle(fr, (int(x - .62 * u + k * .44 * u), int(shy + 1.3 * u)), (int(x - .3 * u + k * .44 * u), int(shy + 1.8 * u)), (34, 38, 30), -1)
        line(fr, (x - .8 * u, hipy - .12 * u), (x + .8 * u, hipy - .12 * u), (16, 16, 18), .22 * u)
    elif kind == 'elegante':
        poly(fr, [(x - .3 * u, shy - .22 * u), (x + .3 * u, shy - .22 * u), (x, shy + .7 * u)], (240, 240, 244))
        line(fr, (x, shy + .7 * u), (x, hipy + .2 * u), (232, 190, 80), 3)
        for i in range(3):
            for sd in (-1, 1): circ(fr, (x + sd * .3 * u, shy + (1.0 + i * .5) * u), .09 * u, (240, 198, 84))
    def arm(sd, pose):
        S = A(x + sd * .86 * u, shy + .38 * u)
        re = S + A(sd * .3 * u, 1.3 * u); rh = re + A(sd * .08 * u, 1.25 * u)
        if pose[0] == 'jarra': e = S + A(sd * 1.15 * u, 1.05 * u); hd = A(x + sd * .9 * u, hipy - .15 * u)
        elif pose[0] == 'palma': e = S + A(sd * .95 * u, .75 * u); hd = e + A(sd * .45 * u, -1.15 * u)
        elif pose[0] == 'apunta':
            d = A(*pose[1]) - S; d /= max(1e-6, np.linalg.norm(d)); k = pose[2]
            e = lerp(re, S + d * 1.35 * u, k); hd = lerp(rh, S + d * 2.65 * u, k)
        else: e, hd = re, rh
        dk = dark(top, .62)
        line(fr, S, e, dk, lw + 5); line(fr, e, hd, dk, lw + 4)
        line(fr, S, e, top, lw); line(fr, e, hd, top, lw * .92)
        circ(fr, hd, .31 * u, (170, 172, 182)); circ(fr, hd, .27 * u, SKIN); hands[sd] = (hd, e)
    arm(-1, armL); arm(1, armR)
    if cuffs:  # esposas en las muñecas reales + cadena entre ellas
        wr = {}
        for sd in (-1, 1):
            hd, e = hands[sd]; dv = A(*hd) - A(*e); dv /= max(1e-6, np.linalg.norm(dv)); w_ = A(*hd) - dv * .3 * u; wr[sd] = w_
            cv2.ellipse(fr, P8(w_), (int(.24 * u * 8), int(.13 * u * 8)), math.degrees(math.atan2(dv[1], dv[0])) + 90, 0, 360, (70, 74, 84), max(3, int(.09 * u)), cv2.LINE_AA, 3)
            cv2.ellipse(fr, P8(w_), (int(.24 * u * 8), int(.13 * u * 8)), math.degrees(math.atan2(dv[1], dv[0])) + 90, 0, 360, (200, 206, 216), max(2, int(.05 * u)), cv2.LINE_AA, 3)
        a_, b_ = wr[-1], wr[1]; n_ = 5
        for k in range(n_):
            p = a_ + (b_ - a_) * (k + .5) / n_ + A(0, math.sin((k + .5) / n_ * math.pi) * .12 * u)
            cv2.ellipse(fr, P8(p), (int(.08 * u * 8), int(.05 * u * 8)), (k % 2) * 90, 0, 360, (190, 196, 206), max(2, int(.035 * u)), cv2.LINE_AA, 3)
    line(fr, (x, shy - .1 * u), head, (214, 214, 222), .34 * u)
    circ(fr, head, 1.0 * u, (150, 154, 170)); circ(fr, head, .96 * u, (204, 206, 218))
    circ(fr, head + A(-.05 * u, -.06 * u), .9 * u, SKIN)
    fc = head + A(look[0] * .34 * u, look[1] * .3 * u)
    for sd in (-1, 1):
        cv2.ellipse(fr, P8(fc + A(sd * .34 * u, -.05 * u)), (int(.1 * u * 8), int(.165 * u * 8)), 0, 0, 360, (18, 18, 24), -1, cv2.LINE_AA, 3)
        line(fr, fc + A(sd * .54 * u, -.44 * u), fc + A(sd * .16 * u, -.38 * u + frown * .24 * u), (18, 18, 24), .09 * u)
    if smile > 0: cv2.ellipse(fr, P8(fc + A(0, .36 * u)), (int(.26 * u * 8), int(.17 * u * smile * 8)), 0, 0, 180, (18, 18, 24), max(2, int(.08 * u)), cv2.LINE_AA, 3)
    else: line(fr, fc + A(-.2 * u, .46 * u), fc + A(.2 * u, .46 * u), (18, 18, 24), .08 * u)
    if mustache:
        mc = fc + A(0, .2 * u)
        poly(fr, [(mc[0] - .42 * u, mc[1] + .1 * u), (mc[0] - .2 * u, mc[1] - .1 * u), (mc[0], mc[1] - .05 * u), (mc[0] + .2 * u, mc[1] - .1 * u), (mc[0] + .42 * u, mc[1] + .1 * u), (mc[0], mc[1] + .04 * u)], (24, 18, 14))
        cv2.ellipse(fr, P8(head + A(-.05 * u, -.55 * u)), (int(.92 * u * 8), int(.48 * u * 8)), 0, 180, 360, (24, 18, 14), -1, cv2.LINE_AA, 3)
    if cap:  # gorra de béisbol puesta de lado (visera hacia la derecha), arriba de las cejas
        cc_ = (36, 40, 50); cy_ = head[1] - .5 * u
        cv2.ellipse(fr, P8((head[0], cy_)), (int(.98 * u * 8), int(.62 * u * 8)), 0, 180, 360, cc_, -1, cv2.LINE_AA, 3)
        poly(fr, [(head[0] - .98 * u, cy_), (head[0] + .98 * u, cy_), (head[0] + .94 * u, cy_ + .1 * u), (head[0] - .94 * u, cy_ + .1 * u)], (26, 28, 36))
        poly(fr, [(head[0] + .7 * u, cy_ - .04 * u), (head[0] + 1.62 * u, cy_ - .02 * u), (head[0] + 1.7 * u, cy_ + .1 * u), (head[0] + .8 * u, cy_ + .14 * u)], (22, 24, 30))  # visera de lado
        line(fr, (head[0], cy_ - .6 * u), (head[0], cy_), (54, 58, 68), 2)
        circ(fr, (head[0], cy_ - .62 * u), .09 * u, (54, 58, 68))
        pc = A(head[0] - .3 * u, cy_ - .3 * u); r_ = .2 * u
        poly(fr, [(pc[0] - r_, pc[1] - r_ * .75), (pc[0] + r_, pc[1] - r_ * .75), (pc[0], pc[1] + r_ * .85)], (250, 200, 70))       # pizza
        line(fr, (pc[0] - r_ * 1.05, pc[1] - r_ * .8), (pc[0] + r_ * 1.05, pc[1] - r_ * .8), (190, 120, 50), .1 * u)
        for (ox, oy) in [(-.07, -.06), (.07, -.06), (0, .06)]: circ(fr, pc + A(ox * u, oy * u), .045 * u, (200, 40, 40))
    if mask:  # pasamontañas negro con abertura en los ojos
        circ(fr, head, .97 * u, (16, 16, 18))
        cv2.ellipse(fr, P8(fc + A(0, -.05 * u)), (int(.62 * u * 8), int(.22 * u * 8)), 0, 0, 360, SKIN, -1, cv2.LINE_AA, 3)
        for sd in (-1, 1): cv2.ellipse(fr, P8(fc + A(sd * .3 * u, -.05 * u)), (int(.09 * u * 8), int(.13 * u * 8)), 0, 0, 360, (18, 18, 24), -1, cv2.LINE_AA, 3)
    if beret:
        cv2.ellipse(fr, P8(head + A(-.1 * u, -.74 * u)), (int(1.08 * u * 8), int(.44 * u * 8)), -12, 0, 360, (40, 66, 44), -1, cv2.LINE_AA, 3)
        cv2.ellipse(fr, P8(head + A(.05 * u, -.52 * u)), (int(.98 * u * 8), int(.16 * u * 8)), -6, 0, 360, (26, 44, 30), -1, cv2.LINE_AA, 3)
        circ(fr, head + A(.5 * u, -.84 * u), .13 * u, (220, 180, 70))
    return hands

def rifle(fr, hands, u, mag=True):
    # fusil de asalto estilizado sostenido con las dos manos (culata atrás, cañón hacia la mano delantera)
    (hR, eR), (hL, eL) = hands[1], hands[-1]; hR, hL = A(*hR), A(*hL)
    v = hR - hL; L_ = np.linalg.norm(v)
    if L_ < 1e-3: return
    v /= L_; n = A(-v[1], v[0])
    if n[1] < 0: n = -n                                      # n apunta hacia abajo
    gun, dk = (64, 68, 64), (30, 32, 30)
    def q(p0, p1, w0, w1, col):
        poly(fr, [tuple(p0 - n * w0), tuple(p1 - n * w1), tuple(p1 + n * w1), tuple(p0 + n * w0)], col)
    q(hL - v * .9 * u, hL - v * .1 * u, .26 * u, .16 * u, dk)                  # culata
    q(hL - v * .15 * u, hR + v * .25 * u, .17 * u, .15 * u, gun)               # cuerpo
    q(hR + v * .2 * u, hR + v * 1.5 * u, .06 * u, .06 * u, dk)                 # cañón
    line(fr, hL - v * .1 * u - n * .12 * u, hR + v * .2 * u - n * .1 * u, (110, 116, 110), 2)
    q(hL + v * .25 * u - n * .2 * u, hL + v * .75 * u - n * .2 * u, .07 * u, .07 * u, dk)  # mira
    if mag:
        m0 = hL + v * .45 * u; poly(fr, [tuple(m0), tuple(m0 + v * .3 * u), tuple(m0 + v * .42 * u + n * .7 * u), tuple(m0 + v * .12 * u + n * .75 * u)], dk)
    circ(fr, hL, .27 * u, SKIN); circ(fr, hR, .27 * u, SKIN)                  # manos encima del arma

class Dust:
    def __init__(s, n, box, color, r=5, op=.5):
        s.p = rng.uniform(0, 1, (n, 4)); s.box = box; s.spr = glow_sprite(r, color); s.op = op
    def draw(s, fr, t):
        x0, y0, x1, y1 = s.box
        for a, b, c, d in s.p:
            x = x0 + ((a + t * .012 * (c - .3)) % 1) * (x1 - x0); y = y0 + ((b - t * .01 * (d + .3)) % 1) * (y1 - y0)
            blit(fr, s.spr, x + math.sin(t * .8 + a * 20) * 8, y, s.op * (.4 + .6 * abs(math.sin(t * .7 + c * 9))), add=True)

# ---------------------------------------------------------------- geografía (contornos aproximados)
USB = [(-117.1, 32.5), (-114.7, 32.7), (-114.8, 32.5), (-111.07, 31.33), (-108.2, 31.33), (-108.2, 31.78), (-106.5, 31.78), (-105.0, 30.65), (-104.5, 29.6), (-103.3, 29.0), (-102.7, 29.75), (-101.4, 29.77), (-100.7, 29.1), (-100.3, 28.3), (-99.5, 27.5), (-99.1, 26.4), (-98.2, 26.05), (-97.15, 25.95)]
GULF = [(-97.15, 25.95), (-97.7, 24.5), (-97.75, 22.3), (-97.3, 20.9), (-96.4, 19.6), (-96.1, 19.2), (-95.2, 18.7), (-94.5, 18.15), (-93.0, 18.4), (-92.0, 18.65), (-91.3, 18.6), (-90.7, 19.4), (-90.5, 20.4), (-90.3, 21.0), (-89.6, 21.3), (-88.2, 21.6), (-87.1, 21.55), (-86.75, 21.15), (-87.45, 20.2), (-87.5, 19.3), (-87.85, 18.3), (-88.3, 18.5)]
SB = [(-88.3, 18.5), (-88.7, 18.0), (-89.15, 17.82), (-90.99, 17.82), (-90.99, 17.25), (-91.43, 17.25), (-90.45, 16.07), (-91.73, 16.07), (-92.2, 15.25), (-92.2, 14.55)]
PAC = [(-92.2, 14.55), (-93.9, 16.0), (-94.9, 16.2), (-96.5, 15.65), (-97.8, 15.95), (-99.9, 16.85), (-101.6, 17.65), (-102.2, 17.95), (-103.5, 18.3), (-104.3, 19.1), (-105.5, 19.95), (-105.7, 20.4), (-105.25, 20.7), (-105.5, 21.4), (-105.65, 22.4), (-106.4, 23.2), (-107.9, 24.6), (-109.0, 25.6), (-109.45, 26.7), (-110.6, 27.9), (-112.2, 28.95), (-112.8, 30.2), (-113.1, 31.2), (-114.0, 31.5), (-114.8, 31.8)]
BAJA = [(-114.8, 31.8), (-114.7, 31.0), (-114.6, 30.0), (-113.5, 29.0), (-112.8, 28.0), (-112.3, 27.2), (-111.4, 26.2), (-110.7, 24.8), (-110.3, 24.2), (-109.45, 23.3), (-109.95, 22.9), (-110.3, 23.5), (-112.1, 24.6), (-112.2, 26.0), (-113.6, 26.7), (-114.3, 27.15), (-115.05, 27.75), (-114.2, 28.1), (-114.1, 28.6), (-114.9, 29.4), (-115.8, 30.4), (-116.7, 31.8), (-117.1, 32.5)]
NAW = [(-117.1, 32.5), (-118.5, 34), (-120.6, 34.5), (-121.9, 36.6), (-123.8, 39.5), (-124.3, 42), (-124, 46.2), (-124.7, 48.4), (-123, 49), (-127.5, 50.5), (-130.5, 54.5), (-134, 58), (-140, 60), (-146, 61), (-151.5, 59.5), (-158, 57), (-165, 54.7), (-160, 58.8), (-165.5, 62), (-166, 65), (-162, 67), (-166.5, 68.5), (-156.5, 71.3), (-141, 69.7), (-128, 70.3), (-115, 68.5), (-108, 68), (-95, 69), (-85, 69.5), (-87, 64.5), (-93, 61), (-94.5, 58.7), (-88, 56.5), (-82.5, 55), (-82, 52.5), (-79.5, 51.5), (-78.5, 54.5), (-77, 57.5), (-78, 62.4), (-73.5, 62), (-65, 60), (-61.5, 56.5), (-56, 53), (-60, 50.2), (-66.5, 50.2), (-64.5, 47), (-61, 45.5), (-66, 44.3), (-70, 43.7), (-70.5, 41.7), (-74, 40.6), (-75.5, 37.5), (-76, 35.2), (-78.5, 33.8), (-81, 31.5), (-80.1, 27), (-80.4, 25.2), (-81.8, 26.1), (-82.8, 28.5), (-84, 30.1), (-85.3, 29.7), (-87.5, 30.3), (-89.5, 30.2), (-89.4, 29.0), (-91.5, 29.4), (-93.8, 29.7), (-94.8, 29.3), (-96.5, 28.3), (-97.4, 27.3), (-97.15, 25.95)]
CAM = [(-92.2, 14.55), (-91.3, 13.95), (-89.8, 13.6), (-87.9, 13.2), (-87.4, 12.9), (-85.7, 10.9), (-85.8, 10), (-83.6, 8.5), (-82.8, 8.1), (-80.4, 7.4), (-79.5, 8.9), (-78.2, 8.3), (-77.5, 7), (-77.3, 8.5), (-79.5, 9.6), (-81.2, 8.8), (-83.5, 10.5), (-83.8, 12), (-83.4, 14.9), (-84.5, 15.8), (-86, 15.9), (-87.5, 15.85), (-88.3, 15.7), (-88.9, 15.9), (-88.3, 16.5), (-88.1, 17.5), (-88.3, 18.5)]
SAM = [(-77.5, 7), (-77.3, 8.5), (-75.5, 10.8), (-72, 12.2), (-70, 11.5), (-67, 10.5), (-62, 10.7), (-59, 8), (-52, 4.5), (-50, 0), (-44, -2.5), (-37, -4.5), (-35, -7.5), (-38.5, -13), (-39, -17.5), (-41, -22), (-48, -25.5), (-48.5, -28.3), (-53.5, -34), (-57, -38), (-62.5, -39), (-65, -42.5), (-66, -47), (-69, -52), (-74, -52), (-75.5, -47), (-73, -41.5), (-73.5, -37), (-71.5, -31), (-70.3, -18.3), (-76, -14), (-79.5, -7), (-81.3, -4.5), (-80, 0.8), (-78.5, 2.5), (-77.5, 7)]
CUBA = [(-84.9, 21.9), (-83, 23), (-80.5, 23.1), (-77, 21.6), (-74.2, 20.2), (-77.7, 19.85), (-78, 20.7), (-80.5, 21.9), (-82, 22.5), (-84.9, 21.9)]
def chaikin(pts, it=2):
    p = np.array(pts, float)
    for _ in range(it):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]): q += [a * .75 + b * .25, a * .25 + b * .75]
        q.append(p[-1]); p = np.array(q)
    return p
sUSB, sGULF, sSB, sPAC, sBAJA, sNAW, sCAM, sSAM, sCUBA = [chaikin(x) for x in (USB, GULF, SB, PAC, BAJA, NAW, CAM, SAM, CUBA)]
MX = np.vstack([sUSB, sGULF, sSB, sPAC, sBAJA])
NA = np.vstack([sNAW, sUSB[::-1]])
CA = np.vstack([sCAM, sSB])
OTHERS = [NA, CA, sSAM, sCUBA]


def panel_frame(w, h, title):
    pn = np.zeros((h, w, 4), np.uint8); im = Image.fromarray(pn); d = ImageDraw.Draw(im)
    d.rectangle((5, 5, w - 6, h - 6), fill=(8, 48, 78, 170), outline=(120, 230, 255, 245), width=4)
    for y in range(10, h - 8, 6): d.line((9, y, w - 9, y), fill=(120, 230, 255, 14), width=2)
    pn = np.array(im); ts = text_sprite(title, 40, (224, 248, 255, 255), glow=(95, 216, 255), glow_r=8, spacing=3, pad=30)
    over(pn, ts, 30 + ts.shape[1] / 2 - 30 + 4, 46); return pn


