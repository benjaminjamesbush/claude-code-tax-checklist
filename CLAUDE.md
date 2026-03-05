# Tax Document Checklist Generator — Agent Instructions

You are helping a user build a comprehensive, deduplicated tax document checklist from their historical tax records. The goal is to identify every unique document type (form + institution + account) they should expect to gather for their upcoming tax filing.

## Overview

The user has tax documents stored as PDFs — possibly organized in year folders, by category, in a flat directory, or any other structure. Do not assume any particular organization. Many PDFs will have clear filenames that identify their contents (e.g., `robinhood 1099.pdf`), but many others will be ambiguous (e.g., `packet 1.pdf`, `Misc.pdf`, `scanned docs.pdf`). Your job is to examine everything and produce a checklist.

**Nothing is assumed irrelevant.** Dental receipts, payment confirmations, state notices, letters, and bundled packets may all contain checklist-worthy items.

---

## Step 1: Catalog All PDFs

Ask the user where their tax documents are stored, then recursively scan for all `.pdf` files:

```python
import os
base = "<USER_SPECIFIED_DIR>"
all_pdfs = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f.lower().endswith('.pdf'):
            all_pdfs.append(os.path.join(root, f))
```

Print the full list with relative paths. Count total files. Note the directory structure — files may be in year folders, category folders, flat, or any combination. Adapt accordingly.

## Step 2: Classify Files as Clear vs. Ambiguous

**Clear filenames** contain explicit form numbers or obvious document types. These can be cataloged from the filename alone:
- IRS form numbers: `1040`, `1099`, `1098`, `1095`, `W-2`, `K-1`, `8879`
- Obvious types: `Estimated Payment`, `Estimated Tax Payment`, `Tax Return`, `State of [state name]`
- Institution + form combos: `schwab IRA`, `robinhood 1099`, `mortgage 1098`

**Ambiguous filenames** lack clear form type identification and require visual examination:
- Generic names: `Misc`, `packet`, `scanned docs`, `tax scans`
- Institution only without form type: `bank of america.pdf`, `blue shield.pdf`
- Descriptions without form types: `dental receipt`, `property tax`, `negligence response`
- Vague payment references: `payment 12-22-2019.pdf`, `cp2000 Payment Confirmation.pdf`

Use substring matching (case-insensitive) against the relative file path to classify. When in doubt, classify as ambiguous — it's better to examine a file unnecessarily than to skip one.

Report the classification: how many clear, how many ambiguous, total page count of ambiguous files.

## Step 3: Extract Text from Ambiguous PDFs (Quick Check)

Before rendering to images, try text extraction on each ambiguous PDF:

```python
import fitz
doc = fitz.open(filepath)
for page in doc:
    text = page.get_text().strip()
    if text:
        # Has extractable text — may not need visual examination
        print(text[:500])
```

Many tax documents are **scanned images with zero extractable text**. These require visual examination (Step 4). If a PDF has good text, catalog its contents from the text and skip rendering.

## Step 4: Render Ambiguous Pages to Small PNGs

**Why PNGs?** Claude Code's Read tool can view images, but:
- Direct PDF reading renders pages as oversized images (>2000px) that crash the context
- Rendering at `dpi=100` produces ~850x1100px images — safely under the limit
- Each PNG is small enough for a subagent to process without context issues

**Why subagents?** Images accumulate in the main conversation context. Using subagents provides isolation — each agent gets its own context with only the images it needs.

Run a single Python script:

```python
import fitz
import os
import re

base = "<USER_SPECIFIED_DIR>"
outdir = os.path.join(base, '.tmp_pngs')
os.makedirs(outdir, exist_ok=True)

total_pages = 0
errors = []

for relpath in ambiguous_files:  # List from Step 2
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
            total_pages += 1
        doc.close()
        print(f'OK {len(doc):3d}p | {relpath}')
    except Exception as e:
        errors.append(f'RENDER ERROR: {relpath} | {e}')

print(f'\nFiles: {len(ambiguous_files)}, Pages rendered: {total_pages}')
if errors:
    print(f'ERRORS: {errors}')
```

**Important:**
- Use `dpi=100` — this keeps images under 2000px on both dimensions
- Sanitize filenames — some have `$`, spaces, parentheses, URL-encoded characters
- Use Python for all file operations — shell commands break on special characters in filenames
- Track page counts — you need a running tally for verification

## Step 5: Visual Examination via Subagents

Launch subagents to read the PNG files. Each subagent:
- Receives a list of PNG file paths (grouped by source PDF)
- Reads each image using the Read tool
- Returns a structured summary of each page

### Grouping Strategy
- Group pages **by source PDF** — one subagent per PDF
- Keep each subagent to **~6-10 pages max**
- For large PDFs (>10 pages), split across multiple subagents
- Run **3 subagents in parallel** for throughput

### Subagent Prompt Template

```
Read each of the following PNG images of scanned tax document pages.
For EACH page, identify:
- Form type / document type (e.g., "1099-INT", "dental receipt", "payment confirmation")
- Institution / source
- Person / account holder
- Tax year
- Any other tax-relevant details (dollar amounts, account numbers, deadlines)

Read ALL of these files and report on each one:
1. <path_to_png_1>
2. <path_to_png_2>
...

Return a structured summary of each page.
```

Use `model: haiku` for subagents to minimize cost — form identification doesn't require the most capable model.

### Tracking
Maintain a running tally:
- Expected pages (from Step 4 render count)
- Examined pages (from subagent results)
- These MUST match at the end. If they don't, find and examine the missing pages.

## Step 6: Compile and Write Checklist

### Merge All Findings

Combine results from:
- Clear files (cataloged from filenames in Step 2)
- Text-extracted files (from Step 3)
- Visually examined files (from Step 5)

Extract every unique **institution + form type + account** combination.

### Deduplicate Across Years

The same document type appearing in multiple years = one checklist item with a year range. Determine the tax year from folder names, filenames, or the document contents themselves.

Example: If `Robinhood 1099` appears across 2016–2024 → one item with `*Seen: 2016–2024*`

### Detect Institutional Transitions

Financial institutions merge, rebrand, and transfer accounts. Watch for:
- Brokerage acquisitions (same account, new institution name)
- Mortgage servicer transfers (same loan, different servicer issuing the 1098)
- Account number format changes during transitions
- Documents from two different institutions in the same year for the same account

When detected, note these in the checklist so the user understands that differently-named items may represent the same account.

### Write the Checklist

Output format: Markdown file with checkbox items.

```markdown
# [YEAR] Tax Document Checklist

Deduplicated from [N] years of tax records ([RANGE]). Gather these documents for your tax preparer.

---

## Investments & Brokerage

- [ ] **[Institution] — [Form Type]** ([Account description])
  [Additional details about what the form includes.]
  *Seen: [year range]*

## Banking — Interest Income
...

## Retirement — IRA Distributions
...

## Mortgage & Property
...

## Health Insurance
...

## State Tax Refunds
...

## Charitable Contributions
...

## Estimated Tax Payments
...

## Tax Balance Due Payments & Notices
...

## Items That May No Longer Apply
...

---

## Notes
- [Institutional transitions detected]
- [Filing states, if multiple]
- [Any other relevant context discovered during examination]

## Verification
- [N] ambiguous PDF files examined ([N] pages total)
- [N] total PDF files cataloged across [RANGE]
- Every page visually inspected — zero pages skipped
```

### Categories

Create categories based on what you actually find in the user's documents. Common categories include:
- **Income** — W-2s, 1099-MISC, 1099-NEC, 1099-G
- **Investments & Brokerage** — 1099 Composites/Consolidated, K-1s, 1099-B, 1099-DIV
- **Banking — Interest Income** — 1099-INT from banks
- **Retirement** — 1099-R, 5498, pension statements
- **Mortgage & Property** — 1098, property tax bills, escrow statements
- **Health Insurance** — 1095-A, 1095-B, 1095-C
- **Education** — 1098-T, 1098-E
- **Charitable Contributions** — donation receipts (cash and non-cash)
- **Estimated Tax Payments** — federal, state, local payment confirmations
- **Tax Notices & Balance Due Payments** — IRS/state notices, underpayment payments
- **Items That May No Longer Apply** — legacy items with `(check if applicable)` flag

Only include categories relevant to the user's documents. Add new categories as needed.

### Flagging Legacy Items

Items last seen more than 3 years ago should be moved to "Items That May No Longer Apply" with a note like:
`*(last seen 2016 — check if applicable)*`

Do NOT remove them — the user may still need them.

## Step 7: Clean Up

Delete the `.tmp_pngs/` directory after all examination is complete:

```python
import shutil
shutil.rmtree(os.path.join(base, '.tmp_pngs'))
```

---

## Error Handling — ZERO Tolerance for Silent Failures

- If a PDF fails to render: try alternative DPI, check file corruption, but **never skip it**
- If a subagent fails to read an image: retry with a fresh subagent, re-render at different DPI, but **never skip it**
- If a file path is wrong (special characters, wrong casing): search for the correct path using `os.walk`, but **never skip it**
- If PyMuPDF is not installed: install it with `pip install pymupdf`
- **Every single page of every ambiguous PDF must be examined.** If something can't be examined, stop and report the failure explicitly — do not continue as if it was handled.

## Technical Notes

- **PyMuPDF import**: `import fitz` (not `import pymupdf`)
- **Shell safety**: Filenames may contain `$`, `%`, spaces, parentheses, apostrophes, commas. Always use Python for file operations, not shell commands.
- **PDF page counting**: `len(fitz.open(path))` gives total pages
- **Image size at dpi=100**: Standard US letter (8.5x11") renders to ~850x1100px. This is safely under Claude's ~2000px image processing limit.
- **Scanned vs. digital PDFs**: Many personal tax documents are scans (photos of paper). These have zero extractable text. Always check `page.get_text()` first, but expect most ambiguous files to be scans requiring visual examination.
