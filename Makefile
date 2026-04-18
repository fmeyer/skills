.PHONY: plan install list prune add-fork rm-fork update-forks status init-vendor help

help:
	@echo "Targets:"
	@echo "  plan             dry-run: show what install would link"
	@echo "  install          apply symlinks into ~/.claude/skills"
	@echo "  list             list discovered skills"
	@echo "  prune            apply + remove stale symlinks pointing into this repo"
	@echo "  status           git status + submodule status"
	@echo "  add-fork         URL=<git-url> [NAME=<dir>] — add upstream as vendor/<name> submodule"
	@echo "  rm-fork          NAME=<dir> — deinit + remove vendor/<name> submodule"
	@echo "  update-forks     pull latest commits on default branch for every vendor submodule"
	@echo "  init-vendor      git submodule update --init --recursive"

plan:
	@lua install.lua

install:
	@lua install.lua --apply

list:
	@lua install.lua --list

prune:
	@lua install.lua --apply --prune

status:
	@git status -s
	@echo "--- submodules ---"
	@git submodule status

init-vendor:
	@git submodule update --init --recursive

update-forks:
	@git submodule update --remote --recursive
	@echo "(staged submodule bumps — commit with: git commit -am 'bump forks')"

# Add a fork/upstream skill repo as a submodule under vendor/
# Usage: make add-fork URL=https://github.com/foo/bar.git
#        make add-fork URL=https://github.com/foo/bar.git NAME=custom
add-fork:
ifndef URL
	$(error URL is required. Usage: make add-fork URL=<git-url> [NAME=<dir>])
endif
	@NAME="$(NAME)"; \
	if [ -z "$$NAME" ]; then \
	  NAME=$$(basename "$(URL)" .git); \
	fi; \
	mkdir -p vendor; \
	git submodule add "$(URL)" "vendor/$$NAME"; \
	echo "Added vendor/$$NAME. Run 'make plan' to preview links."

# Remove a fork submodule cleanly.
# Usage: make rm-fork NAME=bar
rm-fork:
ifndef NAME
	$(error NAME is required. Usage: make rm-fork NAME=<dir>)
endif
	@git submodule deinit -f "vendor/$(NAME)"
	@git rm -f "vendor/$(NAME)"
	@rm -rf ".git/modules/vendor/$(NAME)"
	@echo "Removed vendor/$(NAME). Run 'make prune' to drop its symlink."
