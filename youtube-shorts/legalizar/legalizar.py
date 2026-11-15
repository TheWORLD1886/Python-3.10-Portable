#!/usr/bin/env python3
# Short NEON: ¿QUÉ PASARÍA SI MÉXICO LEGALIZARA TODAS LAS DROGAS? · escenario hipotético · 1080x1920 · 30 fps.
# Tres tipos de plano (directiva NEON): DOCUMENTAL (fotos/videos reales con licencia libre, ver material.json y FUENTES.md),
# NARRATIVO (stickmans del rig compartido) y COMBINADO (stickmans sobre fondos reales). Toda imagen real lleva etiqueta
# «IMAGEN REAL» y crédito; toda escena con stickmans lleva «RECREACIÓN». Sin cifras inventadas: la única tabla mostrada
# es la del art. 479 de la Ley General de Salud (texto vigente en diputados.gob.mx).
import os, sys, json, math, subprocess
HERE_L = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE_L, '..', 'nvidia'))
import nvidia2 as N2
from nvidia2 import *
NV = N2.NV; RG = N2.RG; CTX = N2.CTX
OUTL = os.path.join(HERE_L, 'out'); os.makedirs(OUTL, exist_ok=True)
WORDS = json.load(open(os.path.join(HERE_L, 'words.json')))
MAT = {m['id']: m for m in json.load(open(os.path.join(HERE_L, 'material.json')))}
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
    im = cv2.imread(os.path.join(HERE_L, MAT[i]['archivo']))[:, :, ::-1]
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
        cap = cv2.VideoCapture(os.path.join(HERE_L, MAT[i]['archivo'])); s.fps = cap.get(cv2.CAP_PROP_FPS) or 30.; n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
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

# ================================================================ GANCHO
PILL_CHIPS = [chip(n, (255, 120, 90) if n == 'FENTANILO' else (255, 210, 90), w=560) for n in ('COCAÍNA', 'HEROÍNA', 'METANFETAMINA', 'FENTANILO')]
class Hook(VidDoc):                                 # ¿qué pasaría si mañana México legalizara...? (Zócalo, timelapse real)
    def __init__(s):
        VidDoc.__init__(s, 329, fx=.42, z=(1.0, 1.08), speed=.9)
        s.t1 = big('¿Y SI MÉXICO', 84); s.t2 = big('LEGALIZARA', 84, (255, 220, 120), glow=(255, 120, 30)); s.t3 = big('TODAS LAS DROGAS?', 84)
    def extra(s, fr, t, d):
        for k, (sp, y) in enumerate(((s.t1, 560), (s.t2, 660), (s.t3, 760))): pop(fr, sp, 540, y, t, .1 + k * .2)
        for k, wd in enumerate(('cocaína', 'heroína')): pop(fr, PILL_CHIPS[k], 540, 920 + k * 120, t, s.w(wd) - .1)
        hipo(fr, 330, ss(.8, 1.2, t))
class Pills(Doc):                                   # la cocaína, la heroína, la metanfetamina y hasta el fentanilo (decomiso real de la CBP)
    def __init__(s):
        Doc.__init__(s, 71, fx=.55, fy=.5, z=(1.15, 1.02), dark_=.15)
        s.items = [('cocaína', 'COCAÍNA'), ('heroína', 'HEROÍNA'), ('metanfetamina', 'METANFETAMINA'), ('fentanilo', 'FENTANILO')]
        s.chips = PILL_CHIPS
        s.note = label('Pastillas de fentanilo decomisadas · Nogales, Arizona · 2023', 24, (230, 230, 236))
    def extra(s, fr, t, d):
        for k, (wd, _) in enumerate(s.items): pop(fr, s.chips[k], 540, 620 + k * 120, t, T(wd, 1.5) - s.a - .1)
        blit(fr, s.note, 540, 1340, ss(.3, .7, t))
class Boss(Sl):                                     # los cárteles podrían perder miles de millones (recreación)
    grade = 4
    def __init__(s):
        s.back = NV.stage_bg(11, (12, 8, 6), (200, 140, 60)); s.main = ground(1560, (26, 18, 14), 1.)
        s.front = [(bokeh_layer(8, (255, 200, 120), 811, ymin=300, ymax=1100), 1.7)]; s.p = red_panel('PODRÍAN PERDER MILES DE MILLONES', w=900, h=150)
    def draw(s, fr, t, d):
        x, fy, h = 420, 1720, 760; u = U('capo', h); desk(fr, 520, 1040, 1420)
        n = max(2, int(lerp(9, 2, ss(s.w('perder'), s.w('pesos') + .3, t))))
        money_stack(fr, 676, 1418, n); money_stack(fr, 836, 1418, max(1, n - 2))
        tp = s.w('perder'); hd = (x + 1.3 * u, fy - 5.0 * u)
        keys = [(0, P(look=(.5, .35), frown=.1, boca='sonrisa', grip={'R': (664, 1300, 1.)}, tz=.6)),
                (tp, P(look=(.5, .4), frown=.15, grip={'R': (664, 1300, 1.)}, tz=.6)),
                (tp + .6, P(look=(.45, .3), frown=.6, brow_asym=.3, boca='tensa', lean=.03, grip={'R': (660, 1330, 1.), 'L': (x - .4 * u, fy - 4.6 * u, 1.)}, tz=.6)),
                (d, P(look=(.2, .1), frown=.75, boca='tensa', sh=.1, grip={'R': hd + (1.,), 'L': (x - .9 * u, fy - 4.4 * u, 1.)}, tz=.7))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 81)
        RG.person_34(fr, 'capo', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        float_in(fr, s.p, 540, 400, t, .1); draw_tag(fr, 'rec'); hipo(fr, 290)
    def cam(s, t, d): return lerp(1.04, 1.12, RG.ease(t / d)), 560, 1300, 0, 0
class HealthCrisis(Comb):                           # crisis de salud pública sin precedentes (hospital IMSS real de fondo)
    def __init__(s):
        Comb.__init__(s, 190, fx=.45, gy=1600, dark_=.42); s.p = red_panel('CRISIS DE SALUD PÚBLICA', w=820, h=150)
    def draw(s, fr, t, d):
        fy, h = 1730, 720; x0 = snap(-160, 'doctora', h); x1 = snap(560, 'doctora', h); u = U('doctora', h); tw = 1.8
        a = .5 + .5 * math.sin(t * 6); ov = fr.copy(); cv2.rectangle(ov, (0, 0), (W, H), (200, 30, 30), -1); fr[:] = cv2.addWeighted(fr, 1 - .12 * a, ov, .12 * a, 0)
        if t < tw: walk(fr, 'doctora', x0, x1, -.3, tw, fy, h, t, look=(.5, .1), frown=.3)
        else:
            keys = [(tw, P(look=(.3, .1), frown=.35)), (tw + 1.1, P(look=(0, .05), frown=.5, brow_up=.6, boca='tensa', grip={'L': (x1 - 1.0 * u, fy - 7.2 * u, 1.)}, tz=.5)),
                    (d, P(look=(-.1, .05), frown=.55, brow_up=.6, boca='tensa', grip={'L': (x1 - 1.0 * u, fy - 7.1 * u, 1.)}, tz=.5))]
            def j34(f_): p = RG.anim(keys, t); p['blink'] = blinkp(t, 82); return RG.person_34(f_, 'doctora', x1, fy, h, p, t, feet=stance(x1, u, fy), turn=-1)[0]
            if t < tw + .2: turn_blend(fr, (t - tw) / .2, lambda f_: walk(f_, 'doctora', x0, x1, -.3, tw, fy, h, tw, look=(.5, .1), frown=.3), j34)
            else: j34(fr)
        float_in(fr, s.p, 540, 420, t, .2); s.tags(fr)
class Dilemma(Doc):                                 # ¿principio del fin del narcotráfico o error histórico? (Palacio Nacional real)
    def __init__(s):
        Doc.__init__(s, 6, fx=.5, fy=.45, z=(1.0, 1.1), dark_=.35, warm=.04)
        s.a1 = gold_panel('¿EL FIN DEL', 'NARCOTRÁFICO?', w=760, h=170); s.a2 = red_panel('¿O UN ERROR', 'HISTÓRICO?', w=760, h=170)
    def extra(s, fr, t, d):
        pop(fr, s.a1, 540, 700, t, s.w('principio') - .2); pop(fr, s.a2, 540, 920, t, s.w('error') - .2)
        k = ss(s.w('error') + .2, s.w('error') + .8, t); x = 540; y = 1180                         # balanza
        if k > 0:
            tilt = .12 * math.sin(t * 2.2); line(fr, (x, y - 20), (x, y + 140), (230, 220, 200), 8)
            a = (x - 220, y - 20 + 220 * tilt); b = (x + 220, y - 20 - 220 * tilt); line(fr, a, b, (230, 220, 200), 8)
            for q, c in ((a, (255, 210, 90)), (b, (255, 90, 80))): cv2.ellipse(fr, (int(q[0]), int(q[1] + 60)), (80, 26), 0, 0, 180, c, -1, cv2.LINE_AA); line(fr, q, (q[0], q[1] + 60), (230, 220, 200), 3)

# ================================================================ LOS CÁRTELES
class License(Comb):                                # producir y vender bajo licencias, controles e impuestos (Cámara de Diputados de fondo)
    def __init__(s):
        Comb.__init__(s, 22, fx=.5, fy=.4, gy=1600, dark_=.5)
        s.c = [chip(x, (150, 230, 255), w=440) for x in ('LICENCIAS', 'CONTROLES', 'IMPUESTOS')]
    def draw(s, fr, t, d):
        x, fy, h = 470, 1730, 740; u = U('funcionaria', h); desk(fr, 560, 1060, 1420, (60, 50, 44))
        tst = s.w('licencias') - .1; doc = (650, 1410)
        keys = [(0, P(look=(.4, .3), grip={'R': (doc[0] - 40, doc[1], 1.)}, tz=.6)),
                (tst - .9, P(look=(.45, .4), lean=.03, grip={'R': (doc[0] + 30, doc[1] - 140, 1.)}, tz=.6)),                 # levanta el sello
                (tst, P(look=(.45, .45), lean=.05, frown=.1, grip={'R': (doc[0] + 30, doc[1] - 20, 1.)}, tz=.6)),                 # sella
                (tst + .9, P(look=(.3, .3), grip={'R': (doc[0] + 30, doc[1] - 110, 1.)}, tz=.6)),
                (s.w('impuestos'), P(look=(.1, .05), boca='sonrisa', grip={'R': (x + 1.2 * u, fy - 5.4 * u, 1.), 'L': (x - 1.1 * u, fy - 5.0 * u, 1.)}, tz=.7)),
                (d, P(look=(.05, .05), boca='sonrisa', grip={'R': (x + 1.25 * u, fy - 5.5 * u, 1.), 'L': (x - 1.1 * u, fy - 5.0 * u, 1.)}, tz=.7))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 91)
        license_doc(fr, (doc[0], doc[1] + 50), ss(tst, tst + .2, t))
        hands, _ = RG.person_34(fr, 'funcionaria', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        if t < s.w('impuestos') - .3:
            hd = hands['R']; cv2.rectangle(fr, (int(hd[0] - 16), int(hd[1] + 6)), (int(hd[0] + 16), int(hd[1] + 30)), (150, 40, 40), -1); hands_on_top(fr, {'R': hd}, 'funcionaria', h)
        for k, wd in enumerate(('licencias', 'controles', 'impuestos')): pop(fr, s.c[k], 540, 560 + k * 110, t, s.w(wd) - .1)
        s.tags(fr)
class Markets(Sl):                                  # de mercados clandestinos a venta legal (recreación)
    grade = 2
    def __init__(s):
        s.back = NV.stage_bg(12, (8, 10, 18), (90, 120, 200)); s.main = ground(1560, (20, 22, 30), 1.); s.front = []
        s.c1 = label('MERCADO CLANDESTINO', 28, (255, 140, 120)); s.c2 = label('VENTA REGULADA', 30, (140, 240, 170))
    def draw(s, fr, t, d):
        sw = s.w('legalmente') - .9; k = ss(sw, sw + .8, t)
        # mitad izquierda: callejón oscuro; mitad derecha: mostrador iluminado (se enciende al decir «legalmente»)
        cv2.rectangle(fr, (0, 600), (530, 1560), (16, 16, 22), -1); cv2.rectangle(fr, (40, 700), (160, 1560), (26, 26, 34), -1)
        lit = tuple(int(lerp(30, c, k)) for c in (236, 240, 246)); cv2.rectangle(fr, (550, 600), (W, 1560), lit, -1)
        sign(fr, 815, 720, 420, 90, 'TIENDA AUTORIZADA', (int(lerp(40, 30, k)), int(lerp(40, 120, k)), int(lerp(46, 80, k))))
        counter(fr, 600, 1040, 1250, tuple(int(lerp(50, c, k)) for c in (190, 196, 210)))
        fy, h = 1720, 660
        u = U('pandillero' if False else 'peaton2', h)
        p = P(look=(-.4, .2), frown=.4, sh=.15, hip_dx=.03 * math.sin(t * 1.3), blink=blinkp(t, 92))     # vendedor en la sombra, mira a los lados
        p['look'] = (-.4 + .8 * ss(.5, 1.0, t % 3), .2)
        RG.person_34(fr, 'peaton2', 260, fy, h, p, t, feet=stance(260, u, fy), turn=1)
        ov = fr.copy(); cv2.rectangle(ov, (0, 0), (530, H), (0, 0, 0), -1); fr[:] = cv2.addWeighted(fr, .55, ov, .45, 0)
        uc = U('ejecutivo', h); pc = RG.anim([(0, P(look=(-.2, .1))), (sw + .4, P(look=(-.2, .1))), (sw + 1.2, P(look=(-.2, .1), boca='sonrisa', frown=-.2, grip={'R': (820 + 1.2 * uc, fy - 5.6 * uc, 1.)}, tz=.6)), (d + 1, P(look=(-.2, .1), boca='sonrisa', frown=-.2, grip={'R': (820 + 1.2 * uc, fy - 5.6 * uc, 1.)}, tz=.6))], t); pc['blink'] = blinkp(t, 93)
        fade_in(fr, k, lambda f_: RG.person_34(f_, 'ejecutivo', 820, fy - 40, h, pc, t, feet=stance(820, uc, fy - 40), turn=-1))
        blit(fr, s.c1, 265, 560); blit(fr, s.c2, 815, 560, k)
        draw_tag(fr, 'rec'); hipo(fr, 290)
class Compete(Sl):                                  # competir contra empresas autorizadas y perder parte del mercado (recreación)
    grade = 3
    def __init__(s):
        s.back = NV.stage_bg(13, (10, 10, 16), (120, 160, 220)); s.main = ground(1560, (20, 22, 30), 1.); s.front = []
        s.lab = label('MERCADO', 40, (255, 255, 255)); s.cp = label('CÁRTEL', 30, (255, 140, 120)); s.cl = label('EMPRESA AUTORIZADA', 26, (140, 240, 170))
    def draw(s, fr, t, d):
        cx, cy, r = 540, 900, 250; k = ss(s.w('perderían') - .3, s.w('mercado') + .2, t); legal = lerp(0., .35, k)       # porción ilustrativa, sin cifra
        cv2.circle(fr, (cx, cy), r, (180, 60, 56), -1, cv2.LINE_AA)
        if legal > 0: cv2.ellipse(fr, (cx, cy), (r, r), -90, 0, 360 * legal, (60, 170, 110), -1, cv2.LINE_AA)
        cv2.circle(fr, (cx, cy), r, (240, 240, 240), 4, cv2.LINE_AA); blit(fr, s.lab, cx, cy - r - 50)
        fy, h = 1730, 640; uk = U('capo', h); ue = U('ejecutivo', h); te = s.w('empresas') - .3
        pk = RG.anim([(0, P(look=(.3, -.2), frown=.2)), (te + .5, P(look=(.5, .05), frown=.5, brow_asym=.3)), (s.w('perderían'), P(look=(.2, -.25), frown=.7, boca='tensa', sh=.1, grip={'L': (220 - 1.2 * uk, fy - 5.2 * uk, 1.), 'R': (220 + 1.2 * uk, fy - 5.2 * uk, 1.)}, tz=.7)),
                      (d, P(look=(.2, -.25), frown=.75, boca='tensa', sh=.12, grip={'L': (220 - 1.25 * uk, fy - 5.3 * uk, 1.), 'R': (220 + 1.25 * uk, fy - 5.3 * uk, 1.)}, tz=.7))], t)
        pk['blink'] = blinkp(t, 94); RG.person_34(fr, 'capo', 220, fy, h, pk, t, feet=stance(220, uk, fy), turn=1)
        x1 = snap(860, 'ejecutivo', h); x0 = snap(1300, 'ejecutivo', h)
        if t >= te:
            if t < te + 1.4: walk(fr, 'ejecutivo', x0, x1, te, te + 1.4, fy, h, t, look=(-.5, .05))
            else:
                pe = P(look=(-.4, .05), boca='sonrisa', frown=-.2, grip={'R': (x1 + .7 * ue, fy - 4.8 * ue, 1.)}, tz=.6, blink=blinkp(t, 95))
                def j(f_): return RG.person_34(f_, 'ejecutivo', x1, fy, h, pe, t, feet=stance(x1, ue, fy), turn=-1)[0]
                if t < te + 1.6: turn_blend(fr, (t - te - 1.4) / .2, lambda f_: walk(f_, 'ejecutivo', x0, x1, te, te + 1.4, fy, h, te + 1.4, look=(-.5, .05)), j)
                else: hd = j(fr); clipboard(fr, hd['R']); hands_on_top(fr, {'R': hd['R']}, 'ejecutivo', h)
        blit(fr, s.cp, 220, 1780); blit(fr, s.cl, 820, 1780, ss(te, te + .4, t)); draw_tag(fr, 'rec'); hipo(fr, 290)
        blit(fr, label('Proporción ilustrativa, sin cifra', 22, (220, 220, 226)), 540, cy + r + 40, ss(s.w('perderían'), s.w('perderían') + .4, t))
class Fight(Sl):                                    # pero hay un problema: ¿entregarían su negocio sin pelear? (primer plano del capo)
    grade = 4
    def __init__(s):
        s.back = NV.stage_bg(14, (10, 6, 6), (220, 80, 50)); s.main = ground(1560, (20, 14, 14), 1.); s.front = [(bokeh_layer(8, (255, 120, 80), 814, ymin=200, ymax=1200), 1.7)]
        s.q = big('¿SIN PELEAR?', 90, (255, 236, 220), glow=(255, 60, 40))
    def draw(s, fr, t, d):
        x, fy, h = 540, 2050, 1150; u = U('capo', h); tq = s.w('realmente')
        keys = [(0, P(look=(0, .1), frown=.2)), (tq, P(look=(0, .05), frown=.4, brow_asym=.4)),
                (tq + .8, P(look=(0, 0), frown=.75, boca='tensa', tilt=-.04, grip={'L': (x - .2 * u, fy - 5.4 * u, 1.), 'R': (x + .2 * u, fy - 5.3 * u, 1.)}, tz=1.)),   # truena los nudillos
                (d, P(look=(0, 0), frown=.8, boca='tensa', tilt=-.05, grip={'L': (x - .15 * u, fy - 5.45 * u, 1.), 'R': (x + .25 * u, fy - 5.35 * u, 1.)}, tz=1.))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 96); RG.person(fr, 'capo', x, fy, h, p, t, feet=stance(x, u, fy))
        pop(fr, s.q, 540, 520, t, tq + .3); draw_tag(fr, 'rec'); hipo(fr, 290)
    def cam(s, t, d): return lerp(1.0, 1.1, RG.ease(t / d)), 540, 900, 0, 0
class Illegal(Doc):                                 # podrían intentar controlar la producción ilegal (decomiso real de metanfetamina, CBP)
    def __init__(s):
        Doc.__init__(s, 85, fx=.5, fy=.5, z=(1.04, 1.14), pan=(-20, 20), dark_=.3)
        s.c = red_panel('CONTROLAR LA', 'PRODUCCIÓN ILEGAL', w=760, h=170); s.note = label('Metanfetamina decomisada por la CBP · Pharr, Texas · 2017', 24, (230, 230, 236))
    def extra(s, fr, t, d): pop(fr, s.c, 540, 640, t, s.w('controlar') - .1); blit(fr, s.note, 540, 1300, ss(.3, .7, t)); hipo(fr, 316)
class Diversify(Doc):                               # intimidar, extorsión, secuestro y otros delitos (Guardia Nacional real; contexto: InSight Crime)
    def __init__(s):
        Doc.__init__(s, 50, fx=.55, fy=.5, z=(1.04, 1.14), pan=(20, -20), dark_=.25)
        s.c = [red_panel(x, w=640, h=120) for x in ('INTIMIDAR A COMPETIDORES', 'EXTORSIÓN', 'SECUESTRO', 'OTROS DELITOS')]
        s.src = label('Grupos criminales ya diversifican sus delitos (InSight Crime)', 22, (230, 230, 236))
        s.note = label('Guardia Nacional en Guadalajara · 2023', 24, (230, 230, 236))
    def extra(s, fr, t, d):
        for k, wd in enumerate(('intimidar', 'extorsión', 'secuestro', 'otros')): pop(fr, s.c[k], 540, 560 + k * 140, t, s.w(wd) - .1)
        blit(fr, s.note, 540, 1300, ss(.3, .7, t)); blit(fr, s.src, 540, 1350, ss(s.w('extorsión'), s.w('extorsión') + .4, t)); hipo(fr, 316)

# ================================================================ EL PRECIO HUMANO
class OtherSide(VidDoc):                            # ahora imagina el otro lado (Metro de la CDMX, video real)
    def __init__(s): VidDoc.__init__(s, 147, fx=.5, t0=1.0, dur=3., title='EL OTRO LADO', ty=820, z=(1.0, 1.05))
class Minors(Comb):                                 # impedir que lleguen a menores, controlar distribución, consumo problemático
    def __init__(s):
        Comb.__init__(s, 191, fx=.5, gy=1600, dark_=.55); s.c = [chip(x, (255, 210, 90), w=600) for x in ('PROHIBIR VENTA A MENORES', 'CONTROLAR LA DISTRIBUCIÓN', 'ATENDER EL CONSUMO PROBLEMÁTICO')]
        s.no = big('SOLO ADULTOS', 54, (255, 120, 100))
    def draw(s, fr, t, d):
        fy, h = 1740, 700; counter(fr, 560, 1060, 1300)
        xs = 820; us = U('ejecutivo', h); tm = s.w('menores') - .6
        ps = RG.anim([(0, P(look=(-.3, .1), blink=blinkp(t, 97))), (tm + .4, P(look=(-.45, .25), frown=.3, grip={'R': (xs - 1.45 * us, fy - 6.3 * us, 1.)}, tz=.3)),          # mano en alto: no
                      (tm + 2.4, P(look=(-.45, .25), frown=.35, grip={'R': (xs - 1.45 * us, fy - 6.4 * us, 1.)}, tz=.3)), (tm + 3.0, P(look=(-.3, .1), frown=.2)), (d, P(look=(-.3, .1), frown=.2))], t)
        ps['blink'] = blinkp(t, 97); RG.person_34(fr, 'ejecutivo', xs, fy - 60, h, ps, t, feet=stance(xs, us, fy - 60), turn=-1)
        hm = 520; um = U('menor', hm); x0, x1 = snap(-60, 'menor', hm), snap(400, 'menor', hm); ta = tm - 3.0
        if t < ta + 1.4: walk(fr, 'menor', x0, x1, ta - 1.2, ta + 1.4, fy, hm, t, look=(.5, -.1), mode='suave')
        else:
            pm = RG.anim([(ta + 1.4, P(look=(.5, -.2))), (tm + .4, P(look=(.5, -.3), grip={'R': (x1 + 1.4 * um, fy - 5.2 * um, 1.)}, tz=.4)),
                          (tm + 1.2, P(look=(.4, -.25), frown=-.3, brow_up=.5, boca='triste')), (d, P(look=(.2, -.1), frown=-.3, boca='triste', sh=-.2))], t)
            pm['blink'] = blinkp(t, 98)
            def j(f_): return RG.person_34(f_, 'menor', x1, fy, hm, pm, t, feet=stance(x1, um, fy), turn=1)[0]
            if t < ta + 1.6: turn_blend(fr, (t - ta - 1.4) / .2, lambda f_: walk(f_, 'menor', x0, x1, ta - 1.2, ta + 1.4, fy, hm, ta + 1.4, look=(.5, -.1), mode='suave'), j)
            else: j(fr)
        pop(fr, s.no, 820, 1150, t, tm + .4)
        for k, wd in enumerate(('menores', 'distribución', 'consecuencias')): pop(fr, s.c[k], 540, 520 + k * 110, t, s.w(wd) - .1)
        s.tags(fr)
class Risks(Sl):                                    # sustancias con riesgos muy diferentes (gráfico; sin ordenar ni puntuar)
    grade = 2
    def __init__(s):
        s.back = NV.stage_bg(15, (8, 10, 18), (120, 120, 200)); s.main = np.zeros((H, W, 4), np.uint8); s.front = []
        s.t = big('RIESGOS MUY DIFERENTES', 66, (255, 236, 200)); s.c = [chip(x, (230, 230, 240), w=430) for x in ('COCAÍNA', 'HEROÍNA', 'METANFETAMINA', 'FENTANILO')]
        s.n = label('Cada sustancia tiene efectos y riesgos distintos', 26, (220, 220, 230))
    def draw(s, fr, t, d):
        pop(fr, s.t, 540, 560, t, .1)
        for k in range(4):
            x, y = (300, 780)[k % 2], (860, 1120)[k // 2]; pop(fr, s.c[k], x, y, t, .3 + k * .15)
            kk = ss(.6 + k * .15, 1.0 + k * .15, t)
            if kk > 0:                                                                  # señal de advertencia
                c = (x, y - 120); r = 46 * kk; poly(fr, [(c[0], c[1] - r), (c[0] + r, c[1] + .8 * r), (c[0] - r, c[1] + .8 * r)], (255, 200, 60))
                line(fr, (c[0], c[1] - .35 * r), (c[0], c[1] + .3 * r), (30, 30, 30), 6); circ(fr, (c[0], c[1] + .55 * r), 4, (30, 30, 30))
        blit(fr, s.n, 540, 1300, ss(.8, 1.2, t)); draw_tag(fr, 'rec')
class Fentanyl(Doc):                                # una sobredosis de opioides como el fentanilo puede ser mortal (decomiso real; dato de la OMS)
    def __init__(s):
        Doc.__init__(s, 64, fx=.5, z=(1.0, 1.12), dark_=.3)
        s.p = red_panel('SOBREDOSIS DE OPIOIDES:', 'PUEDE SER MORTAL', w=860, h=180); s.who = label('OMS: el fentanilo es 50 a 100 veces más potente que la morfina', 24, (255, 255, 255))
        s.note = label('Fentanilo decomisado por la CBP · Nogales, Arizona · 2019', 24, (230, 230, 236))
    def extra(s, fr, t, d):
        pop(fr, s.p, 540, 700, t, s.w('mortal') - .6); blit(fr, s.who, 540, 860, ss(s.w('mortal'), s.w('mortal') + .4, t)); blit(fr, s.note, 540, 1300, ss(.2, .6, t))
class Hospitals(Comb):                              # sin hospitales preparados, prevención y tratamiento: grave problema (hospital IMSS real)
    def __init__(s):
        Comb.__init__(s, 187, fx=.5, gy=1600, dark_=.5)
        s.items = [('hospitales', 'HOSPITALES PREPARADOS'), ('prevención', 'PREVENCIÓN'), ('tratamientos', 'TRATAMIENTO DE ADICCIONES')]
        s.c = [chip(x, (230, 230, 240), w=620) for _, x in s.items]; s.p = red_panel('GRAVE PROBLEMA DE SALUD PÚBLICA', w=880, h=140)
    def draw(s, fr, t, d):
        fy, h = 1740, 720; x = 760; u = U('medico', h); tp = s.w('grave')
        keys = [(0, P(look=(-.4, .1), frown=.2)), (s.w('hospitales'), P(look=(-.45, -.2), frown=.3, grip={'L': (x - 1.4 * u, fy - 6.0 * u, 1.)}, tz=.5)),   # señala la lista
                (s.w('tratamientos') + .3, P(look=(-.45, -.25), frown=.45, grip={'L': (x - 1.5 * u, fy - 6.4 * u, 1.)}, tz=.5)),
                (tp, P(look=(0, .05), frown=.6, brow_up=.5, boca='tensa', sh=.05)), (d, P(look=(0, .05), frown=.65, brow_up=.5, boca='tensa'))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 99); RG.person_34(fr, 'medico', x, fy, h, p, t, feet=stance(x, u, fy), turn=-1)
        for k, (wd, _) in enumerate(s.items):
            y = 600 + k * 120; t0 = s.w(wd) - .1; pop(fr, s.c[k], 420, y, t, t0)
            kx = ss(t0 + .5, t0 + .8, t)                                                           # casilla vacía: falta
            if kx > 0: cv2.rectangle(fr, (110, y - 30), (170, y + 30), (255, 255, 255), 4); line(fr, (118, y - 22), (118 + 44 * kx, y - 22 + 44 * kx), (255, 70, 60), 7); line(fr, (162, y - 22), (162 - 44 * kx, y - 22 + 44 * kx), (255, 70, 60), 7)
        pop(fr, s.p, 540, 1010, t, tp - .2); s.tags(fr)

# ================================================================ EL GOBIERNO
class Challenge(Doc):                               # y aquí aparece el mayor desafío (Palacio Nacional real)
    def __init__(s): Doc.__init__(s, 6, fx=.62, fy=.4, z=(1.12, 1.02), dark_=.3, title='EL MAYOR DESAFÍO', ty=760)
class Inspect(Sl):                                  # vigilar laboratorios, empresas, distribuidores y puntos de venta (recreación)
    grade = 2
    def __init__(s):
        s.back = NV.stage_bg(16, (10, 12, 20), (80, 160, 220)); s.main = ground(1560, (22, 24, 32), 1.); s.front = []
        s.items = [('laboratorios', 'LABORATORIOS', (60, 110, 160)), ('empresas', 'EMPRESAS', (70, 120, 90)), ('distribuidores', 'DISTRIBUIDORES', (140, 100, 60)), ('puntos', 'PUNTOS DE VENTA', (120, 70, 110))]
        s.t = gold_panel('SISTEMA DE VIGILANCIA', w=760, h=130)
    def draw(s, fr, t, d):
        fy, h = 1740, 600; u = U('inspector', h)
        for k, (wd, n, c) in enumerate(s.items):
            x = 150 + k * 260; cv2.rectangle(fr, (x - 110, 1060), (x + 110, 1560), c, -1); cv2.rectangle(fr, (x - 110, 1060), (x + 110, 1560), dark(c, .6), 4)
            for q in range(3): cv2.rectangle(fr, (x - 80 + q * 56, 1120), (x - 40 + q * 56, 1180), (230, 230, 200), -1)
            cv2.rectangle(fr, (x - 36, 1440), (x + 36, 1560), dark(c, .5), -1); sign(fr, x, 1010, 236, 60, n, (24, 26, 34), fs=.75)
            kk = ss(s.w(wd), s.w(wd) + .3, t)
            if kk > 0: circ(fr, (x + 80, 1110), 30 * kk, (60, 200, 110)); line(fr, (x + 66, 1110), (x + 78, 1124), (255, 255, 255), 5); line(fr, (x + 78, 1124), (x + 98, 1098), (255, 255, 255), 5)
        x0 = snap(80, 'inspector', h); x1 = snap(900, 'inspector', h)
        xi = walk(fr, 'inspector', x0, x1, .2, s.w('puntos') + .4, fy, h, t, look=(.5, -.05), mode='suave', grip={'R': (0, 0, 0.)}) if t < s.w('puntos') + .4 else None
        if xi is None:
            pi = P(look=(-.3, .05), frown=.1, grip={'R': (x1 + .7 * u, fy - 4.9 * u, 1.)}, tz=.6, blink=blinkp(t, 100))
            def j(f_): return RG.person_34(f_, 'inspector', x1, fy, h, pi, t, feet=stance(x1, u, fy), turn=-1)[0]
            tt = s.w('puntos') + .4
            if t < tt + .2: turn_blend(fr, (t - tt) / .2, lambda f_: walk(f_, 'inspector', x0, x1, .2, tt, fy, h, tt, look=(.5, -.05), mode='suave'), j)
            else: hd = j(fr); clipboard(fr, hd['R']); hands_on_top(fr, {'R': hd['R']}, 'inspector', h)
        float_in(fr, s.t, 540, 420, t, .1); draw_tag(fr, 'rec'); hipo(fr, 290)
    def cam(s, t, d): k = RG.ease(t / d); return 1.06, 540, 1300, lerp(80, -80, k), 0
class Corruption(Sl):                               # combatir la corrupción para que el crimen no se apodere del mercado legal (recreación)
    grade = 4
    def __init__(s):
        s.back = NV.stage_bg(17, (12, 8, 8), (200, 120, 60)); s.main = ground(1560, (22, 18, 16), 1.); s.front = [(bokeh_layer(6, (255, 200, 140), 817, ymin=300, ymax=1100), 1.7)]
        s.p = red_panel('COMBATIR LA CORRUPCIÓN', w=800, h=140); s.no = big('NO', 120, (255, 90, 80), glow=(255, 40, 30))
    def draw(s, fr, t, d):
        fy, h = 1740, 720; xc, xi = 330, 760; uc = U('capo', h); ui = U('inspector', h); te = s.w('corrupción') - .4; tr = s.w('evitar')
        env_out = (xc + 2.1 * uc, fy - 5.2 * uc)
        pc = RG.anim([(0, P(look=(.5, .1), boca='sonrisa', frown=-.1)), (te, P(look=(.5, .1), boca='sonrisa', lean=.05, grip={'R': env_out + (1.,)}, tz=.9)),
                      (tr, P(look=(.5, .1), boca='sonrisa', lean=.05, grip={'R': env_out + (1.,)}, tz=.9)),
                      (tr + .6, P(look=(.5, .1), frown=.6, boca='tensa', grip={'R': (xc + .8 * uc, fy - 4.6 * uc, 1.)}, tz=.6)), (d, P(look=(.45, .1), frown=.7, boca='tensa', grip={'R': (xc + .8 * uc, fy - 4.6 * uc, 1.)}, tz=.6))], t)
        pc['blink'] = blinkp(t, 101); hc, _ = RG.person_34(fr, 'capo', xc, fy, h, pc, t, feet=stance(xc, uc, fy), turn=1)
        pi = RG.anim([(0, P(look=(-.4, .1))), (te + .4, P(look=(-.45, .3), frown=.3)), (tr - .2, P(look=(-.4, .1), frown=.5, brow_asym=.3)),
                      (tr + .6, P(look=(-.4, .05), frown=.7, grip={'R': (xi - 1.45 * ui, fy - 5.7 * ui, 1.)}, tz=.4)), (d, P(look=(-.4, .05), frown=.7, grip={'R': (xi - 1.45 * ui, fy - 5.7 * ui, 1.)}, tz=.4))], t)
        pi['blink'] = blinkp(t, 102); RG.person_34(fr, 'inspector', xi, fy, h, pi, t, feet=stance(xi, ui, fy), turn=-1)
        if te - .1 < t < tr + .6: envelope(fr, hc['R']); hands_on_top(fr, {'R': hc['R']}, 'capo', h)
        float_in(fr, s.p, 540, 420, t, .1); pop(fr, s.no, 760, 760, t, tr + .2); draw_tag(fr, 'rec'); hipo(fr, 290)
    def cam(s, t, d): return lerp(1.05, 1.12, RG.ease(t / d)), 540, 1300, 0, 0
class USA(Doc):                                     # ¿y qué pasaría con Estados Unidos? (muro fronterizo real, Tijuana)
    def extra(s, fr, t, d): blit(fr, s.note, 540, 1300, ss(.2, .6, t))
    def __init__(s):
        Doc.__init__(s, 104, fx=.4, fy=.5, z=(1.0, 1.1), pan=(30, -30), dark_=.2, title='¿Y ESTADOS UNIDOS?', ty=720)
        s.note = label('Muro fronterizo en Tijuana, Baja California · 2017', 24, (230, 230, 236))
class Border(Doc):                                  # una frontera con uno de los mayores mercados de drogas del mundo (placa real, San Ysidro)
    def __init__(s):
        Doc.__init__(s, 115, fx=.5, fy=.5, z=(1.02, 1.12), dark_=.35)
        s.p = gold_panel('FRONTERA CON UNO DE LOS', 'MAYORES MERCADOS DE DROGAS', w=900, h=180); s.src = label('Fuente: UNODC, Informe Mundial sobre las Drogas', 22, (230, 230, 236))
        s.note = label('Placa del límite internacional · San Ysidro · 2019', 24, (230, 230, 236))
    def extra(s, fr, t, d):
        pop(fr, s.p, 540, 640, t, s.w('mayores') - .3); blit(fr, s.src, 540, 780, ss(s.w('mercados'), s.w('mercados') + .4, t)); blit(fr, s.note, 540, 1300, ss(.2, .6, t))
class Tensions(Doc):                                # tensiones legales, comerciales y diplomáticas (reunión real de seguridad, archivo)
    def __init__(s):
        Doc.__init__(s, 262, fx=.55, fy=.45, z=(1.04, 1.14), pan=(-20, 20), dark_=.3)
        s.c = [chip(x, (255, 160, 110), w=560) for x in ('TENSIONES LEGALES', 'COMERCIALES', 'DIPLOMÁTICAS')]
        s.note = label('Archivo: reunión de seguridad México–EE. UU. · dic. 2023', 22, (230, 230, 236))
    def extra(s, fr, t, d):
        for k, wd in enumerate(('legales', 'comerciales', 'diplomáticas')): pop(fr, s.c[k], 540, 560 + k * 120, t, s.w(wd) - .1)
        blit(fr, s.note, 540, 1300, ss(.2, .6, t))

# ================================================================ EL GIRO
class NotSame(Sl):                                  # legalizar no es lo mismo que despenalizar (gráfico explicativo)
    grade = 2
    def __init__(s):
        s.back = NV.stage_bg(18, (8, 10, 18), (200, 170, 90)); s.main = np.zeros((H, W, 4), np.uint8); s.front = []
        s.pa = gold_panel('LEGALIZAR', 'permitir producir y vender', w=760, h=180); s.pb = N.holo_panel(760, 180, 'DESPENALIZAR', 'no castigar penalmente ciertas conductas')
        s.ne = big('≠', 130, (255, 255, 255)) if False else big('NO ES IGUAL', 64, (255, 236, 200))
    def draw(s, fr, t, d):
        pop(fr, s.pa, 540, 640, t, s.w('legalizar') - .1); pop(fr, s.ne, 540, 840, t, s.w('lo') - .1); pop(fr, s.pb, 540, 1040, t, s.w('despenalizar') - .1); draw_tag(fr, 'rec')
class Law(Comb):                                    # México ya contempla cantidades pequeñas para consumo personal (Ley General de Salud, art. 478-479)
    grade = 2
    def __init__(s):
        Comb.__init__(s, 21, fx=.5, fy=.4, gy=1900, dark_=.6, blur=4.)
        s.h1 = label('LEY GENERAL DE SALUD · ARTS. 478 Y 479', 30, (255, 230, 170))
        s.rows = [('Cocaína', '500 mg'), ('Heroína', '50 mg'), ('Metanfetamina', '40 mg'), ('Mariguana', '5 g')]
        s.src = label('Fuente: Cámara de Diputados, texto vigente de la Ley General de Salud', 20, (230, 230, 236))
        s.p = N.holo_panel(880, 150, 'NO SE EJERCE ACCIÓN PENAL', 'por estas cantidades para consumo personal', col=(150, 240, 90), fill=(16, 50, 10, 190))
    def draw(s, fr, t, d):
        k = ss(.1, .6, t); y0 = int(lerp(2100, 560, eOut(k)))                                     # el documento sube desde fuera del cuadro
        x0, x1 = 160, 920; cv2.rectangle(fr, (x0, y0), (x1, y0 + 620), (244, 238, 222), -1); cv2.rectangle(fr, (x0, y0), (x1, y0 + 620), (150, 140, 120), 3)
        cv2.putText(fr, 'Tabla de Orientacion de Dosis Maximas', (x0 + 40, y0 + 70), cv2.FONT_HERSHEY_DUPLEX, .9, (40, 40, 50), 2, cv2.LINE_AA)
        cv2.putText(fr, 'de Consumo Personal e Inmediato', (x0 + 40, y0 + 110), cv2.FONT_HERSHEY_DUPLEX, .9, (40, 40, 50), 2, cv2.LINE_AA)
        for q, (n, v) in enumerate(s.rows):
            y = y0 + 190 + q * 90; kk = ss(s.w('determinadas') + q * .25, s.w('determinadas') + q * .25 + .3, t)
            cv2.line(fr, (x0 + 30, y + 30), (x1 - 30, y + 30), (200, 190, 170), 2)
            if kk > 0:
                ov = fr.copy(); cv2.putText(ov, n, (x0 + 50, y + 10), cv2.FONT_HERSHEY_DUPLEX, 1.2, (30, 30, 40), 2, cv2.LINE_AA); cv2.putText(ov, v, (x1 - 230, y + 10), cv2.FONT_HERSHEY_DUPLEX, 1.2, (150, 30, 30), 2, cv2.LINE_AA)
                fr[:] = cv2.addWeighted(fr, 1 - kk, ov, kk, 0)
        blit(fr, s.h1, 540, 490, k); pop(fr, s.p, 540, 1290, t, s.w('sanciones') - .3); blit(fr, s.src, 540, 1400, ss(.6, 1., t))
        draw_tag(fr, 'rec'); credit(fr, s.i)
class NoSale(Sl):                                   # eso no autoriza vender libremente (recreación)
    grade = 3
    def __init__(s):
        s.back = NV.stage_bg(19, (10, 10, 16), (200, 80, 80)); s.main = ground(1560, (22, 22, 30), 1.); s.front = []
        s.st = big('VENTA LIBRE: NO AUTORIZADA', 60, (255, 110, 100), glow=(255, 40, 30))
    def draw(s, fr, t, d):
        fy, h = 1740, 700; x = 560; u = U('vecino', h); counter(fr, 680, 1060, 1280, (120, 110, 100)); sign(fr, 870, 1120, 300, 80, 'VENTA', (90, 70, 50))
        tn = s.w('no', -.5) + .2
        keys = [(0, P(look=(.4, .2), frown=-.1, grip={'R': (x + 1.6 * u, fy - 5.0 * u, 1.)}, tz=.6)), (tn + .3, P(look=(.4, .1), frown=.2, grip={'R': (x + 1.6 * u, fy - 5.0 * u, 1.)}, tz=.6)),
                (tn + .9, P(look=(0, .05), frown=.4, brow_up=.4, boca='tensa', grip={'R': (x + .6 * u, fy - 4.4 * u, 1.)}, tz=.5)), (d, P(look=(-.1, .05), frown=.45, brow_up=.4, boca='tensa', grip={'R': (x + .6 * u, fy - 4.4 * u, 1.)}, tz=.5))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 103); hands, _ = RG.person_34(fr, 'vecino', x, fy, h, p, t, feet=stance(x, u, fy), turn=1)
        if t < tn + .6: box_item(fr, hands['R'][0], hands['R'][1] + 10, (200, 60, 60)); hands_on_top(fr, {'R': hands['R']}, 'vecino', h)
        k = ss(tn + .5, tn + .8, t)
        if k > 0: blit(fr, s.st, 540, 640, k, lerp(1.6, 1, eOut(k)))
        draw_tag(fr, 'rec')
class NoEvidence(Sl):                               # tampoco hay evidencia de que legalizar elimine automáticamente a los cárteles (recreación)
    grade = 4
    def __init__(s):
        s.back = NV.stage_bg(20, (10, 8, 8), (180, 100, 60)); s.main = ground(1560, (22, 18, 16), 1.); s.front = [(bokeh_layer(8, (255, 180, 120), 820, ymin=300, ymax=1100), 1.7)]
        s.p = gold_panel('SIN EVIDENCIA DE QUE', 'ELIMINE A LOS CÁRTELES', w=880, h=180)
    def draw(s, fr, t, d):
        fy, h = 1740, 760; u = U('capo', h); x = 540
        cv2.rectangle(fr, (180, 760), (900, 1560), (60, 46, 36), -1); cv2.rectangle(fr, (230, 800), (850, 1560), (20, 16, 14), -1)   # puerta: el capo sigue ahí
        keys = [(0, P(look=(0, .1), frown=.3)), (s.w('elimine') - .3, P(look=(.1, .05), frown=.2, brow_asym=.5, boca='sonrisa')),
                (s.w('cárteles'), P(look=(0, .05), frown=.1, brow_asym=.5, boca='sonrisa', grip={'L': (x - .9 * u, fy - 4.2 * u, 1.), 'R': (x + .9 * u, fy - 4.2 * u, 1.)}, tz=.2)),
                (d, P(look=(0, .05), frown=.1, brow_asym=.5, boca='sonrisa', grip={'L': (x - .9 * u, fy - 4.2 * u, 1.), 'R': (x + .9 * u, fy - 4.2 * u, 1.)}, tz=.2))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 104); RG.person(fr, 'capo', x, fy, h, p, t, feet=stance(x, u, fy))
        pop(fr, s.p, 540, 520, t, s.w('evidencia') - .2); draw_tag(fr, 'rec')
    def cam(s, t, d): return lerp(1.0, 1.1, RG.ease(t / d)), 540, 1250, 0, 0

# ================================================================ CIERRE
class WhatNow(Doc):                                 # ¿qué debería hacer México? (Zócalo aéreo real)
    def __init__(s): Doc.__init__(s, 183, fx=.5, fy=.5, z=(1.0, 1.12), dark_=.25, title='¿QUÉ DEBERÍA', sub='HACER MÉXICO?', ty=760)
class Debate(Comb):                                 # regular vs. prohibición (dos vecinos debaten frente a Palacio Nacional real)
    def __init__(s):
        Comb.__init__(s, 6, fx=.5, fy=.4, gy=1600, dark_=.5, warm=.03)
        s.l = N.holo_panel(470, 150, 'REGULAR', 'quitar negocio al crimen', col=(150, 240, 90), fill=(16, 50, 10, 190)); s.r = red_panel('PROHIBIR', 'y reforzar la lucha', w=470, h=150)
    def draw(s, fr, t, d):
        fy, h = 1740, 700; xa, xb = 300, 780; ua, ub = U('vecina', h), U('vecino', h); tr, tp = s.w('regular'), s.w('mantener')
        pa = RG.anim([(0, P(look=(.4, .1))), (tr + .1, P(look=(.35, .1))), (tr + .8, P(look=(.3, .05), boca='habla', abre=.0, brow_up=.3, grip={'L': (xa - 1.2 * ua, fy - 6.4 * ua, 1.)}, tz=.6)),
                      (tp - .3, P(look=(.3, .05), brow_up=.3, grip={'L': (xa - 1.2 * ua, fy - 6.3 * ua, 1.)}, tz=.6)), (tp + .3, P(look=(.5, .15), frown=.3, brow_asym=.3)), (d, P(look=(.5, .15), frown=.35, brow_asym=.3))], t)
        pb = RG.anim([(0, P(look=(-.4, .1))), (tr + .3, P(look=(-.5, .15), frown=.3, brow_asym=.3)), (tp, P(look=(-.3, .05), frown=.2, brow_up=.3, grip={'R': (xb + 1.2 * ub, fy - 6.4 * ub, 1.)}, tz=.6)),
                      (d, P(look=(-.3, .05), frown=.25, brow_up=.3, grip={'R': (xb + 1.2 * ub, fy - 6.3 * ub, 1.)}, tz=.6))], t)
        pa['blink'] = blinkp(t, 105); pb['blink'] = blinkp(t, 106)
        RG.person_34(fr, 'vecina', xa, fy, h, pa, t, feet=stance(xa, ua, fy), turn=1); RG.person_34(fr, 'vecino', xb, fy, h, pb, t, feet=stance(xb, ub, fy), turn=-1)
        pop(fr, s.l, 290, 620, t, tr - .2); pop(fr, s.r, 790, 620, t, tp - .2); s.tags(fr, hyp=False)
class Friend(Sl):                                   # mándaselo a ese amigo que dice que legalizando todo se acaban los cárteles
    grade = 3
    def __init__(s):
        s.back, s.main = room_bg_(); s.front = [(bokeh_layer(8, (255, 200, 255), 826, ymin=200, ymax=1100), 1.7)]
        s.cta = gold_panel('MÁNDASELO A ESE AMIGO', w=900, h=150); s.b = N.text_sprite('«Legalizando todo se acaban los cárteles»', 34, (20, 20, 26, 255), pad=10)
    def draw(s, fr, t, d):
        cv2.rectangle(fr, (120, 1380), (1000, 1560), (110, 60, 80), -1); cv2.rectangle(fr, (120, 1300), (1000, 1390), (130, 74, 96), -1)
        x, fy, h = 540, 1730, 700; u = U('peaton1', h); ts = s.w('siempre')
        keys = [(0, P(look=(0, .1), frown=-.2, boca='sonrisa')), (ts, P(look=(.1, .05), frown=-.3, boca='sonrisa', brow_up=.3, grip={'R': (x + 1.3 * u, fy - 6.6 * u, 1.)}, tz=.6)),
                (d, P(look=(.1, .05), frown=-.3, boca='sonrisa', brow_up=.35, grip={'R': (x + 1.35 * u, fy - 6.7 * u, 1.)}, tz=.6))]
        p = RG.anim(keys, t); p['blink'] = blinkp(t, 107); RG.person(fr, 'peaton1', x, fy, h, p, t, feet=stance(x, u, fy, .38))
        float_in(fr, s.cta, 540, 380, t, .1)
        k = ss(ts, ts + .4, t)
        if k > 0:
            bw, bh = s.b.shape[1], s.b.shape[0]; cx, cy = 540, 760
            cv2.ellipse(fr, (cx, cy), (int(bw * .6 * k), int(bh * 1.1 * k)), 0, 0, 360, (255, 255, 255), -1, cv2.LINE_AA)
            poly(fr, [(cx + 40 * k, cy + bh * .9 * k), (cx + 90 * k, cy + bh * 1.0 * k), (cx + 70 * k, cy + bh * 1.6 * k)], (255, 255, 255))
            if k > .6: blit(fr, s.b, cx, cy, (k - .6) / .4)
        draw_tag(fr, 'rec')
    def cam(s, t, d): return lerp(1.04, 1.1, RG.ease(t / d)), 540, 1250, 0, 0
def room_bg_(wall=(50, 40, 70), floor=(70, 56, 44)):
    w_ = vgrad([(0, wall), (1, tuple(int(c * .7) for c in wall))]); i8 = to8(w_)
    for x in range(0, W, 70): cv2.line(i8, (x, 0), (x, 1300), tuple(int(c * 1.1) for c in wall), 2)
    return [(dof(opaque(i8.astype(np.float32)), 2.5), .4)], floor_layer(1560, floor, tuple(int(c * 1.2) for c in floor))
class Reality(Doc):                                 # la realidad es mucho más complicada (CDMX de noche, vista aérea real)
    def __init__(s): Doc.__init__(s, 168, fx=.5, fy=.5, z=(1.14, 1.0), dark_=.1, title='LA REALIDAD ES', sub='MUCHO MÁS COMPLICADA', ty=760)

# ================================================================ línea de tiempo
def tl():
    seq = [(0, Hook(), 0), (T('la', 3.8) - .25, Pills(), 1), (T('los') - .25, Boss(), 4), (T('pero', 9.5) - .25, HealthCrisis(), 3), (T('sería') - .25, Dilemma(), 1),
           (T('imagina') - .3, License(), 3), (T('de', 23.5) - .25, Markets(), 2), (T('los', 29) - .25, Compete(), 3), (T('pero', 34.5) - .25, Fight(), 4), (T('podrían', 38.8) - .25, Illegal(), 1), (T('intimidar') - .25, Diversify(), 1),
           (T('ahora') - .3, OtherSide(), 1), (T('si', 50) - .25, Minors(), 3), (T('y', 59.5) - .25, Risks(), 2), (T('una', 62) - .25, Fentanyl(), 1), (T('por', 65.8) - .25, Hospitals(), 3),
           (T('y', 73.5) - .3, Challenge(), 1), (T('méxico', 76) - .25, Inspect(), 2), (T('también', 83) - .25, Corruption(), 4), (T('y', 90) - .25, USA(), 1), (T('méxico', 92) - .25, Border(), 1),
           (T('una', 96.4) - .25, Tensions(), 1),
           (T('pero', 102) - .3, NotSame(), 2), (T('méxico', 106) - .25, Law(), 2), (T('eso', 113.5) - .25, NoSale(), 3), (T('y', 117.8) - .25, NoEvidence(), 4),
           (T('entonces') - .3, WhatNow(), 1), (T('regular') - .3, Debate(), 3), (T('y', 133.3) - .25, Friend(), 3), (T('porque', 138) - .25, Reality(), 1)]
    out = []
    for i, (a, sc, g) in enumerate(seq):
        b = seq[i + 1][0] if i + 1 < len(seq) else DUR; sc.a = a; out.append((a, b, sc, g))
    return out

KEYW = {'méxico', 'legalizara', 'cocaína', 'heroína', 'metanfetamina', 'fentanilo', 'cárteles', 'millones', 'crisis', 'salud', 'narcotráfico', 'histórico', 'licencias', 'controles',
        'impuestos', 'clandestinos', 'legalmente', 'autorizadas', 'problema', 'pelear', 'extorsión', 'secuestro', 'delitos', 'menores', 'riesgos', 'sobredosis', 'mortal', 'hospitales',
        'prevención', 'adicciones', 'desafío', 'vigilar', 'corrupción', 'legal', 'unidos', 'frontera', 'diplomáticas', 'despenalizar', 'personal', 'autorización', 'evidencia',
        'regular', 'prohibición', 'amigo', 'complicada'}

def make_frame():
    NV.TR.DUR = DUR; NV.TR.KEY = KEYW
    subs = [(a, b, y, sub_sprite(c)) for a, b, y, c in NV.TR.build_subs(WORDS)]
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
        os.makedirs(f'{OUTL}/test', exist_ok=True)
        for T_ in [float(x) for x in sys.argv[2:]]: cv2.imwrite(f'{OUTL}/test/n_{T_:06.2f}.jpg', cv2.resize(frame(T_)[0], (540, 960), interpolation=cv2.INTER_AREA)[:, :, ::-1])
    elif mode in ('seg', 'qcshot'):
        if mode == 'seg': f0, f1 = int(sys.argv[2]), int(sys.argv[3]); tag_ = f'{f0:05d}'; D_ = OUTL
        else: i = int(sys.argv[2]); f0, f1 = int(math.ceil(shots[i][0] * FPS)), int(math.ceil(shots[i][1] * FPS)); tag_ = f'shot{i:02d}'; D_ = f'{OUTL}/iter'
        os.makedirs(f'{D_}/thumbs', exist_ok=True); p = None
        if mode == 'seg':
            p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', f'{OUTL}/seg_{f0:05d}.mp4'], stdin=subprocess.PIPE)
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

if __name__ == '__main__': main()
