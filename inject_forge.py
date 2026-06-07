lines = []
with open('forge_code.py', 'r', encoding='utf-8') as f:
    in_agent = False
    for line in f:
        if line.startswith('%%writefile /kaggle/working/my_agent.py'):
            in_agent = True
            continue
        if line.startswith('# --- Cell 4 ---'):
            break
        if in_agent:
            lines.append(line)

# Trim trailing spaces or newlines just in case there are trailing lines of garbage before the loop break
while lines and (lines[-1].strip() == "" or lines[-1].strip() == '"""' or lines[-1].strip() == "'''"):
    lines.pop()

with open(r'agent\my_agent.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

