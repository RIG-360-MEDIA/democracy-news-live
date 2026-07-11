Write-Output '=== GPU ==='
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
Write-Output '=== PYTHON PROCS (CPU secs) ==='
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, CPU, StartTime
Write-Output '=== nntest2 FILES ==='
Get-ChildItem "$env:USERPROFILE\neuralnoise_source\neuralnoise-main\output\nntest2" -Recurse -ErrorAction SilentlyContinue | Select-Object Name, Length, LastWriteTime
Write-Output '=== ollama running model ==='
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" ps
