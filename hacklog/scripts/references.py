#!/usr/bin/env python3
"""
Track bibliographic references in HACKLOG_REFS.md.

Each reference: id (R1, R2, ...), citation key, authors, title, year,
venue, url, arxiv id, notes, linked sessions.

Usage:
  references.py add --authors "..." --title "..." --year YYYY \\
                    [--venue "..."] [--url "..."] [--arxiv "2508.05871"] \\
                    [--key "lepovic2010"] [--note "..."]
  references.py update <id> [--...field "..."]
  references.py link <id> <session-date> [--note "..."]
  references.py list [--year YYYY] [--format json|markdown]
  references.py bibtex [--out FILE]    # emit BibTeX file from all refs

Citation keys: if --key not provided, auto-generated as firstauthor+year
(e.g. "lepovic2010", "cioaba2025").
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

FILE = "HACKLOG_REFS.md"
ENTRY_RE = re.compile(r"^### R(?P<id>\d+):\s*(?P<key>\S+)\s*$", re.MULTILINE)


def _find_bullet(body, name):
    m = re.search(rf"^- \*\*{re.escape(name)}\*\*:\s*(.*?)$", body, re.MULTILINE)
    return m.group(1).strip() if m else ""


def today():
    return dt.date.today().isoformat()


def parse_file(path: Path):
    text = path.read_text() if path.exists() else ""
    entries = {}
    for m in ENTRY_RE.finditer(text):
        rid = int(m.group("id"))
        start = m.end()
        nxt = ENTRY_RE.search(text, start)
        nxt_sec = re.search(r"^## ", text[start:], re.MULTILINE)
        end = min([len(text)] +
                  ([nxt.start()] if nxt else []) +
                  ([start + nxt_sec.start()] if nxt_sec else []))
        body = text[start:end]
        notes_lines = []
        nb = re.search(r"^- \*\*Notes\*\*:\s*\n((?:\s+-.*\n?)*)", body, re.MULTILINE)
        if nb:
            for line in nb.group(1).splitlines():
                line = line.strip()
                if line.startswith("-"):
                    notes_lines.append(line.lstrip("- ").strip())
        entries[rid] = {
            "id": rid,
            "key": m.group("key").strip(),
            "authors": _find_bullet(body, "Authors"),
            "title": _find_bullet(body, "Title"),
            "year": _find_bullet(body, "Year"),
            "venue": _find_bullet(body, "Venue"),
            "url": _find_bullet(body, "URL"),
            "arxiv": _find_bullet(body, "arXiv"),
            "notes": notes_lines,
        }
    return entries, text


def render_entry(e):
    lines = [f"### R{e['id']}: {e['key']}"]
    if e["authors"]:
        lines.append(f"- **Authors**: {e['authors']}")
    if e["title"]:
        lines.append(f"- **Title**: {e['title']}")
    if e["year"]:
        lines.append(f"- **Year**: {e['year']}")
    if e["venue"]:
        lines.append(f"- **Venue**: {e['venue']}")
    if e["url"]:
        lines.append(f"- **URL**: {e['url']}")
    if e["arxiv"]:
        lines.append(f"- **arXiv**: {e['arxiv']}")
    if e["notes"]:
        lines.append("- **Notes**:")
        for n in e["notes"]:
            lines.append(f"    - {n}")
    lines.append("")
    return "\n".join(lines)


def write_file(path, entries):
    if path.exists():
        text = path.read_text()
        m = re.search(r"^## Entries\s*$", text, re.MULTILINE)
        preamble = text[: m.start()] if m else text.rstrip() + "\n\n"
    else:
        preamble = ("# Hacklog References\n\n"
                    "Bibliography accumulated across the project.\n\n---\n\n")
    parts = [preamble.rstrip(), "\n\n## Entries\n\n"]
    for e in sorted(entries.values(), key=lambda x: x["id"]):
        parts.append(render_entry(e))
        parts.append("\n")
    path.write_text("".join(parts).rstrip() + "\n")


def auto_key(authors, year):
    if not authors:
        return f"ref{year or 'xxxx'}"
    first = re.split(r"[,\s]", authors.strip())[0].lower()
    first = re.sub(r"[^a-z]", "", first) or "ref"
    return f"{first}{year or ''}"


def cmd_add(args):
    path = Path(args.file)
    entries, _ = parse_file(path)
    next_id = (max(entries) if entries else 0) + 1
    key = args.key or auto_key(args.authors, args.year)
    entries[next_id] = {
        "id": next_id, "key": key,
        "authors": args.authors, "title": args.title, "year": args.year,
        "venue": args.venue, "url": args.url, "arxiv": args.arxiv,
        "notes": [f"{today()}: {args.note}"] if args.note else [],
    }
    write_file(path, entries)
    print(f"Added R{next_id} ({key}): {args.title}")


def cmd_update(args):
    path = Path(args.file)
    entries, _ = parse_file(path)
    if args.id not in entries:
        sys.exit(f"error: R{args.id} not found.")
    e = entries[args.id]
    for field in ("authors", "title", "year", "venue", "url", "arxiv", "key"):
        v = getattr(args, field, None)
        if v:
            e[field] = v
    if args.note:
        e["notes"].append(f"{today()}: {args.note}")
    write_file(path, entries)
    print(f"Updated R{args.id}")


def cmd_link(args):
    path = Path(args.file)
    entries, _ = parse_file(path)
    if args.id not in entries:
        sys.exit(f"error: R{args.id} not found.")
    entries[args.id]["notes"].append(
        f"{args.session_date}: {args.note or '(cited in session)'}")
    write_file(path, entries)
    print(f"R{args.id}: +note ({args.session_date})")


def cmd_list(args):
    path = Path(args.file)
    if not path.exists():
        sys.exit(f"error: {path} does not exist.")
    entries, _ = parse_file(path)
    out = []
    for e in sorted(entries.values(), key=lambda x: x["id"]):
        if args.year and str(e.get("year", "")) != str(args.year):
            continue
        out.append(e)
    if args.format == "json":
        print(json.dumps(out, indent=2))
    else:
        for e in out:
            year = f" ({e['year']})" if e['year'] else ""
            print(f"- R{e['id']} [{e['key']}]: {e['authors']}{year} — {e['title']}")


def cmd_bibtex(args):
    path = Path(args.file)
    if not path.exists():
        sys.exit(f"error: {path} does not exist.")
    entries, _ = parse_file(path)
    lines = []
    for e in sorted(entries.values(), key=lambda x: x["id"]):
        entry_type = "article"  # naive default; user can edit
        if "arXiv" in (e.get("venue") or "") or e.get("arxiv"):
            entry_type = "misc"
        bib = [f"@{entry_type}{{{e['key']},"]
        if e["authors"]:
            bib.append(f"  author = {{{e['authors']}}},")
        if e["title"]:
            bib.append(f"  title = {{{e['title']}}},")
        if e["year"]:
            bib.append(f"  year = {{{e['year']}}},")
        if e["venue"]:
            bib.append(f"  journal = {{{e['venue']}}},")
        if e["arxiv"]:
            bib.append(f"  eprint = {{{e['arxiv']}}},")
            bib.append(f"  archivePrefix = {{arXiv}},")
        if e["url"]:
            bib.append(f"  url = {{{e['url']}}},")
        bib.append("}")
        lines.append("\n".join(bib))
    text = "\n\n".join(lines) + "\n"
    if args.out:
        Path(args.out).write_text(text)
        print(f"Wrote {len(entries)} entries to {args.out}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=FILE)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("--authors", default="")
    a.add_argument("--title", default="")
    a.add_argument("--year", default="")
    a.add_argument("--venue", default="")
    a.add_argument("--url", default="")
    a.add_argument("--arxiv", default="")
    a.add_argument("--key", default="")
    a.add_argument("--note", default="")
    a.set_defaults(fn=cmd_add)

    u = sub.add_parser("update")
    u.add_argument("id", type=int)
    u.add_argument("--authors", default="")
    u.add_argument("--title", default="")
    u.add_argument("--year", default="")
    u.add_argument("--venue", default="")
    u.add_argument("--url", default="")
    u.add_argument("--arxiv", default="")
    u.add_argument("--key", default="")
    u.add_argument("--note", default="")
    u.set_defaults(fn=cmd_update)

    l = sub.add_parser("link")
    l.add_argument("id", type=int); l.add_argument("session_date")
    l.add_argument("--note", default="")
    l.set_defaults(fn=cmd_link)

    ls = sub.add_parser("list")
    ls.add_argument("--year", default="")
    ls.add_argument("--format", choices=["json", "markdown"], default="markdown")
    ls.set_defaults(fn=cmd_list)

    bt = sub.add_parser("bibtex")
    bt.add_argument("--out", default="")
    bt.set_defaults(fn=cmd_bibtex)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
