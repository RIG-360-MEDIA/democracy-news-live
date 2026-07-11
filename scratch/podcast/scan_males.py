import os, math, csv, numpy as np, soundfile as sf
from huggingface_hub import hf_hub_download
repo = "sdialog/voices-libritts"
rows = list(csv.DictReader(open(hf_hub_download(repo, "metadata.csv", repo_type="dataset"), encoding="utf-8")))
males = [r for r in rows if r.get("gender") == "M" and float(r.get("total_duration_s") or 0) >= 29 and "clean" in (r.get("subset") or "")]
sample = males[::max(1, len(males)//24)][:24]
def to24(y, sr):
    if y.ndim > 1: y = y.mean(1)
    y = y.astype(np.float32)
    if sr != 24000:
        n = int(len(y)*24000/sr); y = np.interp(np.linspace(0, len(y)-1, n), np.arange(len(y)), y).astype(np.float32)
    return y
def f0(y):
    fr, hop = int(0.04*24000), int(0.02*24000); v = []
    for i in range(0, len(y)-fr, hop):
        s = y[i:i+fr]
        if np.sqrt(np.mean(s**2)) < 0.02: continue
        s = s-s.mean(); ac = np.correlate(s, s, 'full')[len(s)-1:]; lo, hi = int(24000/300), int(24000/70)
        if hi >= len(ac): continue
        p = lo+int(np.argmax(ac[lo:hi]))
        if ac[p] > 0.3*ac[0]: v.append(24000/p)
    return float(np.median(v)) if len(v) > 5 else 0.0
scored = []
for r in sample:
    try:
        y, sr = sf.read(hf_hub_download(repo, "audio/"+r["file_name"], repo_type="dataset"))
        p = f0(to24(y, sr))
        if p > 0: scored.append((p, r, to24(y, sr))); print(r["name"], round(p), "Hz")
    except Exception as e: print("err", str(e)[:40])
scored.sort(key=lambda t: t[0])
deep, light = scored[0], scored[-1]
def save(y, fn):
    y = y[:int(24*24000)]; rms = float(np.sqrt(np.mean(y**2)))
    y = np.clip(y*10**((-20-20*math.log10(rms+1e-9))/20), -0.99, 0.99)
    sf.write(os.path.expanduser(r"~\podcast_refs\\"+fn), y, 24000)
save(deep[2], "ref_deep.wav"); save(light[2], "ref_light.wav")
print(f"DEEP={deep[1]['name']} {deep[0]:.0f}Hz | LIGHT={light[1]['name']} {light[0]:.0f}Hz")
