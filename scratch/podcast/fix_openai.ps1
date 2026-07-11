$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
Write-Output '=== installing openai>=2.30.0 ==='
& $py -m pip install "openai>=2.30.0" 2>&1 | Select-Object -Last 10
Write-Output '=== versions ==='
& $py -c "import importlib.metadata as m; print('openai', m.version('openai')); print('ag2', m.version('ag2'))" 2>&1
& $py -c "import openai, neuralnoise, kokoro; from autogen.agentchat.contrib.swarm_agent import SwarmResult; print('imports_ok')" 2>&1
