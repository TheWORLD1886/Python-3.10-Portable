#!/usr/bin/env python3
# Videos: pide a la API las versiones transcodificadas y baja la de 1080p (o la mayor disponible).
import json, urllib.request, urllib.parse, time, os, subprocess
UA = {'User-Agent': 'NeonShortsResearch/1.0 (educational video research)'}
I = json.load(open('out/indice.json')); M = {m['id']: m for m in json.load(open('material.json'))} if os.path.exists('material.json') else {}
import re; clean = lambda s: re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s)).strip()
for i in (329, 147, 137, 319, 162, 142):
    x = I[i]; dst = f'material/m{i:03d}.webm'
    if not os.path.exists(dst):
        q = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(dict(action='query', titles=x['title'], prop='videoinfo', viprop='derivatives', format='json'))
        d = json.load(urllib.request.urlopen(urllib.request.Request(q, headers=UA), timeout=60)); p = list(d['query']['pages'].values())[0]
        ds = sorted([v for v in p['videoinfo'][0]['derivatives'] if v['src'].endswith('webm') and v.get('height')], key=lambda v: -v['height'])
        ds = [v for v in ds if v['height'] <= 1080] or ds
        r = subprocess.run(['curl', '-sS', '-f', '-L', '-m', '300', '-A', UA['User-Agent'], '-o', dst, ds[0]['src']]); print(i, ds[0]['height'], r.returncode, flush=True)
        time.sleep(2)
    M[i] = dict(id=i, archivo=dst, titulo=x['title'], pagina=x['page'], licencia=x['licencia'], autor=clean(x['autor']), fecha=clean(x['fecha']), descripcion=clean(x['desc']), mime=x['mime'])
json.dump(sorted(M.values(), key=lambda m: m['id']), open('material.json', 'w'), ensure_ascii=False, indent=1)
