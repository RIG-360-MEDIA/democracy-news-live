import os, math, numpy as np, soundfile as sf
src = os.path.expanduser(r"~\voice_dl")
dst = os.path.expanduser(r"~\podcast_refs"); os.makedirs(dst, exist_ok=True)
def load24(p):
    y, sr = sf.read(p)
    if y.ndim > 1: y = y.mean(1)
    y = y.astype(np.float32)
    if sr != 24000:
        n = int(len(y) * 24000 / sr)
        y = np.interp(np.linspace(0, len(y) - 1, n), np.arange(len(y)), y).astype(np.float32)
    return y
def best_window(y, sr=24000, win=20.0):
    fr = int(0.02 * sr)
    e = np.array([np.sqrt(np.mean(y[i:i+fr]**2)) for i in range(0, len(y)-fr, fr)])
    thr = max(0.008, np.percentile(e, 35))
    voiced = (e > thr).astype(float)
    wf = int(win / 0.02)
    if wf >= len(voiced): return 0, y, float(voiced.mean())
    cs = np.cumsum(np.insert(voiced, 0, 0)); step = int(0.5 / 0.02)
    bi, bv = 0, -1
    for i in range(0, len(voiced) - wf, step):
        v = (cs[i+wf] - cs[i]) / wf
        if v > bv: bv, bi = v, i
    s = bi * fr
    return s, y[s:s+int(win*sr)], bv
res = []
for i in range(1, 5):
    p = os.path.join(src, f"voice{i}.wav")
    if not os.path.exists(p): print(f"voice{i} missing"); continue
    y = load24(p); s, seg, v = best_window(y)
    rms = float(np.sqrt(np.mean(seg**2)))
    seg = np.clip(seg * 10**((-20 - 20*math.log10(rms+1e-9))/20), -0.99, 0.99)
    sf.write(os.path.join(dst, f"ref_v{i}.wav"), seg, 24000)
    db = round(20*math.log10(rms+1e-9), 1)
    res.append((i, round(v, 3), db)); print(f"voice{i}: voiced_frac={v:.2f} rms_dbfs={db} start={round(s/24000,1)}s -> ref_v{i}.wav")
res.sort(key=lambda r: -r[1])
print("TOP3_BY_CLEAN_SPEECH:", [r[0] for r in res[:3]])
