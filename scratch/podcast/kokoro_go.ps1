Get-Process python -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1 | ForEach-Object { Stop-Process -Id $_.Id -Force; Write-Output ('killed_nn_run ' + $_.Id) }
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
Write-Output '=== KOKORO TTS START ==='
& "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\sshuser\kokoro_test.py" 2>&1
Write-Output "=== EXIT $LASTEXITCODE ==="
