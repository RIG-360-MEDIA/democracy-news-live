from huggingface_hub import hf_hub_download
import csv
p = hf_hub_download("sdialog/voices-libritts", "metadata.csv", repo_type="dataset")
r = csv.reader(open(p, encoding="utf-8"))
hdr = next(r)
print("HEADER:", hdr)
for _ in range(3):
    try: print("ROW:", next(r))
    except StopIteration: break
