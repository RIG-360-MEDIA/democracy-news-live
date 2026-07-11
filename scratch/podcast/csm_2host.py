import os, math, numpy as np, torch, soundfile as sf
from transformers import CsmForConditionalGeneration, AutoProcessor, pipeline
SR = 24000
refs = os.path.expanduser(r"~\podcast_refs")
out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\csm_2host"); os.makedirs(out, exist_ok=True)
def load(fn): w, _ = sf.read(os.path.join(refs, fn)); return w.astype(np.float32)
def f0(y):
    fr, hop = int(0.04*SR), int(0.02*SR); v = []
    for i in range(0, len(y)-fr, hop):
        s = y[i:i+fr]
        if np.sqrt(np.mean(s**2)) < 0.02: continue
        s = s - s.mean(); ac = np.correlate(s, s, 'full')[len(s)-1:]
        lo, hi = int(SR/300), int(SR/70)
        if hi >= len(ac): continue
        p = lo + int(np.argmax(ac[lo:hi]))
        if ac[p] > 0.3*ac[0]: v.append(SR/p)
    return float(np.median(v)) if len(v) > 5 else 0.0
cands = [("ref_m1.wav", load("ref_m1.wav")), ("ref_m2.wav", load("ref_m2.wav")), ("ref_m3.wav", load("ref_m3.wav"))]
pitches = [(n, y, f0(y)) for n, y in cands]
for n, _, p in pitches: print(f"{n}: median_f0={p:.0f} Hz")
pitches.sort(key=lambda t: t[2])
low, high = pitches[0], pitches[-1]   # most distinct pair
print(f"PICKED low={low[0]}({low[2]:.0f}Hz)  high={high[0]}({high[2]:.0f}Hz)")

print("transcribing chosen refs...")
asr = pipeline("automatic-speech-recognition", model="openai/whisper-base.en", device="cuda")
def tx(y): return asr({"array": y, "sampling_rate": SR})["text"].strip()
tlo, thi = tx(low[1]), tx(high[1]); del asr; torch.cuda.empty_cache()

mid = "sesame/csm-1b"
proc = AutoProcessor.from_pretrained(mid)
model = CsmForConditionalGeneration.from_pretrained(mid, device_map="cuda", torch_dtype=torch.float32)
seed = [
 {"role": "0", "content": [{"type": "text", "text": tlo}, {"type": "audio", "audio": low[1]}]},   # deeper
 {"role": "1", "content": [{"type": "text", "text": thi}, {"type": "audio", "audio": high[1]}]},   # higher
]
dialogue = [
 (0, "Okay, did you see this? A company says they actually brought back the dire wolf. Like, the real animal."),
 (1, "Come on. Like the Game of Thrones wolf? No way."),
 (0, "It's real. They edited a gray wolf's genes to match dire wolf DNA. Got these massive white pups."),
 (1, "Okay but is it actually a dire wolf, or just a gray wolf in a costume? Because that's different."),
 (0, "I mean, it's gray-wolf-based. It's like, dire-wolf-flavored."),
 (1, "Dire-wolf-flavored. Haha, I love it."),
 (0, "Here's the thing that worries me though. We can't even keep normal wolves alive. People shoot them. And now we're making designer ones?"),
 (1, "That's actually a fair point."),
 (0, "But get this. The same tech, they wanna bring back the mammoth. And it could actually help the climate."),
 (1, "Whoa, whoa. A mammoth helps the climate? How does that even work?"),
 (0, "They stomp down the snow, keeps the ground frozen, keeps all that carbon locked in. It's a real theory."),
 (1, "Okay, ice age elephants fighting climate change. That's the most metal thing I've ever heard."),
 (0, "Right? What a time to be alive."),
 (1, "Fake wolves I'm still suspicious of. The mammoths, though, I'm in."),
 (0, "Haha. Fair enough."),
]
WINDOW = 4
recent, segs, short = [], [], []
for i, (spk, text) in enumerate(dialogue):
    conv = seed + recent[-WINDOW:] + [{"role": str(spk), "content": [{"type": "text", "text": text}]}]
    inputs = proc.apply_chat_template(conv, tokenize=True, return_dict=True).to(model.device)
    oa = model.generate(**inputs, output_audio=True, max_new_tokens=375, do_sample=True, temperature=0.9, top_k=50)
    wav = oa[0].detach().to(torch.float32).cpu().numpy()
    segs.append(wav); short.append(len(text.split()) <= 5)
    recent.append({"role": str(spk), "content": [{"type": "text", "text": text}, {"type": "audio", "audio": wav}]})
    print("turn", i+1, "spk", spk, round(len(wav)/SR, 1), "s")
starts = [0]
for i in range(1, len(segs)):
    pe = starts[i-1] + len(segs[i-1]); lead = int((0.2 if short[i] else -0.08)*SR)
    starts.append(max(0, pe-lead))
total = max(s+len(w) for s, w in zip(starts, segs)); mix = np.zeros(total, dtype=np.float32)
for s, w in zip(starts, segs): mix[s:s+len(w)] += w
def comp(x, thr=0.12, r=3.0):
    a = np.abs(x)+1e-9; g = np.where(a > thr, (thr+(a-thr)/r)/a, 1.0); k = max(1, int(0.006*SR))
    return (x*np.convolve(g, np.ones(k)/k, 'same')).astype(np.float32)
def rev(x, wet=0.07):
    o = x.copy()
    for ms, d in [(23, .6), (37, .45), (53, .35), (71, .25)]:
        n = int(ms/1000*SR); e = np.zeros_like(x); e[n:] = x[:-n]*d; o = o+e*wet
    return o
mm = rev(comp(mix)); rms = float(np.sqrt(np.mean(mm**2)))
mm = np.clip(mm*10**((-16-20*math.log10(rms+1e-9))/20), -0.99, 0.99)
sf.write(os.path.join(out, "episode_2host.wav"), mm, SR)
print("WROTE episode_2host.wav", round(len(mm)/SR, 1), "sec")
