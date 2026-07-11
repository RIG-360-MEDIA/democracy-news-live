# Worldwide content-gen bake-off: 5 strategies x 3 stories, Atlantic length.
# Reads /tmp/ww.tsv (story_id \t bucket \t json). Prints markdown to stdout.
import os, re, json, time, urllib.request, urllib.error

KEYS = [x.strip() for x in os.environ['CEREBRAS_API_KEYS'].split(',') if x.strip()]
URL = 'https://api.cerebras.ai/v1/chat/completions'
_i = [0]

def chat(messages, max_tokens=4000):
    b = json.dumps({'model': 'gpt-oss-120b', 'messages': messages, 'max_tokens': max_tokens, 'temperature': 0.35}).encode()
    last = None
    for _ in range(min(25, len(KEYS) * 2)):
        k = KEYS[_i[0] % len(KEYS)]; _i[0] += 1
        h = {'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (compatible)'}
        try:
            m = json.loads(urllib.request.urlopen(urllib.request.Request(URL, data=b, headers=h), timeout=120).read())['choices'][0]['message']
            return (m.get('content') or '').strip()
        except urllib.error.HTTPError as e:
            last = e.code
            if e.code in (429, 403): time.sleep(0.5); continue
            return f'[HTTP {e.code}: {e.read().decode()[:80]}]'
        except Exception as e:
            return f'[ERR {str(e)[:80]}]'
    return f'[keys exhausted {last}]'

def wc(t): return len(re.findall(r'\S+', t))

# ---------- input formatters ----------
def f_anchor(s):
    ents = ', '.join(list((s.get('entities') or {}).keys())[:10]) if isinstance(s.get('entities'), dict) else ''
    return (f"HEADLINE: {s.get('title')}\nTOPIC: {s.get('topic')}\nPLACE: {s.get('subject_country')}/{s.get('subject_region')}\n"
            f"KEY ENTITIES: {ents}\nCOVERAGE: {s.get('article_count')} articles, {s.get('source_count')} independent sources")

def f_facts(s):
    out = []
    for f in (s.get('facts') or []):
        v = f.get('latest') or f.get('max') or f.get('min')
        u = (f.get('unit') or '')
        c = f.get('claim') or f.get('fact')
        out.append(f"- {f.get('fact')}: {v}{(' ' + u) if u else ''} — \"{c}\" [{f.get('n_sources')} sources]")
    return '\n'.join(out) if out else '(no structured facts — single source)'

def f_quotes(s):
    out = [f'- "{q.get("quote")}" — {q.get("speaker") or "unattributed"}' for q in (s.get('quotes') or [])]
    return '\n'.join(out) if out else '(no quotes)'

def f_articles(s):
    out = []
    for a in (s.get('articles') or []):
        body = (a.get('summary') or a.get('lead') or '').strip().replace('\n', ' ')
        out.append(f"[{a.get('date')}] {a.get('title')}\n    {body[:400]}")
    return '\n'.join(out) if out else '(no member articles)'

LEN = ("Length: write a full Atlantic-style piece as long as the FACTS faithfully support "
       "(~800-1100 words when well-sourced; shorter if the material is thin). NEVER pad, repeat, "
       "or invent to reach a length. Quality and fidelity over length.")
GROUND = "Use ONLY the information provided below. Invent nothing. If a detail is not present, omit it. Do not state any number, name, or claim not given."

# ---------- 5 WAYS (each a different prompt strategy) ----------
def way1_ledger(s):  # Fact-ledger structured, XML-tagged, strict grounding
    p = (f"You are a precise newswriter. Write a clear, analytical news article in a neutral house voice, working ONLY from the "
         f"structured data between the XML tags. {GROUND}\n\nStructure: a vivid but factual LEDE, then a NUT GRAF (by paragraph 2) "
         f"explaining why it matters, then body paragraphs that weave the facts and quotes, then a forward-looking KICKER. "
         f"Distinguish confirmed facts from attributed claims.\n{LEN}\n\n"
         f"<anchor>\n{f_anchor(s)}\n</anchor>\n<facts>\n{f_facts(s)}\n</facts>\n<quotes>\n{f_quotes(s)}\n</quotes>")
    return chat([{'role': 'user', 'content': p}])

def way2_chrono(s):  # Chronological digest + ledger spine -> development arc
    p = (f"You are a senior correspondent writing an explanatory piece. Below is the coverage of one story in CHRONOLOGICAL order, "
         f"plus a VERIFIED FACT SPINE. Write an Atlantic-style article that conveys HOW THE STORY DEVELOPED over time — what was "
         f"known first, what emerged, how it escalated or resolved — anchored strictly to the fact spine. {GROUND} Attribute reported "
         f"claims. Open on the most consequential turn, not a dry summary.\n{LEN}\n\n"
         f"ANCHOR:\n{f_anchor(s)}\n\nVERIFIED FACT SPINE:\n{f_facts(s)}\n\nKEY QUOTES:\n{f_quotes(s)}\n\nCHRONOLOGICAL COVERAGE:\n{f_articles(s)}")
    return chat([{'role': 'user', 'content': p}])

def way3_outline(s):  # Two-pass: outline then write
    o = (f"Plan an Atlantic-style article from the material below. Output ONLY compact JSON: "
         f'{{"angle":"...","lede":"one vivid factual opening image","nutgraf":"why it matters in one sentence",'
         f'"beats":["beat1","beat2","beat3","beat4"],"key_quotes":["...","..."],"kicker":"forward-looking close"}}. '
         f"Base every element ONLY on the material. {GROUND}\n\nANCHOR:\n{f_anchor(s)}\nFACTS:\n{f_facts(s)}\nQUOTES:\n{f_quotes(s)}\nARTICLES:\n{f_articles(s)}")
    outline = chat([{'role': 'user', 'content': o}], 1500)
    p = (f"Write the full Atlantic-style article from this OUTLINE, using ONLY the supporting MATERIAL for facts/quotes. {GROUND} "
         f"Follow the outline's angle, open on its lede, land the nutgraf by paragraph two, develop each beat into a paragraph, "
         f"weave the quotes naturally, end on the kicker.\n{LEN}\n\nOUTLINE:\n{outline}\n\nMATERIAL:\n{f_anchor(s)}\nFACTS:\n{f_facts(s)}\nQUOTES:\n{f_quotes(s)}")
    return chat([{'role': 'user', 'content': p}])

EXEMPLAR = ("STYLE EXEMPLAR (voice only, unrelated topic): \"For a decade the dam had been a promise more than a place. "
            "Now the water was rising, and with it a question the engineers had deferred for years: who, exactly, had agreed to this? "
            "The answer, it turned out, was almost no one.\"")
def way4_persona(s):  # Editor persona + style exemplar
    sysmsg = ("You are a staff writer for The Atlantic. Your voice is measured, analytical, and vivid but exact; you favor a strong "
              "nut graf, concrete detail over adjectives, and you never hype. You write only what the reporting supports.")
    p = (f"{EXEMPLAR}\n\nMatch that VOICE (not its content). Write an Atlantic feature-news article on the story below. {GROUND} "
         f"Facts come only from the data; the craft and voice come from you.\n{LEN}\n\n"
         f"ANCHOR:\n{f_anchor(s)}\nFACTS:\n{f_facts(s)}\nQUOTES:\n{f_quotes(s)}\nCOVERAGE:\n{f_articles(s)}")
    return chat([{'role': 'system', 'content': sysmsg}, {'role': 'user', 'content': p}])

def way5_citation(s):  # Inverted-pyramid + mandatory citation + self-check
    p = (f"Write a rigorously sourced news article as FLOWING PROSE (not headers), internally organized as: lede; nut graf (why it "
         f"matters) by paragraph two; context; the key facts (each traceable to a provided fact, noting how many sources confirm it); "
         f"the voices (quotes); and what's next. {GROUND} RULE: every factual sentence must trace to a provided FACT or QUOTE. "
         f"After drafting, silently DELETE any sentence you cannot trace, then output ONLY the clean final article.\n{LEN}\n\n"
         f"ANCHOR:\n{f_anchor(s)}\nFACTS (with source counts):\n{f_facts(s)}\nQUOTES:\n{f_quotes(s)}")
    return chat([{'role': 'user', 'content': p}])

WAYS = [('Way 1 — Fact-Ledger Structured', way1_ledger),
        ('Way 2 — Chronological Digest + Ledger', way2_chrono),
        ('Way 3 — Two-Pass Outline -> Write', way3_outline),
        ('Way 4 — Editor-Persona + Style-Exemplar', way4_persona),
        ('Way 5 — Inverted-Pyramid + Mandatory-Citation', way5_citation)]

stories = {}
for line in open('/tmp/ww.tsv', encoding='utf-8'):
    parts = line.rstrip('\n').split('\t')
    if len(parts) < 3: continue
    stories[parts[1]] = json.loads(parts[2])

print("# Worldwide Content-Gen Bake-off — 5 strategies x 3 stories (gpt-oss-120b)\n")
for bucket in ['BIG', 'SMALL', 'ONE']:
    s = stories.get(bucket)
    if not s: continue
    print(f"\n---\n# STORY [{bucket}]: {s.get('title')}")
    print(f"_{s.get('article_count')} articles · {s.get('source_count')} sources · topic={s.get('topic')} · "
          f"{len(s.get('facts') or [])} facts · {len(s.get('quotes') or [])} quotes_\n")
    for label, fn in WAYS:
        try:
            art = fn(s)
        except Exception as e:
            art = f'[generation failed: {str(e)[:100]}]'
        print(f"\n## {bucket} · {label}  [{wc(art)} words]\n")
        print(art + "\n")
print("\n<!-- DONE -->")
