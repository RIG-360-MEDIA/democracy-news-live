import importlib, re, os
base = os.path.expanduser(r'~\neuralnoise_source\neuralnoise-main\src\neuralnoise\studio\agents')
print('=== CTXVAR_IMPORT ===')
for p in ['autogen.agentchat.group.context_variables', 'autogen.agentchat.group', 'autogen']:
    try:
        m = importlib.import_module(p)
        hits = [n for n in dir(m) if 'ContextVariables' in n]
        if hits:
            print('FOUND', p, hits)
    except Exception as e:
        print(p, 'ERR', repr(e)[:50])
try:
    from autogen import ContextVariables as CV
    print('autogen.ContextVariables OK; methods:', [x for x in dir(CV) if not x.startswith('_')])
except Exception as e:
    print('autogen.CV ERR', repr(e)[:60])
print('=== SwarmResult ===')
try:
    from autogen.agentchat.contrib.swarm_agent import SwarmResult
    print('SwarmResult fields:', list(getattr(SwarmResult, 'model_fields', {}).keys()))
except Exception as e:
    print('SR ERR', repr(e)[:60])
print('=== AGENT_FILES ===')
for f in ['content_analyzer_agent.py', 'planner_agent.py', 'script_generator_agent.py', 'editor_agent.py']:
    path = os.path.join(base, f)
    print('----', f)
    try:
        for i, line in enumerate(open(path, encoding='utf-8').read().splitlines(), 1):
            if re.search(r'context_variables|model_validate|def save_|SwarmResult|^from|^import', line):
                print(i, line.rstrip()[:120])
    except Exception as e:
        print('readerr', e)
