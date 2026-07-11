import os, math, json, numpy as np, soundfile as sf
from datasets import load_dataset
out = os.path.expanduser(r"~\podcast_refs"); os.makedirs(out, exist_ok=True)
print("loading sdialog/voices-libritts (streaming)...")
ds = load_dataset("sdialog/voices-libritts", split="train", streaming=True)
def txt(r):
    for k in ('text', 'transcript', 'text_normalized', 'sentence', 'text_original'):
        if k in r and r[k]: return str(r[k])
    return ""
picked, manifest, first = [], {}, True
for r in ds:
    if first:
        print("COLUMNS:", sorted(r.keys()))
        print("META:", {k: str(v)[:50] for k, v in r.items() if k != 'audio'})
        first = False
    g = ""
    for gk in ('gender', 'sex', 'speaker_gender'):
        if gk in r: g = str(r[gk]).lower(); break
    is_male = g.startswith('m') and 'female' not in g
    if g == "" or is_male:
        a = np.asarray(r['audio']['array'], dtype=np.float32); sr = r['audio']['sampling_rate']
        if len(a) / sr < 6:  # need enough reference
            continue
        spk = str(r.get('speaker_id', r.get('speaker', r.get('id', '?'))))
        picked.append((spk, g, a, sr, txt(r)[:300]))
        if len(picked) >= 3: break
for i, (spk, g, a, sr, t) in enumerate(picked, 1):
    rms = float(np.sqrt(np.mean(a**2)))
    a = np.clip(a * 10**((-20 - 20*math.log10(rms+1e-9))/20), -0.99, 0.99)
    fn = f"ref_v{i}.wav"; sf.write(os.path.join(out, fn), a, sr)
    manifest[fn] = {"speaker": spk, "gender": g, "text": t, "sr": sr}
    print(f"{fn} <- spk {spk} gender={g} dur={round(len(a)/sr,1)}s sr={sr} :: {t[:60]}")
json.dump(manifest, open(os.path.join(out, "refs_manifest.json"), "w"))
print("DONE", len(picked))
