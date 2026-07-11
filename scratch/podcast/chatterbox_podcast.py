import os, math, numpy as np, soundfile as sf
from chatterbox.tts import ChatterboxTTS

refs = os.path.expanduser(r"~\podcast_refs")
out = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main\output\podcast_v2"); os.makedirs(out, exist_ok=True)
Z = os.path.join(refs, "ref_zach.wav"); E = os.path.join(refs, "ref_emily.wav")
SR = 24000

# ---- conversational script (fillers, reactions, interruptions, varied length) ----
script = [
 (E, "Okay, real question to start. What is the single most useless thing in your house that you would, like, genuinely fight someone to protect?"),
 (Z, "Oh, easy. Bubble wrap. No hesitation."),
 (E, "Haha, I knew it. I knew you were gonna say bubble wrap."),
 (Z, "I mean, come on. It's free stress relief that shows up in the mail. But here's the thing nobody knows. It was never supposed to be packaging at all."),
 (E, "Wait, really? Then what was it?"),
 (Z, "Wallpaper."),
 (E, "Dot dot dot. Wallpaper."),
 (Z, "Yeah! Nineteen fifty-seven, two engineers seal a couple of shower curtains together, trap the air bubbles inside, and they think, this is the future of home decor."),
 (E, "Okay, that is so much worse and better than I expected. So I'm guessing the textured wallpaper thing did not exactly take off."),
 (Z, "Flopped. Hard. So then they try to sell it as greenhouse insulation. Also flops."),
 (E, "Two flops. At what point do you just give up on the bubbles?"),
 (Z, "Right? But then, nineteen sixty, a marketer realizes I-B-M could wrap their shiny new computers in it for shipping. And boom. Failed wallpaper becomes a packaging empire."),
 (E, "From wallpaper nobody wanted, to a billion dollar industry. And, okay, I have to ask. Is the popping thing actually good for you, or did I make that up?"),
 (Z, "No, it's real. There's actual research saying popping it relieves stress. Which is exactly why people lost their minds when they invented a version that doesn't pop."),
 (E, "They made un-poppable bubble wrap? That's a war crime."),
 (Z, "Haha. Ships flat, you inflate it on site, saves space. Practical. Soulless. Anyway. That's bubble wrap."),
 (E, "Go pop something. See you next time!"),
]

print("loading chatterbox...")
model = ChatterboxTTS.from_pretrained(device="cuda")

def trim(x, thr=0.008):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0: return x
    return x[max(0, idx[0]-int(0.02*SR)):min(len(x), idx[-1]+int(0.04*SR))]

segs = []
for i, (ref, text) in enumerate(script):
    wav = model.generate(text, audio_prompt_path=ref, exaggeration=0.6, cfg_weight=0.3)
    x = trim(wav.squeeze(0).detach().cpu().numpy().astype(np.float32))
    segs.append(x)
    # varied gap: short reactions tight, longer lines get a beat
    gap = 0.12 if len(text.split()) <= 5 else (0.34 if text.endswith(('.', '!')) else 0.22)
    segs.append(np.zeros(int(gap*SR), dtype=np.float32))
    print("line", i+1, "done")
talk = np.concatenate(segs)

# ---- procedural music: warm intro/outro jingle + soft bed ----
def adsr(n, a=0.02, r=0.3):
    env = np.ones(n); ai = int(a*SR); ri = int(r*SR)
    env[:ai] = np.linspace(0, 1, ai)
    env[-ri:] = np.linspace(1, 0, ri)**1.5
    return env
def tone(freq, dur, amp=0.2, wave='sine'):
    n = int(dur*SR); t = np.arange(n)/SR
    if wave == 'tri':
        s = 2*np.abs(2*((t*freq) % 1)-1)-1
    else:
        s = np.sin(2*np.pi*freq*t)
    return (s*amp*adsr(n)).astype(np.float32)
def chord(freqs, dur, amp=0.12):
    n = int(dur*SR); mix = np.zeros(n, dtype=np.float32)
    for f in freqs: mix[:len(tone(f, dur, amp))] += tone(f, dur, amp)
    return mix
# C major feel: C E G / G B D / A C E / F A C
prog = [[261.6,329.6,392.0],[392.0,493.9,587.3],[220.0,261.6,329.6],[174.6,220.0,261.6]]
mel = [523.3,659.3,587.3,440.0]  # simple top line
def jingle():
    parts = []
    for ch, m in zip(prog, mel):
        bar = chord(ch, 0.85, 0.10)
        top = tone(m, 0.85, 0.10, 'tri')
        bar[:len(top)] += top
        parts.append(bar)
    return np.concatenate(parts)
intro = jingle(); outro = jingle()
# soft sustained bed (very quiet) for the talk
bedn = len(talk); tb = np.arange(bedn)/SR
bed = (0.5*np.sin(2*np.pi*130.8*tb) + 0.5*np.sin(2*np.pi*196.0*tb)).astype(np.float32)
bed *= 0.035 * (0.85 + 0.15*np.sin(2*np.pi*0.05*tb))  # slow swell, ~-29 dB

# ---- mix: intro -> talk(+bed) -> outro, with fades ----
def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    if fin: x[:int(fin*SR)] *= np.linspace(0, 1, int(fin*SR))
    if fout: x[-int(fout*SR):] *= np.linspace(1, 0, int(fout*SR))
    return x
talk_mixed = talk + bed[:len(talk)]
gap1 = np.zeros(int(0.25*SR), dtype=np.float32)
final = np.concatenate([fade(intro, 0.05, 0.6), gap1, fade(talk_mixed, 0.2, 0.2), gap1, fade(outro, 0.6, 0.1)])
# master to -16 dBFS
rms = float(np.sqrt(np.mean(final**2)))
final = np.clip(final * 10**((-16 - 20*math.log10(rms+1e-9))/20), -0.99, 0.99)
path = os.path.join(out, "episode_v2.wav")
sf.write(path, final, SR)
print("WROTE", path, round(len(final)/SR, 1), "sec")
