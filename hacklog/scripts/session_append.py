#!/usr/bin/env python3
"""
Append a new dated session block to HACKLOG.md.

Usage:
  session_append.py [--title "session title"] [--file PATH]

Behavior:
  - If HACKLOG.md already has a section for today's date, create a
    sub-session (e.g., "Session 2026-04-18 (afternoon)").
  - Insertion point is before a "## Bottom line" section if present,
    otherwise at EOF.
  - Non-destructive: writes only the template; the caller (Claude) fills
    in each subsection based on conversation context.
"""
from __future__ import annotations
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

TEMPLATE = """## Session {date}{suffix}: {title}

### Context
<!-- What the session starts from. Current state of the project at the
     beginning of the session. -->

### Experiments / computations
<!-- Each experiment as its own subsection. Prefer tables for numeric
     findings. -->

### Key findings
<!-- Bulleted structural takeaways. -->

### Hypothesis updates
<!-- Reference hypothesis ids (H1, H2, ...) whose status changed this
     session: proposed / tested / confirmed / rejected / refined.
     Sync to HACKLOG_HYPOTHESES.md with scripts/hypothesis.py. -->

### Files produced / modified
<!-- Scripts and data files touched in this session. -->

### Open questions / next steps
<!-- What's unresolved; what to try next. -->

---

"""


def today_iso():
    return dt.date.today().isoformat()


def count_today_sessions(text: str, today: str) -> int:
    pattern = re.compile(
        rf"^## Session {re.escape(today)}(?:\s+\([^)]+\))?:",
        re.MULTILINE,
    )
    return len(pattern.findall(text))


def suffix_for_nth_session(n: int) -> str:
    suffixes = ["", " (afternoon)", " (evening)", " (late night)"]
    if n < len(suffixes):
        return suffixes[n]
    return f" (session {n+1})"


def find_insertion_point(text: str) -> int:
    m = re.search(r"^## Bottom line", text, re.MULTILINE)
    if m:
        return m.start()
    return len(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="(untitled)")
    ap.add_argument("--file", default="HACKLOG.md")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        sys.exit(
            f"error: {path} does not exist. Run '/hacklog init' first "
            "or point at an existing file with --file."
        )

    text = path.read_text()
    today = today_iso()
    n_existing = count_today_sessions(text, today)
    suffix = suffix_for_nth_session(n_existing)
    block = TEMPLATE.format(date=today, suffix=suffix, title=args.title)

    insertion = find_insertion_point(text)
    new_text = text[:insertion] + block + text[insertion:]
    path.write_text(new_text)
    print(f"Inserted session block at offset {insertion} in {path}.")
    print(f"Date: {today}{suffix}   Title: {args.title}")


if __name__ == "__main__":
    main()
