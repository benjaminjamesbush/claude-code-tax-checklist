#!/usr/bin/env python3
"""
PreToolUse hook for the Read tool. Blocks reading skill scripts
(scan.py, prepare.py, cleanup.py) to avoid wasting context.
Just run them — don't read them first.
"""

import json
import sys

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "")

blocked = ("scan.py", "prepare.py", "cleanup.py")

if any(file_path.endswith(f"scripts/{name}") for name in blocked):
    print(
        "Do not read skill scripts - just run them. "
        "Reading scripts wastes context. See SKILL.md 'Context Management'.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
