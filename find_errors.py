import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'textwrap.dedent' in line:
            print(f"{i+1}: {line.strip()}")
