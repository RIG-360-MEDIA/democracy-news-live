$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
Write-Output '===PYTHON_PROCS==='
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, CPU, StartTime
Write-Output '===AG2_VERSION==='
& $py -c "import importlib.metadata as m;
for p in ['ag2','autogen','pyautogen','openai','kokoro']:
    try: print(p, m.version(p))
    except Exception as e: print(p,'-',e)" 2>&1
Write-Output '===CONTEXT_VARIABLES_USAGE==='
Get-ChildItem $env:USERPROFILE\neuralnoise_source\neuralnoise-main\src\neuralnoise -Recurse -Filter *.py | Select-String -Pattern 'context_variables|ContextVariables|def save_content_analysis|def save_podcast_script|register_for' | Select-Object -First 25
