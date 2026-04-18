#!/usr/bin/env python3
"""
Track experimental runs in HACKLOG_EXPERIMENTS.md.

Each experiment: id (E1, E2, ...), title, status, script path, inputs,
result, duration, session date.

Usage:
  experiments.py add "title" --script PATH [--inputs "..."] [--notes "..."]
  experiments.py update <id> <status> [--result "..."] [--duration "..."]
  experiments.py list [--status STATUS] [--format json|markdown]
  experiments.py link <id> <session-date> [--note "..."]

Statuses: planned, running, complete, failed.

File layout parallels HACKLOG_HYPOTHESES.md with Active / Archived sections.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

STATUSES = {"planned", "running", "complete", "failed"}
FILE = "HACKLOG_EXPERIMENTS.md"

ENTRY_RE = re.compile(r"^### E(?P<id>\d+):\s*(?P<title>.*?)$", re.MULTILINE)


def today():
    return dt.date.today().isoformat()


def _find_bullet(body, name):
    m = re.search(rf"^- \*\*{re.escape(name)}\*\*:\s*(.*?)$", body, re.MULTILINE)
    return m.group(1).strip() if m else ""


def parse_file(path: Path):
    text = path.read_text() if path.exists() else ""
    active_m = re.search(r"^## Active\s*$", text, re.MULTILINE)
    archived_m = re.search(r"^## Archived\s*$", text, re.MULTILINE)
    entries = {}
    for m in ENTRY_RE.finditer(text):
        eid = int(m.group("id"))
        start = m.end()
        nxt = ENTRY_RE.search(text, start)
        nxt_sec = re.search(r"^## ", text[start:], re.MULTILINE)
        end = min([len(text)] +
                  ([nxt.start()] if nxt else []) +
                  ([start + nxt_sec.start()] if nxt_sec else []))
        body = text[start:end]
        section = "Active"
        if archived_m and m.start() > archived_m.start():
            section = "Archived"
        notes_lines = []
        nb = re.search(r"^- \*\*Notes\*\*:\s*\n((?:\s+-.*\n?)*)", body, re.MULTILINE)
        if nb:
            for line in nb.group(1).splitlines():
                line = line.strip()
                if line.startswith("-"):
                    notes_lines.append(line.lstrip("- ").strip())
        entries[eid] = {
            "id": eid,
            "title": m.group("title").strip(),
            "section": section,
            "script": _find_bullet(body, "Script"),
            "inputs": _find_bullet(body, "Inputs"),
            "status_line": _find_bullet(body, "Status"),
            "result": _find_bullet(body, "Result"),
            "duration": _find_bullet(body, "Duration"),
            "notes": notes_lines,
        }
    return entries, text


def render_entry(e):
    lines = [f"### E{e['id']}: {e['title']}"]
    lines.append(f"- **Status**: {e['status_line']}")
    if e["script"]:
        lines.append(f"- **Script**: {e['script']}")
    if e["inputs"]:
        lines.append(f"- **Inputs**: {e['inputs']}")
    if e["result"]:
        lines.append(f"- **Result**: {e['result']}")
    if e["duration"]:
        lines.append(f"- **Duration**: {e['duration']}")
    if e["notes"]:
        lines.append("- **Notes**:")
        for n in e["notes"]:
            lines.append(f"    - {n}")
    lines.append("")
    return "\n".join(lines)


def write_file(path, entries, preamble=None):
    if preamble is None:
        if path.exists():
            text = path.read_text()
            m = re.search(r"^## Active\s*$", text, re.MULTILINE)
            preamble = text[: m.start()] if m else text.rstrip() + "\n\n"
        else:
            preamble = ("# Hacklog Experiments\n\n"
                        "Structured records of experimental runs.\n\n---\n\n")
    active = sorted((e for e in entries.values() if e["section"] == "Active"),
                    key=lambda x: x["id"])
    archived = sorted((e for e in entries.values() if e["section"] == "Archived"),
                      key=lambda x: x["id"])
    parts = [preamble.rstrip(), "\n\n## Active\n\n"]
    for e in active:
        parts.append(render_entry(e))
        parts.append("\n")
    parts.append("\n## Archived\n\n")
    for e in archived:
        parts.append(render_entry(e))
        parts.append("\n")
    path.write_text("".join(parts).rstrip() + "\n")


def cmd_add(args):
    path = Path(args.file)
    entries, _ = parse_file(path)
    next_id = (max(entries) if entries else 0) + 1
    entries[next_id] = {
        "id": next_id,
        "title": args.title,
        "section": "Active",
        "script": args.script or "",
        "inputs": args.inputs or "",
        "status_line": f"planned  ({today()})",
        "result": "",
        "duration": "",
        "notes": [f"{today()}: {args.notes}"] if args.notes else [],
    }
    write_file(path, entries)
    print(f"Added E{next_id}: {args.title}")


def cmd_update(args):
    path = Path(args.file)
    entries, _ = parse_file(path)
    if args.id not in entries:
        sys.exit(f"error: E{args.id} not found.")
    if args.status not in STATUSES:
        sys.exit(f"error: status must be one of {sorted(STATUSES)}")
    e = entries[args.id]
    e["status_line"] = f"{args.status}  ({today()})"
    if args.result:
        e["result"] = args.result
    if args.duration:
        e["duration"] = args.duration
    if args.note:
        e["notes"].append(f"{today()}: {args.note}")
    write_file(path, entries)
    print(f"E{args.id} → {args.status}")


def cmd_link(args):
    path = Path(args.file)
    entries, _ = parse_file(path)
    if args.id not in entries:
        sys.exit(f"error: E{args.id} not found.")
    entries[args.id]["notes"].append(
        f"{args.session_date}: {args.note or '(see session)'}")
    write_file(path, entries)
    print(f"E{args.id}: +note ({args.session_date})")


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
                    "section": e["section"], "status": status,
                    "script": e["script"], "duration": e["duration"]})
    if args.format == "json":
        print(json.dumps(out, indent=2))
    else:
        for e in out:
            extra = f" [{e['duration']}]" if e["duration"] else ""
            print(f"- E{e['id']} [{e['section']}/{e['status']}]: "
                  f"{e['title']}{extra}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=FILE)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add"); a.add_argument("title")
    a.add_argument("--script", default="")
    a.add_argument("--inputs", default="")
    a.add_argument("--notes", default="")
    a.set_defaults(fn=cmd_add)

    u = sub.add_parser("update")
    u.add_argument("id", type=int); u.add_argument("status", choices=sorted(STATUSES))
    u.add_argument("--result", default=""); u.add_argument("--duration", default="")
    u.add_argument("--note", default="")
    u.set_defaults(fn=cmd_update)

    l = sub.add_parser("link")
    l.add_argument("id", type=int); l.add_argument("session_date")
    l.add_argument("--note", default="")
    l.set_defaults(fn=cmd_link)

    ls = sub.add_parser("list")
    ls.add_argument("--status", choices=sorted(STATUSES))
    ls.add_argument("--format", choices=["json", "markdown"], default="markdown")
    ls.set_defaults(fn=cmd_list)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
