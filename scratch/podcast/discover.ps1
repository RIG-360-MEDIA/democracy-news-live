cd $env:USERPROFILE\neuralnoise_source\neuralnoise-main
Write-Output '===OLLAMA_MODELS==='
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" list
Write-Output '===PYPROJECT_DEPS==='
Get-Content pyproject.toml | Select-String -Pattern 'kokoro|openai|groq|litellm|eleven|ag2|autogen|anthropic|dependencies|requires-python|soundfile|pydub'
Write-Output '===README_LLM_HINTS==='
Get-Content README.md | Select-String -Pattern 'API_KEY|OPENAI|GROQ|OLLAMA|--model|provider|MODEL|base_url|export ' | Select-Object -First 20
Write-Output '===SRC_FILES==='
Get-ChildItem src\neuralnoise -Recurse -Filter *.py | Select-Object -ExpandProperty Name
Write-Output '===KOKORO_PRESENT==='
python -c "import importlib.util as u; print('kokoro:', u.find_spec('kokoro') is not None); print('neuralnoise:', u.find_spec('neuralnoise') is not None)"
Write-Output '===FFMPEG==='
(Get-Command ffmpeg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
