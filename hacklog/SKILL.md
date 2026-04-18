---
name: hacklog
description: Maintain a structured research lab notebook (HACKLOG.md) and companion HACKLOG_TODO.md across multi-session research projects. Use when the user wants to start or wrap a research session, append findings, summarize past work, or search prior entries. Typical invocations: "/hacklog session" (append new dated entry for today), "/hacklog summary [--since DATE]" (digest of recent sessions), "/hacklog search <query>" (find prior mentions), "/hacklog wrap" (end-of-session checklist + append + TODO sync).
---

# hacklog

A research lab notebook skill. Maintains two files in the working directory:

- **HACKLOG.md** — chronological log of research sessions, with structured
  subsections per session.
- **HACKLOG_TODO.md** — rolling task list split into *Done*, *Pending*, *Open questions*.
- **HACKLOG_HYPOTHESES.md** — research hypotheses with status and evidence, cross-referenced to sessions.
- **HACKLOG_EXPERIMENTS.md** — structured records of experimental runs (script, inputs, result, duration).
- **HACKLOG_REFS.md** — bibliography accumulated across sessions; exportable as BibTeX.
- **HACKLOG_DECISIONS.md** — methodological choices with rationale and alternatives considered.

Invoked via the slash command `/hacklog <subcommand> [args]`.

## Subcommands

### `/hacklog session`
Append a new dated session entry to `HACKLOG.md`. Structure:

```
## Session YYYY-MM-DD: <one-line title>

### Context
<What the session starts from — current state of the project.>

### Experiments / computations
<Each experiment as its own subsection. Prefer tables where numeric.>

### Key findings
<Bulleted structural takeaways.>

### Files produced / modified
<Script and data filenames with brief descriptions.>

### Open questions / next steps
<What's unresolved; what to try next.>
```

**Invocation**: run `scripts/session_append.py --title "<title>"` to insert the
boilerplate. Claude then fills in each subsection based on the conversation.

### `/hacklog wrap`
End-of-session workflow:

1. Run `scripts/git_summary.py` to list files changed since the last session.
2. Run `/hacklog session` to append the new entry.
3. Run `scripts/todo_sync.py --done <item> --pending <item>` to move items
   between `HACKLOG_TODO.md` sections.
4. Claude synthesizes the session's findings from the conversation and populates
   each subsection of the new entry.

### `/hacklog summary [--since DATE]`
Synthesize recent sessions into a compact digest. Pulls the last N dated
sections (default 3) and produces:

- Cumulative findings across the range
- Outstanding open questions
- File artifacts produced

Run `scripts/search.py --after DATE` to extract sessions, then Claude synthesizes.

### `/hacklog search <query>`
Find past entries matching a keyword or regex. Invoke
`scripts/search.py --query "<q>"`. Output is a list of `(date, section, snippet)`
tuples.

### `/hacklog init`
Initialize `HACKLOG.md`, `HACKLOG_TODO.md`, and `HACKLOG_HYPOTHESES.md` in
the current directory. Invoke `scripts/init.py --project "<project name>"`.

### `/hacklog hypothesis <sub>`
Track research hypotheses across sessions. Hypotheses are stored in
`HACKLOG_HYPOTHESES.md` as H1, H2, … with statuses:
*proposed* → *tested* → *confirmed* / *rejected* / *refined*.

Subcommands (all via `scripts/hypothesis.py`):

- `add "<statement>" [--title "<short>"]` — create a new hypothesis
  with next available id; status starts *proposed*.
- `update <id> <status> [--note "..."]` — change status; optional note
  appended to evidence with today's date.
- `link <id> <YYYY-MM-DD> [--note "..."]` — add a session reference to
  evidence (use after running an experiment that bears on the hypothesis).
- `archive <id> [--reason "..."]` — move from Active to Archived.
- `list [--status STATUS] [--format json|markdown]` — summary.

**Usage pattern**: when a session introduces a new research direction,
Claude should create a hypothesis with `/hacklog hypothesis add "..."` and
link it in the session's "Hypothesis updates" subsection. When a session
gathers evidence, use `update` or `link` to record the progress.

### `/hacklog experiment <sub>`
Track experimental runs in `HACKLOG_EXPERIMENTS.md`. Subcommands
(all via `scripts/experiments.py`):

- `add "<title>" --script <path> [--inputs "..."] [--notes "..."]`
- `update <id> <status> [--result "..."] [--duration "..."] [--note "..."]`
  — status ∈ {planned, running, complete, failed}
- `link <id> <YYYY-MM-DD> [--note "..."]`
- `list [--status STATUS] [--format json|markdown]`

Use for each non-trivial run so its metadata is structured and queryable
(rather than buried in a session's prose). Records cross-reference
sessions via linked notes.

### `/hacklog ref <sub>`
Track references in `HACKLOG_REFS.md`. Subcommands
(all via `scripts/references.py`):

- `add --authors "..." --title "..." --year YYYY [--venue "..."]
   [--url "..."] [--arxiv "2508.05871"] [--key "lepovic2010"]
   [--note "..."]` — auto-generates citation key if not given.
- `update <id> [--field "..."]` — change any field.
- `link <id> <YYYY-MM-DD> [--note "..."]` — record that the ref was
  cited or invoked in a session.
- `list [--year YYYY] [--format json|markdown]`
- `bibtex [--out FILE]` — emit a BibTeX file from all entries.

Use to accumulate the bibliography as the project progresses, so the
paper-writing step doesn't require reconstructing everything from memory.

### `/hacklog decision <sub>`
Track methodological decisions in `HACKLOG_DECISIONS.md`. Subcommands
(all via `scripts/decisions.py`):

- `add "<title>" --context "..." --decision "..." [--rationale "..."]
   [--alternatives "..."]`
- `update <id> <status> [--note "..."]` — status ∈
  {open, decided, revisited, reversed}
- `list [--status STATUS] [--format json|markdown]`

Use for any methodological choice that a reviewer might later question
("why did you use X not Y?"). Captures rationale at the moment of
decision, when it's freshest.

---

## How to use the scripts

All scripts live under `scripts/` relative to this SKILL.md. They accept CLI
args and emit markdown or JSON. Use them as pre-processors; Claude always does
the final synthesis from the conversation context.

### Script inventory

- `session_append.py --title "..."` — insert boilerplate session block into
  `HACKLOG.md`. Non-destructive (atomic insert before trailing
  "Bottom line" section if present, otherwise at EOF).
- `git_summary.py [--since DATE]` — git log + diff summary; output as a
  markdown bullet list of commits and a file-modification summary.
- `todo_sync.py [--done "..."] [--pending "..."] [--open "..."]` — move or
  append items in `HACKLOG_TODO.md`.
- `search.py --query "..." [--after DATE] [--before DATE]` — returns session
  snippets matching the query, in JSON. Default: whole HACKLOG.md.
- `render_table.py <json_or_csv>` — produce a markdown table from structured
  input. Useful when Claude has data rows to report and wants a compact
  representation.
- `init.py --project "..."` — create empty HACKLOG.md, HACKLOG_TODO.md, and
  HACKLOG_HYPOTHESES.md with consistent headers.
- `hypothesis.py {add|update|link|archive|list} ...` — track research
  hypotheses in HACKLOG_HYPOTHESES.md (see `/hacklog hypothesis` section
  above).
- `experiments.py {add|update|link|list} ...` — structured experimental
  run records in HACKLOG_EXPERIMENTS.md.
- `references.py {add|update|link|list|bibtex} ...` — bibliography in
  HACKLOG_REFS.md, with BibTeX export.
- `decisions.py {add|update|list} ...` — methodological decisions in
  HACKLOG_DECISIONS.md.

### Conventions the skill enforces

1. **Dates are ISO 8601** (YYYY-MM-DD). If today's date is already present,
   append a sub-session (e.g., "Session 2026-04-18 (evening)") rather than
   duplicating the header.
2. **Tables over prose for numeric findings.** A 4-row markdown table beats
   four separate prose paragraphs.
3. **File references** use absolute paths in the first mention, then short names.
4. **TODO items are checkboxes** (`- [ ]`) for pending, with clear verbs.
5. **Each session concludes with "Open questions / next steps"** — never leave
   a session with no explicit handoff.

### When the user does NOT say `/hacklog`

This skill only activates on explicit invocation. If the user describes session
activity without the slash command, ask whether they want to append to the
notebook; do not silently write to HACKLOG.md.

### When multiple projects share context

If invoked in a directory where HACKLOG.md does not exist, prompt the user
to run `/hacklog init` first. Never assume an existing file in a parent
directory is the target.
