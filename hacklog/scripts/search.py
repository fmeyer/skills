#!/usr/bin/env python3
"""
Search HACKLOG.md for sessions matching a query or date range.

Usage:
  search.py --query "keyword" [--after YYYY-MM-DD] [--before YYYY-MM-DD]
            [--file PATH] [--format {json,markdown}]

Output: list of matching sessions, each with date, title, and snippet
of the matching subsection. JSON by default; markdown if --format markdown.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path


SESSION_RE = re.compile(
    r"^## Session (?P<date>\d{4}-\d{2}-\d{2})(?P<suffix>\s*\([^)]+\))?"
    r":\s*(?P<title>.*?)$",
    re.MULTILINE,
)


def parse_sessions(text):
    """Split text into session blocks.

    Returns list of dicts: {date, suffix, title, body}
    """
    sessions = []
    matches = list(SESSION_RE.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sessions.append({
            "date": m.group("date"),
            "suffix": (m.group("suffix") or "").strip(),
            "title": m.group("title").strip(),
            "body": body,
        })
    return sessions


def filter_date(sessions, after=None, before=None):
    def keep(s):
        d = dt.date.fromisoformat(s["date"])
        if after and d < dt.date.fromisoformat(after):
            return False
        if before and d > dt.date.fromisoformat(before):
            return False
        return True
    return [s for s in sessions if keep(s)]


def snippets(body, query, context=120):
    """Return list of ~240-char snippets around query matches."""
    out = []
    if not query:
        return out
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    for m in pattern.finditer(body):
        start = max(0, m.start() - context)
        end = min(len(body), m.end() + context)
        snippet = body[start:end].replace("\n", " ")
        out.append("..." + snippet + "...")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="")
    ap.add_argument("--after", help="ISO date lower bound (inclusive).")
    ap.add_argument("--before", help="ISO date upper bound (inclusive).")
    ap.add_argument("--file", default="HACKLOG.md")
    ap.add_argument("--format", choices=["json", "markdown"], default="json")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        sys.exit(f"error: {path} does not exist.")

    text = path.read_text()
    sessions = parse_sessions(text)
    sessions = filter_date(sessions, args.after, args.before)

    results = []
    for s in sessions:
        if args.query:
            snips = snippets(s["body"], args.query)
            if not snips:
                continue
            results.append({
                "date": s["date"],
                "suffix": s["suffix"],
                "title": s["title"],
                "snippets": snips,
            })
        else:
            # No query: include whole session headers
            results.append({
                "date": s["date"],
                "suffix": s["suffix"],
                "title": s["title"],
                "length": len(s["body"]),
            })

    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            hdr = f"**{r['date']}{r['suffix']}** — {r['title']}"
            print(f"- {hdr}")
            for s in r.get("snippets", []):
                print(f"    - {s}")


if __name__ == "__main__":
    main()
