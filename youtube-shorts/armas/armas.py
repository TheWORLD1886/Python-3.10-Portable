#!/usr/bin/env python3
# Short NEON: ¿Y SI MÉXICO LEGALIZARA LAS ARMAS PARA TODOS? · escenario hipotético · 1080x1920 · 30 fps.
# Mismo formato que «legalizar»: planos DOCUMENTALES (material real con licencia libre, ver material.json y CREDITOS.md),
# NARRATIVOS (stickmans del rig compartido) y COMBINADOS. Cada plano lleva «IMAGEN REAL» (con crédito) o «RECREACIÓN».
# Datos verificados: INEGI, comunicado 42/26 (3 ago 2026): 70.8 % de los presuntos homicidios de 2025 por disparo de arma
# de fuego (preliminar). Constitución, art. 10 (texto vigente, diputados.gob.mx). Ninguna otra cifra.
import os, sys, json, math, subprocess
HERE_A = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE_A, '..', 'nvidia'))
import nvidia2 as N2
from nvidia2 import *
NV = N2.NV; RG = N2.RG; CTX = N2.CTX
OUTA = os.path.join(HERE_A, 'out'); os.makedirs(OUTA, exist_ok=True)
WORDS = json.load(open(os.path.join(HERE_A, 'words.json'))); VOZ = os.path.join(HERE_A, 'voz.mp3')
MAT = {m['id']: m for m in json.load(open(os.path.join(HERE_A, 'material.json')))}
import unicodedata
def _n(x): return ''.join(c for c in unicodedata.normalize('NFD', x.lower()) if unicodedata.category(c) != 'Mn' and c.isalnum() or c == '-')
def T(word, after=-1.):
    for w in WORDS:
        if w[1] >= after and _n(w[0]).startswith(_n(word)): return w[1]
    raise KeyError(word)
DUR = int(math.ceil(WORDS[-1][2] + 1.8))
class Sl(NV.Shot):
    a = 0.
    def w(s, word, after=None): return T(word, s.a - .6 if after is None else s.a + after) - s.a
    def cam(s, t, d): return lerp(1.03, 1.09, RG.ease(t / d)), 540, 1150, 0, 0
P, U, walk, stance, turn_blend, hands_on_top, blinkp, snap = N2.P, N2.U, N2.walk, N2.stance, N2.turn_blend, N2.hands_on_top, N2.blinkp, N2.snap

# ---------------------------------------------------------------- reparto (diseños fijos para todo el video)
RG.CAST['capo'] = dict(nombre='CAPO', alto=1.0, cabeza=1.0, top=(28, 28, 32), pants=(34, 34, 40), shoe=(110, 72, 40), ropa='liso', pelo='peinado',
                       pelo_col=(28, 22, 18), barba=(40, 32, 26), gafas=True)
RG.CAST['funcionaria'] = dict(RG.CAST['directora'], nombre='FUNCIONARIA', top=(70, 40, 52), pants=(44, 40, 50))
RG.CAST['inspector'] = dict(nombre='INSPECTOR', alto=1.0, cabeza=1.0, top=(56, 62, 76), pants=(36, 40, 50), shoe=(16, 16, 20), ropa='traje',
                            corbata=(40, 80, 150), pelo='corto', pelo_col=(50, 40, 30))
RG.CAST['menor'] = dict(nombre='MENOR', alto=.8, cabeza=1.1, top=(60, 150, 200), pants=(60, 60, 80), shoe=(240, 240, 244), ropa='sudadera', pelo='corto', pelo_col=(50, 36, 26))

# ---------------------------------------------------------------- material real
_IMG = {}
def load_img(i):
    im = cv2.imread(os.path.join(HERE_A, MAT[i]['archivo']))[:, :, ::-1]
    h, w = im.shape[:2]; s = min(1., 2600. / max(h, w))                     # suficiente para 1080x1920 con zoom de cámara
    return cv2.resize(im, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA) if s < 1 else im.copy()
def cover(img, fx=.5, fy=.5, zoom=1.):
    h, w = img.shape[:2]; s = max(W / w, H / h) * zoom; im = cv2.resize(img, (int(w * s + .5), int(h * s + .5)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    x0 = int(min(max(0, fx * im.shape[1] - W / 2), im.shape[1] - W)); y0 = int(min(max(0, fy * im.shape[0] - H / 2), im.shape[0] - H))
    return im[y0:y0 + H, x0:x0 + W]
def grade_doc(img, dark_=0., warm=0.):
    f = img.astype(np.float32) * (1 - dark_)
    if warm: f[:, :, 0] *= 1 + warm; f[:, :, 2] *= 1 - warm
    return to8(f)
class Video:
    """frames de un video real (cubre 9:16) en memoria."""
    def __init__(s, i, fx=.5, t0=0., dur=None, zoom=1.):
        cap = cv2.VideoCapture(os.path.join(HERE_A, MAT[i]['archivo'])); s.fps = cap.get(cv2.CAP_PROP_FPS) or 30.; n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t0 * s.fps)); s.fr = []
        while dur is None or len(s.fr) < int(dur * s.fps) + 2:
            ok, im = cap.read()
            if not ok: break
            s.fr.append(cv2.imencode('.jpg', cover(im, fx, .5, zoom), [cv2.IMWRITE_JPEG_QUALITY, 93])[1])   # comprimido en memoria
        s.last = (-1, None)
    def at(s, t):
        k = min(len(s.fr) - 1, max(0, int(t * s.fps)))
        if s.last[0] != k: s.last = (k, cv2.imdecode(s.fr[k], cv2.IMREAD_COLOR)[:, :, ::-1].copy())
        return s.last[1]

def short_lic(m):
    l = m['licencia']; return 'DOMINIO PÚBLICO' if l.lower().startswith('public') else l.upper()
def short_author(m):
    a = m['autor'].replace('CBP Photography', 'CBP').replace('U.S. Customs and Border Protection', 'CBP').replace('U.S. Department of State', 'Departamento de Estado de EE. UU.')
    try: a.encode('latin-1')
    except UnicodeEncodeError: a = 'autor: ver créditos'
    return a[:34]
TAG_SPR = {}
def tag(kind, i=None):
    """etiqueta superior izquierda: IMAGEN REAL (con crédito) o RECREACIÓN."""
    k = (kind, i)
    if k not in TAG_SPR:
        col = (110, 230, 140) if kind == 'real' else (255, 200, 90)
        t1 = N.text_sprite('IMAGEN REAL' if kind == 'real' else 'RECREACIÓN', 26, col + (255,), stroke=3, stroke_col=(0, 0, 0, 230), spacing=3, pad=6)
        t2 = N.text_sprite(f"{short_author(MAT[i])} · {short_lic(MAT[i])} · Wikimedia Commons", 22, (235, 235, 240, 255), stroke=3, stroke_col=(0, 0, 0, 230), pad=6) if i is not None else None
        TAG_SPR[k] = (t1, t2)
    return TAG_SPR[k]
PENDING = []                                         # etiquetas fijas: se pintan después de la cámara (nunca se recortan)
def draw_tag(fr, kind, i=None, op=1.): PENDING.append(('tag', kind, i, op))
def _paint_tag(fr, kind, i, op):
    t1, t2 = tag(kind, i); blit(fr, t1, 48 + t1.shape[1] / 2, 240, op)
    if t2 is not None: blit(fr, t2, 48 + t2.shape[1] / 2, 276, op)
HIPO = None
def hipo(fr, y=320, op=1.): PENDING.append(('hipo', y, op))
def _paint_hipo(fr, y, op):
    global HIPO
    if HIPO is None: HIPO = label('ESCENARIO HIPOTÉTICO', 26, (255, 230, 170))
    blit(fr, HIPO, 48 + HIPO.shape[1] / 2, y, op)
def credit(fr, i): PENDING.append(('cred', i))
def paint_pending(fr):
    for p in PENDING:
        if p[0] == 'tag': _paint_tag(fr, *p[1:])
        elif p[0] == 'hipo': _paint_hipo(fr, *p[1:])
        else: t2 = tag('real', p[1])[1]; blit(fr, t2, 48 + t2.shape[1] / 2, 276)
def big(txt, px=78, col=(255, 255, 255), glow=None): return N.text_sprite(txt, px, col + (255,), glow=glow, glow_r=16, stroke=5, stroke_col=(0, 0, 0, 220))
gold_panel, chip = N2.gold_panel, NV.chip
def red_panel(t1, t2=None, w=820, h=160): return N.holo_panel(w, h, t1, t2, col=(255, 110, 90), fill=(70, 12, 8, 190))
def pop(fr, spr, x, y, t, t0, dur=.35):
    k = ss(t0, t0 + dur, t)
    if k > 0: blit(fr, spr, x, y, k, lerp(.7, 1, eBack(min(1, (t - t0) / dur))))

# fondos combinados: foto real desenfocada y oscurecida + piso sombreado para los personajes
def photo_back(i, fx=.5, fy=.5, dark_=.45, blur=3., warm=0.):
    return [(dof(opaque(grade_doc(cover(load_img(i), fx, fy, 1.08), dark_, warm).astype(np.float32)), blur), .35)]
def ground(y0, col=(18, 18, 24), op=.86):
    fl = np.zeros((H, W, 3), np.uint8); fl[:] = col; al = np.zeros((H, W), np.float32)
    al[y0:] = op; g = np.linspace(0, 1, 60); al[y0 - 60:y0] = (g * op)[:, None]
    for j in range(1, 7): y = int(y0 + (H - y0) * (j / 7.) ** 1.6); cv2.line(fl, (0, y), (W, y), tuple(c + 14 for c in col), 2, cv2.LINE_AA)
    return rgba(fl, al)

# ---------------------------------------------------------------- utilería
def money_stack(fr, x, y, n, col=(90, 150, 90)):
    for k in range(n):
        yy = y - k * 14; cv2.rectangle(fr, (int(x - 60), int(yy - 12)), (int(x + 60), int(yy)), col, -1); cv2.rectangle(fr, (int(x - 60), int(yy - 12)), (int(x + 60), int(yy)), dark(col, .6), 2)
        cv2.rectangle(fr, (int(x - 12), int(yy - 12)), (int(x + 12), int(yy)), (230, 220, 180), -1)
def desk(fr, x0, x1, y, col=(70, 50, 38)):
    cv2.rectangle(fr, (x0, y), (x1, y + 30), dark(col, 1.25), -1); cv2.rectangle(fr, (x0 + 20, y + 30), (x1 - 20, y + 260), col, -1)
def counter(fr, x0, x1, y, col=(200, 204, 214)):
    cv2.rectangle(fr, (x0, y), (x1, y + 24), (240, 242, 246), -1); cv2.rectangle(fr, (x0 + 10, y + 24), (x1 - 10, y + 330), col, -1)
    cv2.rectangle(fr, (x0 + 10, y + 24), (x1 - 10, y + 60), dark(col, .85), -1)
def sign(fr, x, y, w, h, txt, bg=(30, 120, 80), fg=(255, 255, 255), fs=1.1):
    cv2.rectangle(fr, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), bg, -1); cv2.rectangle(fr, (int(x - w / 2), int(y - h / 2)), (int(x + w / 2), int(y + h / 2)), dark(bg, .6), 4)
    (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_DUPLEX, fs, 2)
    if tw > w - 24: fs *= (w - 24) / tw; (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_DUPLEX, fs, 2)
    cv2.putText(fr, txt, (int(x - tw / 2), int(y + th / 2)), cv2.FONT_HERSHEY_DUPLEX, fs, fg, 2, cv2.LINE_AA)
def box_item(fr, x, y, col, txt=None):
    cv2.rectangle(fr, (int(x - 34), int(y - 50)), (int(x + 34), int(y)), col, -1); cv2.rectangle(fr, (int(x - 34), int(y - 50)), (int(x + 34), int(y)), dark(col, .6), 2)
    cv2.rectangle(fr, (int(x - 24), int(y - 34)), (int(x + 24), int(y - 18)), (245, 245, 245), -1)
def envelope(fr, hd, col=(214, 190, 130)):
    x, y = hd[0], hd[1] - 14; cv2.rectangle(fr, (int(x - 34), int(y - 22)), (int(x + 34), int(y + 22)), col, -1); cv2.line(fr, (int(x - 34), int(y - 22)), (int(x), int(y + 4)), dark(col, .7), 2); cv2.line(fr, (int(x + 34), int(y - 22)), (int(x), int(y + 4)), dark(col, .7), 2)
def clipboard(fr, hd):
    x, y = hd[0], hd[1] - 40; cv2.rectangle(fr, (int(x - 34), int(y - 50)), (int(x + 34), int(y + 40)), (120, 84, 50), -1); cv2.rectangle(fr, (int(x - 28), int(y - 40)), (int(x + 28), int(y + 34)), (240, 240, 236), -1)
    for q in range(4): cv2.line(fr, (int(x - 20), int(y - 24 + q * 16)), (int(x + 20), int(y - 24 + q * 16)), (120, 120, 130), 2)
def license_doc(fr, hd, k_stamp):
    x, y = hd[0], hd[1] - 60; cv2.rectangle(fr, (int(x - 70), int(y - 90)), (int(x + 70), int(y + 60)), (244, 238, 222), -1)
    cv2.putText(fr, 'LICENCIA', (int(x - 56), int(y - 56)), cv2.FONT_HERSHEY_DUPLEX, .7, (60, 60, 70), 2, cv2.LINE_AA)
    for q in range(4): cv2.line(fr, (int(x - 56), int(y - 30 + q * 18)), (int(x + 56 - q * 10), int(y - 30 + q * 18)), (150, 150, 160), 2)
    if k_stamp > 0:
        r = int(26 * lerp(1.6, 1, k_stamp)); cv2.circle(fr, (int(x + 30), int(y + 30)), r, (190, 40, 40), 4, cv2.LINE_AA)
        cv2.putText(fr, 'OK', (int(x + 16), int(y + 40)), cv2.FONT_HERSHEY_DUPLEX, .8, (190, 40, 40), 2, cv2.LINE_AA)

# ---------------------------------------------------------------- planos base
class Doc(Sl):
    """DOCUMENTAL: foto real a pantalla completa con movimiento de cámara lento y crédito visible."""
    grade = 1
    def __init__(s, i, fx=.5, fy=.5, z=(1.02, 1.12), pan=(0, 0), dark_=.12, warm=0., title=None, sub=None, ty=760):
        s.i = i; s.zz = z; s.pan = pan; img = grade_doc(cover(load_img(i), fx, fy, 1.06), dark_, warm)
        s.back = []; s.main = opaque(img.astype(np.float32)); s.front = []
        s.title = big(title, 74) if title else None; s.sub = big(sub, 60, (255, 230, 170)) if sub else None; s.ty = ty
        sh = np.zeros((H, W, 4), np.uint8); a_ = np.zeros((H, W), np.float32); a_[:520] = np.linspace(.55, 0, 520)[:, None]; a_[1250:] = np.linspace(0, .6, 670)[:, None]
        s.shade = to8(np.dstack([np.zeros((H, W, 3)), a_ * 255]))
    def draw(s, fr, t, d):
        comp_shade(fr, s.shade); s.extra(fr, t, d)
        if s.title is not None: blit(fr, s.title, 540, s.ty, ss(.15, .55, t), lerp(1.2, 1, ss(.15, .55, t)))
        if s.sub is not None: blit(fr, s.sub, 540, s.ty + 90, ss(.4, .8, t))
        draw_tag(fr, 'real', s.i)
    def extra(s, fr, t, d): pass
    def cam(s, t, d): k = RG.ease(t / d); return lerp(*s.zz, k), 540, 960, lerp(*s.pan, k), 0
def comp_shade(fr, sh):
    a = sh[:, :, 3:4].astype(np.float32) / 255.; fr[:] = to8(fr * (1 - a))
class VidDoc(Doc):
    def __init__(s, i, fx=.5, t0=0., dur=None, title=None, sub=None, ty=760, z=(1.0, 1.06), speed=1.):
        s.i = i; s.v = Video(i, fx, t0, dur); s.zz = z; s.pan = (0, 0); s.speed = speed
        s.back = []; s.main = np.zeros((H, W, 4), np.uint8); s.front = []
        s.title = big(title, 74) if title else None; s.sub = big(sub, 60, (255, 230, 170)) if sub else None; s.ty = ty
        a_ = np.zeros((H, W), np.float32); a_[:520] = np.linspace(.55, 0, 520)[:, None]; a_[1250:] = np.linspace(0, .6, 670)[:, None]; s.shade = to8(np.dstack([np.zeros((H, W, 3)), a_ * 255]))
    def draw(s, fr, t, d): fr[:] = s.v.at(t * s.speed); Doc.draw(s, fr, t, d)
class Comb(Sl):
    """COMBINADO: personajes sobre una foto real desenfocada (fondo documental)."""
    grade = 3
    def __init__(s, i, fx=.5, fy=.5, gy=1640, dark_=.5, warm=0., blur=3.):
        s.i = i; s.back = photo_back(i, fx, fy, dark_, blur, warm); s.main = ground(gy); s.front = [(bokeh_layer(6, (255, 220, 180), 900 + i, ymin=300, ymax=1100), 1.6)]
    def tags(s, fr, hyp=True):
        draw_tag(fr, 'rec'); credit(fr, s.i)
        if hyp: hipo(fr, 316)

# ---------------------------------------------------------------- subtítulos: se escucha la cifra en palabras, se lee en número
def _disp(words):
    out, i = [], 0; rep = [(['dos', 'mil', 'veinticinco,'], '2025,'), (['setenta', 'punto', 'ocho', 'por', 'ciento'], '70.8%'), (['Inegi,'], 'INEGI,')]
    while i < len(words):
        for seq, txt in rep:
            if [w[0] for w in words[i:i + len(seq)]] == seq: out.append([txt, words[i][1], words[i + len(seq) - 1][2]]); i += len(seq); break
        else: out.append(list(words[i])); i += 1
    return out
WDISP = _disp(WORDS)

# ---------------------------------------------------------------- escenarios 2.5D y utilería
def street_bg(seed=1, col=(30, 32, 44), sky=((10, 12, 24), (40, 34, 52)), win=(255, 190, 120), gy=1560):
    s_ = vgrad([(0, sky[0]), (1, sky[1])]); back = [(dof(opaque(s_), 2), .1)]
    city = np.zeros((H, W, 3), np.uint8); r_ = np.random.RandomState(seed); x = -20
    while x < W:
        bw, bh = r_.randint(110, 200), r_.randint(300, 700); cv2.rectangle(city, (x, gy - 10 - bh), (x + bw, gy), col, -1)
        for wy in range(gy - bh + 10, gy - 30, 36):
            for wx in range(x + 12, x + bw - 16, 28):
                if r_.rand() < .14: cv2.rectangle(city, (wx, wy), (wx + 12, wy + 16), win, -1)
        x += bw + r_.randint(4, 12)
    back.append((dof(haze(rgba(city, np.any(city > 0, 2).astype(np.float32)), sky[1], .3), 2), .45))
    return back, floor_layer(gy, (34, 34, 40), (46, 46, 54))
def room_bg(wall=(40, 46, 64), floor=(70, 52, 40), gy=1560):
    w_ = vgrad([(0, wall), (1, tuple(int(c * .7) for c in wall))]); i8 = to8(w_)
    for x in range(0, W, 70): cv2.line(i8, (x, 0), (x, gy - 30), tuple(min(255, int(c * 1.1)) for c in wall), 2)
    cv2.rectangle(i8, (0, gy - 30), (W, gy + 10), tuple(int(c * .6) for c in wall), -1)
    return [(dof(opaque(i8.astype(np.float32)), 2.5), .4)], floor_layer(gy, floor, tuple(min(255, int(c * 1.2)) for c in floor))
def home_props(fr, night=True):
    cv2.rectangle(fr, (700, 640), (1000, 980), (30, 40, 70) if night else (150, 190, 230), -1); cv2.rectangle(fr, (700, 640), (1000, 980), (110, 86, 64), 12); cv2.line(fr, (850, 640), (850, 980), (110, 86, 64), 8)
    if night: cv2.circle(fr, (930, 720), 26, (230, 230, 210), -1)
    cv2.rectangle(fr, (90, 1180), (420, 1560), (96, 70, 50), -1); cv2.rectangle(fr, (110, 1200), (400, 1370), (120, 88, 62), -1); cv2.rectangle(fr, (110, 1390), (400, 1540), (120, 88, 62), -1)   # cómoda
    cv2.circle(fr, (255, 1285), 8, (220, 200, 140), -1); cv2.circle(fr, (255, 1465), 8, (220, 200, 140), -1)
    cv2.line(fr, (250, 1100), (250, 1180), (200, 190, 160), 4); cv2.ellipse(fr, (250, 1090), (60, 34), 0, 180, 360, (240, 210, 140), -1)   # lámpara
def pistol(fr, hd, u, d=1, down=.6, col=(78, 82, 94)):
    """pistola estilizada en la mano, apuntando hacia el suelo (nunca a otra persona). d = hacia dónde mira el cañón."""
    u = u * 1.25; c, s_ = math.cos(down), math.sin(down); ax = A(d * c, s_); nx = A(-ax[1], ax[0]) * d
    h0 = A(*hd); grip = [h0 - nx * .18 * u - ax * .12 * u, h0 + nx * .18 * u - ax * .2 * u, h0 + nx * .2 * u + ax * .1 * u, h0 - nx * .1 * u + ax * .12 * u]
    sl0 = h0 - nx * .26 * u - ax * .2 * u; sl = [sl0, sl0 + ax * 1.05 * u, sl0 + ax * 1.05 * u + nx * .26 * u, sl0 + nx * .26 * u]
    poly(fr, sl, col); poly(fr, grip, dark(col, .8)); line(fr, sl0 + nx * .05 * u, sl0 + ax * 1.0 * u + nx * .05 * u, (110, 114, 124), .04 * u)
def gun_box(fr, x, y, open_=0.):
    cv2.rectangle(fr, (int(x - 110), int(y - 50)), (int(x + 110), int(y)), (40, 40, 46), -1); cv2.rectangle(fr, (int(x - 100), int(y - 42)), (int(x + 100), int(y - 8)), (70, 72, 80), -1)
    if open_ > 0: cv2.rectangle(fr, (int(x - 110), int(y - 50 - 70 * open_)), (int(x + 110), int(y - 50)), (52, 52, 60), -1)
def shield(fr, c, r, col, k=1.):
    if k <= 0: return
    r = r * k; poly(fr, [(c[0] - r, c[1] - r * .8), (c[0] + r, c[1] - r * .8), (c[0] + r * .9, c[1] + r * .2), (c[0], c[1] + r), (c[0] - r * .9, c[1] + r * .2)], col)
    line(fr, (c[0] - r * .35, c[1]), (c[0] - r * .05, c[1] + r * .3), (255, 255, 255), max(3, r * .14)); line(fr, (c[0] - r * .05, c[1] + r * .3), (c[0] + r * .45, c[1] - r * .3), (255, 255, 255), max(3, r * .14))
def warn(fr, c, r, k=1.):
    if k <= 0: return
    r *= k; poly(fr, [(c[0], c[1] - r), (c[0] + r, c[1] + .8 * r), (c[0] - r, c[1] + .8 * r)], (255, 200, 60))
    line(fr, (c[0], c[1] - .35 * r), (c[0], c[1] + .3 * r), (30, 30, 30), max(3, r * .12)); circ(fr, (c[0], c[1] + .55 * r), max(2, r * .08), (30, 30, 30))
CARDS = {}
def photo_card(i, fx=.5, fy=.5, w=620, h=420):
    k = (i, fx, fy, w, h)
    if k not in CARDS:
        im = load_img(i); ih, iw = im.shape[:2]; s = max(w / iw, h / ih); im = cv2.resize(im, (int(iw * s + .5), int(ih * s + .5)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        x0 = int(min(max(0, fx * im.shape[1] - w / 2), im.shape[1] - w)); y0 = int(min(max(0, fy * im.shape[0] - h / 2), im.shape[0] - h)); im = im[y0:y0 + h, x0:x0 + w]
        b = 14; out = np.zeros((h + 2 * b + 46, w + 2 * b, 4), np.uint8); out[:, :, :3] = 246; out[:, :, 3] = 255; out[b:b + h, b:b + w, :3] = im
        cap = f"FOTO REAL · {short_author(MAT[i])} · {short_lic(MAT[i])}"; cv2.putText(out, cap, (b + 4, h + b + 32), cv2.FONT_HERSHEY_DUPLEX, .62, (60, 60, 70, 255), 1, cv2.LINE_AA)
        CARDS[k] = out
    return CARDS[k]
def draw_card(fr, card, x, y, t, t0, sc=1.):
    k = ss(t0, t0 + .45, t)
    if k <= 0: return
    e = eOut(min(1., (t - t0) / .45)); sh = np.zeros_like(card); sh[:, :, 3] = (card[:, :, 3] * .45).astype(np.uint8)
    blit(fr, sh, x + 14, y + 18 + math.sin(t * 1.3) * 4, k * .6, sc * lerp(.85, 1, e)); blit(fr, card, x, y + math.sin(t * 1.3) * 4, k, sc * lerp(.85, 1, e))

# ================================================================ GANCHO
class Hook(VidDoc):                                 # ¿y si mañana cualquier mexicano pudiera comprar un arma? (cruce real de Eje Central y Madero)
    def __init__(s):
        VidDoc.__init__(s, 92, fx=.5, t0=2.0, dur=5., z=(1.0, 1.08))
        s.t1 = big('¿Y SI CUALQUIER', 80); s.t2 = big('MEXICANO PUDIERA', 80); s.t3 = big('COMPRAR UN ARMA?', 84, (255, 220, 120), glow=(255, 120, 30))
        s.note = label('Cruce de Eje Central y Madero, Ciudad de México · 2023', 22, (230, 230, 236))
    def extra(s, fr, t, d):
        for k, (sp, y) in enumerate(((s.t1, 600), (s.t2, 700), (s.t3, 810))): pop(fr, sp, 540, y, t, .1 + k * .25)
        blit(fr, s.note, 540, 1300, ss(.4, .8, t)); hipo(fr, 316)
class HomeGun(Sl):                                  # millones de personas con una pistola en casa (recreación)
    grade = 4
    def __init__(s):
        s.back, s.main = room_bg((40, 44, 66), (64, 50, 40)); s.front = [(bokeh_layer(6, (255, 210, 160), 1101, ymin=300, ymax=1100), 1.7)]
        s.p = gold_panel('MILLONES DE PISTOLAS', 'EN CASA', w=820, h=170)
    def draw(s, fr, t, d):
        home_props(fr); x, fy, h = 520, 1730, 720; u = U('vecino', h); top = (300, 1170); tp = s.w('pistola') - .9
        gun_box(fr, top[0], top[1], ss(tp, tp + .4, t))
        keys = [(0, P(look=(-.5, .3), frown=.1)), (tp - .5, P(look=(-.55, .4), lean=.04, grip={'L': (top[0] + 60, top[1] - 40, 1.)}, tz=.4)),        # abre la caja con la mano cercana
                (tp + .5, P(look=(-.5, .45), lean=.05, grip={'L': (top[0] + 60, top[1] - 40, 1.)}, tz=.4)),
                (tp + 1.4, P(look=(-.05, .35), frown=.3, brow_up=.3, grip={'L': (x - .3 * u, fy - 4.6 * u, 1.)}, tz=.9)),                                     # la sostiene y la mira, apuntando al suelo
                (d, P(look=(-.05, .38), frown=.4, brow_up=.4, boca='tensa', grip={'L': (x - .3 * u, fy - 4.6 * u, 1.)}, tz=.9))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 111)
        hands, _ = RG.person_34(fr, 'vecino', x, fy, h, p, t, feet=stance(x, u, fy), turn=-1)
        if t > tp + .5: pistol(fr, hands['L'], u, d=-1, down=1.1); hands_on_top(fr, {'L': hands['L']}, 'vecino', h)
        float_in(fr, s.p, 540, 470, t, .2); draw_tag(fr, 'rec'); hipo(fr, 290)
    def cam(s, t, d): return lerp(1.04, 1.12, RG.ease(t / d)), 480, 1250, 0, 0
class SafeOrNot(Comb):                              # ¿más seguro o mucho más peligroso? (calle Madero de noche, foto real de fondo)
    def __init__(s):
        Comb.__init__(s, 47, fx=.5, fy=.45, gy=1600, dark_=.45)
        s.a1 = N.holo_panel(460, 150, '¿MÁS SEGURO?', None, col=(150, 240, 90), fill=(16, 50, 10, 190)); s.a2 = red_panel('¿MÁS PELIGROSO?', w=460, h=150)
    def draw(s, fr, t, d):
        x, fy, h = 540, 1730, 700; u = U('vecina', h); ts, tp = s.w('seguro'), s.w('peligroso')
        keys = [(0, P(look=(0, .1))), (ts, P(look=(-.5, -.1), brow_up=.3)), (tp - .3, P(look=(-.3, -.1), brow_up=.3, grip={'R': (x + .3 * u, fy - 6.6 * u, 1.)}, tz=.9)),
                (tp + .4, P(look=(.5, -.1), frown=.35, brow_asym=.4, grip={'R': (x + .3 * u, fy - 6.6 * u, 1.)}, tz=.9)), (d, P(look=(.1, .05), frown=.4, brow_asym=.4, grip={'R': (x + .3 * u, fy - 6.6 * u, 1.)}, tz=.9))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 112); RG.person(fr, 'vecina', x, fy, h, p, t, feet=stance(x, u, fy))
        pop(fr, s.a1, 290, 640, t, ts - .3); shield(fr, (290, 840), 70, (60, 170, 100), ss(ts, ts + .4, t))
        pop(fr, s.a2, 790, 640, t, tp - .3); warn(fr, (790, 840), 70, ss(tp, tp + .4, t)); s.tags(fr)

# ================================================================ CONFLICTO
class Supporters(Sl):                               # si los criminales están armados, ¿por qué los honestos no podrían defenderse?
    grade = 3
    def __init__(s):
        s.back, s.main = street_bg(41, (34, 30, 40), ((14, 10, 20), (60, 40, 46))); s.front = [(bokeh_layer(8, (255, 200, 140), 1102, ymin=200, ymax=1200), 1.7)]
        s.l1 = label('CRIMINALES ARMADOS', 30, (255, 140, 120)); s.l2 = label('CIUDADANO HONESTO', 30, (140, 240, 170)); s.q = big('¿POR QUÉ NO DEFENDERSE?', 62, (255, 236, 200))
    def draw(s, fr, t, d):
        fy, h = 1740, 700; xc, xv = 260, 780; uc, uv = U('capo', h), U('vecino', h); tc, th = s.w('criminales'), s.w('honestos')
        pc = P(look=(.4, .1), frown=.5, boca='tensa', grip={'R': (xc + .7 * uc, fy - 4.4 * uc, 1.)}, tz=.6, blink=blinkp(t, 113))
        k = ss(tc - .3, tc + .3, t)
        if k > 0:
            def cap(f_):
                hd, _ = RG.person_34(f_, 'capo', xc, fy, h, pc, t, feet=stance(xc, uc, fy), turn=1); pistol(f_, hd['R'], uc, d=1, down=1.15); hands_on_top(f_, {'R': hd['R']}, 'capo', h); return hd
            fade_in(fr, k, cap); blit(fr, s.l1, xc, 1800, k)
        keys = [(0, P(look=(-.1, .1))), (tc, P(look=(-.45, .1), frown=.3, grip={'R': (xv - 1.4 * uv, fy - 6.0 * uv, 1.)}, tz=.4)),                  # señala al criminal
                (th - .3, P(look=(-.3, .1), frown=.35, grip={'R': (xv - 1.4 * uv, fy - 6.0 * uv, 1.)}, tz=.4)),
                (th + .5, P(look=(0, .05), frown=.2, brow_up=.5, boca='tensa', grip={'R': (xv + .1 * uv, fy - 5.2 * uv, 1.), 'L': (xv - 1.2 * uv, fy - 5.4 * uv, 1.)}, tz=.8)),   # mano al pecho: ¿y yo?
                (d, P(look=(0, .05), frown=.2, brow_up=.55, boca='tensa', grip={'R': (xv + .1 * uv, fy - 5.2 * uv, 1.), 'L': (xv - 1.2 * uv, fy - 5.4 * uv, 1.)}, tz=.8))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 114); RG.person_34(fr, 'vecino', xv, fy, h, p, t, feet=stance(xv, uv, fy), turn=-1)
        blit(fr, s.l2, xv, 1800, ss(.2, .6, t)); pop(fr, s.q, 540, 520, t, th - .2); draw_tag(fr, 'rec'); hipo(fr, 290)
class NoDistinguish(Sl):                            # un arma no distingue: delincuente, víctima o alguien que perdió el control
    grade = 2
    def __init__(s):
        s.back = NV.stage_bg(42, (10, 10, 16), (200, 80, 70)); s.main = ground(1560, (22, 20, 26), 1.); s.front = []
        s.t = red_panel('UN ARMA NO DISTINGUE', w=820, h=140); s.ls = [label(x, 26, (255, 255, 255)) for x in ('DELINCUENTE', 'VÍCTIMA', 'DISCUSIÓN')]
    def draw(s, fr, t, d):
        fy, h = 1740, 560; xs = (190, 540, 890); who = ('capo', 'vecina', 'peaton2'); words = ('delincuente', 'víctima', 'persona')
        for k in range(3):
            tk = s.w(words[k]) - .2; on = ss(tk, tk + .35, t); x = xs[k]; u = U(who[k], h)
            cv2.ellipse(fr, (x, fy + 10), (int(140 * (.4 + .6 * on)), 30), 0, 0, 360, (int(70 + 120 * on), int(60 + 60 * on), 50), -1, cv2.LINE_AA)   # foco
            if k == 0: p = P(look=(.2, .1), frown=.5, boca='tensa')
            elif k == 1: p = RG.anim([(0, P(look=(0, .1))), (tk + .2, P(look=(0, .05), frown=-.4, brow_up=.8, boca='o', sh=-.25))], t)
            else: p = RG.anim([(0, P(look=(-.3, .1))), (tk + .2, P(look=(-.3, .1), frown=.8, boca='grito', sh=.15, grip={'L': (x - 1.3 * u, fy - 6.4 * u, 1.)}, tz=.4)), (d, P(look=(-.3, .1), frown=.8, boca='grito', sh=.15, grip={'L': (x - 1.3 * u, fy - 6.4 * u, 1.)}, tz=.4))], t)
            p['blink'] = blinkp(t, 115 + k)
            dim = lambda f_, w_=who[k], x=x, u=u, p=p: RG.person(f_, w_, x, fy, h, p, t, feet=stance(x, u, fy))
            if on < 1:
                a = fr.copy(); dim(fr); fr[:] = cv2.addWeighted(a, 1 - (.35 + .65 * on), fr, .35 + .65 * on, 0)
            else: dim(fr)
            blit(fr, s.ls[k], x, 1810, on)
        float_in(fr, s.t, 540, 460, t, s.w('arma', 1.4) - .3); draw_tag(fr, 'rec')
    def cam(s, t, d): return lerp(1.02, 1.08, RG.ease(t / d)), 540, 1300, 0, 0

# ================================================================ EL DATO
class Inegi(Doc):                                   # no es una preocupación menor: según el INEGI... (edificio real del INEGI)
    def __init__(s):
        Doc.__init__(s, 12, fx=.55, fy=.45, z=(1.02, 1.12), dark_=.3)
        s.t = big('NO ES UNA', 76); s.t2 = big('PREOCUPACIÓN MENOR', 76, (255, 220, 120), glow=(255, 120, 30)); s.note = label('Edificio central del INEGI, Aguascalientes · 2024', 22, (230, 230, 236))
    def extra(s, fr, t, d): pop(fr, s.t, 540, 640, t, .1); pop(fr, s.t2, 540, 740, t, .3); blit(fr, s.note, 540, 1300, ss(.3, .7, t))
class Data(Sl):                                     # 70.8 % de los homicidios de 2025, con arma de fuego (gráfico con el dato oficial)
    grade = 2
    def __init__(s):
        s.back = NV.stage_bg(43, (12, 8, 8), (220, 70, 60)); s.main = np.zeros((H, W, 4), np.uint8); s.front = []
        s.h = label('HOMICIDIOS EN MÉXICO · 2025', 34, (255, 230, 170)); s.c = label('CON ARMA DE FUEGO', 40, (255, 255, 255))
        s.src = label('INEGI · comunicado 42/26 · datos preliminares', 24, (230, 230, 236)); s.n7 = label('7 DE CADA 10', 46, (255, 120, 100))
    def draw(s, fr, t, d):
        t0 = s.w('setenta') - .2; k = ss(t0, t0 + 1.4, t); pct = 70.8 * eOut(k); cx, cy, r = 540, 900, 270
        cv2.circle(fr, (cx, cy), r, (60, 50, 56), 60, cv2.LINE_AA)
        if pct > 0: cv2.ellipse(fr, (cx, cy), (r, r), -90, 0, 360 * pct / 100, (230, 60, 50), 60, cv2.LINE_AA)
        num = N.text_sprite(f'{pct:.1f}%', 130, (255, 255, 255, 255), stroke=5, stroke_col=(0, 0, 0, 200)); blit(fr, num, cx, cy - 10, ss(t0 - .2, t0, t))
        blit(fr, s.h, 540, 470, ss(0, .4, t)); blit(fr, s.c, 540, cy + r + 62, ss(s.w('armas') - .3, s.w('armas'), t))
        for q in range(10):                                                          # 10 figuras: 7 en rojo (redondeo de 70.8 %)
            x = 135 + q * 90; y = 1335; on = ss(t0 + 1.4 + q * .06, t0 + 1.6 + q * .06, t); col = (230, 60, 50) if q < 7 else (110, 110, 120)
            if on > 0: circ(fr, (x, y - 40), 18 * on, col); poly(fr, [(x - 22 * on, y + 30), (x + 22 * on, y + 30), (x + 14 * on, y - 16), (x - 14 * on, y - 16)], col)
        blit(fr, s.n7, 540, 1418, ss(t0 + 2.2, t0 + 2.6, t)); blit(fr, s.src, 540, 525, ss(t0, t0 + .4, t)); draw_tag(fr, 'rec')

# ================================================================ LA ESCALADA
class EasyBuy(Sl):                                  # conseguir un arma fuera mucho más sencillo: mostrador hipotético
    grade = 3
    def __init__(s):
        s.back, s.main = room_bg((70, 64, 60), (80, 66, 52)); s.front = []; s.t = gold_panel('¿Y SI FUERA', 'MUY FÁCIL CONSEGUIRLA?', w=820, h=170)
    def draw(s, fr, t, d):
        sign(fr, 820, 700, 360, 90, 'VENTA', (120, 40, 40)); counter(fr, 600, 1060, 1300, (110, 90, 74))
        fy, h = 1740, 680; xs = 830; us = U('ejecutivo', h); xb = 330; ub = U('peaton1', h); tb = .9
        gun_box(fr, 760, 1300, 0.)
        ps = RG.anim([(0, P(look=(-.4, .1), boca='sonrisa')), (tb, P(look=(-.4, .2), boca='sonrisa', lean=.03, grip={'R': (760 - 40, 1270, 1.)}, tz=.4)),
                      (tb + .9, P(look=(-.4, .1), boca='sonrisa', grip={'R': (760 - 40, 1270, 1.)}, tz=.4)), (d, P(look=(-.4, .1), boca='sonrisa', grip={'R': (760 - 40, 1270, 1.)}, tz=.4))], t)   # empuja la caja
        ps['blink'] = blinkp(t, 118); RG.person_34(fr, 'ejecutivo', xs, fy - 60, h, ps, t, feet=stance(xs, us, fy - 60), turn=-1)
        pb = RG.anim([(0, P(look=(.45, .1), frown=-.1)), (tb + .6, P(look=(.45, .25), brow_up=.5, boca='o')), (d, P(look=(.45, .2), brow_up=.5, boca='o'))], t); pb['blink'] = blinkp(t, 119)
        RG.person_34(fr, 'peaton1', xb, fy, h, pb, t, feet=stance(xb, ub, fy), turn=1)
        float_in(fr, s.t, 540, 470, t, .1); draw_tag(fr, 'rec'); hipo(fr, 290)
class Family(Sl):                                   # una familia podría sentirse más protegida frente a un asalto
    grade = 1
    def __init__(s): s.back, s.main = room_bg((50, 60, 80), (70, 56, 44)); s.front = [(bokeh_layer(6, (255, 220, 170), 1103, ymin=300, ymax=1100), 1.7)]; s.t = N.holo_panel(760, 150, 'MÁS PROTEGIDOS', 'frente a un asalto', col=(150, 240, 90), fill=(16, 50, 10, 190))
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (780, 760), (1020, 1560), (100, 70, 50), -1); cv2.rectangle(fr, (800, 780), (1000, 1560), (130, 92, 64), -1); circ(fr, (975, 1180), 12, (220, 200, 140))   # puerta con cerrojo
        k = ss(s.w('protegida') - .3, s.w('protegida') + .2, t); line(fr, (930, 1150), (930 + 50 * k, 1150), (200, 200, 210), 10)
        fy, h = 1740, 680
        for i, (w_, x, hh, turn) in enumerate((('vecino', 260, h, 1), ('vecina', 520, h * .96, -1), ('menor', 400, 480, 1))):
            u = U(w_, hh); p = RG.anim([(0, P(look=(.4 * turn, .1), frown=.2)), (s.w('protegida'), P(look=(.4 * turn, .05), frown=-.2, boca='sonrisa')), (d, P(look=(.3 * turn, .05), frown=-.2, boca='sonrisa'))], t)
            if w_ == 'vecino': p['grip'] = {'R': (x + 1.0 * u, fy - 5.2 * u, 1.)}; p['tz'] = .5
            p['blink'] = blinkp(t, 120 + i); RG.person_34(fr, w_, x, fy - (20 if w_ == 'menor' else 0), hh, p, t, feet=stance(x, u, fy - (20 if w_ == 'menor' else 0)), turn=turn)
        shield(fr, (540, 760), 90, (60, 170, 100), ss(s.w('protegida'), s.w('protegida') + .5, t)); float_in(fr, s.t, 540, 470, t, .1); draw_tag(fr, 'rec'); hipo(fr, 290)
class Risks(Sl):                                    # también accidentes, amenazas con armas y enfrentamientos que terminan en tragedia
    grade = 4
    def __init__(s):
        s.back, s.main = street_bg(44, (30, 26, 34), ((12, 8, 16), (70, 30, 34))); s.front = [(bokeh_layer(8, (255, 140, 110), 1104, ymin=200, ymax=1200), 1.7)]
        s.c = [red_panel(x, w=560, h=110) for x in ('ACCIDENTES', 'AMENAZAS CON ARMAS', 'ENFRENTAMIENTOS')]; s.tr = big('TRAGEDIA', 90, (255, 110, 100), glow=(255, 40, 30))
    def draw(s, fr, t, d):
        fy, h = 1740, 680; xa, xb = 330, 760; ua, ub = U('vecino', h), U('peaton2', h); te = s.w('amenazas')
        pa = RG.anim([(0, P(look=(.45, .1), frown=.3)), (te, P(look=(.45, .1), frown=.7, boca='grito', lean=.04, grip={'R': (xa + 1.5 * ua, fy - 6.0 * ua, 1.)}, tz=.4)),
                      (d, P(look=(.45, .1), frown=.75, boca='grito', lean=.05, grip={'R': (xa + 1.5 * ua, fy - 6.1 * ua, 1.)}, tz=.4))], t)
        pb = RG.anim([(0, P(look=(-.45, .1), frown=.3)), (te + .3, P(look=(-.45, .1), frown=.75, boca='grito', grip={'L': (xb - 1.5 * ub, fy - 6.0 * ub, 1.)}, tz=.4)),
                      (d, P(look=(-.45, .1), frown=.8, boca='grito', grip={'L': (xb - 1.5 * ub, fy - 6.1 * ub, 1.)}, tz=.4))], t)
        pa['blink'] = blinkp(t, 123); pb['blink'] = blinkp(t, 124)
        RG.person_34(fr, 'vecino', xa, fy, h, pa, t, feet=stance(xa, ua, fy), turn=1); RG.person_34(fr, 'peaton2', xb, fy, h, pb, t, feet=stance(xb, ub, fy), turn=-1)
        for k, wd in enumerate(('accidentes', 'amenazas', 'enfrentamientos')): pop(fr, s.c[k], 540, 440 + k * 120, t, s.w(wd) - .1); warn(fr, (200, 440 + k * 120), 34, ss(s.w(wd), s.w(wd) + .3, t))
        tt = s.w('tragedia') - .1; k = ss(tt, tt + .3, t)
        if k > 0: blit(fr, s.tr, 540, 860, k, lerp(1.5, 1, eOut(k)))
        draw_tag(fr, 'rec'); hipo(fr, 290)
    def cam(s, t, d): return lerp(1.03, 1.12, RG.ease(t / d)), 540, 1300, 0, 0
class Criminals(Doc):                               # ¿cómo impedirías que terminaran en manos de criminales? (armas aseguradas reales, CBP)
    def __init__(s):
        Doc.__init__(s, 105, fx=.5, fy=.5, z=(1.04, 1.16), pan=(-25, 25), dark_=.3)
        s.p = red_panel('¿Y SI TERMINAN EN MANOS', 'DE CRIMINALES?', w=860, h=170); s.note = label('Armas aseguradas que iban rumbo a México · Nogales, Arizona · 2025', 22, (230, 230, 236))
    def extra(s, fr, t, d): pop(fr, s.p, 540, 660, t, s.w('manos') - .5); blit(fr, s.note, 540, 1300, ss(.3, .7, t))
class Illegal(Doc):                                 # el crimen organizado no dejaría de conseguirlas ilegalmente (decomiso real, CBP)
    def __init__(s):
        Doc.__init__(s, 101, fx=.5, fy=.5, z=(1.14, 1.02), pan=(20, -20), dark_=.32)
        s.p = gold_panel('LEGALIZAR NO DETIENE', 'EL TRÁFICO ILEGAL', w=820, h=170); s.note = label('Aseguramiento de armas en el puerto de Mariposa, Nogales · mayo 2025', 22, (230, 230, 236))
    def extra(s, fr, t, d): pop(fr, s.p, 540, 660, t, s.w('ilegalmente') - .6); blit(fr, s.note, 540, 1300, ss(.3, .7, t)); hipo(fr, 316)

# ================================================================ EL GIRO
class Article10(Comb):                              # México ya reconoce el derecho a poseer armas en el domicilio (Constitución, art. 10)
    grade = 2
    def __init__(s):
        Comb.__init__(s, 12, fx=.5, fy=.5, gy=1900, dark_=.75, blur=6.); s.card = photo_card(9, .5, .5, 300, 420)
        s.h = big('ALGO QUE MUCHOS OLVIDAN', 56, (255, 236, 200)); s.src = label('Constitución, art. 10 · texto vigente (Cámara de Diputados)', 22, (230, 230, 236))
        s.ttl = N.text_sprite('Artículo 10.', 40, (120, 30, 30, 255), pad=4)
        s.lines = [N.text_sprite(x, 30, (40, 40, 50, 255), pad=4) for x in ('Los habitantes de los Estados Unidos', 'Mexicanos tienen derecho a poseer', 'armas en su domicilio, para su', 'seguridad y legítima defensa...')]
        s.req = N.text_sprite('con las excepciones y requisitos de la ley', 24, (150, 30, 30, 255), pad=4)
    def draw(s, fr, t, d):
        pop(fr, s.h, 540, 440, t, .05); draw_card(fr, s.card, 250, 860, t, .3)
        k = ss(s.w('reconoce') - .3, s.w('reconoce') + .3, t); x0, y0 = 430, int(lerp(1900, 640, eOut(k)))
        cv2.rectangle(fr, (x0, y0), (x0 + 600, y0 + 480), (244, 238, 222), -1); cv2.rectangle(fr, (x0, y0), (x0 + 600, y0 + 480), (150, 140, 120), 3)
        blit(fr, s.ttl, x0 + 30 + s.ttl.shape[1] / 2, y0 + 55)
        for q, l in enumerate(s.lines): blit(fr, l, x0 + 30 + l.shape[1] / 2, y0 + 125 + q * 50)
        kh = ss(s.w('domicilio') - .2, s.w('domicilio') + .3, t)
        if kh > 0: cv2.rectangle(fr, (x0 + 24, y0 + 205), (x0 + 24 + int(420 * kh), y0 + 245), (255, 220, 80), 3)
        kr = ss(s.w('restricciones') - .2, s.w('restricciones') + .2, t)
        if kr > 0: blit(fr, s.req, x0 + 30 + s.req.shape[1] / 2, y0 + 395, kr)
        blit(fr, s.src, 540, 1180, ss(.6, 1., t)); draw_tag(fr, 'rec'); credit(fr, 9)
class NoCarry(Sl):                                  # no significa que cualquiera pueda llevar un arma por la calle
    grade = 3
    def __init__(s):
        s.back, s.main = street_bg(45, (40, 38, 50), ((40, 60, 90), (120, 120, 140))); s.front = []
        s.pa = N.holo_panel(460, 140, 'POSEER EN CASA', 'derecho con requisitos', col=(150, 240, 90), fill=(16, 50, 10, 190)); s.pb = red_panel('PORTAR EN LA CALLE', 'requiere permiso', w=460, h=140)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (60, 1100), (420, 1560), (150, 110, 80), -1); poly(fr, [(40, 1110), (240, 920), (440, 1110)], (110, 60, 50)); cv2.rectangle(fr, (190, 1340), (290, 1560), (90, 60, 40), -1)   # casa
        x, fy, h = 640, 1740, 680; u = U('vecino', h); tn = s.w('calle') - .6
        keys = [(0, P(look=(-.4, .1))), (.6, P(look=(-.4, .1), grip={'L': (x - 1.45 * u, fy - 6.0 * u, 1.)}, tz=.4)), (tn - .3, P(look=(.3, .1), grip={'L': (x - 1.45 * u, fy - 6.0 * u, 1.)}, tz=.4)),
                (tn + .4, P(look=(.4, .1), frown=.4, brow_asym=.3, grip={'R': (x + 1.45 * u, fy - 6.0 * u, 1.)}, tz=.4)), (d, P(look=(.4, .1), frown=.45, brow_asym=.3, grip={'R': (x + 1.45 * u, fy - 6.0 * u, 1.)}, tz=.4))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 125); RG.person(fr, 'vecino', x, fy, h, p, t, feet=stance(x, u, fy))
        pop(fr, s.pa, 270, 560, t, .2); shield(fr, (270, 760), 54, (60, 170, 100), ss(.4, .8, t))
        pop(fr, s.pb, 800, 560, t, tn); k = ss(tn + .2, tn + .5, t)
        if k > 0: c = (800, 760); circ(fr, c, 56 * k, (220, 50, 50)); line(fr, (c[0] - 34 * k, c[1] - 34 * k), (c[0] + 34 * k, c[1] + 34 * k), (255, 255, 255), 10); line(fr, (c[0] + 34 * k, c[1] - 34 * k), (c[0] - 34 * k, c[1] + 34 * k), (255, 255, 255), 10)
        draw_tag(fr, 'rec')

# ================================================================ CIERRE
class TrueQuestion(Doc):                            # la verdadera pregunta (calle Madero de noche, foto real)
    def __init__(s): Doc.__init__(s, 47, fx=.5, fy=.45, z=(1.0, 1.1), dark_=.3, title='LA VERDADERA', sub='PREGUNTA', ty=760)
class ArmsOrInst(Sl):                               # ¿ciudadanos mejor armados o instituciones capaces de protegerlos? (foto real de la Policía Federal como referencia)
    grade = 3
    def __init__(s):
        s.back, s.main = street_bg(46, (34, 32, 44), ((16, 14, 30), (70, 50, 70))); s.front = [(bokeh_layer(8, (255, 210, 160), 1106, ymin=200, ymax=1200), 1.7)]
        s.card = photo_card(169, .5, .4, 400, 300); s.pa = gold_panel('¿CIUDADANOS', 'MEJOR ARMADOS?', w=470, h=150); s.pb = N.holo_panel(470, 150, '¿INSTITUCIONES', 'QUE PROTEJAN?')
        s.note = label('Policía Federal, simulacro nacional · CDMX · 2015', 20, (230, 230, 236))
    def draw(s, fr, t, d):
        x, fy, h = 540, 1740, 640; u = U('vecina', h); ta, ti = s.w('armados'), s.w('instituciones')
        keys = [(0, P(look=(0, .1))), (ta - .2, P(look=(-.5, -.1), brow_up=.3, grip={'L': (x - 1.4 * u, fy - 5.6 * u, 1.)}, tz=.5)), (ti - .3, P(look=(-.4, -.1), brow_up=.3, grip={'L': (x - 1.4 * u, fy - 5.6 * u, 1.)}, tz=.5)),
                (ti + .4, P(look=(.5, -.1), brow_up=.3, grip={'R': (x + 1.4 * u, fy - 5.6 * u, 1.)}, tz=.5)), (d, P(look=(.1, .05), frown=.3, brow_asym=.4, grip={'R': (x + .3 * u, fy - 6.6 * u, 1.)}, tz=.9))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 126); RG.person(fr, 'vecina', x, fy, h, p, t, feet=stance(x, u, fy))
        pop(fr, s.pa, 280, 520, t, ta - .4)
        k = ss(ta, ta + .4, t)
        if k > 0: pistol(fr, (250, 760), 70, d=1, down=1.2)
        pop(fr, s.pb, 800, 520, t, ti - .4); draw_card(fr, s.card, 800, 800, t, ti - .2, .95); blit(fr, s.note, 800, 990, ss(ti, ti + .4, t))
        draw_tag(fr, 'rec')
class Permit(Sl):                                   # ¿permitirías que cualquier adulto comprara un arma tras controles estrictos?
    grade = 1
    def __init__(s):
        s.back = NV.stage_bg(47, (8, 12, 20), (90, 160, 230)); s.main = ground(1560, (20, 22, 30), 1.); s.front = []
        s.q = big('¿TÚ LO PERMITIRÍAS?', 76, (255, 220, 120), glow=(255, 120, 30)); s.c = chip('CONTROLES ESTRICTOS', (150, 230, 255), w=560)
    def draw(s, fr, t, d):
        x0, y0 = 300, 640; cv2.rectangle(fr, (x0, y0), (x0 + 480, y0 + 520), (240, 240, 236), -1); cv2.rectangle(fr, (x0, y0), (x0 + 480, y0 + 520), (120, 120, 130), 3)
        tc = s.w('controles') - .4
        for q in range(4):
            y = y0 + 90 + q * 110; cv2.rectangle(fr, (x0 + 40, y - 30), (x0 + 100, y + 30), (90, 90, 100), 4); cv2.rectangle(fr, (x0 + 130, y - 10), (x0 + 420 - q * 30, y + 10), (190, 190, 200), -1)
            k = ss(tc + q * .25, tc + q * .25 + .25, t)
            if k > 0: line(fr, (x0 + 50, y), (x0 + 50 + 18 * k, y + 18 * k), (40, 170, 90), 8); line(fr, (x0 + 68, y + 18), (x0 + 68 + 30 * k, y + 18 - 46 * k), (40, 170, 90), 8)
        pop(fr, s.c, 540, 560, t, tc - .2); pop(fr, s.q, 540, 1290, t, .1); draw_tag(fr, 'rec'); hipo(fr, 290)
class Comments(Sl):                                 # te leo en los comentarios
    grade = 3
    def __init__(s):
        s.back, s.main = room_bg((50, 40, 70), (70, 56, 44)); s.front = [(bokeh_layer(8, (255, 200, 255), 1107, ymin=200, ymax=1100), 1.7)]
        s.cta = gold_panel('TE LEO EN LOS', 'COMENTARIOS', w=820, h=170); s.bub = [N.text_sprite(x, 32, (20, 20, 26, 255), pad=10) for x in ('Más seguridad', 'Más peligro', 'Depende de los controles')]
    def draw(s, fr, t, d):
        for k, (x, w_, turn) in enumerate(((330, 'vecino', 1), (750, 'vecina', -1))):
            h = 660; u = U(w_, h); fy = 1740
            p = RG.anim([(0, P(look=(.3 * turn, .05))), (.3, P(look=(0, .05))), (1.2, P(look=(0, .05), boca='sonrisa', grip={('R' if turn > 0 else 'L'): (x + turn * 1.3 * u, fy - 6.8 * u, 1.)}, tz=.4)),
                         (d, P(look=(0, .05), boca='sonrisa', grip={('R' if turn > 0 else 'L'): (x + turn * 1.35 * u, fy - 6.9 * u, 1.)}, tz=.4))], t)
            p['blink'] = blinkp(t, 127 + k); RG.person_34(fr, w_, x, fy, h, p, t, feet=stance(x, u, fy), turn=turn)
        for k, sp in enumerate(s.bub):
            kk = ss(.3 + k * .3, .6 + k * .3, t)
            if kk > 0:
                y = 760 + k * 130; x = (380, 700, 540)[k]; bw, bh = sp.shape[1], sp.shape[0]
                cv2.rectangle(fr, (int(x - bw * .55), int(y - bh * .7)), (int(x + bw * .55), int(y + bh * .7)), (255, 255, 255), -1); blit(fr, sp, x, y, kk)
        float_in(fr, s.cta, 540, 470, t, .05); draw_tag(fr, 'rec')

# ================================================================ línea de tiempo
def tl():
    seq = [(0, Hook(), 0), (T('imagina') - .3, HomeGun(), 4), (T('méxico') - .3, SafeOrNot(), 3),
           (T('quienes') - .3, Supporters(), 3), (T('pero', 20) - .3, NoDistinguish(), 2),
           (T('y', 28.5) - .3, Inegi(), 1), (T('aproximadamente') - .3, Data(), 2),
           (T('ahora') - .3, EasyBuy(), 3), (T('una', 43) - .3, Family(), 1), (T('pero', 46.3) - .3, Risks(), 4), (T('además') - .3, Criminals(), 1), (T('porque', 56.5) - .3, Illegal(), 1),
           (T('y', 62.7) - .3, Article10(), 2), (T('no', 71.7) - .3, NoCarry(), 3),
           (T('entonces') - .3, TrueQuestion(), 1), (T('méxico', 77.5) - .3, ArmsOrInst(), 3), (T('tú') - .3, Permit(), 1), (T('te', 88.8) - .3, Comments(), 3)]
    out = []
    for i, (a, sc, g) in enumerate(seq):
        b = seq[i + 1][0] if i + 1 < len(seq) else DUR; sc.a = a; out.append((a, b, sc, g))
    return out

KEYW = {'arma', 'armas', 'delincuentes', 'pistola', 'seguro', 'peligroso', 'criminales', 'armados', 'defenderse', 'problema', 'distingue', 'víctima', 'control', 'inegi,', '2025,', '70.8%',
        'homicidios', 'fuego', 'sencillo', 'protegida', 'accidentes', 'amenazas', 'enfrentamientos', 'tragedia', 'ilegalmente', 'domicilio', 'legítima', 'restricciones', 'calle',
        'pregunta', 'instituciones', 'controles', 'estrictos', 'comentarios'}

# ---------------------------------------------------------------- audio: voz de Brian + música original sintetizada + efectos discretos
def audio_plan():
    sh = tl(); st = {type(sc).__name__: a for a, b, sc, g in sh}
    secs = [(0, 'tension', 1), (st['Supporters'], 'tension', 2), (st['Inegi'], 'misterio', 2), (st['EasyBuy'], 'tension', 2), (st['Article10'], 'misterio', 1), (st['TrueQuestion'], 'esperanza', 1)]
    ef = [[0, 'boom', .7], [.2, 'latido', .3]]
    for a, b, sc, g in sh[1:]: ef += [[a - .25, 'whoosh', .22]]
    W_ = lambda w, after=-1: T(w, after)
    ef += [[W_('pistola'), 'impacto', .3], [W_('seguro') - .1, 'ding', .15], [W_('peligroso') - .1, 'impacto', .35], [W_('criminales'), 'impacto', .3], [W_('defenderse', 15), 'pop', .12],
           [W_('delincuente'), 'pop', .12], [W_('víctima'), 'pop', .12], [W_('persona', 24), 'pop', .12], [W_('menor') , 'latido', .35], [W_('setenta') - .1, 'riser', .14, 1.4],
           [W_('armas', 37) , 'boom', .55], [W_('sencillo', 41), 'ding', .15], [W_('protegida'), 'ding', .15], [W_('accidentes'), 'impacto', .3], [W_('amenazas'), 'impacto', .3],
           [W_('enfrentamientos'), 'impacto', .3], [W_('tragedia'), 'boom', .5], [W_('criminales', 54), 'latido', .35], [W_('ilegalmente') - .3, 'impacto', .35],
           [W_('reconoce') - .2, 'whoosh', .3], [W_('domicilio'), 'ding', .15], [W_('calle'), 'impacto', .35], [W_('pregunta'), 'latido', .35],
           [W_('armados'), 'pop', .12], [W_('instituciones'), 'pop', .12], [W_('controles') - .4, 'beep', .08], [W_('controles') - .15, 'beep', .08], [W_('estrictos') - .1, 'beep', .08],
           [W_('comentarios') + .4, 'ding', .25]]
    return secs, sorted(ef, key=lambda e: e[0])
def synth_all(path):
    secs, ef = audio_plan(); src = CH._src
    a = src.index('secs = ['); b = src.index(']', src.index("1)]", a)) + 1; src = src[:a] + 'secs = ' + repr(secs) + src[b:]
    a = src.index('    EF = ['); b = src.index(']]', a) + 2; src = src[:a] + '    EF = ' + repr(ef) + src[b:]
    src = src.replace("env / (env.max() * .25)", "env / (env.max() * .25 + 1e-9)").replace("duck = 1 - .55 * env", "duck = 1 - .7 * env").replace(
        "out = np.tanh((mus * .75 * duck + fx * .6 * (1 - .35 * env)) * 1.1) * .8 + vv * .92", "out = np.tanh((mus * .65 * duck + fx * .42 * (1 - .5 * env)) * 1.1) * .7 + vv * .95")
    g = dict(globals()); g.update(EMOJIS=[], DUR=DUR, VOZ=VOZ, OUT=OUTA); exec(src, g); g['synth_audio'](path)

def make_frame():
    NV.TR.DUR = DUR; NV.TR.KEY = KEYW
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in NV.TR.build_subs(WDISP)]
    shots = tl()
    def one(i, T_):
        a, b, sc, g = shots[i]; CTX['shot'] = i; CTX['counts'] = {}
        return cinema(render3d(sc, T_ - a, b - a, T_), g, T_)
    def frame(T_, f=-1, rec=False):
        CTX['f'], CTX['rec'] = f, rec
        i = max(k for k, s_ in enumerate(shots) if T_ >= s_[0] - 1e-6)
        a = shots[i][0]; prev = None
        if i > 0 and T_ - a < .3:
            rec = CTX['rec']; CTX['rec'] = False; PENDING.clear(); prev = one(i - 1, T_); paint_pending(prev); CTX['rec'] = rec
        PENDING.clear(); fr = one(i, T_); paint_pending(fr)
        if prev is not None: CTX['rec'] = False; fr = cv2.addWeighted(prev, 1 - ss(0, .3, T_ - a), fr, ss(0, .3, T_ - a), 0)
        clean = fr.copy(); draw_overlays(fr, T_, subs, []); return fr, clean, i
    return frame, shots

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'info'
    frame, shots = make_frame()
    if mode == 'info':
        for i, (a, b, sc, g) in enumerate(shots): print(f'{i:2d} {a:6.2f}-{b:6.2f} {b - a:5.2f} {type(sc).__name__}')
    elif mode == 'test':
        os.makedirs(f'{OUTA}/test', exist_ok=True)
        for T_ in [float(x) for x in sys.argv[2:]]: cv2.imwrite(f'{OUTA}/test/n_{T_:06.2f}.jpg', cv2.resize(frame(T_)[0], (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1])
    elif mode in ('seg', 'qcshot'):
        if mode == 'seg': f0, f1 = int(sys.argv[2]), int(sys.argv[3]); tag_ = f'{f0:05d}'; D_ = OUTA
        else: i = int(sys.argv[2]); f0, f1 = int(math.ceil(shots[i][0] * FPS)), int(math.ceil(shots[i][1] * FPS)); tag_ = f'shot{i:02d}'; D_ = f'{OUTA}/iter'
        os.makedirs(f'{D_}/thumbs', exist_ok=True); p = None
        if mode == 'seg':
            p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', f'{OUTA}/seg_{f0:05d}.mp4'], stdin=subprocess.PIPE)
        diffs = {}; prev = None
        if f0 > 0: prev = cv2.resize(frame((f0 - 1) / FPS)[1], (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
        CTX['log'] = []
        for f in range(f0, f1):
            fr, clean, si = frame(f / FPS, f, True); small = cv2.resize(clean, (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
            if prev is not None: diffs[f] = float(np.abs(small - prev).mean())
            prev = small
            if f % 3 == 0: cv2.imwrite(f'{D_}/thumbs/t_{f:05d}.jpg', cv2.resize(clean, (180, 320), interpolation=cv2.INTER_AREA)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 80])
            if p: p.stdin.write(np.ascontiguousarray(fr).tobytes())
        if p: p.stdin.close(); p.wait()
        json.dump(dict(log=CTX['log'], diffs=diffs, f0=f0, f1=f1), open(f'{D_}/qc_{tag_}.json', 'w'))
        print('SEG' if mode == 'seg' else 'QCSHOT', f0, f1, flush=True)
    elif mode == 'audio': synth_all(f'{OUTA}/audio.wav'); print('audio ok')

if __name__ == '__main__': main()
