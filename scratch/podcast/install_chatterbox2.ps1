$ErrorActionPreference = 'Continue'
$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
$venv = "$env:USERPROFILE\cbx_venv"
Write-Output '=== recreate clean isolated venv ==='
Remove-Item $venv -Recurse -Force -ErrorAction SilentlyContinue
& $py -m venv $venv
$vpy = "$venv\Scripts\python.exe"
& $vpy -m pip install -q --upgrade pip 2>&1 | Select-Object -Last 1
Write-Output '=== install chatterbox-tts (clean deps) ==='
& $vpy -m pip install -q chatterbox-tts 2>&1 | Select-Object -Last 10
Write-Output '=== verify torch/cuda/import ==='
& $vpy -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())" 2>&1
& $vpy -c "from chatterbox.tts import ChatterboxTTS; print('chatterbox_import_ok')" 2>&1
