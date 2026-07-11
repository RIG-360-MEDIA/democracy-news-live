import os, numpy as np, soundfile as sf
espeak = r"C:\Program Files\eSpeak NG"
if espeak not in os.environ.get("PATH", ""): os.environ["PATH"] += os.pathsep + espeak
os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", os.path.join(espeak, "libespeak-ng.dll"))
from kokoro import KPipeline
out = os.path.expanduser(r"~\podcast_refs"); os.makedirs(out, exist_ok=True)
pipe = KPipeline(lang_code='a')
refs = {
 'ref_zach.wav':  ('am_adam',  "Hi there, I'm Zach. I love digging into the strange little stories behind everyday things and figuring out how they actually came to be."),
 'ref_emily.wav': ('af_bella', "And I'm Emily. I'm always the one asking the awkward follow up question that nobody else wants to ask out loud."),
}
for fn, (voice, text) in refs.items():
    chunks = [np.asarray(a, dtype=np.float32) for _, _, a in pipe(text, voice=voice)]
    sf.write(os.path.join(out, fn), np.concatenate(chunks), 24000)
    print("wrote", fn)
