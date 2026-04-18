# hacklog

A Claude Code skill for maintaining structured research lab notebooks
(`HACKLOG.md`) and companion task lists (`HACKLOG_TODO.md`) across multi-session
research projects.

## Install

```bash
# Symlink into personal skills directory
mkdir -p ~/.claude/skills
ln -s $(pwd)/hacklog ~/.claude/skills/hacklog
```

Claude Code discovers skills in `~/.claude/skills/` and loads `SKILL.md`
on-demand. The skill surfaces as the slash command `/hacklog`.

## Usage

From any project directory:

```
/hacklog init --project "my research"                           # bootstrap HACKLOG.md, HACKLOG_TODO.md, HACKLOG_HYPOTHESES.md
/hacklog session                                                # append new dated entry, Claude fills it
/hacklog wrap                                                   # end-of-session: git diff + session + todo sync
/hacklog summary --since 2026-04-01                             # digest of recent sessions
/hacklog search "CFI"                                           # find past mentions
/hacklog hypothesis add "statement" --title "short title"       # create H<n>
/hacklog hypothesis update 3 tested --note "ran experiment"     # change status
/hacklog hypothesis link 3 2026-04-18 --note "evidence here"    # link to session
/hacklog hypothesis list --status confirmed                     # filter

/hacklog experiment add "title" --script path/to/run.py --inputs "n=45"
/hacklog experiment update 7 complete --result "0 collisions" --duration "45s"
/hacklog experiment list --status complete

/hacklog ref add --authors "Cioabă et al." --title "..." --year 2025 --arxiv 2508.05871
/hacklog ref bibtex --out refs.bib                              # export BibTeX

/hacklog decision add "WL2 vs 3-WL" --context "distinguishing SRGs" \
    --decision "use WL2" --rationale "compute cost 100x lower" \
    --alternatives "3-WL, LDeck_2"
/hacklog decision update 4 reversed --note "moved to LDeck_2 instead"
```

## Layout

```
hacklog/
├── SKILL.md                 # Skill definition + instructions for Claude
├── scripts/
│   ├── init.py              # Bootstrap HACKLOG.md, HACKLOG_TODO.md, HACKLOG_HYPOTHESES.md
│   ├── session_append.py    # Insert dated session block
│   ├── git_summary.py       # Summarize git activity since last session
│   ├── todo_sync.py         # Move items between Done/Pending/Open
│   ├── hypothesis.py        # Track research hypotheses (add/update/link/archive/list)
│   ├── experiments.py       # Track experimental runs (add/update/link/list)
│   ├── references.py        # Bibliography (add/update/link/list/bibtex)
│   ├── decisions.py         # Methodological choices (add/update/list)
│   ├── search.py            # Find sessions by keyword or date range
│   └── render_table.py      # Markdown tables from JSON/CSV
├── templates/
│   └── session_template.md  # Reference template for session blocks
└── README.md                # This file
```

## Design notes

- **Date handling is ISO 8601.** Same-day sessions get automatic suffixes
  (`afternoon`, `evening`, `late night`, …).
- **Scripts are idempotent where possible.** `init.py` refuses to overwrite
  without `--force`. `session_append.py` inserts; never rewrites existing
  sessions.
- **Scripts do mechanics; Claude does synthesis.** Subsections are left with
  HTML comments for Claude to fill in from conversation context. No AI in the
  scripts themselves.
- **Conventions enforced by the skill** (not by scripts):
  - Tables over prose for numeric findings.
  - Each session ends with "Open questions / next steps" — never leave a
    session with no explicit handoff.
  - TODO items use `- [ ]` checkboxes for tasks, plain bullets for questions.
