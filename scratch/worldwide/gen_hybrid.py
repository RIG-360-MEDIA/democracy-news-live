# Hybrid strategies vs individuals.
# Hybrid A (2+4): Atlantic persona voice + chronological development arc -> BIG story.
# Hybrid B (1+5+4): Atlantic voice + strict ledger grounding + citation/self-check, honest-when-thin -> SINGLE.
import os, re, json, time, urllib.request, urllib.error
KEYS = [x.strip() for x in os.environ['CEREBRAS_API_KEYS'].split(',') if x.strip()]
URL = 'https://api.cerebras.ai/v1/chat/completions'
_i = [0]
def chat(msgs, mt=3600):
    b = json.dumps({'model': 'gpt-oss-120b', 'messages': msgs, 'max_tokens': mt, 'temperature': 0.3}).encode()
    for _ in range(25):
        k = KEYS[_i[0] % len(KEYS)]; _i[0] += 1
        h = {'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (compatible)'}
        try:
            m = json.loads(urllib.request.urlopen(urllib.request.Request(URL, data=b, headers=h), timeout=120).read())['choices'][0]['message']
            return (m.get('content') or '').strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 403): time.sleep(0.4); continue
            return f'[HTTP {e.code}]'
    return '[exhausted]'
def wc(t): return len(re.findall(r'\S+', t))

stories = {}
for line in open('/tmp/ww.tsv', encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) >= 3: stories[p[1]] = json.loads(p[2])

def f_facts(s):
    return '\n'.join(f"- {f.get('fact')}: {f.get('claim')}" for f in (s.get('facts') or [])) or '(none)'
def f_quotes(s):
    return '\n'.join(f'- "{q.get("quote")}" — {q.get("speaker")}' for q in (s.get('quotes') or [])) or '(none)'
def f_articles(s):
    return '\n'.join(f"[{a.get('date')}] {a.get('title')}: {(a.get('summary') or a.get('lead') or '')[:350]}" for a in (s.get('articles') or [])) or '(none)'
def f_anchor(s):
    return f"HEADLINE: {s.get('title')}\nTOPIC: {s.get('topic')} · {s.get('subject_country')} · {s.get('article_count')} articles / {s.get('source_count')} sources"

PERSONA = ("You are a staff writer for The Atlantic. Your voice is measured, analytical, vivid but exact; you favor a strong "
           "nut graf, concrete detail over adjectives, and you never hype. You write only what the reporting supports.")
EXEMPLAR = ("STYLE EXEMPLAR (voice only): \"For a decade the dam had been a promise more than a place. Now the water was rising, "
            "and with it a question the engineers had deferred for years: who, exactly, had agreed to this?\"")

# ---- Hybrid A (2+4) on BIG ----
sBIG = stories['BIG']
hA = chat([{'role': 'system', 'content': PERSONA},
           {'role': 'user', 'content':
            f"{EXEMPLAR}\n\nMatch that VOICE (not its content). Write an Atlantic feature that TRACES HOW THIS STORY DEVELOPED over "
            f"time — what surfaced first, what emerged, how it escalated — anchored strictly to the VERIFIED FACT SPINE; use the "
            f"dated coverage for the arc. Focus on the single dominant event; omit facts about unrelated events. Open on the most "
            f"consequential turn. Use ONLY the material; invent nothing.\n\n{f_anchor(sBIG)}\n\nFACT SPINE:\n{f_facts(sBIG)}\n\n"
            f"QUOTES:\n{f_quotes(sBIG)}\n\nCHRONOLOGICAL COVERAGE:\n{f_articles(sBIG)}"}])

# ---- Hybrid B (1+5+4) on SINGLE ----
sONE = stories['ONE']
one_material = f_anchor(sONE) + "\n\nARTICLE MATERIAL:\n" + f_articles(sONE)
hB = chat([{'role': 'system', 'content': PERSONA},
           {'role': 'user', 'content':
            f"Write in your Atlantic voice, but with STRICT discipline: use ONLY the material below; every factual sentence must "
            f"trace to it; after drafting, silently delete anything you cannot support. CRITICAL: if the material is thin, keep the "
            f"piece SHORT and honest — do NOT invent scenes, context, drama, or detail to reach a length. Length follows the facts. "
            f"State plainly what is and isn't confirmed.\n\n{one_material}"}], 1500)

print("# Hybrid vs Individual\n")
print(f"## HYBRID A (Way 2+4) — BIG story  [{wc(hA)} words]")
print("(compare: individual Way 2 = 1182w, Way 4 = 1377w)\n")
print(hA + "\n")
print("\n---\n")
print(f"## HYBRID B (Way 1+5+4) — SINGLE story  [{wc(hB)} words]")
print("(compare: individual Way 1 = 220w, Way 5 = 94w, Way 4 = 759w)\n")
# honesty scan: did it invent the Way-3-style drama?
halluc = [w for w in ['hidden message', 'login session', 'live wire', 'razor', 'flashes', 'glitch', 'buried in the'] if w in hB.lower()]
print(f"_hallucination-marker scan: {halluc or 'none found'}_\n")
print(hB + "\n")
