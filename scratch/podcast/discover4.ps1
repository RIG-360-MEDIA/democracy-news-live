cd $env:USERPROFILE\neuralnoise_source\neuralnoise-main
Write-Output '===LLMGREP==='
Get-ChildItem src\neuralnoise -Recurse -Filter *.py | Select-String -Pattern 'llm_config|config_list|api_key|base_url|getenv|gpt-4|gpt-3|model=|"model"|LLMConfig|api_type|OAI_CONFIG|11434|ollama|groq|OPENAI_MODEL|NEURALNOISE'
Write-Output '===AGENTS_MGR_HEAD==='
Get-ChildItem src\neuralnoise -Recurse -Filter agents_manager.py | ForEach-Object { Get-Content $_.FullName | Select-Object -First 60 }
Write-Output '===KOKORO_FUNC==='
Get-Content src\neuralnoise\tts.py | Select-Object -Skip 115 -First 80
Write-Output '===ENV==='
Get-ChildItem -Force .env -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
Get-Content .env -ErrorAction SilentlyContinue | ForEach-Object { ($_ -split '=')[0] }
