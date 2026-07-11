$ErrorActionPreference = 'Continue'
$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
$venv = "$env:USERPROFILE\csm_venv"
Remove-Item $venv -Recurse -Force -ErrorAction SilentlyContinue
& $py -m venv $venv
$vpy = "$venv\Scripts\python.exe"
& $vpy -m pip install -q --upgrade pip 2>&1 | Select-Object -Last 1
Write-Output '=== CUDA torch ==='
& $vpy -m pip install -q "torch==2.6.0" "torchaudio==2.6.0" --index-url https://download.pytorch.org/whl/cu124 2>&1 | Select-Object -Last 4
Write-Output '=== transformers + deps ==='
& $vpy -m pip install -q "transformers>=4.53" accelerate soundfile huggingface_hub 2>&1 | Select-Object -Last 6
Write-Output '=== verify ==='
& $vpy -c "import torch; print('cuda', torch.cuda.is_available())" 2>&1
& $vpy -c "import transformers; from transformers import CsmForConditionalGeneration; print('transformers', transformers.__version__, 'csm_OK')" 2>&1
