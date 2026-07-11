import os, math, numpy as np, torch, soundfile as sf
from transformers import CsmForConditionalGeneration, AutoProcessor
mid = "sesame/csm-1b"
proc = AutoProcessor.from_pretrained(mid)
model = CsmForConditionalGeneration.from_pretrained(mid, device_map="cuda", torch_dtype=torch.float32)
SR = 24000
out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\csm_test"); os.makedirs(out, exist_ok=True)

dialogue = [
 (1, "Okay, real question to start. What is the single most useless thing in your house that you would genuinely fight someone to protect?"),
 (0, "Oh, easy. Bubble wrap. No hesitation."),
 (1, "Haha, I knew it. I knew you were gonna say bubble wrap."),
 (0, "I mean, come on. It's free stress relief that shows up in the mail. But here's the thing nobody knows. It was never supposed to be packaging at all."),
 (1, "Wait, really? Then what was it?"),
 (0, "Wallpaper."),
 (1, "Wallpaper."),
 (0, "Yeah! Nineteen fifty-seven, two engineers seal a couple of shower curtains together, trap the air bubbles inside, and they think, this is the future of home decor."),
 (1, "Okay, that is so much worse and better than I expected. So I'm guessing the textured wallpaper thing did not take off."),
 (0, "Flopped. Hard. So then they try to sell it as greenhouse insulation. Also flops."),
 (1, "Two flops. At what point do you just give up on the bubbles?"),
 (0, "Right? But then a marketer realizes IBM could wrap their shiny new computers in it for shipping. And boom. Failed wallpaper becomes a packaging empire."),
 (1, "And, okay, I have to ask. Is the popping thing actually good for you, or did I make that up?"),
 (0, "No, it's real. There's research saying popping it relieves stress. Which is exactly why people lost their minds when they invented a version that doesn't pop."),
 (1, "They made un-poppable bubble wrap? That's a war crime."),
 (0, "Haha. Ships flat, you inflate it on site. Practical. Soulless. Anyway, that's bubble wrap."),
 (1, "Go pop something. See you next time!"),
]

WINDOW = 4
context, segs = [], []
for i, (spk, text) in enumerate(dialogue):
    cur = {"role": str(spk), "content": [{"type": "text", "text": text}]}
    oa = None
    for mode in ("ctx", "noctx"):
        conv = (context[-WINDOW:] + [cur]) if mode == "ctx" else [cur]
        try:
            inputs = proc.apply_chat_template(conv, tokenize=True, return_dict=True).to(model.device)
            oa = model.generate(**inputs, output_audio=True, max_new_tokens=375); used = mode; break
        except Exception as e:
            print(f"turn {i+1} mode={mode} failed: {str(e)[:90]}")
            if mode == "noctx": raise
    wav = oa[0].detach().to(torch.float32).cpu().numpy()
    segs.append(wav)
    context.append({"role": str(spk), "content": [{"type": "text", "text": text}, {"type": "audio", "audio": wav}]})
    print("turn", i + 1, "done", round(len(wav) / SR, 1), "s mode=", used)

gap = np.zeros(int(0.16 * SR), dtype=np.float32)
pieces = []
for w in segs: pieces += [w, gap]
full = np.concatenate(pieces)
rms = float(np.sqrt(np.mean(full ** 2)))
full = np.clip(full * 10 ** ((-16 - 20 * math.log10(rms + 1e-9)) / 20), -0.99, 0.99)
sf.write(os.path.join(out, "episode_csm.wav"), full, SR)
print("WROTE episode_csm.wav", round(len(full) / SR, 1), "sec")
