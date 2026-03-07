#!/usr/bin/env python3
"""
PreToolUse hook for the Task tool. Ensures examination subagents follow
the one-file-per-agent rule from SKILL.md:
  - Must reference exactly one file from .tmp_prepared/
  - Must not reference raw PDFs or files from tax-documents/ directly

Only checks prompts that look like document examination tasks.
Non-examination subagents pass through unchecked.
"""

import json
import re
import sys

data = json.load(sys.stdin)
prompt = data.get("tool_input", {}).get("prompt", "")

if not prompt:
    sys.exit(0)

# Gate: only check prompts that look like document examination tasks
exam_keywords = re.compile(
    r"form.?type|document.?type|institution|tax.?year|1099|tax.?relevant"
    r"|identify.*page|examine.*page|scanned.*document",
    re.IGNORECASE,
)
if not exam_keywords.search(prompt):
    sys.exit(0)

# Rule 1: No raw PDF references
pdfs = re.findall(r"\S+\.pdf\b", prompt, re.IGNORECASE)
if pdfs:
    print(
        "Do not send raw PDF files to examination subagents. "
        "All files must be pre-processed through prepare.py first. "
        "Use the prepared files in .tmp_prepared/ instead.",
        file=sys.stderr,
    )
    sys.exit(2)

# Rule 2: No direct tax-documents/ references (bypassing .tmp_prepared/)
direct = [
    m
    for m in re.findall(r"tax-documents/\S+", prompt)
    if ".tmp_prepared/" not in m
]
if direct:
    print(
        "Do not read files directly from tax-documents/. "
        "Use the prepared single-page files in .tmp_prepared/ instead.",
        file=sys.stderr,
    )
    sys.exit(2)

# Rule 3: Count distinct .tmp_prepared/ file references
files = set(re.findall(r"\.tmp_prepared/[\w._-]+\.(?:png|txt)", prompt))
if len(files) > 1:
    print(
        f"Each examination subagent must examine exactly ONE file from "
        f".tmp_prepared/. You sent {len(files)} files. Launch one subagent "
        f"per file with 3 in parallel. See 'Why One Subagent Per Page' in "
        f"SKILL.md.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
