# claude-code-tax-checklist

A Claude Code skill that scans your historical tax documents and generates a comprehensive checklist of everything you need to gather for tax season.

## What It Does

If you've accumulated years of tax documents in folders, this skill will:

1. **Scan** your tax documents directory to understand how it's organized and what file types are present
2. **Examine** every page of every document — filenames can be misleading (a file named `mortgage 1098.pdf` may contain a 1099-INT on page 2)
3. **Deduplicate** across years to find every unique document type you've historically received
4. **Generate** a Markdown checklist organized by category with year ranges, so you know exactly what to expect and gather

## Why

Every year you need to collect the same tax documents — 1099s from brokerages, 1098 from your mortgage company, K-1s from partnerships, etc. But which ones? If you have years of historical records, the answer is already in your files. This skill reads them all and tells you what to look for.

## Getting Started

### 1. Install Claude Code

You'll need a [Claude subscription](https://claude.com/pricing) or [Anthropic Console](https://console.anthropic.com/) account. Full install instructions at [code.claude.com/docs](https://code.claude.com/docs), reproduced here for convenience.

**macOS, Linux, WSL:**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell:**

> **Windows requires [Git for Windows](https://git-scm.com/downloads/win).** Install it first if you don't have it.

```powershell
irm https://claude.ai/install.ps1 | iex
```

### 2. Clone This Repo

```
git clone https://github.com/benjaminjamesbush/claude-code-tax-checklist.git
```

### 3. Add Your Tax Documents

**Copy** (not move) your tax documents into the `tax-documents/` folder inside the cloned directory. Always keep your originals safe elsewhere. Year folders, flat files, any structure works.

### 4. Launch Claude Code

```
cd claude-code-tax-checklist
claude --dangerously-skip-permissions
```

The `--dangerously-skip-permissions` flag is recommended so the skill can run without prompting for approval at each step.

Now run `/tax-checklist` and the skill will handle the rest.

All other dependencies (Python, PyMuPDF, Pillow, etc.) are auto-installed as needed.

## Supported File Types

| Format | Extensions | How it's processed |
|---|---|---|
| PDFs | .pdf | Rendered page-by-page to PNG |
| Images | .jpg .jpeg .png .gif .tiff .tif .bmp .webp .avif .heic .heif | Converted to PNG, resized if needed |
| Text | .txt .csv .md .json .log | Copied as text |
| HTML/web | .html .htm .mhtml .mht .wbl | Copied as text |
| Rich text | .rtf | Copied as text |
| Spreadsheets | .xlsx .xls | Converted to CSV text |
| Word docs | .docx .doc | Text extracted |
| Archives | .zip | Extracted, then contents processed |

## What to Expect

- **Time**: Depends on total file and page count. A typical run with ~150 files takes 15-30 minutes.
- **Cost**: The skill uses haiku-tier subagents for file examination to minimize cost.
- **Output**: A single Markdown file with checkbox items, organized by category.

## Example Output

```markdown
# Tax Document Checklist

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
2. **Preparation** — Runs `scripts/prepare.py` to convert all files into subagent-readable formats: PDFs and images become PNGs, everything else becomes text. Only installs packages needed for the file types found.
3. **Examination** — Isolated subagents read each prepared file (one agent per file) and identify the form type, institution, account holder, and tax year. Filenames are not trusted.
4. **Compilation** — Merges all findings, deduplicates across years, and writes the categorized checklist

Prepared files are kept in `.tmp_prepared/` with a `manifest.txt` mapping each output back to its source, so follow-up questions can reference specific documents.

## Project Structure

```
claude-code-tax-checklist/
├── CLAUDE.md                              # Project config
├── README.md                              # This file
├── .gitignore                             # Ignores tax-documents/ and temp dirs
├── tax-documents/                         # Your tax documents go here (any structure)
└── .claude/
    └── skills/
        └── tax-checklist/
            ├── SKILL.md                   # Skill definition and process instructions
            └── scripts/
                ├── scan.py                # Step 1: Exploratory directory scan
                ├── prepare.py             # Step 2: Convert all files for examination
                └── cleanup.py             # Manual cleanup (only when user requests)
```

## Limitations

- **Scanned document quality**: Very low-quality scans may be difficult to read. Results depend on what the AI can make out.
- **Not tax advice**: This tool identifies documents — it doesn't interpret tax implications or tell you what to file.

## License

MIT
