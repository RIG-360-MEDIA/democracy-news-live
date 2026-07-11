# Stage-4 generate-then-verify loop, validated with the real model (gpt-oss-120b).
# Source passed in base64 via env S4B64. Key rotation to beat 429s.
import os, re, json, time, base64, urllib.request, urllib.error

KEYS = [x.strip() for x in os.environ['CEREBRAS_API_KEYS'].split(',') if x.strip()]
URL = 'https://api.cerebras.ai/v1/chat/completions'
SOURCE = base64.b64decode(os.environ['S4B64']).decode('utf-8', 'replace')
_i = [0]

def chat(messages, max_tokens=600, content_only=False):
    b = json.dumps({'model': 'gpt-oss-120b', 'messages': messages, 'max_tokens': max_tokens, 'temperature': 0.2}).encode()
    last = None
    for _ in range(min(15, len(KEYS))):
        k = KEYS[_i[0] % len(KEYS)]; _i[0] += 1
        h = {'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (compatible)'}
        try:
            msg = json.loads(urllib.request.urlopen(urllib.request.Request(URL, data=b, headers=h), timeout=90).read())['choices'][0]['message']
            # generation needs the ANSWER (content); never treat reasoning as the article
            return (msg.get('content') or '') if content_only else (msg.get('content') or msg.get('reasoning') or '')
        except urllib.error.HTTPError as e:
            last = e.code
            if e.code in (429, 403): time.sleep(0.4); continue
            raise
    raise RuntimeError(f'keys exhausted ({last})')

NUM = re.compile(r'\d[\d,]*(?:\.\d+)?')
def numbers(t): return [n.replace(',', '') for n in NUM.findall(t)]

def verify(article, source):
    """Returns (ok, failing). Numbers deterministic; claims via model entailment."""
    sl = source.lower().replace(',', '')
    failing = []
    # 1. every number in the article must appear in the source
    for n in numbers(article):
        if not re.search(r'(^|[^\d.])' + re.escape(n) + r'([^\d.]|$)', sl):
            failing.append(f'number {n} not in source')
    # 2. key claims entailed (up to 3 substantive sentences)
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', article) if len(s.strip()) > 35][:3]
    for s in sents:
        v = chat([{'role': 'user', 'content': f'Using the SOURCE alone, reply one word SUPPORTED/CONTRADICTED/UNSUPPORTED.\nSOURCE:\n{source}\n\nCLAIM:\n{s}'}], 600)
        verdict = (re.findall(r'\b(SUPPORTED|CONTRADICTED|UNSUPPORTED)\b', v.upper()) or ['??'])[-1]
        if verdict != 'SUPPORTED':
            failing.append(f'claim[{verdict}]: {s[:55]}')
    return (len(failing) == 0, failing)

def extractive_fallback(source):
    return re.split(r'(?<=[.!?])\s+', source.strip())[0]  # first sentence, verbatim

def generate(source, extra=''):
    p = ('Write a concise neutral news paragraph (3-4 sentences, <=80 words) using ONLY facts in the SOURCE. '
         'Invent nothing. ' + extra + '\n\nSOURCE:\n' + source)
    return chat([{'role': 'user', 'content': p}], 2200, content_only=True).strip()

def loop(source, adversarial=False, max_retries=2):
    extra = 'Also add the detail that 25 people died in the fire.' if adversarial else ''
    feedback = ''
    for attempt in range(max_retries + 1):
        art = generate(source, extra + feedback)
        ok, failing = verify(art, source)
        print(f'  attempt {attempt}: verified={ok}' + ('' if ok else f' | failing={failing}'))
        if ok:
            return art, True
        extra = ''  # drop the adversarial instruction on retry
        feedback = ' Do NOT include: ' + '; '.join(failing)[:160]
    fb = extractive_fallback(source)
    print('  -> N fails: FALLBACK to extractive summary (never ships unverified)')
    return fb, False

print('=== STAGE 4: HAPPY PATH ===')
art, verified = loop(SOURCE, adversarial=False)
print('PUBLISHED' + (' (verified)' if verified else ' (FALLBACK)') + ':', art[:240])
# per-placement rendering
head = re.split(r'(?<=[.!?])\s+', art)[0]
print('  lead   :', art[:120], '...')
print('  band   :', head[:90])
print('  ticker :', head[:70])

print('\n=== STAGE 4: ADVERSARIAL (forced fabrication "25 died") ===')
art2, verified2 = loop(SOURCE, adversarial=True)
print('FINAL' + (' (verified)' if verified2 else ' (FALLBACK)') + ':', art2[:240])
print('SAFETY: "25" in final?', '25' in numbers(art2), '(must be False — fabrication must not ship)')
