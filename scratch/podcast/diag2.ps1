$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
Write-Output '===KILL_LOOPING_RUN==='
# kill the most-recently-started python (the looping nn run), keep older ones
$proc = Get-Process python -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1
if ($proc) { Stop-Process -Id $proc.Id -Force; Write-Output ("killed PID " + $proc.Id) } else { Write-Output 'no python proc' }
Write-Output '===VERSIONS==='
& $py -c "import importlib.metadata as m; print('ag2', m.version('ag2'))" 2>&1
& $py -c "import importlib.metadata as m; print('autogen', m.version('autogen'))" 2>&1
& $py -c "import importlib.metadata as m; print('pyautogen', m.version('pyautogen'))" 2>&1
Write-Output '===CTXVAR_USAGE==='
Get-ChildItem $env:USERPROFILE\neuralnoise_source\neuralnoise-main\src\neuralnoise -Recurse -Filter *.py | Select-String -Pattern 'context_variables|ContextVariables|def save_content_analysis|def save_podcast_script' | Select-Object -First 20
