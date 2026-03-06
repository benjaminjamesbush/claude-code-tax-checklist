"""
Step 1: Exploratory Scan

Recursively scans the current working directory to catalog all files.
Does NOT open or read any file contents — only collects paths and metadata.

Output: prints a summary of directory structure, file formats, naming
conventions, and volume, plus a list of all PDF files found.
"""

import os
import sys
from collections import defaultdict

base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), 'tax-documents')

all_files = []
pdf_files = []
extensions = defaultdict(int)
folders = defaultdict(list)

for root, dirs, files in os.walk(base):
    # Skip hidden directories (like .tmp_pngs, .git, .claude)
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    rel_root = os.path.relpath(root, base)
    for f in files:
        relpath = os.path.join(rel_root, f) if rel_root != '.' else f
        all_files.append(relpath)
        ext = os.path.splitext(f)[1].lower()
        extensions[ext] += 1
        folders[rel_root].append(f)
        if ext == '.pdf':
            pdf_files.append(relpath)

print(f"Base directory: {base}")
print(f"Total files: {len(all_files)}")
print(f"PDF files: {len(pdf_files)}")
print()

print("=== File formats ===")
for ext, count in sorted(extensions.items(), key=lambda x: -x[1]):
    print(f"  {ext or '(no extension)':20s} {count}")
print()

print("=== Directory structure ===")
for folder, files_in_folder in sorted(folders.items()):
    print(f"  {folder}/ ({len(files_in_folder)} files)")
print()

print("=== All PDF files ===")
for p in sorted(pdf_files):
    print(f"  {p}")
