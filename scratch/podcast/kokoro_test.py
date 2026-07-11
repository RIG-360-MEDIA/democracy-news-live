import os, numpy as np, soundfile as sf
espeak = r"C:\Program Files\eSpeak NG"
if espeak not in os.environ.get("PATH", ""):
    os.environ["PATH"] += os.pathsep + espeak
os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", os.path.join(espeak, "libespeak-ng.dll"))
from kokoro import KPipeline

out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\kokoro_test")
os.makedirs(out, exist_ok=True)
pipe = KPipeline(lang_code='a')  # American English

dialogue = [
 ('am_adam',  "Welcome back to the show. Today, a little piece of history that's probably sitting in a drawer in your house right now: bubble wrap."),
 ('af_bella', "Oh, I love bubble wrap. But here's the twist, Zach. It was never supposed to be packaging at all."),
 ('am_adam',  "Right. Back in 1957, two engineers were actually trying to invent textured wallpaper. They sealed two shower curtains together and trapped the air bubbles inside."),
 ('af_bella', "The wallpaper flopped, the greenhouse insulation idea flopped, and then someone realized IBM could use it to protect computers during shipping."),
 ('am_adam',  "And that is how a failed wallpaper became a billion dollar packaging empire. There is even research saying popping it relieves stress."),
 ('af_bella', "Which is why people were furious when they later invented a version that does not pop. Thanks for listening, everyone."),
]

sr = 24000
chunks = []
silence = np.zeros(int(0.35 * sr), dtype=np.float32)
for voice, text in dialogue:
    for gs, ps, audio in pipe(text, voice=voice):
        chunks.append(np.asarray(audio, dtype=np.float32))
    chunks.append(silence)

full = np.concatenate(chunks)
path = os.path.join(out, "episode.wav")
sf.write(path, full, sr)
print("WROTE", path, round(len(full) / sr, 1), "sec")
