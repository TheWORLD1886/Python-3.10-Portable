#!/usr/bin/env python3
# Material elegido (ids de out/indice.json) -> descarga (miniatura oficial 3840/1920 px o transcodificación 720p del video) + ficha de licencia
import json, urllib.request, urllib.parse, os, re, time, sys
UA = {'User-Agent': 'NeonShortsResearch/1.0 (educational video research)'}
SEL = [6, 9, 12, 21, 22, 24, 50, 64, 65, 66, 71, 72, 85, 96, 104, 108, 115, 164, 165, 168, 183, 187, 190, 191, 213, 214, 240, 262, 290, 296,
       137, 142, 147, 162, 319, 329]
I = json.load(open('out/indice.json')); os.makedirs('material', exist_ok=True)
M = {m['id']: m for m in json.load(open('material.json'))} if os.path.exists('material.json') else {}
def get(u):
    for k in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
        except Exception as e: err = e; time.sleep(4 + 6 * k)
    raise err
clean = lambda s: re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', s)).strip()
for i in SEL:
    x = I[i]; vid = x['mime'].startswith(('video', 'application/ogg'))
    dst = f'material/m{i:03d}.' + ('webm' if vid else 'jpg')
    if not os.path.exists(dst):
        if vid:
            fn = x['url'].split('/commons/')[1]; base = 'https://upload.wikimedia.org/wikipedia/commons/transcoded/' + fn + '/' + fn.split('/')[-1]
            for suf in ('.720p.vp9.webm', '.720p.webm', '.480p.vp9.webm', '.480p.webm'):
                try: open(dst, 'wb').write(get(base + suf)); break
                except Exception: pass
        else:
            t = x['thumb'].split('?')[0]
            for w in (3840, 1920):
                if x['w'] <= w: continue
                try: open(dst, 'wb').write(get(t.replace('/1280px-', f'/{w}px-'))); break
                except Exception: pass
            if not os.path.exists(dst): open(dst, 'wb').write(get(t))
    M[i] = dict(id=i, archivo=dst, titulo=x['title'], pagina=x['page'], licencia=x['licencia'], autor=clean(x['autor']),
                fecha=clean(x['fecha']), descripcion=clean(x['desc']), mime=x['mime'])
    print(i, os.path.getsize(dst) // 1024 if os.path.exists(dst) else 'FALLO', flush=True); time.sleep(1)
json.dump(sorted(M.values(), key=lambda m: m['id']), open('material.json', 'w'), ensure_ascii=False, indent=1)
