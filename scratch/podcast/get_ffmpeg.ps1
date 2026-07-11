$ErrorActionPreference = 'Continue'
$dst = "$env:USERPROFILE\ffmpeg"; New-Item -ItemType Directory -Force $dst | Out-Null
$zip = "$dst\ff.zip"
if (-not (Get-ChildItem $dst -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue)) {
  Write-Output "downloading ffmpeg..."
  try { Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip -UseBasicParsing }
  catch { Write-Output ("dl1_err " + $_.Exception.Message); Invoke-WebRequest -Uri "https://github.com/GyanD/codexffmpeg/releases/latest/download/ffmpeg-release-essentials.zip" -OutFile $zip -UseBasicParsing }
  Expand-Archive -Path $zip -DestinationPath $dst -Force
}
$exe = (Get-ChildItem $dst -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
Write-Output ("FFMPEG_EXE: " + $exe)
& $exe -version 2>&1 | Select-Object -First 1
