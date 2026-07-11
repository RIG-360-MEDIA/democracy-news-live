import os, numpy as np, soundfile as sf
def f0_stats(path):
    y, sr = sf.read(path)
    if y.ndim > 1: y = y.mean(1)
    y = y.astype(np.float64)
    fr, hop = int(0.04*sr), int(0.02*sr)
    f0s = []
    for i in range(0, len(y)-fr, hop):
        s = y[i:i+fr]
        if np.sqrt(np.mean(s**2)) < 0.015: continue   # skip silence/unvoiced
        s = s - s.mean()
        ac = np.correlate(s, s, 'full')[len(s)-1:]
        lo, hi = int(sr/350), int(sr/75)
        if hi >= len(ac): continue
        peak = lo + int(np.argmax(ac[lo:hi]))
        if ac[peak] > 0.3*ac[0]:
            f0s.append(sr/peak)
    f0s = np.array(f0s)
    if len(f0s) < 5: return "no voiced frames"
    semitone_std = float(np.std(12*np.log2(f0s/np.median(f0s))))
    return dict(median_hz=round(float(np.median(f0s))), pitch_semitone_std=round(semitone_std, 2), voiced_frames=len(f0s))
base = os.path.expanduser(r"~\neuralnoise_source\neuralnoise-main")
for name, p in [("chatterbox_episode", os.path.join(base, r"output\chatterbox_test\episode_chatterbox.wav")),
                ("kokoro_episode",     os.path.join(base, r"output\kokoro_test\episode.wav")),
                ("ref_zach(kokoro src)", os.path.expanduser(r"~\podcast_refs\ref_zach.wav")),
                ("ref_emily(kokoro src)", os.path.expanduser(r"~\podcast_refs\ref_emily.wav"))]:
    print(name, "->", f0_stats(p))
print("(natural expressive speech ~ 2.5-4+ semitone std; monotone/mechanical ~ <1.5)")
