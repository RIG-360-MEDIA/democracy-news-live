$py = "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\python.exe"
Write-Output '=== upgrading llama-index + chromadb stack ==='
& $py -m pip install -U "llama-index-core>=0.14.5" "llama-index-llms-ollama" "llama-index-vector-stores-chroma" "llama-index-embeddings-huggingface" "chromadb" 2>&1 | Select-Object -Last 14
Write-Output '=== verify ==='
& $py -c "from llama_index.core.base.llms.types import ThinkingBlock; print('ThinkingBlock_OK')" 2>&1
& $py -c "import chromadb; print('chromadb', chromadb.__version__)" 2>&1
& $py -c "import importlib.metadata as m; print('lic', m.version('llama-index-core'), 'openai', m.version('openai'), 'ag2', m.version('ag2'))" 2>&1
& $py -c "import neuralnoise, kokoro; print('nn_kokoro_ok')" 2>&1
