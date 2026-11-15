#!/usr/bin/env python3
# Busca material en Wikimedia Commons y guarda sus datos de licencia (ficha oficial del archivo). No descarga nada sin licencia libre.
import json, sys, urllib.parse, urllib.request, time, os
UA = {'User-Agent': 'NeonShortsResearch/1.0 (educational video research)'}
API = 'https://commons.wikimedia.org/w/api.php?'
OK_LIC = ('cc0', 'public domain', 'pd', 'cc by', 'cc-by')   # se descartan CC BY-NC / ND y licencias desconocidas
def api(**p):
    p.update(format='json'); r = urllib.request.Request(API + urllib.parse.urlencode(p), headers=UA)
    for k in range(4):
        try: return json.load(urllib.request.urlopen(r, timeout=30))
        except Exception as e: time.sleep(3 + 3 * k)
    return {}
def search(q, n=12, video=False):
    q2 = q + (' filetype:video' if video else ' filetype:bitmap')
    d = api(action='query', generator='search', gsrsearch=q2, gsrnamespace=6, gsrlimit=n, prop='imageinfo',
            iiprop='url|extmetadata|size|mime', iiurlwidth=1280, iiextmetadatafilter='LicenseShortName|Artist|DateTimeOriginal|ImageDescription|Credit|UsageTerms')
    out = []
    for pg in (d.get('query', {}).get('pages', {}) or {}).values():
        ii = pg['imageinfo'][0]; m = ii.get('extmetadata', {}); g = lambda k: (m.get(k, {}) or {}).get('value', '')
        lic = g('LicenseShortName'); ok = any(lic.lower().startswith(x) for x in OK_LIC) and 'nc' not in lic.lower() and 'nd' not in lic.lower().split('-')
        out.append(dict(q=q, title=pg['title'], page='https://commons.wikimedia.org/wiki/' + urllib.parse.quote(pg['title'].replace(' ', '_')),
                        url=ii.get('url'), thumb=ii.get('thumburl'), w=ii.get('width'), h=ii.get('height'), mime=ii.get('mime'),
                        licencia=lic, autor=g('Artist'), fecha=g('DateTimeOriginal'), desc=g('ImageDescription')[:300], credito=g('Credit')[:200], libre=ok))
    return out
if __name__ == '__main__':
    qs = json.load(open(sys.argv[1])); res = json.load(open('candidatos.json')) if os.path.exists('candidatos.json') else []
    have = {r['title'] for r in res}
    for q in qs:
        vid = q.startswith('VIDEO:'); r = search(q[6:] if vid else q, video=vid); time.sleep(1.5)
        new = [x for x in r if x['title'] not in have]; res += new; have |= {x['title'] for x in new}
        print(f'{q}: {len(r)} ({sum(x["libre"] for x in r)} libres)', flush=True)
    json.dump(res, open('candidatos.json', 'w'), ensure_ascii=False, indent=1)
