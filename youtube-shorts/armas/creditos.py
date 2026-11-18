#!/usr/bin/env python3
# Genera CREDITOS.md a partir del material realmente usado en legalizar.py (ids citados en el código) y de material.json.
import json, re
src = open('armas.py').read(); M = {m['id']: m for m in json.load(open('material.json'))}
used = sorted({int(x) for x in re.findall(r'(?:Doc\.__init__\(s, |VidDoc\.__init__\(s, |Comb\.__init__\(s, |photo_card\()(\d+)', src)})
L = ['# Créditos del material audiovisual', '', 'Todo el material real procede de Wikimedia Commons. La licencia se leyó en la ficha oficial de cada archivo (API de Commons, campo LicenseShortName).',
     'Se usaron solo CC0, dominio público, CC BY y CC BY-SA. Las obras CC BY-SA se reencuadraron, se ajustó su color y se les superpusieron gráficos; esas adaptaciones se comparten bajo la misma licencia.', '',
     '| # | Archivo | Autor | Licencia | Fecha de la toma | Ficha |', '|---|---|---|---|---|---|']
for i in used:
    m = M[i]; L.append(f"| {i} | {m['titulo'][5:]} | {m['autor']} | {m['licencia']} | {m['fecha'][:10]} | [Commons]({m['pagina']}) |")
L += ['', 'Voz: ElevenLabs (voz «Brian»), generada para este video. Personajes, escenarios y gráficos: NEON CINEMATIC STUDIO (animación propia).']
open('CREDITOS.md', 'w').write('\n'.join(L) + '\n'); print(used)
