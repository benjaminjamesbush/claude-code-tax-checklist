# claude-code-tax-checklist

A Claude Code skill that scans your historical tax documents and generates a comprehensive checklist of everything you need to gather for your tax preparer.

## What It Does

If you've accumulated years of tax documents in folders, this skill will:

1. **Scan** your tax documents directory to understand how it's organized and what file types are present
2. **Examine** every page of every document — filenames can be misleading (a file named `mortgage 1098.pdf` may contain a 1099-INT on page 2)
3. **Deduplicate** across years to find every unique document type you've historically received
4. **Generate** a Markdown checklist organized by category with year ranges, so you know exactly what to expect and gather

## Why

Every year you need to collect the same tax documents — 1099s from brokerages, 1098 from your mortgage company, K-1s from partnerships, etc. But which ones? If you have years of historical records, the answer is already in your files. This skill reads them all and tells you what to look for.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and configured
- Python 3.7+
- PyMuPDF (auto-installed by the skill if missing)

## Setup

### 1. Gather Your Tax Documents

Put your historical tax documents in a single directory. The skill will do an exploratory scan to figure out how things are organized and what file types are present (PDFs, images, etc.). Any folder structure works — for example:

```
tax-documents/
  2023/
    robinhood 1099.pdf
    mortgage 1098.pdf
  2024/
    bank of america.pdf
    scanned docs.pdf
  misc/
    old receipts.pdf
```

Files can have any name — the skill examines every page of every file regardless of filename.

### 2. Clone This Repo and Add Your Documents

```
git clone https://github.com/your-username/claude-code-tax-checklist.git
cd claude-code-tax-checklist
```

Copy or move your tax documents into this directory. Year folders, flat files, any structure works.

### 3. Run Claude Code

```
cd claude-code-tax-checklist
claude
```

Then run:

```
/tax-checklist
```

The skill will handle the rest.

## What to Expect

- **Time**: Depends on total page count across all PDFs. A typical run with ~150 files takes 15-30 minutes.
- **Cost**: The skill uses haiku-tier subagents for image reading to minimize cost. Most of the token usage is in the visual examination step.
- **Output**: A single Markdown file with checkbox items, organized by category.

## Example Output

```markdown
# 2025 Tax Document Checklist

## Investments & Brokerage

- [ ] **Schwab — 1099 Composite** (Schwab One account)
  Includes 1099-DIV, 1099-INT, 1099-OID, 1099-B.
  *Seen: 2014–2015, 2021, 2023–2024*

- [ ] **Robinhood — Consolidated 1099** (Securities, Crypto & Derivatives)
  *Seen: 2016–2024*

## Banking — Interest Income

- [ ] **Bank of America — 1099-INT** (checking & savings)
  *Seen: 2016, 2019, 2022–2024*

## Mortgage & Property

- [ ] **Carrington Mortgage — 1098** (Mortgage Interest Statement)
  *Seen: 2019–2024*

...
```

## How It Works (Technical)

The skill follows a multi-step process:

1. **Exploratory scan** — Runs `scripts/scan.py` to survey the directory structure, file types, and naming conventions
2. **Rendering** — Runs `scripts/render.py` to render every page of every PDF to a small PNG (850x1100px at 100 DPI). Text extraction is not used — even digital PDFs may have bundled forms or content not captured by text layers.
3. **Visual examination** — Isolated subagents visually read each PNG and identify the form type, institution, account holder, and tax year. Every page of every file is examined — filenames are not trusted.
4. **Compilation** — Merges all findings, deduplicates across years, and writes the categorized checklist
5. **Cleanup** — Runs `scripts/cleanup.py` to delete temporary PNG files

The visual examination step uses subagents (separate Claude instances) to avoid accumulating images in the main conversation context, which would cause memory issues.

## Project Structure

```
claude-code-tax-checklist/
├── CLAUDE.md                              # Minimal project config
├── README.md                              # This file
└── .claude/
    └── skills/
        └── tax-checklist/
            ├── SKILL.md                   # Skill definition and process instructions
            └── scripts/
                ├── scan.py                # Step 1: Exploratory directory scan
                ├── render.py              # Step 2: Render PDFs to PNGs via PyMuPDF
                └── cleanup.py             # Step 5: Delete temporary PNGs
```

## Limitations

- **Scanned document quality**: Very low-quality scans may be difficult to read. The skill will flag these rather than skip them.
- **Multi-document PDFs**: Some PDFs bundle multiple forms (e.g., a 1098 and 1099-INT in one file). The skill examines every page to catch these.
- **Not tax advice**: This tool identifies documents — it doesn't interpret tax implications or tell you what to file.

## License

MIT
