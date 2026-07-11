import os, collections
from huggingface_hub import list_repo_files, hf_hub_download
repo = "sdialog/voices-libritts"
files = list_repo_files(repo, repo_type="dataset")
print("total_files", len(files))
print("exts", dict(collections.Counter(os.path.splitext(f)[1] for f in files)))
meta = [f for f in files if f.lower().endswith((".csv", ".tsv", ".json", ".parquet")) or "meta" in f.lower() or "speaker" in f.lower()]
print("meta_files", meta[:12])
print("sample_audio", [f for f in files if f.lower().endswith((".wav", ".flac", ".mp3"))][:10])
# try to grab a metadata file and peek
for m in meta:
    try:
        p = hf_hub_download(repo, m, repo_type="dataset")
        head = open(p, encoding="utf-8", errors="ignore").read()[:500]
        print("=== META", m, "===\n", head)
        break
    except Exception as e:
        print("meta_dl_err", m, str(e)[:60])
