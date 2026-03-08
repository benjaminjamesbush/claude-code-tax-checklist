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

# Collect findings files, checking for non-empty and required fields
findings = set()
empty = []
malformed = []
required_fields = {'file:', 'form_type:', 'institution:'}
for f in os.listdir(findings_dir):
    if f.endswith('.findings.txt'):
        base_name = f[:-len('.findings.txt')]
        fpath = os.path.join(findings_dir, f)
        # Check non-empty
        if os.path.getsize(fpath) == 0:
            empty.append(f)
            continue
        # Check required fields present
        content = open(fpath).read().lower()
        missing_fields = [field for field in required_fields if field not in content]
        if missing_fields:
            malformed.append((f, missing_fields))
            continue
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

has_issues = False

if empty:
    print(f'\nEMPTY ({len(empty)} files):')
    for f in empty:
        print(f'  {f}')
    has_issues = True

if malformed:
    print(f'\nMALFORMED ({len(malformed)} files):')
    for f, fields in malformed:
        print(f'  {f} — missing: {", ".join(fields)}')
    has_issues = True

if missing:
    print(f'\nMISSING ({len(missing)} files):')
    for f in missing:
        print(f'  {f}')
    has_issues = True

if has_issues:
    sys.exit(1)
else:
    print('\nAll files covered. OK to proceed.')
    sys.exit(0)
