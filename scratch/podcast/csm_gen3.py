import os, math, numpy as np, torch, soundfile as sf
from transformers import CsmForConditionalGeneration, AutoProcessor
try:
    from scipy.signal import butter, filtfilt
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False
mid = "sesame/csm-1b"
proc = AutoProcessor.from_pretrained(mid)
model = CsmForConditionalGeneration.from_pretrained(mid, device_map="cuda", torch_dtype=torch.float32)
SR = 24000
refs = os.path.expanduser(r"~\podcast_refs")
out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\csm_test3"); os.makedirs(out, exist_ok=True)
def load(fn): w, _ = sf.read(os.path.join(refs, fn)); return w.astype(np.float32)
MAN = "Hey, welcome back. I'm the one who always brings the skeptical take, so fair warning on that."
WOMAN = "And I'm the optimist of the two of us. I get a little too excited about basically everything."
seed = [
 {"role": "0", "content": [{"type": "text", "text": MAN}, {"type": "audio", "audio": load("ref_man.wav")}]},
 {"role": "1", "content": [{"type": "text", "text": WOMAN}, {"type": "audio", "audio": load("ref_woman.wav")}]},
]
dialogue = [
 (1, "Okay, so I saw this morning that a company says they basically brought back the dire wolf. Like the Game of Thrones animal. That's a real thing now?"),
 (0, "Sort of. That's the part everyone's fighting about. They took a gray wolf, edited a bunch of genes to match dire wolf DNA, and got these big white pups. So it's, dire-wolf-ish."),
 (1, "Dire-wolf-ish. Haha."),
 (0, "Right? It's not a clone. It's more like a gray wolf cosplaying as a dire wolf."),
 (1, "Okay but honestly, I'm into it. Who doesn't want giant fluffy ice age wolves running around?"),
 (0, "See, this is where I get nervous. We can't even keep regular wolves from getting shot, and now we're making designer ones?"),
 (1, "Oh come on, buzzkill."),
 (0, "It's not a buzzkill, it's ecology. You can't just drop a brand new predator into an ecosystem and hope it works out."),
 (1, "Fair. Okay, fair. But the same tech could bring back things that actually mattered for the environment, right?"),
 (0, "Now that, I'd sign up for. Mammoths, supposedly, could help the tundra. That's the real pitch behind all this."),
 (1, "Wait, mammoths help the tundra? How?"),
 (0, "They stomp down the snow and grass, which keeps the ground frozen, which keeps carbon locked up. Genuinely."),
 (1, "Okay, that's actually really cool. I take back the buzzkill thing. Partly."),
 (0, "Partly. I'll take partly."),
 (1, "Haha. Anyway. Fake dire wolves today, climate-saving mammoths tomorrow. What a timeline."),
]
WINDOW = 3
recent, segs, short = [], [], []
for i, (spk, text) in enumerate(dialogue):
    conv = seed + recent[-WINDOW:] + [{"role": str(spk), "content": [{"type": "text", "text": text}]}]
    inputs = proc.apply_chat_template(conv, tokenize=True, return_dict=True).to(model.device)
    oa = model.generate(**inputs, output_audio=True, max_new_tokens=375, do_sample=True, temperature=0.9, top_k=50)
    wav = oa[0].detach().to(torch.float32).cpu().numpy()
    segs.append(wav); short.append(len(text.split()) <= 4)
    recent.append({"role": str(spk), "content": [{"type": "text", "text": text}, {"type": "audio", "audio": wav}]})
    print("turn", i + 1, "done", round(len(wav) / SR, 1), "s")

# ---- overlap-aware placement (short reactions overlap the prior tail) ----
starts = [0]
for i in range(1, len(segs)):
    prev_end = starts[i-1] + len(segs[i-1])
    lead = int((0.18 if short[i] else -0.10) * SR)   # reactions start early; else small gap
    starts.append(max(0, prev_end - lead))
total = max(s + len(w) for s, w in zip(starts, segs))
mix = np.zeros(total, dtype=np.float32)
for s, w in zip(starts, segs): mix[s:s+len(w)] += w

# ---- mastering chain: HPF -> compress -> shared room reverb -> normalize ----
def highpass(x, fc=85):
    if not HAVE_SCIPY: return x
    b, a = butter(2, fc/(SR/2), btype='high'); return filtfilt(b, a, x).astype(np.float32)
def compress(x, thr=0.12, ratio=3.0):
    a = np.abs(x) + 1e-9
    g = np.where(a > thr, (thr + (a - thr)/ratio)/a, 1.0)
    k = max(1, int(0.006*SR)); g = np.convolve(g, np.ones(k)/k, 'same')
    return (x * g).astype(np.float32)
def reverb(x, wet=0.08):
    out = x.copy()
    for ms, dec in [(23, 0.6), (37, 0.45), (53, 0.35), (71, 0.25)]:
        d = int(ms/1000*SR); e = np.zeros_like(x); e[d:] = x[:-d]*dec; out = out + e*wet
    return out
m = reverb(compress(highpass(mix)))
rms = float(np.sqrt(np.mean(m**2)))
m = np.clip(m * 10**((-16 - 20*math.log10(rms+1e-9))/20), -0.99, 0.99)
sf.write(os.path.join(out, "episode_csm3.wav"), m, SR)
print("WROTE episode_csm3.wav", round(len(m)/SR, 1), "sec scipy=", HAVE_SCIPY)
