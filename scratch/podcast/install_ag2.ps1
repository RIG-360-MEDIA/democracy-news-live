$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
Write-Output '=== current ag2 ==='
& $py -c "import importlib.metadata as m; print(m.version('ag2'))" 2>&1
Write-Output '=== installing ag2[rag]==0.7.6 ==='
& $py -m pip install "ag2[rag]==0.7.6" 2>&1 | Select-Object -Last 18
Write-Output '=== ag2 after ==='
& $py -c "import importlib.metadata as m; print('ag2', m.version('ag2'))" 2>&1
Write-Output '=== import sanity ==='
& $py -c "from autogen.agentchat.contrib.swarm_agent import SwarmResult; import neuralnoise, kokoro; print('imports_ok')" 2>&1
