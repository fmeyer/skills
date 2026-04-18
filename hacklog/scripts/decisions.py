#!/usr/bin/env python3
"""
Track methodological decisions in HACKLOG_DECISIONS.md.

Each decision: id (D1, D2, ...), title, context, decision, rationale,
alternatives considered, status (open / decided / revisited / reversed).

Usage:
  decisions.py add "title" --context "..." --decision "..." \\
                [--rationale "..."] [--alternatives "..."]
  decisions.py update <id> <status> [--note "..."]
  decisions.py list [--status STATUS] [--format json|markdown]

Statuses: open, decided, revisited, reversed.

Differs from hypotheses: a decision is a methodological choice (e.g.,
"use L(G) not A(G)"), not a claim being empirically tested.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

STATUSES = {"open", "decided", "revisited", "reversed"}
FILE = "HACKLOG_DECISIONS.md"
ENTRY_RE = re.compile(r"^### D(?P<id>\d+):\s*(?P<title>.*?)$", re.MULTILINE)


def today():
    return dt.date.today().isoformat()


def _find_bullet(body, name):
    m = re.search(rf"^- \*\*{re.escape(name)}\*\*:\s*(.*?)$", body, re.MULTILINE)
    return m.group(1).strip() if m else ""


def parse_file(path: Path):
    text = path.read_text() if path.exists() else ""
    entries = {}
    for m in ENTRY_RE.finditer(text):
        did = int(m.group("id"))
        start = m.end()
        nxt = ENTRY_RE.search(text, start)
        nxt_sec = re.search(r"^## ", text[start:], re.MULTILINE)
        end = min([len(text)] +
                  ([nxt.start()] if nxt else []) +
                  ([start + nxt_sec.start()] if nxt_sec else []))
        body = text[start:end]
        notes_lines = []
        nb = re.search(r"^- \*\*History\*\*:\s*\n((?:\s+-.*\n?)*)", body, re.MULTILINE)
        if nb:
            for line in nb.group(1).splitlines():
                line = line.strip()
                if line.startswith("-"):
                    notes_lines.append(line.lstrip("- ").strip())
        entries[did] = {
            "id": did,
            "title": m.group("title").strip(),
            "context": _find_bullet(body, "Context"),
            "decision": _find_bullet(body, "Decision"),
            "rationale": _find_bullet(body, "Rationale"),
            "alternatives": _find_bullet(body, "Alternatives"),
            "status_line": _find_bullet(body, "Status"),
            "history": notes_lines,
        }
    return entries, text


def render_entry(e):
    lines = [f"### D{e['id']}: {e['title']}"]
    lines.append(f"- **Status**: {e['status_line']}")
    if e["context"]:
        lines.append(f"- **Context**: {e['context']}")
    if e["decision"]:
        lines.append(f"- **Decision**: {e['decision']}")
    if e["rationale"]:
        lines.append(f"- **Rationale**: {e['rationale']}")
    if e["alternatives"]:
        lines.append(f"- **Alternatives**: {e['alternatives']}")
    if e["history"]:
        lines.append("- **History**:")
        for n in e["history"]:
            lines.append(f"    - {n}")
    lines.append("")
    return "\n".join(lines)


def write_file(path, entries):
    if path.exists():
        text = path.read_text()
        m = re.search(r"^## Entries\s*$", text, re.MULTILINE)
        preamble = text[: m.start()] if m else text.rstrip() + "\n\n"
    else:
        preamble = ("# Hacklog Decisions\n\n"
                    "Methodological choices with rationale and "
                    "alternatives considered.\n\n---\n\n")
    parts = [preamble.rstrip(), "\n\n## Entries\n\n"]
    for e in sorted(entries.values(), key=lambda x: x["id"]):
        parts.append(render_entry(e))
        parts.append("\n")
    path.write_text("".join(parts).rstrip() + "\n")


def cmd_add(args):
    path = Path(args.file)
    entries, _ = parse_file(path)
    next_id = (max(entries) if entries else 0) + 1
    entries[next_id] = {
        "id": next_id, "title": args.title,
        "context": args.context, "decision": args.decision,
        "rationale": args.rationale, "alternatives": args.alternatives,
        "status_line": f"decided  ({today()})" if args.decision else f"open  ({today()})",
        "history": [f"{today()}: created"],
    }
    write_file(path, entries)
    print(f"Added D{next_id}: {args.title}")


def cmd_update(args):
    path = Path(args.file)
    entries, _ = parse_file(path)
    if args.id not in entries:
        sys.exit(f"error: D{args.id} not found.")
    if args.status not in STATUSES:
        sys.exit(f"error: status must be one of {sorted(STATUSES)}")
    e = entries[args.id]
    e["status_line"] = f"{args.status}  ({today()})"
    if args.note:
        e["history"].append(f"{today()}: {args.note}")
    else:
        e["history"].append(f"{today()}: status → {args.status}")
    write_file(path, entries)
    print(f"D{args.id} → {args.status}")


def cmd_list(args):
    path = Path(args.file)
    if not path.exists():
        sys.exit(f"error: {path} does not exist.")
    entries, _ = parse_file(path)
    out = []
    for e in sorted(entries.values(), key=lambda x: x["id"]):
        status = e["status_line"].split()[0] if e["status_line"] else "?"
        if args.status and status != args.status:
            continue
        out.append({"id": e["id"], "title": e["title"],
                    "status": status,
                    "decision": e["decision"],
                    "history_len": len(e["history"])})
    if args.format == "json":
        print(json.dumps(out, indent=2))
    else:
        for e in out:
            dec = f" — {e['decision']}" if e['decision'] else ""
            print(f"- D{e['id']} [{e['status']}]: {e['title']}{dec}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=FILE)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("--context", default="")
    a.add_argument("--decision", default="")
    a.add_argument("--rationale", default="")
    a.add_argument("--alternatives", default="")
    a.set_defaults(fn=cmd_add)

    u = sub.add_parser("update")
    u.add_argument("id", type=int); u.add_argument("status", choices=sorted(STATUSES))
    u.add_argument("--note", default="")
    u.set_defaults(fn=cmd_update)

    ls = sub.add_parser("list")
    ls.add_argument("--status", choices=sorted(STATUSES))
    ls.add_argument("--format", choices=["json", "markdown"], default="markdown")
    ls.set_defaults(fn=cmd_list)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
