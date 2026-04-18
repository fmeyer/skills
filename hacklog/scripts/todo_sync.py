#!/usr/bin/env python3
"""
Sync HACKLOG_TODO.md sections: move items between Done / Pending / Open questions.

Usage:
  todo_sync.py [--done "item"]... [--pending "item"]... [--open "question"]... [--file PATH]

Conventions:
  HACKLOG_TODO.md should have sections like:
    ## Done
    - [x] ...
    ## Pending
    - [ ] ...
    ## Open questions
    - <question>

Behavior:
  --done "<item>"    Append to Done section with [x] checkbox.
  --pending "<item>" Append to Pending section with [ ] checkbox.
  --open "<item>"    Append to Open questions section (no checkbox).

If the section doesn't exist, this creates it at EOF.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path


def ensure_section(text: str, header: str) -> str:
    """Ensure '## <header>' exists as a line; append if missing."""
    if re.search(rf"^## {re.escape(header)}\b", text, re.MULTILINE):
        return text
    if not text.endswith("\n"):
        text += "\n"
    return text + f"\n## {header}\n\n"


def append_to_section(text: str, header: str, line: str) -> str:
    """Insert `line` at the end of the section '## {header}'.

    If there are trailing blank lines or the next '##' header follows,
    place the new line immediately before them.
    """
    pattern = re.compile(
        rf"(^## {re.escape(header)}\n[\s\S]*?)(?=^## |\Z)",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        # Section missing; add it and recurse
        text = ensure_section(text, header)
        return append_to_section(text, header, line)
    section = m.group(1).rstrip("\n")
    new_section = section + "\n" + line + "\n"
    return text[: m.start()] + new_section + "\n" + text[m.end():]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--done", action="append", default=[], help="Item to mark as done.")
    ap.add_argument("--pending", action="append", default=[], help="Pending item.")
    ap.add_argument("--open", action="append", default=[], dest="open_q",
                    help="Open question.")
    ap.add_argument("--file", default="HACKLOG_TODO.md")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        # Bootstrap a blank HACKLOG_TODO.md
        path.write_text("# Hacklog TODO\n\n## Pending\n\n## Done\n\n## Open questions\n\n")

    text = path.read_text()

    for item in args.done:
        text = append_to_section(text, "Done", f"- [x] {item}")
    for item in args.pending:
        text = append_to_section(text, "Pending", f"- [ ] {item}")
    for item in args.open_q:
        text = append_to_section(text, "Open questions", f"- {item}")

    path.write_text(text)
    total = len(args.done) + len(args.pending) + len(args.open_q)
    print(f"Updated {path}: +{len(args.done)} done, "
          f"+{len(args.pending)} pending, +{len(args.open_q)} open.")


if __name__ == "__main__":
    main()
