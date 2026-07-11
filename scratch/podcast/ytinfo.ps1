$url = "https://www.youtube.com/shorts/zQYs5mT_vgI"
$yt = (Get-Command yt-dlp -ErrorAction SilentlyContinue).Source
Write-Output ("ytdlp_path: " + $yt)
Write-Output ("ffmpeg_path: " + (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source)
if (-not $yt) {
  Write-Output "--- searching yt-relay for yt-dlp ---"
  Get-ChildItem $env:USERPROFILE\yt-relay -Recurse -Include yt-dlp.exe,yt_dlp* -ErrorAction SilentlyContinue | Select-Object -First 5 -ExpandProperty FullName
  Write-Output ("pip yt-dlp? " + (Test-Path "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\Scripts\yt-dlp.exe"))
}
if ($yt) { & $yt --no-warnings --skip-download --print "TITLE: %(title)s`nUPLOADER: %(uploader)s`nDURATION: %(duration)ss" $url 2>&1 }
