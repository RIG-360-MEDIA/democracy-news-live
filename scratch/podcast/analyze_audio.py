import os, math, numpy as np, soundfile as sf
p = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\kokoro_test\episode.wav")
y, sr = sf.read(p)
ch = 1 if y.ndim == 1 else y.shape[1]
if y.ndim > 1: y = y.mean(axis=1)
y = y.astype(np.float64)
dur = len(y) / sr
peak = float(np.max(np.abs(y)))
rms = float(np.sqrt(np.mean(y**2)))
db = lambda v: 20*math.log10(v+1e-9)
fr = int(0.02*sr)
loud = np.array([np.sqrt(np.mean(y[i:i+fr]**2)) for i in range(0, len(y)-fr, fr)])
thr = 0.02
sil = loud < thr
# silence runs
runs, cur = [], 0
for s in sil:
    if s: cur += 1
    elif cur: runs.append(cur*0.02); cur = 0
if cur: runs.append(cur*0.02)
gaps = [round(r, 2) for r in runs if r >= 0.2]
clip = int(np.sum(np.abs(y) > 0.99))
# crest factor (dynamics)
print(f"sr={sr}Hz channels={ch} dur={dur:.1f}s")
print(f"peak={peak:.3f} ({db(peak):.1f} dBFS)  RMS={db(rms):.1f} dBFS  crest={db(peak)-db(rms):.1f}dB")
print(f"silence_fraction={np.mean(sil):.2f}  clipped_samples={clip}")
print(f"gaps>=0.2s (count={len(gaps)}): {gaps[:20]}")
print(f"loudness_std={np.std(loud[loud>thr]):.4f} (higher=more dynamic prosody)")
