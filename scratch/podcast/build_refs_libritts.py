import os, math, csv, numpy as np, soundfile as sf
from huggingface_hub import hf_hub_download
repo = "sdialog/voices-libritts"
mp = hf_hub_download(repo, "metadata.csv", repo_type="dataset")
rows = list(csv.DictReader(open(mp, encoding="utf-8")))
males = [r for r in rows if r.get("gender") == "M"
         and float(r.get("total_duration_s") or 0) >= 28
         and "clean" in (r.get("subset") or "")]
print("males_available", len(males))
idxs = [8, len(males)//2, len(males)-8]
pick = [males[i] for i in idxs]
dst = os.path.expanduser(r"~\podcast_refs"); os.makedirs(dst, exist_ok=True)
for k, row in enumerate(pick, 1):
    src = hf_hub_download(repo, "audio/" + row["file_name"], repo_type="dataset")
    y, sr = sf.read(src)
    if y.ndim > 1: y = y.mean(1)
    y = y.astype(np.float32)
    if sr != 24000:
        n = int(len(y)*24000/sr); y = np.interp(np.linspace(0, len(y)-1, n), np.arange(len(y)), y).astype(np.float32)
    y = y[:int(24*24000)]
    rms = float(np.sqrt(np.mean(y**2)))
    y = np.clip(y*10**((-20 - 20*math.log10(rms+1e-9))/20), -0.99, 0.99)
    sf.write(os.path.join(dst, f"ref_m{k}.wav"), y, 24000)
    print(f"ref_m{k} = {row['name']} | id {row['identifier']} | {row['subset']} | {round(len(y)/24000,1)}s")
