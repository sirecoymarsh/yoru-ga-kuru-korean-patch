"""r15 helper: static scan of the Codex helper-module import closure (read-only; nothing is imported or executed)."""
import ast, sys, json
from pathlib import Path
HERE = Path(r'C:\Users\CadriacLord\OneDrive\문서\ChatGPT\밤이 온다 한국어화')
roots = sys.argv[1:] or ['build_term_switch_20260923', 'resume_compat_20260923', 'publish_cheat_menu_20260915',
                          'build_dungeon_sweep_20260916', 'build_instant_loot_20260915']
seen = {}
todo = list(roots)
while todo:
    m = todo.pop()
    if m in seen:
        continue
    f = HERE / (m + '.py')
    if not f.exists():
        seen[m] = None
        continue
    tree = ast.parse(f.read_text('utf8'))
    deps = []
    risky = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            deps += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            deps.append(node.module)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            continue
        elif isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and getattr(node.test.left, 'id', '') == '__name__':
            continue
        else:
            src = ast.get_source_segment(f.read_text('utf8'), node) or ''
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
            names = set()
            for c in calls:
                fn = c.func
                if isinstance(fn, ast.Attribute):
                    names.add(fn.attr)
                elif isinstance(fn, ast.Name):
                    names.add(fn.id)
            bad = names & {'mkdir', 'write_text', 'write_bytes', 'open', 'copy2', 'copyfile', 'rmtree', 'unlink', 'run', 'Popen', 'makedirs', 'rename', 'replace', 'main', 'system'}
            if bad:
                risky.append((node.lineno, sorted(bad), src[:160]))
    seen[m] = dict(deps=[d for d in deps if (HERE / (d + '.py')).exists()], risky=risky)
    todo += seen[m]['deps']
local = {k: v for k, v in seen.items() if v}
print('modules in closure:', len(local))
for k, v in sorted(local.items()):
    if v['risky']:
        print('RISKY', k, v['risky'])
print(json.dumps(sorted(local), ensure_ascii=False))
