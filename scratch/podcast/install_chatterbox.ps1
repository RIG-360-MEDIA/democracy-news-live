$ErrorActionPreference = 'Continue'
Write-Output '=== RESOURCE CHECK ==='
(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$os = Get-CimInstance Win32_OperatingSystem; [math]::Round(100*$os.FreePhysicalMemory/$os.TotalVisibleMemorySize,1)
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
$venv = "$env:USERPROFILE\cbx_venv"
if (-not (Test-Path $venv)) { & $py -m venv --system-site-packages $venv; Write-Output 'venv created' } else { Write-Output 'venv exists' }
$vpy = "$venv\Scripts\python.exe"
Write-Output '=== installing chatterbox-tts (reusing system torch) ==='
& $vpy -m pip install -q chatterbox-tts 2>&1 | Select-Object -Last 12
Write-Output '=== verify ==='
& $vpy -c "import torch; print('cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')" 2>&1
& $vpy -c "from chatterbox.tts import ChatterboxTTS; print('chatterbox_import_ok')" 2>&1
& $vpy -c "import kokoro; print('kokoro_visible_ok')" 2>&1
