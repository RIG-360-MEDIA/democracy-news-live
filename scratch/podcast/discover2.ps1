cd $env:USERPROFILE\neuralnoise_source\neuralnoise-main
Write-Output '===ENTRYPOINTS==='
Get-Content pyproject.toml | Select-String -Pattern 'scripts|project.scripts|=\s*"neuralnoise'
Write-Output '===README_USAGE==='
Get-Content README.md | Select-String -Pattern 'neuralnoise |--config|--name|python -m|uv run|generate|\.json|http' | Select-Object -First 22
Write-Output '===LLM_WIRING==='
Get-ChildItem src\neuralnoise -Recurse -Filter *.py | Select-String -Pattern 'base_url|OPENAI_BASE_URL|GROQ|config_list|os\.environ|llm_config|api_key|ollama|11434|MODEL|gpt-' | Select-Object -First 30
Write-Output '===TTS_KOKORO==='
Get-Content src\neuralnoise\tts.py | Select-String -Pattern 'kokoro|class |def |sample_rate|\.wav|\.mp3|export|provider|KPipeline|soundfile|sf\.|lang' | Select-Object -First 35
Write-Output '===CLI==='
Get-Content src\neuralnoise\cli.py | Select-Object -First 40
