"""
Deribit Volatility Surface Pipeline — Main Entry Point

Usage:
    python main.py fetch-live          # Run daily live pipeline
    python main.py fetch-historical    # Fetch historical surfaces
    python main.py fetch-dvol          # Fetch 1-year DVOL data
    python main.py analyze             # Compute metrics + generate charts
    python main.py backtest            # Walk-forward backtest
    python main.py all                 # Run everything
"""

import sys
import subprocess
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

COMMANDS = {
    'fetch-live': ['src/data/fetch_live.py'],
    'fetch-historical': ['src/data/fetch_historical_btc.py', 'src/data/fetch_historical_eth.py'],
    'fetch-dvol': ['src/data/fetch_dvol.py'],
    'analyze': ['src/features/compute_metrics.py'],
    'backtest': ['src/strategy/walk_forward.py'],
}

def run_script(path):
    full_path = os.path.join(ROOT, path)
    print(f"\n>>> Running {path}")
    result = subprocess.run([sys.executable, full_path], cwd=ROOT)
    if result.returncode != 0:
        print(f"!!! Failed: {path} (exit {result.returncode})")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'all':
        for key in ['fetch-historical', 'fetch-dvol', 'analyze', 'backtest']:
            for script in COMMANDS[key]:
                run_script(script)
    elif cmd in COMMANDS:
        for script in COMMANDS[cmd]:
            run_script(script)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)

if __name__ == '__main__':
    main()