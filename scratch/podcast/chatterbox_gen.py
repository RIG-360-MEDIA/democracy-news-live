import os, math, numpy as np, soundfile as sf
from chatterbox.tts import ChatterboxTTS
refs = os.path.expanduser(r"~\podcast_refs")
out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\chatterbox_test"); os.makedirs(out, exist_ok=True)
Z = os.path.join(refs, "ref_zach.wav"); E = os.path.join(refs, "ref_emily.wav")
print("loading model...")
model = ChatterboxTTS.from_pretrained(device="cuda")
sr = model.sr
dialogue = [
 (Z, "Welcome back to the show. Today, a little piece of history that's probably sitting in a drawer in your house right now: bubble wrap."),
 (E, "Oh, I love bubble wrap. But here's the twist, Zach. It was never supposed to be packaging at all."),
 (Z, "Right. Back in 1957, two engineers were actually trying to invent textured wallpaper. They sealed two shower curtains together and trapped the air bubbles inside."),
 (E, "The wallpaper flopped, the greenhouse insulation idea flopped, and then someone realized IBM could use it to protect computers during shipping."),
 (Z, "And that is how a failed wallpaper became a billion dollar packaging empire. There is even research saying popping it relieves stress."),
 (E, "Which is why people were furious when they later invented a version that does not pop. Thanks for listening, everyone."),
]
def trim(x, sr, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0: return x
    a = max(0, idx[0] - int(0.03*sr)); b = min(len(x), idx[-1] + int(0.06*sr)); return x[a:b]
segs = []
for i, (ref, text) in enumerate(dialogue):
    wav = model.generate(text, audio_prompt_path=ref, exaggeration=0.5, cfg_weight=0.4)
    x = wav.squeeze(0).detach().cpu().numpy().astype(np.float32)
    segs.append(trim(x, sr)); segs.append(np.zeros(int(0.28*sr), dtype=np.float32))
    print("line", i + 1, "done")
full = np.concatenate(segs)
rms = float(np.sqrt(np.mean(full**2)))
gain = 10 ** ((-16 - 20*math.log10(rms + 1e-9)) / 20)   # normalize to -16 dBFS
full = np.clip(full * gain, -0.99, 0.99)
path = os.path.join(out, "episode_chatterbox.wav")
sf.write(path, full, sr)
print("WROTE", path, round(len(full)/sr, 1), "sec sr", sr,
      "rms_dbfs", round(20*math.log10(float(np.sqrt(np.mean(full**2))) + 1e-9), 1))
