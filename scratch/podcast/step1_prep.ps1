$ErrorActionPreference = 'Continue'
$ol = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (-not (Get-Process ollama -ErrorAction SilentlyContinue)) {
  Start-Process -FilePath $ol -ArgumentList 'serve' -WindowStyle Hidden
  Start-Sleep -Seconds 6
}
Write-Output '===OLLAMA_PROC==='
Get-Process ollama -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Name
Write-Output '===QWEN_TEST==='
$body = @{ model='qwen2.5:32b'; messages=@(@{role='user';content='Reply with one word: OK'}); max_tokens=5 } | ConvertTo-Json -Depth 6
try {
  $r = Invoke-RestMethod -Uri 'http://localhost:11434/v1/chat/completions' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 180
  Write-Output ('QWEN_REPLY: ' + $r.choices[0].message.content)
} catch { Write-Output ('QWEN_ERR: ' + $_.Exception.Message) }
Write-Output '===NN_CLI==='
$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
$nn = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\Scripts\nn.exe"
if (Test-Path $nn) { Write-Output "nn_exe: $nn" } else { Write-Output 'nn_exe: NOT FOUND' }
& $py -c "import neuralnoise, kokoro; print('imports_ok')" 2>&1
Write-Output '===FFMPEG==='
(Get-Command ffmpeg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source) ; if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Write-Output 'ffmpeg: MISSING' }
