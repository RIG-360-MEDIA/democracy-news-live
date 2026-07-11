import os
print("HF_TOKEN_env:", bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")))
try:
    from huggingface_hub import whoami
    print("hf_whoami:", whoami().get("name"))
except Exception as e:
    print("hf_whoami_err:", str(e)[:90])
for repo in ["sesame/csm-1b", "meta-llama/Llama-3.2-1B"]:
    try:
        from huggingface_hub import model_info
        mi = model_info(repo)
        print(f"{repo}: accessible gated={getattr(mi,'gated',None)} files={len(mi.siblings)}")
    except Exception as e:
        print(f"{repo}: ERR {str(e)[:120]}")
try:
    import transformers
    from transformers import CsmForConditionalGeneration  # noqa
    print("transformers", transformers.__version__, "csm_supported: YES")
except Exception as e:
    import transformers
    print("transformers", getattr(transformers, "__version__", "?"), "csm_supported: NO ->", str(e)[:60])
