#!/usr/bin/env python3
# Short: ¿Qué pasaría si México tuviera por primera vez una bomba nuclear? (60 s, 1080x1920)
import numpy as np, cv2, math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.signal import butter, lfilter
from scipy.io import wavfile

W, H, FPS, DUR = 1080, 1920, 30, 60
OUT = '/home/claude/out'; os.makedirs(OUT, exist_ok=True)
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

