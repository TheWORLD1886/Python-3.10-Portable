#!/usr/bin/env python3
# Control de calidad por plano del short Legalizar: mismas fórmulas que nvidia/qc_final.py (se reutiliza evaluate()).
import os, sys, json, glob, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'nvidia'))
import numpy as np, cv2
import qc_final as Q
O = os.path.join(HERE, 'out', 'iter') if 'iter' in sys.argv else os.path.join(HERE, 'out')
def main():
    import legalizar as I
    shots = I.tl(); log, diffs = [], {}
    for p in sorted(glob.glob(os.path.join(O, 'qc_*.json'))):
        if p.endswith('qc_final.json'): continue
        d = json.load(open(p)); log += d['log']; diffs.update({int(k): v for k, v in d['diffs'].items()})
    rep = dict(fotogramas_video=int(math.ceil(I.DUR * 30)), fotogramas_con_diff=len(diffs), planos=[])
    for i, (a, b, sc_, g) in enumerate(shots):
        f0, f1 = int(math.ceil(a * 30)), int(math.ceil(b * 30))
        if 'iter' in sys.argv and not any(f0 <= f < f1 for f in diffs): continue
        recs = [r for r in log if r['shot'] == i and f0 <= r['f'] < f1]
        sc, med, E = Q.evaluate(recs, {f: v for f, v in diffs.items() if f0 <= f < f1}, set(range(f0, f0 + 11)))
        ok = all(v is None or v >= 9 for v in sc.values())
        rep['planos'].append(dict(n=i + 1, nombre=type(sc_).__name__, inicio=round(a, 2), fin=round(b, 2), fotogramas=f1 - f0,
                                  puntuacion={k: (None if v is None else round(v, 1)) for k, v in sc.items()}, aprobado=ok, medidas=med, errores=E[:60], n_errores=len(E)))
        th = sorted(p for p in glob.glob(os.path.join(O, 'thumbs', 't_*.jpg')) if f0 <= int(p[-9:-4]) < f1)
        if th:
            sel = th[::max(1, len(th) // 16)][:16]; ims = [cv2.imread(p) for p in sel]
            for k, im in enumerate(ims): cv2.putText(im, sel[k][-9:-4], (3, 12), cv2.FONT_HERSHEY_SIMPLEX, .35, (0, 255, 255), 1)
            while len(ims) % 8: ims.append(np.zeros_like(ims[0]))
            os.makedirs(os.path.join(O, 'contactos'), exist_ok=True)
            cv2.imwrite(os.path.join(O, 'contactos', f'plano_{i + 1:02d}.jpg'), np.vstack([np.hstack(ims[r:r + 8]) for r in range(0, len(ims), 8)]))
    json.dump(rep, open(os.path.join(O, 'qc_final.json'), 'w'), ensure_ascii=False, indent=1)
    for p in rep['planos']:
        s = ' '.join(f"{k.split()[0][:6]}={v}" for k, v in p['puntuacion'].items() if v is not None)
        print(f"{p['n']:2d} {p['nombre']:14s} {'OK ' if p['aprobado'] else 'MAL'} {s}  errores={p['n_errores']}")
    print('todos aprobados' if all(p['aprobado'] for p in rep['planos']) else 'HAY PLANOS POR CORREGIR', '·', len(diffs), '/', rep['fotogramas_video'])
if __name__ == '__main__': main()
