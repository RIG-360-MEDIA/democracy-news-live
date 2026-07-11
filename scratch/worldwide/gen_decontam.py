# Test 3 anti-contamination guards on the over-merged SMALL story (+ BIG control).
# Guard A = pre-check/segment then write dominant; B = refuse-mixed (dominant-only prompt);
# C = post-check (one-event verdict). Baseline = no guard. Metric = off-topic keyword leakage.
import os, re, json, time, urllib.request, urllib.error
KEYS = [x.strip() for x in os.environ['CEREBRAS_API_KEYS'].split(',') if x.strip()]
URL = 'https://api.cerebras.ai/v1/chat/completions'
_i = [0]
def chat(msgs, mt=1200):
    b = json.dumps({'model': 'gpt-oss-120b', 'messages': msgs, 'max_tokens': mt, 'temperature': 0.2}).encode()
    for _ in range(25):
        k = KEYS[_i[0] % len(KEYS)]; _i[0] += 1
        h = {'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (compatible)'}
        try:
            m = json.loads(urllib.request.urlopen(urllib.request.Request(URL, data=b, headers=h), timeout=90).read())['choices'][0]['message']
            return (m.get('content') or '').strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 403): time.sleep(0.4); continue
            return f'[HTTP {e.code}]'
    return '[exhausted]'

stories = {}
for line in open('/tmp/ww.tsv', encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) >= 3: stories[p[1]] = json.loads(p[2])

# off-topic ("foreign") vs on-topic keyword sets, per story
KW = {
 'SMALL': {'topic': 'the Uluru Kakararra hiking trail',
           'foreign': ['indonesia', 'dairy', 'milk', 'sri lanka', 'cyclone', 'ditwah', 'vegetable', 'nuwara', 'badulla', 'food security', 'cheese', 'farmer'],
           'legit': ['uluru', 'trail', 'anangu', 'hike', 'kata tjuta', 'godfrey']},
 'BIG':   {'topic': 'the South African xenophobia / fake-videos controversy',
           'foreign': ['abu dhabi', 'adfd', 'korea', 'critical mineral', 'nurse', 'togo', 'madagascar', 'dairy'],
           'legit': ['xenophob', 'south africa', 'nigeria', 'evacuat', 'video']},
}
def contam(t, bucket):
    tl = t.lower(); return sum(tl.count(w) for w in KW[bucket]['foreign'])
def wc(t): return len(re.findall(r'\S+', t))

def ledger(s, numbered=False):
    facts = s.get('facts') or []
    fl = []
    for i, f in enumerate(facts):
        fl.append((f'[{i}] ' if numbered else '- ') + f"{f.get('fact')}: {f.get('claim')}")
    ql = [f'- "{q.get("quote")}" — {q.get("speaker")}' for q in (s.get('quotes') or [])]
    return 'FACTS:\n' + '\n'.join(fl) + '\nQUOTES:\n' + '\n'.join(ql)

WRITE = "Write a ~250-word neutral news article. Use ONLY the given facts/quotes; invent nothing."

def baseline(s):  # no guard
    return chat([{'role': 'user', 'content': f"{WRITE}\nHEADLINE: {s.get('title')}\n{ledger(s)}"}])

def guardA_segment(s):  # pre-check: segment ledger into events, write the dominant one
    seg = chat([{'role': 'user', 'content':
        "These numbered facts may describe SEVERAL unrelated events. Group them by event. "
        'Output ONLY JSON: {"events":[{"label":"...","facts":[indices]}]}.\n' + ledger(s, numbered=True)}], 800)
    m = re.search(r'\{.*\}', seg, re.S)
    try: evs = json.loads(m.group(0))['events']
    except Exception: evs = [{'label': 'all', 'facts': list(range(len(s.get('facts') or [])))}]
    dom = max(evs, key=lambda e: len(e.get('facts', [])))
    idx = set(dom.get('facts', []))
    facts = [f for i, f in enumerate(s.get('facts') or []) if i in idx]
    sub = dict(s); sub['facts'] = facts; sub['quotes'] = []  # dominant facts only
    art = chat([{'role': 'user', 'content': f"{WRITE}\nWrite about: {dom.get('label')}\n{ledger(sub)}"}])
    return len(evs), [e.get('label') for e in evs], art

def guardB_dominant(s):  # refuse-mixed prompt
    return chat([{'role': 'user', 'content':
        "The facts below MAY describe more than one unrelated event. Identify the SINGLE dominant event "
        "(the one in the headline / with the most facts) and write ~250 words about ONLY that event. "
        f"Ignore and omit any fact about any other event. Invent nothing.\nHEADLINE: {s.get('title')}\n{ledger(s)}"}])

def guardC_postcheck(article):  # one-event verdict
    v = chat([{'role': 'user', 'content':
        "Does this article cover ONE coherent news event, or SEVERAL unrelated events stitched together? "
        'Reply exactly: VERDICT=ONE or VERDICT=SEVERAL, then a short reason.\n\nARTICLE:\n' + article}], 300)
    return 'SEVERAL' if 'SEVERAL' in v.upper() else 'ONE', v[:120]

print("# Anti-contamination guard test\n")
for bucket in ['SMALL', 'BIG']:
    s = stories[bucket]
    print(f"## {bucket}: {s.get('title')[:60]}  (topic = {KW[bucket]['topic']})")
    base = baseline(s)
    bC, bV = contam(base, bucket), guardC_postcheck(base)[0]
    print(f"- BASELINE (no guard):        contamination={bC:2d}  postcheck={bV}  [{wc(base)}w]")
    nE, labels, aA = guardA_segment(s)
    print(f"- GUARD A (segment+dominant): contamination={contam(aA,bucket):2d}  events_found={nE} {labels}")
    aB = guardB_dominant(s)
    cV = guardC_postcheck(aB)[0]
    print(f"- GUARD B (refuse-mixed):     contamination={contam(aB,bucket):2d}  postcheck={cV}  [{wc(aB)}w]")
    print(f"- GUARD C (post-check on baseline): caught_contamination={'YES' if bV=='SEVERAL' else 'no'}")
    print()
