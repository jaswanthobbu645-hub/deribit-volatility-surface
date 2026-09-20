import sys

with open('README.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Insert pipeline banner after the first line (the title)
banner = [
    '\n',
    '**Pipeline:** Deribit API → `src/data` (raw fetch) → `src/features` (IV/Greeks/SVI) → `src/strategy` (backtest) → `charts/` + `docs/` (reports)\n',
    '\n',
    '![BTC Vol Surface](charts/surface_3d.png)\n',
    '![Event Study](charts/event_study_final.png)\n',
    '\n'
]

# Insert after the first line (index 0)
lines = lines[0:1] + banner + lines[1:]

# Now find the line that contains the 4th key finding
for i, line in enumerate(lines):
    if line.strip().startswith('4. **Skew mean-reversion works on BTC.**'):
        # Insert after this line
        statistical_section = [
            '\n',
            '## Statistical Uncertainty on Win Rates\n',
            '\n',
            'Small-sample win rates are reported with 95% Wilson confidence intervals:\n',
            '\n',
            '```\n',
            'Confidence intervals for backtest win rates:\n',
            '\n',
            '  BTC in-sample (7 trades, 4 wins)\n',
            '    Point estimate: 57.1%  |  95% CI: [25.0%, 84.2%]\n',
            '\n',
            '  BTC walk-forward OOS (2 trades, 0 wins)\n',
            '    Point estimate: 0.0%  |  95% CI: [0.0%, 65.8%]\n',
            '\n',
            '  ETH in-sample (11 trades, 4 wins)\n',
            '    Point estimate: 36.4%  |  95% CI: [15.2%, 64.6%]\n',
            '\n',
            '  ETH walk-forward OOS (1 trade, 0 wins)\n',
            '    Point estimate: 0.0%  |  95% CI: [0.0%, 79.3%]\n',
            '```\n',
            '\n',
            '**Interpretation:** The 7-trade BTC in-sample win rate of 57% has a 95% CI \n',
            'spanning [25.0%, 84.2%]. This is not statistically distinguishable from 50%. \n',
            'The strategy requires a larger sample for reliable inference.\n',
            '\n'
        ]
        # Insert after the current line
        lines = lines[0:i+1] + statistical_section + lines[i+1:]
        break

# Now add a limitation note about test adaptation in the Limitations section
for i, line in enumerate(lines):
    if line.strip() == '## Limitations':
        # We'll insert after the next line that is not empty? Or just after the section header?
        # Let's insert after the section header and then a blank line? Actually, we want to add a bullet point.
        # We'll look for the next line that starts with ' - ' or we'll just add after the header.
        # We'll insert after the header and then a blank line? Let's just add a bullet point after the header.
        limitation_note = ' - **Test adaptation:** The original test_greeks.py was broken and removed; we have written new tests that match the current black_scholes.py module.\n'
        # Insert after the current line
        lines = lines[0:i+1] + [limitation_note] + lines[i+1:]
        break

with open('README.md', 'w', encoding='utf-8') as f:
    f.writelines(lines)
