#!/usr/bin/env python3
"""
Render a markdown table from JSON or CSV input.

Usage:
  render_table.py --json PATH [--columns col1 col2 ...] [--align right|left|center]
  render_table.py --csv  PATH [--columns col1 col2 ...] [--align right|left|center]

JSON input forms accepted:
  - list of dicts: [{"name": "...", "value": 42}, ...]
  - dict with rows: {"rows": [...], "columns": [...]}

CSV input: standard with header row.

Output: markdown table to stdout. Meant to be used by Claude to produce
consistent numeric tables in lab notebook entries.
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path


def rows_from_json(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, list):
        if not data:
            return [], []
        cols = list(data[0].keys())
        rows = [[row.get(c, "") for c in cols] for row in data]
        return cols, rows
    if isinstance(data, dict) and "rows" in data:
        cols = data.get("columns") or list(data["rows"][0].keys())
        rows = [[row.get(c, "") for c in cols] for row in data["rows"]]
        return cols, rows
    sys.exit("error: JSON input must be a list of dicts or {rows, columns} dict.")


def rows_from_csv(path):
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        cols = reader.fieldnames or []
        rows = [[row.get(c, "") for c in cols] for row in reader]
        return cols, rows


def render(cols, rows, selected=None, align="left"):
    if selected:
        missing = [c for c in selected if c not in cols]
        if missing:
            sys.exit(f"error: columns not in input: {missing}")
        idxs = [cols.index(c) for c in selected]
        cols = selected
        rows = [[r[i] for i in idxs] for r in rows]

    # Stringify
    rows_str = [[str(v) if v is not None else "" for v in r] for r in rows]
    widths = [max(len(c), *(len(row[i]) for row in rows_str)) for i, c in enumerate(cols)]

    sep_parts = []
    for w in widths:
        if align == "right":
            sep_parts.append("-" * (w - 1) + ":")
        elif align == "center":
            sep_parts.append(":" + "-" * (w - 2) + ":")
        else:
            sep_parts.append("-" * w)
    sep = "| " + " | ".join(sep_parts) + " |"

    hdr = "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cols)) + " |"
    print(hdr)
    print(sep)
    for row in rows_str:
        print("| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(cols))) + " |")


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--json")
    src.add_argument("--csv")
    ap.add_argument("--columns", nargs="*",
                    help="Subset / reorder columns to display.")
    ap.add_argument("--align", choices=["left", "right", "center"], default="left")
    args = ap.parse_args()

    if args.json:
        cols, rows = rows_from_json(args.json)
    else:
        cols, rows = rows_from_csv(args.csv)
    render(cols, rows, args.columns, args.align)


if __name__ == "__main__":
    main()
