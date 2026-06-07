lines = []
with open(r'agent\my_agent.py', 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('# --- Cell 2 ---') or line.startswith('!curl') or line.startswith('!cd') or line.startswith('# --- Cell 3 ---'):
            break
        lines.append(line)

with open(r'agent\my_agent.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
