import os, numpy as np, soundfile as sf
espeak = r"C:\Program Files\eSpeak NG"
if espeak not in os.environ.get("PATH", ""): os.environ["PATH"] += os.pathsep + espeak
os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", os.path.join(espeak, "libespeak-ng.dll"))
from kokoro import KPipeline
out = os.path.expanduser(r"~\podcast_refs"); os.makedirs(out, exist_ok=True)
pipe = KPipeline(lang_code='a')
used = set()
sets = [
 (['am_michael', 'am_liam', 'am_adam'],  "ref_m1.wav", "Yo, what's up everybody, welcome back to the show. Good to have you guys here today."),
 (['am_eric', 'am_puck', 'am_echo'],     "ref_m2.wav", "Dude, I'm telling you, I came in today with way too many tabs open in my brain."),
 (['am_onyx', 'am_fenrir', 'am_santa'],  "ref_m3.wav", "Alright, alright, let's get into it. I've been looking forward to this one all week, man."),
]
for opts, fn, text in sets:
    for v in opts:
        if v in used: continue
        try:
            chunks = [np.asarray(a, np.float32) for _, _, a in pipe(text, voice=v)]
            sf.write(os.path.join(out, fn), np.concatenate(chunks), 24000)
            used.add(v); print("used", v, "->", fn); break
        except Exception as e:
            print("skip", v, str(e)[:40])
