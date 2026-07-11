$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
Write-Output '=== restoring ag2==0.13.3 ==='
& $py -m pip install "ag2==0.13.3" 2>&1 | Select-Object -Last 10
Write-Output '=== verify ==='
& $py -c "import importlib.metadata as m; print('ag2', m.version('ag2'))" 2>&1
& $py -c "from autogen.agentchat.contrib.swarm_agent import SwarmResult; print('swarm_import_OK')" 2>&1
& $py -c "import neuralnoise, kokoro; print('nn_kokoro_OK')" 2>&1
