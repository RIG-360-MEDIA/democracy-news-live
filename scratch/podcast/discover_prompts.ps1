$ErrorActionPreference = 'Continue'
$vpy = "$env:USERPROFILE\csm_venv\Scripts\python.exe"
Write-Output '=== csm-1b repo files ==='
& $vpy -c "from huggingface_hub import list_repo_files; print('\n'.join(f for f in list_repo_files('sesame/csm-1b')))" 2>&1
Write-Output '=== run_csm.py prompt defs (github) ==='
try {
  Invoke-WebRequest "https://raw.githubusercontent.com/SesameAILabs/csm/main/run_csm.py" -OutFile "$env:USERPROFILE\run_csm_ref.py" -UseBasicParsing
  Get-Content "$env:USERPROFILE\run_csm_ref.py" | Select-String -Pattern 'text|prompt|conversational|\.wav|hf_hub_download|filepath|gender|speaker' | Select-Object -First 45
} catch { Write-Output ('github_err: ' + $_.Exception.Message) }
