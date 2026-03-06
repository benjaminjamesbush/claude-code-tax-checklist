---
name: tax-checklist
description: Generate a comprehensive, deduplicated tax document checklist by scanning and visually examining every page of every PDF in the user's tax document collection.
---

# Tax Document Checklist Generator

Build a comprehensive, deduplicated tax document checklist from historical tax records. The goal is to identify every unique document type (form + institution + account) the user should expect to gather for their upcoming tax filing.

## Core Principles

**Do not trust filenames.** A file named `mortgage 1098.pdf` may contain a 1099-INT bundled on page 2. A file named `Misc.pdf` may contain five different forms. Every page of every file must be examined — filenames are hints, not facts.

**Nothing is assumed irrelevant.** Dental receipts, payment confirmations, state notices, letters, and bundled packets should all be assumed to contain checklist-worthy items.

---

## Step 1: Exploratory Scan

**Do not open or read any files during this step.** Only collect file paths, names, and directory structure. Reading file contents here will overflow the context window.

Run the scan script:

```
python ${CLAUDE_SKILL_DIR}/scripts/scan.py
```

Review the output and report:
- **Directory structure**: year folders, category folders, flat, nested, mixed?
- **File formats**: PDFs, images (JPG/PNG), spreadsheets, text files, other?
- **Naming conventions**: descriptive filenames, cryptic codes, dates, form numbers?
- **Volume**: total files, files per folder, approximate scope

This scan informs how you approach the remaining steps. The collection may be tidy or chaotic — adapt accordingly.

## Step 2: Render All PDF Pages to Small PNGs

**Do not open or read any files during this step.** Only render PDFs to PNGs. Reading file contents here will overflow the context window.

Run the render script:

```
python ${CLAUDE_SKILL_DIR}/scripts/render.py
```

This renders **every page of every PDF** at `dpi=100` (~850x1100px) into a `.tmp_pngs/` directory. The script will auto-install PyMuPDF if not present.

**Why PNGs?** Claude Code's Read tool can view images, but:
- Direct PDF reading renders pages as oversized images (>2000px) that crash the context
- Rendering at `dpi=100` produces ~850x1100px images — safely under the limit
- Each PNG is small enough for a subagent to process without context issues

**Why subagents?** Images accumulate in the main conversation context. Using subagents provides isolation — each agent gets its own context with only the images it needs.

Record the total page count from the script output — you need this for verification.

## Step 3: Visual Examination via Subagents

**Do not read any PNG files in the main conversation context.** Use subagents for all image reading. Reading images here will overflow the context window.

Launch one subagent per PNG — one agent, one page. Run 3 subagents in parallel for throughput.

### Subagent Prompt Template

```
Read the following PNG image of a scanned tax document page and identify:
- Form type / document type (e.g., "1099-INT", "dental receipt", "payment confirmation")
- Institution / source
- Person / account holder
- Tax year
- Any other tax-relevant details (dollar amounts, account numbers, deadlines)

File: <path_to_png>

Return a brief structured summary of the page. Be concise.
```

Use `model: haiku` for subagents to minimize cost — form identification doesn't require the most capable model.

### Tracking
Maintain a running tally:
- Expected pages (from Step 2 render count)
- Examined pages (from subagent results)
- These MUST match at the end. If they don't, re-launch subagents and troubleshoot as needed — never read images directly in the main context.

## Step 4: Compile and Write Checklist

### Merge All Findings

Combine all results from visual examination (Step 3).

Extract every unique **institution + form type + account** combination.

### Deduplicate Across Years

The same document type appearing in multiple years = one checklist item with a year range. Deduplicate by institution + form type + account.

Example: If `Robinhood 1099` appears across 2016–2024 → one item with `*Seen: 2016–2024*`

### Detect Institutional Transitions

Financial institutions merge, rebrand, and transfer accounts. Watch for:
- Brokerage acquisitions (same account, new institution name)
- Mortgage servicer transfers (same loan, different servicer issuing the 1098)
- Account number format changes during transitions
- Documents from two different institutions in the same year for the same account

When detected, note these in the checklist so the user understands that differently-named items may represent the same account.

### Write the Checklist

Output format: Markdown file with checkbox items. Categories are examples — adapt based on what you actually find. Only include categories relevant to the user's documents, and add new ones as needed.

Common categories: Income (W-2, 1099-MISC, 1099-NEC, 1099-G), Investments & Brokerage (1099 Composites, K-1s, 1099-B, 1099-DIV), Banking (1099-INT), Retirement (1099-R, 5498), Mortgage & Property (1098, property tax), Health Insurance (1095-A/B/C), Education (1098-T, 1098-E), Charitable Contributions, Estimated Tax Payments, Tax Notices & Balance Due Payments, Items That May No Longer Apply.

```markdown
# Tax Document Checklist

Deduplicated from [N] years of tax records ([RANGE]). Gather these documents for your tax preparer.

---

## [Category]

- [ ] **[Institution] — [Form Type]** ([Account description])
  [Additional details about what the form includes.]
  *Seen: [year range]*

...

## Items That May No Longer Apply
...

---

## Notes
- [Institutional transitions detected]
- [Filing states, if multiple]
- [Any other relevant context discovered during examination]

## Verification
- [N] PDF files rendered and visually examined ([N] pages total)
- Every page visually inspected — zero pages skipped
```

**Do not delete the `.tmp_pngs/` directory.** The user may have follow-up questions that require re-examining specific pages. The directory contains a `manifest.txt` mapping each PNG back to its source PDF and page number.

### Flagging Legacy Items

Items last seen more than 3 years ago should be moved to "Items That May No Longer Apply" with a note like:
`*(last seen 2016 — check if applicable)*`

Do NOT remove them — the user may still need them.

---

## Error Handling — ZERO Tolerance for Silent Failures

- If a PDF fails to render: try alternative DPI, check file corruption, but **never skip it**
- If a subagent fails to read an image: retry with a fresh subagent, re-render at different DPI, but **never skip it**
- If a file path is wrong (special characters, wrong casing): search for the correct path using `os.walk`, but **never skip it**
- **Every single page of every PDF must be examined.** If something can't be examined, stop and report the failure explicitly — do not continue as if it was handled.

## Technical Notes

- **PyMuPDF import**: `import fitz` (not `import pymupdf`)
- **Shell safety**: Filenames may contain `$`, `%`, spaces, parentheses, apostrophes, commas. Always use Python for file operations, not shell commands.
- **PDF page counting**: `len(fitz.open(path))` gives total pages
- **Image size at dpi=100**: Standard US letter (8.5x11") renders to ~850x1100px. This is safely under Claude's ~2000px image processing limit.
- **Scanned vs. digital PDFs**: Many personal tax documents are scans (photos of paper). Even digital PDFs may have content (stamps, images, bundled forms) not captured by text extraction. Visual examination of every page avoids missing anything.
