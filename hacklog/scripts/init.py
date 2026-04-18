#!/usr/bin/env python3
"""
Initialize HACKLOG.md, HACKLOG_TODO.md, and HACKLOG_HYPOTHESES.md
in the current directory.

Usage:
  init.py --project "Project name" [--description "Short description"]
          [--force]

Refuses to overwrite existing files unless --force is given.
"""
from __future__ import annotations
import argparse
import datetime as dt
import sys
from pathlib import Path


LOG_TEMPLATE = """# Hacklog — {project}

{description}

---

"""

TODO_TEMPLATE = """# Hacklog TODO — {project}

## Pending

## Done

## Open questions

"""

HYPOTHESES_TEMPLATE = """# Hacklog Hypotheses — {project}

Tracked research hypotheses with status, evidence, and cross-references
to sessions in HACKLOG.md.

## Legend

- **proposed**: stated, not yet tested
- **tested**: evidence gathered (positive or negative)
- **confirmed**: strong evidence supports
- **rejected**: disproved or counterexample found
- **refined**: superseded by a sharper statement (with pointer to the new id)

---

## Active

## Archived

"""

EXPERIMENTS_TEMPLATE = """# Hacklog Experiments — {project}

Structured records of experimental runs, cross-referenced to sessions
in HACKLOG.md.

## Legend

- **planned**: designed, not yet executed
- **running**: in progress
- **complete**: finished, result recorded
- **failed**: aborted or errored

---

## Active

## Archived

"""

REFS_TEMPLATE = """# Hacklog References — {project}

Bibliography accumulated across the project. Emit BibTeX via
`scripts/references.py bibtex --out refs.bib`.

---

## Entries

"""

DECISIONS_TEMPLATE = """# Hacklog Decisions — {project}

Methodological choices with rationale and alternatives considered.
Distinct from hypotheses: a decision is a chosen path (e.g., "use WL2
not 3-WL"), not a claim being empirically tested.

## Legend

- **open**: under consideration
- **decided**: chosen
- **revisited**: re-examined, possibly confirmed or reversed
- **reversed**: decision overturned

---

## Entries

"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    paths_templates = [
        (Path("HACKLOG.md"), LOG_TEMPLATE),
        (Path("HACKLOG_TODO.md"), TODO_TEMPLATE),
        (Path("HACKLOG_HYPOTHESES.md"), HYPOTHESES_TEMPLATE),
        (Path("HACKLOG_EXPERIMENTS.md"), EXPERIMENTS_TEMPLATE),
        (Path("HACKLOG_REFS.md"), REFS_TEMPLATE),
        (Path("HACKLOG_DECISIONS.md"), DECISIONS_TEMPLATE),
    ]

    for p, _ in paths_templates:
        if p.exists() and not args.force:
            sys.exit(
                f"error: {p} already exists. Use --force to overwrite."
            )

    desc = args.description or (
        f"_Started {dt.date.today().isoformat()}._"
    )
    for p, tmpl in paths_templates:
        p.write_text(tmpl.format(project=args.project, description=desc))
    print(f"Created {len(paths_templates)} files: "
          + ", ".join(str(p) for p, _ in paths_templates))


if __name__ == "__main__":
    main()
