cd $env:USERPROFILE\neuralnoise_source\neuralnoise-main
Write-Output '===CLI_FULL==='
Get-Content src\neuralnoise\cli.py
Write-Output '===LLM_CONFIG_SEARCH==='
Get-ChildItem src\neuralnoise -Recurse -Filter *.py | Select-String -Pattern 'llm_config|config_list|OAI_CONFIG|base_url|gpt-4|gpt-3|model_name|OPENAI_MODEL|getenv|api_type|temperature|AssistantAgent'
Write-Output '===KOKORO_FUNC==='
Get-Content src\neuralnoise\tts.py | Select-Object -Skip 115 -First 80
