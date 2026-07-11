import os, numpy as np, soundfile as sf
espeak = r"C:\Program Files\eSpeak NG"
if espeak not in os.environ.get("PATH", ""): os.environ["PATH"] += os.pathsep + espeak
os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", os.path.join(espeak, "libespeak-ng.dll"))
from kokoro import KPipeline
out = os.path.expanduser(r"~\podcast_refs"); os.makedirs(out, exist_ok=True)
pipe = KPipeline(lang_code='a')
MAN_TEXT = "Hey, welcome back. I'm the one who always brings the skeptical take, so fair warning on that."
WOMAN_TEXT = "And I'm the optimist of the two of us. I get a little too excited about basically everything."
def gen(opts, text, fn):
    for v in opts:
        try:
            chunks = [np.asarray(a, np.float32) for _, _, a in pipe(text, voice=v)]
            sf.write(os.path.join(out, fn), np.concatenate(chunks), 24000)
            print("used", v, "->", fn); return
        except Exception as e:
            print("skip", v, str(e)[:40])
    raise RuntimeError("no voice for " + fn)
gen(['am_michael', 'am_liam', 'am_adam'], MAN_TEXT, "ref_man.wav")      # lighter male
gen(['af_sky', 'af_nicole', 'af_bella'], WOMAN_TEXT, "ref_woman.wav")   # light female
