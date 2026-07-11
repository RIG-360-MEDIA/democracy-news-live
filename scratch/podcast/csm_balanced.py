import os, math, numpy as np, torch, soundfile as sf
from transformers import CsmForConditionalGeneration, AutoProcessor, pipeline
SR = 24000
refs = os.path.expanduser(r"~\podcast_refs")
out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\csm_bal"); os.makedirs(out, exist_ok=True)
def load(fn): w, _ = sf.read(os.path.join(refs, fn)); return w.astype(np.float32)
deep, light = load("ref_deep.wav"), load("ref_light.wav")
print("transcribing seeds...")
asr = pipeline("automatic-speech-recognition", model="openai/whisper-base.en", device="cuda")
def tx(y): return asr({"array": y, "sampling_rate": SR})["text"].strip()
td, tl = tx(deep), tx(light); del asr; torch.cuda.empty_cache()
mid = "sesame/csm-1b"
proc = AutoProcessor.from_pretrained(mid)
model = CsmForConditionalGeneration.from_pretrained(mid, device_map="cuda", torch_dtype=torch.float32)
seed = [
 {"role": "0", "content": [{"type": "text", "text": td}, {"type": "audio", "audio": deep}]},   # deep / calm
 {"role": "1", "content": [{"type": "text", "text": tl}, {"type": "audio", "audio": light}]},   # light / punchy
]
dialogue = [
 (1, "Okay okay okay, did you see this? They brought back the dire wolf. The actual dire wolf!"),
 (0, "The Game of Thrones one. Yeah, I saw it. I'm not totally sold, though."),
 (1, "Not sold? Dude, it's a real animal, walking around, right now!"),
 (0, "Sort of. They took a gray wolf and edited the genes to look like a dire wolf. So it's more, dire-wolf-ish."),
 (1, "Dire-wolf-ish. Hah. Okay, that's a little underwhelming, I'll give you that."),
 (0, "Right. It's basically a gray wolf in a really good costume."),
 (1, "Still cool though! Giant white wolves? Come on, that's awesome."),
 (0, "It is cool. My worry is, we can barely keep regular wolves alive. People shoot them. And now we're making new ones?"),
 (1, "Okay, buzzkill. But wait, didn't they say they wanna do mammoths next?"),
 (0, "They do. And weirdly, that one might actually matter. For the climate."),
 (1, "Hold on. A mammoth fights climate change? How?"),
 (0, "They trample the snow, the ground stays frozen, the carbon stays locked underground. It's a real theory."),
 (1, "Dude. Woolly mammoths versus global warming. That's the coolest sentence I've ever heard."),
 (0, "Heh. That one I'm actually on board with."),
 (1, "See! Mammoths good, fake wolves suspicious. We agree."),
 (0, "Partly."),
]
WINDOW = 4
recent, segs, short = [], [], []
for i, (spk, text) in enumerate(dialogue):
    conv = seed + recent[-WINDOW:] + [{"role": str(spk), "content": [{"type": "text", "text": text}]}]
    inputs = proc.apply_chat_template(conv, tokenize=True, return_dict=True).to(model.device)
    oa = model.generate(**inputs, output_audio=True, max_new_tokens=375, do_sample=True, temperature=0.9, top_k=50)
    wav = oa[0].detach().to(torch.float32).cpu().numpy()
    segs.append(wav); short.append(len(text.split()) <= 6)
    recent.append({"role": str(spk), "content": [{"type": "text", "text": text}, {"type": "audio", "audio": wav}]})
    print("turn", i+1, "spk", spk, round(len(wav)/SR, 1), "s")
starts = [0]
for i in range(1, len(segs)):
    pe = starts[i-1] + len(segs[i-1]); lead = int((0.22 if short[i] else -0.07)*SR)
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
sf.write(os.path.join(out, "episode_2host_v2.wav"), mm, SR)
print("WROTE episode_2host_v2.wav", round(len(mm)/SR, 1), "sec")
