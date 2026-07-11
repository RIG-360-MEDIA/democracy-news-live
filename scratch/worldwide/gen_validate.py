# Validation suite for the open content-gen decisions. Prints a structured report.
import os, re, json, time, urllib.request, urllib.error
KEYS = [x.strip() for x in os.environ['CEREBRAS_API_KEYS'].split(',') if x.strip()]
URL = 'https://api.cerebras.ai/v1/chat/completions'
_i = [0]; _lat = []
def chat(msgs, mt=1400):
    b = json.dumps({'model': 'gpt-oss-120b', 'messages': msgs, 'max_tokens': mt, 'temperature': 0.3}).encode()
    for _ in range(30):
        k = KEYS[_i[0] % len(KEYS)]; _i[0] += 1
        h = {'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (compatible)'}
        try:
            t0 = time.time()
            m = json.loads(urllib.request.urlopen(urllib.request.Request(URL, data=b, headers=h), timeout=120).read())['choices'][0]['message']
            _lat.append(time.time() - t0)
            return (m.get('content') or '').strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 403): time.sleep(0.4); continue
            return f'[HTTP {e.code}]'
    return '[exhausted]'
def wc(t): return len(re.findall(r'\S+', t))
def ungrounded_numbers(article, source):
    sl = source.lower().replace(',', '')
    bad = []
    for n in set(re.findall(r'\d[\d,]*', article)):
        nn = n.replace(',', '')
        if len(nn) >= 2 and not re.search(r'(^|[^\d.])' + re.escape(nn) + r'([^\d.]|$)', sl):
            bad.append(n)
    return len(bad)

# ---- load ladder ----
rows = []
for line in open('/tmp/ladder.tsv', encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) < 6: p += [''] * (6 - len(p))
    rows.append({'ac': int(p[0]), 'isrc': int(p[1]), 'title': p[2], 'facts': p[3], 'quotes': p[4], 'articles': p[5]})
rows.sort(key=lambda r: r['ac'])

LEN = "~300 words. Use ONLY the material; invent nothing; no number/claim not present."
def hybridA(r):  # chrono + persona (rich)
    return chat([{'role': 'system', 'content': "You are an Atlantic staff writer: measured, vivid but exact, strong nut graf, no hype, only what the reporting supports."},
                 {'role': 'user', 'content': f"Write an Atlantic news piece tracing how the story DEVELOPED over time, anchored to the fact spine; focus on the dominant event. {LEN}\nHEADLINE: {r['title']}\nFACTS: {r['facts']}\nQUOTES: {r['quotes']}\nCOVERAGE (chrono): {r['articles']}"}])
def hybridB(r):  # cited-ledger atlantic (honest-when-thin)
    return chat([{'role': 'system', 'content': "You are an Atlantic staff writer with strict sourcing discipline."},
                 {'role': 'user', 'content': f"Write in Atlantic voice but cite-only: every factual sentence must trace to the material; if thin, stay SHORT and honest, flag the unverified. {LEN}\nHEADLINE: {r['title']}\nFACTS: {r['facts']}\nQUOTES: {r['quotes']}"}])
def guardC(article):
    v = chat([{'role': 'user', 'content': "Does this cover ONE coherent event or SEVERAL unrelated events? Reply VERDICT=ONE or VERDICT=SEVERAL.\n\n" + article}], 250)
    return 'SEVERAL' if 'SEVERAL' in v.upper() else 'ONE'

print("# CONTENT-GEN VALIDATION SUITE\n\n## Test 1+5: Boundary (A vs B) + Guard-C reject rate + faithfulness")
print("ac | isrc | A_words A_ungrounded | B_words B_ungrounded | guardC(B)")
several = 0
for r in rows:
    src = r['facts'] + ' ' + r['quotes'] + ' ' + r['articles']
    a = hybridA(r); b = hybridB(r); g = guardC(b)
    if g == 'SEVERAL': several += 1
    print(f"{r['ac']:3d} | {r['isrc']:3d} | A:{wc(a):4d}w u={ungrounded_numbers(a,src):2d} | B:{wc(b):4d}w u={ungrounded_numbers(b,src):2d} | {g}")
print(f"GUARD-C reject rate (current contaminated pool): {several}/{len(rows)} = {round(100*several/len(rows))}%")

print("\n## Test 2: Numeric-disagreement (must report RANGE, not pick)")
for name, src in [('disagree', "Source A: 'At least 20 people were killed.' Source B: 'Officials put the toll at 25 dead.' Source C: '23 confirmed deaths.'"),
                  ('agree', "Source A: '20 killed.' Source B: 'a death toll of 20.'")]:
    out = chat([{'role': 'user', 'content': f"Write one sentence on the death toll using these sources. If they disagree, report the RANGE; never pick one.\n{src}"}], 200)
    print(f"- {name}: {out[:140]}")

print("\n## Test 4: FN/FP at scale (real model entailment)")
S = {'a': "The USMNT led Paraguay 2-0; Balogun scored in the 30th minute. Coach Pochettino's side is ranked 17th.",
     'b': "Chennai petrol is Rs 107.77/litre, diesel Rs 99.55/litre. Oil firms set prices on crude and forex.",
     'c': "Four World Cup matches Saturday: Qatar-Switzerland, Brazil-Morocco, Haiti-Scotland, Australia-Turkiye, in the US and Canada."}
CASES = [('a','The US led Paraguay two-nil.','SUP'),('a','Balogun scored in the 30th minute.','SUP'),('a','Pochettino coaches the US side.','SUP'),
         ('a','Balogun scored an own goal.','BAD'),('a','The US trailed Paraguay.','BAD'),('a','The US is ranked 5th.','BAD'),
         ('b','Diesel is under 100 rupees a litre.','SUP'),('b','Oil firms set fuel prices.','SUP'),
         ('b','Petrol is cheaper than diesel.','BAD'),('b','Petrol costs Rs 200 a litre.','BAD'),('b','The government sets the prices.','BAD'),
         ('c','Scotland play Haiti.','SUP'),('c','Matches are in the US and Canada.','SUP'),
         ('c','All matches are in Qatar.','BAD'),('c','Argentina play Saturday.','BAD'),('c','There are eight matches.','BAD')]
fn = fp = correct = 0
for sk, claim, intended in CASES:
    v = chat([{'role': 'user', 'content': f"Using the SOURCE alone, reply one word SUPPORTED/CONTRADICTED/UNSUPPORTED.\nSOURCE: {S[sk]}\nCLAIM: {claim}"}], 300)
    verdict = (re.findall(r'\b(SUPPORTED|CONTRADICTED|UNSUPPORTED)\b', v.upper()) or ['?'])[-1]
    passed = (verdict == 'SUPPORTED')
    if intended == 'BAD' and passed: fn += 1
    if intended == 'SUP' and not passed: fp += 1
    if (intended == 'SUP') == passed: correct += 1
print(f"cases={len(CASES)} correct={correct} FN(fabrication passed)={fn} FP(faithful flagged)={fp}")

import statistics
print(f"\n## Latency/cost: {len(_lat)} calls, avg {statistics.mean(_lat):.1f}s/call, max {max(_lat):.1f}s")
print("<!-- DONE -->")
