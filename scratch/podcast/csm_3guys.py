import os, math, numpy as np, torch, soundfile as sf
from transformers import CsmForConditionalGeneration, AutoProcessor
mid = "sesame/csm-1b"
proc = AutoProcessor.from_pretrained(mid)
model = CsmForConditionalGeneration.from_pretrained(mid, device_map="cuda", torch_dtype=torch.float32)
SR = 24000
refs = os.path.expanduser(r"~\podcast_refs")
out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\csm_3guys"); os.makedirs(out, exist_ok=True)
def load(fn): w, _ = sf.read(os.path.join(refs, fn)); return w.astype(np.float32)
S = [
 ("Yo, what's up everybody, welcome back to the show. Good to have you guys here today.", "ref_m1.wav"),
 ("Dude, I'm telling you, I came in today with way too many tabs open in my brain.", "ref_m2.wav"),
 ("Alright, alright, let's get into it. I've been looking forward to this one all week, man.", "ref_m3.wav"),
]
seed = [{"role": str(i), "content": [{"type": "text", "text": t}, {"type": "audio", "audio": load(f)}]} for i, (t, f) in enumerate(S)]
dialogue = [
 (0, "Dude, did you guys see this? A company says they actually brought back the dire wolf. Like, the real animal."),
 (1, "Bro, come on. Like the Game of Thrones wolf? No way."),
 (2, "No, it's real, I read about this. They edited a gray wolf's genes to match dire wolf DNA. Got these massive white pups."),
 (0, "It's insane, right? We're living in the future."),
 (1, "Okay but is it actually a dire wolf, or is it just a gray wolf in a costume? Because that's different, man."),
 (2, "I mean, it's gray-wolf-based. It's like, dire-wolf-flavored."),
 (0, "Dire-wolf-flavored. Haha, I love it."),
 (1, "See, that's the thing that gets me. We can't even keep normal wolves alive, dude. People shoot 'em. And now we're making designer ones?"),
 (2, "That's a fair point, actually."),
 (0, "Okay but here's where it gets crazy. The same tech, they wanna bring back the mammoth. And get this, it could actually help the climate."),
 (1, "Whoa, whoa. A mammoth helps the climate? How does that even work?"),
 (2, "It's wild. They stomp down the snow, keeps the ground frozen, keeps all that carbon locked in the ground. It's a real theory."),
 (0, "Bro, ice age elephants fighting climate change. That's the most metal thing I've ever heard."),
 (1, "Okay, that one I'm actually on board with. The fake wolves, I'm still suspicious."),
 (2, "Haha, fair. Skeptic to the end."),
 (0, "Dude. What a time to be alive."),
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
    print("turn", i + 1, "spk", spk, "done", round(len(wav) / SR, 1), "s")
starts = [0]
for i in range(1, len(segs)):
    pe = starts[i-1] + len(segs[i-1]); lead = int((0.2 if short[i] else -0.08) * SR)
    starts.append(max(0, pe - lead))
total = max(s + len(w) for s, w in zip(starts, segs))
mix = np.zeros(total, dtype=np.float32)
for s, w in zip(starts, segs): mix[s:s+len(w)] += w
def compress(x, thr=0.12, ratio=3.0):
    a = np.abs(x) + 1e-9; g = np.where(a > thr, (thr + (a - thr)/ratio)/a, 1.0)
    k = max(1, int(0.006*SR)); return (x*np.convolve(g, np.ones(k)/k, 'same')).astype(np.float32)
def reverb(x, wet=0.08):
    o = x.copy()
    for ms, d in [(23, 0.6), (37, 0.45), (53, 0.35), (71, 0.25)]:
        n = int(ms/1000*SR); e = np.zeros_like(x); e[n:] = x[:-n]*d; o = o + e*wet
    return o
m = reverb(compress(mix)); rms = float(np.sqrt(np.mean(m**2)))
m = np.clip(m * 10**((-16 - 20*math.log10(rms+1e-9))/20), -0.99, 0.99)
sf.write(os.path.join(out, "episode_3guys.wav"), m, SR)
print("WROTE episode_3guys.wav", round(len(m)/SR, 1), "sec")
