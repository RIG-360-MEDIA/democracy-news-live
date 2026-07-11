import os,re,json,base64,time,urllib.request,urllib.error
KEYS=[x.strip() for x in os.environ['CEREBRAS_API_KEYS'].split(',') if x.strip()]
SRC=base64.b64decode(os.environ['S4B64']).decode('utf-8','replace')
_i=[0]
def chat(msgs,mt):
    b=json.dumps({'model':'gpt-oss-120b','messages':msgs,'max_tokens':mt,'temperature':0.2}).encode()
    for _ in range(15):
        k=KEYS[_i[0]%len(KEYS)];_i[0]+=1
        h={'Authorization':'Bearer '+k,'Content-Type':'application/json','User-Agent':'Mozilla/5.0 (compatible)'}
        try:
            m=json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cerebras.ai/v1/chat/completions',data=b,headers=h),timeout=120).read())['choices'][0]['message']
            return m.get('content') or ''
        except urllib.error.HTTPError as e:
            if e.code in(429,403):time.sleep(0.4);continue
            raise
    return ''
p=('Write a full news article in a neutral house voice (3-4 short paragraphs, 180-240 words) using ONLY facts '
   'present in the SOURCE. Invent nothing; include no number or claim not in the source.\n\nSOURCE:\n'+SRC)
art=chat([{'role':'user','content':p}],2600).strip()
print('WORDS:',len(art.split()))
print(art)
# number-grounding check
sl=SRC.lower().replace(',','')
bad=[n for n in set(re.findall(r'\d[\d,]*',art)) if not re.search(r'(^|[^\d.])'+re.escape(n.replace(',',''))+r'([^\d.]|$)',sl)]
print('\nNUMBERS_NOT_IN_SOURCE:',bad or 'NONE (all grounded)')
