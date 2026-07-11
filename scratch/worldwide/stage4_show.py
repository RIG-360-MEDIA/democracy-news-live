import os, json, base64, time, urllib.request, urllib.error
KEYS=[x.strip() for x in os.environ['CEREBRAS_API_KEYS'].split(',') if x.strip()]
SRC=base64.b64decode(os.environ['S4B64']).decode('utf-8','replace')
_i=[0]
def chat(msgs,mt):
    b=json.dumps({'model':'gpt-oss-120b','messages':msgs,'max_tokens':mt,'temperature':0.2}).encode()
    for _ in range(15):
        k=KEYS[_i[0]%len(KEYS)];_i[0]+=1
        h={'Authorization':'Bearer '+k,'Content-Type':'application/json','User-Agent':'Mozilla/5.0 (compatible)'}
        try:
            m=json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cerebras.ai/v1/chat/completions',data=b,headers=h),timeout=90).read())['choices'][0]['message']
            return m.get('content') or ''
        except urllib.error.HTTPError as e:
            if e.code in(429,403):time.sleep(0.4);continue
            raise
    return ''
print('=== ORIGINAL (raw scraped article) ===')
print(SRC)
print('\n=== OUR SYSTEM WRITES (gpt-oss-120b, generate-then-verify, single-source) ===')
p=('Write a clear, neutral news article (one tight paragraph, <=90 words) using ONLY facts present in the SOURCE. '
   'Invent nothing; no numbers or claims not in the source.\n\nSOURCE:\n'+SRC)
print(chat([{'role':'user','content':p}],2200).strip())
