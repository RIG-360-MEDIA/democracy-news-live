$py="$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
& $py -m pip install -q datasets soundfile 2>&1 | Select-Object -Last 2
& $py "$env:USERPROFILE\get_libritts_voices.py" 2>&1
