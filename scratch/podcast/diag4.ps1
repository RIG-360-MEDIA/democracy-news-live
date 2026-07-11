cd $env:USERPROFILE\neuralnoise_source\neuralnoise-main
Write-Output '===WHERE_SAVE_DEFINED==='
Get-ChildItem src\neuralnoise -Recurse -Filter *.py | Select-String -Pattern 'def save_content_analysis|def save_podcast_script|save_content_analysis|save_podcast_script' | ForEach-Object { $_.Path.Replace($PWD.Path,'') + ':' + $_.LineNumber + ': ' + $_.Line.Trim() }
Write-Output '===CONTENT_ANALYZER_AGENT_FULL==='
Get-Content src\neuralnoise\studio\agents\content_analyzer_agent.py
