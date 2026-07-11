import os, shutil, statistics, numpy as np, soundfile as sf
src = open(os.path.expanduser('~/run_csm_ref.py'), encoding='utf-8', errors='ignore').read()
i = src.find('SPEAKER_PROMPTS'); j = src.find('def load_prompt_audio')
print('=== PROMPTS BLOCK ===')
print(src[i:j][:1700])
from huggingface_hub import hf_hub_download
def med_f0(y, sr):
    fr = int(0.04*sr); f0 = []
    for k in range(0, len(y)-fr, int(0.02*sr)):
        s = y[k:k+fr]
        if np.sqrt(np.mean(s**2)) < 0.02: continue
        s = s - s.mean(); ac = np.correlate(s, s, 'full')[len(s)-1:]
        lo, hi = int(sr/350), int(sr/75)
        if hi < len(ac):
            pk = lo + int(np.argmax(ac[lo:hi]))
            if ac[pk] > 0.3*ac[0]: f0.append(sr/pk)
    return round(statistics.median(f0)) if f0 else None
print('=== DOWNLOAD + PITCH ===')
for name in ['conversational_a', 'conversational_b']:
    p = hf_hub_download('sesame/csm-1b', f'prompts/{name}.wav')
    dst = os.path.expanduser('~/podcast_refs/' + name + '.wav'); shutil.copy(p, dst)
    y, sr = sf.read(dst)
    if y.ndim > 1: y = y.mean(1)
    f0 = med_f0(y.astype(np.float64), sr)
    print(name, 'sr', sr, 'dur', round(len(y)/sr, 1), 'med_f0', f0, '->', ('MALE' if (f0 or 200) < 165 else 'FEMALE'))
