"""
Step 5: Clean Up

Deletes the .tmp_pngs/ directory after all examination is complete.

Usage:
    python cleanup.py                     # clean cwd
    python cleanup.py /path/to/tax/docs   # clean specified directory
"""

import os
import shutil
import sys

base = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
tmp_dir = os.path.join(base, '.tmp_pngs')

if os.path.exists(tmp_dir):
    count = len(os.listdir(tmp_dir))
    shutil.rmtree(tmp_dir)
    print(f'Deleted {tmp_dir} ({count} files)')
else:
    print(f'Nothing to clean up — {tmp_dir} does not exist')
