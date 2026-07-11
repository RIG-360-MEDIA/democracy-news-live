# Real-model validation of the verifier's claim path + enrichment generation.
# Runs inside osint-backend (reads CEREBRAS_API_KEYS from env). Model: gpt-oss-120b.
# Part A: entailment FN/FP on the semantic golden set.
# Part B: enrichment generation (data sheet) + deterministic fact-check loop.
import os, re, json, time, urllib.request, urllib.error

KEYS = [x.strip() for x in os.environ['CEREBRAS_API_KEYS'].split(',') if x.strip()]
URL = 'https://api.cerebras.ai/v1/chat/completions'
_i = [0]

def chat(messages, max_tokens=400):
    b = json.dumps({'model': 'gpt-oss-120b', 'messages': messages, 'max_tokens': max_tokens, 'temperature': 0}).encode()
    last = None
    for _ in range(min(12, len(KEYS))):
        k = KEYS[_i[0] % len(KEYS)]; _i[0] += 1
        h = {'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (compatible)'}
        try:
            msg = json.loads(urllib.request.urlopen(urllib.request.Request(URL, data=b, headers=h), timeout=60).read())['choices'][0]['message']
            return msg.get('content') or msg.get('reasoning') or ''
        except urllib.error.HTTPError as e:
            last = e.code
            if e.code in (429, 403): time.sleep(0.4); continue
            raise
    raise RuntimeError(f'all keys exhausted (last {last})')

S1 = "The USMNT started their World Cup campaign strongly with a 2-0 lead over Paraguay at Los Angeles Stadium. Damian Bobadilla scored an own goal within the first 10 minutes, followed by Folarin Balogun doubling the lead in the 30th minute. Coach Mauricio Pochettino leads the team, ranked 17th by FIFA."
S2 = "In Chennai today (June 13, 2026), petrol is being sold at Rs. 107.77 per litre, diesel at Rs. 99.55 per litre, and CNG at Rs. 96.00 per kg. Oil companies determine prices based on crude oil costs and the rupee-dollar exchange rate."
S3 = "The FIFA World Cup 2026 continues on Saturday, June 13, with four group-stage matches: Qatar vs Switzerland, Brazil vs Morocco, Haiti vs Scotland, and Australia vs Turkiye. Matches take place in the US and Canada."

# (name, source, claim, intended_entailment)  intended SUPPORTED = faithful; else must NOT pass
CASES = [
 ('paraphrase_score', S1, 'The United States led Paraguay two-nil.', 'SUPPORTED'),
 ('attribution_correct', S1, 'Balogun doubled the lead in the 30th minute.', 'SUPPORTED'),
 ('numeric_inference', S2, 'Diesel costs under 100 rupees a litre in Chennai.', 'SUPPORTED'),
 ('fixture_faithful', S3, 'Scotland play Haiti in the group stage.', 'SUPPORTED'),
 ('false_comparison', S2, 'Petrol is cheaper than diesel in Chennai.', 'CONTRADICTED'),
 ('entity_confusion', S1, 'Balogun scored the own goal.', 'CONTRADICTED'),
 ('contradicted_agent', S2, 'The government sets fuel prices in Chennai.', 'CONTRADICTED'),
 ('contradicted_venue', S3, 'All four matches are held in Qatar.', 'CONTRADICTED'),
 ('intent_contradiction', S1, 'Bobadilla deliberately scored for Paraguay.', 'CONTRADICTED'),
 ('plausible_unsupported', S1, 'Pochettino was sacked after the match.', 'UNSUPPORTED'),
 ('unsupported_team', S3, 'Argentina play on June 13.', 'UNSUPPORTED'),
]
PROMPT = "You are a strict faithfulness checker. Using the SOURCE text ALONE (ignore outside knowledge), classify the CLAIM. Reply with exactly one word: SUPPORTED, CONTRADICTED, or UNSUPPORTED.\n\nSOURCE:\n{src}\n\nCLAIM:\n{claim}"

def parse(v):
    found = re.findall(r'\b(SUPPORTED|CONTRADICTED|UNSUPPORTED)\b', v.upper())
    return found[-1] if found else '??'

print("=== PART A: entailment FN/FP (gpt-oss-120b) ===")
fn = fp = correct = 0
for name, src, claim, intended in CASES:
    try:
        got = parse(chat([{'role': 'user', 'content': PROMPT.format(src=src, claim=claim)}], 300))
    except Exception as e:
        got = 'ERR:' + str(getattr(e, 'code', e))[:30]
    faithful_intended = (intended == 'SUPPORTED')
    model_pass = (got == 'SUPPORTED')
    ok = (got == intended) or (not faithful_intended and got in ('CONTRADICTED', 'UNSUPPORTED'))
    # FN = bad claim passed; FP = faithful claim flagged
    if not faithful_intended and model_pass: fn += 1
    if faithful_intended and not model_pass: fp += 1
    if ok: correct += 1
    print(f"{'ok ' if ok else 'XX '}{name}: intended={intended} model={got}")
print(f"--- accuracy {correct}/{len(CASES)} | FN(bad passed)={fn} | FP(faithful flagged)={fp} ---")

print("\n=== PART B: enrichment generation + verify loop ===")
gen_prompt = ("Extract a clean story data sheet from the ARTICLE. Output ONLY a JSON object, "
              "no preamble or explanation, with keys: topic (one word, never OTHER), "
              "headline (<=12 words), summary (<=30 words), facts (list of short strings, each a "
              "single number/fact stated in the article). Use ONLY the article.\n\nARTICLE:\n" + S2)
try:
    raw = chat([{'role': 'user', 'content': gen_prompt}], 2000)
    ms = re.findall(r'\{.*\}', raw, re.S)
    sheet = json.loads(ms[-1]) if ms else {'parse_error': raw[:200]}
    print("GENERATED SHEET:", json.dumps(sheet)[:400])
    # deterministic verify: each numeric fact's number must appear in the source
    src_low = S2.lower()
    for f in sheet.get('facts', [])[:6]:
        nums = re.findall(r'\d[\d,]*(?:\.\d+)?', str(f))
        ok = all(n.replace(',', '') in src_low.replace(',', '') for n in nums) if nums else None
        print(f"  fact={f!r} numbers_grounded={ok}")
except Exception as e:
    print("GEN ERR:", getattr(e, 'code', ''), str(e)[:120])
