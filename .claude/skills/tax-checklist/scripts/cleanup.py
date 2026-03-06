"""
Clean Up (manual only — never run automatically)

Deletes the .tmp_prepared/ and .tmp_zip_extracted/ directories.
Only run this when the user explicitly asks to clean up.

Usage:
    python cleanup.py                     # clean cwd
    python cleanup.py /path/to/tax/docs   # clean specified directory
"""

import os
import shutil
import sys

base = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

for dirname in ['.tmp_prepared', '.tmp_zip_extracted']:
    tmp_dir = os.path.join(base, dirname)
    if os.path.exists(tmp_dir):
        count = len(os.listdir(tmp_dir))
        shutil.rmtree(tmp_dir)
        print(f'Deleted {tmp_dir} ({count} items)')
    else:
        print(f'Nothing to clean up — {tmp_dir} does not exist')
