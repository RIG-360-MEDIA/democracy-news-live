$ErrorActionPreference = 'Continue'
$ff = "C:\Users\sshuser\ffmpeg\ffmpeg-8.1.1-essentials_build\bin"
$ytdlp = "C:\Users\sshuser\AppData\Local\Programs\Python\Python311\Scripts\yt-dlp.exe"
$urls = @(
 "https://www.youtube.com/watch?v=YRtOFPRnCP0",
 "https://www.youtube.com/watch?v=Di7vbNJwzZQ",
 "https://www.youtube.com/watch?v=YTFdjs_QGWc",
 "https://www.youtube.com/watch?v=tjTrFo-bITU"
)
$dir = "$env:USERPROFILE\voice_dl"; New-Item -ItemType Directory -Force $dir | Out-Null
$i = 1
foreach ($u in $urls) {
  Write-Output ("=== downloading voice$i : $u ===")
  & $ytdlp --no-playlist -x --audio-format wav --audio-quality 0 `
     --download-sections "*30-110" --force-keyframes-at-cuts `
     --ffmpeg-location $ff -o "$dir\voice$i.%(ext)s" $u 2>&1 | Select-Object -Last 3
  $i++
}
Write-Output "=== FILES ==="
Get-ChildItem $dir -Filter *.wav | Select-Object Name, @{n='MB';e={[math]::Round($_.Length/1MB,1)}}
