"""
Step 2: Render All PDF Pages to Small PNGs

Renders every page of every PDF in the current working directory to a PNG
at dpi=100 (~850x1100px), safely under Claude's ~2000px image limit.

Usage:
    python render.py                     # scan cwd for PDFs
    python render.py /path/to/tax/docs   # scan specified directory

Output directory: <base>/.tmp_pngs/
"""

import os
import re
import sys

try:
    import fitz
except ImportError:
    print("PyMuPDF is not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymupdf"])
    import fitz

base = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
outdir = os.path.join(base, '.tmp_pngs')
os.makedirs(outdir, exist_ok=True)

# Find all PDFs
pdf_files = []
for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for f in files:
        if f.lower().endswith('.pdf'):
            pdf_files.append(os.path.relpath(os.path.join(root, f), base))

total_pages = 0
errors = []
manifest = []  # Maps each PNG back to its source PDF and page number

for relpath in pdf_files:
    fullpath = os.path.join(base, relpath)
    if not os.path.exists(fullpath):
        errors.append(f'MISSING: {relpath}')
        continue
    try:
        doc = fitz.open(fullpath)
        # Build a descriptive prefix from the relative path
        parts = os.path.normpath(relpath).replace(os.sep, '_')
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', os.path.splitext(parts)[0])[:60]
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(dpi=100)
            png_name = f'{sanitized}_p{i+1:02d}.png'
            pix.save(os.path.join(outdir, png_name))
            manifest.append(f'{png_name} <- {relpath} (page {i+1})')
            total_pages += 1
        doc.close()
        print(f'OK {len(doc):3d}p | {relpath}')
    except Exception as e:
        errors.append(f'RENDER ERROR: {relpath} | {e}')

# Write manifest so PNGs can be traced back to source PDFs
manifest_path = os.path.join(outdir, 'manifest.txt')
with open(manifest_path, 'w') as f:
    for line in manifest:
        f.write(line + '\n')

print(f'\nFiles: {len(pdf_files)}, Pages rendered: {total_pages}')
print(f'Output directory: {outdir}')
print(f'Manifest: {manifest_path}')
if errors:
    print(f'\nERRORS ({len(errors)}):')
    for err in errors:
        print(f'  {err}')
