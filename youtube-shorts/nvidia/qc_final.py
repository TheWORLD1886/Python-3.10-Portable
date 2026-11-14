#!/usr/bin/env python3
# Control de calidad del video completo, plano por plano. Entradas: out2/qc_*.json (registro del rig en cada fotograma +
# diferencias de imagen entre fotogramas consecutivos) y out2/thumbs (1 de cada 3 fotogramas).
# Mismas fórmulas que prueba/qc.py. Los planos sin personajes solo se evalúan en continuidad temporal.
import os, sys, json, glob, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(HERE, 'out2', 'iter') if 'iter' in sys.argv else os.path.join(HERE, 'out2')
LIM = dict(bone_tol=.02, pop=.35, slide_px=.5, floor_tol=.05, grip_px=3., diff_k=4., diff_min=6.)
BONES = [('hipL', 'kneeL', 1.55), ('kneeL', 'ankleL', 1.55), ('hipR', 'kneeR', 1.55), ('kneeR', 'ankleR', 1.55),
         ('shL', 'elbowL', 1.3), ('elbowL', 'handL', 1.25), ('shR', 'elbowR', 1.3), ('elbowR', 'handR', 1.25)]
JOINTS = ['head', 'neck', 'hip', 'shL', 'shR', 'elbowL', 'elbowR', 'handL', 'handR', 'kneeL', 'kneeR', 'ankleL', 'ankleR']
FPS = 30

def load():
    log, diffs = [], {}
    for p in sorted(glob.glob(os.path.join(O, 'qc_*.json'))):
        d = json.load(open(p)); log += d['log']; diffs.update({int(k): v for k, v in d['diffs'].items()})
    return log, diffs

def evaluate(recs, diffs, excl):
    E = []; err = lambda cat, f, i, m: E.append(dict(cat=cat, frame=f, id=i, msg=m))
    seq = {}; trans = set()
    for r in recs:
        if r.get('tag') == 'giro': trans.add(r['f'])
        seq.setdefault(r['id'], {})[r['f']] = r
    bone = []; pops = slides = floats = sinks = lip = gbad = gn = 0; hand_r = {}; us = {}; walkf = 0
    for i, S in seq.items():
        fs = sorted(S)
        for f in fs:
            r = S[f]; u = r['u']; J = r['raw'] or r['joints']; Z = r.get('z', {})
            if r.get('tag') == 'camina': walkf += 1
            us.setdefault(i, set()).add(round(u, 2)); hand_r.setdefault(i, set()).add(round(r['hand_r'], 2))
            if r['who'] == 'figura' or u < 12: continue                         # siluetas / personajes miniatura en monitores: sin rig visible fino
            for a, b, L in BONES:
                if a in J and b in J:
                    e = abs(math.dist(list(J[a]) + [Z.get(a, 0.)], list(J[b]) + [Z.get(b, 0.)]) - L * u) / (L * u); bone.append(e)
                    if e > LIM['bone_tol']: err('continuidad corporal', f, i, f'{a}-{b} {e * 100:.1f}%')
            jj = r['joints']; gy = r['fy'] - .22 * u; ank = [jj[k][1] for k in ('ankleL', 'ankleR') if k in jj]
            if ank:
                if max(ank) > gy + LIM['floor_tol'] * u: sinks += 1; err('caminata', f, i, f'pie bajo el suelo {max(ank) - gy:.1f}px')
                if max(ank) < gy - LIM['floor_tol'] * u: floats += 1; err('caminata', f, i, f'ningún pie en el suelo ({gy - max(ank):.1f}px)')
            if not r['speaking'] and r['boca'] == 'habla' and r['abre'] > .08: lip += 1; err('sincronización labial', f, i, 'boca hablando sin diálogo')
            for k, g in r['grip'].items():
                if g[2] >= .999 and ('hand' + k) in jj:
                    gn += 1; dd = math.dist(jj['hand' + k], g[:2])
                    if dd > LIM['grip_px']: gbad += 1; err('interacción con objetos', f, i, f'mano {k} a {dd:.1f}px del objeto')
        for f in fs[1:]:
            if f - 1 not in S: continue
            a, b = S[f - 1], S[f]
            if a['view'] != b['view'] or b['u'] < 12: continue
            for k in ('ankleL', 'ankleR'):
                if k in a['joints'] and k in b['joints']:
                    gy = b['fy'] - .22 * b['u']; pa, pb = a['joints'][k], b['joints'][k]
                    if abs(pa[1] - gy) < .5 and abs(pb[1] - gy) < .5 and abs(pb[0] - pa[0]) > LIM['slide_px']: slides += 1; err('caminata', f, i, f'{k} se desliza {abs(pb[0] - pa[0]):.1f}px')
        for f in fs[2:]:
            if f - 1 not in S or f - 2 not in S or {f, f - 1, f - 2} & trans: continue
            rs = (S[f - 2], S[f - 1], S[f])
            if len({r['view'] for r in rs}) > 1 or rs[2]['u'] < 12: continue
            for k in JOINTS:
                if all(k in r['joints'] for r in rs):
                    p0, p1, p2 = (np.array(r['joints'][k]) for r in rs); acc = float(np.linalg.norm(p2 - 2 * p1 + p0))
                    if acc > LIM['pop'] * rs[2]['u']: pops += 1; err('movimiento de extremidades', f, i, f'{k} salta {acc:.1f}px ({acc / rs[2]["u"]:.2f}u)')
    dv = {f: v for f, v in diffs.items() if f not in excl}; med = float(np.median(list(dv.values()))) if dv else 0.; spikes = 0
    for f, v in sorted(dv.items()):                                        # salto = pico respecto a los fotogramas vecinos (un movimiento suave y continuo no es salto)
        nb = max(diffs.get(f - 1, med), diffs.get(f + 1, med))
        if v > max(LIM['diff_k'] * med, LIM['diff_min']) and v > 2.5 * nb and f not in trans and f - 1 not in trans: spikes += 1; err('continuidad temporal', f, '-', f'salto de imagen {v:.1f} (vecinos {nb:.1f}, mediana {med:.2f})')
    has_chars = bool(seq) and any(r['who'] != 'figura' and r['u'] >= 12 for r in recs)
    be = max(bone) if bone else 0.
    sc = {'Continuidad temporal': max(0., 10 - 1. * spikes)}
    if has_chars:
        sc.update({'Continuidad corporal': max(0., 10 - 50 * max(0., be - .005)), 'Movimiento de extremidades': max(0., 10 - 1. * pops),
                   'Naturalidad de caminata': max(0., 10 - .5 * (slides + floats + sinks)) if walkf or ank_any(recs) else None,
                   'Consistencia visual': 10. if all(len(v) == 1 for v in hand_r.values()) and all(len(v) == 1 for v in us.values()) else 6.,
                   'Sincronización labial': max(0., 10 - .5 * lip), 'Interacción con objetos': max(0., 10 - .25 * gbad) if gn else None})
    med_ = dict(personajes=sorted({r['who'] for r in recs}), registros=len(recs), err_hueso_max_pct=round(be * 100, 3), saltos=pops, deslizamientos=slides,
                flotando=floats, bajo_suelo=sinks, fotogramas_caminando=walkf, agarres=gn, agarres_fuera=gbad, bocas_sin_dialogo=lip,
                diff_mediana=round(med, 2), picos_imagen=spikes, fotogramas_giro=len(trans))
    return sc, med_, E
def ank_any(recs): return any(('ankleL' in r['joints']) for r in recs)

def main():
    sys.path.insert(0, HERE)
    import nvidia2 as N2
    shots = N2.tl(); log, diffs = load()
    nf = int(math.ceil(N2.NV.DUR * FPS)); have = sorted({r['f'] for r in log})
    rep = dict(fotogramas_video=nf, fotogramas_con_diff=len(diffs), planos=[])
    for i, (a, b, sc_, g) in enumerate(shots):
        f0, f1 = int(math.ceil(a * FPS)), int(math.ceil(b * FPS))
        recs = [r for r in log if r['shot'] == i and f0 <= r['f'] < f1]
        if 'iter' in sys.argv and not any(f0 <= f < f1 for f in diffs): continue
        excl = set(range(f0, f0 + int(.35 * FPS) + 1))                         # fundido planificado entre planos
        d = {f: v for f, v in diffs.items() if f0 <= f < f1}
        sc, med, E = evaluate(recs, d, excl)
        ok = all(v is None or v >= 9 for v in sc.values())
        rep['planos'].append(dict(n=i + 1, nombre=type(sc_).__name__, inicio=round(a, 2), fin=round(b, 2), fotogramas=f1 - f0,
                                  puntuacion={k: (None if v is None else round(v, 1)) for k, v in sc.items()}, aprobado=ok, medidas=med, errores=E[:60], n_errores=len(E)))
        # hoja de contacto del plano (miniaturas 1 de cada 3 fotogramas)
        th = sorted(p for p in glob.glob(os.path.join(O, 'thumbs', 't_*.jpg')) if f0 <= int(p[-9:-4]) < f1)
        if th:
            sel = th[::max(1, len(th) // 24)][:24]; ims = [cv2.imread(p) for p in sel]
            for k, im in enumerate(ims): cv2.putText(im, sel[k][-9:-4], (3, 12), cv2.FONT_HERSHEY_SIMPLEX, .35, (0, 255, 255), 1)
            while len(ims) % 8: ims.append(np.zeros_like(ims[0]))
            os.makedirs(os.path.join(O, 'contactos'), exist_ok=True)
            cv2.imwrite(os.path.join(O, 'contactos', f'plano_{i + 1:02d}.jpg'), np.vstack([np.hstack(ims[r:r + 8]) for r in range(0, len(ims), 8)]))
    json.dump(rep, open(os.path.join(O, 'qc_final.json'), 'w'), ensure_ascii=False, indent=1)
    for p in rep['planos']:
        s = ' '.join(f"{k.split()[0][:6]}={v}" for k, v in p['puntuacion'].items() if v is not None)
        print(f"{p['n']:2d} {p['nombre']:12s} {'OK ' if p['aprobado'] else 'MAL'} {s}  errores={p['n_errores']}")
    print('todos aprobados' if all(p['aprobado'] for p in rep['planos']) else 'HAY PLANOS POR CORREGIR', '· fotogramas con diff:', len(diffs), '/', nf)

if __name__ == '__main__': main()
