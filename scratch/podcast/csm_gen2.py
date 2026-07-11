import os, math, numpy as np, torch, soundfile as sf
from transformers import CsmForConditionalGeneration, AutoProcessor
mid = "sesame/csm-1b"
proc = AutoProcessor.from_pretrained(mid)
model = CsmForConditionalGeneration.from_pretrained(mid, device_map="cuda", torch_dtype=torch.float32)
SR = 24000
refs = os.path.expanduser(r"~\podcast_refs")
out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\csm_test2"); os.makedirs(out, exist_ok=True)

def load(fn):
    w, _ = sf.read(os.path.join(refs, fn)); return w.astype(np.float32)
MAN_TEXT = "Hey, welcome back. I'm the one who always brings the skeptical take, so fair warning on that."
WOMAN_TEXT = "And I'm the optimist of the two of us. I get a little too excited about basically everything."
# persistent voice anchors: speaker 0 = man, speaker 1 = woman
seed = [
 {"role": "0", "content": [{"type": "text", "text": MAN_TEXT}, {"type": "audio", "audio": load("ref_man.wav")}]},
 {"role": "1", "content": [{"type": "text", "text": WOMAN_TEXT}, {"type": "audio", "audio": load("ref_woman.wav")}]},
]

# balanced, opinionated conversation (both contribute facts + takes, disagree, react)
dialogue = [
 (1, "Okay, so I saw this morning that a company says they basically brought back the dire wolf. Like the Game of Thrones animal. That's a real thing now?"),
 (0, "Sort of. That's the part everyone's fighting about. They took a gray wolf, edited a bunch of genes to match dire wolf DNA, and got these big white pups. So it's, dire-wolf-ish."),
 (1, "Dire-wolf-ish. Haha, that's the most underwhelming way to bring back an extinct animal."),
 (0, "Right? It's not a clone. It's more like a gray wolf cosplaying as a dire wolf."),
 (1, "Okay but honestly, I'm into it. Who doesn't want giant fluffy ice age wolves running around?"),
 (0, "See, this is where I get nervous. We can't even keep regular wolves from getting shot, and now we're making designer ones?"),
 (1, "Oh come on, that's such a buzzkill take."),
 (0, "It's not a buzzkill, it's ecology. You can't just drop a brand new predator into an ecosystem and hope it works out."),
 (1, "Fair. Okay, fair. But the same tech could bring back things that actually mattered for the environment, right?"),
 (0, "Now that, I'd sign up for. Mammoths, supposedly, could help the tundra. That's the real pitch behind all of this."),
 (1, "Wait, mammoths help the tundra? How does a giant hairy elephant help anything except being awesome?"),
 (0, "They stomp down the snow and grass, which keeps the ground frozen, which keeps carbon locked up. Genuinely."),
 (1, "Okay, that's actually really cool. I take back the buzzkill thing. Partly."),
 (0, "Partly. I'll take partly."),
 (1, "Haha. Anyway. Fake dire wolves today, climate-saving mammoths tomorrow. What a timeline."),
]

WINDOW = 3
recent, segs = [], []
for i, (spk, text) in enumerate(dialogue):
    conv = seed + recent[-WINDOW:] + [{"role": str(spk), "content": [{"type": "text", "text": text}]}]
    inputs = proc.apply_chat_template(conv, tokenize=True, return_dict=True).to(model.device)
    oa = model.generate(**inputs, output_audio=True, max_new_tokens=375)
    wav = oa[0].detach().to(torch.float32).cpu().numpy()
    segs.append(wav)
    recent.append({"role": str(spk), "content": [{"type": "text", "text": text}, {"type": "audio", "audio": wav}]})
    print("turn", i + 1, "done", round(len(wav) / SR, 1), "s")

gap = np.zeros(int(0.14 * SR), dtype=np.float32)
pieces = []
for w in segs: pieces += [w, gap]
full = np.concatenate(pieces)
rms = float(np.sqrt(np.mean(full ** 2)))
full = np.clip(full * 10 ** ((-16 - 20 * math.log10(rms + 1e-9)) / 20), -0.99, 0.99)
sf.write(os.path.join(out, "episode_csm2.wav"), full, SR)
print("WROTE episode_csm2.wav", round(len(full) / SR, 1), "sec")
