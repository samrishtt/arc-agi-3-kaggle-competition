with open('heartbeat_code.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(r'agent\my_agent.py', 'w', encoding='utf-8') as f:
    # Skip the %%writefile line (which is on line 7 or so)
    # The actual code starts around line 8 with '# ==================='
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('# ===') and 'MASTER BASELINE' in lines[i+1]:
            start_idx = i
            break
    
    f.writelines(lines[start_idx:])
