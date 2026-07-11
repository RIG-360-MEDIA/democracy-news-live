$ErrorActionPreference = 'Continue'
$env:OLLAMA_MODEL = 'qwen2.5:32b'
$env:OLLAMA_BASE_URL = 'http://localhost:11434/v1'
$env:OPENAI_API_KEY = 'ollama'
cd $env:USERPROFILE\neuralnoise_source\neuralnoise-main
$dir = 'output\nntest1'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$content = @'
The Surprising History of Bubble Wrap

Bubble wrap was invented in 1957 by two engineers, Alfred Fielding and Marc Chavannes. They were not trying to make packaging at all. They were trying to create a trendy, textured wallpaper by sealing two plastic shower curtains together, trapping air bubbles inside. The wallpaper flopped. They then pitched the same material as greenhouse insulation, and that failed too.

The real breakthrough came in 1960, when a marketer named Frederick Bowers realised that IBM could use the bubbles to protect its new 1401 computer during shipping. That single idea turned a failed wallpaper into a packaging empire, and the Sealed Air Corporation was born.

There is also a psychological twist. Several studies suggest that popping bubble wrap genuinely relieves stress, which may explain why the material became a pop-culture icon as much as a shipping product.

In 2015, Sealed Air introduced a new version called iBubble Wrap that does not pop on its own. It ships flat and is inflated on site to save space, to the dismay of bubble-popping fans everywhere.
'@
Set-Content -Encoding UTF8 -Path "$dir\content.md" -Value $content
$nn = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\Scripts\nn.exe"
Write-Output "=== START nn generate (qwen2.5:32b + kokoro) ==="
& $nn generate --name nntest1 --config config\config_groq_kokoro.json 2>&1
Write-Output "=== nn EXIT CODE: $LASTEXITCODE ==="
Write-Output "=== OUTPUT FILES ==="
Get-ChildItem $dir -Recurse | Select-Object Name, Length
