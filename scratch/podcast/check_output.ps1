$dir = "$env:USERPROFILE\neuralnoise_source\neuralnoise-main\output\nntest1"
Write-Output '===FILES==='
Get-ChildItem $dir -Recurse -ErrorAction SilentlyContinue | Select-Object FullName, Length
Write-Output '===SCRIPT_PEEK==='
$scripts = Get-ChildItem $dir -Recurse -Include *.json -ErrorAction SilentlyContinue
foreach ($s in $scripts) { Write-Output ('--- ' + $s.Name + ' (' + $s.Length + ' bytes) ---'); Get-Content $s.FullName -TotalCount 40 }
Write-Output '===AUDIO==='
Get-ChildItem $dir -Recurse -Include *.wav,*.mp3,*.m4a -ErrorAction SilentlyContinue | Select-Object FullName, Length
