$ErrorActionPreference = 'Continue'
$venv = "$env:USERPROFILE\cbx_venv"; $vpy = "$venv\Scripts\python.exe"
Write-Output '=== installing CUDA torch 2.6.0 (cu124) into cbx_venv ==='
& $vpy -m pip install -q "torch==2.6.0" "torchaudio==2.6.0" "torchvision==0.21.0" --index-url https://download.pytorch.org/whl/cu124 2>&1 | Select-Object -Last 8
Write-Output '=== verify ==='
& $vpy -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.version.cuda)" 2>&1
& $vpy -c "from chatterbox.tts import ChatterboxTTS; print('chatterbox_ok')" 2>&1
