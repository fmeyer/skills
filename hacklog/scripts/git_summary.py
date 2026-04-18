#!/usr/bin/env python3
"""
Summarize git activity since a reference point.

Usage:
  git_summary.py [--since YYYY-MM-DD] [--since-ref REF] [--paths PATH...]

Output: markdown-formatted summary suitable for inclusion in a lab
notebook entry's "Files produced / modified" subsection.

If --since is not specified, defaults to the last 24 hours.
If --since-ref is specified, uses that git reference (e.g., a commit
hash or tag) as the starting point.
"""
from __future__ import annotations
import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path


def run_git(args, cwd=None):
    try:
        r = subprocess.run(["git"] + args, capture_output=True, text=True,
                           cwd=cwd, check=True)
        return r.stdout
    except subprocess.CalledProcessError as e:
        return f"<git error: {e.stderr.strip()}>"
    except FileNotFoundError:
        sys.exit("error: git not found in PATH.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="ISO date, e.g. 2026-04-18")
    ap.add_argument("--since-ref",
                    help="Git ref (commit or tag) to use as starting point.")
    ap.add_argument("--paths", nargs="*", default=["."],
                    help="Directories or files to restrict the diff (default: .)")
    args = ap.parse_args()

    # Default to last 24h if nothing given
    if not args.since and not args.since_ref:
        since_date = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    else:
        since_date = args.since

    lines = ["### Git activity"]

    # Commits
    if args.since_ref:
        log_range = f"{args.since_ref}..HEAD"
        log_args = ["log", "--pretty=format:- %h %s", log_range, "--"] + args.paths
    else:
        log_args = ["log", "--pretty=format:- %h %s", f"--since={since_date}", "--"] + args.paths
    commits = run_git(log_args).strip()

    if commits and not commits.startswith("<git error"):
        lines.append("")
        lines.append("**Commits:**")
        lines.append("")
        lines.append(commits)
    else:
        lines.append("")
        lines.append("(no new commits)")

    # Files changed (tracked)
    if args.since_ref:
        diff_args = ["diff", "--stat", f"{args.since_ref}..HEAD", "--"] + args.paths
    else:
        # List files modified since the date
        diff_args = ["log", "--pretty=format:", "--name-only",
                     f"--since={since_date}", "--"] + args.paths
    diff_out = run_git(diff_args).strip()

    if diff_out and not diff_out.startswith("<git error"):
        files = sorted(set(line for line in diff_out.splitlines() if line.strip()))
        if files:
            lines.append("")
            lines.append("**Files touched:**")
            lines.append("")
            for f in files:
                lines.append(f"- `{f}`")

    # Untracked files
    untracked = run_git(["ls-files", "--others", "--exclude-standard"]).strip()
    if untracked and not untracked.startswith("<git error"):
        files = [line for line in untracked.splitlines() if line.strip()]
        if files:
            lines.append("")
            lines.append("**Untracked files:**")
            lines.append("")
            for f in sorted(files):
                lines.append(f"- `{f}`")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
