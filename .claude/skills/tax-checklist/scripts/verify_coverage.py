#!/usr/bin/env python3
"""
Verify 100% coverage: every prepared file has a corresponding findings file.
Exits 0 if complete, exits 1 if gaps found (prints missing files to stdout).
"""

import os
import sys

base = os.path.join('tax-documents', '.tmp_prepared')
findings_dir = os.path.join(base, 'findings')

if not os.path.isdir(base):
    print(f'ERROR: {base} does not exist. Run prepare.py first.', file=sys.stderr)
    sys.exit(1)

if not os.path.isdir(findings_dir):
    print(f'ERROR: {findings_dir} does not exist. No findings yet.', file=sys.stderr)
    sys.exit(1)

# Collect prepared files (PNGs and TXTs, excluding metadata)
skip = {'manifest.txt', 'filelist.txt', 'findings_merged.txt'}
prepared = set()
for f in os.listdir(base):
    if f in skip or os.path.isdir(os.path.join(base, f)):
        continue
    if f.endswith('.png') or f.endswith('.txt'):
        prepared.add(f)

# Collect findings files
findings = set()
for f in os.listdir(findings_dir):
    if f.endswith('.findings.txt'):
        # Strip .findings.txt to get the base name, then re-add extension
        base_name = f[:-len('.findings.txt')]
        # Find which extension the prepared file has
        if base_name + '.png' in prepared:
            findings.add(base_name + '.png')
        elif base_name + '.txt' in prepared:
            findings.add(base_name + '.txt')
        else:
            findings.add(base_name)  # Unknown, still count it

# Find gaps
missing = sorted(prepared - findings)

print(f'Prepared files: {len(prepared)}')
print(f'Findings files: {len(findings)}')
print(f'Coverage: {len(findings)}/{len(prepared)} ({100*len(findings)//len(prepared) if prepared else 0}%)')

if missing:
    print(f'\nMISSING ({len(missing)} files):')
    for f in missing:
        print(f'  {f}')
    sys.exit(1)
else:
    print('\nAll files covered. OK to proceed.')
    sys.exit(0)
