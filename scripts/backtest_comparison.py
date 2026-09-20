import pandas as pd
import subprocess
import sys
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), '..')

def run_wf(train, test):
    """Temporarily modify walk_forward.py and run."""
    wf_path = os.path.join(ROOT, 'src', 'strategy', 'walk_forward.py')
    with open(wf_path, 'r') as f:
        content = f.read()
    
    # Replace TRAIN, TEST line
    content = re.sub(r'TRAIN,\s*TEST\s*=\s*\d+,\s*\d+', f'TRAIN, TEST = {train}, {test}', content)
    
    with open(wf_path, 'w') as f:
        f.write(content)
    
    # Run
    result = subprocess.run([sys.executable, wf_path], capture_output=True, text=True, cwd=ROOT)
    return result.stdout

print("=" * 70)
print("WALK-FORWARD SPLIT COMPARISON")
print("=" * 70)

for train, test in [(60, 20), (30, 10)]:
    print(f"\n{'='*70}")
    print(f"SPLIT: {train}-day train, {test}-day test")
    print(f"{'='*70}")
    output = run_wf(train, test)
    print(output)
