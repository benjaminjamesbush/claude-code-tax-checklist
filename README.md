# claude-code-tax-checklist

A Claude Code agent that scans your historical tax documents and generates a comprehensive checklist of everything you need to gather for your tax preparer.

## What It Does

If you've accumulated years of tax documents in folders, this agent will:

1. **Scan** every PDF across all your year folders
2. **Identify** the form type, institution, and account for each document — including opening and visually reading scanned PDFs that have ambiguous filenames
3. **Deduplicate** across years to find every unique document type you've historically received
4. **Generate** a Markdown checklist organized by category with year ranges, so you know exactly what to expect and gather

## Why

Every year you need to collect the same tax documents — 1099s from brokerages, 1098 from your mortgage company, K-1s from partnerships, etc. But which ones? If you have years of historical records, the answer is already in your files. This agent reads them all and tells you what to look for.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and configured
- Python 3.7+
- PyMuPDF for PDF rendering:
  ```
  pip install pymupdf
  ```

## Setup

### 1. Organize Your Tax Documents

Put your historical tax documents in a directory with year-based subfolders:

```
tax-documents/
  2018/
    robinhood 1099.pdf
    mortgage 1098.pdf
    ...
  2019/
    estimated payments/
      fed-q1.pdf
      ca-q1.pdf
    bank of america.pdf
    scanned docs.pdf
    ...
  2020/
    ...
  2024/
    ...
```

Subfolder names should be the tax year (e.g., `2020`, `2021`). Files within can have any name — the agent handles both clearly-named files and ambiguous ones.

### 2. Clone This Repo

Clone or copy this repo into your tax documents directory (or anywhere convenient):

```
cd /path/to/your/tax-documents
git clone https://github.com/your-username/claude-code-tax-checklist.git
```

Or just copy the `CLAUDE.md` file into your tax documents root directory.

### 3. Run Claude Code

From your tax documents directory:

```
cd /path/to/your/tax-documents
claude
```

Then ask:

> Build me a tax document checklist for [YEAR] based on all the PDFs in this directory.

The agent will follow the instructions in `CLAUDE.md` automatically.

## What to Expect

- **Time**: Depends on how many ambiguous PDFs need visual examination. A typical run with ~40 ambiguous files takes 15-30 minutes.
- **Cost**: The agent uses haiku-tier subagents for image reading to minimize cost. Most of the token usage is in the visual examination step.
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

The agent follows a multi-step process described in `CLAUDE.md`:

1. **Filename scan** — Catalogs all PDFs and classifies them as "clear" (form type obvious from filename) or "ambiguous"
2. **Text extraction** — Tries extracting text from ambiguous PDFs (works for digitally-generated documents)
3. **Visual examination** — For scanned PDFs with no extractable text, renders each page to a small PNG (850x1100px at 100 DPI) and uses isolated subagents to visually identify each page's contents
4. **Compilation** — Merges all findings, deduplicates across years, and writes the categorized checklist

The visual examination step uses subagents (separate Claude instances) to avoid accumulating images in the main conversation context, which would cause memory issues.

## Limitations

- **Scanned document quality**: Very low-quality scans may be difficult to read. The agent will flag these rather than skip them.
- **Multi-document PDFs**: Some PDFs bundle multiple forms (e.g., a 1098 and 1099-INT in one file). The agent examines every page to catch these.
- **Not tax advice**: This tool identifies documents — it doesn't interpret tax implications or tell you what to file.

## License

MIT
