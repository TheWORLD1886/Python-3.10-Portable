import json, re
SPEED, TOTAL = 1.05, 60.0
scenes, chunks, t0 = [], [], 0.0
durs = []
import subprocess
for i in range(1, 6):
    d = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f'vo{i}.mp3']))/SPEED
    durs.append(d)
durs[-1] += TOTAL - sum(durs)
for i, d in enumerate(durs, 1):
    a = json.load(open(f'vo{i}.json'))
    chars, st, en = a['characters'], a['character_start_times_seconds'], a['character_end_times_seconds']
    words, cur, intag = [], None, False
    for c, s, e in zip(chars, st, en):
        if c == '<': intag = True
        if intag:
            if c == '>': intag = False
            if cur: words.append(cur); cur = None
            continue
        if c.isspace():
            if cur: words.append(cur); cur = None
            continue
        if cur is None: cur = {'text': '', 'start': s}
        cur['text'] += c; cur['end'] = e
    if cur: words.append(cur)
    for w in words: w['start'] = round(t0 + w['start']/SPEED, 3); w['end'] = round(t0 + w['end']/SPEED, 3)
    grp = []
    for w in words:
        grp.append(w)
        if len(grp) >= 3 or re.search(r'[.,:?!]$', w['text']) or (len(grp) == 2 and len(''.join(x['text'] for x in grp)) > 16):
            chunks.append(grp); grp = []
    if grp: chunks.append(grp)
    scenes.append({'start': round(t0, 3), 'end': round(t0 + d, 3)})
    t0 += d
out = []
for j, g in enumerate(chunks):
    nxt = chunks[j+1][0]['start'] if j+1 < len(chunks) else TOTAL
    out.append({'start': g[0]['start'], 'end': min(nxt, g[-1]['end'] + .6), 'words': [{'text': w['text'], 'start': w['start']} for w in g]})
json.dump({'scenes': scenes, 'chunks': out, 'total': TOTAL}, open('timeline.json', 'w'), ensure_ascii=False)
print(scenes); print(len(out), [ ' '.join(w['text'] for w in c['words']) for c in out[:8]])
