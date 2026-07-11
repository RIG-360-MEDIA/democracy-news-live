import os, torch, soundfile as sf
from transformers import CsmForConditionalGeneration, AutoProcessor
mid = "sesame/csm-1b"
print("loading processor/model (downloads ~first time)...")
proc = AutoProcessor.from_pretrained(mid)
model = CsmForConditionalGeneration.from_pretrained(mid, device_map="cuda", torch_dtype=torch.bfloat16)
print("model loaded")
conv = [{"role": "0", "content": [{"type": "text", "text":
    "Welcome back to the show. Today we're talking about bubble wrap, and honestly, it has a much weirder history than you'd think."}]}]
inputs = proc.apply_chat_template(conv, tokenize=True, return_dict=True).to(model.device)
out = model.generate(**inputs, output_audio=True)
print("gen_type", type(out).__name__, "len", (len(out) if hasattr(out, '__len__') else '?'))
a = out[0]
print("audio_type", type(a).__name__, "shape", getattr(a, 'shape', None),
      "sr", getattr(proc.feature_extractor, 'sampling_rate', '?'))
dst = os.path.expanduser(r"~\csm_smoke.wav")
try:
    proc.save_audio(out, dst); print("saved_via save_audio")
except Exception as e:
    print("save_audio_err", str(e)[:90])
    w = a.detach().to(torch.float32).cpu().numpy()
    sf.write(dst, w, getattr(proc.feature_extractor, 'sampling_rate', 24000)); print("saved_via soundfile")
print("DONE", dst)
