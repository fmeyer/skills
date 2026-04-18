# skills

My Claude Code skills repo — a dotfiles-style setup that symlinks each skill
into `~/.claude/skills/<name>`.

## Layout

```
.
├── install.lua        # Lua installer (dry-run by default)
├── Makefile           # plan / install / add-fork / update-forks
├── <skill>/           # local skill — any dir with SKILL.md
│   └── SKILL.md
└── vendor/            # forks / upstream skills as git submodules
    └── <repo>/
        ├── SKILL.md           # single-skill repo → linked as <repo>
        └── ...                # OR a collection: each child dir with
                               # SKILL.md is linked individually
```

A top-level dir is treated as a skill when it contains `SKILL.md`. Prefix
a dir with `_` or drop a `.skillignore` file inside it to exclude.

## Usage

```sh
make plan           # show what would be linked (dry run)
make install        # create/update symlinks in ~/.claude/skills
make list           # list discovered skills
make prune          # install + remove stale symlinks pointing into this repo
make status         # git status + submodule status
```

Or call the installer directly:

```sh
lua install.lua --apply --target ~/.claude/skills
```

## Managing forks / submodules

Add a third-party skill repo as a submodule under `vendor/`:

```sh
make add-fork URL=https://github.com/someone/their-skills.git
make add-fork URL=https://github.com/foo/bar.git NAME=bar-custom
make install
```

Pull newest commits for every vendored fork:

```sh
make update-forks
git commit -am "bump forks"
```

Remove a fork cleanly:

```sh
make rm-fork NAME=their-skills
make prune
```

After cloning fresh:

```sh
git clone --recurse-submodules <this-repo>
make init-vendor    # if --recurse-submodules was forgotten
make install
```
