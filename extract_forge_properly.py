lines = []
with open('forge_code.py', 'r', encoding='utf-8') as f:
    in_agent = False
    for line in f:
        if line.startswith('# =====================================================================') and 'FORGE v19' in line:
            in_agent = True
        
        if in_agent:
            if line.startswith('# --- Cell 3 ---') or line.startswith('!curl') or line.startswith('!cd') or "with open('/kaggle/working/ARC-AGI-3-Agents/.env', 'w') as f:" in line:
                break
            lines.append(line)

with open(r'agent\my_agent.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
