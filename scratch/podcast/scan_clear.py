import os, math, csv, numpy as np, soundfile as sf
from huggingface_hub import hf_hub_download
repo = "sdialog/voices-libritts"
rows = list(csv.DictReader(open(hf_hub_download(repo, "metadata.csv", repo_type="dataset"), encoding="utf-8")))
males = [r for r in rows if r.get("gender") == "M" and float(r.get("total_duration_s") or 0) >= 29 and "clean" in (r.get("subset") or "")]
sample = males[::max(1, len(males)//30)][:30]
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
def centroid(y):
    fr, hop = 2048, 1024; fr_ = np.fft.rfftfreq(fr, 1/24000); cs = []
    for i in range(0, len(y)-fr, hop):
        s = y[i:i+fr]
        if np.sqrt(np.mean(s**2)) < 0.02: continue
        mag = np.abs(np.fft.rfft(s*np.hanning(fr)))
        cs.append(np.sum(fr_*mag)/(np.sum(mag)+1e-9))
    return float(np.median(cs)) if cs else 0.0
best = None
for r in sample:
    try:
        y, sr = sf.read(hf_hub_download(repo, "audio/"+r["file_name"], repo_type="dataset")); y = to24(y, sr)
        p, c = f0(y), centroid(y)
        tag = ""
        if 125 <= p <= 180:  # light/mid, candidate for the clear fast host
            if best is None or c > best[3]: best = (r, y, p, c); tag = " <== candidate"
        print(f"{r['name']:22s} f0={p:3.0f} centroid={c:4.0f}{tag}")
    except Exception as e: print("err", str(e)[:40])
def save(y, fn):
    y = y[:int(24*24000)]; rms = float(np.sqrt(np.mean(y**2)))
    y = np.clip(y*10**((-20-20*math.log10(rms+1e-9))/20), -0.99, 0.99)
    sf.write(os.path.expanduser(r"~\podcast_refs\\"+fn), y, 24000)
save(best[1], "ref_light2.wav")
print(f"CHOSEN_CLEAR_LIGHT={best[0]['name']} f0={best[2]:.0f}Hz centroid={best[3]:.0f}")
