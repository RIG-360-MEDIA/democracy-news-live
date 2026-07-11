'PROC_COUNT: ' + ((Get-Process ollama -ErrorAction SilentlyContinue | Measure-Object).Count)
try { $t = Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -TimeoutSec 20; 'MODELS: ' + (($t.models | ForEach-Object { $_.name }) -join ', ') } catch { 'TAGS_ERR: ' + $_.Exception.Message }
'PY: ' + (Test-Path "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe")
'NN: ' + (Test-Path "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\Scripts\nn.exe")
