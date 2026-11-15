import json, base64, urllib.request, sys, re
d=json.load(open('../prompts.json'))
txt=open('../elevenlabs_voz.txt').read().strip().split('\n\n')
assert len(txt)==5
e=d['elevenlabs']
for i,t in enumerate(txt,1):
    body={'text':t.strip(),'model_id':e['model_id'],'voice_settings':{k:v for k,v in e['voice_settings'].items()}}
    req=urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{e['voice_id']}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(),headers={'Content-Type':'application/json','xi-api-key':'proxy-injected'})
    r=json.load(urllib.request.urlopen(req))
    open(f'vo{i}.mp3','wb').write(base64.b64decode(r['audio_base64']))
    json.dump(r['alignment'],open(f'vo{i}.json','w'),ensure_ascii=False)
    print(i,'ok')
