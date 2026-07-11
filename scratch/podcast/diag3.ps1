cd $env:USERPROFILE\neuralnoise_source\neuralnoise-main
Write-Output '===UVLOCK_AG2_VERSION==='
$lines = Get-Content uv.lock
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match 'name = "(ag2|autogen|pyautogen)"') {
    Write-Output ($lines[$i] + ' | ' + $lines[$i+1])
  }
}
Write-Output '===SAVE_FUNCS_AND_CTXVAR==='
Get-ChildItem src\neuralnoise -Recurse -Filter *.py | Select-String -Pattern 'def save_|context_variables|ContextVariables|register_for|initiate_swarm|AfterWork|GroupChat'
