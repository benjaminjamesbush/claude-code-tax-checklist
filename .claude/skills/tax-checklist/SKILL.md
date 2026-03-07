---
name: tax-checklist
description: Generate a comprehensive, deduplicated tax document checklist by scanning and visually examining every page of every PDF in the user's tax document collection.
---

# Tax Document Checklist Generator

Build a comprehensive, deduplicated tax document checklist from historical tax records in the `tax-documents/` directory. The goal is to identify every unique document type (form + institution + account) the user should expect to gather for their upcoming tax filing. Only process files inside `tax-documents/` — do not scan or process any other files in the project.

## Core Principles

**Do not trust filenames.** A file named `mortgage 1098.pdf` may contain a 1099-INT bundled on page 2. A file named `Misc.pdf` may contain five different forms. Every page of every file must be examined — filenames are hints, not facts.

**Nothing is assumed irrelevant.** Dental receipts, payment confirmations, state notices, letters, test documents, and bundled packets should all be assumed to contain checklist-worthy items. Do not skip or dismiss any document based on its content — if something seems unimportant, include it in an appendix at the bottom of the checklist rather than omitting it.

---

## Context Management

**Do not read the skill scripts (scan.py, prepare.py, cleanup.py).** Just run them. Reading scripts wastes context on code you don't need to understand.

**Subagent results must be written to files, not returned to the main context.** With 1000+ subagent launches, returned results will overflow the context window. See Step 3 for details.

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

## Step 2: Prepare All Files for Examination

**Do not open or read any files during this step.** Only run the prepare script. Reading file contents here will overflow the context window.

Run the prepare script:

```
python ${CLAUDE_SKILL_DIR}/scripts/prepare.py
```

This processes every file into a `.tmp_prepared/` directory in one of two formats:
- **PNG** — PDF pages rendered at `dpi=100` (~850x1100px), images converted and resized
- **TXT** — text extracted from spreadsheets, Word docs, or copied from text/HTML/RTF files

The script auto-installs only the packages needed based on file types found:
- PDFs → PyMuPDF
- Images (JPG, PNG, GIF, TIFF, BMP, WEBP, AVIF, HEIC, HEIF) → Pillow + format plugins
- XLSX → openpyxl, XLS → xlrd
- DOCX → python-docx, DOC → doc2txt
- Text/CSV/MD/JSON/HTML/MHTML/RTF → built-in (no install needed)
- ZIP files → extracted first, then contents processed

**Why subagents?** Images and even text files accumulate in the main conversation context. Using subagents provides isolation — each agent gets its own context with only the file it needs.

Record the total output count from the script — you need this for verification.

## Step 3: Visual Examination via Subagents

**Do not read any PNG files in the main conversation context.** Use subagents for all image reading. Reading images here will overflow the context window.

### Why One Subagent Per Page (Do NOT Re-Batch)

Each file in `.tmp_prepared/` is a single page. Launch one subagent per file — one agent, one page, one image. Run 3 in parallel.

**Do NOT re-group pages into larger batches.** This is the most common failure mode: an agent sees 1000+ files, decides "one per file is too slow," batches them by year or document, and sends 60-80 images to a single subagent. The subagent then silently skips pages — in testing, batches of 77 pages achieved only 35% coverage. The per-page approach exists to make skipping structurally impossible.

**Expected runtime:** ~60-90 minutes for a typical collection (1000-1500 pages at 3 parallel). This is acceptable — the checklist runs once per year and missing a single form can mean a missed deduction or IRS notice.

**Expected cost:** ~$1-2 in Haiku API calls. Cheap insurance for completeness.

### Subagent Output: Write to Files (Do NOT Return to Main Context)

Before launching subagents, create the findings directory:
```
mkdir -p tax-documents/.tmp_prepared/findings
```

Each subagent must **write its findings to a file** rather than returning them as a response. With 1000+ subagents, returned results will accumulate in the main conversation and overflow the context window. This is not optional.

### Subagent Prompt Template (PNG files)

```
Read the following PNG image of a scanned tax document page and identify:
- Form type / document type (e.g., "1099-INT", "dental receipt", "payment confirmation")
- Institution / source
- Person / account holder
- Tax year
- Any other tax-relevant details (dollar amounts, account numbers, deadlines)

File: <path_to_png>

Write your findings to: <path_to_findings_txt>

Use this exact format:
file: <filename>
form_type: <form type or document type>
institution: <institution or source>
person: <person or account holder>
tax_year: <year>
details: <any other relevant details>

Be concise. Write the file and confirm done.
```

Replace `<path_to_findings_txt>` with `tax-documents/.tmp_prepared/findings/<filename_without_ext>.findings.txt`.

### Subagent Prompt Template (TXT files)

```
Read the following text extracted from a tax document and identify:
- Form type / document type (e.g., "1099-INT", "dental receipt", "payment confirmation")
- Institution / source
- Person / account holder
- Tax year
- Any other tax-relevant details (dollar amounts, account numbers, deadlines)

File: <path_to_txt>

Write your findings to: <path_to_findings_txt>

Use this exact format:
file: <filename>
form_type: <form type or document type>
institution: <institution or source>
person: <person or account holder>
tax_year: <year>
details: <any other relevant details>

Be concise. Write the file and confirm done.
```

Use `model: haiku` for subagents to minimize cost — form identification doesn't require the most capable model.

### Tracking and Verification

Track only counts in the main context — not findings content:
- Expected outputs (from Step 2 output count)
- Subagents launched (increment as you go)
- These MUST match at the end. If they don't, re-launch subagents and troubleshoot as needed — never read images directly in the main context.

After all subagents complete, programmatically verify 100% coverage:

1. List every file in `.tmp_prepared/` (excluding `manifest.txt` and the `findings/` directory)
2. List every `.findings.txt` in `.tmp_prepared/findings/`
3. Any prepared file without a corresponding findings file = a gap. Re-launch a subagent for it.
4. Do not proceed to Step 4 until coverage is confirmed at 100%.

## Step 4: Compile and Write Checklist

**Do not read findings files in the main context.** Delegate compilation to a subagent with a fresh context window.

### Merge Findings into One File

Concatenate all individual findings into a single file:

```
cat tax-documents/.tmp_prepared/findings/*.findings.txt > tax-documents/.tmp_prepared/findings_merged.txt
```

### Launch Compilation Subagent

Launch a single subagent to read the merged findings and write the checklist. Use `model: sonnet` — compilation requires more reasoning than examination.

```
Read the file tax-documents/.tmp_prepared/findings_merged.txt, which contains
structured findings from examining every page of a tax document collection.

Your task:
1. Extract every unique institution + form type + account combination
2. Deduplicate across years — same document type in multiple years = one checklist
   item with a year range (e.g., "Seen: 2016–2024")
3. Detect institutional transitions — brokerages merge, mortgage servicers change,
   accounts transfer. Note these so the user understands differently-named items
   may be the same account.
4. Flag legacy items — anything last seen more than 3 years ago goes in
   "Items That May No Longer Apply" with *(last seen YYYY — check if applicable)*
5. Write the checklist to tax-documents/TAX_CHECKLIST.md

Output format: Markdown with checkbox items. Categories are examples — adapt based
on what you find. Only include categories relevant to the documents.

Common categories: Income (W-2, 1099-MISC, 1099-NEC, 1099-G), Investments &
Brokerage (1099 Composites, K-1s, 1099-B, 1099-DIV), Banking (1099-INT),
Retirement (1099-R, 5498), Mortgage & Property (1098, property tax), Health
Insurance (1095-A/B/C), Education (1098-T, 1098-E), Charitable Contributions,
Estimated Tax Payments, Tax Notices & Balance Due Payments, Items That May No
Longer Apply.

If any document seems unimportant, include it in an appendix rather than omitting.

Use this template:

# Tax Document Checklist

Deduplicated from [N] years of tax records ([RANGE]). Gather these documents
for tax season.

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
- [N] files processed, [N] outputs examined (PNGs + TXTs)
- Every page visually inspected — zero pages skipped
```

After the compilation subagent finishes, confirm that `TAX_CHECKLIST.md` was written and report the summary to the user.

**Do not delete the `.tmp_prepared/` directory.** The user may have follow-up questions that require re-examining specific files. The directory contains a `manifest.txt` mapping each output (PNG or TXT) back to its source file.

---

## Error Handling — ZERO Tolerance for Silent Failures

- If a file fails to process: check the error output from the prepare script, troubleshoot, but **never skip it**
- If a subagent fails to read a file: retry with a fresh subagent, but **never skip it**
- If a file path is wrong (special characters, wrong casing): search for the correct path using `os.walk`, but **never skip it**
- **Every single output in `.tmp_prepared/` must be examined.** If something can't be examined, stop and report the failure explicitly — do not continue as if it was handled.

## Technical Notes

- **Shell safety**: Filenames may contain `$`, `%`, spaces, parentheses, apostrophes, commas. Always use Python for file operations, not shell commands.
- **Image size at dpi=100**: Standard US letter (8.5x11") renders to ~850x1100px. This is safely under Claude's ~2000px image processing limit.
- **Scanned vs. digital PDFs**: Many personal tax documents are scans (photos of paper). Even digital PDFs may have content (stamps, images, bundled forms) not captured by text extraction. Visual examination of every page avoids missing anything.
- **Package installs**: The prepare script only installs packages for file types that actually exist in the collection. No unnecessary dependencies.
