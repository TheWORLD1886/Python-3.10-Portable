#!/usr/bin/env python3
# Control de calidad automático de un plano. Entradas: out/rig_log.json (articulaciones de cada personaje en CADA fotograma,
# tal como las dibujó el rig) y out/frames/*.png (cada fotograma renderizado, sin subtítulos).
# Las puntuaciones salen de fórmulas fijas sobre lo medido (ver PUNTUACION abajo); no hay notas puestas a mano.
import os, sys, json, glob, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out')
LIM = dict(bone_tol=.02, pop=.35, slide_px=.5, floor_tol=.05, grip_px=3., diff_k=4., diff_min=6.)
BONES = [('hipL', 'kneeL', 1.55), ('kneeL', 'ankleL', 1.55), ('hipR', 'kneeR', 1.55), ('kneeR', 'ankleR', 1.55),
         ('shL', 'elbowL', 1.3), ('elbowL', 'handL', 1.25), ('shR', 'elbowR', 1.3), ('elbowR', 'handR', 1.25)]
JOINTS = ['head', 'neck', 'hip', 'shL', 'shR', 'elbowL', 'elbowR', 'handL', 'handR', 'kneeL', 'kneeR', 'ankleL', 'ankleR']

def run():
    log = {int(k): v for k, v in json.load(open(os.path.join(OUT, 'rig_log.json'))).items()}
    nf = max(log) + 1; ids = sorted({r['id'] for v in log.values() for r in v})
    rep = dict(frames=nf, personajes=ids, errores=[], medidas={})
    E = rep['errores']
    def err(cat, f, who, msg): E.append(dict(cat=cat, frame=f, id=who, msg=msg))
    # ---------- por personaje: serie temporal (en fotogramas con dos registros —el fundido de giro— se toma el último)
    trans = set()
    seq = {i: {} for i in ids}
    for f, recs in log.items():
        for r in recs:
            if r.get('tag') == 'giro': trans.add(f)
            seq[r['id']][f] = r
    bone_err = []; pops = 0; slides = 0; floats = 0; sinks = 0; hand_r = {}; us = {}; lip = 0; grip_bad = 0; grip_n = 0
    for i in ids:
        S = seq[i]; fs = sorted(S)
        for f in fs:
            r = S[f]; u = r['u']; J = r['raw'] or r['joints']; us.setdefault(i, set()).add(round(u, 3)); hand_r.setdefault(i, set()).add(round(r['hand_r'], 3))
            Z = r.get('z', {})
            for a, b, L in BONES:                                              # 1. huesos que no cambian de largo (en 3D si hay profundidad)
                if a in J and b in J:
                    pa, pb = list(J[a]) + [Z.get(a, 0.)], list(J[b]) + [Z.get(b, 0.)]
                    e = abs(math.dist(pa, pb) - L * u) / (L * u); bone_err.append(e)
                    if e > LIM['bone_tol']: err('continuidad corporal', f, i, f'{a}-{b} {e * 100:.1f}% fuera de largo')
            jj = r['joints']; gy = r['fy'] - .22 * u                             # 3. pies: ni flotan ni atraviesan el suelo
            ank = [jj[k][1] for k in ('ankleL', 'ankleR') if k in jj]
            if ank:
                if max(ank) > gy + LIM['floor_tol'] * u: sinks += 1; err('caminata', f, i, f'pie atraviesa el suelo {max(ank) - gy:.1f}px')
                if max(ank) < gy - LIM['floor_tol'] * u: floats += 1; err('caminata', f, i, f'ningún pie toca el suelo ({gy - max(ank):.1f}px)')
            if not r['speaking'] and r['boca'] == 'habla' and r['abre'] > .08: lip += 1; err('sincronización labial', f, i, 'boca hablando sin diálogo')
            for k, g in r['grip'].items():                                     # 6. la mano llega exactamente al objeto que agarra
                if g[2] >= .999 and ('hand' + k) in jj:
                    grip_n += 1; dd = math.dist(jj['hand' + k], g[:2])
                    if dd > LIM['grip_px']: grip_bad += 1; err('interacción con objetos', f, i, f'mano {k} a {dd:.1f}px del objeto')
        for f in fs[1:]:                                                       # 3b. pie apoyado que se desliza
            if f - 1 not in S: continue
            a, b = S[f - 1], S[f]
            if a['view'] != b['view']: continue
            for k in ('ankleL', 'ankleR'):
                if k in a['joints'] and k in b['joints']:
                    gy = b['fy'] - .22 * b['u']
                    pa, pb = a['joints'][k], b['joints'][k]
                    if abs(pa[1] - gy) < .5 and abs(pb[1] - gy) < .5 and abs(pb[0] - pa[0]) > LIM['slide_px']:
                        slides += 1; err('caminata', f, i, f'{k} se desliza {abs(pb[0] - pa[0]):.1f}px apoyado')
        for f in fs[2:]:                                                       # 2. saltos: aceleración de cada articulación
            if f - 1 not in S or f - 2 not in S or {f, f - 1, f - 2} & trans: continue
            rs = (S[f - 2], S[f - 1], S[f])
            if len({r['view'] for r in rs}) > 1: continue
            for k in JOINTS:
                if all(k in r['joints'] for r in rs):
                    p0, p1, p2 = (np.array(r['joints'][k]) for r in rs); acc = np.linalg.norm(p2 - 2 * p1 + p0)
                    if acc > LIM['pop'] * rs[2]['u']: pops += 1; err('movimiento de extremidades', f, i, f'{k} salta {acc:.1f}px ({acc / rs[2]["u"]:.2f}u)')
    # ---------- 7. continuidad temporal en la imagen (todos los fotogramas)
    files = sorted(glob.glob(os.path.join(OUT, 'frames', 'f_*.png'))); diffs = []
    prev = None
    for fpath in files:
        im = cv2.resize(cv2.imread(fpath), (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32)
        if prev is not None: diffs.append(float(np.abs(im - prev).mean()))
        prev = im
    diffs = np.array(diffs); med = float(np.median(diffs)) if len(diffs) else 0.; spikes = 0
    for k, dv in enumerate(diffs):
        f = k + 1; nb = max(diffs[k - 1] if k > 0 else med, diffs[k + 1] if k + 1 < len(diffs) else med)   # pico respecto a los vecinos
        if dv > max(LIM['diff_k'] * med, LIM['diff_min']) and dv > 2.5 * nb and f not in trans and f - 1 not in trans: spikes += 1; err('continuidad temporal', f, '-', f'salto de imagen {dv:.1f} (vecinos {nb:.1f}, mediana {med:.2f})')
    # ---------- PUNTUACION (fórmulas fijas)
    be = max(bone_err) if bone_err else 0.
    walk_frames = sum(1 for v in log.values() for r in v if r.get('tag') == 'camina')
    sc = {
        'Continuidad corporal': max(0., 10 - 50 * max(0., be - .005)),
        'Movimiento de extremidades': max(0., 10 - 1. * pops),
        'Naturalidad de caminata': max(0., 10 - .5 * (slides + floats + sinks)),
        'Consistencia visual': 10. if all(len(v) == 1 for v in hand_r.values()) and all(len(v) == 1 for v in us.values()) else 6.,
        'Sincronización labial': max(0., 10 - .5 * lip),
        'Interacción con objetos': max(0., 10 - .25 * grip_bad),
        'Continuidad temporal': max(0., 10 - 1. * spikes),
    }
    rep['medidas'] = dict(error_max_hueso_pct=round(be * 100, 3), saltos_articulacion=pops, deslizamientos=slides, flotando=floats, atraviesa_suelo=sinks,
                          fotogramas_caminando=walk_frames, radios_mano=sorted({x for v in hand_r.values() for x in v}), bocas_hablando_sin_dialogo=lip,
                          agarres_medidos=grip_n, agarres_fuera=grip_bad, diff_mediana=round(med, 3), diff_max=round(float(diffs.max()) if len(diffs) else 0, 3),
                          saltos_imagen=spikes, fotogramas_transicion=sorted(trans))
    rep['puntuacion'] = {k: round(v, 1) for k, v in sc.items()}; rep['aprobado'] = all(v >= 9 for v in sc.values())
    json.dump(rep, open(os.path.join(OUT, 'qc.json'), 'w'), ensure_ascii=False, indent=1)
    # ---------- hojas de contacto (1 de cada 2 fotogramas) y trayectorias de articulaciones
    sel = files[::2]
    for s_ in range(0, len(sel), 36):
        ims = [cv2.resize(cv2.imread(p)[700:1800, 120:1000], (176, 220)) for p in sel[s_:s_ + 36]]
        for k, im in enumerate(ims): cv2.putText(im, os.path.basename(sel[s_ + k])[2:5], (4, 14), cv2.FONT_HERSHEY_SIMPLEX, .4, (0, 255, 255), 1)
        while len(ims) % 6: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(os.path.join(OUT, f'contacto_{s_ // 36 + 1}.jpg'), np.vstack([np.hstack(ims[r:r + 6]) for r in range(0, len(ims), 6)]))
    base = cv2.imread(files[len(files) // 2]) // 3
    cols = {'head': (0, 255, 255), 'handL': (255, 120, 0), 'handR': (0, 120, 255), 'ankleL': (255, 0, 255), 'ankleR': (0, 255, 0), 'elbowL': (200, 200, 0), 'elbowR': (0, 200, 200), 'kneeL': (160, 0, 255), 'kneeR': (0, 160, 255)}
    for i in ids:
        fs = sorted(seq[i])
        for k, c in cols.items():
            pts = [seq[i][f]['joints'][k] for f in fs if k in seq[i][f]['joints']]
            for a, b in zip(pts[:-1], pts[1:]): cv2.line(base, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), c, 2, cv2.LINE_AA)
    cv2.imwrite(os.path.join(OUT, 'trayectorias.jpg'), cv2.resize(base[600:1800, 0:1080], (540, 600)))
    return rep

if __name__ == '__main__':
    r = run(); print(json.dumps({k: r[k] for k in ('puntuacion', 'aprobado', 'medidas')}, ensure_ascii=False, indent=1))
    from collections import Counter; print(Counter(e['cat'] for e in r['errores'])); [print(e) for e in r['errores'][:25]]
