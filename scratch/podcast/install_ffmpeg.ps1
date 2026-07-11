$dst = "$env:USERPROFILE\ffmpeg"
$ff = Get-ChildItem $dst -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
if (-not $ff) {
  $zip = "$env:TEMP\ffmpeg.zip"
  Write-Output "downloading ffmpeg static build..."
  Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip -UseBasicParsing
  Expand-Archive -Path $zip -DestinationPath $dst -Force
  $ff = Get-ChildItem $dst -Recurse -Filter ffmpeg.exe | Select-Object -First 1 -ExpandProperty FullName
}
Write-Output ("FFMPEG: " + $ff)
& $ff -version 2>&1 | Select-Object -First 1
