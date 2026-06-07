import json
import os

def extract_code(ipynb_path, out_path):
    try:
        with open(ipynb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            for i, cell in enumerate(data.get('cells', [])):
                if cell.get('cell_type') == 'code':
                    f.write(f'# --- Cell {i} ---\n')
                    f.write(''.join(cell.get('source', [])))
                    f.write('\n\n')
        print(f'Extracted {ipynb_path} to {out_path}')
    except Exception as e:
        print(f'Error extracting {ipynb_path}: {e}')

extract_code(r'C:\Users\Sam Pavi\Downloads\no-error-heartbeat.ipynb', 'heartbeat_code.py')
extract_code(r'C:\Users\Sam Pavi\Downloads\arc-agi-3-forge-v3.ipynb', 'forge_code.py')
