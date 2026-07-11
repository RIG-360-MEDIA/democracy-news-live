import os, sys, importlib, shutil
base = os.path.expanduser(r'~\neuralnoise_source\neuralnoise-main\src\neuralnoise\studio\agents')
src_root = os.path.expanduser(r'~\neuralnoise_source\neuralnoise-main\src')
files = ['content_analyzer_agent.py', 'planner_agent.py', 'script_generator_agent.py', 'editor_agent.py']
IMPORT = 'from autogen.agentchat.group.context_variables import ContextVariables'

# decide return form from SwarmResult field type
from autogen.agentchat.contrib.swarm_agent import SwarmResult
ann = str(SwarmResult.model_fields['context_variables'].annotation)
wrap_return = 'ContextVariables' in ann
print('SwarmResult.context_variables annotation:', ann, '| wrap_return =', wrap_return)

UNWRAP = ('SharedContext.model_validate('
          'context_variables.to_dict() if hasattr(context_variables, "to_dict") '
          'else getattr(context_variables, "data", context_variables))')

for f in files:
    p = os.path.join(base, f)
    src = open(p, encoding='utf-8').read()
    if not os.path.exists(p + '.bak'):
        shutil.copy(p, p + '.bak')
    orig = src
    if IMPORT not in src:
        src = src.replace('from autogen.agentchat.contrib.swarm_agent import SwarmResult',
                          'from autogen.agentchat.contrib.swarm_agent import SwarmResult\n' + IMPORT, 1)
    src = src.replace('context_variables: dict', 'context_variables: ContextVariables')
    src = src.replace('SharedContext.model_validate(context_variables)', UNWRAP)
    if wrap_return:
        src = src.replace('context_variables=shared_state.model_dump(),',
                          'context_variables=ContextVariables(data=shared_state.model_dump()),')
    open(p, 'w', encoding='utf-8').write(src)
    print(f, '-> CHANGED' if src != orig else '-> no change')

# verify imports (syntax + symbol resolution)
sys.path.insert(0, src_root)
for f in files:
    mod = 'neuralnoise.studio.agents.' + f[:-3]
    try:
        importlib.import_module(mod)
        print('import OK:', mod)
    except Exception as e:
        print('IMPORT FAIL:', mod, repr(e)[:140])
