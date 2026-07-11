import os, math, numpy as np, torch, soundfile as sf
from transformers import CsmForConditionalGeneration, AutoProcessor, pipeline
SR = 24000
refs = os.path.expanduser(r"~\podcast_refs")
out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\csm_pers"); os.makedirs(out, exist_ok=True)
def load(fn): w, _ = sf.read(os.path.join(refs, fn)); return w.astype(np.float32)
quirky, smart = load("ref_deep.wav"), load("ref_light2.wav")   # 0=Gord deep/quirky, 1=Gary clear/smart
print("transcribing seeds...")
asr = pipeline("automatic-speech-recognition", model="openai/whisper-base.en", device="cuda")
def tx(y): return asr({"array": y, "sampling_rate": SR})["text"].strip()
tq, ts = tx(quirky), tx(smart); del asr; torch.cuda.empty_cache()
mid = "sesame/csm-1b"
proc = AutoProcessor.from_pretrained(mid)
model = CsmForConditionalGeneration.from_pretrained(mid, device_map="cuda", torch_dtype=torch.float32)
seed = [
 {"role": "0", "content": [{"type": "text", "text": tq}, {"type": "audio", "audio": quirky}]},   # deep, quirky
 {"role": "1", "content": [{"type": "text", "text": ts}, {"type": "audio", "audio": smart}]},    # clear, smart/curious/fast
]
dialogue = [
 (1, "Okay, I just fell down a rabbit hole. A company says they actually resurrected the dire wolf. Brought it back from extinction. Is that even real?"),
 (0, "Oh, it's real. Sort of. They made a chunky gray wolf and called it a dire wolf. Honestly? Respect the audacity."),
 (1, "Wait, so it's not a true clone. They gene-edited a gray wolf to match dire wolf DNA. How close is it actually, genetically?"),
 (0, "Close-ish. It's like ordering a wolf off a knockoff website. Looks the part, probably voids the warranty."),
 (1, "Ha. Okay but that raises a real question. If you can edit a species to look extinct, where's the line? What even counts as bringing it back?"),
 (0, "See, I don't think about lines. I think about, can I have one as a pet, and will it eat my mailman."),
 (1, "Okay but seriously, the part that fascinates me is the mammoth project. They say mammoths could fight climate change. What's the actual mechanism?"),
 (0, "Big stompy elephants pack down the snow. Ground stays frozen. Carbon stays trapped. Nature's lawn rollers."),
 (1, "Right, the permafrost stays cold so it doesn't release methane. That actually tracks. So the wolf is a publicity stunt, but the mammoth could be genuinely useful?"),
 (0, "Exactly. One's a costume party. The other's a climate intern with tusks."),
 (1, "A climate intern with tusks. I'm stealing that. Okay, I'm sold on mammoths, suspicious of wolves."),
 (0, "Wise. Trust the tusks, not the fur."),
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
sf.write(os.path.join(out, "episode_personas.wav"), mm, SR)
print("WROTE episode_personas.wav", round(len(mm)/SR, 1), "sec")
