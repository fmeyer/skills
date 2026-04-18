#!/usr/bin/env python3
"""
Track research hypotheses in HACKLOG_HYPOTHESES.md.

Usage:
  hypothesis.py add "hypothesis statement" [--title "short title"]
  hypothesis.py update <id> <status> [--note "..."]
  hypothesis.py link <id> <session-date> [--note "..."]
  hypothesis.py archive <id> [--reason "..."]
  hypothesis.py list [--status STATUS] [--format json|markdown]

Statuses (enforced): proposed, tested, confirmed, rejected, refined.

File format (parsed and written):
  Under "## Active" or "## Archived":

  ### H<id>: <title>
  - **Statement**: ...
  - **Status**: <status>  (YYYY-MM-DD)
  - **Evidence**:
    - YYYY-MM-DD: <note>
  - **Notes**: <free-form>

Each hypothesis is parsed/written atomically.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

STATUSES = {"proposed", "tested", "confirmed", "rejected", "refined"}
FILE = "HACKLOG_HYPOTHESES.md"


# -------- parsing --------

HYPOTHESIS_RE = re.compile(
    r"^### H(?P<id>\d+):\s*(?P<title>.*?)$",
    re.MULTILINE,
)


def parse_file(path: Path):
    """Return (hypotheses, preamble, active_idx, archived_idx).

    hypotheses: dict id -> {title, status, statement, evidence[], notes, section}
    """
    text = path.read_text() if path.exists() else ""
    # Locate section indexes
    active_m = re.search(r"^## Active\s*$", text, re.MULTILINE)
    archived_m = re.search(r"^## Archived\s*$", text, re.MULTILINE)

    hypotheses = {}
    for m in HYPOTHESIS_RE.finditer(text):
        hid = int(m.group("id"))
        title = m.group("title").strip()
        start = m.end()
        next_m = HYPOTHESIS_RE.search(text, start)
        # Also stop at next ##
        next_sec = re.search(r"^## ", text[start:], re.MULTILINE)
        end_candidates = [len(text)]
        if next_m:
            end_candidates.append(next_m.start())
        if next_sec:
            end_candidates.append(start + next_sec.start())
        end = min(end_candidates)
        body = text[start:end]

        # Determine section
        section = "Active"
        if archived_m and m.start() > archived_m.start():
            section = "Archived"

        statement = _find_bullet(body, "Statement")
        status_line = _find_bullet(body, "Status")
        notes = _find_bullet(body, "Notes")

        # Evidence is a multi-line bulleted sub-list
        evidence = []
        ev_block_m = re.search(r"^- \*\*Evidence\*\*:\s*\n((?:\s+-.*\n?)*)", body, re.MULTILINE)
        if ev_block_m:
            for line in ev_block_m.group(1).splitlines():
                line = line.strip()
                if line.startswith("-"):
                    evidence.append(line.lstrip("- ").strip())

        hypotheses[hid] = {
            "id": hid,
            "title": title,
            "section": section,
            "statement": statement,
            "status_line": status_line,
            "evidence": evidence,
            "notes": notes,
        }
    return hypotheses, text


def _find_bullet(body: str, name: str):
    m = re.search(rf"^- \*\*{re.escape(name)}\*\*:\s*(.*?)$",
                  body, re.MULTILINE)
    return m.group(1).strip() if m else ""


def render_hypothesis(h):
    lines = [f"### H{h['id']}: {h['title']}"]
    lines.append(f"- **Statement**: {h['statement']}")
    lines.append(f"- **Status**: {h['status_line']}")
    if h["evidence"]:
        lines.append("- **Evidence**:")
        for e in h["evidence"]:
            lines.append(f"    - {e}")
    if h["notes"]:
        lines.append(f"- **Notes**: {h['notes']}")
    lines.append("")
    return "\n".join(lines)


def write_file(path: Path, hypotheses: dict, preamble: str = None):
    """Rewrite HACKLOG_HYPOTHESES.md with hypotheses reorganised by section."""
    # Keep preamble from existing file, or build minimal one
    if preamble is None:
        if path.exists():
            text = path.read_text()
            m = re.search(r"^## Active\s*$", text, re.MULTILINE)
            if m:
                preamble = text[: m.start()]
            else:
                preamble = text.rstrip() + "\n\n"
        else:
            preamble = (
                "# Hacklog Hypotheses\n\n"
                "Tracked research hypotheses with status, evidence, and "
                "cross-references.\n\n---\n\n"
            )

    active = [h for h in hypotheses.values() if h["section"] == "Active"]
    archived = [h for h in hypotheses.values() if h["section"] == "Archived"]
    active.sort(key=lambda x: x["id"])
    archived.sort(key=lambda x: x["id"])

    parts = [preamble.rstrip(), "\n\n## Active\n\n"]
    for h in active:
        parts.append(render_hypothesis(h))
        parts.append("\n")
    parts.append("\n## Archived\n\n")
    for h in archived:
        parts.append(render_hypothesis(h))
        parts.append("\n")
    path.write_text("".join(parts).rstrip() + "\n")


def today():
    return dt.date.today().isoformat()


# -------- commands --------

def cmd_add(args):
    path = Path(args.file)
    hypotheses, _ = parse_file(path)
    next_id = (max(hypotheses) if hypotheses else 0) + 1
    new = {
        "id": next_id,
        "title": args.title or args.statement[:60],
        "section": "Active",
        "statement": args.statement,
        "status_line": f"proposed  ({today()})",
        "evidence": [],
        "notes": "",
    }
    hypotheses[next_id] = new
    write_file(path, hypotheses)
    print(f"Added H{next_id}: {new['title']}")


def cmd_update(args):
    path = Path(args.file)
    hypotheses, _ = parse_file(path)
    if args.id not in hypotheses:
        sys.exit(f"error: H{args.id} not found.")
    if args.status not in STATUSES:
        sys.exit(f"error: status must be one of {sorted(STATUSES)}")
    h = hypotheses[args.id]
    h["status_line"] = f"{args.status}  ({today()})"
    if args.note:
        h["evidence"].append(f"{today()}: {args.note}")
    write_file(path, hypotheses)
    print(f"H{args.id} → {args.status}")


def cmd_link(args):
    path = Path(args.file)
    hypotheses, _ = parse_file(path)
    if args.id not in hypotheses:
        sys.exit(f"error: H{args.id} not found.")
    h = hypotheses[args.id]
    stamp = args.session_date
    if args.note:
        h["evidence"].append(f"{stamp}: {args.note}")
    else:
        h["evidence"].append(f"{stamp}: (see session)")
    write_file(path, hypotheses)
    print(f"H{args.id}: +evidence ({stamp})")


def cmd_archive(args):
    path = Path(args.file)
    hypotheses, _ = parse_file(path)
    if args.id not in hypotheses:
        sys.exit(f"error: H{args.id} not found.")
    h = hypotheses[args.id]
    h["section"] = "Archived"
    if args.reason:
        h["evidence"].append(f"{today()}: archived — {args.reason}")
    write_file(path, hypotheses)
    print(f"H{args.id} archived")


def cmd_list(args):
    path = Path(args.file)
    if not path.exists():
        sys.exit(f"error: {path} does not exist.")
    hypotheses, _ = parse_file(path)
    filtered = []
    for h in hypotheses.values():
        current_status = h["status_line"].split()[0] if h["status_line"] else "?"
        if args.status and current_status != args.status:
            continue
        filtered.append({
            "id": h["id"],
            "title": h["title"],
            "section": h["section"],
            "status": current_status,
            "evidence_count": len(h["evidence"]),
        })
    filtered.sort(key=lambda x: x["id"])
    if args.format == "json":
        print(json.dumps(filtered, indent=2))
    else:
        for h in filtered:
            print(f"- H{h['id']} [{h['section']}/{h['status']}]: {h['title']} "
                  f"({h['evidence_count']} evidence)")


# -------- CLI --------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=FILE)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("statement")
    a.add_argument("--title", default="")
    a.set_defaults(fn=cmd_add)

    u = sub.add_parser("update")
    u.add_argument("id", type=int)
    u.add_argument("status", choices=sorted(STATUSES))
    u.add_argument("--note", default="")
    u.set_defaults(fn=cmd_update)

    l = sub.add_parser("link")
    l.add_argument("id", type=int)
    l.add_argument("session_date")
    l.add_argument("--note", default="")
    l.set_defaults(fn=cmd_link)

    ar = sub.add_parser("archive")
    ar.add_argument("id", type=int)
    ar.add_argument("--reason", default="")
    ar.set_defaults(fn=cmd_archive)

    ls = sub.add_parser("list")
    ls.add_argument("--status", choices=sorted(STATUSES))
    ls.add_argument("--format", choices=["json", "markdown"], default="markdown")
    ls.set_defaults(fn=cmd_list)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
